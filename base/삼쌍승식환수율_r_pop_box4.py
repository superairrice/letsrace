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
    r_pop(예상), r_rank(실제순위), 삼쌍승식 배당 포함.
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
        CAST(SUBSTRING(r.r123alloc, 4) AS DECIMAL(10, 0)) AS 삼쌍승식배당율
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
# 2. r_pop 1~4 BOX4 삼쌍승식 환수 계산
# =========================
def calc_rpop_box4_trifecta(
    from_date: str,
    to_date: str,
    bet_unit: int = 1000,
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
    - 각 경주에 대해 r_pop 기준 상위 4마리를 BOX4로 삼쌍승식 베팅.
    - 삼쌍승식은 순서가 있는 배당이므로, 실제 1~3위가 BOX4 안에 있으면 적중으로 간주.
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

    df["삼쌍승식배당율"] = df["삼쌍승식배당율"].astype(float)

    # 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    box_bet_per_race = 24 * bet_unit  # P(4,3)
    anchor_bet_per_race = 6 * bet_unit  # P(3,2)
    anchor12_bet_per_race = 2 * bet_unit  # P(2,1)
    anchor21_bet_per_race = 2 * bet_unit  # P(2,1)
    anchor2_134_bet_per_race = 6 * bet_unit  # P(3,2)
    anchor2_35_bet_per_race = 6 * bet_unit  # P(3,2)
    anchor3_124_bet_per_race = 6 * bet_unit  # P(3,2)
    anchor4_123_bet_per_race = 6 * bet_unit  # P(3,2)
    anchor1_25_bet_per_race = 12 * bet_unit  # P(4,2)
    anchor1_26_bet_per_race = 20 * bet_unit  # P(5,2)
    total_races = 0
    excluded_races = 0
    box_total_bet = 0.0
    box_total_refund = 0.0
    box_total_hits = 0
    anchor_total_bet = 0.0
    anchor_total_refund = 0.0
    anchor_total_hits = 0
    anchor12_total_bet = 0.0
    anchor12_total_refund = 0.0
    anchor12_total_hits = 0
    anchor21_total_bet = 0.0
    anchor21_total_refund = 0.0
    anchor21_total_hits = 0
    anchor2_134_total_bet = 0.0
    anchor2_134_total_refund = 0.0
    anchor2_134_total_hits = 0
    anchor2_35_total_bet = 0.0
    anchor2_35_total_refund = 0.0
    anchor2_35_total_hits = 0
    anchor3_124_total_bet = 0.0
    anchor3_124_total_refund = 0.0
    anchor3_124_total_hits = 0
    anchor4_123_total_bet = 0.0
    anchor4_123_total_refund = 0.0
    anchor4_123_total_hits = 0
    anchor1_25_total_bet = 0.0
    anchor1_25_total_refund = 0.0
    anchor1_25_total_hits = 0
    anchor1_26_total_bet = 0.0
    anchor1_26_total_refund = 0.0
    anchor1_26_total_hits = 0
    month_summary = {}
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
        top4_set = set(top4)
        anchor_gate = top4[0] if top4 else None
        top234 = top4[1:]
        top234_set = set(top234)
        anchor12_gates = top4[:2]
        top34 = top4[2:]
        top34_set = set(top34)
        anchor2_gate = top4[1] if len(top4) > 1 else None
        anchor3_gate = top4[2] if len(top4) > 2 else None
        anchor4_gate = top4[3] if len(top4) > 3 else None
        top134 = [top4[0], *top34] if len(top4) == 4 else []
        top124 = [top4[0], top4[1], top4[3]] if len(top4) == 4 else []
        top134_set = set(top134)
        top124_set = set(top124)
        top123 = top4[:3] if len(top4) >= 3 else []
        top123_set = set(top123)
        top35 = g_sorted.iloc[2:5]["마번"].tolist()
        top35_set = set(top35)
        top2_5 = g_sorted.iloc[1:5]["마번"].tolist()
        top2_5_set = set(top2_5)
        top2_6 = g_sorted.iloc[1:6]["마번"].tolist()
        top2_6_set = set(top2_6)

        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()
        actual_set = set(actual_top3)
        box_hit_flag = int(len(actual_top3) == 3 and actual_set.issubset(top4_set))
        anchor_hit_flag = int(
            len(actual_top3) == 3
            and anchor_gate is not None
            and actual_top3[0] == anchor_gate
            and set(actual_top3[1:]).issubset(top234_set)
        )

        odds = (
            float(g["삼쌍승식배당율"].iloc[0])
            if not g["삼쌍승식배당율"].isna().all()
            else 0.0
        )
        box_refund = odds * bet_unit if box_hit_flag == 1 else 0.0
        anchor_refund = odds * bet_unit if anchor_hit_flag == 1 else 0.0
        anchor12_hit_flag = int(
            len(actual_top3) == 3
            and len(anchor12_gates) == 2
            and actual_top3[0] == anchor12_gates[0]
            and actual_top3[1] == anchor12_gates[1]
            and actual_top3[2] in top34_set
        )
        anchor12_refund = odds * bet_unit if anchor12_hit_flag == 1 else 0.0
        anchor21_hit_flag = int(
            len(actual_top3) == 3
            and len(anchor12_gates) == 2
            and actual_top3[0] == anchor12_gates[1]
            and actual_top3[1] == anchor12_gates[0]
            and actual_top3[2] in top34_set
        )
        anchor21_refund = odds * bet_unit if anchor21_hit_flag == 1 else 0.0
        anchor2_134_hit_flag = int(
            len(actual_top3) == 3
            and anchor2_gate is not None
            and actual_top3[0] == anchor2_gate
            and set(actual_top3[1:]).issubset(top134_set)
            and len(set(actual_top3[1:])) == 2
        )
        anchor2_134_refund = (
            odds * bet_unit if anchor2_134_hit_flag == 1 else 0.0
        )
        anchor2_35_hit_flag = int(
            len(actual_top3) == 3
            and anchor2_gate is not None
            and actual_top3[0] == anchor2_gate
            and set(actual_top3[1:]).issubset(top35_set)
            and len(set(actual_top3[1:])) == 2
        )
        anchor2_35_refund = odds * bet_unit if anchor2_35_hit_flag == 1 else 0.0
        anchor3_124_hit_flag = int(
            len(actual_top3) == 3
            and anchor3_gate is not None
            and actual_top3[0] == anchor3_gate
            and set(actual_top3[1:]).issubset(top124_set)
            and len(set(actual_top3[1:])) == 2
        )
        anchor3_124_refund = (
            odds * bet_unit if anchor3_124_hit_flag == 1 else 0.0
        )
        anchor4_123_hit_flag = int(
            len(actual_top3) == 3
            and anchor4_gate is not None
            and actual_top3[0] == anchor4_gate
            and set(actual_top3[1:]).issubset(top123_set)
            and len(set(actual_top3[1:])) == 2
        )
        anchor4_123_refund = (
            odds * bet_unit if anchor4_123_hit_flag == 1 else 0.0
        )
        anchor1_25_hit_flag = int(
            len(actual_top3) == 3
            and anchor_gate is not None
            and actual_top3[0] == anchor_gate
            and set(actual_top3[1:]).issubset(top2_5_set)
            and len(set(actual_top3[1:])) == 2
        )
        anchor1_25_refund = (
            odds * bet_unit if anchor1_25_hit_flag == 1 else 0.0
        )
        anchor1_26_hit_flag = int(
            len(actual_top3) == 3
            and anchor_gate is not None
            and actual_top3[0] == anchor_gate
            and set(actual_top3[1:]).issubset(top2_6_set)
            and len(set(actual_top3[1:])) == 2
        )
        anchor1_26_refund = (
            odds * bet_unit if anchor1_26_hit_flag == 1 else 0.0
        )

        box_total_bet += box_bet_per_race
        box_total_refund += box_refund
        box_total_hits += box_hit_flag
        anchor_total_bet += anchor_bet_per_race
        anchor_total_refund += anchor_refund
        anchor_total_hits += anchor_hit_flag
        anchor12_total_bet += anchor12_bet_per_race
        anchor12_total_refund += anchor12_refund
        anchor12_total_hits += anchor12_hit_flag
        anchor21_total_bet += anchor21_bet_per_race
        anchor21_total_refund += anchor21_refund
        anchor21_total_hits += anchor21_hit_flag
        anchor2_134_total_bet += anchor2_134_bet_per_race
        anchor2_134_total_refund += anchor2_134_refund
        anchor2_134_total_hits += anchor2_134_hit_flag
        anchor2_35_total_bet += anchor2_35_bet_per_race
        anchor2_35_total_refund += anchor2_35_refund
        anchor2_35_total_hits += anchor2_35_hit_flag
        anchor3_124_total_bet += anchor3_124_bet_per_race
        anchor3_124_total_refund += anchor3_124_refund
        anchor3_124_total_hits += anchor3_124_hit_flag
        anchor4_123_total_bet += anchor4_123_bet_per_race
        anchor4_123_total_refund += anchor4_123_refund
        anchor4_123_total_hits += anchor4_123_hit_flag
        anchor1_25_total_bet += anchor1_25_bet_per_race
        anchor1_25_total_refund += anchor1_25_refund
        anchor1_25_total_hits += anchor1_25_hit_flag
        anchor1_26_total_bet += anchor1_26_bet_per_race
        anchor1_26_total_refund += anchor1_26_refund
        anchor1_26_total_hits += anchor1_26_hit_flag
        if year_month not in month_summary:
            month_summary[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        total_bet_race = (
            box_bet_per_race
            + anchor_bet_per_race
            + anchor12_bet_per_race
            + anchor21_bet_per_race
            + anchor2_134_bet_per_race
            + anchor2_35_bet_per_race
            + anchor3_124_bet_per_race
            + anchor4_123_bet_per_race
            + anchor1_25_bet_per_race
            + anchor1_26_bet_per_race
        )
        total_refund_race = (
            box_refund
            + anchor_refund
            + anchor12_refund
            + anchor21_refund
            + anchor2_134_refund
            + anchor2_35_refund
            + anchor3_124_refund
            + anchor4_123_refund
            + anchor1_25_refund
            + anchor1_26_refund
        )
        total_hit_race = int(
            box_hit_flag
            or anchor_hit_flag
            or anchor12_hit_flag
            or anchor21_hit_flag
            or anchor2_134_hit_flag
            or anchor2_35_hit_flag
            or anchor3_124_hit_flag
            or anchor4_123_hit_flag
            or anchor1_25_hit_flag
            or anchor1_26_hit_flag
        )
        month_summary[year_month]["races"] += 1
        month_summary[year_month]["total_bet"] += total_bet_race
        month_summary[year_month]["total_refund"] += total_refund_race
        month_summary[year_month]["hits"] += total_hit_race

        race_rows.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "r_pop_top4_마번": ",".join(map(str, top4)),
                "r_pop1_축_마번": anchor_gate if anchor_gate is not None else "",
                "r_pop2_마번": top234[0] if len(top234) > 0 else "",
                "r_pop3_마번": top234[1] if len(top234) > 1 else "",
                "r_pop4_마번": top234[2] if len(top234) > 2 else "",
                "실제_top3_마번": ",".join(map(str, actual_top3)),
                "BOX4_적중": box_hit_flag,
                "BOX4_환수액": box_refund,
                "r_pop1_축_2~4_적중": anchor_hit_flag,
                "r_pop1_축_2~4_환수액": anchor_refund,
                "r_pop1_2_축_3~4_적중": anchor12_hit_flag,
                "r_pop1_2_축_3~4_환수액": anchor12_refund,
                "r_pop2_1_축_3~4_적중": anchor21_hit_flag,
                "r_pop2_1_축_3~4_환수액": anchor21_refund,
                "r_pop2_축_1_3_4_적중": anchor2_134_hit_flag,
                "r_pop2_축_1_3_4_환수액": anchor2_134_refund,
                "r_pop2_축_3~5_적중": anchor2_35_hit_flag,
                "r_pop2_축_3~5_환수액": anchor2_35_refund,
                "r_pop3_축_1_2_4_적중": anchor3_124_hit_flag,
                "r_pop3_축_1_2_4_환수액": anchor3_124_refund,
                "r_pop4_축_1_2_3_적중": anchor4_123_hit_flag,
                "r_pop4_축_1_2_3_환수액": anchor4_123_refund,
                "r_pop1_축_2~5_적중": anchor1_25_hit_flag,
                "r_pop1_축_2~5_환수액": anchor1_25_refund,
                "r_pop1_축_2~6_적중": anchor1_26_hit_flag,
                "r_pop1_축_2~6_환수액": anchor1_26_refund,
                "총베팅액": total_bet_race,
                "총환수액": total_refund_race,
                "삼쌍승식배당율": odds,
            }
        )

    race_df = pd.DataFrame(race_rows)
    box_refund_rate = box_total_refund / box_total_bet if box_total_bet > 0 else 0.0
    box_hit_rate = box_total_hits / total_races if total_races > 0 else 0.0
    anchor_refund_rate = (
        anchor_total_refund / anchor_total_bet if anchor_total_bet > 0 else 0.0
    )
    anchor_hit_rate = anchor_total_hits / total_races if total_races > 0 else 0.0
    anchor12_refund_rate = (
        anchor12_total_refund / anchor12_total_bet
        if anchor12_total_bet > 0
        else 0.0
    )
    anchor12_hit_rate = anchor12_total_hits / total_races if total_races > 0 else 0.0
    anchor21_refund_rate = (
        anchor21_total_refund / anchor21_total_bet
        if anchor21_total_bet > 0
        else 0.0
    )
    anchor21_hit_rate = anchor21_total_hits / total_races if total_races > 0 else 0.0
    anchor2_134_refund_rate = (
        anchor2_134_total_refund / anchor2_134_total_bet
        if anchor2_134_total_bet > 0
        else 0.0
    )
    anchor2_134_hit_rate = (
        anchor2_134_total_hits / total_races if total_races > 0 else 0.0
    )
    anchor2_35_refund_rate = (
        anchor2_35_total_refund / anchor2_35_total_bet
        if anchor2_35_total_bet > 0
        else 0.0
    )
    anchor2_35_hit_rate = (
        anchor2_35_total_hits / total_races if total_races > 0 else 0.0
    )
    anchor3_124_refund_rate = (
        anchor3_124_total_refund / anchor3_124_total_bet
        if anchor3_124_total_bet > 0
        else 0.0
    )
    anchor3_124_hit_rate = (
        anchor3_124_total_hits / total_races if total_races > 0 else 0.0
    )
    anchor4_123_refund_rate = (
        anchor4_123_total_refund / anchor4_123_total_bet
        if anchor4_123_total_bet > 0
        else 0.0
    )
    anchor4_123_hit_rate = (
        anchor4_123_total_hits / total_races if total_races > 0 else 0.0
    )
    anchor1_25_refund_rate = (
        anchor1_25_total_refund / anchor1_25_total_bet
        if anchor1_25_total_bet > 0
        else 0.0
    )
    anchor1_25_hit_rate = (
        anchor1_25_total_hits / total_races if total_races > 0 else 0.0
    )
    anchor1_26_refund_rate = (
        anchor1_26_total_refund / anchor1_26_total_bet
        if anchor1_26_total_bet > 0
        else 0.0
    )
    anchor1_26_hit_rate = (
        anchor1_26_total_hits / total_races if total_races > 0 else 0.0
    )
    total_bet = (
        box_total_bet + anchor_total_bet + anchor12_total_bet + anchor21_total_bet
        + anchor2_134_total_bet + anchor2_35_total_bet + anchor3_124_total_bet
        + anchor4_123_total_bet
        + anchor1_25_total_bet
        + anchor1_26_total_bet
    )
    total_refund = (
        box_total_refund
        + anchor_total_refund
        + anchor12_total_refund
        + anchor21_total_refund
        + anchor2_134_total_refund
        + anchor2_35_total_refund
        + anchor3_124_total_refund
        + anchor4_123_total_refund
        + anchor1_25_total_refund
        + anchor1_26_total_refund
    )
    total_refund_rate = total_refund / total_bet if total_bet > 0 else 0.0
    total_hit_rate = (
        (
            box_total_hits
            + anchor_total_hits
            + anchor12_total_hits
            + anchor21_total_hits
            + anchor2_134_total_hits
            + anchor2_35_total_hits
            + anchor3_124_total_hits
            + anchor4_123_total_hits
            + anchor1_25_total_hits
            + anchor1_26_total_hits
        )
        / total_races
        if total_races > 0
        else 0.0
    )

    summary = {
        "races": total_races,
        "excluded_races": excluded_races,
        "box_total_bet": box_total_bet,
        "box_total_refund": box_total_refund,
        "box_refund_rate": box_refund_rate,
        "box_hit_rate": box_hit_rate,
        "anchor_total_bet": anchor_total_bet,
        "anchor_total_refund": anchor_total_refund,
        "anchor_refund_rate": anchor_refund_rate,
        "anchor_hit_rate": anchor_hit_rate,
        "anchor12_total_bet": anchor12_total_bet,
        "anchor12_total_refund": anchor12_total_refund,
        "anchor12_refund_rate": anchor12_refund_rate,
        "anchor12_hit_rate": anchor12_hit_rate,
        "anchor21_total_bet": anchor21_total_bet,
        "anchor21_total_refund": anchor21_total_refund,
        "anchor21_refund_rate": anchor21_refund_rate,
        "anchor21_hit_rate": anchor21_hit_rate,
        "anchor2_134_total_bet": anchor2_134_total_bet,
        "anchor2_134_total_refund": anchor2_134_total_refund,
        "anchor2_134_refund_rate": anchor2_134_refund_rate,
        "anchor2_134_hit_rate": anchor2_134_hit_rate,
        "anchor2_35_total_bet": anchor2_35_total_bet,
        "anchor2_35_total_refund": anchor2_35_total_refund,
        "anchor2_35_refund_rate": anchor2_35_refund_rate,
        "anchor2_35_hit_rate": anchor2_35_hit_rate,
        "anchor3_124_total_bet": anchor3_124_total_bet,
        "anchor3_124_total_refund": anchor3_124_total_refund,
        "anchor3_124_refund_rate": anchor3_124_refund_rate,
        "anchor3_124_hit_rate": anchor3_124_hit_rate,
        "anchor4_123_total_bet": anchor4_123_total_bet,
        "anchor4_123_total_refund": anchor4_123_total_refund,
        "anchor4_123_refund_rate": anchor4_123_refund_rate,
        "anchor4_123_hit_rate": anchor4_123_hit_rate,
        "anchor1_25_total_bet": anchor1_25_total_bet,
        "anchor1_25_total_refund": anchor1_25_total_refund,
        "anchor1_25_refund_rate": anchor1_25_refund_rate,
        "anchor1_25_hit_rate": anchor1_25_hit_rate,
        "anchor1_26_total_bet": anchor1_26_total_bet,
        "anchor1_26_total_refund": anchor1_26_total_refund,
        "anchor1_26_refund_rate": anchor1_26_refund_rate,
        "anchor1_26_hit_rate": anchor1_26_hit_rate,
        "total_bet": total_bet,
        "total_refund": total_refund,
        "total_refund_rate": total_refund_rate,
        "total_hit_rate": total_hit_rate,
    }

    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    print(f"경주수: {total_races}  제외(신마 2두 이상/13두↑): {excluded_races}")
    print(
        f"[r_pop 1~4 BOX4 삼쌍승식]  적중율: {box_hit_rate:.3f}  "
        f"총베팅액: {int(box_total_bet):,}원  총환수액: {box_total_refund:,.1f}원  "
        f"환수율: {box_refund_rate:.3f}"
    )
    print(
        f"[r_pop 1축(2~4) 삼쌍승식]  적중율: {anchor_hit_rate:.3f}  "
        f"총베팅액: {int(anchor_total_bet):,}원  총환수액: {anchor_total_refund:,.1f}원  "
        f"환수율: {anchor_refund_rate:.3f}"
    )
    print(
        f"[r_pop 1~2축(3~4) 삼쌍승식]  적중율: {anchor12_hit_rate:.3f}  "
        f"총베팅액: {int(anchor12_total_bet):,}원  총환수액: {anchor12_total_refund:,.1f}원  "
        f"환수율: {anchor12_refund_rate:.3f}"
    )
    print(
        f"[r_pop 2~1축(3~4) 삼쌍승식]  적중율: {anchor21_hit_rate:.3f}  "
        f"총베팅액: {int(anchor21_total_bet):,}원  총환수액: {anchor21_total_refund:,.1f}원  "
        f"환수율: {anchor21_refund_rate:.3f}"
    )
    print(
        f"[r_pop 2축(1,3,4) 삼쌍승식]  적중율: {anchor2_134_hit_rate:.3f}  "
        f"총베팅액: {int(anchor2_134_total_bet):,}원  총환수액: {anchor2_134_total_refund:,.1f}원  "
        f"환수율: {anchor2_134_refund_rate:.3f}"
    )
    print(
        f"[r_pop 2축(3~5) 삼쌍승식]  적중율: {anchor2_35_hit_rate:.3f}  "
        f"총베팅액: {int(anchor2_35_total_bet):,}원  총환수액: {anchor2_35_total_refund:,.1f}원  "
        f"환수율: {anchor2_35_refund_rate:.3f}"
    )
    print(
        f"[r_pop 3축(1,2,4) 삼쌍승식]  적중율: {anchor3_124_hit_rate:.3f}  "
        f"총베팅액: {int(anchor3_124_total_bet):,}원  총환수액: {anchor3_124_total_refund:,.1f}원  "
        f"환수율: {anchor3_124_refund_rate:.3f}"
    )
    print(
        f"[r_pop 4축(1,2,3) 삼쌍승식]  적중율: {anchor4_123_hit_rate:.3f}  "
        f"총베팅액: {int(anchor4_123_total_bet):,}원  총환수액: {anchor4_123_total_refund:,.1f}원  "
        f"환수율: {anchor4_123_refund_rate:.3f}"
    )
    print(
        f"[r_pop 1축(2~5) 4복조 삼쌍승식]  적중율: {anchor1_25_hit_rate:.3f}  "
        f"총베팅액: {int(anchor1_25_total_bet):,}원  총환수액: {anchor1_25_total_refund:,.1f}원  "
        f"환수율: {anchor1_25_refund_rate:.3f}"
    )
    print(
        f"[r_pop 1축(2~6) 5복조 삼쌍승식]  적중율: {anchor1_26_hit_rate:.3f}  "
        f"총베팅액: {int(anchor1_26_total_bet):,}원  총환수액: {anchor1_26_total_refund:,.1f}원  "
        f"환수율: {anchor1_26_refund_rate:.3f}"
    )
    print(
        f"[합계]  적중율: {total_hit_rate:.3f}  "
        f"총베팅액: {int(total_bet):,}원  총환수액: {total_refund:,.1f}원  "
        f"환수율: {total_refund_rate:.3f}"
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
            f"환수율: {month_refund_rate:.3f}  적중율: {month_hit_rate:.3f}"
        )
    print("===================================")

    return race_df, summary


if __name__ == "__main__":
    from_date = "20231201"
    to_date = "20251231"

    race_df, summary = calc_rpop_box4_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=1000,
    )

    out_path = "/Users/Super007/Documents/r_pop_box4_trifecta_raw.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
