# === Django 초기화 블록 (파일 최상단에 위치) ===
import os
import sys
from pathlib import Path
from contextlib import closing

# 현재 파일: /Users/Super007/Project/letsrace/base/train_LightGBM.py
# -> parent: base
# -> parent.parent: 프로젝트 루트(여기에 manage.py가 있다고 가정)
BASE_DIR = Path(__file__).resolve().parent.parent

# 프로젝트 루트를 sys.path 에 추가 (패키지 import 가능하도록)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ★ manage.py 에 있는 값으로 정확히 맞춰 주세요 ★
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "letsrace.settings")

import django

django.setup()
# === 여기까지 Django 초기화 ===

import pymysql
import pandas as pd
import lightgbm as lgb
from typing import List, Tuple


def _get_db_conf_from_django():
    """Try reading DB settings from Django if available.

    Returns a dict compatible with pymysql.connect or None if not available.
    """
    try:
        import django
        from django.conf import settings

        # If Django isn't setup yet (running as a script), set it up.
        if not settings.configured:
            # Best-effort: use env DJANGO_SETTINGS_MODULE if present
            if os.getenv("DJANGO_SETTINGS_MODULE"):
                django.setup()
            else:
                return None

        db = settings.DATABASES.get("default", {})
        if not db or db.get("ENGINE") != "django.db.backends.mysql":
            return None

        opts = db.get("OPTIONS", {})
        conf = {
            "host": db.get("HOST") or "127.0.0.1",
            "user": db.get("USER"),
            "password": db.get("PASSWORD"),
            "db": db.get("NAME"),
            "port": int(db.get("PORT") or 3306),
            "charset": opts.get("charset", "utf8mb4"),
            "cursorclass": pymysql.cursors.DictCursor,
            "autocommit": True,
        }
        # Propagate SSL if provided in Django options
        if "ssl" in opts:
            conf["ssl"] = opts["ssl"]
        return conf
    except Exception:
        return None


def _get_db_conf_from_env():
    """Read DB settings from environment variables (optionally loading .env).

    Supported vars: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_SSL_CA
    """
    # Lazy-load dotenv if present
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        pass

    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    db = os.getenv("MYSQL_DB")
    port = int(os.getenv("MYSQL_PORT") or 3306)
    ssl_ca = os.getenv("MYSQL_SSL_CA")

    if not all([host, user, password, db]):
        return None

    conf = {
        "host": host,
        "user": user,
        "password": password,
        "db": db,
        "port": port,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }
    if ssl_ca:
        conf["ssl"] = {"ca": ssl_ca}
    return conf


def get_conn():
    """Obtain a PyMySQL connection using Django settings or env fallback.

    Order of precedence:
      1) Django DATABASES['default'] if configured and MySQL backend
      2) Environment variables (MYSQL_*)
    """
    conf = _get_db_conf_from_django() or _get_db_conf_from_env()

    if conf is None:
        # Final fallback (explicit values required). Raise a helpful error.
        raise RuntimeError(
            "Database configuration not found. Set DJANGO_SETTINGS_MODULE or export MYSQL_* env vars."
        )

    conn = pymysql.connect(**conf)
    try:
        conn.ping(reconnect=True)
    except Exception:
        pass
    return conn


