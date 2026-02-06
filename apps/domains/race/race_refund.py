import pandas as pd
from contextlib import closing
from django.conf import settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


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
        CAST(SUBSTRING(r.r123alloc, 4) AS DECIMAL(10, 1)) AS 삼쌍승식배당율,
        CAST(SUBSTRING(r.r333alloc, 4) AS DECIMAL(10, 1)) AS 삼복승식배당율
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
    return pd.read_sql(
        text(sql),
        conn,
        params={"from_date": from_date, "to_date": to_date},
    )


def get_engine():
    db = settings.DATABASES.get("default", {})
    url = URL.create(
        drivername="mysql+pymysql",
        username=db.get("USER"),
        password=db.get("PASSWORD"),
        host=db.get("HOST") or "localhost",
        port=int(db.get("PORT") or 3306),
        database=db.get("NAME"),
        query={"charset": "utf8mb4"},
    )
    return create_engine(url)


# =========================
# 2. r_pop 1축(2~4) 2등/5~7 3등 삼쌍승식
#    + r_pop 1~4 BOX4 삼복승식 환수 계산
# =========================
def calc_rpop_anchor_26_trifecta(
    from_date: str,
    to_date: str,
    bet_unit: int = 200,
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
    try:
        with closing(engine.connect()) as conn:
            df = load_result_data_from_db(conn, from_date=from_date, to_date=to_date)
    finally:
        engine.dispose()

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
    df["경주번호"] = pd.to_numeric(df["경주번호"], errors="coerce")
    df["마번"] = pd.to_numeric(df["마번"], errors="coerce")
    df = df.dropna(subset=["경주번호", "마번"]).copy()
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

    anchor1_24_57_bet_unit = bet_unit
    anchor1_24_57_bet_per_race = 9 * anchor1_24_57_bet_unit  # 3 * 3
    anchor1_24_bet_unit = bet_unit
    anchor1_24_bet_per_race = 6 * anchor1_24_bet_unit  # 3P2
    anchor1_24_trio_bet_unit = bet_unit
    anchor1_24_trio_bet_per_race = 3 * anchor1_24_trio_bet_unit  # C(3,2)
    box4_trio_bet_unit = bet_unit
    box4_trio_bet_per_race = 4 * box4_trio_bet_unit  # C(4,3)
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
    total_hits_any = 0
    total_holes_all = 0
    day_summary = {}
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

        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()
        odds = float(g["삼쌍승식배당율"].iloc[0])
        odds_trio = float(g["삼복승식배당율"].iloc[0])
        if odds <= 0 or odds_trio <= 0:
            excluded_races += 1
            continue

        total_races += 1

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
        hit_any = int(
            anchor1_24_57_hit_flag
            or anchor1_24_hit_flag
            or anchor1_24_trio_hit_flag
            or box4_trio_hit_flag
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
        total_hits_any += hit_any

        holes_per_race = (
            (9 if anchor1_24_57_valid else 0)
            + (6 if anchor1_24_valid else 0)
            + (3 if anchor1_24_trio_valid else 0)
            + 4
        )
        total_holes_all += holes_per_race
        if date not in day_summary:
            day_summary[date] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        day_summary[date]["races"] += 1
        day_summary[date]["total_bet"] += (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (anchor1_24_trio_bet_per_race if anchor1_24_trio_valid else 0.0)
            + box4_trio_bet_per_race
        )
        day_summary[date]["total_refund"] += (
            anchor1_24_57_refund
            + anchor1_24_refund
            + anchor1_24_trio_refund
            + box4_trio_refund
        )
        day_summary[date]["hits"] += hit_any
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
                "총구멍수": holes_per_race,
                "총베팅액": (
                    (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
                    + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
                    + (anchor1_24_trio_bet_per_race if anchor1_24_trio_valid else 0.0)
                    + box4_trio_bet_per_race
                ),
                "총환수액": anchor1_24_57_refund
                + anchor1_24_refund
                + anchor1_24_trio_refund
                + box4_trio_refund,
                "삼쌍승식배당율": odds,
                "삼복승식배당율": odds_trio,
            }
        )

    race_df = pd.DataFrame(race_rows)
    summary = {
        
        "day_summary": day_summary,
    }
    # total summary values no longer used in return or output

    print("===================================")
    for day in sorted(day_summary.keys()):
        d = day_summary[day]
        day_refund_rate = (
            d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
        )
        day_hit_rate = d["hits"] / d["races"] if d["races"] > 0 else 0.0
        day_profit = d["total_refund"] - d["total_bet"]
        print(
            f"[일별 {day}]  경주수: {d['races']}  "
            f"총베팅액: {int(d['total_bet']):,}원  총환수액: {d['total_refund']:,.1f}원  "
            f"이익금액: {day_profit:,.1f}원  "
            f"환수율: {day_refund_rate:.3f}  적중경주수: {d['hits']}  적중율: {day_hit_rate:.3f}"
        )
    print("===================================")

    return race_df, summary


if __name__ == "__main__":
    from_date = "20260116"
    to_date = "20260118"

    race_df, summary = calc_rpop_anchor_26_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,
    )
    print(summary)
