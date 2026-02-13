import pandas as pd
from sqlalchemy import create_engine, text


# =========================
# 0. DB 접속 설정 (필요에 맞게 수정)
# =========================
DB_CONF = {
    "host": "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",
    "port": 3306,
    "user": "letslove",
    "password": "Ruddksp!23",
    "db": "The1",
    "charset": "utf8mb4",
}


def get_engine():
    """SQLAlchemy 엔진 생성."""
    url = (
        f"mysql+pymysql://{DB_CONF['user']}:{DB_CONF['password']}"
        f"@{DB_CONF['host']}:{DB_CONF['port']}/{DB_CONF['db']}?charset={DB_CONF['charset']}"
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
    r_pop(예상), r_rank(실제순위), 삼쌍승식 배당 포함.
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
        CAST(SUBSTRING(r.r123alloc, 4) AS DECIMAL(10, 0)) AS 삼쌍승식배당율,
        CAST(SUBSTRING(r.r333alloc, 4) AS DECIMAL(10, 0)) AS 삼복승식배당율
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


# =========================
# 2. r_pop 1축(2~4) 2등/5~7 3등 삼쌍승식
#    + r_pop 1~4 BOX4 삼복승식 환수 계산
# =========================
def calc_rpop_anchor_26_trifecta(
    from_date: str,
    to_date: str,
    bet_unit: int = 100,
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
    - 각 경주에 대해 r_pop 1을 1등축으로,
      r_pop 2~4(2등축), r_pop 5~7(3등) 삼쌍승식 베팅.
    - r_pop 1축 + r_pop 2~4(3복조) 삼쌍승식 베팅.
    - r_pop 1축 + r_pop 2~4 삼복승식 베팅.
    - r_pop 1~4 BOX4 삼복승식 베팅.
    - 실제 1~3위가 (r_pop1, r_pop2~4, r_pop5~7) 순서로 맞으면 적중.
    - BOX4는 실제 1~3위가 r_pop 1~4 안에 있으면 적중.
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

    df["삼쌍승식배당율"] = pd.to_numeric(df["삼쌍승식배당율"], errors="coerce").fillna(
        0.0
    )
    df["삼복승식배당율"] = pd.to_numeric(df["삼복승식배당율"], errors="coerce").fillna(
        0.0
    )
    # 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    anchor1_24_57_bet_unit = 100
    anchor1_24_57_bet_per_race = 9 * anchor1_24_57_bet_unit  # 3 * 3
    anchor1_24_bet_unit = 100
    anchor1_24_bet_per_race = 6 * anchor1_24_bet_unit  # 3P2
    anchor1_24_trio_bet_unit = 100
    anchor1_24_trio_bet_per_race = 3 * anchor1_24_trio_bet_unit  # C(3,2)
    box4_trio_bet_unit = 100
    box4_trio_bet_per_race = 4 * box4_trio_bet_unit  # C(4,3)
    top3_anchor_4_8_trio_unit = 100
    top3_anchor_4_8_trio_bet_per_race = 15 * top3_anchor_4_8_trio_unit  # C(3,2)*5
    top3_anchor_4_7_trio_unit = 100
    top3_anchor_4_7_trio_bet_per_race = 12 * top3_anchor_4_7_trio_unit  # C(3,2)*4
    anchor1_25_trio_unit = 100
    anchor1_25_trio_bet_per_race = 6 * anchor1_25_trio_unit  # C(4,2)
    anchor1_26_trio_unit = 100
    anchor1_26_trio_bet_per_race = 10 * anchor1_26_trio_unit  # C(5,2)
    anchor12_36_trio_unit = 100
    anchor12_36_trio_bet_per_race = 4 * anchor12_36_trio_unit  # 2 anchors + 4 choices
    top3_anchor_4_6_trio_unit = 100
    top3_anchor_4_6_trio_bet_per_race = 9 * top3_anchor_4_6_trio_unit  # C(3,2)*3
    top3_anchor_4_6_trifecta_unit = 100
    top3_anchor_4_6_trifecta_bet_per_race = (
        18 * top3_anchor_4_6_trifecta_unit
    )  # P(3,2)*3
    total_races = 0
    excluded_races = 0
    anchor1_24_57_total_bet = 0.0
    anchor1_24_57_total_refund = 0.0
    anchor1_24_57_total_hits = 0
    anchor1_24_total_bet = 0.0
    anchor1_24_total_refund = 0.0
    anchor1_24_total_hits = 0
    anchor1_24_trio_total_bet = 0.0
    anchor1_24_trio_total_refund = 0.0
    anchor1_24_trio_total_hits = 0
    box4_trio_total_bet = 0.0
    box4_trio_total_refund = 0.0
    box4_trio_total_hits = 0
    top3_anchor_4_8_trio_total_bet = 0.0
    top3_anchor_4_8_trio_total_refund = 0.0
    top3_anchor_4_8_trio_total_hits = 0
    top3_anchor_4_7_trio_total_bet = 0.0
    top3_anchor_4_7_trio_total_refund = 0.0
    top3_anchor_4_7_trio_total_hits = 0
    anchor1_25_trio_total_bet = 0.0
    anchor1_25_trio_total_refund = 0.0
    anchor1_25_trio_total_hits = 0
    anchor1_26_trio_total_bet = 0.0
    anchor1_26_trio_total_refund = 0.0
    anchor1_26_trio_total_hits = 0
    anchor12_36_trio_total_bet = 0.0
    anchor12_36_trio_total_refund = 0.0
    anchor12_36_trio_total_hits = 0
    top3_anchor_4_6_trio_total_bet = 0.0
    top3_anchor_4_6_trio_total_refund = 0.0
    top3_anchor_4_6_trio_total_hits = 0
    top3_anchor_4_6_trifecta_total_bet = 0.0
    top3_anchor_4_6_trifecta_total_refund = 0.0
    top3_anchor_4_6_trifecta_total_hits = 0
    total_hits_any = 0
    total_holes_all = 0
    week_summary = {}
    month_summary = {}
    month_summary_anchor_24_57 = {}
    month_summary_anchor_24 = {}
    month_summary_anchor1_24_trio = {}
    month_summary_box4_trio = {}
    month_summary_rpop1_5_7_anchor_2_4_trio = {}
    month_summary_rpop5_7_anchor_1_4_trio = {}
    month_summary_top3_anchor_4_8_trio = {}
    month_summary_top3_anchor_4_7_trio = {}
    month_summary_anchor1_25_trio = {}
    month_summary_anchor1_26_trio = {}
    month_summary_anchor12_36_trio = {}
    month_summary_top3_anchor_4_6_trio = {}
    month_summary_top3_anchor_4_6_trifecta = {}
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

        g_sorted = g.sort_values("r_pop", ascending=True)
        top4 = g_sorted.head(4)["마번"].tolist()
        anchor_gate = top4[0] if top4 else None
        top2_4 = g_sorted.iloc[1:4]["마번"].tolist()
        top5_7 = g_sorted.iloc[4:7]["마번"].tolist()
        top2_4_set = set(top2_4)
        top5_7_set = set(top5_7)
        top1_4_set = set(top4)
        top1_2 = g_sorted.iloc[0:2]["마번"].tolist()
        top1_2_set = set(top1_2)
        top1_3 = g_sorted.iloc[0:3]["마번"].tolist()
        top4_6 = g_sorted.iloc[3:6]["마번"].tolist()
        top1_3_set = set(top1_3)
        top4_6_set = set(top4_6)
        top4_10 = g_sorted.iloc[3:10]["마번"].tolist()
        top4_10_set = set(top4_10)
        top4_8 = g_sorted.iloc[3:8]["마번"].tolist()
        top4_8_set = set(top4_8)
        top4_7 = g_sorted.iloc[3:7]["마번"].tolist()
        top4_7_set = set(top4_7)
        top5_8 = g_sorted.iloc[4:8]["마번"].tolist()
        top5_8_set = set(top5_8)
        top5_7 = g_sorted.iloc[4:7]["마번"].tolist()
        top5_7_set = set(top5_7)
        top2_5 = g_sorted.iloc[1:5]["마번"].tolist()
        top2_5_set = set(top2_5)
        top2_6 = g_sorted.iloc[1:6]["마번"].tolist()
        top2_6_set = set(top2_6)
        top3_6 = g_sorted.iloc[2:6]["마번"].tolist()
        top3_6_set = set(top3_6)
        anchor1_5_7 = [anchor_gate] + top5_7 if anchor_gate is not None else top5_7
        anchor1_5_7 = list(dict.fromkeys(anchor1_5_7))
        anchor1_5_7_set = set(anchor1_5_7)

        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()
        actual_set = set(actual_top3)
        odds = float(g["삼쌍승식배당율"].iloc[0])
        odds_trio = float(g["삼복승식배당율"].iloc[0])

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
        actual_set = set(actual_top3)
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
        anchor1_24_trio_valid = anchor_gate is not None and len(top2_4) == 3
        anchor1_24_trio_hit_flag = int(
            anchor1_24_trio_valid
            and len(actual_top3) == 3
            and anchor_gate in actual_set
            and set(actual_top3).issubset({anchor_gate} | top2_4_set)
        )
        anchor1_24_trio_refund = (
            odds_trio * anchor1_24_trio_bet_unit
            if anchor1_24_trio_hit_flag == 1
            else 0.0
        )
        r_pop1_top1_hit = int(len(actual_top3) >= 1 and actual_top3[0] == anchor_gate)
        r_pop1_top3_hit = int(anchor_gate is not None and anchor_gate in actual_set)
        box4_trio_hit_flag = int(
            len(actual_set) == 3 and actual_set.issubset(set(top4))
        )
        box4_trio_refund = (
            odds_trio * box4_trio_bet_unit if box4_trio_hit_flag == 1 else 0.0
        )
        top3_anchor_4_8_trio_valid = len(top1_3) == 3 and len(top4_8) == 5
        top3_anchor_4_8_trio_hit_flag = int(
            top3_anchor_4_8_trio_valid
            and len(actual_set) == 3
            and len(actual_set.intersection(top1_3_set)) == 2
            and len(actual_set.intersection(top4_8_set)) == 1
        )
        top3_anchor_4_8_trio_refund = (
            odds_trio * top3_anchor_4_8_trio_unit
            if top3_anchor_4_8_trio_hit_flag == 1
            else 0.0
        )
        top3_anchor_4_7_trio_valid = len(top1_3) == 3 and len(top4_7) == 4
        top3_anchor_4_7_trio_hit_flag = int(
            top3_anchor_4_7_trio_valid
            and len(actual_set) == 3
            and len(actual_set.intersection(top1_3_set)) == 2
            and len(actual_set.intersection(top4_7_set)) == 1
        )
        top3_anchor_4_7_trio_refund = (
            odds_trio * top3_anchor_4_7_trio_unit
            if top3_anchor_4_7_trio_hit_flag == 1
            else 0.0
        )
        anchor1_25_trio_valid = anchor_gate is not None and len(top2_5) == 4
        anchor1_25_trio_hit_flag = int(
            anchor1_25_trio_valid
            and len(actual_set) == 3
            and anchor_gate in actual_set
            and set(actual_set).issubset({anchor_gate} | top2_5_set)
        )
        anchor1_25_trio_refund = (
            odds_trio * anchor1_25_trio_unit if anchor1_25_trio_hit_flag == 1 else 0.0
        )
        anchor1_26_trio_valid = anchor_gate is not None and len(top2_6) == 5
        anchor1_26_trio_hit_flag = int(
            anchor1_26_trio_valid
            and len(actual_set) == 3
            and anchor_gate in actual_set
            and set(actual_set).issubset({anchor_gate} | top2_6_set)
        )
        anchor1_26_trio_refund = (
            odds_trio * anchor1_26_trio_unit if anchor1_26_trio_hit_flag == 1 else 0.0
        )
        anchor12_36_trio_valid = len(top4) >= 2 and len(top3_6) == 4
        anchor12_36_trio_hit_flag = int(
            anchor12_36_trio_valid
            and len(actual_set) == 3
            and set(top4[:2]).issubset(actual_set)
            and len(actual_set.intersection(top3_6_set)) == 1
        )
        anchor12_36_trio_refund = (
            odds_trio * anchor12_36_trio_unit
            if anchor12_36_trio_hit_flag == 1
            else 0.0
        )
        top3_anchor_4_6_trio_valid = len(top1_3) == 3 and len(top4_6) == 3
        top3_anchor_4_6_trio_hit_flag = int(
            top3_anchor_4_6_trio_valid
            and len(actual_set) == 3
            and len(actual_set.intersection(top1_3_set)) == 2
            and len(actual_set.intersection(top4_6_set)) == 1
        )
        top3_anchor_4_6_trio_refund = (
            odds_trio * top3_anchor_4_6_trio_unit
            if top3_anchor_4_6_trio_hit_flag == 1
            else 0.0
        )
        top3_anchor_4_6_trifecta_valid = len(top1_3) == 3 and len(top4_6) == 3
        top3_anchor_4_6_trifecta_hit_flag = int(
            top3_anchor_4_6_trifecta_valid
            and len(actual_top3) == 3
            and actual_top3[0] in top1_3_set
            and actual_top3[1] in top1_3_set
            and actual_top3[0] != actual_top3[1]
            and actual_top3[2] in top4_6_set
        )
        top3_anchor_4_6_trifecta_refund = (
            odds * top3_anchor_4_6_trifecta_unit
            if top3_anchor_4_6_trifecta_hit_flag == 1
            else 0.0
        )
        hit_any = int(
            anchor1_24_57_hit_flag
            or anchor1_24_hit_flag
            or anchor1_24_trio_hit_flag
            or box4_trio_hit_flag
            or top3_anchor_4_8_trio_hit_flag
            or top3_anchor_4_7_trio_hit_flag
            or anchor1_25_trio_hit_flag
            or anchor1_26_trio_hit_flag
            or anchor12_36_trio_hit_flag
            or top3_anchor_4_6_trio_hit_flag
            or top3_anchor_4_6_trifecta_hit_flag
        )
        anchor1_24_57_total_bet += (
            anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
        )
        anchor1_24_57_total_refund += anchor1_24_57_refund
        anchor1_24_57_total_hits += anchor1_24_57_hit_flag
        anchor1_24_total_bet += anchor1_24_bet_per_race if anchor1_24_valid else 0.0
        anchor1_24_total_refund += anchor1_24_refund
        anchor1_24_total_hits += anchor1_24_hit_flag
        anchor1_24_trio_total_bet += (
            anchor1_24_trio_bet_per_race if anchor1_24_trio_valid else 0.0
        )
        anchor1_24_trio_total_refund += anchor1_24_trio_refund
        anchor1_24_trio_total_hits += anchor1_24_trio_hit_flag
        box4_trio_total_bet += box4_trio_bet_per_race
        box4_trio_total_refund += box4_trio_refund
        box4_trio_total_hits += box4_trio_hit_flag
        top3_anchor_4_8_trio_total_bet += (
            top3_anchor_4_8_trio_bet_per_race if top3_anchor_4_8_trio_valid else 0.0
        )
        top3_anchor_4_8_trio_total_refund += top3_anchor_4_8_trio_refund
        top3_anchor_4_8_trio_total_hits += top3_anchor_4_8_trio_hit_flag
        top3_anchor_4_7_trio_total_bet += (
            top3_anchor_4_7_trio_bet_per_race if top3_anchor_4_7_trio_valid else 0.0
        )
        top3_anchor_4_7_trio_total_refund += top3_anchor_4_7_trio_refund
        top3_anchor_4_7_trio_total_hits += top3_anchor_4_7_trio_hit_flag
        anchor1_25_trio_total_bet += (
            anchor1_25_trio_bet_per_race if anchor1_25_trio_valid else 0.0
        )
        anchor1_25_trio_total_refund += anchor1_25_trio_refund
        anchor1_25_trio_total_hits += anchor1_25_trio_hit_flag
        anchor1_26_trio_total_bet += (
            anchor1_26_trio_bet_per_race if anchor1_26_trio_valid else 0.0
        )
        anchor1_26_trio_total_refund += anchor1_26_trio_refund
        anchor1_26_trio_total_hits += anchor1_26_trio_hit_flag
        anchor12_36_trio_total_bet += (
            anchor12_36_trio_bet_per_race if anchor12_36_trio_valid else 0.0
        )
        anchor12_36_trio_total_refund += anchor12_36_trio_refund
        anchor12_36_trio_total_hits += anchor12_36_trio_hit_flag
        top3_anchor_4_6_trio_total_bet += (
            top3_anchor_4_6_trio_bet_per_race if top3_anchor_4_6_trio_valid else 0.0
        )
        top3_anchor_4_6_trio_total_refund += top3_anchor_4_6_trio_refund
        top3_anchor_4_6_trio_total_hits += top3_anchor_4_6_trio_hit_flag
        top3_anchor_4_6_trifecta_total_bet += (
            top3_anchor_4_6_trifecta_bet_per_race
            if top3_anchor_4_6_trifecta_valid
            else 0.0
        )
        top3_anchor_4_6_trifecta_total_refund += top3_anchor_4_6_trifecta_refund
        top3_anchor_4_6_trifecta_total_hits += top3_anchor_4_6_trifecta_hit_flag
        total_hits_any += hit_any

        date_dt = pd.to_datetime(date, format="%Y%m%d", errors="coerce")
        if pd.notna(date_dt):
            weekday = date_dt.weekday()
            # Saturday-centered bucket: Thu/Fri/Sat/Sun/Mon -> same Saturday,
            # Tue/Wed -> next Saturday.
            sat_offset = {0: -2, 1: -3, 2: 3, 3: 2, 4: 1, 5: 0, 6: -1}[weekday]
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
        if year_month not in month_summary:
            month_summary[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
                "r_pop1_top1_hits": 0,
                "r_pop1_top3_hits": 0,
            }
        if year_month not in month_summary_anchor_24_57:
            month_summary_anchor_24_57[year_month] = {
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
        if year_month not in month_summary_anchor1_24_trio:
            month_summary_anchor1_24_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_box4_trio:
            month_summary_box4_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_rpop1_5_7_anchor_2_4_trio:
            month_summary_rpop1_5_7_anchor_2_4_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top3_anchor_4_8_trio:
            month_summary_top3_anchor_4_8_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top3_anchor_4_7_trio:
            month_summary_top3_anchor_4_7_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor1_25_trio:
            month_summary_anchor1_25_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor1_26_trio:
            month_summary_anchor1_26_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor12_36_trio:
            month_summary_anchor12_36_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top3_anchor_4_6_trio:
            month_summary_top3_anchor_4_6_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_top3_anchor_4_6_trifecta:
            month_summary_top3_anchor_4_6_trifecta[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_summary[year_month]["races"] += 1
        week_summary[week_key]["races"] += 1
        month_summary[year_month]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (anchor1_24_trio_bet_per_race if anchor1_24_trio_valid else 0.0)
            + box4_trio_bet_per_race
            + (
                top3_anchor_4_8_trio_bet_per_race
                if top3_anchor_4_8_trio_valid
                else 0.0
            )
            + (
                top3_anchor_4_7_trio_bet_per_race
                if top3_anchor_4_7_trio_valid
                else 0.0
            )
            + (
                anchor1_25_trio_bet_per_race if anchor1_25_trio_valid else 0.0
            )
            + (
                anchor1_26_trio_bet_per_race if anchor1_26_trio_valid else 0.0
            )
            + (
                anchor12_36_trio_bet_per_race if anchor12_36_trio_valid else 0.0
            )
            + (
                top3_anchor_4_6_trio_bet_per_race
                if top3_anchor_4_6_trio_valid
                else 0.0
            )
            + (
                top3_anchor_4_6_trifecta_bet_per_race
                if top3_anchor_4_6_trifecta_valid
                else 0.0
            )
        )
        week_summary[week_key]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (anchor1_24_trio_bet_per_race if anchor1_24_trio_valid else 0.0)
            + box4_trio_bet_per_race
            + (
                top3_anchor_4_8_trio_bet_per_race
                if top3_anchor_4_8_trio_valid
                else 0.0
            )
            + (
                top3_anchor_4_7_trio_bet_per_race
                if top3_anchor_4_7_trio_valid
                else 0.0
            )
            + (
                anchor1_25_trio_bet_per_race if anchor1_25_trio_valid else 0.0
            )
            + (
                anchor1_26_trio_bet_per_race if anchor1_26_trio_valid else 0.0
            )
            + (
                anchor12_36_trio_bet_per_race if anchor12_36_trio_valid else 0.0
            )
            + (
                top3_anchor_4_6_trio_bet_per_race
                if top3_anchor_4_6_trio_valid
                else 0.0
            )
            + (
                top3_anchor_4_6_trifecta_bet_per_race
                if top3_anchor_4_6_trifecta_valid
                else 0.0
            )
        )
        month_summary[year_month]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_24_refund
            + anchor1_24_trio_refund
            + box4_trio_refund
            + top3_anchor_4_8_trio_refund
            + top3_anchor_4_7_trio_refund
            + anchor1_25_trio_refund
            + anchor1_26_trio_refund
            + anchor12_36_trio_refund
            + top3_anchor_4_6_trio_refund
            + top3_anchor_4_6_trifecta_refund
        )
        week_summary[week_key]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_24_refund
            + anchor1_24_trio_refund
            + box4_trio_refund
            + top3_anchor_4_8_trio_refund
            + top3_anchor_4_7_trio_refund
            + anchor1_25_trio_refund
            + anchor1_26_trio_refund
            + anchor12_36_trio_refund
            + top3_anchor_4_6_trio_refund
            + top3_anchor_4_6_trifecta_refund
        )
        month_summary[year_month]["hits"] += hit_any
        week_summary[week_key]["hits"] += hit_any
        month_summary[year_month]["r_pop1_top1_hits"] += r_pop1_top1_hit
        month_summary[year_month]["r_pop1_top3_hits"] += r_pop1_top3_hit
        month_summary_anchor_24_57[year_month]["races"] += 1
        month_summary_anchor_24_57[year_month]["total_bet"] += (
            anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
        )
        month_summary_anchor_24_57[year_month]["total_refund"] += anchor1_24_57_refund
        month_summary_anchor_24_57[year_month]["hits"] += anchor1_24_57_hit_flag
        month_summary_anchor_24[year_month]["races"] += 1
        month_summary_anchor_24[year_month]["total_bet"] += (
            anchor1_24_bet_per_race if anchor1_24_valid else 0.0
        )
        month_summary_anchor_24[year_month]["total_refund"] += anchor1_24_refund
        month_summary_anchor_24[year_month]["hits"] += anchor1_24_hit_flag
        month_summary_anchor1_24_trio[year_month]["races"] += 1
        month_summary_anchor1_24_trio[year_month]["total_bet"] += (
            anchor1_24_trio_bet_per_race if anchor1_24_trio_valid else 0.0
        )
        month_summary_anchor1_24_trio[year_month][
            "total_refund"
        ] += anchor1_24_trio_refund
        month_summary_anchor1_24_trio[year_month]["hits"] += anchor1_24_trio_hit_flag
        month_summary_box4_trio[year_month]["races"] += 1
        month_summary_box4_trio[year_month]["total_bet"] += box4_trio_bet_per_race
        month_summary_box4_trio[year_month]["total_refund"] += box4_trio_refund
        month_summary_box4_trio[year_month]["hits"] += box4_trio_hit_flag
        month_summary_top3_anchor_4_8_trio[year_month]["races"] += 1
        month_summary_top3_anchor_4_8_trio[year_month]["total_bet"] += (
            top3_anchor_4_8_trio_bet_per_race if top3_anchor_4_8_trio_valid else 0.0
        )
        month_summary_top3_anchor_4_8_trio[year_month][
            "total_refund"
        ] += top3_anchor_4_8_trio_refund
        month_summary_top3_anchor_4_8_trio[year_month]["hits"] += (
            top3_anchor_4_8_trio_hit_flag
        )
        month_summary_top3_anchor_4_7_trio[year_month]["races"] += 1
        month_summary_top3_anchor_4_7_trio[year_month]["total_bet"] += (
            top3_anchor_4_7_trio_bet_per_race if top3_anchor_4_7_trio_valid else 0.0
        )
        month_summary_top3_anchor_4_7_trio[year_month][
            "total_refund"
        ] += top3_anchor_4_7_trio_refund
        month_summary_top3_anchor_4_7_trio[year_month]["hits"] += (
            top3_anchor_4_7_trio_hit_flag
        )
        month_summary_anchor1_25_trio[year_month]["races"] += 1
        month_summary_anchor1_25_trio[year_month]["total_bet"] += (
            anchor1_25_trio_bet_per_race if anchor1_25_trio_valid else 0.0
        )
        month_summary_anchor1_25_trio[year_month][
            "total_refund"
        ] += anchor1_25_trio_refund
        month_summary_anchor1_25_trio[year_month]["hits"] += anchor1_25_trio_hit_flag
        month_summary_anchor1_26_trio[year_month]["races"] += 1
        month_summary_anchor1_26_trio[year_month]["total_bet"] += (
            anchor1_26_trio_bet_per_race if anchor1_26_trio_valid else 0.0
        )
        month_summary_anchor1_26_trio[year_month][
            "total_refund"
        ] += anchor1_26_trio_refund
        month_summary_anchor1_26_trio[year_month]["hits"] += anchor1_26_trio_hit_flag
        month_summary_anchor12_36_trio[year_month]["races"] += 1
        month_summary_anchor12_36_trio[year_month]["total_bet"] += (
            anchor12_36_trio_bet_per_race if anchor12_36_trio_valid else 0.0
        )
        month_summary_anchor12_36_trio[year_month][
            "total_refund"
        ] += anchor12_36_trio_refund
        month_summary_anchor12_36_trio[year_month]["hits"] += anchor12_36_trio_hit_flag
        month_summary_top3_anchor_4_6_trio[year_month]["races"] += 1
        month_summary_top3_anchor_4_6_trio[year_month]["total_bet"] += (
            top3_anchor_4_6_trio_bet_per_race if top3_anchor_4_6_trio_valid else 0.0
        )
        month_summary_top3_anchor_4_6_trio[year_month][
            "total_refund"
        ] += top3_anchor_4_6_trio_refund
        month_summary_top3_anchor_4_6_trio[year_month]["hits"] += (
            top3_anchor_4_6_trio_hit_flag
        )
        month_summary_top3_anchor_4_6_trifecta[year_month]["races"] += 1
        month_summary_top3_anchor_4_6_trifecta[year_month]["total_bet"] += (
            top3_anchor_4_6_trifecta_bet_per_race
            if top3_anchor_4_6_trifecta_valid
            else 0.0
        )
        month_summary_top3_anchor_4_6_trifecta[year_month][
            "total_refund"
        ] += top3_anchor_4_6_trifecta_refund
        month_summary_top3_anchor_4_6_trifecta[year_month]["hits"] += (
            top3_anchor_4_6_trifecta_hit_flag
        )
        holes_per_race = (
            (9 if anchor1_24_57_valid else 0)
            + (6 if anchor1_24_valid else 0)
            + (3 if anchor1_24_trio_valid else 0)
            + 4
            + (15 if top3_anchor_4_8_trio_valid else 0)
            + (12 if top3_anchor_4_7_trio_valid else 0)
            + (6 if anchor1_25_trio_valid else 0)
            + (10 if anchor1_26_trio_valid else 0)
            + (4 if anchor12_36_trio_valid else 0)
            + (9 if top3_anchor_4_6_trio_valid else 0)
            + (18 if top3_anchor_4_6_trifecta_valid else 0)
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
                "2~4_마번": ",".join(map(str, top2_4)),
                "5~7_마번": ",".join(map(str, top5_7)),
                "r_pop_top4_마번": ",".join(map(str, top4)),
                "실제_top3_마번": ",".join(map(str, actual_top3)),
                "r_pop1_축_2~4_5~7_적중": anchor1_24_57_hit_flag,
                "r_pop1_축_2~4_5~7_환수액": anchor1_24_57_refund,
                "r_pop1_축_2~4_적중": anchor1_24_hit_flag,
                "r_pop1_축_2~4_환수액": anchor1_24_refund,
                "r_pop1_축_2~4_삼복_적중": anchor1_24_trio_hit_flag,
                "r_pop1_축_2~4_삼복_환수액": anchor1_24_trio_refund,
                "r_pop1~4_BOX4_삼복_적중": box4_trio_hit_flag,
                "r_pop1~4_BOX4_삼복_환수액": box4_trio_refund,
                "r_pop1~3_복조_4~8_삼복_적중": top3_anchor_4_8_trio_hit_flag,
                "r_pop1~3_복조_4~8_삼복_환수액": top3_anchor_4_8_trio_refund,
                "r_pop1~3_복조_4~7_삼복_적중": top3_anchor_4_7_trio_hit_flag,
                "r_pop1~3_복조_4~7_삼복_환수액": top3_anchor_4_7_trio_refund,
                "r_pop1_축_2~5_삼복_적중": anchor1_25_trio_hit_flag,
                "r_pop1_축_2~5_삼복_환수액": anchor1_25_trio_refund,
                "r_pop1_축_2~6_삼복_적중": anchor1_26_trio_hit_flag,
                "r_pop1_축_2~6_삼복_환수액": anchor1_26_trio_refund,
                "r_pop1~2_복조_3~6_삼복_적중": anchor12_36_trio_hit_flag,
                "r_pop1~2_복조_3~6_삼복_환수액": anchor12_36_trio_refund,
                "r_pop1~3_복조_4~6_삼복_적중": top3_anchor_4_6_trio_hit_flag,
                "r_pop1~3_복조_4~6_삼복_환수액": top3_anchor_4_6_trio_refund,
                "r_pop1~3_복조_4~6_삼쌍_적중": top3_anchor_4_6_trifecta_hit_flag,
                "r_pop1~3_복조_4~6_삼쌍_환수액": top3_anchor_4_6_trifecta_refund,
                "1축_2~4_5~7_베팅액": (
                    anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
                ),
                "1축_2~4_5~7_환수액": anchor1_24_57_refund,
                "1축_2~4_베팅액": (
                    anchor1_24_bet_per_race if anchor1_24_valid else 0.0
                ),
                "1축_2~4_환수액": anchor1_24_refund,
                "1축_2~4_삼복_베팅액": (
                    anchor1_24_trio_bet_per_race if anchor1_24_trio_valid else 0.0
                ),
                "1축_2~4_삼복_환수액": anchor1_24_trio_refund,
                "BOX4_삼복_베팅액": box4_trio_bet_per_race,
                "BOX4_삼복_환수액": box4_trio_refund,
                "1~3복조_4~8_삼복_베팅액": (
                    top3_anchor_4_8_trio_bet_per_race
                    if top3_anchor_4_8_trio_valid
                    else 0.0
                ),
                "1~3복조_4~8_삼복_환수액": top3_anchor_4_8_trio_refund,
                "1~3복조_4~7_삼복_베팅액": (
                    top3_anchor_4_7_trio_bet_per_race
                    if top3_anchor_4_7_trio_valid
                    else 0.0
                ),
                "1~3복조_4~7_삼복_환수액": top3_anchor_4_7_trio_refund,
                "1축_2~5_삼복_베팅액": (
                    anchor1_25_trio_bet_per_race if anchor1_25_trio_valid else 0.0
                ),
                "1축_2~5_삼복_환수액": anchor1_25_trio_refund,
                "1축_2~6_삼복_베팅액": (
                    anchor1_26_trio_bet_per_race if anchor1_26_trio_valid else 0.0
                ),
                "1축_2~6_삼복_환수액": anchor1_26_trio_refund,
                "1~2복조_3~6_삼복_베팅액": (
                    anchor12_36_trio_bet_per_race
                    if anchor12_36_trio_valid
                    else 0.0
                ),
                "1~2복조_3~6_삼복_환수액": anchor12_36_trio_refund,
                "1~3복조_4~6_삼복_베팅액": (
                    top3_anchor_4_6_trio_bet_per_race
                    if top3_anchor_4_6_trio_valid
                    else 0.0
                ),
                "1~3복조_4~6_삼복_환수액": top3_anchor_4_6_trio_refund,
                "1~3복조_4~6_삼쌍_베팅액": (
                    top3_anchor_4_6_trifecta_bet_per_race
                    if top3_anchor_4_6_trifecta_valid
                    else 0.0
                ),
                "1~3복조_4~6_삼쌍_환수액": top3_anchor_4_6_trifecta_refund,
                "총구멍수": holes_per_race,
                "총베팅액": (
                    (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
                    + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
                    + (anchor1_24_trio_bet_per_race if anchor1_24_trio_valid else 0.0)
                    + box4_trio_bet_per_race
                    + (
                        top3_anchor_4_8_trio_bet_per_race
                        if top3_anchor_4_8_trio_valid
                        else 0.0
                    )
                    + (
                        top3_anchor_4_7_trio_bet_per_race
                        if top3_anchor_4_7_trio_valid
                        else 0.0
                    )
                    + (
                        anchor1_25_trio_bet_per_race
                        if anchor1_25_trio_valid
                        else 0.0
                    )
                    + (
                        anchor1_26_trio_bet_per_race
                        if anchor1_26_trio_valid
                        else 0.0
                    )
                    + (
                        anchor12_36_trio_bet_per_race
                        if anchor12_36_trio_valid
                        else 0.0
                    )
                    + (
                        top3_anchor_4_6_trio_bet_per_race
                        if top3_anchor_4_6_trio_valid
                        else 0.0
                    )
                    + (
                        top3_anchor_4_6_trifecta_bet_per_race
                        if top3_anchor_4_6_trifecta_valid
                        else 0.0
                    )
                ),
                "총환수액": anchor1_24_57_refund
                + anchor1_24_refund
                + anchor1_24_trio_refund
                + box4_trio_refund
                + top3_anchor_4_8_trio_refund
                + top3_anchor_4_7_trio_refund
                + anchor1_25_trio_refund
                + anchor1_26_trio_refund
                + anchor12_36_trio_refund
                + top3_anchor_4_6_trio_refund
                + top3_anchor_4_6_trifecta_refund,
                "삼쌍승식배당율": odds,
                "삼복승식배당율": odds_trio,
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
        "anchor1_24_trio_total_bet": anchor1_24_trio_total_bet,
        "anchor1_24_trio_total_refund": anchor1_24_trio_total_refund,
        "anchor1_24_trio_refund_rate": (
            anchor1_24_trio_total_refund / anchor1_24_trio_total_bet
            if anchor1_24_trio_total_bet > 0
            else 0.0
        ),
        "anchor1_24_trio_hit_rate": (
            anchor1_24_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "box4_trio_total_bet": box4_trio_total_bet,
        "box4_trio_total_refund": box4_trio_total_refund,
        "box4_trio_refund_rate": (
            box4_trio_total_refund / box4_trio_total_bet
            if box4_trio_total_bet > 0
            else 0.0
        ),
        "box4_trio_hit_rate": (
            box4_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top3_anchor_4_8_trio_total_bet": top3_anchor_4_8_trio_total_bet,
        "top3_anchor_4_8_trio_total_refund": top3_anchor_4_8_trio_total_refund,
        "top3_anchor_4_8_trio_refund_rate": (
            top3_anchor_4_8_trio_total_refund / top3_anchor_4_8_trio_total_bet
            if top3_anchor_4_8_trio_total_bet > 0
            else 0.0
        ),
        "top3_anchor_4_8_trio_hit_rate": (
            top3_anchor_4_8_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top3_anchor_4_7_trio_total_bet": top3_anchor_4_7_trio_total_bet,
        "top3_anchor_4_7_trio_total_refund": top3_anchor_4_7_trio_total_refund,
        "top3_anchor_4_7_trio_refund_rate": (
            top3_anchor_4_7_trio_total_refund / top3_anchor_4_7_trio_total_bet
            if top3_anchor_4_7_trio_total_bet > 0
            else 0.0
        ),
        "top3_anchor_4_7_trio_hit_rate": (
            top3_anchor_4_7_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_25_trio_total_bet": anchor1_25_trio_total_bet,
        "anchor1_25_trio_total_refund": anchor1_25_trio_total_refund,
        "anchor1_25_trio_refund_rate": (
            anchor1_25_trio_total_refund / anchor1_25_trio_total_bet
            if anchor1_25_trio_total_bet > 0
            else 0.0
        ),
        "anchor1_25_trio_hit_rate": (
            anchor1_25_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor1_26_trio_total_bet": anchor1_26_trio_total_bet,
        "anchor1_26_trio_total_refund": anchor1_26_trio_total_refund,
        "anchor1_26_trio_refund_rate": (
            anchor1_26_trio_total_refund / anchor1_26_trio_total_bet
            if anchor1_26_trio_total_bet > 0
            else 0.0
        ),
        "anchor1_26_trio_hit_rate": (
            anchor1_26_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "anchor12_36_trio_total_bet": anchor12_36_trio_total_bet,
        "anchor12_36_trio_total_refund": anchor12_36_trio_total_refund,
        "anchor12_36_trio_refund_rate": (
            anchor12_36_trio_total_refund / anchor12_36_trio_total_bet
            if anchor12_36_trio_total_bet > 0
            else 0.0
        ),
        "anchor12_36_trio_hit_rate": (
            anchor12_36_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top3_anchor_4_6_trio_total_bet": top3_anchor_4_6_trio_total_bet,
        "top3_anchor_4_6_trio_total_refund": top3_anchor_4_6_trio_total_refund,
        "top3_anchor_4_6_trio_refund_rate": (
            top3_anchor_4_6_trio_total_refund / top3_anchor_4_6_trio_total_bet
            if top3_anchor_4_6_trio_total_bet > 0
            else 0.0
        ),
        "top3_anchor_4_6_trio_hit_rate": (
            top3_anchor_4_6_trio_total_hits / total_races if total_races > 0 else 0.0
        ),
        "top3_anchor_4_6_trifecta_total_bet": top3_anchor_4_6_trifecta_total_bet,
        "top3_anchor_4_6_trifecta_total_refund": top3_anchor_4_6_trifecta_total_refund,
        "top3_anchor_4_6_trifecta_refund_rate": (
            top3_anchor_4_6_trifecta_total_refund
            / top3_anchor_4_6_trifecta_total_bet
            if top3_anchor_4_6_trifecta_total_bet > 0
            else 0.0
        ),
        "top3_anchor_4_6_trifecta_hit_rate": (
            top3_anchor_4_6_trifecta_total_hits / total_races
            if total_races > 0
            else 0.0
        ),
    }
    total_bet_all = (
        anchor1_24_57_total_bet
        + anchor1_24_total_bet
        + anchor1_24_trio_total_bet
        + box4_trio_total_bet
        + top3_anchor_4_8_trio_total_bet
        + top3_anchor_4_7_trio_total_bet
        + anchor1_25_trio_total_bet
        + anchor1_26_trio_total_bet
        + anchor12_36_trio_total_bet
        + top3_anchor_4_6_trio_total_bet
        + top3_anchor_4_6_trifecta_total_bet
    )
    total_refund_all = (
        anchor1_24_57_total_refund
        + anchor1_24_total_refund
        + anchor1_24_trio_total_refund
        + box4_trio_total_refund
        + top3_anchor_4_8_trio_total_refund
        + top3_anchor_4_7_trio_total_refund
        + anchor1_25_trio_total_refund
        + anchor1_26_trio_total_refund
        + anchor12_36_trio_total_refund
        + top3_anchor_4_6_trio_total_refund
        + top3_anchor_4_6_trifecta_total_refund
    )
    total_refund_rate_all = (
        total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
    )
    total_hit_rate_all = total_hits_any / total_races if total_races > 0 else 0.0
    avg_holes_per_race = total_holes_all / total_races if total_races > 0 else 0.0
    avg_bet_per_race = total_bet_all / total_races if total_races > 0 else 0.0
    total_profit_all = total_refund_all - total_bet_all
    anchor1_24_57_profit = anchor1_24_57_total_refund - anchor1_24_57_total_bet
    anchor1_24_profit = anchor1_24_total_refund - anchor1_24_total_bet
    anchor1_24_trio_profit = anchor1_24_trio_total_refund - anchor1_24_trio_total_bet
    box4_trio_profit = box4_trio_total_refund - box4_trio_total_bet
    top3_anchor_4_8_trio_profit = (
        top3_anchor_4_8_trio_total_refund - top3_anchor_4_8_trio_total_bet
    )
    top3_anchor_4_7_trio_profit = (
        top3_anchor_4_7_trio_total_refund - top3_anchor_4_7_trio_total_bet
    )
    anchor1_25_trio_profit = (
        anchor1_25_trio_total_refund - anchor1_25_trio_total_bet
    )
    anchor1_26_trio_profit = (
        anchor1_26_trio_total_refund - anchor1_26_trio_total_bet
    )
    anchor12_36_trio_profit = (
        anchor12_36_trio_total_refund - anchor12_36_trio_total_bet
    )
    top3_anchor_4_6_trio_profit = (
        top3_anchor_4_6_trio_total_refund - top3_anchor_4_6_trio_total_bet
    )
    top3_anchor_4_6_trifecta_profit = (
        top3_anchor_4_6_trifecta_total_refund - top3_anchor_4_6_trifecta_total_bet
    )

    print("===================================")
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
    print(
        "[r_pop 1축(2~4) 2등/5~7 3등 삼쌍승식]  "
        f"적중율: {summary['anchor1_24_57_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_24_57_total_bet):,}원  "
        f"총환수액: {anchor1_24_57_total_refund:,.1f}원  "
        f"이익금액: {anchor1_24_57_profit:,.1f}원  "
        f"환수율: {summary['anchor1_24_57_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1축(2~4) 3복조 삼쌍승식]  "
        f"적중율: {summary['anchor1_24_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_24_total_bet):,}원  "
        f"총환수액: {anchor1_24_total_refund:,.1f}원  "
        f"이익금액: {anchor1_24_profit:,.1f}원  "
        f"환수율: {summary['anchor1_24_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1축(2~4) 삼복승식]  "
        f"적중율: {summary['anchor1_24_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_24_trio_total_bet):,}원  "
        f"총환수액: {anchor1_24_trio_total_refund:,.1f}원  "
        f"이익금액: {anchor1_24_trio_profit:,.1f}원  "
        f"환수율: {summary['anchor1_24_trio_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1~4 BOX4 삼복승식]  "
        f"적중율: {summary['box4_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(box4_trio_total_bet):,}원  "
        f"총환수액: {box4_trio_total_refund:,.1f}원  "
        f"이익금액: {box4_trio_profit:,.1f}원  "
        f"환수율: {summary['box4_trio_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1~3 복조 + 4~8 삼복승식]  "
        f"적중율: {summary['top3_anchor_4_8_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(top3_anchor_4_8_trio_total_bet):,}원  "
        f"총환수액: {top3_anchor_4_8_trio_total_refund:,.1f}원  "
        f"이익금액: {top3_anchor_4_8_trio_profit:,.1f}원  "
        f"환수율: {summary['top3_anchor_4_8_trio_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1~3 복조 + 4~7 삼복승식]  "
        f"적중율: {summary['top3_anchor_4_7_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(top3_anchor_4_7_trio_total_bet):,}원  "
        f"총환수액: {top3_anchor_4_7_trio_total_refund:,.1f}원  "
        f"이익금액: {top3_anchor_4_7_trio_profit:,.1f}원  "
        f"환수율: {summary['top3_anchor_4_7_trio_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1축(2~5) 삼복승식]  "
        f"적중율: {summary['anchor1_25_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_25_trio_total_bet):,}원  "
        f"총환수액: {anchor1_25_trio_total_refund:,.1f}원  "
        f"이익금액: {anchor1_25_trio_profit:,.1f}원  "
        f"환수율: {summary['anchor1_25_trio_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1축(2~6) 삼복승식]  "
        f"적중율: {summary['anchor1_26_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_26_trio_total_bet):,}원  "
        f"총환수액: {anchor1_26_trio_total_refund:,.1f}원  "
        f"이익금액: {anchor1_26_trio_profit:,.1f}원  "
        f"환수율: {summary['anchor1_26_trio_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1~2 복조 + 3~6 삼복승식]  "
        f"적중율: {summary['anchor12_36_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor12_36_trio_total_bet):,}원  "
        f"총환수액: {anchor12_36_trio_total_refund:,.1f}원  "
        f"이익금액: {anchor12_36_trio_profit:,.1f}원  "
        f"환수율: {summary['anchor12_36_trio_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1~3 복조 + 4~6 삼복승식]  "
        f"적중율: {summary['top3_anchor_4_6_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(top3_anchor_4_6_trio_total_bet):,}원  "
        f"총환수액: {top3_anchor_4_6_trio_total_refund:,.1f}원  "
        f"이익금액: {top3_anchor_4_6_trio_profit:,.1f}원  "
        f"환수율: {summary['top3_anchor_4_6_trio_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1~3 복조 + 4~6 삼쌍승식]  "
        f"적중율: {summary['top3_anchor_4_6_trifecta_hit_rate']:.3f}  "
        f"총베팅액: {int(top3_anchor_4_6_trifecta_total_bet):,}원  "
        f"총환수액: {top3_anchor_4_6_trifecta_total_refund:,.1f}원  "
        f"이익금액: {top3_anchor_4_6_trifecta_profit:,.1f}원  "
        f"환수율: {summary['top3_anchor_4_6_trifecta_refund_rate']:.3f}"
    )
    for week in sorted(week_summary.keys()):
        d = week_summary[week]
        day_refund_rate = (
            d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
        )
        day_hit_rate = d["hits"] / d["races"] if d["races"] > 0 else 0.0
        day_profit = d["total_refund"] - d["total_bet"]
        print(
            f"[토요일기준 {week}]  경주수: {d['races']}  "
            f"총베팅액: {int(d['total_bet']):,}원  총환수액: {d['total_refund']:,.1f}원  "
            f"이익금액: {day_profit:,.1f}원  "
            f"환수율: {day_refund_rate:.3f}  적중경주수: {d['hits']}  적중율: {day_hit_rate:.3f}"
        )
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
    for ym in sorted(month_summary_anchor1_24_trio.keys()):
        m = month_summary_anchor1_24_trio[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(1축2~4 삼복) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_summary_box4_trio.keys()):
        m = month_summary_box4_trio[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(BOX4 삼복승식) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_summary_top3_anchor_4_8_trio.keys()):
        m = month_summary_top3_anchor_4_8_trio[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(1~3복조+4~8 삼복) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_summary_top3_anchor_4_7_trio.keys()):
        m = month_summary_top3_anchor_4_7_trio[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(1~3복조+4~7 삼복) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_summary_anchor1_25_trio.keys()):
        m = month_summary_anchor1_25_trio[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(1축2~5 삼복) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_summary_anchor1_26_trio.keys()):
        m = month_summary_anchor1_26_trio[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(1축2~6 삼복) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_summary_anchor12_36_trio.keys()):
        m = month_summary_anchor12_36_trio[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(1~2복조+3~6 삼복) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_summary_top3_anchor_4_6_trio.keys()):
        m = month_summary_top3_anchor_4_6_trio[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(1~3복조+4~6 삼복) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_summary_top3_anchor_4_6_trifecta.keys()):
        m = month_summary_top3_anchor_4_6_trifecta[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(1~3복조+4~6 삼쌍) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"이익금액: {month_profit:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    week_rows = []
    for week in sorted(week_summary.keys()):
        d = week_summary[week]
        day_refund_rate = (
            d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
        )
        day_hit_rate = d["hits"] / d["races"] if d["races"] > 0 else 0.0
        day_profit = d["total_refund"] - d["total_bet"]
        week_rows.append(
            {
                "토요일기준일": week,
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

    to_date = "20260209"

    race_df, summary = calc_rpop_anchor_26_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,
    )

    out_path = "/Users/Super007/Documents/r_pop_total.csv"
    if not race_df.empty:
        race_df = race_df.drop_duplicates(subset=["경마장", "경주일", "경주번호"])
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
