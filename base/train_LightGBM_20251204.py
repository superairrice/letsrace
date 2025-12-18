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
    """Django DATABASES['default']에서 MySQL 설정을 읽어온다 (있으면)."""
    try:
        import django
        from django.conf import settings

        if not settings.configured:
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
        if "ssl" in opts:
            conf["ssl"] = opts["ssl"]
        return conf
    except Exception:
        return None


def _get_db_conf_from_env():
    """MYSQL_* 환경변수에서 DB 설정을 읽어온다."""
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
    """Django 설정 또는 환경변수 기반으로 PyMySQL 커넥션 획득."""
    conf = _get_db_conf_from_django() or _get_db_conf_from_env()
    if conf is None:
        raise RuntimeError(
            "Database configuration not found. "
            "Set DJANGO_SETTINGS_MODULE or export MYSQL_* env vars."
        )

    conn = pymysql.connect(**conf)
    try:
        conn.ping(reconnect=True)
    except Exception:
        pass
    return conn


# =========================
# 2. 모델 저장용 테이블
# =========================


def _ensure_lgb_models_table(conn):
    """lgb_models 테이블이 없으면 생성."""
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


def save_lgb_model_to_db(conn, model: lgb.Booster, model_name: str, comment: str = ""):
    """학습한 LightGBM Booster를 lgb_models 테이블에 문자열로 저장."""
    _ensure_lgb_models_table(conn)
    model_str = model.model_to_string()

    with conn.cursor() as cur:
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


# =========================
# 3. 데이터 로드
# =========================


