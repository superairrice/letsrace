import pandas as pd
from sqlalchemy import create_engine, text
from typing import Dict, Optional
from itertools import combinations
import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


STRATEGY_TRACK_SECTION_LABEL = "[베팅방법별 경마장별]"
SHOW_TRACK_NAME_IN_STRATEGY_SECTION = True
COMBINE_STRATEGY_AND_TRACK_LINE = False
SHOW_MONTHLY_STRATEGY_OUTPUT = True
EXCLUDED_STRATEGY_KEYS = set()

STRATEGY_RESULT_COLUMNS = {
    "anchor1_24_quinella": {
        "bet": "1축_2~4_복승_베팅액",
        "refund": "1축_2~4_복승_환수액",
        "hit": "r_pop1_축_2~4_복승_적중",
    },
    "top3pair_46_quinella": {
        "bet": "1~3_복조축_4~6_복승_베팅액",
        "refund": "1~3_복조축_4~6_복승_환수액",
        "hit": "r_pop1~3_복조축_4~6_복승_적중",
    },
    "anchor12_3_5_quinella": {
        "bet": "1,2축_3~5_복승_베팅액",
        "refund": "1,2축_3~5_복승_환수액",
        "hit": "r_pop1,2_축_3~5_복승_적중",
    },
    "anchor12_3_4_quinella": {
        "bet": "1,2축_3~4_복승_베팅액",
        "refund": "1,2축_3~4_복승_환수액",
        "hit": "r_pop1,2_축_3~4_복승_적중",
    },
    "anchor1_24_58": {
        "bet": "1축_2~4_5~8_베팅액",
        "refund": "1축_2~4_5~8_환수액",
        "hit": "r_pop1_축_2~4_5~8_적중",
    },
    "anchor1_58_24": {
        "bet": "1축_5~8_2~4_베팅액",
        "refund": "1축_5~8_2~4_환수액",
        "hit": "r_pop1_축_5~8_2~4_적중",
    },
    "anchor1_25": {
        "bet": "1축_2~5_베팅액",
        "refund": "1축_2~5_환수액",
        "hit": "r_pop1_축_2~5_적중",
    },
    "anchor1_23_46": {
        "bet": "1축_2~3_4~6_베팅액",
        "refund": "1축_2~3_4~6_환수액",
        "hit": "r_pop1_축_2~3_4~6_적중",
    },
    "anchor1_23_47": {
        "bet": "1축_2~3_4~7_베팅액",
        "refund": "1축_2~3_4~7_환수액",
        "hit": "r_pop1_축_2~3_4~7_적중",
    },
    "anchor1_23_48": {
        "bet": "1축_2~3_4~8_베팅액",
        "refund": "1축_2~3_4~8_환수액",
        "hit": "r_pop1_축_2~3_4~8_적중",
    },
    "anchor12_3_7": {
        "bet": "1축_2축_3~7_베팅액",
        "refund": "1축_2축_3~7_환수액",
        "hit": "r_pop1_1축_r_pop2_2축_3~7_적중",
    },
    "top4_box_trifecta": {
        "bet": "1~4_4복_베팅액",
        "refund": "1~4_4복_환수액",
        "hit": "r_pop1~4_4복_적중",
    },
}

SATURDAY_COMBO_PRESETS = {
    "보수형": [
        "anchor1_25",
        "anchor1_24_58",
        "anchor1_58_24",
        "anchor12_3_7",
    ],
    "균형형": [
        "anchor1_25",
        "anchor1_23_47",
        "anchor1_23_48",
        "anchor1_24_58",
        "anchor1_58_24",
        "anchor12_3_7",
    ],
    "공격형": [
        "anchor1_25",
        "anchor1_23_46",
        "anchor1_23_47",
        "anchor1_23_48",
    ],
}

STRATEGY_LABELS = {
    "anchor1_24_quinella": "[복승식 r_pop 1축 / 2~4]",
    "anchor1_26_quinella": "[복승식 r_pop 1축 / 2~6]",
    "top3pair_46_quinella": "[복승식 r_pop 1~3 복조 축 / 4~6]",
    "anchor12_3_4_quinella": "[복승식 r_pop 1~2 복조축 / 3~4]",
    "anchor12_3_5_quinella": "[복승식 r_pop 1~2 복조축 / 3~5]",
    "anchor12_3_6_quinella": "[복승식 r_pop 1,2 축 / 3~6]",
    "anchor12_3_7_quinella": "[복승식 r_pop 1,2 축 / 3~7]",
    "anchor12_3_8_quinella": "[복승식 r_pop 1,2 축 / 3~8]",
    "anchor12_3_12_quinella": "[복승식 r_pop 1,2 축 / 3~12]",
    "anchor1_24_57": "[r_pop 1축(2~4) 2등/5~7 3등 삼쌍승식]",
    "anchor1_24_58": "[r_pop 1축(2~4) 2등/5~8 3등 삼쌍승식]",
    "top4_box_trifecta": "[r_pop 1~4 삼쌍승식 4복]",
    "top5_box_trifecta": "[r_pop 1~5 삼쌍승식 5복]",
    "top6_trio": "[r_pop 1~6 삼복승식 6복조]",
    "top3pair_46_trio": "[r_pop 1~3 복조 / 4~6 삼복승식]",
    "top3pair_47_trio": "[r_pop 1~3 복조 / 4~7 삼복승식]",
    "top3pair_49_trio": "[r_pop 1~3 복조 / 4~9 삼복승식]",
    "top4pair_58_trio": "[r_pop 1~4 복조 / 5~8 삼복승식]",
    "top12anchor_3_10_trio": "[r_pop 1~2 복조 축 / 3~10 삼복승식]",
    "top12anchor_3_8_12_trio": "[r_pop 1~2 복조 축 / 3~8,12 삼복승식]",
    "top12anchor_3_12_trio": "[r_pop 1~2 복조 축 / 3~12 삼복승식]",
    "anchor1_57_24": "[r_pop 1축(5~7) 2등/2~4 3등 삼쌍승식]",
    "anchor1_58_24": "[r_pop 1축(5~8) 2등/2~4 3등 삼쌍승식]",
    "anchor3_24": "[r_pop 1을 3축 / 2~4를 1~2축 삼쌍승식]",
    "anchor2_24": "[r_pop 1을 2축 / 2~4를 1,3축 삼쌍승식]",
    "anchor1_24": "[r_pop 1축(2~4) 3복조 삼쌍승식]",
    "anchor1_25": "[r_pop 1축(2~5) 4복조 삼쌍승식]",
    "anchor1_25_68": "[r_pop 1축(2~5) 2등/6~8 3등 삼쌍승식]",
    "anchor1_25_69": "[r_pop 1축(2~5) 2등/6~9 3등 삼쌍승식]",
    "anchor1_69_25": "[r_pop 1축(6~9) 2등/2~5 3등 삼쌍승식]",
    "anchor1_23_46": "[r_pop 1축(2~3) 2등/4~6 3등 삼쌍승식]",
    "anchor1_23_47": "[r_pop 1축(2~3) 2등/4~7 3등 삼쌍승식]",
    "anchor1_23_48": "[r_pop 1축(2~3) 2등/4~8 3등 삼쌍승식]",
    "anchor1_23_49": "[r_pop 1축(2~3) 2등/4~9 3등 삼쌍승식]",
    "anchor12_3_7": "[r_pop 1축, 2 2축, 3~7 3등 삼쌍승식]",
    "anchor12_3_10": "[r_pop 1축, 2 2축, 3~10 3등 삼쌍승식]",
}


# =========================
# 0. DB 접속 설정 (필요에 맞게 수정)
# =========================
DEFAULT_DB_CONF = {
    "host": "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",
    "port": 3306,
    "user": "letslove",
    "password": "Ruddksp!23",
    "db": "The1",
    "charset": "utf8mb4",
}


def _load_django_db_conf() -> Optional[Dict[str, object]]:
    """letsrace.settings 의 DATABASES 기본값을 우선 사용한다."""
    settings_module = os.getenv("DJANGO_SETTINGS_MODULE", "").strip()
    candidate_modules = ["letsrace.settings"]
    if settings_module and settings_module not in candidate_modules:
        candidate_modules.append(settings_module)
    if "letsrace.settings_dev" not in candidate_modules:
        candidate_modules.append("letsrace.settings_dev")

    for module_name in candidate_modules:
        try:
            settings_mod = importlib.import_module(module_name)
            default_db = getattr(settings_mod, "DATABASES", {}).get("default", {})
            engine = str(default_db.get("ENGINE", "") or "").strip()
            if engine != "django.db.backends.mysql":
                continue

            name = str(default_db.get("NAME", "") or "").strip()
            user = str(default_db.get("USER", "") or "").strip()
            password = str(default_db.get("PASSWORD", "") or "")
            host = str(default_db.get("HOST", "") or "").strip()
            if not all([name, user, host]):
                continue

            port = default_db.get("PORT") or 3306
            return {
                "host": host,
                "port": int(port),
                "user": user,
                "password": password,
                "db": name,
                "charset": "utf8mb4",
            }
        except Exception:
            continue
    return None


DB_CONF = _load_django_db_conf() or DEFAULT_DB_CONF


def get_db_conf() -> Dict[str, object]:
    """현재 환경 기준 DB 설정을 반환하고 전역 캐시도 갱신한다."""
    global DB_CONF
    DB_CONF = _load_django_db_conf() or DEFAULT_DB_CONF
    return DB_CONF


def get_engine():
    """SQLAlchemy 엔진 생성."""
    db_conf = get_db_conf()
    print(
        f"[DB] host={db_conf['host']} port={db_conf['port']} "
        f"db={db_conf['db']} user={db_conf['user']}"
    )
    url = (
        f"mysql+pymysql://{db_conf['user']}:{db_conf['password']}"
        f"@{db_conf['host']}:{db_conf['port']}/{db_conf['db']}?charset={db_conf['charset']}"
    )
    return create_engine(url, pool_pre_ping=True)


