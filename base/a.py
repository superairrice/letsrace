import pymysql
import pandas as pd
from contextlib import closing
from typing import List, Optional


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
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}


def get_conn():
    """단순 MySQL 커넥션 생성."""
    conn = pymysql.connect(**DB_CONF)
    try:
        conn.ping(reconnect=True)
    except Exception:
        pass
    return conn


# =========================
# 1. 기간별 결과 데이터 로드
# =========================
def load_result_data_from_db(
    conn,
    from_date: str,
    to_date: str,
) -> pd.DataFrame:
    """
    기간(from_date ~ to_date) 동안의 결과 데이터 로드.
    r_pop(예상), r_rank(실제순위), 삼쌍승식 배당 포함.
    """
    sql = """
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
        e.tot_score  AS tot_score,  -- 종합점수
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
    WHERE e.rdate >= %s
      AND e.rdate <= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    return pd.read_sql(sql, conn, params=[from_date, to_date])


# =========================
# 2. r_pop 1축(2~4) 2등/5~7 3등 삼쌍승식
#    + r_pop 1축(2~6) 5복조 삼쌍승식
#    + r_pop 1~4 BOX4 삼쌍승식 환수 계산
# =========================
def calc_rpop_anchor_26_trifecta(
    from_date: str,
    to_date: str,
    bet_unit: int = 100,
    tot_score_bins: Optional[List[float]] = None,
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
    - 각 경주에 대해 r_pop 1을 1등축으로,
      r_pop 2~4(2등축), r_pop 5~7(3등) 삼쌍승식 베팅.
    - r_pop 1축, r_pop 2~6 5복조 삼쌍승식 베팅.
    - r_pop 1~4 BOX4 삼쌍승식 베팅.
    - 실제 1~3위가 (r_pop1, r_pop2~4, r_pop5~7) 순서로 맞으면 적중.
    - 5복조는 r_pop1 고정, r_pop2~6 중 2/3착 조합이 순서대로 맞으면 적중.
    - BOX4는 실제 1~3위가 r_pop 1~4 안에 있으면 적중.
    - 환수금/환수율 집계.
    """
    with closing(get_conn()) as conn:
        df = load_result_data_from_db(conn, from_date=from_date, to_date=to_date)

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
    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)
    df["연월"] = df["경주일"].str.slice(0, 6)
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")

    for col in ["rank", "r_pop", "r_rank"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["tot_score"] = pd.to_numeric(df["tot_score"], errors="coerce")
    before_rows = len(df)
    df = df.dropna(subset=["rank", "r_pop", "r_rank", "tot_score"]).copy()
    dropped = before_rows - len(df)
    if dropped:
        print(f"⚠️ rank/r_pop/r_rank NaN {dropped}건 제외")
    for col in ["rank", "r_pop", "r_rank"]:
        df[col] = df[col].astype(int)
    df["r_pop"] = df["r_pop"].where(df["r_pop"] != 0, 99)

    df["삼쌍승식배당율"] = pd.to_numeric(
        df["삼쌍승식배당율"], errors="coerce"
    ).fillna(0.0)
    df["삼복승식배당율"] = pd.to_numeric(
        df["삼복승식배당율"], errors="coerce"
    ).fillna(0.0)
    # 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)
    if tot_score_bins is None:
        tot_score_bins = [float("-inf"), 60, 65, 70, 75, 80, 85, 90, 95, float("inf")]

    anchor1_24_57_bet_unit = bet_unit
    anchor1_24_57_bet_per_race = 9 * anchor1_24_57_bet_unit  # 3 * 3
    anchor1_26_tri_bet_unit = bet_unit
    anchor1_26_tri_bet_per_race = 20 * anchor1_26_tri_bet_unit  # 5P2
    box4_tri_bet_unit = bet_unit
    box4_tri_bet_per_race = 24 * box4_tri_bet_unit  # 4P3
    anchor2_137_trio_bet_unit = bet_unit
    anchor2_137_trio_bet_per_race = 15 * anchor2_137_trio_bet_unit  # C(6,2)
    total_races = 0
    excluded_races = 0
    anchor1_24_57_total_bet = 0.0
    anchor1_24_57_total_refund = 0.0
    anchor1_24_57_total_hits = 0
    anchor1_26_tri_total_bet = 0.0
    anchor1_26_tri_total_refund = 0.0
    anchor1_26_tri_total_hits = 0
    box4_tri_total_bet = 0.0
    box4_tri_total_refund = 0.0
    box4_tri_total_hits = 0
    total_hits_any = 0
    month_summary = {}
    month_summary_anchor_24_57 = {}
    month_summary_anchor_26_tri = {}
    month_summary_anchor2_137_trio = {}
    month_summary_box4_tri = {}
    daily_summary = {}
    monthly_summary = {}
    race_rows = []

    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()
        if len(g) >= 13:
            excluded_races += 1
            continue
        new_cnt = int(g["신마"].sum())
        if new_cnt >= 2:
            excluded_races += 1
            continue
        total_races += 1
        year_month = str(date)[:6]
        distance = g["경주거리"].iloc[0]
        grade = g["등급"].iloc[0]

        g_sorted = g.sort_values("r_pop", ascending=True)
        top4 = g_sorted.head(4)["마번"].tolist()
        anchor_gate = top4[0] if top4 else None
        anchor2_gate = top4[1] if len(top4) > 1 else None
        top2_4 = g_sorted.iloc[1:4]["마번"].tolist()
        top5_7 = g_sorted.iloc[4:7]["마번"].tolist()
        top3_7 = g_sorted.iloc[2:7]["마번"].tolist()
        top2_6 = g_sorted.iloc[1:6]["마번"].tolist()
        top2_4_set = set(top2_4)
        top5_7_set = set(top5_7)
        top3_7_set = set(top3_7)
        top2_6_set = set(top2_6)

        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()
        odds = float(g["삼쌍승식배당율"].iloc[0])
        odds_trio = float(g["삼복승식배당율"].iloc[0])

        anchor_tot_score = None
        if anchor_gate is not None:
            anchor_score_series = g.loc[g["마번"] == anchor_gate, "tot_score"]
            if not anchor_score_series.empty:
                anchor_tot_score = float(anchor_score_series.iloc[0])
        bet_allowed = True
        anchor1_24_57_valid = (
            bet_allowed
            and anchor_gate is not None
            and len(top2_4) == 3
            and len(top5_7) == 3
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
        anchor1_26_tri_valid = bet_allowed and anchor_gate is not None and len(top2_6) == 5
        anchor1_26_tri_hit_flag = int(
            anchor1_26_tri_valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_6_set
            and actual_top3[2] in top2_6_set
            and actual_top3[1] != actual_top3[2]
        )
        anchor1_26_tri_refund = (
            odds * anchor1_26_tri_bet_unit if anchor1_26_tri_hit_flag == 1 else 0.0
        )
        anchor2_137_trio_valid = (
            anchor2_gate is not None and anchor_gate is not None and len(top3_7) == 5
        )
        anchor2_137_trio_hit_flag = 0
        if (
            anchor2_137_trio_valid
            and len(actual_top3) == 3
            and anchor2_gate in actual_top3
        ):
            others = [x for x in actual_top3 if x != anchor2_gate]
            combo_set = set(top3_7_set)
            combo_set.add(anchor_gate)
            if len(others) == 2 and len(set(others)) == 2 and set(others).issubset(
                combo_set
            ):
                anchor2_137_trio_hit_flag = 1
        anchor2_137_trio_refund = (
            odds_trio * anchor2_137_trio_bet_unit
            if anchor2_137_trio_hit_flag == 1
            else 0.0
        )
        actual_set = set(actual_top3)
        r_pop1_top1_hit = int(len(actual_top3) >= 1 and actual_top3[0] == anchor_gate)
        r_pop1_top3_hit = int(anchor_gate is not None and anchor_gate in actual_set)
        box4_tri_hit_flag = int(len(actual_set) == 3 and actual_set.issubset(set(top4)))
        if not bet_allowed:
            box4_tri_hit_flag = 0
        box4_tri_refund = odds * box4_tri_bet_unit if box4_tri_hit_flag == 1 else 0.0
        anchor1_24_57_total_bet += (
            anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
        )
        anchor1_24_57_total_refund += anchor1_24_57_refund
        anchor1_24_57_total_hits += anchor1_24_57_hit_flag
        anchor1_26_tri_total_bet += (
            anchor1_26_tri_bet_per_race if anchor1_26_tri_valid else 0.0
        )
        anchor1_26_tri_total_refund += anchor1_26_tri_refund
        anchor1_26_tri_total_hits += anchor1_26_tri_hit_flag
        box4_tri_bet_per_race_effective = box4_tri_bet_per_race if bet_allowed else 0.0
        box4_tri_total_bet += box4_tri_bet_per_race_effective
        box4_tri_total_refund += box4_tri_refund
        box4_tri_total_hits += box4_tri_hit_flag
        hit_any = int(
            anchor1_24_57_hit_flag or anchor1_26_tri_hit_flag or box4_tri_hit_flag
        )
        total_hits_any += hit_any

        r_pop1_rank_series = g.loc[g["r_pop"] == 1, "r_rank"]
        r_pop1_rank = (
            int(r_pop1_rank_series.iloc[0]) if not r_pop1_rank_series.empty else None
        )
        total_bet_race = (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_26_tri_bet_per_race if anchor1_26_tri_valid else 0.0)
            + (anchor2_137_trio_bet_per_race if anchor2_137_trio_valid else 0.0)
            + box4_tri_bet_per_race_effective
        )
        total_refund_race = (
            anchor1_24_57_refund
            + anchor1_26_tri_refund
            + anchor2_137_trio_refund
            + box4_tri_refund
        )
        if date not in daily_summary:
            daily_summary[date] = {
                "races": 0,
                "r_pop1_top3_hits": 0,
                "r_pop1_rank4_plus": 0,
                "r_pop1_rank4_plus_rpop2_8_win": 0,
                "r_pop1_rank4_plus_races": 0,
                "r_pop1_rank4_plus_rpop2_top3": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
            }
        if year_month not in monthly_summary:
            monthly_summary[year_month] = {
                "races": 0,
                "r_pop1_top3_hits": 0,
                "r_pop1_rank4_plus": 0,
                "r_pop1_rank4_plus_rpop2_8_win": 0,
                "r_pop1_rank4_plus_rpop2_top3": 0,
                "r_pop1_rank4_plus_races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
            }
        daily_summary[date]["races"] += 1
        monthly_summary[year_month]["races"] += 1
        if r_pop1_rank is not None:
            if r_pop1_rank <= 3:
                daily_summary[date]["r_pop1_top3_hits"] += 1
                monthly_summary[year_month]["r_pop1_top3_hits"] += 1
            elif r_pop1_rank >= 4:
                daily_summary[date]["r_pop1_rank4_plus"] += 1
                daily_summary[date]["r_pop1_rank4_plus_races"] += 1
                monthly_summary[year_month]["r_pop1_rank4_plus"] += 1
                monthly_summary[year_month]["r_pop1_rank4_plus_races"] += 1
                winner_r_pop = g.loc[g["r_rank"] == 1, "r_pop"]
                if not winner_r_pop.empty:
                    winner_r_pop_val = int(winner_r_pop.iloc[0])
                    if 2 <= winner_r_pop_val <= 8:
                        daily_summary[date]["r_pop1_rank4_plus_rpop2_8_win"] += 1
                        monthly_summary[year_month]["r_pop1_rank4_plus_rpop2_8_win"] += 1
                r_pop2_rank = g.loc[g["r_pop"] == 2, "r_rank"]
                if not r_pop2_rank.empty and int(r_pop2_rank.iloc[0]) <= 3:
                    daily_summary[date]["r_pop1_rank4_plus_rpop2_top3"] += 1
                    monthly_summary[year_month]["r_pop1_rank4_plus_rpop2_top3"] += 1
        daily_summary[date]["total_bet"] += total_bet_race
        daily_summary[date]["total_refund"] += total_refund_race
        monthly_summary[year_month]["total_bet"] += total_bet_race
        monthly_summary[year_month]["total_refund"] += total_refund_race

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
        if year_month not in month_summary_anchor_26_tri:
            month_summary_anchor_26_tri[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_box4_tri:
            month_summary_box4_tri[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_summary_anchor2_137_trio:
            month_summary_anchor2_137_trio[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_summary[year_month]["races"] += 1
        month_summary[year_month]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_26_tri_bet_per_race if anchor1_26_tri_valid else 0.0)
            + box4_tri_bet_per_race_effective
        )
        month_summary[year_month]["total_refund"] += (
            anchor1_24_57_refund + anchor1_26_tri_refund + box4_tri_refund
        )
        month_summary[year_month]["hits"] += hit_any
        month_summary[year_month]["r_pop1_top1_hits"] += r_pop1_top1_hit
        month_summary[year_month]["r_pop1_top3_hits"] += r_pop1_top3_hit
        month_summary_anchor_24_57[year_month]["races"] += 1
        month_summary_anchor_24_57[year_month]["total_bet"] += (
            anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
        )
        month_summary_anchor_24_57[year_month]["total_refund"] += anchor1_24_57_refund
        month_summary_anchor_24_57[year_month]["hits"] += anchor1_24_57_hit_flag
        month_summary_anchor_26_tri[year_month]["races"] += 1
        month_summary_anchor_26_tri[year_month]["total_bet"] += (
            anchor1_26_tri_bet_per_race if anchor1_26_tri_valid else 0.0
        )
        month_summary_anchor_26_tri[year_month]["total_refund"] += anchor1_26_tri_refund
        month_summary_anchor_26_tri[year_month]["hits"] += anchor1_26_tri_hit_flag
        month_summary_box4_tri[year_month]["races"] += 1
        month_summary_box4_tri[year_month]["total_bet"] += box4_tri_bet_per_race_effective
        month_summary_box4_tri[year_month]["total_refund"] += box4_tri_refund
        month_summary_box4_tri[year_month]["hits"] += box4_tri_hit_flag
        month_summary_anchor2_137_trio[year_month]["races"] += 1
        month_summary_anchor2_137_trio[year_month]["total_bet"] += (
            anchor2_137_trio_bet_per_race if anchor2_137_trio_valid else 0.0
        )
        month_summary_anchor2_137_trio[year_month]["total_refund"] += anchor2_137_trio_refund
        month_summary_anchor2_137_trio[year_month]["hits"] += anchor2_137_trio_hit_flag
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
                "2~6_마번": ",".join(map(str, top2_6)),
                "r_pop_top4_마번": ",".join(map(str, top4)),
                "실제_top3_마번": ",".join(map(str, actual_top3)),
                "r_pop1_축_2~4_5~7_적중": anchor1_24_57_hit_flag,
                "r_pop1_축_2~4_5~7_환수액": anchor1_24_57_refund,
                "r_pop1_축_2~6_5복조_적중": anchor1_26_tri_hit_flag,
                "r_pop1_축_2~6_5복조_환수액": anchor1_26_tri_refund,
                "r_pop2_축_1_3~7_적중": anchor2_137_trio_hit_flag,
                "r_pop2_축_1_3~7_환수액": anchor2_137_trio_refund,
                "r_pop1~4_BOX4_적중": box4_tri_hit_flag,
                "r_pop1~4_BOX4_환수액": box4_tri_refund,
                "1축_2~4_5~7_베팅액": (
                    anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
                ),
                "1축_2~4_5~7_환수액": anchor1_24_57_refund,
                "1축_2~6_5복조_베팅액": (
                    anchor1_26_tri_bet_per_race if anchor1_26_tri_valid else 0.0
                ),
                "1축_2~6_5복조_환수액": anchor1_26_tri_refund,
                "2축_1_3~7_베팅액": (
                    anchor2_137_trio_bet_per_race if anchor2_137_trio_valid else 0.0
                ),
                "2축_1_3~7_환수액": anchor2_137_trio_refund,
                "BOX4_베팅액": box4_tri_bet_per_race_effective,
                "BOX4_환수액": box4_tri_refund,
                "총베팅액": (
                    (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
                    + (anchor1_26_tri_bet_per_race if anchor1_26_tri_valid else 0.0)
                    + (anchor2_137_trio_bet_per_race if anchor2_137_trio_valid else 0.0)
                    + box4_tri_bet_per_race_effective
                ),
                "총환수액": anchor1_24_57_refund
                + anchor1_26_tri_refund
                + anchor2_137_trio_refund
                + box4_tri_refund,
                "삼쌍승식배당율": odds,
                "삼복승식배당율": odds_trio,
            }
        )

    race_df = pd.DataFrame(race_rows)
    r_pop1_top3 = df[(df["r_pop"] == 1) & (df["r_rank"] <= 3)].copy()
    r_pop1_rank4_plus = df[(df["r_pop"] == 1) & (df["r_rank"] >= 4)].copy()
    tot_score_summary = {}
    tot_score_summary_rank4 = {}
    if not r_pop1_top3.empty:
        r_pop1_top3["tot_score_bin"] = pd.cut(
            r_pop1_top3["tot_score"],
            bins=tot_score_bins,
            labels=[
                "60 이하",
                "61~65",
                "66~70",
                "71~75",
                "76~80",
                "81~85",
                "86~90",
                "91~95",
                "96 이상",
            ],
            right=True,
            include_lowest=True,
        )
        tot_score_summary = (
            r_pop1_top3["tot_score_bin"]
            .value_counts(dropna=False)
            .sort_index()
            .to_dict()
        )
    if not r_pop1_rank4_plus.empty:
        r_pop1_rank4_plus["tot_score_bin"] = pd.cut(
            r_pop1_rank4_plus["tot_score"],
            bins=tot_score_bins,
            labels=[
                "60 이하",
                "61~65",
                "66~70",
                "71~75",
                "76~80",
                "81~85",
                "86~90",
                "91~95",
                "96 이상",
            ],
            right=True,
            include_lowest=True,
        )
        tot_score_summary_rank4 = (
            r_pop1_rank4_plus["tot_score_bin"]
            .value_counts(dropna=False)
            .sort_index()
            .to_dict()
        )
    summary = {}
    if monthly_summary:
        total_races_all = sum(d["races"] for d in monthly_summary.values())
        total_bet_all = sum(d["total_bet"] for d in monthly_summary.values())
        total_refund_all = sum(d["total_refund"] for d in monthly_summary.values())
        total_r_pop1_rank4_races = sum(
            d["r_pop1_rank4_plus_races"] for d in monthly_summary.values()
        )
        total_r_pop2_8_wins = sum(
            d["r_pop1_rank4_plus_rpop2_8_win"] for d in monthly_summary.values()
        )
        total_refund_rate = (
            total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
        )
        total_r_pop2_8_ratio = (
            total_r_pop2_8_wins / total_r_pop1_rank4_races
            if total_r_pop1_rank4_races > 0
            else 0.0
        )
        total_r_pop2_top3 = sum(
            d["r_pop1_rank4_plus_rpop2_top3"] for d in monthly_summary.values()
        )
        total_r_pop2_top3_ratio = (
            total_r_pop2_top3 / total_r_pop1_rank4_races
            if total_r_pop1_rank4_races > 0
            else 0.0
        )
        monthly_rows = [
            {
                "연월": "TOTAL",
                "경주수": total_races_all,
                "r_pop1_4위이상": sum(
                    d["r_pop1_rank4_plus"] for d in monthly_summary.values()
                ),
                "r_pop1_4위이상_비율": (
                    sum(d["r_pop1_rank4_plus"] for d in monthly_summary.values())
                    / total_races_all
                    if total_races_all > 0
                    else 0.0
                ),
                "r_pop1_4위이상_r_pop2_8_1착_비율": total_r_pop2_8_ratio,
                "r_pop1_4위이상_r_pop2_3위내_비율": total_r_pop2_top3_ratio,
                "베팅금": total_bet_all,
                "환수금": total_refund_all,
                "환수율": total_refund_rate,
            }
        ]
        print("[총합]")
        print(
            f"경주수: {total_races_all}  "
            f"베팅금: {int(total_bet_all):,}원  "
            f"환수금: {total_refund_all:,.1f}원  "
            f"환수율: {total_refund_rate:.3f}"
        )
        print("[월별 환수율]")
        for ym in sorted(monthly_summary.keys()):
            d = monthly_summary[ym]
            if d["races"] == 0:
                continue
            refund_rate = (
                d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
            )
            r_pop1_rank4_ratio = d["r_pop1_rank4_plus"] / d["races"]
            r_pop2_8_ratio = (
                d["r_pop1_rank4_plus_rpop2_8_win"] / d["r_pop1_rank4_plus_races"]
                if d["r_pop1_rank4_plus_races"] > 0
                else 0.0
            )
            r_pop2_top3_ratio = (
                d["r_pop1_rank4_plus_rpop2_top3"] / d["r_pop1_rank4_plus_races"]
                if d["r_pop1_rank4_plus_races"] > 0
                else 0.0
            )
            print(
                f"{ym}  "
                f"경주수: {d['races']}  "
                f"r_pop1_4위이상: {d['r_pop1_rank4_plus']}  "
                f"r_pop1_4위이상_비율: {r_pop1_rank4_ratio:.3f}  "
                f"r_pop1_4위이상_r_pop2_8_1착_비율: {r_pop2_8_ratio:.3f}  "
                f"r_pop1_4위이상_r_pop2_3위내_비율: {r_pop2_top3_ratio:.3f}  "
                f"베팅금: {int(d['total_bet']):,}원  "
                f"환수금: {d['total_refund']:,.1f}원  "
                f"환수율: {refund_rate:.3f}"
            )
            monthly_rows.append(
                {
                    "연월": ym,
                    "경주수": d["races"],
                    "r_pop1_4위이상": d["r_pop1_rank4_plus"],
                    "r_pop1_4위이상_비율": r_pop1_rank4_ratio,
                    "r_pop1_4위이상_r_pop2_8_1착_비율": r_pop2_8_ratio,
                    "r_pop1_4위이상_r_pop2_3위내_비율": r_pop2_top3_ratio,
                    "베팅금": d["total_bet"],
                    "환수금": d["total_refund"],
                    "환수율": refund_rate,
                }
            )
        print("[월별 r_pop2 1축/1,3~7 환수율]")
        for ym in sorted(month_summary_anchor2_137_trio.keys()):
            m = month_summary_anchor2_137_trio[ym]
            refund_rate = m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            print(
                f"{ym}  "
                f"베팅금: {int(m['total_bet']):,}원  "
                f"환수금: {m['total_refund']:,.1f}원  "
                f"환수율: {refund_rate:.3f}"
            )

        monthly_df = pd.DataFrame(monthly_rows)
        out_path = "/Users/Super007/Documents/r_pop_monthly_summary.csv"
        monthly_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 월별 요약 CSV 저장: {out_path}")

    return race_df, summary


if __name__ == "__main__":
    from_date = "20260111"
    to_date = "20260111"

    race_df, summary = calc_rpop_anchor_26_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,
    )

    out_path = "/Users/Super007/Documents/r_pop_total_일별.csv"
    if not race_df.empty:
        race_df = race_df.drop_duplicates(subset=["경마장", "경주일", "경주번호"])
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