def load_train_data_from_db(conn, from_date: str = "20231201") -> pd.DataFrame:
    sql = """
    SELECT
        e.rcity      AS 경마장,
        e.rdate      AS 경주일,
        e.rno        AS 경주번호,
        x.distance   AS 경주거리,
        e.gate       AS 마번,
        e.rank       AS 예상순위1,
        e.r_pop      AS 예상순위2,
        e.r_rank     AS 실제순위,
        e.alloc1r    AS 단승식배당율,
        e.alloc3r    AS 연승식배당율,
        /* 복승식 배당율 */
        CAST(SUBSTRING(r.r2alloc,   3) AS DECIMAL(10, 0)) AS 복승식배당율,
        /* 삼복승식 배당율 */
        CAST(SUBSTRING(r.r333alloc, 4) AS DECIMAL(10, 0)) AS 삼복승식배당율
    FROM The1.exp011 AS e
    LEFT JOIN The1.exp010 AS x
           ON x.rcity = e.rcity
          AND x.rdate = e.rdate
          AND x.rno   = e.rno
    LEFT JOIN The1.rec010 AS r
           ON r.rcity = e.rcity
          AND r.rdate = e.rdate
          AND r.rno   = e.rno
    WHERE e.rdate >= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    df = pd.read_sql(sql, conn, params=[from_date])
    return df


def save_lgb_model_to_db(conn, model: lgb.Booster, model_name: str, comment: str = ""):
    """LightGBM Booster를 DB에 문자열로 저장"""
    model_str = model.model_to_string()  # Booster 전체를 text로 직렬화

    # Ensure table exists
    _ensure_lgb_models_table(conn)

    with conn.cursor() as cur:
        # 같은 model_name 내에서 version +1
        cur.execute(
            """
            SELECT IFNULL(MAX(version), 0) AS max_ver
            FROM lgb_models
            WHERE model_name = %s
            """,
            (model_name,),
        )
        row = cur.fetchone()
        next_ver = (row["max_ver"] or 0) + 1

        cur.execute(
            """
            INSERT INTO lgb_models (model_name, version, created_at, comment, model_text)
            VALUES (%s, %s, NOW(), %s, %s)
            """,
            (model_name, next_ver, comment, model_str),
        )
    conn.commit()
    print(f"▶ 모델 [{model_name}] v{next_ver} DB 저장 완료.")


def load_latest_lgb_model_from_db(conn, model_name: str) -> lgb.Booster:

    print(f"▶ DB에서 모델 [{model_name}] 최신 버전 로드 시도...")

    """해당 model_name의 최신 버전 모델을 DB에서 읽어서 Booster 복원"""

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT model_text
            FROM lgb_models
            WHERE model_name = %s
            ORDER BY version DESC
            LIMIT 1
            """,
            (model_name,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"DB에 모델 [{model_name}] 이(가) 없습니다.")
        model_str = row["model_text"]

    booster = lgb.Booster(model_str=model_str)
    print(f"▶ 모델 [{model_name}] 최신 버전 로드 완료.")
    return booster


def _ensure_lgb_models_table(conn):
    """Create lgb_models table if it does not exist."""
    sql = """
    CREATE TABLE IF NOT EXISTS lgb_models (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        model_name VARCHAR(100) NOT NULL,
        version INT NOT NULL,
        created_at DATETIME NOT NULL,
        comment VARCHAR(255) NULL,
        model_text LONGTEXT NOT NULL,
        UNIQUE KEY unique_model_version (model_name, version),
        KEY idx_model_name_created (model_name, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def train_lgb_for_top3_from_db(
    from_date: str = "20231201", model_name: str = "sb_top3_v1"
) -> lgb.Booster:
    """DB에서 학습 데이터 로드 → LightGBM 학습 → 모델을 DB에 저장"""
    with closing(get_conn()) as conn:
        df = load_train_data_from_db(conn, from_date=from_date)

    # 타입 정리
    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)

    df["예상순위1"] = df["예상순위1"].astype(int)
    df["예상순위2"] = df["예상순위2"].astype(int)

    df["실제순위"] = df["실제순위"].astype(int)

    if "경주거리" in df.columns:
        df["경주거리"] = df["경주거리"].astype(int)

    # 특징 엔지니어링 (학습/예측 모두 동일 규칙 사용)
    df["rank_gap"] = df["예상순위2"] - df["예상순위1"]
    df["is_new"] = ((df["예상순위1"] >= 98) | (df["예상순위2"] >= 98)).astype(int)

    feature_cols = ["예상순위1", "예상순위2", "rank_gap", "is_new"]
    if "경주거리" in df.columns:
        feature_cols.append("경주거리")

    # label: 실제 1~3위 안에 들었는가?
    df["label_sb"] = (df["실제순위"] <= 3).astype(int)

    train_set = lgb.Dataset(df[feature_cols], label=df["label_sb"])

    params = dict(
        objective="binary",
        boosting_type="gbdt",
        learning_rate=0.03,
        num_leaves=31,
        feature_fraction=0.9,
        bagging_fraction=0.9,
        bagging_freq=3,
        verbose=-1,
    )

    print("▶ LightGBM 학습 시작...")
    model = lgb.train(params, train_set, num_boost_round=400)
    print("▶ 학습 완료.")

    # 학습한 모델 DB에 저장
    with closing(get_conn()) as conn:
        save_lgb_model_to_db(
            conn, model, model_name, comment=f"{from_date} 이후 데이터로 학습"
        )

    return model


def load_new_races_from_db(conn, from_date: str = "20251129") -> pd.DataFrame:
    """실제순위 없이, 새 경주(예상순위만 있는) 데이터 로드"""
    sql = """
    SELECT
        e.rcity     AS 경마장,
        e.rdate     AS 경주일,
        e.rno       AS 경주번호,
        x.distance  AS 경주거리,
        e.gate      AS 마번,
        e.rank      AS 예상순위1,
        e.r_pop     AS 예상순위2
    FROM The1.exp011 AS e
    LEFT JOIN The1.exp010 AS x
           ON x.rcity = e.rcity
          AND x.rdate = e.rdate
          AND x.rno   = e.rno
    WHERE e.rdate >= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    df = pd.read_sql(sql, conn, params=[from_date])
    return df


