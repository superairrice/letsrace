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

    df["삼쌍승식배당율"] = pd.to_numeric(df["삼쌍승식배당율"], errors="coerce").fillna(0.0)
    # 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    anchor1_24_57_bet_unit = 100
    anchor1_24_57_bet_per_race = 9 * anchor1_24_57_bet_unit  # 3 * 3
    anchor1_57_24_bet_unit = 100
    anchor1_57_24_bet_per_race = 9 * anchor1_57_24_bet_unit  # 3 * 3
    anchor1_24_bet_unit = 100
    anchor1_24_bet_per_race = 6 * anchor1_24_bet_unit  # 3P2
    anchor1_26_trifecta_bet_unit = 100
    anchor1_26_trifecta_bet_per_race = 20 * anchor1_26_trifecta_bet_unit  # 5P2
    total_races = 0
    excluded_races = 0
    anchor1_24_57_total_bet = 0.0
    anchor1_24_57_total_refund = 0.0
    anchor1_24_57_total_hits = 0
    anchor1_57_24_total_bet = 0.0
    anchor1_57_24_total_refund = 0.0
    anchor1_57_24_total_hits = 0
    anchor1_24_total_bet = 0.0
    anchor1_24_total_refund = 0.0
    anchor1_24_total_hits = 0
    anchor1_26_trifecta_total_bet = 0.0
    anchor1_26_trifecta_total_refund = 0.0
    anchor1_26_trifecta_total_hits = 0
    total_hits_any = 0
    total_holes_all = 0
    week_summary = {}
    week_track_summary = {}
    month_summary = {}
    track_summary = {}
    track_month_summary = {}
    month_summary_rpop5_7_anchor_1_4_trio = {}
    month_summary_anchor_24_57 = {}
    month_summary_anchor_24 = {}
    month_summary_anchor1_26_trifecta = {}
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
        anchor2_gate = g_sorted.iloc[1]["마번"] if len(g_sorted) >= 2 else None
        top2_4 = g_sorted.iloc[1:4]["마번"].tolist()
        top5_7 = g_sorted.iloc[4:7]["마번"].tolist()
        top2_4_set = set(top2_4)
        top5_7_set = set(top5_7)
        top1_2 = g_sorted.iloc[0:2]["마번"].tolist()
        top1_2_set = set(top1_2)
        top2_6 = g_sorted.iloc[1:6]["마번"].tolist()
        top2_6_set = set(top2_6)
        top3_8 = g_sorted.iloc[2:8]["마번"].tolist()
        top3_8_set = set(top3_8)
        top3_12 = g_sorted.iloc[2:12]["마번"].tolist()
        top3_12_set = set(top3_12)

        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()
        actual_set = set(actual_top3)
        odds = float(g["삼쌍승식배당율"].iloc[0])
        if apply_odds_filter and odds >= 1000:
            excluded_races += 1
            continue

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
        anchor1_26_trifecta_valid = anchor_gate is not None and len(top2_6) == 5
        anchor1_26_trifecta_hit_flag = int(
            anchor1_26_trifecta_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_6_set
            and actual_top3[2] in top2_6_set
            and actual_top3[1] != actual_top3[2]
        )
        anchor1_26_trifecta_refund = (
            odds * anchor1_26_trifecta_bet_unit
            if anchor1_26_trifecta_hit_flag == 1
            else 0.0
        )
        hit_any = int(
            anchor1_24_57_hit_flag
            or anchor1_57_24_hit_flag
            or anchor1_24_hit_flag
            or anchor1_26_trifecta_hit_flag
        )
        anchor1_24_57_total_bet += (
            anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
        )
        anchor1_24_57_total_refund += anchor1_24_57_refund
        anchor1_24_57_total_hits += anchor1_24_57_hit_flag
        anchor1_57_24_total_bet += (
            anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0
        )
        anchor1_57_24_total_refund += anchor1_57_24_refund
        anchor1_57_24_total_hits += anchor1_57_24_hit_flag
        anchor1_24_total_bet += anchor1_24_bet_per_race if anchor1_24_valid else 0.0
        anchor1_24_total_refund += anchor1_24_refund
        anchor1_24_total_hits += anchor1_24_hit_flag
        anchor1_26_trifecta_total_bet += (
            anchor1_26_trifecta_bet_per_race if anchor1_26_trifecta_valid else 0.0
        )
        anchor1_26_trifecta_total_refund += anchor1_26_trifecta_refund
        anchor1_26_trifecta_total_hits += anchor1_26_trifecta_hit_flag
        total_hits_any += hit_any

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
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (
                anchor1_26_trifecta_bet_per_race
                if anchor1_26_trifecta_valid
                else 0.0
            )
        )
        track_summary[track]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_57_24_refund
            + anchor1_24_refund
            + anchor1_26_trifecta_refund
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
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (
                anchor1_26_trifecta_bet_per_race
                if anchor1_26_trifecta_valid
                else 0.0
            )
        )
        track_month_summary[track_month_key]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_57_24_refund
            + anchor1_24_refund
            + anchor1_26_trifecta_refund
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
        if year_month not in month_summary_anchor1_26_trifecta:
            month_summary_anchor1_26_trifecta[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_summary[year_month]["races"] += 1
        week_summary[week_key]["races"] += 1
        month_summary[year_month]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (
                anchor1_26_trifecta_bet_per_race
                if anchor1_26_trifecta_valid
                else 0.0
            )
        )
        week_summary[week_key]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (
                anchor1_26_trifecta_bet_per_race
                if anchor1_26_trifecta_valid
                else 0.0
            )
        )
        month_summary[year_month]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_57_24_refund
            + anchor1_24_refund
            + anchor1_26_trifecta_refund
        )
        week_summary[week_key]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_57_24_refund
            + anchor1_24_refund
            + anchor1_26_trifecta_refund
        )
        month_summary[year_month]["hits"] += hit_any
        week_summary[week_key]["hits"] += hit_any
        week_track_summary[week_track_key]["races"] += 1
        week_track_summary[week_track_key]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (
                anchor1_26_trifecta_bet_per_race
                if anchor1_26_trifecta_valid
                else 0.0
            )
        )
        week_track_summary[week_track_key]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_57_24_refund
            + anchor1_24_refund
            + anchor1_26_trifecta_refund
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
        month_summary_anchor_24[year_month]["races"] += 1
        month_summary_anchor_24[year_month]["total_bet"] += (
            anchor1_24_bet_per_race if anchor1_24_valid else 0.0
        )
        month_summary_anchor_24[year_month]["total_refund"] += anchor1_24_refund
        month_summary_anchor_24[year_month]["hits"] += anchor1_24_hit_flag
        month_summary_anchor1_26_trifecta[year_month]["races"] += 1
        month_summary_anchor1_26_trifecta[year_month]["total_bet"] += (
            anchor1_26_trifecta_bet_per_race if anchor1_26_trifecta_valid else 0.0
        )
        month_summary_anchor1_26_trifecta[year_month]["total_refund"] += (
            anchor1_26_trifecta_refund
        )
        month_summary_anchor1_26_trifecta[year_month]["hits"] += (
            anchor1_26_trifecta_hit_flag
        )
        holes_per_race = (
            (9 if anchor1_24_57_valid else 0)
            + (9 if anchor1_57_24_valid else 0)
            + (6 if anchor1_24_valid else 0)
            + (20 if anchor1_26_trifecta_valid else 0)
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
                "r_pop1_축_5~7_2~4_적중": anchor1_57_24_hit_flag,
                "r_pop1_축_5~7_2~4_환수액": anchor1_57_24_refund,
                "r_pop1_축_2~4_적중": anchor1_24_hit_flag,
                "r_pop1_축_2~4_환수액": anchor1_24_refund,
                "1축_2~4_5~7_베팅액": (
                    anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
                ),
                "1축_2~4_5~7_환수액": anchor1_24_57_refund,
                "1축_5~7_2~4_베팅액": (
                    anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0
                ),
                "1축_5~7_2~4_환수액": anchor1_57_24_refund,
                "1축_2~4_베팅액": (
                    anchor1_24_bet_per_race if anchor1_24_valid else 0.0
                ),
                "1축_2~4_환수액": anchor1_24_refund,
                "1축_2~6_삼쌍_적중": anchor1_26_trifecta_hit_flag,
                "1축_2~6_삼쌍_베팅액": (
                    anchor1_26_trifecta_bet_per_race
                    if anchor1_26_trifecta_valid
                    else 0.0
                ),
                "1축_2~6_삼쌍_환수액": anchor1_26_trifecta_refund,
                "r_pop1_축_2~6_5복조_삼쌍_적중": anchor1_26_trifecta_hit_flag,
                "r_pop1_축_2~6_5복조_삼쌍_베팅액": (
                    anchor1_26_trifecta_bet_per_race
                    if anchor1_26_trifecta_valid
                    else 0.0
                ),
                "r_pop1_축_2~6_5복조_삼쌍_환수액": anchor1_26_trifecta_refund,
                "총구멍수": holes_per_race,
                "총베팅액": (
                    (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
                    + (anchor1_57_24_bet_per_race if anchor1_57_24_valid else 0.0)
                    + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
                    + (
                        anchor1_26_trifecta_bet_per_race
                        if anchor1_26_trifecta_valid
                        else 0.0
                    )
                ),
                "총환수액": anchor1_24_57_refund
                + anchor1_57_24_refund
                + anchor1_24_refund
                + anchor1_26_trifecta_refund,
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
        "anchor1_26_trifecta_total_bet": anchor1_26_trifecta_total_bet,
        "anchor1_26_trifecta_total_refund": anchor1_26_trifecta_total_refund,
        "anchor1_26_trifecta_refund_rate": (
            anchor1_26_trifecta_total_refund / anchor1_26_trifecta_total_bet
            if anchor1_26_trifecta_total_bet > 0
            else 0.0
        ),
        "anchor1_26_trifecta_hit_rate": (
            anchor1_26_trifecta_total_hits / total_races if total_races > 0 else 0.0
        ),
    }
    total_bet_all = (
        anchor1_24_57_total_bet
        + anchor1_57_24_total_bet
        + anchor1_24_total_bet
        + anchor1_26_trifecta_total_bet
    )
    total_refund_all = (
        anchor1_24_57_total_refund
        + anchor1_57_24_total_refund
        + anchor1_24_total_refund
        + anchor1_26_trifecta_total_refund
    )
    total_refund_rate_all = (
        total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
    )
    total_hit_rate_all = total_hits_any / total_races if total_races > 0 else 0.0
    avg_holes_per_race = total_holes_all / total_races if total_races > 0 else 0.0
    avg_bet_per_race = total_bet_all / total_races if total_races > 0 else 0.0
    total_profit_all = total_refund_all - total_bet_all
    anchor1_24_57_profit = anchor1_24_57_total_refund - anchor1_24_57_total_bet
    anchor1_57_24_profit = anchor1_57_24_total_refund - anchor1_57_24_total_bet
    anchor1_24_profit = anchor1_24_total_refund - anchor1_24_total_bet
    anchor1_26_trifecta_profit = (
        anchor1_26_trifecta_total_refund - anchor1_26_trifecta_total_bet
    )
    summary["total_bet_all"] = total_bet_all
    summary["total_refund_all"] = total_refund_all
    summary["total_profit_all"] = total_profit_all
    summary["total_refund_rate_all"] = total_refund_rate_all
    summary["total_hit_rate_all"] = total_hit_rate_all
    summary["track_summary"] = track_summary
    summary["track_month_summary"] = track_month_summary

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
    print(
        "[r_pop 1축(2~4) 2등/5~7 3등 삼쌍승식]  "
        f"적중율: {summary['anchor1_24_57_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_24_57_total_bet):,}원  "
        f"총환수액: {anchor1_24_57_total_refund:,.1f}원  "
        f"이익금액: {anchor1_24_57_profit:,.1f}원  "
        f"환수율: {summary['anchor1_24_57_refund_rate']:.3f}"
    )
    print(
        "[r_pop 1축(5~7) 2등/2~4 3등 삼쌍승식]  "
        f"적중율: {summary['anchor1_57_24_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_57_24_total_bet):,}원  "
        f"총환수액: {anchor1_57_24_total_refund:,.1f}원  "
        f"이익금액: {anchor1_57_24_profit:,.1f}원  "
        f"환수율: {summary['anchor1_57_24_refund_rate']:.3f}"
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
        "[r_pop 1축 2~6 삼쌍승식]  "
        f"적중율: {summary['anchor1_26_trifecta_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_26_trifecta_total_bet):,}원  "
        f"총환수액: {anchor1_26_trifecta_total_refund:,.1f}원  "
        f"이익금액: {anchor1_26_trifecta_profit:,.1f}원  "
        f"환수율: {summary['anchor1_26_trifecta_refund_rate']:.3f}"
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
    for ym in sorted(month_summary_anchor1_26_trifecta.keys()):
        m = month_summary_anchor1_26_trifecta[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        month_profit = m["total_refund"] - m["total_bet"]
        print(
            f"[월별(r_pop1축 2~6 5복조 삼쌍) {ym}]  경주수: {m['races']}  "
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
    to_date = "20260312"
    





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
