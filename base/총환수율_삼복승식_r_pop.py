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
    r_pop(예상), r_rank(실제순위), 삼복승식 배당 포함.
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
# 2. r_pop 1축(2~4) A4 + r_pop 1축(2~3/4~7) + r_pop 1~4 BOX4 삼복승식 환수 계산
# =========================
def calc_rpop_a4_box4_trifecta(
    from_date: str,
    to_date: str,
    bet_unit: int = 1000,
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
    - 각 경주에 대해 r_pop 1을 축으로 r_pop 2~4 중 2두 조합(A4) 삼복승식 베팅.
    - 각 경주에 대해 r_pop 1을 축으로 r_pop 2~3 중 1두 + r_pop 4~7 중 1두 조합 삼복승식 베팅.
    - 실제 1~3위가 r_pop 1을 포함하고, 나머지 2두가 r_pop 2~4 안이면 적중.
    - 실제 1~3위가 r_pop 1을 포함하고, 나머지 2두가 r_pop 2~3과 4~7에서 각 1두씩이면 적중.
    - r_pop 1~4 BOX4 (순서 무관)도 함께 계산.
    - r_pop 1~4 중 1두 + r_pop 5~7 중 2두 조합도 함께 계산.
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

    df["삼복승식배당율"] = df["삼복승식배당율"].astype(float)

    # 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    anchor1_24_bet_per_race = 3 * bet_unit  # C(3,2)
    anchor1_23_47_bet_per_race = 8 * bet_unit  # 2 * 4
    box4_bet_per_race = 4 * bet_unit  # C(4,3)
    anchor13_47_bet_per_race = 18 * bet_unit  # 3 * C(4,2)
    total_races = 0
    excluded_races = 0
    anchor1_24_total_bet = 0.0
    anchor1_24_total_refund = 0.0
    anchor1_24_total_hits = 0
    anchor1_23_47_total_bet = 0.0
    anchor1_23_47_total_refund = 0.0
    anchor1_23_47_total_hits = 0
    box4_total_bet = 0.0
    box4_total_refund = 0.0
    box4_total_hits = 0
    anchor13_47_total_bet = 0.0
    anchor13_47_total_refund = 0.0
    anchor13_47_total_hits = 0
    total_hits_any = 0
    month_summary = {}
    month_anchor_23_47 = {}
    month_box4 = {}
    month_anchor13_47 = {}
    month_total = {}
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

        g_sorted = g.sort_values("r_pop", ascending=True)
        top4 = g_sorted.head(4)["마번"].tolist()
        anchor_gate = top4[0] if top4 else None
        top2_4 = g_sorted.iloc[1:4]["마번"].tolist()
        top2_3 = g_sorted.iloc[1:3]["마번"].tolist()
        top4_7 = g_sorted.iloc[3:7]["마번"].tolist()
        top3_7 = g_sorted.iloc[2:7]["마번"].tolist()
        top1_3 = g_sorted.iloc[0:3]["마번"].tolist()
        top2_4_set = set(top2_4)
        top2_3_set = set(top2_3)
        top4_7_set = set(top4_7)
        top4_set = set(top4)
        top1_3_set = set(top1_3)

        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()

        odds = (
            float(g["삼복승식배당율"].iloc[0])
            if not g["삼복승식배당율"].isna().all()
            else 0.0
        )

        anchor1_24_hit_flag = int(
            len(actual_top3) == 3
            and anchor_gate is not None
            and anchor_gate in set(actual_top3)
            and set(actual_top3).issubset(set([anchor_gate]) | top2_4_set)
        )
        anchor1_24_refund = odds * bet_unit if anchor1_24_hit_flag == 1 else 0.0
        anchor1_23_47_hit_flag = 0
        if len(actual_top3) == 3 and anchor_gate is not None and anchor_gate in actual_top3:
            others = [x for x in actual_top3 if x != anchor_gate]
            if len(others) == 2:
                one_in_23 = (others[0] in top2_3_set and others[1] in top4_7_set) or (
                    others[1] in top2_3_set and others[0] in top4_7_set
                )
                anchor1_23_47_hit_flag = int(one_in_23)
        anchor1_23_47_refund = (
            odds * bet_unit if anchor1_23_47_hit_flag == 1 else 0.0
        )
        box4_hit_flag = int(
            len(actual_top3) == 3
            and len(top4_set) == 4
            and set(actual_top3).issubset(top4_set)
        )
        box4_refund = odds * bet_unit if box4_hit_flag == 1 else 0.0
        anchor13_47_hit_flag = int(
            len(actual_top3) == 3
            and len(top1_3_set) == 3
            and len(top4_7_set) == 4
            and sum(h in top1_3_set for h in actual_top3) == 1
            and sum(h in top4_7_set for h in actual_top3) == 2
        )
        anchor13_47_refund = (
            odds * bet_unit if anchor13_47_hit_flag == 1 else 0.0
        )

        anchor1_24_total_bet += anchor1_24_bet_per_race
        anchor1_24_total_refund += anchor1_24_refund
        anchor1_24_total_hits += anchor1_24_hit_flag
        anchor1_23_47_total_bet += anchor1_23_47_bet_per_race
        anchor1_23_47_total_refund += anchor1_23_47_refund
        anchor1_23_47_total_hits += anchor1_23_47_hit_flag
        box4_total_bet += box4_bet_per_race
        box4_total_refund += box4_refund
        box4_total_hits += box4_hit_flag
        anchor13_47_total_bet += (
            anchor13_47_bet_per_race
            if len(top1_3_set) == 3 and len(top4_7_set) == 4
            else 0.0
        )
        anchor13_47_total_refund += anchor13_47_refund
        anchor13_47_total_hits += anchor13_47_hit_flag
        total_hits_any += int(
            anchor1_24_hit_flag
            or anchor1_23_47_hit_flag
            or box4_hit_flag
            or anchor13_47_hit_flag
        )

        if year_month not in month_summary:
            month_summary[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_summary[year_month]["races"] += 1
        month_summary[year_month]["total_bet"] += anchor1_24_bet_per_race
        month_summary[year_month]["total_refund"] += anchor1_24_refund
        month_summary[year_month]["hits"] += anchor1_24_hit_flag
        if year_month not in month_anchor_23_47:
            month_anchor_23_47[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_anchor_23_47[year_month]["races"] += 1
        month_anchor_23_47[year_month]["total_bet"] += anchor1_23_47_bet_per_race
        month_anchor_23_47[year_month]["total_refund"] += anchor1_23_47_refund
        month_anchor_23_47[year_month]["hits"] += anchor1_23_47_hit_flag
        if year_month not in month_box4:
            month_box4[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_box4[year_month]["races"] += 1
        month_box4[year_month]["total_bet"] += box4_bet_per_race
        month_box4[year_month]["total_refund"] += box4_refund
        month_box4[year_month]["hits"] += box4_hit_flag
        if year_month not in month_anchor13_47:
            month_anchor13_47[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_anchor13_47[year_month]["races"] += 1
        month_anchor13_47[year_month]["total_bet"] += (
            anchor13_47_bet_per_race
            if len(top1_3_set) == 3 and len(top4_7_set) == 4
            else 0.0
        )
        month_anchor13_47[year_month]["total_refund"] += anchor13_47_refund
        month_anchor13_47[year_month]["hits"] += anchor13_47_hit_flag
        if year_month not in month_total:
            month_total[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_total[year_month]["races"] += 1
        month_total[year_month]["total_bet"] += (
            anchor1_24_bet_per_race
            + anchor1_23_47_bet_per_race
            + box4_bet_per_race
            + (
                anchor13_47_bet_per_race
                if len(top1_3_set) == 3 and len(top4_7_set) == 4
                else 0.0
            )
        )
        month_total[year_month]["total_refund"] += (
            anchor1_24_refund
            + anchor1_23_47_refund
            + box4_refund
            + anchor13_47_refund
        )
        month_total[year_month]["hits"] += int(
            anchor1_24_hit_flag
            or anchor1_23_47_hit_flag
            or box4_hit_flag
            or anchor13_47_hit_flag
        )

        race_rows.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "축마": anchor_gate if anchor_gate is not None else "",
                "A4": ",".join(map(str, top2_4)),
                "2~3_마번": ",".join(map(str, top2_3)),
                "4~7_마번": ",".join(map(str, top4_7)),
                "3~7_마번": ",".join(map(str, top3_7)),
                "r_pop_top4_마번": ",".join(map(str, top4)),
                "실제_top3_마번": ",".join(map(str, actual_top3)),
                "r_pop1_축_2~4_적중": anchor1_24_hit_flag,
                "r_pop1_축_2~4_환수액": anchor1_24_refund,
                "r_pop1_축_2~3_4~7_적중": anchor1_23_47_hit_flag,
                "r_pop1_축_2~3_4~7_환수액": anchor1_23_47_refund,
                "r_pop1~4_box4_적중": box4_hit_flag,
                "r_pop1~4_box4_환수액": box4_refund,
                "r_pop1~3_축_4~7_적중": anchor13_47_hit_flag,
                "r_pop1~3_축_4~7_환수액": anchor13_47_refund,
                "1축_2~4_베팅액": anchor1_24_bet_per_race,
                "1축_2~4_환수액": anchor1_24_refund,
                "1축_2~3_4~7_베팅액": anchor1_23_47_bet_per_race,
                "1축_2~3_4~7_환수액": anchor1_23_47_refund,
                "BOX4_베팅액": box4_bet_per_race,
                "BOX4_환수액": box4_refund,
                "1~3축_4~7_베팅액": (
                    anchor13_47_bet_per_race
                    if len(top1_3_set) == 3 and len(top4_7_set) == 4
                    else 0.0
                ),
                "1~3축_4~7_환수액": anchor13_47_refund,
                "총베팅액": anchor1_24_bet_per_race
                + anchor1_23_47_bet_per_race
                + box4_bet_per_race
                + (
                    anchor13_47_bet_per_race
                    if len(top1_3_set) == 3 and len(top4_7_set) == 4
                    else 0.0
                ),
                "총환수액": anchor1_24_refund
                + anchor1_23_47_refund
                + box4_refund
                + anchor13_47_refund,
                "삼복승식배당율": odds,
            }
        )

    race_df = pd.DataFrame(race_rows)
    anchor1_24_refund_rate = (
        anchor1_24_total_refund / anchor1_24_total_bet
        if anchor1_24_total_bet > 0
        else 0.0
    )
    anchor1_24_hit_rate = (
        anchor1_24_total_hits / total_races if total_races > 0 else 0.0
    )
    anchor1_23_47_refund_rate = (
        anchor1_23_47_total_refund / anchor1_23_47_total_bet
        if anchor1_23_47_total_bet > 0
        else 0.0
    )
    anchor1_23_47_hit_rate = (
        anchor1_23_47_total_hits / total_races if total_races > 0 else 0.0
    )
    box4_refund_rate = box4_total_refund / box4_total_bet if box4_total_bet > 0 else 0.0
    box4_hit_rate = box4_total_hits / total_races if total_races > 0 else 0.0
    anchor13_47_refund_rate = (
        anchor13_47_total_refund / anchor13_47_total_bet
        if anchor13_47_total_bet > 0
        else 0.0
    )
    anchor13_47_hit_rate = (
        anchor13_47_total_hits / total_races if total_races > 0 else 0.0
    )

    summary = {
        "races": total_races,
        "excluded_races": excluded_races,
        "anchor1_24_total_bet": anchor1_24_total_bet,
        "anchor1_24_total_refund": anchor1_24_total_refund,
        "anchor1_24_refund_rate": anchor1_24_refund_rate,
        "anchor1_24_hit_rate": anchor1_24_hit_rate,
        "anchor1_23_47_total_bet": anchor1_23_47_total_bet,
        "anchor1_23_47_total_refund": anchor1_23_47_total_refund,
        "anchor1_23_47_refund_rate": anchor1_23_47_refund_rate,
        "anchor1_23_47_hit_rate": anchor1_23_47_hit_rate,
        "box4_total_bet": box4_total_bet,
        "box4_total_refund": box4_total_refund,
        "box4_refund_rate": box4_refund_rate,
        "box4_hit_rate": box4_hit_rate,
        "anchor13_47_total_bet": anchor13_47_total_bet,
        "anchor13_47_total_refund": anchor13_47_total_refund,
        "anchor13_47_refund_rate": anchor13_47_refund_rate,
        "anchor13_47_hit_rate": anchor13_47_hit_rate,
    }
    total_bet_all = (
        anchor1_24_total_bet
        + anchor1_23_47_total_bet
        + box4_total_bet
        + anchor13_47_total_bet
    )
    total_refund_all = (
        anchor1_24_total_refund
        + anchor1_23_47_total_refund
        + box4_total_refund
        + anchor13_47_total_refund
    )
    total_refund_rate_all = (
        total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
    )
    total_hit_rate_all = total_hits_any / total_races if total_races > 0 else 0.0

    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    print(f"경주수: {total_races}  제외(신마 2두 이상/13두↑): {excluded_races}")
    print(
        f"[총 환수율]  총베팅액: {int(total_bet_all):,}원  "
        f"총환수액: {total_refund_all:,.1f}원  환수율: {total_refund_rate_all:.3f}  "
        f"적중경주수: {total_hits_any}  적중율: {total_hit_rate_all:.3f}"
    )
    print(
        f"[r_pop 1축(2~4) A4 삼복승식]  적중율: {anchor1_24_hit_rate:.3f}  "
        f"총베팅액: {int(anchor1_24_total_bet):,}원  총환수액: {anchor1_24_total_refund:,.1f}원  "
        f"환수율: {anchor1_24_refund_rate:.3f}"
    )
    print(
        f"[r_pop 1축(2~3/4~7) 삼복승식]  적중율: {anchor1_23_47_hit_rate:.3f}  "
        f"총베팅액: {int(anchor1_23_47_total_bet):,}원  총환수액: {anchor1_23_47_total_refund:,.1f}원  "
        f"환수율: {anchor1_23_47_refund_rate:.3f}"
    )
    print(
        f"[r_pop 1~4 BOX4 삼복승식]  적중율: {box4_hit_rate:.3f}  "
        f"총베팅액: {int(box4_total_bet):,}원  총환수액: {box4_total_refund:,.1f}원  "
        f"환수율: {box4_refund_rate:.3f}"
    )
    print(
        f"[r_pop 1~3 축 + 4~7 삼복승식]  적중율: {anchor13_47_hit_rate:.3f}  "
        f"총베팅액: {int(anchor13_47_total_bet):,}원  총환수액: {anchor13_47_total_refund:,.1f}원  "
        f"환수율: {anchor13_47_refund_rate:.3f}"
    )
    for ym in sorted(month_summary.keys()):
        m = month_summary[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        print(
            f"[월별 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_box4.keys()):
        m = month_box4[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        print(
            f"[월별 BOX4 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_anchor_23_47.keys()):
        m = month_anchor_23_47[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        print(
            f"[월별 1축(2~3/4~7) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_anchor13_47.keys()):
        m = month_anchor13_47[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        print(
            f"[월별 1~3축(4~7) {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    for ym in sorted(month_total.keys()):
        m = month_total[ym]
        month_refund_rate = (
            m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        )
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        print(
            f"[월별 총합 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"총환수율: {month_refund_rate:.3f}  적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}"
        )
    print("===================================")

    return race_df, summary


if __name__ == "__main__":
    from_date = "20260109"
    to_date = "20260111"

    race_df, summary = calc_rpop_a4_box4_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=1000,
    )

    out_path = "/Users/Super007/Documents/r_pop_a4_box4_333.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