def predict_top6_for_new_races(
    model: lgb.Booster, df_new: pd.DataFrame
) -> pd.DataFrame:
    """
    df_new: (경마장, 경주일, 경주번호, 경주거리, 마번, 예상순위1, 예상순위2)
    return: 경주별 상위 6두 (마번 + 확률)
    """
    d = df_new.copy()

    # 타입 정리
    d["경주일"] = d["경주일"].astype(str)
    d["경주번호"] = d["경주번호"].astype(int)
    d["마번"] = d["마번"].astype(int)
    d["예상순위1"] = d["예상순위1"].astype(int)
    d["예상순위2"] = d["예상순위2"].astype(int)
    if "경주거리" in d.columns:
        d["경주거리"] = d["경주거리"].astype(int)

    # 학습과 동일한 feature 생성
    d["rank_gap"] = d["예상순위2"] - d["예상순위1"]
    d["is_new"] = ((d["예상순위1"] >= 98) | (d["예상순위2"] >= 98)).astype(int)

    feature_cols = ["예상순위1", "예상순위2", "rank_gap", "is_new"]
    if "경주거리" in d.columns:
        feature_cols.append("경주거리")

    d["p_sb"] = model.predict(d[feature_cols])

    # 경주별 상위 6두 정리
    rows = []
    for (track, date, rno), g in d.groupby(["경마장", "경주일", "경주번호"]):
        g2 = g.sort_values("p_sb", ascending=False).head(6)

        rows.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "선택_상위6_마번": ",".join(map(str, g2["마번"].tolist())),
                "선택_상위6_p_sb": ",".join(f"{x:.4f}" for x in g2["p_sb"].tolist()),
            }
        )

    result = pd.DataFrame(rows)
    return result


def predict_full_rank_for_new_races(
    model: lgb.Booster, df_new: pd.DataFrame
) -> pd.DataFrame:
    """
    👉 df_new: (경마장, 경주일, 경주번호, 경주거리, 마번, 예상순위1, 예상순위2)
    👉 출력: 각 경주별 모든 말에 대해
        - p_sb: 상위 3위 안에 들 확률
        - 예상순위_LGBM: p_sb 내림차순 기준 랭킹(1,2,3,...)
    """
    d = df_new.copy()

    # 타입 정리
    d["경주일"] = d["경주일"].astype(str)
    d["경주번호"] = d["경주번호"].astype(int)
    d["마번"] = d["마번"].astype(int)
    d["예상순위1"] = d["예상순위1"].astype(int)
    d["예상순위2"] = d["예상순위2"].astype(int)
    if "경주거리" in d.columns:
        d["경주거리"] = d["경주거리"].astype(int)

    # 학습 시와 동일 Feature
    d["rank_gap"] = d["예상순위2"] - d["예상순위1"]
    d["is_new"] = ((d["예상순위1"] >= 98) | (d["예상순위2"] >= 98)).astype(int)

    feature_cols = ["예상순위1", "예상순위2", "rank_gap", "is_new"]
    if "경주거리" in d.columns:
        feature_cols.append("경주거리")

    # LightGBM 확률 예측
    d["p_sb"] = model.predict(d[feature_cols])

    # 경주별 p_sb 내림차순 정렬 후 예상순위 부여
    d = d.sort_values(
        ["경마장", "경주일", "경주번호", "p_sb"],
        ascending=[True, True, True, False],
    )

    d["예상순위_LGBM"] = (
        d.groupby(["경마장", "경주일", "경주번호"]).cumcount().astype(int) + 1
    )

    # 보기 좋게 정렬
    d = d.sort_values(["경마장", "경주일", "경주번호", "예상순위_LGBM"]).reset_index(
        drop=True
    )

    return d


