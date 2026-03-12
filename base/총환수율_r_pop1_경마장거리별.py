import pandas as pd
from sqlalchemy import create_engine, text


DB_CONF = {
    "host": "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",
    "port": 3306,
    "user": "letslove",
    "password": "Ruddksp!23",
    "db": "The1",
    "charset": "utf8mb4",
}


def get_engine():
    url = (
        f"mysql+pymysql://{DB_CONF['user']}:{DB_CONF['password']}"
        f"@{DB_CONF['host']}:{DB_CONF['port']}/{DB_CONF['db']}?charset={DB_CONF['charset']}"
    )
    return create_engine(url, pool_pre_ping=True)


def load_result_data_from_db(engine, from_date: str, to_date: str) -> pd.DataFrame:
    sql = text(
        """
    SELECT
        e.rcity AS 경마장,
        e.rdate AS 경주일,
        e.rno AS 경주번호,
        e.gate AS 마번,
        r.distance AS 경주거리,
        x.grade AS 등급,
        e.rank AS rank,
        e.r_pop AS r_pop,
        e.r_rank AS r_rank,
        e.alloc1r AS 단승식배당율,
        e.alloc3r AS 연승식배당율
    FROM The1.exp011 AS e
    LEFT JOIN The1.rec010 AS r
           ON r.rcity = e.rcity
          AND r.rdate = e.rdate
          AND r.rno = e.rno
    LEFT JOIN The1.exp010 AS x
           ON x.rcity = e.rcity
          AND x.rdate = e.rdate
          AND x.rno = e.rno
    WHERE e.rdate >= :from_date
      AND e.rdate <= :to_date
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    )
    with engine.connect() as conn:
        return pd.read_sql(
            sql, conn, params={"from_date": from_date, "to_date": to_date}
        )


def calc_rpop1_track_distance_summary(
    from_date: str,
    to_date: str,
    bet_unit: int = 100,
) -> tuple[pd.DataFrame, dict]:
    engine = get_engine()
    df = load_result_data_from_db(engine, from_date=from_date, to_date=to_date)

    if df.empty:
        print(f"▶ [{from_date} ~ {to_date}] 기간 데이터가 없습니다.")
        return pd.DataFrame(), {}

    df = df.copy()
    df["등급"] = df["등급"].fillna("")
    df = df[
        ~df["등급"].str.contains(r"(?:국OPEN|혼OPEN)", case=False, na=False, regex=True)
    ]
    df["경주일"] = df["경주일"].astype(str)
    df = df[df["경주일"].str.slice(6, 8).astype(int).between(1, 31)].copy()
    df["경주번호"] = pd.to_numeric(df["경주번호"], errors="coerce").fillna(0).astype(int)
    df["마번"] = pd.to_numeric(df["마번"], errors="coerce").fillna(0).astype(int)
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

    df["단승식배당율"] = pd.to_numeric(df["단승식배당율"], errors="coerce").fillna(0.0)
    df["연승식배당율"] = pd.to_numeric(df["연승식배당율"], errors="coerce").fillna(0.0)
    df["신마"] = (df["rank"] >= 98).astype(int)

    race_rows = []
    summary = {}
    total_races = 0
    excluded_races = 0

    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()
        distance = g["경주거리"].iloc[0]

        if len(g) >= 13:
            excluded_races += 1
            continue
        if int(g["신마"].sum()) >= 3:
            excluded_races += 1
            continue
        g_sorted = g.sort_values(["r_pop", "마번"], ascending=[True, True])
        anchor = g_sorted.iloc[0]
        finish_rank = int(anchor["r_rank"])
        total_races += 1

        track_distance_key = (track, distance)
        if track_distance_key not in summary:
            summary[track_distance_key] = {
                "track": track,
                "distance": distance,
                "races": 0,
                "first_hits": 0,
                "second_hits": 0,
                "third_hits": 0,
                "top3_hits": 0,
                "win_bet": 0.0,
                "win_refund": 0.0,
                "place_bet": 0.0,
                "place_refund": 0.0,
            }

        item = summary[track_distance_key]
        item["races"] += 1
        item["first_hits"] += int(finish_rank == 1)
        item["second_hits"] += int(finish_rank == 2)
        item["third_hits"] += int(finish_rank == 3)
        item["top3_hits"] += int(finish_rank <= 3)
        item["win_bet"] += bet_unit
        item["place_bet"] += bet_unit
        item["win_refund"] += (
            float(anchor["단승식배당율"]) * bet_unit if finish_rank == 1 else 0.0
        )
        item["place_refund"] += (
            float(anchor["연승식배당율"]) * bet_unit if finish_rank <= 3 else 0.0
        )

        race_rows.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "경주거리": distance,
                "r_pop1_마번": int(anchor["마번"]),
                "r_pop1_실착순": finish_rank,
                "r_pop1_1위적중": int(finish_rank == 1),
                "r_pop1_2위적중": int(finish_rank == 2),
                "r_pop1_3위적중": int(finish_rank == 3),
                "r_pop1_3위내적중": int(finish_rank <= 3),
                "단승식배당율": float(anchor["단승식배당율"]),
                "연승식배당율": float(anchor["연승식배당율"]),
                "단승베팅액": bet_unit,
                "단승환수액": (
                    float(anchor["단승식배당율"]) * bet_unit
                    if finish_rank == 1
                    else 0.0
                ),
                "연승베팅액": bet_unit,
                "연승환수액": (
                    float(anchor["연승식배당율"]) * bet_unit
                    if finish_rank <= 3
                    else 0.0
                ),
            }
        )

    race_df = pd.DataFrame(race_rows)

    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    print(f"경주수: {total_races}  제외(신마 3두 이상/13두↑): {excluded_races}")

    for key in sorted(summary.keys(), key=lambda x: (str(x[0]), x[1])):
        d = summary[key]
        distance_label = (
            f"{int(d['distance'])}m" if pd.notna(d["distance"]) else "거리없음"
        )
        first_rate = d["first_hits"] / d["races"] if d["races"] > 0 else 0.0
        second_rate = d["second_hits"] / d["races"] if d["races"] > 0 else 0.0
        third_rate = d["third_hits"] / d["races"] if d["races"] > 0 else 0.0
        top3_rate = d["top3_hits"] / d["races"] if d["races"] > 0 else 0.0
        win_roi = d["win_refund"] / d["win_bet"] if d["win_bet"] > 0 else 0.0
        place_roi = (
            d["place_refund"] / d["place_bet"] if d["place_bet"] > 0 else 0.0
        )
        print(
            f"[경마장별 거리별 {d['track']} {distance_label}]  경주수: {d['races']}  "
            f"1위: {d['first_hits']} ({first_rate:.3f})  "
            f"2위: {d['second_hits']} ({second_rate:.3f})  "
            f"3위: {d['third_hits']} ({third_rate:.3f})  "
            f"3위내: {d['top3_hits']} ({top3_rate:.3f})  "
            f"단승환수율: {win_roi:.3f}  연승환수율: {place_roi:.3f}"
        )

    print("===================================")

    summary_rows = []
    for key in sorted(summary.keys(), key=lambda x: (str(x[0]), x[1])):
        d = summary[key]
        summary_rows.append(
            {
                "경마장": d["track"],
                "경주거리": d["distance"],
                "경주수": d["races"],
                "r_pop1_1위적중수": d["first_hits"],
                "r_pop1_1위적중율": d["first_hits"] / d["races"] if d["races"] else 0.0,
                "r_pop1_2위적중수": d["second_hits"],
                "r_pop1_2위적중율": d["second_hits"] / d["races"] if d["races"] else 0.0,
                "r_pop1_3위적중수": d["third_hits"],
                "r_pop1_3위적중율": d["third_hits"] / d["races"] if d["races"] else 0.0,
                "r_pop1_3위내적중수": d["top3_hits"],
                "r_pop1_3위내적중율": d["top3_hits"] / d["races"] if d["races"] else 0.0,
                "단승총베팅액": d["win_bet"],
                "단승총환수액": d["win_refund"],
                "단승환수율": d["win_refund"] / d["win_bet"] if d["win_bet"] else 0.0,
                "연승총베팅액": d["place_bet"],
                "연승총환수액": d["place_refund"],
                "연승환수율": (
                    d["place_refund"] / d["place_bet"] if d["place_bet"] else 0.0
                ),
            }
        )

    return race_df, {
        "races": total_races,
        "excluded_races": excluded_races,
        "track_distance_summary": pd.DataFrame(summary_rows),
    }


if __name__ == "__main__":
    from_date = "20250101"
    to_date = "20260331"

    race_df, summary = calc_rpop1_track_distance_summary(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,
    )

    raw_out_path = "/Users/Super007/Documents/r_pop1_경마장거리별_raw.csv"
    summary_out_path = "/Users/Super007/Documents/r_pop1_경마장거리별_summary.csv"

    if not race_df.empty:
        race_df.to_csv(raw_out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {raw_out_path}")

    summary_df = summary.get("track_distance_summary", pd.DataFrame())
    if not summary_df.empty:
        summary_df.to_csv(summary_out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경마장 경주거리별 summary CSV 저장: {summary_out_path}")
