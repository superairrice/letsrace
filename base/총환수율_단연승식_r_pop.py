import pymysql
import pandas as pd
from contextlib import closing


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
    r_pop(예상), r_rank(실제순위), 단승식/연승식 배당 포함.
    """
    sql = """
    SELECT
        e.rcity      AS 경마장,
        e.rdate      AS 경주일,
        e.rno        AS 경주번호,
        e.gate       AS 마번,
        x.grade      AS 등급,
        e.rank       AS rank,       -- 예상순위(rank)
        e.r_pop      AS r_pop,      -- 예상순위(r_pop)
        e.r_rank     AS r_rank,     -- 실제순위
        CAST(e.alloc1r AS DECIMAL(10, 1)) AS 단승식배당율,
        CAST(e.alloc3r AS DECIMAL(10, 1)) AS 연승식배당율
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
# 2. 단승식/연승식 r_pop 1 단독 계산
# =========================
def calc_rpop_a4_box4_trifecta(
    from_date: str,
    to_date: str,
    bet_unit: int = 1000,
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
    - 각 경주에 대해 단승식/연승식 r_pop 1 단독 베팅(구멍당 1000원) 계산.
    - 실제 1~3위에 r_pop 1이 포함되면 적중.
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
    

    # 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    win_unit = 1000
    place_unit = 1000
    win_anchor1_bet_per_race = win_unit
    total_races = 0
    excluded_races = 0
    win_anchor1_total_bet = 0.0
    win_anchor1_total_refund = 0.0
    win_anchor1_total_hits = 0
    place_anchor1_total_bet = 0.0
    place_anchor1_total_refund = 0.0
    place_anchor1_total_hits = 0
    total_hits_any = 0
    month_win = {}
    month_place = {}
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

        g_sorted = g.sort_values("r_pop", ascending=True)
        top4 = g_sorted.head(4)["마번"].tolist()
        anchor_gate = top4[0] if top4 else None
        anchor_row = (
            g[g["마번"] == anchor_gate] if anchor_gate is not None else g.iloc[0:0]
        )
        anchor_rank = anchor_row.iloc[0]["r_rank"] if not anchor_row.empty else None
        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()

        odds_win = (
            float(anchor_row["단승식배당율"].iloc[0])
            if not anchor_row.empty
            else float(g["단승식배당율"].iloc[0])
        )
        odds_place = (
            float(anchor_row["연승식배당율"].iloc[0])
            if not anchor_row.empty
            else float(g["연승식배당율"].iloc[0])
        )

        if odds_place <= 1.1:
            place_bet_race = 0
            win_bet_race = 0
        else:
            place_bet_race = place_unit
            win_bet_race = win_unit
        win_anchor1_hit_flag = int(
            win_bet_race > 0
            and anchor_gate is not None
            and anchor_rank == 1
        )
        win_anchor1_refund = odds_win * win_bet_race if win_anchor1_hit_flag == 1 else 0.0
        place_anchor1_hit_flag = int(
            place_bet_race > 0
            and len(actual_top3) == 3
            and anchor_gate is not None
            and anchor_gate in set(actual_top3)
        )
        place_anchor1_refund = (
            odds_place * place_bet_race if place_anchor1_hit_flag == 1 else 0.0
        )

        win_anchor1_total_bet += win_bet_race
        win_anchor1_total_refund += win_anchor1_refund
        win_anchor1_total_hits += win_anchor1_hit_flag
        place_anchor1_total_bet += place_bet_race
        place_anchor1_total_refund += place_anchor1_refund
        place_anchor1_total_hits += place_anchor1_hit_flag
        total_hits_any += int(win_anchor1_hit_flag or place_anchor1_hit_flag)
        if year_month not in month_win:
            month_win[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        if year_month not in month_place:
            month_place[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_win[year_month]["races"] += 1
        month_win[year_month]["total_bet"] += win_bet_race
        month_win[year_month]["total_refund"] += win_anchor1_refund
        month_win[year_month]["hits"] += win_anchor1_hit_flag
        month_place[year_month]["races"] += 1
        month_place[year_month]["total_bet"] += place_bet_race
        month_place[year_month]["total_refund"] += place_anchor1_refund
        month_place[year_month]["hits"] += place_anchor1_hit_flag

        total_bet_race = win_bet_race + place_bet_race
        total_refund_race = win_anchor1_refund + place_anchor1_refund
        race_rows.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "축마": anchor_gate if anchor_gate is not None else "",
                "r_pop1_실제순위": anchor_rank if anchor_rank is not None else "",
                "단승식_1축_적중": win_anchor1_hit_flag,
                "단승식_1축_환수액": win_anchor1_refund,
                "단승식_1축_베팅액": win_bet_race,
                "연승식_1축_적중": place_anchor1_hit_flag,
                "연승식_1축_환수액": place_anchor1_refund,
                "연승식_1축_베팅액": place_bet_race,
                "총베팅액": total_bet_race,
                "총환수액": total_refund_race,
                "단승식배당율": odds_win,
                "연승식배당율": odds_place,
            }
        )

    race_df = pd.DataFrame(race_rows)
    win_anchor1_refund_rate = (
        win_anchor1_total_refund / win_anchor1_total_bet
        if win_anchor1_total_bet > 0
        else 0.0
    )
    win_anchor1_hit_rate = (
        win_anchor1_total_hits / total_races if total_races > 0 else 0.0
    )
    place_anchor1_refund_rate = (
        place_anchor1_total_refund / place_anchor1_total_bet
        if place_anchor1_total_bet > 0
        else 0.0
    )
    place_anchor1_hit_rate = (
        place_anchor1_total_hits / total_races if total_races > 0 else 0.0
    )
    summary = {
        "races": total_races,
        "excluded_races": excluded_races,
        "win_anchor1_total_bet": win_anchor1_total_bet,
        "win_anchor1_total_refund": win_anchor1_total_refund,
        "win_anchor1_refund_rate": win_anchor1_refund_rate,
        "win_anchor1_hit_rate": win_anchor1_hit_rate,
        "place_anchor1_total_bet": place_anchor1_total_bet,
        "place_anchor1_total_refund": place_anchor1_total_refund,
        "place_anchor1_refund_rate": place_anchor1_refund_rate,
        "place_anchor1_hit_rate": place_anchor1_hit_rate,
    }
    total_bet_all = (
        win_anchor1_total_bet
        + place_anchor1_total_bet
    )
    total_refund_all = (
        win_anchor1_total_refund
        + place_anchor1_total_refund
    )
    total_refund_rate_all = (
        total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
    )
    total_hit_rate_all = total_hits_any / total_races if total_races > 0 else 0.0

    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    print(f"경주수: {total_races}  제외(신마 3두 이상/13두↑): {excluded_races}")
    print(
        f"[총 환수율]  총베팅액: {int(total_bet_all):,}원  "
        f"총환수액: {total_refund_all:,.1f}원  환수율: {total_refund_rate_all:.3f}  "
        f"적중경주수: {total_hits_any}  적중율: {total_hit_rate_all:.3f}"
    )
    print(
        f"[단승식 r_pop 1 단독]  적중율: {win_anchor1_hit_rate:.3f}  "
        f"총베팅액: {int(win_anchor1_total_bet):,}원  "
        f"총환수액: {win_anchor1_total_refund:,.1f}원  "
        f"환수율: {win_anchor1_refund_rate:.3f}"
    )
    print(
        f"[연승식 r_pop 1 단독]  적중율: {place_anchor1_hit_rate:.3f}  "
        f"총베팅액: {int(place_anchor1_total_bet):,}원  "
        f"총환수액: {place_anchor1_total_refund:,.1f}원  "
        f"환수율: {place_anchor1_refund_rate:.3f}"
    )
    for ym in sorted(month_win.keys()):
        m = month_win[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        print(
            f"[월별 단승식 r_pop 1 단독 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_place.keys()):
        m = month_place[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        print(
            f"[월별 연승식 r_pop 1 단독 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    print("===================================")

    return race_df, summary


if __name__ == "__main__":
    from_date = "20241201"
    to_date = "20251231"

    race_df, summary = calc_rpop_a4_box4_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=1000,
    )

    out_path = "/Users/Super007/Documents/r_pop_a4_box4_22.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