def predict_full_rank_for_new_races_and_update_db(
    conn, model: lgb.Booster, df_new: pd.DataFrame
) -> pd.DataFrame:
    """
    df_new: (경마장, 경주일, 경주번호, 경주거리, 마번, 예상순위1, 예상순위2)

    수행:
      1) LGBM p_sb 예측
      2) 예상순위_LGBM 계산
      3) exp011 테이블에 m_score = p_sb, m_rank = 예상순위_LGBM UPDATE 반영
      4) 전체 예측 DataFrame 반환
    """
    d = df_new.copy()

    # -----------------------------
    # 1) 타입 정리
    # -----------------------------
    d["경주일"] = d["경주일"].astype(str)
    d["경주번호"] = d["경주번호"].astype(int)
    d["마번"] = d["마번"].astype(int)
    d["예상순위1"] = d["예상순위1"].astype(int)
    d["예상순위2"] = d["예상순위2"].astype(int)

    if "경주거리" in d.columns:
        d["경주거리"] = d["경주거리"].astype(int)

    # -----------------------------
    # 2) Feature 생성 (학습과 동일)
    # -----------------------------
    d["rank_gap"] = d["예상순위2"] - d["예상순위1"]
    d["is_new"] = ((d["예상순위1"] >= 98) | (d["예상순위2"] >= 98)).astype(int)

    feature_cols = ["예상순위1", "예상순위2", "rank_gap", "is_new"]
    if "경주거리" in d.columns:
        feature_cols.append("경주거리")

    # -----------------------------
    # 3) LGBM 확률 추정 (상위3 들 확률)
    # -----------------------------
    d["p_sb"] = model.predict(d[feature_cols])

    # -----------------------------
    # 4) 경주별 의사순위 생성
    # -----------------------------
    d = d.sort_values(
        ["경마장", "경주일", "경주번호", "p_sb"], ascending=[True, True, True, False]
    )
    d["예상순위_LGBM"] = d.groupby(["경마장", "경주일", "경주번호"]).cumcount() + 1

    d = d.sort_values(["경마장", "경주일", "경주번호", "예상순위_LGBM"]).reset_index(
        drop=True
    )

    # -----------------------------
    # 5) exp011 DB UPDATE 처리
    # -----------------------------
    with conn.cursor() as cur:
        sql = """
            UPDATE The1.exp011
            SET m_score = %s,   -- p_sb 값 저장
                m_rank  = %s    -- LGBM 순위 저장
            WHERE rcity = %s
              AND rdate = %s
              AND rno   = %s
              AND gate  = %s
        """
        update_params = [
            (
                float(row["p_sb"]),
                int(row["예상순위_LGBM"]),
                row["경마장"],
                row["경주일"],
                int(row["경주번호"]),
                int(row["마번"]),
            )
            for _, row in d.iterrows()
        ]

        cur.executemany(sql, update_params)
        conn.commit()

    print("▶ exp011 테이블 m_score, m_rank 업데이트 완료!")

    return d


if __name__ == "__main__":
    conn = get_conn()

    try:
        # 1) DB에서 최신 모델 로드 시도
        model = load_latest_lgb_model_from_db(conn, model_name="sb_top3_v1")
    except ValueError:
        print("▶ DB에 모델이 없어서 새로 학습을 시작합니다...")
        conn.close()
        # 2) 없으면 학습 + 저장
        model = train_lgb_for_top3_from_db(
            from_date="20231201", model_name="sb_top3_v1"
        )
        # 3) 다시 연결해서 로드 (일관성을 위해)
        conn = get_conn()
        model = load_latest_lgb_model_from_db(conn, model_name="sb_top3_v1")

#     # 4) 새 경주 로드
#     df_new = load_new_races_from_db(conn, from_date="20251205")
#     conn.close()

#     # # 5) LGBM 상위 6두 예측
#     # top6_df = predict_top6_for_new_races(model, df_new)
#     # print("▶ 상위 6두 예측 예시")
#     # print(top6_df.head())

#     # # 6) LGBM 전체 예상순위(1위~꼴찌) 예측
#     # # full_rank_df = predict_full_rank_for_new_races(model, df_new)
#     conn = get_conn()
#     full_rank_df = predict_full_rank_for_new_races_and_update_db(conn, model, df_new)
#     print("▶ 전체 예상순위 예측 예시")
#     print(full_rank_df.head(20))