# =========================
# 1. 기간별 결과 데이터 로드
# =========================
def load_result_data_from_db(
    engine,
    from_date: str,
    to_date: str,
) -> pd.DataFrame:
    """
    기간(from_date ~ to_date) 동안의 결과 데이터 로드.
    r_pop(예상), r_rank(실제순위), 삼복승식/삼쌍승식/복승식 배당 포함.
    """
    sql = text(
        """
    SELECT
        e.rcity      AS 경마장,
        e.rdate      AS 경주일,
        e.rno        AS 경주번호,
        e.gate       AS 마번,
        r.distance   AS 경주거리,
        x.grade      AS 등급,
        e.rank       AS rank,       -- 예상순위(rank)
        e.r_pop      AS r_pop,      -- 예상순위(r_pop)
        e.r_rank     AS r_rank,     -- 실제순위
        CAST(r.r2alloc1 AS DECIMAL(10, 1)) AS 복승식배당율,
        CAST(SUBSTRING(r.r333alloc, 4) AS DECIMAL(10, 1)) AS 삼복승식배당율,
        CAST(SUBSTRING(r.r123alloc, 4) AS DECIMAL(10, 1)) AS 삼쌍승식배당율
    FROM The1.exp011 AS e
    LEFT JOIN The1.rec010 AS r
           ON r.rcity = e.rcity
          AND r.rdate = e.rdate
          AND r.rno   = e.rno
    LEFT JOIN The1.exp010 AS x
           ON x.rcity = e.rcity
          AND x.rdate = e.rdate
          AND x.rno   = e.rno
    WHERE e.rdate >= :from_date
      AND e.rdate <= :to_date
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    )
    with engine.connect() as conn:
        return pd.read_sql(
            sql, conn, params={"from_date": from_date, "to_date": to_date}
        )


def upsert_weekly_betting_summary(engine, week_df: pd.DataFrame) -> None:
    if week_df.empty:
        return
    with engine.begin() as conn:
        cols = conn.execute(text("SHOW COLUMNS FROM weekly_betting_summary")).fetchall()

        # SHOW COLUMNS returns: Field, Type, Null, Key, Default, Extra
        col_names = {row[0].lower(): row[0] for row in cols}
        required_cols = {
            row[0]
            for row in cols
            if row[2] == "NO"
            and row[4] is None
            and "auto_increment" not in (row[5] or "")
        }
        date_candidates = [
            "week_date",
            "week",
            "week_key",
            "weekend",
            "week_start",
            "week_end",
            "week_ymd",
            "sat_date",
            "sat",
        ]
        date_col = next((col_names[c] for c in date_candidates if c in col_names), None)
        if not date_col:
            print("⚠️ weekly_betting_summary 날짜 컬럼을 찾지 못했습니다.")
            print(f"   available columns: {sorted(col_names.values())}")
            return

        col_map = {
            "토요일기준일": date_col,
            "경마장": next(
                (
                    col_names[c]
                    for c in ["track", "rcity", "race_track", "track_name"]
                    if c in col_names
                ),
                None,
            ),
            "경주수": next(
                (
                    col_names[c]
                    for c in ["races", "race_count", "race_cnt", "cnt"]
                    if c in col_names
                ),
                None,
            ),
            "총베팅액": next(
                (
                    col_names[c]
                    for c in ["total_bet", "bet_total", "bet_amount"]
                    if c in col_names
                ),
                None,
            ),
            "총환수액": next(
                (
                    col_names[c]
                    for c in ["total_refund", "refund_total", "refund_amount"]
                    if c in col_names
                ),
                None,
            ),
            "이익금액": next(
                (
                    col_names[c]
                    for c in ["profit", "profit_amount", "benefit", "net_profit"]
                    if c in col_names
                ),
                None,
            ),
            "환수율": next(
                (
                    col_names[c]
                    for c in ["refund_rate", "roi", "return_rate"]
                    if c in col_names
                ),
                None,
            ),
            "적중경주수": next(
                (
                    col_names[c]
                    for c in ["hit_race_cnt", "hits", "hit_count", "hit_cnt"]
                    if c in col_names
                ),
                None,
            ),
            "적중율": next(
                (col_names[c] for c in ["hit_rate", "hit_ratio"] if c in col_names),
                None,
            ),
        }
        col_map = {k: v for k, v in col_map.items() if v}
        week_df_db = week_df.rename(columns=col_map)[list(col_map.values())]

        track_col = col_map.get("경마장")
        if "경마장" in week_df.columns and not track_col:
            print("⚠️ weekly_betting_summary 경마장 컬럼이 없어 날짜 기준으로 합산 후 upsert 합니다.")
            metric_cols = [
                c
                for c in [
                    "경주수",
                    "총베팅액",
                    "총환수액",
                    "이익금액",
                    "적중경주수",
                ]
                if c in week_df.columns
            ]
            rate_cols = [c for c in ["환수율", "적중율"] if c in week_df.columns]
            grouped = (
                week_df.groupby("토요일기준일", dropna=False)[metric_cols].sum().reset_index()
                if metric_cols
                else week_df[["토요일기준일"]].drop_duplicates()
            )
            for rate_col in rate_cols:
                if rate_col == "환수율":
                    grouped[rate_col] = grouped.apply(
                        lambda r: (r["총환수액"] / r["총베팅액"]) if r.get("총베팅액", 0) else 0.0,
                        axis=1,
                    )
                elif rate_col == "적중율":
                    grouped[rate_col] = grouped.apply(
                        lambda r: (r["적중경주수"] / r["경주수"]) if r.get("경주수", 0) else 0.0,
                        axis=1,
                    )
            week_df_db = grouped.rename(columns=col_map)[list(col_map.values())]

        missing_required = [c for c in required_cols if c not in week_df_db.columns]
        if missing_required:
            print("⚠️ weekly_betting_summary 필수 컬럼 매핑이 누락되었습니다.")
            print(f"   missing required columns: {sorted(missing_required)}")
            print(f"   available columns: {sorted(col_names.values())}")
            return

        preferred_order = [
            date_col,
            col_names.get("race_cnt"),
            col_names.get("bet_amount"),
            col_names.get("refund_amount"),
            col_names.get("profit_amount"),
            col_names.get("roi"),
            col_names.get("hit_race_cnt"),
            col_names.get("hit_rate"),
        ]
        preferred_order = [c for c in preferred_order if c in week_df_db.columns]
        insert_cols = preferred_order if preferred_order else list(week_df_db.columns)
        week_df_db = week_df_db[insert_cols]

        for int_col in [
            "race_cnt",
            "bet_amount",
            "refund_amount",
            "profit_amount",
            "hit_race_cnt",
        ]:
            col = col_names.get(int_col)
            if col in week_df_db.columns:
                week_df_db[col] = week_df_db[col].round(0).astype(int)
        value_cols = ", ".join(insert_cols)
        value_params = ", ".join(f":{c}" for c in insert_cols)
        update_cols = [c for c in insert_cols if c != date_col]
        update_sql = ", ".join(f"{c} = VALUES({c})" for c in update_cols)
        upsert_sql = text(
            f"""
            INSERT INTO weekly_betting_summary ({value_cols})
            VALUES ({value_params})
            ON DUPLICATE KEY UPDATE {update_sql}
            """
        )
        conn.execute(upsert_sql, week_df_db.to_dict(orient="records"))


def print_saturday_combo_backtest(
    race_df: pd.DataFrame,
    section_title: str = "[토요일 기준 전략 조합 백테스트]",
    combo_presets: Optional[Dict[str, list]] = None,
) -> None:
    if race_df.empty:
        return

    combo_presets = combo_presets or SATURDAY_COMBO_PRESETS
    df = race_df.copy()
    df["경주일"] = pd.to_datetime(df["경주일"].astype(str), format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["경주일"]).copy()
    if df.empty:
        return

    df["토요일기준일"] = df["경주일"] + pd.to_timedelta(5 - df["경주일"].dt.weekday, unit="D")
    print(section_title)

    printed = False
    for combo_name, strategy_keys in combo_presets.items():
        active_keys = [
            key
            for key in strategy_keys
            if key not in EXCLUDED_STRATEGY_KEYS and key in STRATEGY_RESULT_COLUMNS
        ]
        if not active_keys:
            continue

        bet_cols = [STRATEGY_RESULT_COLUMNS[key]["bet"] for key in active_keys]
        refund_cols = [STRATEGY_RESULT_COLUMNS[key]["refund"] for key in active_keys]
        hit_cols = [STRATEGY_RESULT_COLUMNS[key]["hit"] for key in active_keys]
        if not all(col in df.columns for col in bet_cols + refund_cols + hit_cols):
            continue

        combo_df = df[["토요일기준일"] + bet_cols + refund_cols + hit_cols].copy()
        combo_df["총베팅액"] = combo_df[bet_cols].sum(axis=1)
        combo_df["총환수액"] = combo_df[refund_cols].sum(axis=1)
        combo_df["적중경주"] = combo_df[hit_cols].max(axis=1)
        weekly = (
            combo_df.groupby("토요일기준일", dropna=False)[["총베팅액", "총환수액", "적중경주"]]
            .sum()
            .reset_index()
            .sort_values("토요일기준일")
        )
        weekly = weekly[weekly["총베팅액"] > 0].copy()
        if weekly.empty:
            continue

        weekly["이익금액"] = weekly["총환수액"] - weekly["총베팅액"]
        weekly["환수율"] = weekly["총환수액"] / weekly["총베팅액"]
        losing_weeks = int((weekly["이익금액"] < 0).sum())
        profitable_weeks = int((weekly["이익금액"] > 0).sum())
        flat_weeks = int((weekly["이익금액"] == 0).sum())
        total_bet = float(weekly["총베팅액"].sum())
        total_refund = float(weekly["총환수액"].sum())
        total_profit = total_refund - total_bet
        total_roi = total_refund / total_bet if total_bet > 0 else 0.0
        median_roi = float(weekly["환수율"].median())
        worst_roi = float(weekly["환수율"].min())
        best_roi = float(weekly["환수율"].max())
        losing_rate = losing_weeks / len(weekly) if len(weekly) > 0 else 0.0
        total_hit_races = int(combo_df["적중경주"].sum())
        total_races = len(combo_df)
        hit_rate = total_hit_races / total_races if total_races > 0 else 0.0
        active_label = ", ".join(STRATEGY_LABELS[key] for key in active_keys)

        print(
            f"[{combo_name}]  주수: {len(weekly)}  손실주: {losing_weeks} ({losing_rate:.3f})  "
            f"수익주: {profitable_weeks}  보합주: {flat_weeks}  적중경주수: {total_hit_races}  적중율: {hit_rate:.3f}  총베팅액: {int(total_bet):,}원  "
            f"총환수액: {total_refund:,.1f}원  이익금액: {total_profit:,.1f}원  "
            f"총환수율: {total_roi:.3f}  중앙값환수율: {median_roi:.3f}  "
            f"최저주환수율: {worst_roi:.3f}  최고주환수율: {best_roi:.3f}"
        )
        print(f"  전략: {active_label}")
        printed = True

    if printed:
        print("===================================")


def print_saturday_combo_optimizer(
    race_df: pd.DataFrame,
    section_title: str = "[토요일 기준 최적 조합 탐색]",
    min_combo_size: int = 2,
    max_combo_size: int = 4,
    top_n: int = 5,
) -> None:
    if race_df.empty:
        return

    df = race_df.copy()
    df["경주일"] = pd.to_datetime(df["경주일"].astype(str), format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["경주일"]).copy()
    if df.empty:
        return

    df["토요일기준일"] = df["경주일"] + pd.to_timedelta(5 - df["경주일"].dt.weekday, unit="D")
    candidate_keys = [
        key
        for key in STRATEGY_RESULT_COLUMNS.keys()
        if key not in EXCLUDED_STRATEGY_KEYS
        and STRATEGY_RESULT_COLUMNS[key]["bet"] in df.columns
        and STRATEGY_RESULT_COLUMNS[key]["refund"] in df.columns
        and STRATEGY_RESULT_COLUMNS[key]["hit"] in df.columns
    ]
    if not candidate_keys:
        return

    max_combo_size = min(max_combo_size, len(candidate_keys))
    if min_combo_size > max_combo_size:
        min_combo_size = max_combo_size

    results = []
    for combo_size in range(min_combo_size, max_combo_size + 1):
        for combo_keys in combinations(candidate_keys, combo_size):
            bet_cols = [STRATEGY_RESULT_COLUMNS[key]["bet"] for key in combo_keys]
            refund_cols = [STRATEGY_RESULT_COLUMNS[key]["refund"] for key in combo_keys]
            hit_cols = [STRATEGY_RESULT_COLUMNS[key]["hit"] for key in combo_keys]
            combo_df = df[["토요일기준일"] + bet_cols + refund_cols + hit_cols].copy()
            combo_df["총베팅액"] = combo_df[bet_cols].sum(axis=1)
            combo_df["총환수액"] = combo_df[refund_cols].sum(axis=1)
            combo_df["적중경주"] = combo_df[hit_cols].max(axis=1)
            weekly = (
                combo_df.groupby("토요일기준일", dropna=False)[["총베팅액", "총환수액", "적중경주"]]
                .sum()
                .reset_index()
                .sort_values("토요일기준일")
            )
            weekly = weekly[weekly["총베팅액"] > 0].copy()
            if weekly.empty:
                continue

            weekly["이익금액"] = weekly["총환수액"] - weekly["총베팅액"]
            weekly["환수율"] = weekly["총환수액"] / weekly["총베팅액"]

            total_bet = float(weekly["총베팅액"].sum())
            total_refund = float(weekly["총환수액"].sum())
            total_roi = total_refund / total_bet if total_bet > 0 else 0.0
            losing_weeks = int((weekly["이익금액"] < 0).sum())
            losing_rate = losing_weeks / len(weekly) if len(weekly) > 0 else 0.0
            total_hit_races = int(combo_df["적중경주"].sum())
            total_races = len(combo_df)
            hit_rate = total_hit_races / total_races if total_races > 0 else 0.0

            results.append(
                {
                    "keys": combo_keys,
                    "weeks": len(weekly),
                    "losing_weeks": losing_weeks,
                    "losing_rate": losing_rate,
                    "hit_races": total_hit_races,
                    "hit_rate": hit_rate,
                    "median_roi": float(weekly["환수율"].median()),
                    "worst_roi": float(weekly["환수율"].min()),
                    "best_roi": float(weekly["환수율"].max()),
                    "total_bet": total_bet,
                    "total_refund": total_refund,
                    "total_profit": total_refund - total_bet,
                    "total_roi": total_roi,
                }
            )

    if not results:
        return

    results.sort(
        key=lambda x: (
            x["losing_rate"],
            -x["hit_rate"],
            -x["median_roi"],
            -x["worst_roi"],
            -x["total_roi"],
            x["total_bet"],
        )
    )

    print(section_title)
    for rank, item in enumerate(results[:top_n], start=1):
        label = ", ".join(STRATEGY_LABELS[key] for key in item["keys"])
        print(
            f"[Top {rank}]  전략수: {len(item['keys'])}  주수: {item['weeks']}  "
            f"손실주: {item['losing_weeks']} ({item['losing_rate']:.3f})  "
            f"적중경주수: {item['hit_races']}  적중율: {item['hit_rate']:.3f}  "
            f"총베팅액: {int(item['total_bet']):,}원  총환수액: {item['total_refund']:,.1f}원  "
            f"이익금액: {item['total_profit']:,.1f}원  총환수율: {item['total_roi']:.3f}  "
            f"중앙값환수율: {item['median_roi']:.3f}  최저주환수율: {item['worst_roi']:.3f}"
        )
        print(f"  전략: {label}")
    print("===================================")


# =========================
# 2. r_pop 기반 환수 계산
# =========================
def calc_rpop_anchor_26_trifecta(
    from_date: str,
    to_date: str,
    bet_unit: int = 100,
    apply_odds_filter: bool = False,
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
    - 환수금/환수율 집계.
    """
    engine = get_engine()
    df = load_result_data_from_db(engine, from_date=from_date, to_date=to_date)

    if df.empty:
        print(f"▶ [{from_date} ~ {to_date}] 기간 데이터가 없습니다.")
        return pd.DataFrame(), {}

    df = df.copy()
    if "등급" in df.columns:
        df["등급"] = df["등급"].fillna("")
    else:
        df["등급"] = ""
    df = df[
        ~df["등급"].str.contains(r"(?:국OPEN|혼OPEN)", case=False, na=False, regex=True)
    ]
    df["경주일"] = df["경주일"].astype(str)
    df = df[df["경주일"].str.slice(6, 8).astype(int).between(1, 31)].copy()
    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)
    df["연월"] = df["경주일"].str.slice(0, 6)
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")

    for col in ["rank", "r_pop", "r_rank"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    before_rows = len(df)
    df = df.dropna(subset=["rank", "r_pop", "r_rank"]).copy()
    dropped = before_rows - len(df)
    if dropped:
        print(f"⚠️ rank/r_pop/r_rank NaN {dropped}건 제외")
    for col in ["rank", "r_pop", "r_rank"]:
        df[col] = df[col].astype(int)
    df["r_pop"] = df["r_pop"].where(df["r_pop"] != 0, 99)

    df["복승식배당율"] = pd.to_numeric(df["복승식배당율"], errors="coerce").fillna(0.0)
    df["삼복승식배당율"] = (
        pd.to_numeric(df["삼복승식배당율"], errors="coerce").fillna(0.0).round(1)
    )
    df["삼쌍승식배당율"] = (
        pd.to_numeric(df["삼쌍승식배당율"], errors="coerce").fillna(0.0).round(1)
    )
    # 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    anchor1_24_quinella_bet_unit = 100
    anchor1_24_quinella_bet_per_race = 3 * anchor1_24_quinella_bet_unit  # 1 * 3
    anchor1_26_quinella_bet_unit = 100
    anchor1_26_quinella_bet_per_race = 5 * anchor1_26_quinella_bet_unit  # 1 * 5
    top3pair_46_quinella_bet_unit = 100
    top3pair_46_quinella_bet_per_race = 9 * top3pair_46_quinella_bet_unit  # 3 * 3
    anchor12_3_4_quinella_bet_unit = 100
    anchor12_3_5_quinella_bet_unit = 100
    anchor12_3_6_quinella_bet_unit = 100
    anchor12_3_7_quinella_bet_unit = 100
    anchor12_3_8_quinella_bet_unit = 100
    anchor12_3_12_quinella_bet_unit = 100
    anchor1_24_57_bet_unit = 100
    anchor1_24_57_bet_per_race = 9 * anchor1_24_57_bet_unit  # 3 * 3
    anchor1_24_58_bet_unit = 100
    anchor1_24_58_bet_per_race = 12 * anchor1_24_58_bet_unit  # 3 * 4
    top4_box_trifecta_bet_unit = 100
    top4_box_trifecta_bet_per_race = 24 * top4_box_trifecta_bet_unit  # 4P3
    top5_box_trifecta_bet_unit = 100
    top5_box_trifecta_bet_per_race = 60 * top5_box_trifecta_bet_unit  # 5P3
    top6_trio_bet_unit = 100
    top6_trio_bet_per_race = 20 * top6_trio_bet_unit  # 6C3
    top3pair_46_trio_bet_unit = 100
    top3pair_46_trio_bet_per_race = 9 * top3pair_46_trio_bet_unit  # 3C2 * 3
    top3pair_47_trio_bet_unit = 100
    top3pair_47_trio_bet_per_race = 12 * top3pair_47_trio_bet_unit  # 3C2 * 4
    top3pair_49_trio_bet_unit = 100
    top3pair_49_trio_bet_per_race = 18 * top3pair_49_trio_bet_unit  # 3C2 * 6
    top4pair_58_trio_bet_unit = 100
    top4pair_58_trio_bet_per_race = 24 * top4pair_58_trio_bet_unit  # 4C2 * 4
    top12anchor_3_10_trio_bet_unit = 100
    top12anchor_3_10_trio_bet_per_race = 8 * top12anchor_3_10_trio_bet_unit  # 1 * 8
    top12anchor_3_8_12_trio_bet_unit = 100
    top12anchor_3_12_trio_bet_unit = 100
    top12anchor_3_12_trio_bet_per_race = 10 * top12anchor_3_12_trio_bet_unit  # 1 * 10
    anchor1_57_24_bet_unit = 100
    anchor1_57_24_bet_per_race = 9 * anchor1_57_24_bet_unit  # 3 * 3
    anchor1_58_24_bet_unit = 100
    anchor1_58_24_bet_per_race = 12 * anchor1_58_24_bet_unit  # 4 * 3
    anchor3_24_bet_unit = 100
    anchor3_24_bet_per_race = 6 * anchor3_24_bet_unit  # 3P2
    anchor2_24_bet_unit = 100
    anchor2_24_bet_per_race = 6 * anchor2_24_bet_unit  # 3P2
    anchor1_24_bet_unit = 100
    anchor1_24_bet_per_race = 6 * anchor1_24_bet_unit  # 3P2
    anchor1_25_bet_unit = 100
    anchor1_25_bet_per_race = 12 * anchor1_25_bet_unit  # 4P2
    anchor1_25_68_bet_unit = 100
    anchor1_25_68_bet_per_race = 12 * anchor1_25_68_bet_unit  # 4 * 3
    anchor1_25_69_bet_unit = 100
    anchor1_25_69_bet_per_race = 16 * anchor1_25_69_bet_unit  # 4 * 4
    anchor1_69_25_bet_unit = 100
    anchor1_69_25_bet_per_race = 16 * anchor1_69_25_bet_unit  # 4 * 4
    anchor1_23_46_bet_unit = 100
    anchor1_23_46_bet_per_race = 6 * anchor1_23_46_bet_unit  # 2 * 3
    anchor1_23_47_bet_unit = 100
    anchor1_23_47_bet_per_race = 8 * anchor1_23_47_bet_unit  # 2 * 4
    anchor1_23_48_bet_unit = 100
    anchor1_23_48_bet_per_race = 10 * anchor1_23_48_bet_unit  # 2 * 5
    anchor1_23_49_bet_unit = 100
    anchor1_23_49_bet_per_race = 12 * anchor1_23_49_bet_unit  # 2 * 6
    anchor12_3_7_bet_unit = 100
    anchor12_3_7_bet_per_race = 5 * anchor12_3_7_bet_unit  # 1 * 5
    anchor12_3_10_bet_unit = 100
    anchor12_3_10_bet_per_race = 8 * anchor12_3_10_bet_unit  # 1 * 8
    total_races = 0
    excluded_races = 0
    anchor1_24_quinella_total_bet = 0.0
    anchor1_24_quinella_total_refund = 0.0
    anchor1_24_quinella_total_hits = 0
    anchor1_26_quinella_total_bet = 0.0
    anchor1_26_quinella_total_refund = 0.0
    anchor1_26_quinella_total_hits = 0
    top3pair_46_quinella_total_bet = 0.0
    top3pair_46_quinella_total_refund = 0.0
    top3pair_46_quinella_total_hits = 0
    anchor12_3_4_quinella_total_bet = 0.0
    anchor12_3_4_quinella_total_refund = 0.0
    anchor12_3_4_quinella_total_hits = 0
    anchor12_3_5_quinella_total_bet = 0.0
    anchor12_3_5_quinella_total_refund = 0.0
    anchor12_3_5_quinella_total_hits = 0
    anchor12_3_6_quinella_total_bet = 0.0
    anchor12_3_6_quinella_total_refund = 0.0
    anchor12_3_6_quinella_total_hits = 0
    anchor12_3_7_quinella_total_bet = 0.0
    anchor12_3_7_quinella_total_refund = 0.0
    anchor12_3_7_quinella_total_hits = 0
    anchor12_3_8_quinella_total_bet = 0.0
    anchor12_3_8_quinella_total_refund = 0.0
    anchor12_3_8_quinella_total_hits = 0
    anchor12_3_12_quinella_total_bet = 0.0
    anchor12_3_12_quinella_total_refund = 0.0
    anchor12_3_12_quinella_total_hits = 0
    anchor1_24_57_total_bet = 0.0
    anchor1_24_57_total_refund = 0.0
    anchor1_24_57_total_hits = 0
    anchor1_24_58_total_bet = 0.0
    anchor1_24_58_total_refund = 0.0
    anchor1_24_58_total_hits = 0
    top4_box_trifecta_total_bet = 0.0
    top4_box_trifecta_total_refund = 0.0
    top4_box_trifecta_total_hits = 0
    top5_box_trifecta_total_bet = 0.0
    top5_box_trifecta_total_refund = 0.0
    top5_box_trifecta_total_hits = 0
    top6_trio_total_bet = 0.0
    top6_trio_total_refund = 0.0
    top6_trio_total_hits = 0
    top3pair_46_trio_total_bet = 0.0
    top3pair_46_trio_total_refund = 0.0
    top3pair_46_trio_total_hits = 0
    top3pair_47_trio_total_bet = 0.0
    top3pair_47_trio_total_refund = 0.0
    top3pair_47_trio_total_hits = 0
    top3pair_49_trio_total_bet = 0.0
    top3pair_49_trio_total_refund = 0.0
    top3pair_49_trio_total_hits = 0
    top4pair_58_trio_total_bet = 0.0
    top4pair_58_trio_total_refund = 0.0
    top4pair_58_trio_total_hits = 0
    top12anchor_3_10_trio_total_bet = 0.0
    top12anchor_3_10_trio_total_refund = 0.0
    top12anchor_3_10_trio_total_hits = 0
    top12anchor_3_8_12_trio_total_bet = 0.0
    top12anchor_3_8_12_trio_total_refund = 0.0
    top12anchor_3_8_12_trio_total_hits = 0
    top12anchor_3_12_trio_total_bet = 0.0
    top12anchor_3_12_trio_total_refund = 0.0
    top12anchor_3_12_trio_total_hits = 0
    anchor1_57_24_total_bet = 0.0
    anchor1_57_24_total_refund = 0.0
    anchor1_57_24_total_hits = 0
    anchor1_58_24_total_bet = 0.0
    anchor1_58_24_total_refund = 0.0
    anchor1_58_24_total_hits = 0
    anchor3_24_total_bet = 0.0
    anchor3_24_total_refund = 0.0
    anchor3_24_total_hits = 0
    anchor2_24_total_bet = 0.0
    anchor2_24_total_refund = 0.0
    anchor2_24_total_hits = 0
    anchor1_24_total_bet = 0.0
    anchor1_24_total_refund = 0.0
    anchor1_24_total_hits = 0
    anchor1_25_total_bet = 0.0
    anchor1_25_total_refund = 0.0
    anchor1_25_total_hits = 0
    anchor1_25_68_total_bet = 0.0
    anchor1_25_68_total_refund = 0.0
    anchor1_25_68_total_hits = 0
    anchor1_25_69_total_bet = 0.0
    anchor1_25_69_total_refund = 0.0
    anchor1_25_69_total_hits = 0
    anchor1_69_25_total_bet = 0.0
    anchor1_69_25_total_refund = 0.0
    anchor1_69_25_total_hits = 0
    anchor1_23_46_total_bet = 0.0
    anchor1_23_46_total_refund = 0.0
    anchor1_23_46_total_hits = 0
    anchor1_23_47_total_bet = 0.0
    anchor1_23_47_total_refund = 0.0
    anchor1_23_47_total_hits = 0
    anchor1_23_48_total_bet = 0.0
    anchor1_23_48_total_refund = 0.0
    anchor1_23_48_total_hits = 0
    anchor1_23_49_total_bet = 0.0
    anchor1_23_49_total_refund = 0.0
    anchor1_23_49_total_hits = 0
    anchor12_3_7_total_bet = 0.0
    anchor12_3_7_total_refund = 0.0
    anchor12_3_7_total_hits = 0
    anchor12_3_10_total_bet = 0.0
    anchor12_3_10_total_refund = 0.0
    anchor12_3_10_total_hits = 0
    total_hits_any = 0
    total_holes_all = 0
    week_summary = {}
    week_track_summary = {}
    month_summary = {}
    track_summary = {}
    track_month_summary = {}
    strategy_track_summary = {}
    month_summary_anchor1_24_quinella = {}
    month_summary_anchor1_26_quinella = {}
    month_summary_top3pair_46_quinella = {}
    month_summary_anchor12_3_4_quinella = {}
    month_summary_anchor12_3_5_quinella = {}
    month_summary_anchor12_3_6_quinella = {}
    month_summary_anchor12_3_7_quinella = {}
    month_summary_anchor12_3_8_quinella = {}
    month_summary_anchor12_3_12_quinella = {}
    month_summary_rpop5_7_anchor_1_4_trio = {}
    month_summary_rpop5_8_anchor_1_4_trio = {}
    month_summary_anchor_24_57 = {}
    month_summary_anchor_24_58 = {}
    month_summary_top4_box_trifecta = {}
    month_summary_top5_box_trifecta = {}
    month_summary_top6_trio = {}
    month_summary_top3pair_46_trio = {}
    month_summary_top3pair_47_trio = {}
    month_summary_top3pair_49_trio = {}
    month_summary_top4pair_58_trio = {}
    month_summary_top12anchor_3_10_trio = {}
    month_summary_top12anchor_3_8_12_trio = {}
    month_summary_top12anchor_3_12_trio = {}
    month_summary_anchor3_24 = {}
    month_summary_anchor2_24 = {}
    month_summary_anchor_24 = {}
    month_summary_anchor_25 = {}
    month_summary_anchor_25_68 = {}
    month_summary_anchor_25_69 = {}
    month_summary_anchor_69_25 = {}
    month_summary_anchor_23_46 = {}
    month_summary_anchor_23_47 = {}
    month_summary_anchor_23_48 = {}
    month_summary_anchor_23_49 = {}
    month_summary_anchor12_3_7 = {}
    month_summary_anchor12_3_10 = {}
    strategy_labels = STRATEGY_LABELS
    race_rows = []

    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()
        if len(g) >= 13:
            excluded_races += 1
            continue
        new_cnt = int(g["신마"].sum())
        if new_cnt >= 3:
            excluded_races += 1
            continue
        total_races += 1
        year_month = str(date)[:6]
        distance = g["경주거리"].iloc[0]
        grade = g["등급"].iloc[0]

        # rank 기준 집계: 축마/상대군/복조군을 exp011.rank 순서로 구성한다.
        g_sorted = g.sort_values("rank", ascending=True)
        top3 = g_sorted.head(3)["마번"].tolist()
        top4 = g_sorted.head(4)["마번"].tolist()
        top5 = g_sorted.head(5)["마번"].tolist()
        top6 = g_sorted.head(6)["마번"].tolist()
        anchor_gate = top4[0] if top4 else None
        second_gate = g_sorted.iloc[1]["마번"] if len(g_sorted) >= 2 else None
        top2_6 = g_sorted.iloc[1:6]["마번"].tolist()
        top2_3 = g_sorted.iloc[1:3]["마번"].tolist()
        top3_4 = g_sorted.iloc[2:4]["마번"].tolist()
        top3_5 = g_sorted.iloc[2:5]["마번"].tolist()
        top3_8 = g_sorted.iloc[2:8]["마번"].tolist()
        top3_7 = g_sorted.iloc[2:7]["마번"].tolist()
        top3_10 = g_sorted.iloc[2:10]["마번"].tolist()
        top3_12 = g_sorted.iloc[2:12]["마번"].tolist()
        rank12_gate = g_sorted.iloc[11]["마번"] if len(g_sorted) >= 12 else None
        top3_8_12 = top3_8 + ([rank12_gate] if rank12_gate is not None else [])
        top2_4 = g_sorted.iloc[1:4]["마번"].tolist()
        top2_5 = g_sorted.iloc[1:5]["마번"].tolist()
        top4_6 = g_sorted.iloc[3:6]["마번"].tolist()
        top4_7 = g_sorted.iloc[3:7]["마번"].tolist()
        top4_8 = g_sorted.iloc[3:8]["마번"].tolist()
        top4_9 = g_sorted.iloc[3:9]["마번"].tolist()
        top4_10 = g_sorted.iloc[3:10]["마번"].tolist()
        top5_7 = g_sorted.iloc[4:7]["마번"].tolist()
        top5_8 = g_sorted.iloc[4:8]["마번"].tolist()
        top6_8 = g_sorted.iloc[5:8]["마번"].tolist()
        top6_9 = g_sorted.iloc[5:9]["마번"].tolist()
        top3_set = set(top3)
        top2_3_set = set(top2_3)
        top2_6_set = set(top2_6)
        top3_4_set = set(top3_4)
        top3_5_set = set(top3_5)
        top3_8_set = set(top3_8)
        top3_7_set = set(top3_7)
        top3_10_set = set(top3_10)
        top3_8_12_set = set(top3_8_12)
        top3_12_set = set(top3_12)
        top2_4_set = set(top2_4)
        top2_5_set = set(top2_5)
        top4_6_set = set(top4_6)
        top4_7_set = set(top4_7)
        top4_8_set = set(top4_8)
        top4_9_set = set(top4_9)
        top4_10_set = set(top4_10)
        top5_7_set = set(top5_7)
        top5_8_set = set(top5_8)
        top6_8_set = set(top6_8)
        top6_9_set = set(top6_9)

        actual_top2 = g[g["r_rank"] <= 2].sort_values("r_rank")["마번"].tolist()
        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()
        actual_set = set(actual_top3)
        actual_top2_set = set(actual_top2)
        quinella_odds = float(g["복승식배당율"].iloc[0])
        trio_odds = float(g["삼복승식배당율"].iloc[0])
        odds = float(g["삼쌍승식배당율"].iloc[0])
        if apply_odds_filter and odds >= 1000:
            excluded_races += 1
            continue

        anchor1_24_quinella_valid = anchor_gate is not None and len(top2_4) == 3
        anchor1_24_quinella_hit_flag = int(
            anchor1_24_quinella_valid
            and len(actual_top2) == 2
            and anchor_gate in actual_top2_set
            and len(actual_top2_set & top2_4_set) == 1
        )
        anchor1_24_quinella_refund = (
            quinella_odds * anchor1_24_quinella_bet_unit
            if anchor1_24_quinella_hit_flag == 1
            else 0.0
        )
        anchor1_26_quinella_valid = anchor_gate is not None and len(top2_6) == 5
        anchor1_26_quinella_hit_flag = int(
            anchor1_26_quinella_valid
            and len(actual_top2) == 2
            and anchor_gate in actual_top2_set
            and len(actual_top2_set & top2_6_set) == 1
        )
        anchor1_26_quinella_refund = (
            quinella_odds * anchor1_26_quinella_bet_unit
            if anchor1_26_quinella_hit_flag == 1
            else 0.0
        )
        top3pair_46_quinella_valid = len(top3) == 3 and len(top4_6) == 3
        top3pair_46_quinella_hit_flag = int(
            top3pair_46_quinella_valid
            and len(actual_top2) == 2
            and len(actual_top2_set & top3_set) == 1
            and len(actual_top2_set & top4_6_set) == 1
        )
        top3pair_46_quinella_refund = (
            quinella_odds * top3pair_46_quinella_bet_unit
            if top3pair_46_quinella_hit_flag == 1
            else 0.0
        )
        anchor12_3_4_quinella_valid = second_gate is not None and len(top3_4) >= 1
        anchor12_3_4_quinella_bet_per_race_current = (
            len(top3_4) * 2 * anchor12_3_4_quinella_bet_unit
            if anchor12_3_4_quinella_valid
            else 0.0
        )
        anchor12_3_4_quinella_hit_flag = int(
            anchor12_3_4_quinella_valid
            and len(actual_top2) == 2
            and len(actual_top2_set & {anchor_gate, second_gate}) == 1
            and len(actual_top2_set & top3_4_set) == 1
        )
        anchor12_3_4_quinella_refund = (
            quinella_odds * anchor12_3_4_quinella_bet_unit
            if anchor12_3_4_quinella_hit_flag == 1
            else 0.0
        )
        anchor12_3_5_quinella_valid = second_gate is not None and len(top3_5) >= 1
        anchor12_3_5_quinella_bet_per_race_current = (
            len(top3_5) * 2 * anchor12_3_5_quinella_bet_unit
            if anchor12_3_5_quinella_valid
            else 0.0
        )
        anchor12_3_5_quinella_hit_flag = int(
            anchor12_3_5_quinella_valid
            and len(actual_top2) == 2
            and len(actual_top2_set & {anchor_gate, second_gate}) == 1
            and len(actual_top2_set & top3_5_set) == 1
        )
        anchor12_3_5_quinella_refund = (
            quinella_odds * anchor12_3_5_quinella_bet_unit
            if anchor12_3_5_quinella_hit_flag == 1
            else 0.0
        )
        anchor12_3_6_quinella_valid = second_gate is not None and len(top4_6) >= 1
        anchor12_3_6_quinella_bet_per_race_current = (
            len(top4_6) * 2 * anchor12_3_6_quinella_bet_unit
            if anchor12_3_6_quinella_valid
            else 0.0
        )
        anchor12_3_6_quinella_hit_flag = int(
            anchor12_3_6_quinella_valid
            and len(actual_top2) == 2
            and len(actual_top2_set & {anchor_gate, second_gate}) == 1
            and len(actual_top2_set & top4_6_set) == 1
        )
        anchor12_3_6_quinella_refund = (
            quinella_odds * anchor12_3_6_quinella_bet_unit
            if anchor12_3_6_quinella_hit_flag == 1
            else 0.0
        )
        anchor12_3_7_quinella_valid = second_gate is not None and len(top3_7) >= 1
        anchor12_3_7_quinella_bet_per_race_current = (
            len(top3_7) * 2 * anchor12_3_7_quinella_bet_unit
            if anchor12_3_7_quinella_valid
            else 0.0
        )
        anchor12_3_7_quinella_hit_flag = int(
            anchor12_3_7_quinella_valid
            and len(actual_top2) == 2
            and len(actual_top2_set & {anchor_gate, second_gate}) == 1
            and len(actual_top2_set & top3_7_set) == 1
        )
        anchor12_3_7_quinella_refund = (
            quinella_odds * anchor12_3_7_quinella_bet_unit
            if anchor12_3_7_quinella_hit_flag == 1
            else 0.0
        )
        anchor12_3_8_quinella_valid = second_gate is not None and len(top3_8) >= 1
        anchor12_3_8_quinella_bet_per_race_current = (
            len(top3_8) * 2 * anchor12_3_8_quinella_bet_unit
            if anchor12_3_8_quinella_valid
            else 0.0
        )
        anchor12_3_8_quinella_hit_flag = int(
            anchor12_3_8_quinella_valid
            and len(actual_top2) == 2
            and len(actual_top2_set & {anchor_gate, second_gate}) == 1
            and len(actual_top2_set & top3_8_set) == 1
        )
        anchor12_3_8_quinella_refund = (
            quinella_odds * anchor12_3_8_quinella_bet_unit
            if anchor12_3_8_quinella_hit_flag == 1
            else 0.0
        )
        anchor12_3_12_quinella_valid = second_gate is not None and len(top3_12) >= 1
        anchor12_3_12_quinella_bet_per_race_current = (
            len(top3_12) * 2 * anchor12_3_12_quinella_bet_unit
            if anchor12_3_12_quinella_valid
            else 0.0
        )
        anchor12_3_12_quinella_hit_flag = int(
            anchor12_3_12_quinella_valid
            and len(actual_top2) == 2
            and len(actual_top2_set & {anchor_gate, second_gate}) == 1
            and len(actual_top2_set & top3_12_set) == 1
        )
        anchor12_3_12_quinella_refund = (
            quinella_odds * anchor12_3_12_quinella_bet_unit
            if anchor12_3_12_quinella_hit_flag == 1
            else 0.0
        )
        r_pop1_top1_hit = int(len(actual_top3) >= 1 and actual_top3[0] == anchor_gate)
        r_pop1_top3_hit = int(anchor_gate is not None and anchor_gate in actual_set)
        anchor1_24_57_valid = (
            anchor_gate is not None and len(top2_4) == 3 and len(top5_7) == 3
        )
        anchor1_24_57_hit_flag = int(
            anchor1_24_57_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_4_set
            and actual_top3[2] in top5_7_set
        )
        anchor1_24_57_refund = (
            odds * anchor1_24_57_bet_unit if anchor1_24_57_hit_flag == 1 else 0.0
        )
        anchor1_24_58_valid = (
            anchor_gate is not None and len(top2_4) == 3 and len(top5_8) == 4
        )
        anchor1_24_58_hit_flag = int(
            anchor1_24_58_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_4_set
            and actual_top3[2] in top5_8_set
        )
        anchor1_24_58_refund = (
            odds * anchor1_24_58_bet_unit if anchor1_24_58_hit_flag == 1 else 0.0
        )
        top4_box_trifecta_valid = len(top4) == 4
        top4_box_trifecta_hit_flag = int(
            top4_box_trifecta_valid
            and len(actual_top3) == 3
            and actual_set.issubset(set(top4))
        )
        top4_box_trifecta_refund = (
            odds * top4_box_trifecta_bet_unit
            if top4_box_trifecta_hit_flag == 1
            else 0.0
        )
        top5_box_trifecta_valid = len(top5) == 5
        top5_box_trifecta_hit_flag = int(
            top5_box_trifecta_valid
            and len(actual_top3) == 3
            and actual_set.issubset(set(top5))
        )
        top5_box_trifecta_refund = (
            odds * top5_box_trifecta_bet_unit
            if top5_box_trifecta_hit_flag == 1
            else 0.0
        )
        top6_trio_valid = len(top6) == 6
        top6_trio_hit_flag = int(
            top6_trio_valid
            and len(actual_top3) == 3
            and actual_set.issubset(set(top6))
        )
        top6_trio_refund = (
            trio_odds * top6_trio_bet_unit if top6_trio_hit_flag == 1 else 0.0
        )
        top3pair_46_trio_valid = len(top3) == 3 and len(top4_6) == 3
        top3pair_46_trio_hit_flag = int(
            top3pair_46_trio_valid
            and len(actual_top3) == 3
            and len(actual_set & top3_set) == 2
            and len(actual_set & top4_6_set) == 1
        )
        top3pair_46_trio_refund = (
            trio_odds * top3pair_46_trio_bet_unit
            if top3pair_46_trio_hit_flag == 1
            else 0.0
        )
        top3pair_47_trio_valid = len(top3) == 3 and len(top4_7) == 4
        top3pair_47_trio_hit_flag = int(
            top3pair_47_trio_valid
            and len(actual_top3) == 3
            and len(actual_set & top3_set) == 2
            and len(actual_set & top4_7_set) == 1
        )
        top3pair_47_trio_refund = (
            trio_odds * top3pair_47_trio_bet_unit
            if top3pair_47_trio_hit_flag == 1
            else 0.0
        )
        top3pair_49_trio_valid = len(top3) == 3 and len(top4_9) == 6
        top3pair_49_trio_hit_flag = int(
            top3pair_49_trio_valid
            and len(actual_top3) == 3
            and len(actual_set & top3_set) == 2
            and len(actual_set & top4_9_set) == 1
        )
        top3pair_49_trio_refund = (
            trio_odds * top3pair_49_trio_bet_unit
            if top3pair_49_trio_hit_flag == 1
            else 0.0
        )
        top4pair_58_trio_valid = len(top4) == 4 and len(top5_8) == 4
        top4pair_58_trio_hit_flag = int(
            top4pair_58_trio_valid
            and len(actual_top3) == 3
            and len(actual_set & set(top4)) == 2
            and len(actual_set & top5_8_set) == 1
        )
        top4pair_58_trio_refund = (
            trio_odds * top4pair_58_trio_bet_unit
            if top4pair_58_trio_hit_flag == 1
            else 0.0
        )
        top12anchor_3_10_trio_valid = second_gate is not None and len(top3_10) == 8
        top12anchor_3_10_trio_hit_flag = int(
            top12anchor_3_10_trio_valid
            and len(actual_top3) == 3
            and anchor_gate in actual_set
            and second_gate in actual_set
            and len(actual_set & top3_10_set) == 1
        )
        top12anchor_3_10_trio_refund = (
            trio_odds * top12anchor_3_10_trio_bet_unit
            if top12anchor_3_10_trio_hit_flag == 1
            else 0.0
        )
        top12anchor_3_8_12_trio_valid = (
            second_gate is not None and len(top3_8_12) >= 1
        )
        top12anchor_3_8_12_bet_per_race_current = (
            len(top3_8_12) * top12anchor_3_8_12_trio_bet_unit
            if top12anchor_3_8_12_trio_valid
            else 0.0
        )
        top12anchor_3_8_12_trio_hit_flag = int(
            top12anchor_3_8_12_trio_valid
            and len(actual_top3) == 3
            and anchor_gate in actual_set
            and second_gate in actual_set
            and len(actual_set & top3_8_12_set) == 1
        )
        top12anchor_3_8_12_trio_refund = (
            trio_odds * top12anchor_3_8_12_trio_bet_unit
            if top12anchor_3_8_12_trio_hit_flag == 1
            else 0.0
        )
        top12anchor_3_12_trio_valid = second_gate is not None and len(top3_12) >= 1
        top12anchor_3_12_bet_per_race_current = (
            len(top3_12) * top12anchor_3_12_trio_bet_unit
            if top12anchor_3_12_trio_valid
            else 0.0
        )
        top12anchor_3_12_trio_hit_flag = int(
            top12anchor_3_12_trio_valid
            and len(actual_top3) == 3
            and anchor_gate in actual_set
            and second_gate in actual_set
            and len(actual_set & top3_12_set) == 1
        )
        top12anchor_3_12_trio_refund = (
            trio_odds * top12anchor_3_12_trio_bet_unit
            if top12anchor_3_12_trio_hit_flag == 1
            else 0.0
        )
        anchor1_57_24_valid = (
            anchor_gate is not None and len(top5_7) == 3 and len(top2_4) == 3
        )
        anchor1_57_24_hit_flag = int(
            anchor1_57_24_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top5_7_set
            and actual_top3[2] in top2_4_set
        )
        anchor1_57_24_refund = (
            odds * anchor1_57_24_bet_unit if anchor1_57_24_hit_flag == 1 else 0.0
        )
        anchor1_58_24_valid = (
            anchor_gate is not None and len(top5_8) == 4 and len(top2_4) == 3
        )
        anchor1_58_24_hit_flag = int(
            anchor1_58_24_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top5_8_set
            and actual_top3[2] in top2_4_set
        )
        anchor1_58_24_refund = (
            odds * anchor1_58_24_bet_unit if anchor1_58_24_hit_flag == 1 else 0.0
        )
        anchor3_24_valid = anchor_gate is not None and len(top2_4) == 3
        anchor3_24_hit_flag = int(
            anchor3_24_valid
            and len(actual_top3) == 3
            and actual_top3[0] in top2_4_set
            and actual_top3[1] in top2_4_set
            and actual_top3[0] != actual_top3[1]
            and actual_top3[2] == anchor_gate
        )
        anchor3_24_refund = (
            odds * anchor3_24_bet_unit if anchor3_24_hit_flag == 1 else 0.0
        )
        anchor2_24_valid = anchor_gate is not None and len(top2_4) == 3
        anchor2_24_hit_flag = int(
            anchor2_24_valid
            and len(actual_top3) == 3
            and actual_top3[0] in top2_4_set
            and actual_top3[1] == anchor_gate
            and actual_top3[2] in top2_4_set
            and actual_top3[0] != actual_top3[2]
        )
        anchor2_24_refund = (
            odds * anchor2_24_bet_unit if anchor2_24_hit_flag == 1 else 0.0
        )
        anchor1_24_valid = anchor_gate is not None and len(top2_4) == 3
        anchor1_24_hit_flag = int(
            anchor1_24_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_4_set
            and actual_top3[2] in top2_4_set
            and actual_top3[1] != actual_top3[2]
        )
        anchor1_24_refund = (
            odds * anchor1_24_bet_unit if anchor1_24_hit_flag == 1 else 0.0
        )
        anchor1_25_valid = anchor_gate is not None and len(top2_5) == 4
        anchor1_25_hit_flag = int(
            anchor1_25_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_5_set
            and actual_top3[2] in top2_5_set
            and actual_top3[1] != actual_top3[2]
        )
        anchor1_25_refund = (
            odds * anchor1_25_bet_unit if anchor1_25_hit_flag == 1 else 0.0
        )
        anchor1_25_68_valid = (
            anchor_gate is not None and len(top2_5) == 4 and len(top6_8) == 3
        )
        anchor1_25_68_hit_flag = int(
            anchor1_25_68_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_5_set
            and actual_top3[2] in top6_8_set
        )
        anchor1_25_68_refund = (
            odds * anchor1_25_68_bet_unit if anchor1_25_68_hit_flag == 1 else 0.0
        )
        anchor1_25_69_valid = (
            anchor_gate is not None and len(top2_5) == 4 and len(top6_9) == 4
        )
        anchor1_25_69_hit_flag = int(
            anchor1_25_69_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_5_set
            and actual_top3[2] in top6_9_set
        )
        anchor1_25_69_refund = (
            odds * anchor1_25_69_bet_unit if anchor1_25_69_hit_flag == 1 else 0.0
        )
        anchor1_69_25_valid = (
            anchor_gate is not None and len(top6_9) == 4 and len(top2_5) == 4
        )
        anchor1_69_25_hit_flag = int(
            anchor1_69_25_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top6_9_set
            and actual_top3[2] in top2_5_set
        )
        anchor1_69_25_refund = (
            odds * anchor1_69_25_bet_unit if anchor1_69_25_hit_flag == 1 else 0.0
        )
        anchor1_23_46_valid = (
            anchor_gate is not None and len(top2_3) == 2 and len(top4_6) == 3
        )
        anchor1_23_46_hit_flag = int(
            anchor1_23_46_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_3_set
            and actual_top3[2] in top4_6_set
        )
        anchor1_23_46_refund = (
            odds * anchor1_23_46_bet_unit if anchor1_23_46_hit_flag == 1 else 0.0
        )
        anchor1_23_47_valid = (
            anchor_gate is not None and len(top2_3) == 2 and len(top4_7) == 4
        )
        anchor1_23_47_hit_flag = int(
            anchor1_23_47_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_3_set
            and actual_top3[2] in top4_7_set
        )
        anchor1_23_47_refund = (
            odds * anchor1_23_47_bet_unit if anchor1_23_47_hit_flag == 1 else 0.0
        )
        anchor1_23_48_valid = (
            anchor_gate is not None and len(top2_3) == 2 and len(top4_8) == 5
        )
        anchor1_23_48_hit_flag = int(
            anchor1_23_48_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_3_set
            and actual_top3[2] in top4_8_set
        )
        anchor1_23_48_refund = (
            odds * anchor1_23_48_bet_unit if anchor1_23_48_hit_flag == 1 else 0.0
        )
        anchor1_23_49_valid = (
            anchor_gate is not None and len(top2_3) == 2 and len(top4_9) == 6
        )
        anchor1_23_49_hit_flag = int(
            anchor1_23_49_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_3_set
            and actual_top3[2] in top4_9_set
        )
        anchor1_23_49_refund = (
            odds * anchor1_23_49_bet_unit if anchor1_23_49_hit_flag == 1 else 0.0
        )
        anchor12_3_7_valid = (
            anchor_gate is not None and second_gate is not None and len(top3_7) == 5
        )
        anchor12_3_7_hit_flag = int(
            anchor12_3_7_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] == second_gate
            and actual_top3[2] in top3_7_set
        )
        anchor12_3_7_refund = (
            odds * anchor12_3_7_bet_unit if anchor12_3_7_hit_flag == 1 else 0.0
        )
        anchor12_3_10_valid = anchor_gate is not None and second_gate is not None and len(top3_10) == 8
        anchor12_3_10_hit_flag = int(
            anchor12_3_10_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] == second_gate
            and actual_top3[2] in top3_10_set
        )
        anchor12_3_10_refund = (
            odds * anchor12_3_10_bet_unit if anchor12_3_10_hit_flag == 1 else 0.0
        )
        if "anchor1_24_57" in EXCLUDED_STRATEGY_KEYS:
            anchor1_24_57_valid = False
            anchor1_24_57_hit_flag = 0
            anchor1_24_57_refund = 0.0
        if "top4_box_trifecta" in EXCLUDED_STRATEGY_KEYS:
            top4_box_trifecta_valid = False
            top4_box_trifecta_hit_flag = 0
            top4_box_trifecta_refund = 0.0
        if "top5_box_trifecta" in EXCLUDED_STRATEGY_KEYS:
            top5_box_trifecta_valid = False
            top5_box_trifecta_hit_flag = 0
            top5_box_trifecta_refund = 0.0
        if "anchor1_24_quinella" in EXCLUDED_STRATEGY_KEYS:
            anchor1_24_quinella_valid = False
            anchor1_24_quinella_hit_flag = 0
            anchor1_24_quinella_refund = 0.0
        if "anchor1_26_quinella" in EXCLUDED_STRATEGY_KEYS:
            anchor1_26_quinella_valid = False
            anchor1_26_quinella_hit_flag = 0
            anchor1_26_quinella_refund = 0.0
        if "top3pair_46_quinella" in EXCLUDED_STRATEGY_KEYS:
            top3pair_46_quinella_valid = False
            top3pair_46_quinella_hit_flag = 0
            top3pair_46_quinella_refund = 0.0
        if "anchor12_3_4_quinella" in EXCLUDED_STRATEGY_KEYS:
            anchor12_3_4_quinella_valid = False
            anchor12_3_4_quinella_hit_flag = 0
            anchor12_3_4_quinella_refund = 0.0
        if "anchor12_3_5_quinella" in EXCLUDED_STRATEGY_KEYS:
            anchor12_3_5_quinella_valid = False
            anchor12_3_5_quinella_hit_flag = 0
            anchor12_3_5_quinella_refund = 0.0
        if "anchor12_3_6_quinella" in EXCLUDED_STRATEGY_KEYS:
            anchor12_3_6_quinella_valid = False
            anchor12_3_6_quinella_hit_flag = 0
            anchor12_3_6_quinella_refund = 0.0
        if "anchor12_3_7_quinella" in EXCLUDED_STRATEGY_KEYS:
            anchor12_3_7_quinella_valid = False
            anchor12_3_7_quinella_hit_flag = 0
            anchor12_3_7_quinella_refund = 0.0
        if "anchor12_3_8_quinella" in EXCLUDED_STRATEGY_KEYS:
            anchor12_3_8_quinella_valid = False
            anchor12_3_8_quinella_hit_flag = 0
            anchor12_3_8_quinella_refund = 0.0
        if "anchor12_3_12_quinella" in EXCLUDED_STRATEGY_KEYS:
            anchor12_3_12_quinella_valid = False
            anchor12_3_12_quinella_hit_flag = 0
            anchor12_3_12_quinella_refund = 0.0
        if "top6_trio" in EXCLUDED_STRATEGY_KEYS:
            top6_trio_valid = False
            top6_trio_hit_flag = 0
            top6_trio_refund = 0.0
        if "top3pair_46_trio" in EXCLUDED_STRATEGY_KEYS:
            top3pair_46_trio_valid = False
            top3pair_46_trio_hit_flag = 0
            top3pair_46_trio_refund = 0.0
        if "top3pair_47_trio" in EXCLUDED_STRATEGY_KEYS:
            top3pair_47_trio_valid = False
            top3pair_47_trio_hit_flag = 0
            top3pair_47_trio_refund = 0.0
        if "top3pair_49_trio" in EXCLUDED_STRATEGY_KEYS:
            top3pair_49_trio_valid = False
            top3pair_49_trio_hit_flag = 0
            top3pair_49_trio_refund = 0.0
        if "top4pair_58_trio" in EXCLUDED_STRATEGY_KEYS:
            top4pair_58_trio_valid = False
            top4pair_58_trio_hit_flag = 0
            top4pair_58_trio_refund = 0.0
        if "top12anchor_3_10_trio" in EXCLUDED_STRATEGY_KEYS:
            top12anchor_3_10_trio_valid = False
            top12anchor_3_10_trio_hit_flag = 0
            top12anchor_3_10_trio_refund = 0.0
        if "top12anchor_3_8_12_trio" in EXCLUDED_STRATEGY_KEYS:
            top12anchor_3_8_12_trio_valid = False
            top12anchor_3_8_12_trio_hit_flag = 0
            top12anchor_3_8_12_trio_refund = 0.0
        if "top12anchor_3_12_trio" in EXCLUDED_STRATEGY_KEYS:
            top12anchor_3_12_trio_valid = False
            top12anchor_3_12_trio_hit_flag = 0
            top12anchor_3_12_trio_refund = 0.0
        if "anchor3_24" in EXCLUDED_STRATEGY_KEYS:
            anchor3_24_valid = False
            anchor3_24_hit_flag = 0
            anchor3_24_refund = 0.0
        if "anchor2_24" in EXCLUDED_STRATEGY_KEYS:
            anchor2_24_valid = False
            anchor2_24_hit_flag = 0
            anchor2_24_refund = 0.0
        if "anchor1_25_68" in EXCLUDED_STRATEGY_KEYS:
            anchor1_25_68_valid = False
            anchor1_25_68_hit_flag = 0
            anchor1_25_68_refund = 0.0
        if "anchor1_25_69" in EXCLUDED_STRATEGY_KEYS:
            anchor1_25_69_valid = False
            anchor1_25_69_hit_flag = 0
            anchor1_25_69_refund = 0.0
        if "anchor1_69_25" in EXCLUDED_STRATEGY_KEYS:
            anchor1_69_25_valid = False
            anchor1_69_25_hit_flag = 0
            anchor1_69_25_refund = 0.0
        if "anchor12_3_10" in EXCLUDED_STRATEGY_KEYS:
            anchor12_3_10_valid = False
            anchor12_3_10_hit_flag = 0
            anchor12_3_10_refund = 0.0
        hit_any = int(
            anchor1_24_57_hit_flag
            or anchor1_24_quinella_hit_flag
            or anchor1_26_quinella_hit_flag
            or top3pair_46_quinella_hit_flag
            or anchor12_3_4_quinella_hit_flag
            or anchor12_3_5_quinella_hit_flag
            or anchor12_3_6_quinella_hit_flag
            or anchor12_3_7_quinella_hit_flag
            or anchor12_3_8_quinella_hit_flag
            or anchor12_3_12_quinella_hit_flag
            or anchor1_24_58_hit_flag
            or top4_box_trifecta_hit_flag
            or top5_box_trifecta_hit_flag
            or top6_trio_hit_flag
            or top3pair_46_trio_hit_flag
            or top3pair_47_trio_hit_flag
            or top3pair_49_trio_hit_flag
            or top4pair_58_trio_hit_flag
            or top12anchor_3_10_trio_hit_flag
            or top12anchor_3_8_12_trio_hit_flag
            or top12anchor_3_12_trio_hit_flag
            or anchor1_57_24_hit_flag
            or anchor1_58_24_hit_flag
            or anchor3_24_hit_flag
            or anchor2_24_hit_flag
            or anchor1_24_hit_flag
            or anchor1_25_hit_flag
            or anchor1_25_68_hit_flag
            or anchor1_25_69_hit_flag
            or anchor1_69_25_hit_flag
            or anchor1_23_46_hit_flag
            or anchor1_23_47_hit_flag
            or anchor1_23_48_hit_flag
            or anchor1_23_49_hit_flag
            or anchor12_3_7_hit_flag
            or anchor12_3_10_hit_flag
        )
        strategy_results = (
            ("anchor1_24_57", anchor1_24_57_valid, anchor1_24_57_bet_per_race, anchor1_24_57_refund, anchor1_24_57_hit_flag),
            ("anchor1_24_quinella", anchor1_24_quinella_valid, anchor1_24_quinella_bet_per_race, anchor1_24_quinella_refund, anchor1_24_quinella_hit_flag),
            ("anchor1_26_quinella", anchor1_26_quinella_valid, anchor1_26_quinella_bet_per_race, anchor1_26_quinella_refund, anchor1_26_quinella_hit_flag),
            ("top3pair_46_quinella", top3pair_46_quinella_valid, top3pair_46_quinella_bet_per_race, top3pair_46_quinella_refund, top3pair_46_quinella_hit_flag),
            ("anchor12_3_4_quinella", anchor12_3_4_quinella_valid, anchor12_3_4_quinella_bet_per_race_current, anchor12_3_4_quinella_refund, anchor12_3_4_quinella_hit_flag),
            ("anchor12_3_5_quinella", anchor12_3_5_quinella_valid, anchor12_3_5_quinella_bet_per_race_current, anchor12_3_5_quinella_refund, anchor12_3_5_quinella_hit_flag),
            ("anchor12_3_6_quinella", anchor12_3_6_quinella_valid, anchor12_3_6_quinella_bet_per_race_current, anchor12_3_6_quinella_refund, anchor12_3_6_quinella_hit_flag),
            ("anchor12_3_7_quinella", anchor12_3_7_quinella_valid, anchor12_3_7_quinella_bet_per_race_current, anchor12_3_7_quinella_refund, anchor12_3_7_quinella_hit_flag),
            ("anchor12_3_8_quinella", anchor12_3_8_quinella_valid, anchor12_3_8_quinella_bet_per_race_current, anchor12_3_8_quinella_refund, anchor12_3_8_quinella_hit_flag),
            ("anchor12_3_12_quinella", anchor12_3_12_quinella_valid, anchor12_3_12_quinella_bet_per_race_current, anchor12_3_12_quinella_refund, anchor12_3_12_quinella_hit_flag),
            ("anchor1_24_58", anchor1_24_58_valid, anchor1_24_58_bet_per_race, anchor1_24_58_refund, anchor1_24_58_hit_flag),
            ("top4_box_trifecta", top4_box_trifecta_valid, top4_box_trifecta_bet_per_race, top4_box_trifecta_refund, top4_box_trifecta_hit_flag),
            ("top5_box_trifecta", top5_box_trifecta_valid, top5_box_trifecta_bet_per_race, top5_box_trifecta_refund, top5_box_trifecta_hit_flag),
            ("top6_trio", top6_trio_valid, top6_trio_bet_per_race, top6_trio_refund, top6_trio_hit_flag),
            ("top3pair_46_trio", top3pair_46_trio_valid, top3pair_46_trio_bet_per_race, top3pair_46_trio_refund, top3pair_46_trio_hit_flag),
            ("top3pair_47_trio", top3pair_47_trio_valid, top3pair_47_trio_bet_per_race, top3pair_47_trio_refund, top3pair_47_trio_hit_flag),
            ("top3pair_49_trio", top3pair_49_trio_valid, top3pair_49_trio_bet_per_race, top3pair_49_trio_refund, top3pair_49_trio_hit_flag),
            ("top4pair_58_trio", top4pair_58_trio_valid, top4pair_58_trio_bet_per_race, top4pair_58_trio_refund, top4pair_58_trio_hit_flag),
            ("top12anchor_3_10_trio", top12anchor_3_10_trio_valid, top12anchor_3_10_trio_bet_per_race, top12anchor_3_10_trio_refund, top12anchor_3_10_trio_hit_flag),
            ("top12anchor_3_8_12_trio", top12anchor_3_8_12_trio_valid, top12anchor_3_8_12_bet_per_race_current, top12anchor_3_8_12_trio_refund, top12anchor_3_8_12_trio_hit_flag),
            ("top12anchor_3_12_trio", top12anchor_3_12_trio_valid, top12anchor_3_12_bet_per_race_current, top12anchor_3_12_trio_refund, top12anchor_3_12_trio_hit_flag),
            ("anchor1_57_24", anchor1_57_24_valid, anchor1_57_24_bet_per_race, anchor1_57_24_refund, anchor1_57_24_hit_flag),
            ("anchor1_58_24", anchor1_58_24_valid, anchor1_58_24_bet_per_race, anchor1_58_24_refund, anchor1_58_24_hit_flag),
            ("anchor3_24", anchor3_24_valid, anchor3_24_bet_per_race, anchor3_24_refund, anchor3_24_hit_flag),
            ("anchor2_24", anchor2_24_valid, anchor2_24_bet_per_race, anchor2_24_refund, anchor2_24_hit_flag),
            ("anchor1_24", anchor1_24_valid, anchor1_24_bet_per_race, anchor1_24_refund, anchor1_24_hit_flag),
            ("anchor1_25", anchor1_25_valid, anchor1_25_bet_per_race, anchor1_25_refund, anchor1_25_hit_flag),
            ("anchor1_25_68", anchor1_25_68_valid, anchor1_25_68_bet_per_race, anchor1_25_68_refund, anchor1_25_68_hit_flag),
            ("anchor1_25_69", anchor1_25_69_valid, anchor1_25_69_bet_per_race, anchor1_25_69_refund, anchor1_25_69_hit_flag),
            ("anchor1_69_25", anchor1_69_25_valid, anchor1_69_25_bet_per_race, anchor1_69_25_refund, anchor1_69_25_hit_flag),
            ("anchor1_23_46", anchor1_23_46_valid, anchor1_23_46_bet_per_race, anchor1_23_46_refund, anchor1_23_46_hit_flag),
            ("anchor1_23_47", anchor1_23_47_valid, anchor1_23_47_bet_per_race, anchor1_23_47_refund, anchor1_23_47_hit_flag),
            ("anchor1_23_48", anchor1_23_48_valid, anchor1_23_48_bet_per_race, anchor1_23_48_refund, anchor1_23_48_hit_flag),
            ("anchor1_23_49", anchor1_23_49_valid, anchor1_23_49_bet_per_race, anchor1_23_49_refund, anchor1_23_49_hit_flag),
            ("anchor12_3_7", anchor12_3_7_valid, anchor12_3_7_bet_per_race, anchor12_3_7_refund, anchor12_3_7_hit_flag),
            ("anchor12_3_10", anchor12_3_10_valid, anchor12_3_10_bet_per_race, anchor12_3_10_refund, anchor12_3_10_hit_flag),
        )
        anchor1_24_57_total_bet += (
            anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
        )
        anchor1_24_57_total_refund += anchor1_24_57_refund
        anchor1_24_57_total_hits += anchor1_24_57_hit_flag
        anchor1_24_quinella_total_bet += (
            anchor1_24_quinella_bet_per_race if anchor1_24_quinella_valid else 0.0
        )
        anchor1_24_quinella_total_refund += anchor1_24_quinella_refund
        anchor1_24_quinella_total_hits += anchor1_24_quinella_hit_flag
        anchor1_26_quinella_total_bet += (
            anchor1_26_quinella_bet_per_race if anchor1_26_quinella_valid else 0.0
        )
        anchor1_26_quinella_total_refund += anchor1_26_quinella_refund
        anchor1_26_quinella_total_hits += anchor1_26_quinella_hit_flag
        top3pair_46_quinella_total_bet += (
            top3pair_46_quinella_bet_per_race if top3pair_46_quinella_valid else 0.0
        )
        top3pair_46_quinella_total_refund += top3pair_46_quinella_refund
        top3pair_46_quinella_total_hits += top3pair_46_quinella_hit_flag
        anchor12_3_4_quinella_total_bet += (
            anchor12_3_4_quinella_bet_per_race_current
            if anchor12_3_4_quinella_valid
            else 0.0
        )
        anchor12_3_4_quinella_total_refund += anchor12_3_4_quinella_refund
        anchor12_3_4_quinella_total_hits += anchor12_3_4_quinella_hit_flag
        anchor12_3_5_quinella_total_bet += (
            anchor12_3_5_quinella_bet_per_race_current
            if anchor12_3_5_quinella_valid
            else 0.0
        )
        anchor12_3_5_quinella_total_refund += anchor12_3_5_quinella_refund
        anchor12_3_5_quinella_total_hits += anchor12_3_5_quinella_hit_flag
        anchor12_3_6_quinella_total_bet += (
            anchor12_3_6_quinella_bet_per_race_current
            if anchor12_3_6_quinella_valid
            else 0.0
        )
        anchor12_3_6_quinella_total_refund += anchor12_3_6_quinella_refund
        anchor12_3_6_quinella_total_hits += anchor12_3_6_quinella_hit_flag
        anchor12_3_7_quinella_total_bet += (
            anchor12_3_7_quinella_bet_per_race_current
            if anchor12_3_7_quinella_valid
            else 0.0
        )
        anchor12_3_7_quinella_total_refund += anchor12_3_7_quinella_refund
        anchor12_3_7_quinella_total_hits += anchor12_3_7_quinella_hit_flag
        anchor12_3_8_quinella_total_bet += (
            anchor12_3_8_quinella_bet_per_race_current
            if anchor12_3_8_quinella_valid
            else 0.0
        )
        anchor12_3_8_quinella_total_refund += anchor12_3_8_quinella_refund
        anchor12_3_8_quinella_total_hits += anchor12_3_8_quinella_hit_flag
        anchor12_3_12_quinella_total_bet += (
            anchor12_3_12_quinella_bet_per_race_current
            if anchor12_3_12_quinella_valid
            else 0.0
        )
        anchor12_3_12_quinella_total_refund += anchor12_3_12_quinella_refund
        anchor12_3_12_quinella_total_hits += anchor12_3_12_quinella_hit_flag
        anchor1_24_58_total_bet += (
            anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0
        )
        anchor1_24_58_total_refund += anchor1_24_58_refund
        anchor1_24_58_total_hits += anchor1_24_58_hit_flag
        top4_box_trifecta_total_bet += (
            top4_box_trifecta_bet_per_race if top4_box_trifecta_valid else 0.0
        )
        top4_box_trifecta_total_refund += top4_box_trifecta_refund
        top4_box_trifecta_total_hits += top4_box_trifecta_hit_flag
        top5_box_trifecta_total_bet += (
            top5_box_trifecta_bet_per_race if top5_box_trifecta_valid else 0.0
        )
        top5_box_trifecta_total_refund += top5_box_trifecta_refund
        top5_box_trifecta_total_hits += top5_box_trifecta_hit_flag
        top6_trio_total_bet += (
            top6_trio_bet_per_race if top6_trio_valid else 0.0
        )
        top6_trio_total_refund += top6_trio_refund
        top6_trio_total_hits += top6_trio_hit_flag
        top3pair_46_trio_total_bet += (
            top3pair_46_trio_bet_per_race if top3pair_46_trio_valid else 0.0
        )
        top3pair_46_trio_total_refund += top3pair_46_trio_refund
        top3pair_46_trio_total_hits += top3pair_46_trio_hit_flag
        top3pair_47_trio_total_bet += (
            top3pair_47_trio_bet_per_race if top3pair_47_trio_valid else 0.0
        )
        top3pair_47_trio_total_refund += top3pair_47_trio_refund
        top3pair_47_trio_total_hits += top3pair_47_trio_hit_flag
        top3pair_49_trio_total_bet += (
            top3pair_49_trio_bet_per_race if top3pair_49_trio_valid else 0.0
        )
        top3pair_49_trio_total_refund += top3pair_49_trio_refund
        top3pair_49_trio_total_hits += top3pair_49_trio_hit_flag
        top4pair_58_trio_total_bet += (
            top4pair_58_trio_bet_per_race if top4pair_58_trio_valid else 0.0
        )
        top4pair_58_trio_total_refund += top4pair_58_trio_refund
        top4pair_58_trio_total_hits += top4pair_58_trio_hit_flag
        top12anchor_3_10_trio_total_bet += (
            top12anchor_3_10_trio_bet_per_race if top12anchor_3_10_trio_valid else 0.0
        )
        top12anchor_3_10_trio_total_refund += top12anchor_3_10_trio_refund
        top12anchor_3_10_trio_total_hits += top12anchor_3_10_trio_hit_flag
        top12anchor_3_8_12_trio_total_bet += (
            top12anchor_3_8_12_bet_per_race_current
            if top12anchor_3_8_12_trio_valid
            else 0.0
        )
        top12anchor_3_8_12_trio_total_refund += top12anchor_3_8_12_trio_refund
        top12anchor_3_8_12_trio_total_hits += top12anchor_3_8_12_trio_hit_flag
        top12anchor_3_12_trio_total_bet += (
            top12anchor_3_12_bet_per_race_current if top12anchor_3_12_trio_valid else 0.0
        )
        top12anchor_3_12_trio_total_refund += top12anchor_3_12_trio_refund
        top12anchor_3_12_trio_total_hits += top12anchor_3_12_trio_hit_flag
        anchor1_57_24_total_bet += (
            anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0
        )
        anchor1_57_24_total_refund += anchor1_57_24_refund
        anchor1_57_24_total_hits += anchor1_57_24_hit_flag
        anchor1_58_24_total_bet += (
            anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0
        )
        anchor1_58_24_total_refund += anchor1_58_24_refund
        anchor1_58_24_total_hits += anchor1_58_24_hit_flag
        anchor3_24_total_bet += anchor3_24_bet_per_race if anchor3_24_valid else 0.0
        anchor3_24_total_refund += anchor3_24_refund
        anchor3_24_total_hits += anchor3_24_hit_flag
        anchor2_24_total_bet += anchor2_24_bet_per_race if anchor2_24_valid else 0.0
        anchor2_24_total_refund += anchor2_24_refund
        anchor2_24_total_hits += anchor2_24_hit_flag
        anchor1_24_total_bet += anchor1_24_bet_per_race if anchor1_24_valid else 0.0
        anchor1_24_total_refund += anchor1_24_refund
        anchor1_24_total_hits += anchor1_24_hit_flag
        anchor1_25_total_bet += anchor1_25_bet_per_race if anchor1_25_valid else 0.0
        anchor1_25_total_refund += anchor1_25_refund
        anchor1_25_total_hits += anchor1_25_hit_flag
        anchor1_25_68_total_bet += (
            anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0
        )
        anchor1_25_68_total_refund += anchor1_25_68_refund
        anchor1_25_68_total_hits += anchor1_25_68_hit_flag
        anchor1_25_69_total_bet += (
            anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0
        )
        anchor1_25_69_total_refund += anchor1_25_69_refund
        anchor1_25_69_total_hits += anchor1_25_69_hit_flag
        anchor1_69_25_total_bet += (
            anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0
        )
        anchor1_69_25_total_refund += anchor1_69_25_refund
        anchor1_69_25_total_hits += anchor1_69_25_hit_flag
        anchor1_23_46_total_bet += (
            anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0
        )
        anchor1_23_46_total_refund += anchor1_23_46_refund
        anchor1_23_46_total_hits += anchor1_23_46_hit_flag
        anchor1_23_47_total_bet += (
            anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0
        )
        anchor1_23_47_total_refund += anchor1_23_47_refund
        anchor1_23_47_total_hits += anchor1_23_47_hit_flag
        anchor1_23_48_total_bet += (
            anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0
        )
        anchor1_23_48_total_refund += anchor1_23_48_refund
        anchor1_23_48_total_hits += anchor1_23_48_hit_flag
        anchor1_23_49_total_bet += (
            anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0
        )
        anchor1_23_49_total_refund += anchor1_23_49_refund
        anchor1_23_49_total_hits += anchor1_23_49_hit_flag
        anchor12_3_7_total_bet += (
            anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0
        )
        anchor12_3_7_total_refund += anchor12_3_7_refund
        anchor12_3_7_total_hits += anchor12_3_7_hit_flag
        anchor12_3_10_total_bet += (
            anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0
        )
        anchor12_3_10_total_refund += anchor12_3_10_refund
        anchor12_3_10_total_hits += anchor12_3_10_hit_flag
        total_hits_any += hit_any
        for strategy_key, valid, bet_per_race, refund, hit_flag in strategy_results:
            if strategy_key not in strategy_track_summary:
                strategy_track_summary[strategy_key] = {}
            if track not in strategy_track_summary[strategy_key]:
                strategy_track_summary[strategy_key][track] = {
                    "races": 0,
                    "total_bet": 0.0,
                    "total_refund": 0.0,
                    "hits": 0,
                }
            strategy_track_summary[strategy_key][track]["races"] += 1
            strategy_track_summary[strategy_key][track]["total_bet"] += (
                bet_per_race if valid else 0.0
            )
            strategy_track_summary[strategy_key][track]["total_refund"] += refund
            strategy_track_summary[strategy_key][track]["hits"] += hit_flag

        if track not in track_summary:
            track_summary[track] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
                "r_pop1_top1_hits": 0,
                "r_pop1_top3_hits": 0,
            }
        track_summary[track]["races"] += 1
        track_summary[track]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0)
            + (
                top4_box_trifecta_bet_per_race if top4_box_trifecta_valid else 0.0
            )
            + (
                top5_box_trifecta_bet_per_race if top5_box_trifecta_valid else 0.0
            )
            + (top6_trio_bet_per_race if top6_trio_valid else 0.0)
            + (
                top3pair_46_trio_bet_per_race if top3pair_46_trio_valid else 0.0
            )
            + (
                top3pair_47_trio_bet_per_race if top3pair_47_trio_valid else 0.0
            )
            + (
                top3pair_49_trio_bet_per_race if top3pair_49_trio_valid else 0.0
            )
            + (
                top4pair_58_trio_bet_per_race if top4pair_58_trio_valid else 0.0
            )
            + (
                top12anchor_3_10_trio_bet_per_race
                if top12anchor_3_10_trio_valid
                else 0.0
            )
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0)
            + (anchor3_24_bet_per_race if anchor3_24_valid else 0.0)
            + (anchor2_24_bet_per_race if anchor2_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (anchor1_25_bet_per_race if anchor1_25_valid else 0.0)
            + (anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0)
            + (anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0)
            + (anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0)
            + (anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0)
            + (anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0)
            + (anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0)
            + (anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0)
            + (anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0)
            + (anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0)
        )
        track_summary[track]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_24_58_refund
            + top4_box_trifecta_refund
            + top5_box_trifecta_refund
            + top6_trio_refund
            + top3pair_46_trio_refund
            + top3pair_47_trio_refund
            + top3pair_49_trio_refund
            + top4pair_58_trio_refund
            + top12anchor_3_10_trio_refund
            + anchor1_57_24_refund
            + anchor1_58_24_refund
            + anchor3_24_refund
            + anchor2_24_refund
            + anchor1_24_refund
            + anchor1_25_refund
            + anchor1_25_68_refund
            + anchor1_25_69_refund
            + anchor1_69_25_refund
            + anchor1_23_46_refund
            + anchor1_23_47_refund
            + anchor1_23_48_refund
            + anchor1_23_49_refund
            + anchor12_3_7_refund
            + anchor12_3_10_refund
        )
        track_summary[track]["hits"] += hit_any
        track_summary[track]["r_pop1_top1_hits"] += r_pop1_top1_hit
        track_summary[track]["r_pop1_top3_hits"] += r_pop1_top3_hit
        track_month_key = (track, year_month)
        if track_month_key not in track_month_summary:
            track_month_summary[track_month_key] = {
                "track": track,
                "year_month": year_month,
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
                "r_pop1_top1_hits": 0,
                "r_pop1_top3_hits": 0,
            }
        track_month_summary[track_month_key]["races"] += 1
        track_month_summary[track_month_key]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0)
            + (
                top4_box_trifecta_bet_per_race if top4_box_trifecta_valid else 0.0
            )
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0)
            + (anchor3_24_bet_per_race if anchor3_24_valid else 0.0)
            + (anchor2_24_bet_per_race if anchor2_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (anchor1_25_bet_per_race if anchor1_25_valid else 0.0)
            + (anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0)
            + (anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0)
            + (anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0)
            + (anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0)
            + (anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0)
            + (anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0)
            + (anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0)
            + (anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0)
            + (anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0)
        )
        track_month_summary[track_month_key]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_24_58_refund
            + top4_box_trifecta_refund
            + anchor1_57_24_refund
            + anchor1_58_24_refund
            + anchor3_24_refund
            + anchor2_24_refund
            + anchor1_24_refund
            + anchor1_25_refund
            + anchor1_25_68_refund
            + anchor1_25_69_refund
            + anchor1_69_25_refund
            + anchor1_23_46_refund
            + anchor1_23_47_refund
            + anchor1_23_48_refund
            + anchor1_23_49_refund
            + anchor12_3_7_refund
            + anchor12_3_10_refund
        )
        track_month_summary[track_month_key]["hits"] += hit_any
        track_month_summary[track_month_key]["r_pop1_top1_hits"] += r_pop1_top1_hit
        track_month_summary[track_month_key]["r_pop1_top3_hits"] += r_pop1_top3_hit

        date_dt = pd.to_datetime(date, format="%Y%m%d", errors="coerce")
        if pd.notna(date_dt):
            weekday = date_dt.weekday()
            # Saturday-centered 5-day bucket: Thu/Fri/Sat/Sun/Mon map to that Saturday.
            # Tue/Wed fall outside +/-2 days, so they map to the next Saturday.
            sat_offset = {0: -2, 1: 4, 2: 3, 3: 2, 4: 1, 5: 0, 6: -1}[weekday]
            week_key = (date_dt + pd.to_timedelta(sat_offset, unit="D")).strftime(
                "%Y%m%d"
            )
        else:
            week_key = date
        if week_key not in week_summary:
            week_summary[week_key] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        week_track_key = (week_key, track)
        if week_track_key not in week_track_summary:
            week_track_summary[week_track_key] = {
                "week": week_key,
                "track": track,
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary:
            month_summary[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
                "r_pop1_top1_hits": 0,
                "r_pop1_top3_hits": 0,
            }
        if year_month not in month_summary_rpop5_7_anchor_1_4_trio:
            month_summary_rpop5_7_anchor_1_4_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_rpop5_8_anchor_1_4_trio:
            month_summary_rpop5_8_anchor_1_4_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_24_57:
            month_summary_anchor_24_57[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_24_58:
            month_summary_anchor_24_58[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top4_box_trifecta:
            month_summary_top4_box_trifecta[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top5_box_trifecta:
            month_summary_top5_box_trifecta[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor1_24_quinella:
            month_summary_anchor1_24_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor1_26_quinella:
            month_summary_anchor1_26_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top3pair_46_quinella:
            month_summary_top3pair_46_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_3_4_quinella:
            month_summary_anchor12_3_4_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_3_5_quinella:
            month_summary_anchor12_3_5_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_3_6_quinella:
            month_summary_anchor12_3_6_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_3_7_quinella:
            month_summary_anchor12_3_7_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_3_8_quinella:
            month_summary_anchor12_3_8_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_3_12_quinella:
            month_summary_anchor12_3_12_quinella[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top6_trio:
            month_summary_top6_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top3pair_46_trio:
            month_summary_top3pair_46_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top3pair_47_trio:
            month_summary_top3pair_47_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top3pair_49_trio:
            month_summary_top3pair_49_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top4pair_58_trio:
            month_summary_top4pair_58_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top12anchor_3_10_trio:
            month_summary_top12anchor_3_10_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top12anchor_3_8_12_trio:
            month_summary_top12anchor_3_8_12_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top12anchor_3_12_trio:
            month_summary_top12anchor_3_12_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor3_24:
            month_summary_anchor3_24[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor2_24:
            month_summary_anchor2_24[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_24:
            month_summary_anchor_24[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_25:
            month_summary_anchor_25[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_25_68:
            month_summary_anchor_25_68[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_25_69:
            month_summary_anchor_25_69[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_69_25:
            month_summary_anchor_69_25[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_23_46:
            month_summary_anchor_23_46[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_23_47:
            month_summary_anchor_23_47[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_23_48:
            month_summary_anchor_23_48[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor_23_49:
            month_summary_anchor_23_49[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_3_7:
            month_summary_anchor12_3_7[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_3_10:
            month_summary_anchor12_3_10[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_summary[year_month]["races"] += 1
        week_summary[week_key]["races"] += 1
        month_summary[year_month]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_quinella_bet_per_race if anchor1_24_quinella_valid else 0.0)
            + (anchor1_26_quinella_bet_per_race if anchor1_26_quinella_valid else 0.0)
            + (
                top3pair_46_quinella_bet_per_race
                if top3pair_46_quinella_valid
                else 0.0
            )
            + (
                anchor12_3_4_quinella_bet_per_race_current
                if anchor12_3_4_quinella_valid
                else 0.0
            )
            + (
                anchor12_3_5_quinella_bet_per_race_current
                if anchor12_3_5_quinella_valid
                else 0.0
            )
            + (anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0)
            + (
                top4_box_trifecta_bet_per_race if top4_box_trifecta_valid else 0.0
            )
            + (
                top5_box_trifecta_bet_per_race if top5_box_trifecta_valid else 0.0
            )
            + (top6_trio_bet_per_race if top6_trio_valid else 0.0)
            + (
                top3pair_46_trio_bet_per_race if top3pair_46_trio_valid else 0.0
            )
            + (
                top3pair_47_trio_bet_per_race if top3pair_47_trio_valid else 0.0
            )
            + (
                top3pair_49_trio_bet_per_race if top3pair_49_trio_valid else 0.0
            )
            + (
                top4pair_58_trio_bet_per_race if top4pair_58_trio_valid else 0.0
            )
            + (
                top12anchor_3_10_trio_bet_per_race
                if top12anchor_3_10_trio_valid
                else 0.0
            )
            + (
                top12anchor_3_8_12_bet_per_race_current
                if top12anchor_3_8_12_trio_valid
                else 0.0
            )
            + (
                top12anchor_3_12_bet_per_race_current
                if top12anchor_3_12_trio_valid
                else 0.0
            )
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0)
            + (anchor3_24_bet_per_race if anchor3_24_valid else 0.0)
            + (anchor2_24_bet_per_race if anchor2_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (anchor1_25_bet_per_race if anchor1_25_valid else 0.0)
            + (anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0)
            + (anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0)
            + (anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0)
            + (anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0)
            + (anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0)
            + (anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0)
            + (anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0)
            + (anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0)
            + (anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0)
        )
        week_summary[week_key]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_quinella_bet_per_race if anchor1_24_quinella_valid else 0.0)
            + (anchor1_26_quinella_bet_per_race if anchor1_26_quinella_valid else 0.0)
            + (
                top3pair_46_quinella_bet_per_race
                if top3pair_46_quinella_valid
                else 0.0
            )
            + (
                anchor12_3_4_quinella_bet_per_race_current
                if anchor12_3_4_quinella_valid
                else 0.0
            )
            + (
                anchor12_3_5_quinella_bet_per_race_current
                if anchor12_3_5_quinella_valid
                else 0.0
            )
            + (anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0)
            + (
                top4_box_trifecta_bet_per_race if top4_box_trifecta_valid else 0.0
            )
            + (
                top5_box_trifecta_bet_per_race if top5_box_trifecta_valid else 0.0
            )
            + (top6_trio_bet_per_race if top6_trio_valid else 0.0)
            + (
                top3pair_46_trio_bet_per_race if top3pair_46_trio_valid else 0.0
            )
            + (
                top3pair_47_trio_bet_per_race if top3pair_47_trio_valid else 0.0
            )
            + (
                top3pair_49_trio_bet_per_race if top3pair_49_trio_valid else 0.0
            )
            + (
                top4pair_58_trio_bet_per_race if top4pair_58_trio_valid else 0.0
            )
            + (
                top12anchor_3_10_trio_bet_per_race
                if top12anchor_3_10_trio_valid
                else 0.0
            )
            + (
                top12anchor_3_8_12_bet_per_race_current
                if top12anchor_3_8_12_trio_valid
                else 0.0
            )
            + (
                top12anchor_3_12_bet_per_race_current
                if top12anchor_3_12_trio_valid
                else 0.0
            )
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0)
            + (anchor3_24_bet_per_race if anchor3_24_valid else 0.0)
            + (anchor2_24_bet_per_race if anchor2_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (anchor1_25_bet_per_race if anchor1_25_valid else 0.0)
            + (anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0)
            + (anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0)
            + (anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0)
            + (anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0)
            + (anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0)
            + (anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0)
            + (anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0)
            + (anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0)
            + (anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0)
        )
        month_summary[year_month]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_24_quinella_refund
            + anchor1_26_quinella_refund
            + top3pair_46_quinella_refund
            + anchor12_3_4_quinella_refund
            + anchor12_3_5_quinella_refund
            + anchor1_24_58_refund
            + top4_box_trifecta_refund
            + top5_box_trifecta_refund
            + top6_trio_refund
            + top3pair_46_trio_refund
            + top3pair_47_trio_refund
            + top3pair_49_trio_refund
            + top4pair_58_trio_refund
            + top12anchor_3_10_trio_refund
            + top12anchor_3_8_12_trio_refund
            + top12anchor_3_12_trio_refund
            + anchor1_57_24_refund
            + anchor1_58_24_refund
            + anchor3_24_refund
            + anchor2_24_refund
            + anchor1_24_refund
            + anchor1_25_refund
            + anchor1_25_68_refund
            + anchor1_25_69_refund
            + anchor1_69_25_refund
            + anchor1_23_46_refund
            + anchor1_23_47_refund
            + anchor1_23_48_refund
            + anchor1_23_49_refund
            + anchor12_3_7_refund
            + anchor12_3_10_refund
        )
        week_summary[week_key]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_24_quinella_refund
            + anchor1_26_quinella_refund
            + top3pair_46_quinella_refund
            + anchor12_3_4_quinella_refund
            + anchor12_3_5_quinella_refund
            + anchor1_24_58_refund
            + top4_box_trifecta_refund
            + top5_box_trifecta_refund
            + top6_trio_refund
            + top3pair_46_trio_refund
            + top3pair_47_trio_refund
            + top3pair_49_trio_refund
            + top4pair_58_trio_refund
            + top12anchor_3_10_trio_refund
            + top12anchor_3_8_12_trio_refund
            + top12anchor_3_12_trio_refund
            + anchor1_57_24_refund
            + anchor1_58_24_refund
            + anchor3_24_refund
            + anchor2_24_refund
            + anchor1_24_refund
            + anchor1_25_refund
            + anchor1_25_68_refund
            + anchor1_25_69_refund
            + anchor1_69_25_refund
            + anchor1_23_46_refund
            + anchor1_23_47_refund
            + anchor1_23_48_refund
            + anchor1_23_49_refund
            + anchor12_3_7_refund
            + anchor12_3_10_refund
        )
        month_summary[year_month]["hits"] += hit_any
        week_summary[week_key]["hits"] += hit_any
        week_track_summary[week_track_key]["races"] += 1
        week_track_summary[week_track_key]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_quinella_bet_per_race if anchor1_24_quinella_valid else 0.0)
            + (anchor1_26_quinella_bet_per_race if anchor1_26_quinella_valid else 0.0)
            + (
                top3pair_46_quinella_bet_per_race
                if top3pair_46_quinella_valid
                else 0.0
            )
            + (
                anchor12_3_4_quinella_bet_per_race_current
                if anchor12_3_4_quinella_valid
                else 0.0
            )
            + (
                anchor12_3_5_quinella_bet_per_race_current
                if anchor12_3_5_quinella_valid
                else 0.0
            )
            + (anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0)
            + (
                top4_box_trifecta_bet_per_race if top4_box_trifecta_valid else 0.0
            )
            + (
                top5_box_trifecta_bet_per_race if top5_box_trifecta_valid else 0.0
            )
            + (top6_trio_bet_per_race if top6_trio_valid else 0.0)
            + (
                top3pair_46_trio_bet_per_race if top3pair_46_trio_valid else 0.0
            )
            + (
                top3pair_47_trio_bet_per_race if top3pair_47_trio_valid else 0.0
            )
            + (
                top3pair_49_trio_bet_per_race if top3pair_49_trio_valid else 0.0
            )
            + (
                top4pair_58_trio_bet_per_race if top4pair_58_trio_valid else 0.0
            )
            + (
                top12anchor_3_10_trio_bet_per_race
                if top12anchor_3_10_trio_valid
                else 0.0
            )
            + (
                top12anchor_3_8_12_bet_per_race_current
                if top12anchor_3_8_12_trio_valid
                else 0.0
            )
            + (
                top12anchor_3_12_bet_per_race_current
                if top12anchor_3_12_trio_valid
                else 0.0
            )
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0)
            + (anchor3_24_bet_per_race if anchor3_24_valid else 0.0)
            + (anchor2_24_bet_per_race if anchor2_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (anchor1_25_bet_per_race if anchor1_25_valid else 0.0)
            + (anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0)
            + (anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0)
            + (anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0)
            + (anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0)
            + (anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0)
            + (anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0)
            + (anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0)
            + (anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0)
            + (anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0)
        )
        week_track_summary[week_track_key]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_24_quinella_refund
            + anchor1_26_quinella_refund
            + top3pair_46_quinella_refund
            + anchor12_3_4_quinella_refund
            + anchor12_3_5_quinella_refund
            + anchor1_24_58_refund
            + top4_box_trifecta_refund
            + top5_box_trifecta_refund
            + top6_trio_refund
            + top3pair_46_trio_refund
            + top3pair_47_trio_refund
            + top3pair_49_trio_refund
            + top4pair_58_trio_refund
            + top12anchor_3_10_trio_refund
            + top12anchor_3_8_12_trio_refund
            + top12anchor_3_12_trio_refund
            + anchor1_57_24_refund
            + anchor1_58_24_refund
            + anchor3_24_refund
            + anchor2_24_refund
            + anchor1_24_refund
            + anchor1_25_refund
            + anchor1_25_68_refund
            + anchor1_25_69_refund
            + anchor1_69_25_refund
            + anchor1_23_46_refund
            + anchor1_23_47_refund
            + anchor1_23_48_refund
            + anchor1_23_49_refund
            + anchor12_3_7_refund
            + anchor12_3_10_refund
        )
        week_track_summary[week_track_key]["hits"] += hit_any
        month_summary[year_month]["r_pop1_top1_hits"] += r_pop1_top1_hit
        month_summary[year_month]["r_pop1_top3_hits"] += r_pop1_top3_hit
        month_summary_anchor_24_57[year_month]["races"] += 1
        month_summary_anchor_24_57[year_month]["total_bet"] += (
            anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
        )
        month_summary_anchor_24_57[year_month][
            "total_refund"
        ] += anchor1_24_57_refund
        month_summary_anchor_24_57[year_month]["hits"] += anchor1_24_57_hit_flag
        month_summary_anchor1_24_quinella[year_month]["races"] += 1
        month_summary_anchor1_24_quinella[year_month]["total_bet"] += (
            anchor1_24_quinella_bet_per_race if anchor1_24_quinella_valid else 0.0
        )
        month_summary_anchor1_24_quinella[year_month]["total_refund"] += (
            anchor1_24_quinella_refund
        )
        month_summary_anchor1_24_quinella[year_month]["hits"] += (
            anchor1_24_quinella_hit_flag
        )
        month_summary_anchor1_26_quinella[year_month]["races"] += 1
        month_summary_anchor1_26_quinella[year_month]["total_bet"] += (
            anchor1_26_quinella_bet_per_race if anchor1_26_quinella_valid else 0.0
        )
        month_summary_anchor1_26_quinella[year_month]["total_refund"] += (
            anchor1_26_quinella_refund
        )
        month_summary_anchor1_26_quinella[year_month]["hits"] += (
            anchor1_26_quinella_hit_flag
        )
        month_summary_top3pair_46_quinella[year_month]["races"] += 1
        month_summary_top3pair_46_quinella[year_month]["total_bet"] += (
            top3pair_46_quinella_bet_per_race if top3pair_46_quinella_valid else 0.0
        )
        month_summary_top3pair_46_quinella[year_month]["total_refund"] += (
            top3pair_46_quinella_refund
        )
        month_summary_top3pair_46_quinella[year_month]["hits"] += (
            top3pair_46_quinella_hit_flag
        )
        month_summary_anchor12_3_4_quinella[year_month]["races"] += 1
        month_summary_anchor12_3_4_quinella[year_month]["total_bet"] += (
            anchor12_3_4_quinella_bet_per_race_current
            if anchor12_3_4_quinella_valid
            else 0.0
        )
        month_summary_anchor12_3_4_quinella[year_month]["total_refund"] += (
            anchor12_3_4_quinella_refund
        )
        month_summary_anchor12_3_4_quinella[year_month]["hits"] += (
            anchor12_3_4_quinella_hit_flag
        )
        month_summary_anchor12_3_5_quinella[year_month]["races"] += 1
        month_summary_anchor12_3_5_quinella[year_month]["total_bet"] += (
            anchor12_3_5_quinella_bet_per_race_current
            if anchor12_3_5_quinella_valid
            else 0.0
        )
        month_summary_anchor12_3_5_quinella[year_month]["total_refund"] += (
            anchor12_3_5_quinella_refund
        )
        month_summary_anchor12_3_5_quinella[year_month]["hits"] += (
            anchor12_3_5_quinella_hit_flag
        )
        month_summary_anchor12_3_6_quinella[year_month]["races"] += 1
        month_summary_anchor12_3_6_quinella[year_month]["total_bet"] += (
            anchor12_3_6_quinella_bet_per_race_current
            if anchor12_3_6_quinella_valid
            else 0.0
        )
        month_summary_anchor12_3_6_quinella[year_month]["total_refund"] += (
            anchor12_3_6_quinella_refund
        )
        month_summary_anchor12_3_6_quinella[year_month]["hits"] += (
            anchor12_3_6_quinella_hit_flag
        )
        month_summary_anchor12_3_7_quinella[year_month]["races"] += 1
        month_summary_anchor12_3_7_quinella[year_month]["total_bet"] += (
            anchor12_3_7_quinella_bet_per_race_current
            if anchor12_3_7_quinella_valid
            else 0.0
        )
        month_summary_anchor12_3_7_quinella[year_month]["total_refund"] += (
            anchor12_3_7_quinella_refund
        )
        month_summary_anchor12_3_7_quinella[year_month]["hits"] += (
            anchor12_3_7_quinella_hit_flag
        )
        month_summary_anchor12_3_8_quinella[year_month]["races"] += 1
        month_summary_anchor12_3_8_quinella[year_month]["total_bet"] += (
            anchor12_3_8_quinella_bet_per_race_current
            if anchor12_3_8_quinella_valid
            else 0.0
        )
        month_summary_anchor12_3_8_quinella[year_month]["total_refund"] += (
            anchor12_3_8_quinella_refund
        )
        month_summary_anchor12_3_8_quinella[year_month]["hits"] += (
            anchor12_3_8_quinella_hit_flag
        )
        month_summary_anchor12_3_12_quinella[year_month]["races"] += 1
        month_summary_anchor12_3_12_quinella[year_month]["total_bet"] += (
            anchor12_3_12_quinella_bet_per_race_current
            if anchor12_3_12_quinella_valid
            else 0.0
        )
        month_summary_anchor12_3_12_quinella[year_month]["total_refund"] += (
            anchor12_3_12_quinella_refund
        )
        month_summary_anchor12_3_12_quinella[year_month]["hits"] += (
            anchor12_3_12_quinella_hit_flag
        )
        month_summary_anchor_24_58[year_month]["races"] += 1
        month_summary_anchor_24_58[year_month]["total_bet"] += (
            anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0
        )
        month_summary_anchor_24_58[year_month][
            "total_refund"
        ] += anchor1_24_58_refund
        month_summary_anchor_24_58[year_month]["hits"] += anchor1_24_58_hit_flag
        month_summary_top4_box_trifecta[year_month]["races"] += 1
        month_summary_top4_box_trifecta[year_month]["total_bet"] += (
            top4_box_trifecta_bet_per_race if top4_box_trifecta_valid else 0.0
        )
        month_summary_top4_box_trifecta[year_month][
            "total_refund"
        ] += top4_box_trifecta_refund
        month_summary_top4_box_trifecta[year_month]["hits"] += (
            top4_box_trifecta_hit_flag
        )
        month_summary_top5_box_trifecta[year_month]["races"] += 1
        month_summary_top5_box_trifecta[year_month]["total_bet"] += (
            top5_box_trifecta_bet_per_race if top5_box_trifecta_valid else 0.0
        )
        month_summary_top5_box_trifecta[year_month][
            "total_refund"
        ] += top5_box_trifecta_refund
        month_summary_top5_box_trifecta[year_month]["hits"] += (
            top5_box_trifecta_hit_flag
        )
        month_summary_top6_trio[year_month]["races"] += 1
        month_summary_top6_trio[year_month]["total_bet"] += (
            top6_trio_bet_per_race if top6_trio_valid else 0.0
        )
        month_summary_top6_trio[year_month]["total_refund"] += top6_trio_refund
        month_summary_top6_trio[year_month]["hits"] += top6_trio_hit_flag
        month_summary_top3pair_46_trio[year_month]["races"] += 1
        month_summary_top3pair_46_trio[year_month]["total_bet"] += (
            top3pair_46_trio_bet_per_race if top3pair_46_trio_valid else 0.0
        )
        month_summary_top3pair_46_trio[year_month]["total_refund"] += (
            top3pair_46_trio_refund
        )
        month_summary_top3pair_46_trio[year_month]["hits"] += (
            top3pair_46_trio_hit_flag
        )
        month_summary_top3pair_47_trio[year_month]["races"] += 1
        month_summary_top3pair_47_trio[year_month]["total_bet"] += (
            top3pair_47_trio_bet_per_race if top3pair_47_trio_valid else 0.0
        )
        month_summary_top3pair_47_trio[year_month]["total_refund"] += (
            top3pair_47_trio_refund
        )
        month_summary_top3pair_47_trio[year_month]["hits"] += (
            top3pair_47_trio_hit_flag
        )
        month_summary_top3pair_49_trio[year_month]["races"] += 1
        month_summary_top3pair_49_trio[year_month]["total_bet"] += (
            top3pair_49_trio_bet_per_race if top3pair_49_trio_valid else 0.0
        )
        month_summary_top3pair_49_trio[year_month]["total_refund"] += (
            top3pair_49_trio_refund
        )
        month_summary_top3pair_49_trio[year_month]["hits"] += (
            top3pair_49_trio_hit_flag
        )
        month_summary_top4pair_58_trio[year_month]["races"] += 1
        month_summary_top4pair_58_trio[year_month]["total_bet"] += (
            top4pair_58_trio_bet_per_race if top4pair_58_trio_valid else 0.0
        )
        month_summary_top4pair_58_trio[year_month]["total_refund"] += (
            top4pair_58_trio_refund
        )
        month_summary_top4pair_58_trio[year_month]["hits"] += (
            top4pair_58_trio_hit_flag
        )
        month_summary_top12anchor_3_10_trio[year_month]["races"] += 1
        month_summary_top12anchor_3_10_trio[year_month]["total_bet"] += (
            top12anchor_3_10_trio_bet_per_race
            if top12anchor_3_10_trio_valid
            else 0.0
        )
        month_summary_top12anchor_3_10_trio[year_month]["total_refund"] += (
            top12anchor_3_10_trio_refund
        )
        month_summary_top12anchor_3_10_trio[year_month]["hits"] += (
            top12anchor_3_10_trio_hit_flag
        )
        month_summary_top12anchor_3_8_12_trio[year_month]["races"] += 1
        month_summary_top12anchor_3_8_12_trio[year_month]["total_bet"] += (
            top12anchor_3_8_12_bet_per_race_current
            if top12anchor_3_8_12_trio_valid
            else 0.0
        )
        month_summary_top12anchor_3_8_12_trio[year_month]["total_refund"] += (
            top12anchor_3_8_12_trio_refund
        )
        month_summary_top12anchor_3_8_12_trio[year_month]["hits"] += (
            top12anchor_3_8_12_trio_hit_flag
        )
        month_summary_top12anchor_3_12_trio[year_month]["races"] += 1
        month_summary_top12anchor_3_12_trio[year_month]["total_bet"] += (
            top12anchor_3_12_bet_per_race_current
            if top12anchor_3_12_trio_valid
            else 0.0
        )
        month_summary_top12anchor_3_12_trio[year_month]["total_refund"] += (
            top12anchor_3_12_trio_refund
        )
        month_summary_top12anchor_3_12_trio[year_month]["hits"] += (
            top12anchor_3_12_trio_hit_flag
        )
        month_summary_anchor3_24[year_month]["races"] += 1
        month_summary_anchor3_24[year_month]["total_bet"] += (
            anchor3_24_bet_per_race if anchor3_24_valid else 0.0
        )
        month_summary_anchor3_24[year_month]["total_refund"] += anchor3_24_refund
        month_summary_anchor3_24[year_month]["hits"] += anchor3_24_hit_flag
        month_summary_anchor2_24[year_month]["races"] += 1
        month_summary_anchor2_24[year_month]["total_bet"] += (
            anchor2_24_bet_per_race if anchor2_24_valid else 0.0
        )
        month_summary_anchor2_24[year_month]["total_refund"] += anchor2_24_refund
        month_summary_anchor2_24[year_month]["hits"] += anchor2_24_hit_flag
        month_summary_rpop5_7_anchor_1_4_trio[year_month]["races"] += 1
        month_summary_rpop5_7_anchor_1_4_trio[year_month]["total_bet"] += (
            anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0
        )
        month_summary_rpop5_7_anchor_1_4_trio[year_month]["total_refund"] += (
            anchor1_57_24_refund
        )
        month_summary_rpop5_7_anchor_1_4_trio[year_month]["hits"] += (
            anchor1_57_24_hit_flag
        )
        month_summary_rpop5_8_anchor_1_4_trio[year_month]["races"] += 1
        month_summary_rpop5_8_anchor_1_4_trio[year_month]["total_bet"] += (
            anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0
        )
        month_summary_rpop5_8_anchor_1_4_trio[year_month]["total_refund"] += (
            anchor1_58_24_refund
        )
        month_summary_rpop5_8_anchor_1_4_trio[year_month]["hits"] += (
            anchor1_58_24_hit_flag
        )
        month_summary_anchor_24[year_month]["races"] += 1
        month_summary_anchor_24[year_month]["total_bet"] += (
            anchor1_24_bet_per_race if anchor1_24_valid else 0.0
        )
        month_summary_anchor_24[year_month]["total_refund"] += anchor1_24_refund
        month_summary_anchor_24[year_month]["hits"] += anchor1_24_hit_flag
        month_summary_anchor_25[year_month]["races"] += 1
        month_summary_anchor_25[year_month]["total_bet"] += (
            anchor1_25_bet_per_race if anchor1_25_valid else 0.0
        )
        month_summary_anchor_25[year_month]["total_refund"] += anchor1_25_refund
        month_summary_anchor_25[year_month]["hits"] += anchor1_25_hit_flag
        month_summary_anchor_25_68[year_month]["races"] += 1
        month_summary_anchor_25_68[year_month]["total_bet"] += (
            anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0
        )
        month_summary_anchor_25_68[year_month]["total_refund"] += (
            anchor1_25_68_refund
        )
        month_summary_anchor_25_68[year_month]["hits"] += anchor1_25_68_hit_flag
        month_summary_anchor_25_69[year_month]["races"] += 1
        month_summary_anchor_25_69[year_month]["total_bet"] += (
            anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0
        )
        month_summary_anchor_25_69[year_month]["total_refund"] += (
            anchor1_25_69_refund
        )
        month_summary_anchor_25_69[year_month]["hits"] += anchor1_25_69_hit_flag
        month_summary_anchor_69_25[year_month]["races"] += 1
        month_summary_anchor_69_25[year_month]["total_bet"] += (
            anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0
        )
        month_summary_anchor_69_25[year_month]["total_refund"] += (
            anchor1_69_25_refund
        )
        month_summary_anchor_69_25[year_month]["hits"] += anchor1_69_25_hit_flag
        month_summary_anchor_23_46[year_month]["races"] += 1
        month_summary_anchor_23_46[year_month]["total_bet"] += (
            anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0
        )
        month_summary_anchor_23_46[year_month]["total_refund"] += (
            anchor1_23_46_refund
        )
        month_summary_anchor_23_46[year_month]["hits"] += anchor1_23_46_hit_flag
        month_summary_anchor_23_47[year_month]["races"] += 1
        month_summary_anchor_23_47[year_month]["total_bet"] += (
            anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0
        )
        month_summary_anchor_23_47[year_month]["total_refund"] += (
            anchor1_23_47_refund
        )
        month_summary_anchor_23_47[year_month]["hits"] += anchor1_23_47_hit_flag
        month_summary_anchor_23_48[year_month]["races"] += 1
        month_summary_anchor_23_48[year_month]["total_bet"] += (
            anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0
        )
        month_summary_anchor_23_48[year_month]["total_refund"] += (
            anchor1_23_48_refund
        )
        month_summary_anchor_23_48[year_month]["hits"] += anchor1_23_48_hit_flag
        month_summary_anchor_23_49[year_month]["races"] += 1
        month_summary_anchor_23_49[year_month]["total_bet"] += (
            anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0
        )
        month_summary_anchor_23_49[year_month]["total_refund"] += (
            anchor1_23_49_refund
        )
        month_summary_anchor_23_49[year_month]["hits"] += anchor1_23_49_hit_flag
        month_summary_anchor12_3_7[year_month]["races"] += 1
        month_summary_anchor12_3_7[year_month]["total_bet"] += (
            anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0
        )
        month_summary_anchor12_3_7[year_month]["total_refund"] += (
            anchor12_3_7_refund
        )
        month_summary_anchor12_3_7[year_month]["hits"] += anchor12_3_7_hit_flag
        month_summary_anchor12_3_10[year_month]["races"] += 1
        month_summary_anchor12_3_10[year_month]["total_bet"] += (
            anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0
        )
        month_summary_anchor12_3_10[year_month]["total_refund"] += (
            anchor12_3_10_refund
        )
        month_summary_anchor12_3_10[year_month]["hits"] += anchor12_3_10_hit_flag
        holes_per_race = (
            (9 if anchor1_24_57_valid else 0)
            + (3 if anchor1_24_quinella_valid else 0)
            + (5 if anchor1_26_quinella_valid else 0)
            + (9 if top3pair_46_quinella_valid else 0)
            + (len(top3_4) * 2 if anchor12_3_4_quinella_valid else 0)
            + (len(top3_5) * 2 if anchor12_3_5_quinella_valid else 0)
            + (len(top4_6) * 2 if anchor12_3_6_quinella_valid else 0)
            + (len(top3_7) * 2 if anchor12_3_7_quinella_valid else 0)
            + (len(top3_8) * 2 if anchor12_3_8_quinella_valid else 0)
            + (len(top3_12) * 2 if anchor12_3_12_quinella_valid else 0)
            + (12 if anchor1_24_58_valid else 0)
            + (24 if top4_box_trifecta_valid else 0)
            + (60 if top5_box_trifecta_valid else 0)
            + (20 if top6_trio_valid else 0)
            + (9 if top3pair_46_trio_valid else 0)
            + (12 if top3pair_47_trio_valid else 0)
            + (18 if top3pair_49_trio_valid else 0)
            + (24 if top4pair_58_trio_valid else 0)
            + (8 if top12anchor_3_10_trio_valid else 0)
            + (len(top3_8_12) if top12anchor_3_8_12_trio_valid else 0)
            + (len(top3_12) if top12anchor_3_12_trio_valid else 0)
            + (9 if anchor1_57_24_valid else 0)
            + (12 if anchor1_58_24_valid else 0)
            + (6 if anchor3_24_valid else 0)
            + (6 if anchor2_24_valid else 0)
            + (6 if anchor1_24_valid else 0)
            + (12 if anchor1_25_valid else 0)
            + (12 if anchor1_25_68_valid else 0)
            + (16 if anchor1_25_69_valid else 0)
            + (16 if anchor1_69_25_valid else 0)
            + (6 if anchor1_23_46_valid else 0)
            + (8 if anchor1_23_47_valid else 0)
            + (10 if anchor1_23_48_valid else 0)
            + (12 if anchor1_23_49_valid else 0)
            + (5 if anchor12_3_7_valid else 0)
            + (8 if anchor12_3_10_valid else 0)
        )
        total_holes_all += holes_per_race
        race_rows.append(
            {
                "연월": year_month,
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "경주거리": distance,
                "등급": grade,
                "축마": anchor_gate if anchor_gate is not None else "",
                "2축마": second_gate if second_gate is not None else "",
                "2~6_마번": ",".join(map(str, top2_6)),
                "2~3_마번": ",".join(map(str, top2_3)),
                "3~4_마번": ",".join(map(str, top3_4)),
                "3~5_마번": ",".join(map(str, top3_5)),
                "3~7_마번": ",".join(map(str, top3_7)),
                "3~10_마번": ",".join(map(str, top3_10)),
                "3~8,12_마번": ",".join(map(str, top3_8_12)),
                "2~4_마번": ",".join(map(str, top2_4)),
                "2~5_마번": ",".join(map(str, top2_5)),
                "4~6_마번": ",".join(map(str, top4_6)),
                "4~7_마번": ",".join(map(str, top4_7)),
                "4~8_마번": ",".join(map(str, top4_8)),
                "4~9_마번": ",".join(map(str, top4_9)),
                "3~12_마번": ",".join(map(str, top3_12)),
                "5~7_마번": ",".join(map(str, top5_7)),
                "5~8_마번": ",".join(map(str, top5_8)),
                "6~8_마번": ",".join(map(str, top6_8)),
                "6~9_마번": ",".join(map(str, top6_9)),
                "r_pop_top4_마번": ",".join(map(str, top4)),
                "r_pop_top5_마번": ",".join(map(str, top5)),
                "r_pop_top6_마번": ",".join(map(str, top6)),
                "r_pop_top3_마번": ",".join(map(str, top3)),
                "실제_top2_마번": ",".join(map(str, actual_top2)),
                "실제_top3_마번": ",".join(map(str, actual_top3)),
                "r_pop1_축_2~4_5~7_적중": anchor1_24_57_hit_flag,
                "r_pop1_축_2~4_5~7_환수액": anchor1_24_57_refund,
                "r_pop1_축_2~4_복승_적중": anchor1_24_quinella_hit_flag,
                "r_pop1_축_2~4_복승_환수액": anchor1_24_quinella_refund,
                "r_pop1_축_2~6_복승_적중": anchor1_26_quinella_hit_flag,
                "r_pop1_축_2~6_복승_환수액": anchor1_26_quinella_refund,
                "r_pop1~3_복조축_4~6_복승_적중": top3pair_46_quinella_hit_flag,
                "r_pop1~3_복조축_4~6_복승_환수액": top3pair_46_quinella_refund,
                "r_pop1,2_축_3~4_복승_적중": anchor12_3_4_quinella_hit_flag,
                "r_pop1,2_축_3~4_복승_환수액": anchor12_3_4_quinella_refund,
                "r_pop1,2_축_3~5_복승_적중": anchor12_3_5_quinella_hit_flag,
                "r_pop1,2_축_3~5_복승_환수액": anchor12_3_5_quinella_refund,
                "r_pop1,2_축_3~6_복승_적중": anchor12_3_6_quinella_hit_flag,
                "r_pop1,2_축_3~6_복승_환수액": anchor12_3_6_quinella_refund,
                "r_pop1,2_축_3~7_복승_적중": anchor12_3_7_quinella_hit_flag,
                "r_pop1,2_축_3~7_복승_환수액": anchor12_3_7_quinella_refund,
                "r_pop1,2_축_3~8_복승_적중": anchor12_3_8_quinella_hit_flag,
                "r_pop1,2_축_3~8_복승_환수액": anchor12_3_8_quinella_refund,
                "r_pop1,2_축_3~12_복승_적중": anchor12_3_12_quinella_hit_flag,
                "r_pop1,2_축_3~12_복승_환수액": anchor12_3_12_quinella_refund,
                "r_pop1_축_2~4_5~8_적중": anchor1_24_58_hit_flag,
                "r_pop1_축_2~4_5~8_환수액": anchor1_24_58_refund,
                "r_pop1~4_4복_적중": top4_box_trifecta_hit_flag,
                "r_pop1~4_4복_환수액": top4_box_trifecta_refund,
                "r_pop1~5_5복_적중": top5_box_trifecta_hit_flag,
                "r_pop1~5_5복_환수액": top5_box_trifecta_refund,
                "r_pop1~6_6복조_삼복_적중": top6_trio_hit_flag,
                "r_pop1~6_6복조_삼복_환수액": top6_trio_refund,
                "r_pop1~3_복조_4~6_삼복_적중": top3pair_46_trio_hit_flag,
                "r_pop1~3_복조_4~6_삼복_환수액": top3pair_46_trio_refund,
                "r_pop1~3_복조_4~7_삼복_적중": top3pair_47_trio_hit_flag,
                "r_pop1~3_복조_4~7_삼복_환수액": top3pair_47_trio_refund,
                "r_pop1~3_복조_4~9_삼복_적중": top3pair_49_trio_hit_flag,
                "r_pop1~3_복조_4~9_삼복_환수액": top3pair_49_trio_refund,
                "r_pop1~4_복조_5~8_삼복_적중": top4pair_58_trio_hit_flag,
                "r_pop1~4_복조_5~8_삼복_환수액": top4pair_58_trio_refund,
                "r_pop1~2_복조축_3~10_삼복_적중": top12anchor_3_10_trio_hit_flag,
                "r_pop1~2_복조축_3~10_삼복_환수액": top12anchor_3_10_trio_refund,
                "r_pop1~2_복조축_3~8,12_삼복_적중": top12anchor_3_8_12_trio_hit_flag,
                "r_pop1~2_복조축_3~8,12_삼복_환수액": top12anchor_3_8_12_trio_refund,
                "r_pop1~2_복조축_3~12_삼복_적중": top12anchor_3_12_trio_hit_flag,
                "r_pop1~2_복조축_3~12_삼복_환수액": top12anchor_3_12_trio_refund,
                "r_pop1_축_5~7_2~4_적중": anchor1_57_24_hit_flag,
                "r_pop1_축_5~7_2~4_환수액": anchor1_57_24_refund,
                "r_pop1_축_5~8_2~4_적중": anchor1_58_24_hit_flag,
                "r_pop1_축_5~8_2~4_환수액": anchor1_58_24_refund,
                "r_pop1_3축_2~4_적중": anchor3_24_hit_flag,
                "r_pop1_3축_2~4_환수액": anchor3_24_refund,
                "r_pop1_2축_2~4_적중": anchor2_24_hit_flag,
                "r_pop1_2축_2~4_환수액": anchor2_24_refund,
                "r_pop1_축_2~4_적중": anchor1_24_hit_flag,
                "r_pop1_축_2~4_환수액": anchor1_24_refund,
                "r_pop1_축_2~5_적중": anchor1_25_hit_flag,
                "r_pop1_축_2~5_환수액": anchor1_25_refund,
                "r_pop1_축_2~5_6~8_적중": anchor1_25_68_hit_flag,
                "r_pop1_축_2~5_6~8_환수액": anchor1_25_68_refund,
                "r_pop1_축_2~5_6~9_적중": anchor1_25_69_hit_flag,
                "r_pop1_축_2~5_6~9_환수액": anchor1_25_69_refund,
                "r_pop1_축_6~9_2~5_적중": anchor1_69_25_hit_flag,
                "r_pop1_축_6~9_2~5_환수액": anchor1_69_25_refund,
                "r_pop1_축_2~3_4~6_적중": anchor1_23_46_hit_flag,
                "r_pop1_축_2~3_4~6_환수액": anchor1_23_46_refund,
                "r_pop1_축_2~3_4~7_적중": anchor1_23_47_hit_flag,
                "r_pop1_축_2~3_4~7_환수액": anchor1_23_47_refund,
                "r_pop1_축_2~3_4~8_적중": anchor1_23_48_hit_flag,
                "r_pop1_축_2~3_4~8_환수액": anchor1_23_48_refund,
                "r_pop1_축_2~3_4~9_적중": anchor1_23_49_hit_flag,
                "r_pop1_축_2~3_4~9_환수액": anchor1_23_49_refund,
                "r_pop1_1축_r_pop2_2축_3~7_적중": anchor12_3_7_hit_flag,
                "r_pop1_1축_r_pop2_2축_3~7_환수액": anchor12_3_7_refund,
                "r_pop1_1축_r_pop2_2축_3~10_적중": anchor12_3_10_hit_flag,
                "r_pop1_1축_r_pop2_2축_3~10_환수액": anchor12_3_10_refund,
                "1축_2~4_5~7_베팅액": (
                    anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
                ),
                "1축_2~4_5~7_환수액": anchor1_24_57_refund,
                "1축_2~4_복승_베팅액": (
                    anchor1_24_quinella_bet_per_race if anchor1_24_quinella_valid else 0.0
                ),
                "1축_2~4_복승_환수액": anchor1_24_quinella_refund,
                "1축_2~6_복승_베팅액": (
                    anchor1_26_quinella_bet_per_race if anchor1_26_quinella_valid else 0.0
                ),
                "1축_2~6_복승_환수액": anchor1_26_quinella_refund,
                "1~3_복조축_4~6_복승_베팅액": (
                    top3pair_46_quinella_bet_per_race
                    if top3pair_46_quinella_valid
                    else 0.0
                ),
                "1~3_복조축_4~6_복승_환수액": top3pair_46_quinella_refund,
                "1,2축_3~4_복승_베팅액": (
                    anchor12_3_4_quinella_bet_per_race_current
                    if anchor12_3_4_quinella_valid
                    else 0.0
                ),
                "1,2축_3~4_복승_환수액": anchor12_3_4_quinella_refund,
                "1,2축_3~5_복승_베팅액": (
                    anchor12_3_5_quinella_bet_per_race_current
                    if anchor12_3_5_quinella_valid
                    else 0.0
                ),
                "1,2축_3~5_복승_환수액": anchor12_3_5_quinella_refund,
                "1,2축_3~6_복승_베팅액": (
                    anchor12_3_6_quinella_bet_per_race_current
                    if anchor12_3_6_quinella_valid
                    else 0.0
                ),
                "1,2축_3~6_복승_환수액": anchor12_3_6_quinella_refund,
                "1,2축_3~7_복승_베팅액": (
                    anchor12_3_7_quinella_bet_per_race_current
                    if anchor12_3_7_quinella_valid
                    else 0.0
                ),
                "1,2축_3~7_복승_환수액": anchor12_3_7_quinella_refund,
                "1,2축_3~8_복승_베팅액": (
                    anchor12_3_8_quinella_bet_per_race_current
                    if anchor12_3_8_quinella_valid
                    else 0.0
                ),
                "1,2축_3~8_복승_환수액": anchor12_3_8_quinella_refund,
                "1,2축_3~12_복승_베팅액": (
                    anchor12_3_12_quinella_bet_per_race_current
                    if anchor12_3_12_quinella_valid
                    else 0.0
                ),
                "1,2축_3~12_복승_환수액": anchor12_3_12_quinella_refund,
                "1축_2~4_5~8_베팅액": (
                    anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0
                ),
                "1축_2~4_5~8_환수액": anchor1_24_58_refund,
                "1~4_4복_베팅액": (
                    top4_box_trifecta_bet_per_race if top4_box_trifecta_valid else 0.0
                ),
                "1~4_4복_환수액": top4_box_trifecta_refund,
                "1~5_5복_베팅액": (
                    top5_box_trifecta_bet_per_race if top5_box_trifecta_valid else 0.0
                ),
                "1~5_5복_환수액": top5_box_trifecta_refund,
                "1~6_6복조_삼복_베팅액": (
                    top6_trio_bet_per_race if top6_trio_valid else 0.0
                ),
                "1~6_6복조_삼복_환수액": top6_trio_refund,
                "1~3_복조_4~6_삼복_베팅액": (
                    top3pair_46_trio_bet_per_race if top3pair_46_trio_valid else 0.0
                ),
                "1~3_복조_4~6_삼복_환수액": top3pair_46_trio_refund,
                "1~3_복조_4~7_삼복_베팅액": (
                    top3pair_47_trio_bet_per_race if top3pair_47_trio_valid else 0.0
                ),
                "1~3_복조_4~7_삼복_환수액": top3pair_47_trio_refund,
                "1~3_복조_4~9_삼복_베팅액": (
                    top3pair_49_trio_bet_per_race if top3pair_49_trio_valid else 0.0
                ),
                "1~3_복조_4~9_삼복_환수액": top3pair_49_trio_refund,
                "1~4_복조_5~8_삼복_베팅액": (
                    top4pair_58_trio_bet_per_race if top4pair_58_trio_valid else 0.0
                ),
                "1~4_복조_5~8_삼복_환수액": top4pair_58_trio_refund,
                "1~2_복조축_3~10_삼복_베팅액": (
                    top12anchor_3_10_trio_bet_per_race
                    if top12anchor_3_10_trio_valid
                    else 0.0
                ),
                "1~2_복조축_3~10_삼복_환수액": top12anchor_3_10_trio_refund,
                "1~2_복조축_3~8,12_삼복_베팅액": (
                    top12anchor_3_8_12_bet_per_race_current
                    if top12anchor_3_8_12_trio_valid
                    else 0.0
                ),
                "1~2_복조축_3~8,12_삼복_환수액": top12anchor_3_8_12_trio_refund,
                "1~2_복조축_3~12_삼복_베팅액": (
                    top12anchor_3_12_bet_per_race_current
                    if top12anchor_3_12_trio_valid
                    else 0.0
                ),
                "1~2_복조축_3~12_삼복_환수액": top12anchor_3_12_trio_refund,
                "1축_5~7_2~4_베팅액": (
                    anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0
                ),
                "1축_5~7_2~4_환수액": anchor1_57_24_refund,
                "1축_5~8_2~4_베팅액": (
                    anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0
                ),
                "1축_5~8_2~4_환수액": anchor1_58_24_refund,
                "3축_2~4_베팅액": (
                    anchor3_24_bet_per_race if anchor3_24_valid else 0.0
                ),
                "3축_2~4_환수액": anchor3_24_refund,
                "2축_2~4_베팅액": (
                    anchor2_24_bet_per_race if anchor2_24_valid else 0.0
                ),
                "2축_2~4_환수액": anchor2_24_refund,
                "1축_2~4_베팅액": (
                    anchor1_24_bet_per_race if anchor1_24_valid else 0.0
                ),
                "1축_2~4_환수액": anchor1_24_refund,
                "1축_2~5_베팅액": (
                    anchor1_25_bet_per_race if anchor1_25_valid else 0.0
                ),
                "1축_2~5_환수액": anchor1_25_refund,
                "1축_2~5_6~8_베팅액": (
                    anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0
                ),
                "1축_2~5_6~8_환수액": anchor1_25_68_refund,
                "1축_2~5_6~9_베팅액": (
                    anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0
                ),
                "1축_2~5_6~9_환수액": anchor1_25_69_refund,
                "1축_6~9_2~5_베팅액": (
                    anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0
                ),
                "1축_6~9_2~5_환수액": anchor1_69_25_refund,
                "1축_2~3_4~6_베팅액": (
                    anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0
                ),
                "1축_2~3_4~6_환수액": anchor1_23_46_refund,
                "1축_2~3_4~7_베팅액": (
                    anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0
                ),
                "1축_2~3_4~7_환수액": anchor1_23_47_refund,
                "1축_2~3_4~8_베팅액": (
                    anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0
                ),
                "1축_2~3_4~8_환수액": anchor1_23_48_refund,
                "1축_2~3_4~9_베팅액": (
                    anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0
                ),
                "1축_2~3_4~9_환수액": anchor1_23_49_refund,
                "1축_2축_3~7_베팅액": (
                    anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0
                ),
                "1축_2축_3~7_환수액": anchor12_3_7_refund,
                "1축_2축_3~10_베팅액": (
                    anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0
                ),
                "1축_2축_3~10_환수액": anchor12_3_10_refund,
                "총구멍수": holes_per_race,
                "총베팅액": (
                    (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
                    + (
                        anchor1_24_quinella_bet_per_race
                        if anchor1_24_quinella_valid
                        else 0.0
                    )
                    + (
                        anchor1_26_quinella_bet_per_race
                        if anchor1_26_quinella_valid
                        else 0.0
                    )
                    + (
                        top3pair_46_quinella_bet_per_race
                        if top3pair_46_quinella_valid
                        else 0.0
                    )
                    + (
                        anchor12_3_4_quinella_bet_per_race_current
                        if anchor12_3_4_quinella_valid
                        else 0.0
                    )
                    + (
                        anchor12_3_5_quinella_bet_per_race_current
                        if anchor12_3_5_quinella_valid
                        else 0.0
                    )
                    + (
                        anchor12_3_6_quinella_bet_per_race_current
                        if anchor12_3_6_quinella_valid
                        else 0.0
                    )
                    + (
                        anchor12_3_7_quinella_bet_per_race_current
                        if anchor12_3_7_quinella_valid
                        else 0.0
                    )
                    + (
                        anchor12_3_8_quinella_bet_per_race_current
                        if anchor12_3_8_quinella_valid
                        else 0.0
                    )
                    + (
                        anchor12_3_12_quinella_bet_per_race_current
                        if anchor12_3_12_quinella_valid
                        else 0.0
                    )
                    + (anchor1_24_58_bet_per_race if anchor1_24_58_valid else 0.0)
                    + (
                        top4_box_trifecta_bet_per_race
                        if top4_box_trifecta_valid
                        else 0.0
                    )
                    + (
                        top5_box_trifecta_bet_per_race
                        if top5_box_trifecta_valid
                        else 0.0
                    )
                    + (top6_trio_bet_per_race if top6_trio_valid else 0.0)
                    + (
                        top3pair_49_trio_bet_per_race
                        if top3pair_49_trio_valid
                        else 0.0
                    )
                    + (
                        top3pair_46_trio_bet_per_race
                        if top3pair_46_trio_valid
                        else 0.0
                    )
                    + (
                        top3pair_47_trio_bet_per_race
                        if top3pair_47_trio_valid
                        else 0.0
                    )
                    + (
                        top4pair_58_trio_bet_per_race
                        if top4pair_58_trio_valid
                        else 0.0
                    )
                    + (
                        top12anchor_3_10_trio_bet_per_race
                        if top12anchor_3_10_trio_valid
                        else 0.0
                    )
                    + (
                        top12anchor_3_8_12_bet_per_race_current
                        if top12anchor_3_8_12_trio_valid
                        else 0.0
                    )
                    + (
                        top12anchor_3_12_bet_per_race_current
                        if top12anchor_3_12_trio_valid
                        else 0.0
                    )
                    + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
                    + (anchor1_58_24_bet_per_race if anchor1_58_24_valid else 0.0)
                    + (anchor3_24_bet_per_race if anchor3_24_valid else 0.0)
                    + (anchor2_24_bet_per_race if anchor2_24_valid else 0.0)
                    + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
                    + (anchor1_25_bet_per_race if anchor1_25_valid else 0.0)
                    + (anchor1_25_68_bet_per_race if anchor1_25_68_valid else 0.0)
                    + (anchor1_25_69_bet_per_race if anchor1_25_69_valid else 0.0)
                    + (anchor1_69_25_bet_per_race if anchor1_69_25_valid else 0.0)
                    + (anchor1_23_46_bet_per_race if anchor1_23_46_valid else 0.0)
                    + (anchor1_23_47_bet_per_race if anchor1_23_47_valid else 0.0)
                    + (anchor1_23_48_bet_per_race if anchor1_23_48_valid else 0.0)
                    + (anchor1_23_49_bet_per_race if anchor1_23_49_valid else 0.0)
                    + (anchor12_3_7_bet_per_race if anchor12_3_7_valid else 0.0)
                    + (anchor12_3_10_bet_per_race if anchor12_3_10_valid else 0.0)
                ),
                "총환수액": anchor1_24_57_refund
                + anchor1_24_quinella_refund
                + anchor1_26_quinella_refund
                + top3pair_46_quinella_refund
                + anchor12_3_4_quinella_refund
                + anchor12_3_5_quinella_refund
                + anchor12_3_6_quinella_refund
                + anchor12_3_7_quinella_refund
                + anchor12_3_8_quinella_refund
                + anchor12_3_12_quinella_refund
                + anchor1_24_58_refund
                + top4_box_trifecta_refund
                + top5_box_trifecta_refund
                + top6_trio_refund
                + top3pair_46_trio_refund
                + top3pair_47_trio_refund
                + top3pair_49_trio_refund
                + top4pair_58_trio_refund
                + top12anchor_3_10_trio_refund
                + top12anchor_3_8_12_trio_refund
                + top12anchor_3_12_trio_refund
                + anchor1_57_24_refund
                + anchor1_58_24_refund
                + anchor3_24_refund
                + anchor2_24_refund
                + anchor1_24_refund
                + anchor1_25_refund
                + anchor1_25_68_refund
                + anchor1_25_69_refund
                + anchor1_69_25_refund
                + anchor1_23_46_refund
                + anchor1_23_47_refund
                + anchor1_23_48_refund
                + anchor1_23_49_refund
                + anchor12_3_7_refund
                + anchor12_3_10_refund,
                "복승식배당율": quinella_odds,
                "삼복승식배당율": trio_odds,
                "삼쌍승식배당율": odds,
            }
        )

    race_df = pd.DataFrame(race_rows)
    summary = {
        "races": total_races,
        "excluded_races": excluded_races,
        "anchor1_24_57_total_bet": anchor1_24_57_total_bet,
        "anchor1_24_57_total_refund": anchor1_24_57_total_refund,
        "anchor1_24_57_refund_rate": (
            anchor1_24_57_total_refund / anchor1_24_57_total_bet
            if anchor1_24_57_total_bet > 0
            else 0.0
        ),
        "anchor1_24_57_hit_rate": (
            anchor1_24_57_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_24_quinella_total_bet": anchor1_24_quinella_total_bet,
        "anchor1_24_quinella_total_refund": anchor1_24_quinella_total_refund,
        "anchor1_24_quinella_refund_rate": (
            anchor1_24_quinella_total_refund / anchor1_24_quinella_total_bet
            if anchor1_24_quinella_total_bet > 0
            else 0.0
        ),
        "anchor1_24_quinella_hit_rate": (
            anchor1_24_quinella_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_26_quinella_total_bet": anchor1_26_quinella_total_bet,
        "anchor1_26_quinella_total_refund": anchor1_26_quinella_total_refund,
        "anchor1_26_quinella_refund_rate": (
            anchor1_26_quinella_total_refund / anchor1_26_quinella_total_bet
            if anchor1_26_quinella_total_bet > 0
            else 0.0
        ),
        "anchor1_26_quinella_hit_rate": (
            anchor1_26_quinella_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top3pair_46_quinella_total_bet": top3pair_46_quinella_total_bet,
        "top3pair_46_quinella_total_refund": top3pair_46_quinella_total_refund,
        "top3pair_46_quinella_refund_rate": (
            top3pair_46_quinella_total_refund / top3pair_46_quinella_total_bet
            if top3pair_46_quinella_total_bet > 0
            else 0.0
        ),
        "top3pair_46_quinella_hit_rate": (
            top3pair_46_quinella_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
        "anchor12_3_4_quinella_total_bet": anchor12_3_4_quinella_total_bet,
        "anchor12_3_4_quinella_total_refund": anchor12_3_4_quinella_total_refund,
        "anchor12_3_4_quinella_refund_rate": (
            anchor12_3_4_quinella_total_refund / anchor12_3_4_quinella_total_bet
            if anchor12_3_4_quinella_total_bet > 0
            else 0.0
        ),
        "anchor12_3_4_quinella_hit_rate": (
            anchor12_3_4_quinella_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
        "anchor12_3_5_quinella_total_bet": anchor12_3_5_quinella_total_bet,
        "anchor12_3_5_quinella_total_refund": anchor12_3_5_quinella_total_refund,
        "anchor12_3_5_quinella_refund_rate": (
            anchor12_3_5_quinella_total_refund / anchor12_3_5_quinella_total_bet
            if anchor12_3_5_quinella_total_bet > 0
            else 0.0
        ),
        "anchor12_3_5_quinella_hit_rate": (
            anchor12_3_5_quinella_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
        "anchor12_3_6_quinella_total_bet": anchor12_3_6_quinella_total_bet,
        "anchor12_3_6_quinella_total_refund": anchor12_3_6_quinella_total_refund,
        "anchor12_3_6_quinella_refund_rate": (
            anchor12_3_6_quinella_total_refund / anchor12_3_6_quinella_total_bet
            if anchor12_3_6_quinella_total_bet > 0
            else 0.0
        ),
        "anchor12_3_6_quinella_hit_rate": (
            anchor12_3_6_quinella_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
        "anchor12_3_7_quinella_total_bet": anchor12_3_7_quinella_total_bet,
        "anchor12_3_7_quinella_total_refund": anchor12_3_7_quinella_total_refund,
        "anchor12_3_7_quinella_refund_rate": (
            anchor12_3_7_quinella_total_refund / anchor12_3_7_quinella_total_bet
            if anchor12_3_7_quinella_total_bet > 0
            else 0.0
        ),
        "anchor12_3_7_quinella_hit_rate": (
            anchor12_3_7_quinella_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
        "anchor12_3_8_quinella_total_bet": anchor12_3_8_quinella_total_bet,
        "anchor12_3_8_quinella_total_refund": anchor12_3_8_quinella_total_refund,
        "anchor12_3_8_quinella_refund_rate": (
            anchor12_3_8_quinella_total_refund / anchor12_3_8_quinella_total_bet
            if anchor12_3_8_quinella_total_bet > 0
            else 0.0
        ),
        "anchor12_3_8_quinella_hit_rate": (
            anchor12_3_8_quinella_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
        "anchor12_3_12_quinella_total_bet": anchor12_3_12_quinella_total_bet,
        "anchor12_3_12_quinella_total_refund": anchor12_3_12_quinella_total_refund,
        "anchor12_3_12_quinella_refund_rate": (
            anchor12_3_12_quinella_total_refund / anchor12_3_12_quinella_total_bet
            if anchor12_3_12_quinella_total_bet > 0
            else 0.0
        ),
        "anchor12_3_12_quinella_hit_rate": (
            anchor12_3_12_quinella_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
        "anchor1_24_58_total_bet": anchor1_24_58_total_bet,
        "anchor1_24_58_total_refund": anchor1_24_58_total_refund,
        "anchor1_24_58_refund_rate": (
            anchor1_24_58_total_refund / anchor1_24_58_total_bet
            if anchor1_24_58_total_bet > 0
            else 0.0
        ),
        "anchor1_24_58_hit_rate": (
            anchor1_24_58_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top4_box_trifecta_total_bet": top4_box_trifecta_total_bet,
        "top4_box_trifecta_total_refund": top4_box_trifecta_total_refund,
        "top4_box_trifecta_refund_rate": (
            top4_box_trifecta_total_refund / top4_box_trifecta_total_bet
            if top4_box_trifecta_total_bet > 0
            else 0.0
        ),
        "top4_box_trifecta_hit_rate": (
            top4_box_trifecta_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top5_box_trifecta_total_bet": top5_box_trifecta_total_bet,
        "top5_box_trifecta_total_refund": top5_box_trifecta_total_refund,
        "top5_box_trifecta_refund_rate": (
            top5_box_trifecta_total_refund / top5_box_trifecta_total_bet
            if top5_box_trifecta_total_bet > 0
            else 0.0
        ),
        "top5_box_trifecta_hit_rate": (
            top5_box_trifecta_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top6_trio_total_bet": top6_trio_total_bet,
        "top6_trio_total_refund": top6_trio_total_refund,
        "top6_trio_refund_rate": (
            top6_trio_total_refund / top6_trio_total_bet
            if top6_trio_total_bet > 0
            else 0.0
        ),
        "top6_trio_hit_rate": (
            top6_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top3pair_46_trio_total_bet": top3pair_46_trio_total_bet,
        "top3pair_46_trio_total_refund": top3pair_46_trio_total_refund,
        "top3pair_46_trio_refund_rate": (
            top3pair_46_trio_total_refund / top3pair_46_trio_total_bet
            if top3pair_46_trio_total_bet > 0
            else 0.0
        ),
        "top3pair_46_trio_hit_rate": (
            top3pair_46_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top3pair_47_trio_total_bet": top3pair_47_trio_total_bet,
        "top3pair_47_trio_total_refund": top3pair_47_trio_total_refund,
        "top3pair_47_trio_refund_rate": (
            top3pair_47_trio_total_refund / top3pair_47_trio_total_bet
            if top3pair_47_trio_total_bet > 0
            else 0.0
        ),
        "top3pair_47_trio_hit_rate": (
            top3pair_47_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top3pair_49_trio_total_bet": top3pair_49_trio_total_bet,
        "top3pair_49_trio_total_refund": top3pair_49_trio_total_refund,
        "top3pair_49_trio_refund_rate": (
            top3pair_49_trio_total_refund / top3pair_49_trio_total_bet
            if top3pair_49_trio_total_bet > 0
            else 0.0
        ),
        "top3pair_49_trio_hit_rate": (
            top3pair_49_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top4pair_58_trio_total_bet": top4pair_58_trio_total_bet,
        "top4pair_58_trio_total_refund": top4pair_58_trio_total_refund,
        "top4pair_58_trio_refund_rate": (
            top4pair_58_trio_total_refund / top4pair_58_trio_total_bet
            if top4pair_58_trio_total_bet > 0
            else 0.0
        ),
        "top4pair_58_trio_hit_rate": (
            top4pair_58_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top12anchor_3_10_trio_total_bet": top12anchor_3_10_trio_total_bet,
        "top12anchor_3_10_trio_total_refund": top12anchor_3_10_trio_total_refund,
        "top12anchor_3_10_trio_refund_rate": (
            top12anchor_3_10_trio_total_refund / top12anchor_3_10_trio_total_bet
            if top12anchor_3_10_trio_total_bet > 0
            else 0.0
        ),
        "top12anchor_3_10_trio_hit_rate": (
            top12anchor_3_10_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top12anchor_3_8_12_trio_total_bet": top12anchor_3_8_12_trio_total_bet,
        "top12anchor_3_8_12_trio_total_refund": top12anchor_3_8_12_trio_total_refund,
        "top12anchor_3_8_12_trio_refund_rate": (
            top12anchor_3_8_12_trio_total_refund
            / top12anchor_3_8_12_trio_total_bet
            if top12anchor_3_8_12_trio_total_bet > 0
            else 0.0
        ),
        "top12anchor_3_8_12_trio_hit_rate": (
            top12anchor_3_8_12_trio_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
        "top12anchor_3_12_trio_total_bet": top12anchor_3_12_trio_total_bet,
        "top12anchor_3_12_trio_total_refund": top12anchor_3_12_trio_total_refund,
        "top12anchor_3_12_trio_refund_rate": (
            top12anchor_3_12_trio_total_refund / top12anchor_3_12_trio_total_bet
            if top12anchor_3_12_trio_total_bet > 0
            else 0.0
        ),
        "top12anchor_3_12_trio_hit_rate": (
            top12anchor_3_12_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_57_24_total_bet": anchor1_57_24_total_bet,
        "anchor1_57_24_total_refund": anchor1_57_24_total_refund,
        "anchor1_57_24_refund_rate": (
            anchor1_57_24_total_refund / anchor1_57_24_total_bet
            if anchor1_57_24_total_bet > 0
            else 0.0
        ),
        "anchor1_57_24_hit_rate": (
            anchor1_57_24_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_58_24_total_bet": anchor1_58_24_total_bet,
        "anchor1_58_24_total_refund": anchor1_58_24_total_refund,
        "anchor1_58_24_refund_rate": (
            anchor1_58_24_total_refund / anchor1_58_24_total_bet
            if anchor1_58_24_total_bet > 0
            else 0.0
        ),
        "anchor1_58_24_hit_rate": (
            anchor1_58_24_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor3_24_total_bet": anchor3_24_total_bet,
        "anchor3_24_total_refund": anchor3_24_total_refund,
        "anchor3_24_refund_rate": (
            anchor3_24_total_refund / anchor3_24_total_bet
            if anchor3_24_total_bet > 0
            else 0.0
        ),
        "anchor3_24_hit_rate": (
            anchor3_24_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor2_24_total_bet": anchor2_24_total_bet,
        "anchor2_24_total_refund": anchor2_24_total_refund,
        "anchor2_24_refund_rate": (
            anchor2_24_total_refund / anchor2_24_total_bet
            if anchor2_24_total_bet > 0
            else 0.0
        ),
        "anchor2_24_hit_rate": (
            anchor2_24_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_24_total_bet": anchor1_24_total_bet,
        "anchor1_24_total_refund": anchor1_24_total_refund,
        "anchor1_24_refund_rate": (
            anchor1_24_total_refund / anchor1_24_total_bet
            if anchor1_24_total_bet > 0
            else 0.0
        ),
        "anchor1_24_hit_rate": (
            anchor1_24_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_25_total_bet": anchor1_25_total_bet,
        "anchor1_25_total_refund": anchor1_25_total_refund,
        "anchor1_25_refund_rate": (
            anchor1_25_total_refund / anchor1_25_total_bet
            if anchor1_25_total_bet > 0
            else 0.0
        ),
        "anchor1_25_hit_rate": (
            anchor1_25_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_25_68_total_bet": anchor1_25_68_total_bet,
        "anchor1_25_68_total_refund": anchor1_25_68_total_refund,
        "anchor1_25_68_refund_rate": (
            anchor1_25_68_total_refund / anchor1_25_68_total_bet
            if anchor1_25_68_total_bet > 0
            else 0.0
        ),
        "anchor1_25_68_hit_rate": (
            anchor1_25_68_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_25_69_total_bet": anchor1_25_69_total_bet,
        "anchor1_25_69_total_refund": anchor1_25_69_total_refund,
        "anchor1_25_69_refund_rate": (
            anchor1_25_69_total_refund / anchor1_25_69_total_bet
            if anchor1_25_69_total_bet > 0
            else 0.0
        ),
        "anchor1_25_69_hit_rate": (
            anchor1_25_69_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_69_25_total_bet": anchor1_69_25_total_bet,
        "anchor1_69_25_total_refund": anchor1_69_25_total_refund,
        "anchor1_69_25_refund_rate": (
            anchor1_69_25_total_refund / anchor1_69_25_total_bet
            if anchor1_69_25_total_bet > 0
            else 0.0
        ),
        "anchor1_69_25_hit_rate": (
            anchor1_69_25_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_23_46_total_bet": anchor1_23_46_total_bet,
        "anchor1_23_46_total_refund": anchor1_23_46_total_refund,
        "anchor1_23_46_refund_rate": (
            anchor1_23_46_total_refund / anchor1_23_46_total_bet
            if anchor1_23_46_total_bet > 0
            else 0.0
        ),
        "anchor1_23_46_hit_rate": (
            anchor1_23_46_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_23_47_total_bet": anchor1_23_47_total_bet,
        "anchor1_23_47_total_refund": anchor1_23_47_total_refund,
        "anchor1_23_47_refund_rate": (
            anchor1_23_47_total_refund / anchor1_23_47_total_bet
            if anchor1_23_47_total_bet > 0
            else 0.0
        ),
        "anchor1_23_47_hit_rate": (
            anchor1_23_47_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_23_48_total_bet": anchor1_23_48_total_bet,
        "anchor1_23_48_total_refund": anchor1_23_48_total_refund,
        "anchor1_23_48_refund_rate": (
            anchor1_23_48_total_refund / anchor1_23_48_total_bet
            if anchor1_23_48_total_bet > 0
            else 0.0
        ),
        "anchor1_23_48_hit_rate": (
            anchor1_23_48_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_23_49_total_bet": anchor1_23_49_total_bet,
        "anchor1_23_49_total_refund": anchor1_23_49_total_refund,
        "anchor1_23_49_refund_rate": (
            anchor1_23_49_total_refund / anchor1_23_49_total_bet
            if anchor1_23_49_total_bet > 0
            else 0.0
        ),
        "anchor1_23_49_hit_rate": (
            anchor1_23_49_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor12_3_7_total_bet": anchor12_3_7_total_bet,
        "anchor12_3_7_total_refund": anchor12_3_7_total_refund,
        "anchor12_3_7_refund_rate": (
            anchor12_3_7_total_refund / anchor12_3_7_total_bet
            if anchor12_3_7_total_bet > 0
            else 0.0
        ),
        "anchor12_3_7_hit_rate": (
            anchor12_3_7_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor12_3_10_total_bet": anchor12_3_10_total_bet,
        "anchor12_3_10_total_refund": anchor12_3_10_total_refund,
        "anchor12_3_10_refund_rate": (
            anchor12_3_10_total_refund / anchor12_3_10_total_bet
            if anchor12_3_10_total_bet > 0
            else 0.0
        ),
        "anchor12_3_10_hit_rate": (
            anchor12_3_10_total_hits / total_races if total_races > 0 else 0.0
        ),
    }
    total_bet_all = (
        anchor1_24_57_total_bet
        + anchor1_24_quinella_total_bet
        + anchor1_26_quinella_total_bet
        + top3pair_46_quinella_total_bet
        + anchor12_3_4_quinella_total_bet
        + anchor12_3_5_quinella_total_bet
        + anchor12_3_6_quinella_total_bet
        + anchor12_3_7_quinella_total_bet
        + anchor12_3_8_quinella_total_bet
        + anchor12_3_12_quinella_total_bet
        + anchor1_24_58_total_bet
        + top4_box_trifecta_total_bet
        + top5_box_trifecta_total_bet
        + top6_trio_total_bet
        + top3pair_46_trio_total_bet
        + top3pair_47_trio_total_bet
        + top3pair_49_trio_total_bet
        + top4pair_58_trio_total_bet
        + top12anchor_3_10_trio_total_bet
        + top12anchor_3_8_12_trio_total_bet
        + top12anchor_3_12_trio_total_bet
        + anchor1_57_24_total_bet
        + anchor1_58_24_total_bet
        + anchor3_24_total_bet
        + anchor2_24_total_bet
        + anchor1_24_total_bet
        + anchor1_25_total_bet
        + anchor1_25_68_total_bet
        + anchor1_25_69_total_bet
        + anchor1_69_25_total_bet
        + anchor1_23_46_total_bet
        + anchor1_23_47_total_bet
        + anchor1_23_48_total_bet
        + anchor1_23_49_total_bet
        + anchor12_3_7_total_bet
        + anchor12_3_10_total_bet
    )
    total_refund_all = (
        anchor1_24_57_total_refund
        + anchor1_24_quinella_total_refund
        + anchor1_26_quinella_total_refund
        + top3pair_46_quinella_total_refund
        + anchor12_3_4_quinella_total_refund
        + anchor12_3_5_quinella_total_refund
        + anchor12_3_6_quinella_total_refund
        + anchor12_3_7_quinella_total_refund
        + anchor12_3_8_quinella_total_refund
        + anchor12_3_12_quinella_total_refund
        + anchor1_24_58_total_refund
        + top4_box_trifecta_total_refund
        + top5_box_trifecta_total_refund
        + top6_trio_total_refund
        + top3pair_46_trio_total_refund
        + top3pair_47_trio_total_refund
        + top3pair_49_trio_total_refund
        + top4pair_58_trio_total_refund
        + top12anchor_3_10_trio_total_refund
        + top12anchor_3_8_12_trio_total_refund
        + top12anchor_3_12_trio_total_refund
        + anchor1_57_24_total_refund
        + anchor1_58_24_total_refund
        + anchor3_24_total_refund
        + anchor2_24_total_refund
        + anchor1_24_total_refund
        + anchor1_25_total_refund
        + anchor1_25_68_total_refund
        + anchor1_25_69_total_refund
        + anchor1_69_25_total_refund
        + anchor1_23_46_total_refund
        + anchor1_23_47_total_refund
        + anchor1_23_48_total_refund
        + anchor1_23_49_total_refund
        + anchor12_3_7_total_refund
        + anchor12_3_10_total_refund
    )
    total_refund_rate_all = (
        total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
    )
    total_hit_rate_all = total_hits_any / total_races if total_races > 0 else 0.0
    avg_holes_per_race = total_holes_all / total_races if total_races > 0 else 0.0
    avg_bet_per_race = total_bet_all / total_races if total_races > 0 else 0.0
    total_profit_all = total_refund_all - total_bet_all
    anchor1_24_57_profit = anchor1_24_57_total_refund - anchor1_24_57_total_bet
    anchor1_24_quinella_profit = (
        anchor1_24_quinella_total_refund - anchor1_24_quinella_total_bet
    )
    anchor1_26_quinella_profit = (
        anchor1_26_quinella_total_refund - anchor1_26_quinella_total_bet
    )
    top3pair_46_quinella_profit = (
        top3pair_46_quinella_total_refund - top3pair_46_quinella_total_bet
    )
    anchor12_3_4_quinella_profit = (
        anchor12_3_4_quinella_total_refund - anchor12_3_4_quinella_total_bet
    )
    anchor12_3_5_quinella_profit = (
        anchor12_3_5_quinella_total_refund - anchor12_3_5_quinella_total_bet
    )
    anchor12_3_6_quinella_profit = (
        anchor12_3_6_quinella_total_refund - anchor12_3_6_quinella_total_bet
    )
    anchor12_3_7_quinella_profit = (
        anchor12_3_7_quinella_total_refund - anchor12_3_7_quinella_total_bet
    )
    anchor12_3_8_quinella_profit = (
        anchor12_3_8_quinella_total_refund - anchor12_3_8_quinella_total_bet
    )
    anchor12_3_12_quinella_profit = (
        anchor12_3_12_quinella_total_refund - anchor12_3_12_quinella_total_bet
    )
    anchor1_24_58_profit = anchor1_24_58_total_refund - anchor1_24_58_total_bet
    top4_box_trifecta_profit = (
        top4_box_trifecta_total_refund - top4_box_trifecta_total_bet
    )
    top5_box_trifecta_profit = (
        top5_box_trifecta_total_refund - top5_box_trifecta_total_bet
    )
    top6_trio_profit = top6_trio_total_refund - top6_trio_total_bet
    top3pair_46_trio_profit = (
        top3pair_46_trio_total_refund - top3pair_46_trio_total_bet
    )
    top3pair_47_trio_profit = (
        top3pair_47_trio_total_refund - top3pair_47_trio_total_bet
    )
    top3pair_49_trio_profit = (
        top3pair_49_trio_total_refund - top3pair_49_trio_total_bet
    )
    top4pair_58_trio_profit = (
        top4pair_58_trio_total_refund - top4pair_58_trio_total_bet
    )
    top12anchor_3_10_trio_profit = (
        top12anchor_3_10_trio_total_refund - top12anchor_3_10_trio_total_bet
    )
    top12anchor_3_8_12_trio_profit = (
        top12anchor_3_8_12_trio_total_refund - top12anchor_3_8_12_trio_total_bet
    )
    top12anchor_3_12_trio_profit = (
        top12anchor_3_12_trio_total_refund - top12anchor_3_12_trio_total_bet
    )
    anchor1_57_24_profit = anchor1_57_24_total_refund - anchor1_57_24_total_bet
    anchor1_58_24_profit = anchor1_58_24_total_refund - anchor1_58_24_total_bet
    anchor3_24_profit = anchor3_24_total_refund - anchor3_24_total_bet
    anchor2_24_profit = anchor2_24_total_refund - anchor2_24_total_bet
    anchor1_24_profit = anchor1_24_total_refund - anchor1_24_total_bet
    anchor1_25_profit = anchor1_25_total_refund - anchor1_25_total_bet
    anchor1_25_68_profit = anchor1_25_68_total_refund - anchor1_25_68_total_bet
    anchor1_25_69_profit = anchor1_25_69_total_refund - anchor1_25_69_total_bet
    anchor1_69_25_profit = anchor1_69_25_total_refund - anchor1_69_25_total_bet
    anchor1_23_46_profit = anchor1_23_46_total_refund - anchor1_23_46_total_bet
    anchor1_23_47_profit = anchor1_23_47_total_refund - anchor1_23_47_total_bet
    anchor1_23_48_profit = anchor1_23_48_total_refund - anchor1_23_48_total_bet
    anchor1_23_49_profit = anchor1_23_49_total_refund - anchor1_23_49_total_bet
    anchor12_3_7_profit = anchor12_3_7_total_refund - anchor12_3_7_total_bet
    anchor12_3_10_profit = anchor12_3_10_total_refund - anchor12_3_10_total_bet
    summary["total_bet_all"] = total_bet_all
    summary["total_refund_all"] = total_refund_all
    summary["total_profit_all"] = total_profit_all
    summary["total_refund_rate_all"] = total_refund_rate_all
    summary["total_hit_rate_all"] = total_hit_rate_all
    summary["track_summary"] = track_summary
    summary["track_month_summary"] = track_month_summary
    summary["strategy_track_summary"] = strategy_track_summary

    print("===================================")
    print("[전체 총계]")
    print(f"기간: {from_date} ~ {to_date}")
    print(f"경주수: {total_races}  제외(신마 3두 이상/13두↑): {excluded_races}")
    print(
        f"[총 환수율]  총베팅액: {int(total_bet_all):,}원  "
        f"총환수액: {total_refund_all:,.1f}원  이익금액: {total_profit_all:,.1f}원  "
        f"환수율: {total_refund_rate_all:.3f}  "
        f"적중경주수: {total_hits_any}  적중율: {total_hit_rate_all:.3f}"
    )
    print(
        f"[경주당]  총구멍수: {avg_holes_per_race:.1f}  "
        f"총베팅액: {avg_bet_per_race:,.1f}원"
    )
    print("[경마장별 총계]")
    sorted_tracks = sorted(track_summary.keys(), key=lambda x: str(x))
    for track in sorted_tracks:
        d = track_summary[track]
        track_refund_rate = (
            d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
        )
        track_hit_rate = d["hits"] / d["races"] if d["races"] > 0 else 0.0
        track_profit = d["total_refund"] - d["total_bet"]
        r_pop1_top1_rate = (
            d["r_pop1_top1_hits"] / d["races"] if d["races"] > 0 else 0.0
        )
        r_pop1_top3_rate = (
            d["r_pop1_top3_hits"] / d["races"] if d["races"] > 0 else 0.0
        )
        print(
            f"[경마장별 {track}]  경주수: {d['races']}  "
            f"총베팅액: {int(d['total_bet']):,}원  총환수액: {d['total_refund']:,.1f}원  "
            f"이익금액: {track_profit:,.1f}원  환수율: {track_refund_rate:.3f}  "
            f"적중경주수: {d['hits']}  적중율: {track_hit_rate:.3f}  "
            f"r_pop1_1위_적중율: {r_pop1_top1_rate:.3f}  "
            f"r_pop1_3위내_적중율: {r_pop1_top3_rate:.3f}"
        )
        for track_month_key in sorted(
            track_month_summary.keys(), key=lambda x: (str(x[0]), x[1])
        ):
            if track_month_key[0] != track:
                continue
            month_data = track_month_summary[track_month_key]
            track_month_refund_rate = (
                month_data["total_refund"] / month_data["total_bet"]
                if month_data["total_bet"] > 0
                else 0.0
            )
            track_month_hit_rate = (
                month_data["hits"] / month_data["races"]
                if month_data["races"] > 0
                else 0.0
            )
            track_month_profit = month_data["total_refund"] - month_data["total_bet"]
            r_pop1_top1_rate = (
                month_data["r_pop1_top1_hits"] / month_data["races"]
                if month_data["races"] > 0
                else 0.0
            )
            r_pop1_top3_rate = (
                month_data["r_pop1_top3_hits"] / month_data["races"]
                if month_data["races"] > 0
                else 0.0
            )
            print(
                f"  [월별 {month_data['year_month']}]  경주수: {month_data['races']}  "
                f"총베팅액: {int(month_data['total_bet']):,}원  총환수액: {month_data['total_refund']:,.1f}원  "
                f"이익금액: {track_month_profit:,.1f}원  환수율: {track_month_refund_rate:.3f}  "
                f"적중경주수: {month_data['hits']}  적중율: {track_month_hit_rate:.3f}  "
                f"r_pop1_1위_적중율: {r_pop1_top1_rate:.3f}  "
                f"r_pop1_3위내_적중율: {r_pop1_top3_rate:.3f}"
            )
        for week_track_key in sorted(
            week_track_summary.keys(), key=lambda x: (str(x[1]), x[0])
        ):
            if week_track_key[1] != track:
                continue
            week_data = week_track_summary[week_track_key]
            day_refund_rate = (
                week_data["total_refund"] / week_data["total_bet"]
                if week_data["total_bet"] > 0
                else 0.0
            )
            day_hit_rate = (
                week_data["hits"] / week_data["races"]
                if week_data["races"] > 0
                else 0.0
            )
            day_profit = week_data["total_refund"] - week_data["total_bet"]
            print(
                f"  [토요일기준 {week_data['week']}]  경주수: {week_data['races']}  "
                f"총베팅액: {int(week_data['total_bet']):,}원  총환수액: {week_data['total_refund']:,.1f}원  "
                f"이익금액: {day_profit:,.1f}원  "
                f"환수율: {day_refund_rate:.3f}  적중경주수: {week_data['hits']}  적중율: {day_hit_rate:.3f}"
            )
    def print_strategy_total(
        strategy_key: str,
        total_bet: float,
        total_refund: float,
        profit: float,
        hit_rate: float,
        refund_rate: float,
    ) -> None:
        if strategy_key in EXCLUDED_STRATEGY_KEYS:
            return
        print(
            f"{strategy_labels[strategy_key]}  "
            f"적중율: {hit_rate:.3f}  "
            f"총베팅액: {int(total_bet):,}원  "
            f"총환수액: {total_refund:,.1f}원  "
            f"이익금액: {profit:,.1f}원  "
            f"환수율: {refund_rate:.3f}"
        )

    def print_strategy_track_details(strategy_key: str) -> None:
        if strategy_key in EXCLUDED_STRATEGY_KEYS:
            return
        for track_name in sorted(strategy_track_summary.get(strategy_key, {}).keys(), key=lambda x: str(x)):
            track_data = strategy_track_summary[strategy_key][track_name]
            track_profit = track_data["total_refund"] - track_data["total_bet"]
            track_refund_rate = (
                track_data["total_refund"] / track_data["total_bet"]
                if track_data["total_bet"] > 0
                else 0.0
            )
            track_hit_rate = (
                track_data["hits"] / track_data["races"]
                if track_data["races"] > 0
                else 0.0
            )
            print(
                (
                    f"  {track_name} | "
                    if SHOW_TRACK_NAME_IN_STRATEGY_SECTION
                    else "  "
                )
                + f"경주 {track_data['races']:,} | "
                f"적중 {track_data['hits']:,} ({track_hit_rate:.3f}) | "
                f"베팅 {int(track_data['total_bet']):,}원 | "
                f"환수 {track_data['total_refund']:,.1f}원 | "
                f"이익 {track_profit:,.1f}원 | "
                f"환수율 {track_refund_rate:.3f}"
            )

    def print_strategy_track_summary_line(strategy_key: str) -> None:
        if strategy_key in EXCLUDED_STRATEGY_KEYS:
            return
        for track_name in sorted(strategy_track_summary.get(strategy_key, {}).keys(), key=lambda x: str(x)):
            track_data = strategy_track_summary[strategy_key][track_name]
            track_profit = track_data["total_refund"] - track_data["total_bet"]
            track_refund_rate = (
                track_data["total_refund"] / track_data["total_bet"]
                if track_data["total_bet"] > 0
                else 0.0
            )
            track_hit_rate = (
                track_data["hits"] / track_data["races"]
                if track_data["races"] > 0
                else 0.0
            )
            track_prefix = (
                f"  {track_name} | " if SHOW_TRACK_NAME_IN_STRATEGY_SECTION else "  "
            )
            print(
                f"{strategy_labels[strategy_key]} | "
                + track_prefix
                + f"경주 {track_data['races']:,} | "
                f"적중 {track_data['hits']:,} ({track_hit_rate:.3f}) | "
                f"베팅 {int(track_data['total_bet']):,}원 | "
                f"환수 {track_data['total_refund']:,.1f}원 | "
                f"이익 {track_profit:,.1f}원 | "
                f"환수율 {track_refund_rate:.3f}"
            )

    print("[베팅방법별 총계]")
    print_strategy_total(
        "anchor1_24_57",
        anchor1_24_57_total_bet,
        anchor1_24_57_total_refund,
        anchor1_24_57_profit,
        summary["anchor1_24_57_hit_rate"],
        summary["anchor1_24_57_refund_rate"],
    )
    print_strategy_total(
        "anchor1_24_quinella",
        anchor1_24_quinella_total_bet,
        anchor1_24_quinella_total_refund,
        anchor1_24_quinella_profit,
        summary["anchor1_24_quinella_hit_rate"],
        summary["anchor1_24_quinella_refund_rate"],
    )
    print_strategy_total(
        "anchor1_26_quinella",
        anchor1_26_quinella_total_bet,
        anchor1_26_quinella_total_refund,
        anchor1_26_quinella_profit,
        summary["anchor1_26_quinella_hit_rate"],
        summary["anchor1_26_quinella_refund_rate"],
    )
    print_strategy_total(
        "top3pair_46_quinella",
        top3pair_46_quinella_total_bet,
        top3pair_46_quinella_total_refund,
        top3pair_46_quinella_profit,
        summary["top3pair_46_quinella_hit_rate"],
        summary["top3pair_46_quinella_refund_rate"],
    )
    print_strategy_total(
        "anchor12_3_4_quinella",
        anchor12_3_4_quinella_total_bet,
        anchor12_3_4_quinella_total_refund,
        anchor12_3_4_quinella_profit,
        summary["anchor12_3_4_quinella_hit_rate"],
        summary["anchor12_3_4_quinella_refund_rate"],
    )
    print_strategy_total(
        "anchor12_3_5_quinella",
        anchor12_3_5_quinella_total_bet,
        anchor12_3_5_quinella_total_refund,
        anchor12_3_5_quinella_profit,
        summary["anchor12_3_5_quinella_hit_rate"],
        summary["anchor12_3_5_quinella_refund_rate"],
    )
    print_strategy_total(
        "anchor12_3_6_quinella",
        anchor12_3_6_quinella_total_bet,
        anchor12_3_6_quinella_total_refund,
        anchor12_3_6_quinella_profit,
        summary["anchor12_3_6_quinella_hit_rate"],
        summary["anchor12_3_6_quinella_refund_rate"],
    )
    print_strategy_total(
        "anchor12_3_7_quinella",
        anchor12_3_7_quinella_total_bet,
        anchor12_3_7_quinella_total_refund,
        anchor12_3_7_quinella_profit,
        summary["anchor12_3_7_quinella_hit_rate"],
        summary["anchor12_3_7_quinella_refund_rate"],
    )
    print_strategy_total(
        "anchor12_3_8_quinella",
        anchor12_3_8_quinella_total_bet,
        anchor12_3_8_quinella_total_refund,
        anchor12_3_8_quinella_profit,
        summary["anchor12_3_8_quinella_hit_rate"],
        summary["anchor12_3_8_quinella_refund_rate"],
    )
    print_strategy_total(
        "anchor12_3_12_quinella",
        anchor12_3_12_quinella_total_bet,
        anchor12_3_12_quinella_total_refund,
        anchor12_3_12_quinella_profit,
        summary["anchor12_3_12_quinella_hit_rate"],
        summary["anchor12_3_12_quinella_refund_rate"],
    )
    print_strategy_total(
        "anchor1_24_58",
        anchor1_24_58_total_bet,
        anchor1_24_58_total_refund,
        anchor1_24_58_profit,
        summary["anchor1_24_58_hit_rate"],
        summary["anchor1_24_58_refund_rate"],
    )
    print_strategy_total(
        "top4_box_trifecta",
        top4_box_trifecta_total_bet,
        top4_box_trifecta_total_refund,
        top4_box_trifecta_profit,
        summary["top4_box_trifecta_hit_rate"],
        summary["top4_box_trifecta_refund_rate"],
    )
    print_strategy_total(
        "top5_box_trifecta",
        top5_box_trifecta_total_bet,
        top5_box_trifecta_total_refund,
        top5_box_trifecta_profit,
        summary["top5_box_trifecta_hit_rate"],
        summary["top5_box_trifecta_refund_rate"],
    )
    print_strategy_total(
        "top6_trio",
        top6_trio_total_bet,
        top6_trio_total_refund,
        top6_trio_profit,
        summary["top6_trio_hit_rate"],
        summary["top6_trio_refund_rate"],
    )
    print_strategy_total(
        "top3pair_46_trio",
        top3pair_46_trio_total_bet,
        top3pair_46_trio_total_refund,
        top3pair_46_trio_profit,
        summary["top3pair_46_trio_hit_rate"],
        summary["top3pair_46_trio_refund_rate"],
    )
    print_strategy_total(
        "top3pair_47_trio",
        top3pair_47_trio_total_bet,
        top3pair_47_trio_total_refund,
        top3pair_47_trio_profit,
        summary["top3pair_47_trio_hit_rate"],
        summary["top3pair_47_trio_refund_rate"],
    )
    print_strategy_total(
        "top3pair_49_trio",
        top3pair_49_trio_total_bet,
        top3pair_49_trio_total_refund,
        top3pair_49_trio_profit,
        summary["top3pair_49_trio_hit_rate"],
        summary["top3pair_49_trio_refund_rate"],
    )
    print_strategy_total(
        "top4pair_58_trio",
        top4pair_58_trio_total_bet,
        top4pair_58_trio_total_refund,
        top4pair_58_trio_profit,
        summary["top4pair_58_trio_hit_rate"],
        summary["top4pair_58_trio_refund_rate"],
    )
    print_strategy_total(
        "top12anchor_3_10_trio",
        top12anchor_3_10_trio_total_bet,
        top12anchor_3_10_trio_total_refund,
        top12anchor_3_10_trio_profit,
        summary["top12anchor_3_10_trio_hit_rate"],
        summary["top12anchor_3_10_trio_refund_rate"],
    )
    print_strategy_total(
        "top12anchor_3_8_12_trio",
        top12anchor_3_8_12_trio_total_bet,
        top12anchor_3_8_12_trio_total_refund,
        top12anchor_3_8_12_trio_profit,
        summary["top12anchor_3_8_12_trio_hit_rate"],
        summary["top12anchor_3_8_12_trio_refund_rate"],
    )
    print_strategy_total(
        "top12anchor_3_12_trio",
        top12anchor_3_12_trio_total_bet,
        top12anchor_3_12_trio_total_refund,
        top12anchor_3_12_trio_profit,
        summary["top12anchor_3_12_trio_hit_rate"],
        summary["top12anchor_3_12_trio_refund_rate"],
    )
    print_strategy_total(
        "anchor1_57_24",
        anchor1_57_24_total_bet,
        anchor1_57_24_total_refund,
        anchor1_57_24_profit,
        summary["anchor1_57_24_hit_rate"],
        summary["anchor1_57_24_refund_rate"],
    )
    print_strategy_total(
        "anchor1_58_24",
        anchor1_58_24_total_bet,
        anchor1_58_24_total_refund,
        anchor1_58_24_profit,
        summary["anchor1_58_24_hit_rate"],
        summary["anchor1_58_24_refund_rate"],
    )
    print_strategy_total(
        "anchor3_24",
        anchor3_24_total_bet,
        anchor3_24_total_refund,
        anchor3_24_profit,
        summary["anchor3_24_hit_rate"],
        summary["anchor3_24_refund_rate"],
    )
    print_strategy_total(
        "anchor2_24",
        anchor2_24_total_bet,
        anchor2_24_total_refund,
        anchor2_24_profit,
        summary["anchor2_24_hit_rate"],
        summary["anchor2_24_refund_rate"],
    )
    print_strategy_total(
        "anchor1_24",
        anchor1_24_total_bet,
        anchor1_24_total_refund,
        anchor1_24_profit,
        summary["anchor1_24_hit_rate"],
        summary["anchor1_24_refund_rate"],
    )
    print_strategy_total(
        "anchor1_25",
        anchor1_25_total_bet,
        anchor1_25_total_refund,
        anchor1_25_profit,
        summary["anchor1_25_hit_rate"],
        summary["anchor1_25_refund_rate"],
    )
    print_strategy_total(
        "anchor1_25_68",
        anchor1_25_68_total_bet,
        anchor1_25_68_total_refund,
        anchor1_25_68_profit,
        summary["anchor1_25_68_hit_rate"],
        summary["anchor1_25_68_refund_rate"],
    )
    print_strategy_total(
        "anchor1_25_69",
        anchor1_25_69_total_bet,
        anchor1_25_69_total_refund,
        anchor1_25_69_profit,
        summary["anchor1_25_69_hit_rate"],
        summary["anchor1_25_69_refund_rate"],
    )
    print_strategy_total(
        "anchor1_69_25",
        anchor1_69_25_total_bet,
        anchor1_69_25_total_refund,
        anchor1_69_25_profit,
        summary["anchor1_69_25_hit_rate"],
        summary["anchor1_69_25_refund_rate"],
    )
    print_strategy_total(
        "anchor1_23_46",
        anchor1_23_46_total_bet,
        anchor1_23_46_total_refund,
        anchor1_23_46_profit,
        summary["anchor1_23_46_hit_rate"],
        summary["anchor1_23_46_refund_rate"],
    )
    print_strategy_total(
        "anchor1_23_47",
        anchor1_23_47_total_bet,
        anchor1_23_47_total_refund,
        anchor1_23_47_profit,
        summary["anchor1_23_47_hit_rate"],
        summary["anchor1_23_47_refund_rate"],
    )
    print_strategy_total(
        "anchor1_23_48",
        anchor1_23_48_total_bet,
        anchor1_23_48_total_refund,
        anchor1_23_48_profit,
        summary["anchor1_23_48_hit_rate"],
        summary["anchor1_23_48_refund_rate"],
    )
    print_strategy_total(
        "anchor1_23_49",
        anchor1_23_49_total_bet,
        anchor1_23_49_total_refund,
        anchor1_23_49_profit,
        summary["anchor1_23_49_hit_rate"],
        summary["anchor1_23_49_refund_rate"],
    )
    print_strategy_total(
        "anchor12_3_7",
        anchor12_3_7_total_bet,
        anchor12_3_7_total_refund,
        anchor12_3_7_profit,
        summary["anchor12_3_7_hit_rate"],
        summary["anchor12_3_7_refund_rate"],
    )
    print_strategy_total(
        "anchor12_3_10",
        anchor12_3_10_total_bet,
        anchor12_3_10_total_refund,
        anchor12_3_10_profit,
        summary["anchor12_3_10_hit_rate"],
        summary["anchor12_3_10_refund_rate"],
    )
    print(STRATEGY_TRACK_SECTION_LABEL)
    for strategy_key in strategy_labels.keys():
        if strategy_key in EXCLUDED_STRATEGY_KEYS:
            continue
        if COMBINE_STRATEGY_AND_TRACK_LINE:
            print_strategy_track_summary_line(strategy_key)
        else:
            print(strategy_labels[strategy_key])
            print_strategy_track_details(strategy_key)
            print()
    for ym in sorted(month_summary.keys()):
        m = month_summary[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        r_pop1_top1_rate = m["r_pop1_top1_hits"] / m["races"] if m["races"] > 0 else 0.0
        r_pop1_top3_rate = m["r_pop1_top3_hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}  "
            f"r_pop1_1위_적중수: {m['r_pop1_top1_hits']}  r_pop1_1위_적중율: {r_pop1_top1_rate:.3f}  "
            f"r_pop1_3위내_적중수: {m['r_pop1_top3_hits']}  r_pop1_3위내_적중율: {r_pop1_top3_rate:.3f}"
        )
    if SHOW_MONTHLY_STRATEGY_OUTPUT:
        if "anchor1_24_57" not in EXCLUDED_STRATEGY_KEYS:
            for ym in sorted(month_summary_anchor_24_57.keys()):
                m = month_summary_anchor_24_57[ym]
                month_refund_rate = (
                    m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
                )
                month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
                month_profit = m["total_refund"] - m["total_bet"]
                print(
                    f"[월별(1축2~4/5~7) {ym}]  경주수: {m['races']}  "
                    f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                    f"이익금액: {month_profit:,.1f}원  "
                    f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
                )
        for ym in sorted(month_summary_anchor1_24_quinella.keys()):
            m = month_summary_anchor1_24_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1축2~4) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor1_26_quinella.keys()):
            m = month_summary_anchor1_26_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1축2~6) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top3pair_46_quinella.keys()):
            m = month_summary_top3pair_46_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1~3복조/4~6) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor12_3_4_quinella.keys()):
            m = month_summary_anchor12_3_4_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1,2축/3~4) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor12_3_5_quinella.keys()):
            m = month_summary_anchor12_3_5_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1,2축/3~5) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor12_3_6_quinella.keys()):
            m = month_summary_anchor12_3_6_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1,2축/3~6) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor12_3_7_quinella.keys()):
            m = month_summary_anchor12_3_7_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1,2축/3~7) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor12_3_8_quinella.keys()):
            m = month_summary_anchor12_3_8_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1,2축/3~8) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor12_3_12_quinella.keys()):
            m = month_summary_anchor12_3_12_quinella[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(복승식 1,2축/3~12) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_24_58.keys()):
            m = month_summary_anchor_24_58[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~4/5~8) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top4_box_trifecta.keys()):
            m = month_summary_top4_box_trifecta[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~4 4복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top5_box_trifecta.keys()):
            m = month_summary_top5_box_trifecta[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~5 5복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top6_trio.keys()):
            m = month_summary_top6_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~6 6복조 삼복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top3pair_46_trio.keys()):
            m = month_summary_top3pair_46_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~3 복조/4~6 삼복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top3pair_47_trio.keys()):
            m = month_summary_top3pair_47_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~3 복조/4~7 삼복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top3pair_49_trio.keys()):
            m = month_summary_top3pair_49_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~3 복조/4~9 삼복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top4pair_58_trio.keys()):
            m = month_summary_top4pair_58_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~4 복조/5~8 삼복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top12anchor_3_10_trio.keys()):
            m = month_summary_top12anchor_3_10_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~2 복조축/3~10 삼복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top12anchor_3_8_12_trio.keys()):
            m = month_summary_top12anchor_3_8_12_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~2 복조축/3~8,12 삼복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_top12anchor_3_12_trio.keys()):
            m = month_summary_top12anchor_3_12_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1~2 복조축/3~12 삼복) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        if "anchor3_24" not in EXCLUDED_STRATEGY_KEYS:
            for ym in sorted(month_summary_anchor3_24.keys()):
                m = month_summary_anchor3_24[ym]
                month_refund_rate = (
                    m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
                )
                month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
                month_profit = m["total_refund"] - m["total_bet"]
                print(
                    f"[월별(3축1/1~2축2~4) {ym}]  경주수: {m['races']}  "
                    f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                    f"이익금액: {month_profit:,.1f}원  "
                    f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
                )
        if "anchor2_24" not in EXCLUDED_STRATEGY_KEYS:
            for ym in sorted(month_summary_anchor2_24.keys()):
                m = month_summary_anchor2_24[ym]
                month_refund_rate = (
                    m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
                )
                month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
                month_profit = m["total_refund"] - m["total_bet"]
                print(
                    f"[월별(2축1/1,3축2~4) {ym}]  경주수: {m['races']}  "
                    f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                    f"이익금액: {month_profit:,.1f}원  "
                    f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
                )
        for ym in sorted(month_summary_rpop5_7_anchor_1_4_trio.keys()):
            m = month_summary_rpop5_7_anchor_1_4_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축5~7/2~4) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_rpop5_8_anchor_1_4_trio.keys()):
            m = month_summary_rpop5_8_anchor_1_4_trio[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축5~8/2~4) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_24.keys()):
            m = month_summary_anchor_24[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~4) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_25.keys()):
            m = month_summary_anchor_25[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~5 4복조) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_25_68.keys()):
            m = month_summary_anchor_25_68[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~5/6~8) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_25_69.keys()):
            m = month_summary_anchor_25_69[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~5/6~9) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_69_25.keys()):
            m = month_summary_anchor_69_25[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축6~9/2~5) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_23_46.keys()):
            m = month_summary_anchor_23_46[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~3/4~6) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_23_47.keys()):
            m = month_summary_anchor_23_47[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~3/4~7) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_23_48.keys()):
            m = month_summary_anchor_23_48[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~3/4~8) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor_23_49.keys()):
            m = month_summary_anchor_23_49[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2~3/4~9) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor12_3_7.keys()):
            m = month_summary_anchor12_3_7[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2축/3~7) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
        for ym in sorted(month_summary_anchor12_3_10.keys()):
            m = month_summary_anchor12_3_10[ym]
            month_refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            month_profit = m["total_refund"] - m["total_bet"]
            print(
                f"[월별(1축2축/3~10) {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"이익금액: {month_profit:,.1f}원  "
                f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
            )
    week_rows = []
    for week_track_key in sorted(week_track_summary.keys(), key=lambda x: (x[0], str(x[1]))):
        d = week_track_summary[week_track_key]
        day_refund_rate = (
            d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
        )
        day_hit_rate = d["hits"] / d["races"] if d["races"] > 0 else 0.0
        day_profit = d["total_refund"] - d["total_bet"]
        week_rows.append(
            {
                "토요일기준일": d["week"],
                "경마장": d["track"],
                "경주수": d["races"],
                "총베팅액": d["total_bet"],
                "총환수액": d["total_refund"],
                "이익금액": day_profit,
                "환수율": day_refund_rate,
                "적중경주수": d["hits"],
                "적중율": day_hit_rate,
            }
        )
    if week_rows:
        week_df = pd.DataFrame(week_rows)
        week_out_path = "/Users/Super007/Documents/r_pop_weekly_summary.csv"
        week_df.to_csv(week_out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 토요일 기준 주별 총 집계 CSV 저장: {week_out_path}")
        upsert_weekly_betting_summary(engine, week_df)
        print("▶ weekly_betting_summary upsert 완료")
    print("===================================")

    return race_df, summary


if __name__ == "__main__":
    from_date = "20250101"
    to_date = "20260330"
    





    race_df, summary = calc_rpop_anchor_26_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,
        apply_odds_filter=False,
    )

    out_path = "/Users/Super007/Documents/r_pop_total_new.csv"
    if not race_df.empty:
        race_df = race_df.drop_duplicates(subset=["경마장", "경주일", "경주번호"])
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