def load_train_data_from_db(
    conn,
    from_date: str,
    to_date: str,
) -> pd.DataFrame:
    """
    학습용 데이터 로드: exp011 + exp010 + rec010
    (실제순위가 있는 과거 경주)
    """
    sql = """
    SELECT
        e.rcity      AS 경마장,
        e.rdate      AS 경주일,
        e.rno        AS 경주번호,
        x.distance   AS 경주거리,
        e.gate       AS 마번,
        e.rank       AS 예상순위1,
        e.r_pop      AS 예상순위2,
        e.r_rank     AS 실제순위
    FROM The1.exp011 AS e
    LEFT JOIN The1.exp010 AS x
           ON x.rcity = e.rcity
          AND x.rdate = e.rdate
          AND x.rno   = e.rno
    WHERE e.rdate >= %s
      AND e.rdate <= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    df = pd.read_sql(sql, conn, params=[from_date, to_date])
    return df


def load_new_races_from_db(
    conn,
    from_date: str,
    to_date: str,
) -> pd.DataFrame:
    """
    예측 대상 데이터 로드:
      - 실제순위 없이, exp011에 예상순위만 있는 데이터를 그 기간만큼 가져옴.
      - 여기서는 같은 기간(from~to)을 대상으로 m_score/m_rank 업데이트에 사용.
    """
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
      AND e.rdate <= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    df = pd.read_sql(sql, conn, params=[from_date, to_date])
    return df


# =========================
# 4. Feature 준비
# =========================


def _prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """경주 관련 공통 컬럼 dtype 정리 및 feature_cols 생성."""
    d = df.copy()

    # 기본 타입 정리
    if "경주일" in d.columns:
        d["경주일"] = d["경주일"].astype(str)

    for col in ("경주번호", "마번", "예상순위1", "예상순위2", "경주거리"):
        if col in d.columns:
            d[col] = d[col].astype(int)

    # Feature 생성
    d["rank_gap"] = d["예상순위2"] - d["예상순위1"]
    d["is_new"] = ((d["예상순위1"] >= 98) | (d["예상순위2"] >= 98)).astype(int)

    feature_cols: List[str] = [
        col
        for col in ["예상순위1", "예상순위2", "rank_gap", "is_new", "경주거리"]
        if col in d.columns
    ]
    return d, feature_cols


# =========================
# 5. 예측 + exp011 업데이트
# =========================


def predict_full_rank_for_new_races_and_update_db(
    conn,
    model: lgb.Booster,
    df_new: pd.DataFrame,
) -> pd.DataFrame:
    """
    df_new: (경마장, 경주일, 경주번호, 경주거리, 마번, 예상순위1, 예상순위2)

    수행:
      1) LGBM으로 p_sb(상위3위 안에 들 확률) 예측
      2) p_sb 기준 경주별 예상순위_LGBM 계산
      3) exp011.m_score = p_sb, exp011.m_rank = 예상순위_LGBM 으로 UPDATE
      4) 전체 예측 DataFrame 반환
    """
    d, feature_cols = _prepare_features(df_new)

    # 1) 확률 예측
    d["p_sb"] = model.predict(d[feature_cols])

    # 2) 경주별 내림차순 정렬 후 예상순위 부여
    d = d.sort_values(
        ["경마장", "경주일", "경주번호", "p_sb"],
        ascending=[True, True, True, False],
    )
    d["예상순위_LGBM"] = (
        d.groupby(["경마장", "경주일", "경주번호"]).cumcount().astype(int) + 1
    )

    d = d.sort_values(["경마장", "경주일", "경주번호", "예상순위_LGBM"]).reset_index(
        drop=True
    )

    # 3) exp011 UPDATE
    with conn.cursor() as cur:
        sql = """
            UPDATE The1.exp011
            SET m_score = %s,
                m_rank  = %s
            WHERE rcity = %s
              AND rdate = %s
              AND rno   = %s
              AND gate  = %s
        """
        params = [
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
        cur.executemany(sql, params)
        conn.commit()

    print("▶ exp011 테이블 m_score, m_rank 업데이트 완료!")
    return d


# =========================
# 6. 메인: 기간 모델 학습 + 그 기간 exp011 업데이트
# =========================


def train_model_for_period_and_update_exp011(
    from_date: str,
    to_date: str,
    model_name: str = "sb_top3_period",
) -> lgb.Booster:
    """
    기간(from_date ~ to_date) 데이터로 새 LGBM 모델을 학습하고,
    같은 기간 exp011의 m_score, m_rank를 업데이트한다.

    - from_date, to_date: 'YYYYMMDD' 문자열
    - model_name: lgb_models 테이블에 저장할 모델 이름
    """
    # 1) 학습 데이터 로드 + 모델 학습
    with closing(get_conn()) as conn:
        df_train = load_train_data_from_db(conn, from_date=from_date, to_date=to_date)

        if df_train.empty:
            raise ValueError(f"[{from_date} ~ {to_date}] 학습용 데이터가 없습니다.")

        df_train, feature_cols = _prepare_features(df_train)

        df_train["실제순위"] = df_train["실제순위"].astype(int)
        df_train["label_sb"] = (df_train["실제순위"] <= 3).astype(int)

        train_set = lgb.Dataset(df_train[feature_cols], label=df_train["label_sb"])

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

        print(f"▶ [{from_date} ~ {to_date}] 기간 LightGBM 학습 시작...")
        model = lgb.train(params, train_set, num_boost_round=400)
        print("▶ 학습 완료.")

        # 모델 저장 (옵션이지만 유용하므로 유지)
        save_lgb_model_to_db(
            conn,
            model,
            model_name,
            comment=f"{from_date}~{to_date} 데이터로 학습",
        )

    # 2) 같은 기간 exp011에 대해 m_score/m_rank 업데이트
    with closing(get_conn()) as conn:
        df_new = load_new_races_from_db(conn, from_date=from_date, to_date=to_date)

        if df_new.empty:
            print(
                f"▶ [{from_date} ~ {to_date}] 기간 exp011 데이터가 없습니다. UPDATE 생략."
            )
            return model

        predict_full_rank_for_new_races_and_update_db(conn, model, df_new)

    print(
        f"▶ [{from_date} ~ {to_date}] 기간 모델 학습 및 exp011(m_score, m_rank) 업데이트 완료."
    )
    return model


# =========================
# 7. 예시 실행
# =========================

# if __name__ == "__main__":
#     # 예시: 2024년 1월~3월 데이터로 모델 만들고 그 기간 exp011 업데이트
#     train_model_for_period_and_update_exp011(
#         from_date="20231201",
#         to_date="20251130",
#         model_name="sb_top3_20231201_20251130",
#     )


def load_latest_lgb_model_from_db(conn, model_name: str) -> lgb.Booster:
    """
    lgb_models 테이블에서 주어진 model_name의 최신 버전 모델을 로드하여
    LightGBM Booster 객체로 반환.
    """
    sql = """
        SELECT model_text
        FROM lgb_models
        WHERE model_name = %s
        ORDER BY version DESC
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, (model_name,))
        row = cur.fetchone()

    if not row:
        raise ValueError(
            f"[{model_name}] 이름의 모델을 lgb_models에서 찾을 수 없습니다."
        )

    model_text = row["model_text"]
    booster = lgb.Booster(model_str=model_text)
    print(f"▶ 모델 [{model_name}] 최신 버전 로드 완료.")
    return booster