#     # 7) CSV로 저장
#     # top6_df.to_csv(
#     #     "/Users/Super007/Documents/new_races_top6_lgb_from_db.csv",
#     #     index=False,
#     #     encoding="utf-8-sig",
#     # )
#     full_rank_df.to_csv(
#         "/Users/Super007/Documents/new_races_full_rank_lgb_from_db.csv",
#         index=False,
#         encoding="utf-8-sig",
#     )
#     print("▶ CSV 저장 완료:")
#     print("  - 상위6두:", "/Users/Super007/Documents/new_races_top6_lgb_from_db.csv")
#     print(
#         "  - 전체순위:", "/Users/Super007/Documents/new_races_full_rank_lgb_from_db.csv"
#     )


def simulate_roi_with_lgb_rank(
    from_date: str = "20231201",
    model_name: str = "sb_top3_v1",
    exclude_new_races: bool = True,
    new_horse_threshold: int = 2,
    odds_cap: float = 500.0,
):
    """
    ▶ 학습/검증용 과거 데이터 + DB 저장된 LGBM 모델을 기반으로
       '예상순위_LGBM' 상위 6두를 써서 삼복/복승 ROI 시뮬레이션.

    - from_date: 학습/평가에 사용할 데이터 시작일(포함)
    - model_name: DB에 저장한 LightGBM 모델 이름
    - exclude_new_races:
        True  → 신마가 new_horse_threshold 두 이상인 경주는 아예 제외
        False → 신마 경주도 포함
    - new_horse_threshold:
        예: 2 라면, "신마가 2두 이상"인 경주는 제외 조건에 해당
    - odds_cap:
        삼복/복승 배당이 이 값 이상이면 환급금 0 처리 (초고배당 컷)
    """
    # 1) DB 연결 + 학습/평가용 데이터 로드
    conn = get_conn()
    df = load_train_data_from_db(conn, from_date=from_date)
    conn.close()

    # 타입 정리
    df = df.copy()
    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)

    df["예상순위1"] = df["예상순위1"].astype(int)
    df["예상순위2"] = df["예상순위2"].astype(int)
    df["실제순위"] = df["실제순위"].astype(int)

    if "경주거리" in df.columns:
        df["경주거리"] = df["경주거리"].astype(int)

    # 2) Feature 생성 (학습 때와 동일 규칙)
    df["rank_gap"] = df["예상순위2"] - df["예상순위1"]
    df["is_new"] = ((df["예상순위1"] >= 98) | (df["예상순위2"] >= 98)).astype(int)

    feature_cols = ["예상순위1", "예상순위2", "rank_gap", "is_new"]
    if "경주거리" in df.columns:
        feature_cols.append("경주거리")

    # 3) DB에서 LGBM 모델 로드
    conn = get_conn()
    model = load_latest_lgb_model_from_db(conn, model_name=model_name)
    conn.close()

    # 4) LGBM 확률 예측
    df["p_sb"] = model.predict(df[feature_cols])

    # 5) 경주별 예상순위_LGBM (p_sb 내림차순으로 1,2,3,...)
    df = df.sort_values(
        ["경마장", "경주일", "경주번호", "p_sb"],
        ascending=[True, True, True, False],
    )

    df["예상순위_LGBM"] = (
        df.groupby(["경마장", "경주일", "경주번호"]).cumcount().astype(int) + 1
    )

    # 6) 신마 두 수 집계(경주 단위)
    #    is_new == 1인 마필 수 (예상순위1/2 중 98 이상)
    race_new_count = (
        df.groupby(["경마장", "경주일", "경주번호"])["is_new"].sum().reset_index()
    )
    race_new_count = race_new_count.rename(columns={"is_new": "신마수"})

    df = df.merge(
        race_new_count,
        on=["경마장", "경주일", "경주번호"],
        how="left",
    )

    if exclude_new_races:
        # 신마수가 일정 기준 이상인 경주는 아예 제외
        before = df["경주번호"].nunique()
        df = df[df["신마수"] < new_horse_threshold].copy()
        after = df["경주번호"].nunique()
        print(f"▶ 신마 {new_horse_threshold}두 이상 경주 제외: {before} → {after} 경주")

    # 7) 경주별 삼복/복승 적중 & 환급 계산
    race_rows = []

    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()

        # 상위6 = 예상순위_LGBM 1~6위
        selected = g[g["예상순위_LGBM"] <= 6]["마번"].tolist()
        selected_set = set(selected)

        # 실제 상위3 / 상위2
        actual_top3 = g[g["실제순위"] <= 3]["마번"].tolist()
        actual_top2 = g[g["실제순위"] <= 2]["마번"].tolist()
        actual_top3_set = set(actual_top3)
        actual_top2_set = set(actual_top2)

        # 적중 여부
        sb_hit = int(actual_top3_set.issubset(selected_set)) if actual_top3_set else 0
        bs_hit = int(actual_top2_set.issubset(selected_set)) if actual_top2_set else 0

        # 배당율 (경주별로 동일 가정)
        sb_odds = (
            float(g["삼복승식배당율"].iloc[0]) if "삼복승식배당율" in g.columns else 0.0
        )
        bs_odds = (
            float(g["복승식배당율"].iloc[0]) if "복승식배당율" in g.columns else 0.0
        )

        # 500배 이상 컷
        if sb_hit == 1 and sb_odds < odds_cap:
            sb_refund = sb_odds * 100.0
        else:
            sb_refund = 0.0

        if bs_hit == 1 and bs_odds < odds_cap:
            bs_refund = bs_odds * 100.0
        else:
            bs_refund = 0.0

        race_rows.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "신마수": int(g["신마수"].iloc[0]),
                "선택_상위6_LGBM_마번": ",".join(map(str, sorted(selected_set))),
                "실제_1_3위_마번": (
                    ",".join(map(str, sorted(actual_top3_set)))
                    if actual_top3_set
                    else ""
                ),
                "실제_1_2위_마번": (
                    ",".join(map(str, sorted(actual_top2_set)))
                    if actual_top2_set
                    else ""
                ),
                "삼복_적중": sb_hit,
                "삼복_환급금": sb_refund,
                "복승_적중": bs_hit,
                "복승_환급금": bs_refund,
                "삼복승식배당율": sb_odds,
                "복승식배당율": bs_odds,
            }
        )

    race_df = pd.DataFrame(race_rows)

    # 8) ROI 계산 (6복조 기준)
    total_races = len(race_df)
    print(f"▶ ROI 계산 대상 경주수: {total_races}")

    # 삼복: 6복조 → 20구멍 * 100원 = 2,000원 / 경주
    sb_bet_per_race = 20 * 100
    sb_total_bet = total_races * sb_bet_per_race
    sb_total_refund = race_df["삼복_환급금"].sum()
    sb_roi = (
        (sb_total_refund - sb_total_bet) / sb_total_bet if sb_total_bet > 0 else 0.0
    )

    # 복승: 6두 2마리 조합 → 15구멍 * 100원 = 1,500원 / 경주
    bs_bet_per_race = 15 * 100
    bs_total_bet = total_races * bs_bet_per_race
    bs_total_refund = race_df["복승_환급금"].sum()
    bs_roi = (
        (bs_total_refund - bs_total_bet) / bs_total_bet if bs_total_bet > 0 else 0.0
    )

    print("===================================")
    print(f"총 경주수: {total_races}")
    print(
        f"[삼복] 총베팅액: {sb_total_bet:,}  총환급액: {sb_total_refund:,.1f}  ROI: {sb_roi:.3f}"
    )
    print(
        f"[복승] 총베팅액: {bs_total_bet:,}  총환급액: {bs_total_refund:,.1f}  ROI: {bs_roi:.3f}"
    )
    print("===================================")

    return race_df, sb_roi, bs_roi


if __name__ == "__main__":
    # 1) 먼저 LGBM 모델이 DB에 없다면 한 번 학습해서 저장
    #    (한 번 저장해두면 이후에는 생략 가능)
    # train_lgb_for_top3_from_db(from_date="20241129", model_name="sb_top3_v1")

    # 2) LGBM 순위 기반 삼복/복승 ROI 시뮬레이션 실행
    race_df, sb_roi, bs_roi = simulate_roi_with_lgb_rank(
        from_date="20231201",
        model_name="sb_top3_v1",
        exclude_new_races=True,  # 신마 2두 이상 경주 제외
        new_horse_threshold=2,
        odds_cap=500.0,  # 500배 이상 환급 0 처리
    )

    # 3) 경주별 raw 결과 저장
    out_path = "/Users/Super007/Documents/lgb_rank_top6_roi_result.csv"
    race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"▶ 경주별 LGBM 순위 기반 ROI 결과 CSV 저장 완료: {out_path}")