def update_m_rank_score_for_period(
    from_date: str,
    to_date: str,
    model_name: str = "sb_top3_period",
):
    """
    특정 기간(from_date ~ to_date)에 대해
    exp011의 m_score, m_rank를 갱신한다.

    - 이미 DB(lgb_models)에 저장된 model_name의 최신 버전 모델을 불러와 사용.
    - exp011 + exp010에서 해당 기간의 경주를 모두 가져와서
      p_sb(3위 이내 확률)를 예측하고, 경주별로 내림차순 정렬하여 m_rank를 부여.

    from_date, to_date: 'YYYYMMDD' 문자열
    """
    with closing(get_conn()) as conn:
        # 1) 최신 모델 로드
        model = load_latest_lgb_model_from_db(conn, model_name)

        # 2) 대상 기간 exp011(예측용) 데이터 로드
        df_new = load_new_races_from_db(conn, from_date=from_date, to_date=to_date)

        if df_new.empty:
            print(
                f"▶ [{from_date} ~ {to_date}] 기간 exp011 데이터가 없습니다. UPDATE 생략."
            )
            return

        # 3) feature 준비
        d, feature_cols = _prepare_features(df_new)

        # 4) LightGBM으로 상위3위 진입 확률 p_sb 예측
        d["p_sb"] = model.predict(d[feature_cols])

        # 5) 경주별(p_sb 내림차순)로 예상순위_LGBM 부여
        d = d.sort_values(
            ["경마장", "경주일", "경주번호", "p_sb"],
            ascending=[True, True, True, False],
        )
        d["예상순위_LGBM"] = (
            d.groupby(["경마장", "경주일", "경주번호"]).cumcount().astype(int) + 1
        )

        d = d.sort_values(
            ["경마장", "경주일", "경주번호", "예상순위_LGBM"]
        ).reset_index(drop=True)

        # 6) exp011 UPDATE
        with conn.cursor() as cur:
            sql = """
                UPDATE The1.exp011
                SET m_score = %s,
                    m_rank  = %s
                WHERE rcity = %s
                  AND rdate = %s
                  AND rno   = %s
                  AND gate  = %s
            """
            params = [
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
            cur.executemany(sql, params)
            conn.commit()

        print(
            f"▶ [{from_date} ~ {to_date}] 기간 exp011(m_score, m_rank) 업데이트 완료. "
            f"(총 {len(d)}건)"
        )
        return d


def update_m_rank_score_for_race(
    rcity: str,
    rdate: str,
    rno: int,
    model_name: str = "sb_top3_period",
):
    """
    단일 경주(경마장, 경주일, 경주번호)에 대해
    exp011의 m_score / m_rank만 갱신하는 유틸 함수.

    1) DB에서 최신 LightGBM 모델 로드
    2) 해당 경주의 exp011 + exp010 데이터 로드
    3) _prepare_features → p_sb 예측
    4) p_sb 기준 내림차순으로 m_rank 재계산
    5) exp011(m_score, m_rank) UPDATE
    """
    with closing(get_conn()) as conn:
        # 1) 최신 모델 로드
        model = load_latest_lgb_model_from_db(conn, model_name)

        # 2) 해당 경주 데이터 로드
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
        WHERE e.rcity = %s
          AND e.rdate = %s
          AND e.rno   = %s
        ORDER BY e.gate
        """
        df_new = pd.read_sql(sql, conn, params=[rcity, rdate, rno])

        if df_new.empty:
            print(f"▶ [{rcity} {rdate} {rno}] 경주의 exp011 데이터가 없습니다.")
            return

        # 3) 피처 준비 + 예측
        d, feature_cols = _prepare_features(df_new)

        d["p_sb"] = model.predict(d[feature_cols])

        # 4) p_sb 기준 내림차순 정렬 후 예상순위 부여
        d = d.sort_values(
            ["경마장", "경주일", "경주번호", "p_sb"],
            ascending=[True, True, True, False],
        )
        d["예상순위_LGBM"] = (
            d.groupby(["경마장", "경주일", "경주번호"]).cumcount().astype(int) + 1
        )

        d = d.sort_values(
            ["경마장", "경주일", "경주번호", "예상순위_LGBM"]
        ).reset_index(drop=True)

        # 5) exp011 UPDATE
        with conn.cursor() as cur:
            upd_sql = """
                UPDATE The1.exp011
                SET m_score = %s,
                    m_rank  = %s
                WHERE rcity = %s
                  AND rdate = %s
                  AND rno   = %s
                  AND gate  = %s
            """
            params = [
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
            cur.executemany(upd_sql, params)
            conn.commit()

        print(f"▶ [{rcity} {rdate} {rno}] m_score, m_rank 업데이트 완료.")
        return d


# if __name__ == "__main__":
#     # 예: 서울 20251119 11경주만 m_score/m_rank 재계산
#     update_m_rank_score_for_race(
#         rcity="부산",
#         rdate="20251205",
#         rno=1,
#         model_name="sb_top3_20231201_20251130",  # 저장해둔 모델 이름
#     )

if __name__ == "__main__":
    update_m_rank_score_for_period(
        from_date="20251205",
        to_date="20251207",
        model_name="sb_top3_20231201_20251130",
    )
