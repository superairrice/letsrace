import pymysql
import pandas as pd
from contextlib import closing
from collections import Counter


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
        e.jockey     AS 기수,
        r.distance   AS 경주거리,
        x.grade      AS 등급,
        x.dividing   AS 부담방식,
        e.rank       AS rank,       -- 예상순위(rank)
        e.r_pop      AS r_pop,      -- 예상순위(r_pop)
        e.r_rank     AS r_rank,     -- 실제순위
        e.handycap   AS 부담중량,
        e.h_weight   AS 마체중_raw,
        e.tot_score  AS tot_score,
        e.s1f_per    AS s1f_per,
        e.g3f_per    AS g3f_per,
        e.g1f_per    AS g1f_per,
        CAST(SUBSTRING(r.r123alloc, 4) AS DECIMAL(10, 1)) AS 삼쌍승식배당율,
        CAST(SUBSTRING(r.r333alloc, 4) AS DECIMAL(10, 1)) AS 삼복승식배당율,
        CAST(SUBSTRING(r.r2alloc, 3) AS DECIMAL(10, 1)) AS 복승식배당율
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
#    + r_pop 1~4 BOX4 삼복승식 집계
#    + r_pop 5~7 1축 + r_pop 1~4 복조 삼복승식
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
    - r_pop 5~7 1축 + r_pop 1~4 복조 삼복승식 베팅.
    - r_pop 1축 + r_pop 2~4 삼복승식 베팅.
    - r_pop 1~4 BOX4 삼복승식 베팅.
    - 실제 1~3위가 (r_pop1, r_pop2~4, r_pop5~7) 순서로 맞으면 적중.
    - BOX4는 실제 1~3위가 r_pop 1~4 안에 있으면 적중.
    - 베팅/적중 집계.
    """
    def get_avg_bucket(avg_val):
        if avg_val is None or pd.isna(avg_val):
            return "NA"
        if avg_val >= 90:
            return "90+"
        if avg_val >= 80:
            return "80~89.9"
        if avg_val >= 70:
            return "70~79.9"
        if avg_val >= 60:
            return "60~69.9"
        if avg_val >= 50:
            return "50~59.9"
        return "<50"


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
    if "부담방식" in df.columns:
        df["부담방식"] = df["부담방식"].fillna("").astype(str).str.strip()
    else:
        df["부담방식"] = ""
    df = df[
        ~df["등급"].str.contains(r"(?:국OPEN|혼OPEN)", case=False, na=False, regex=True)
    ]
    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)
    df["연월"] = df["경주일"].str.slice(0, 6)
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")
    df["부담중량"] = pd.to_numeric(df["부담중량"], errors="coerce")
    if "기수" in df.columns:
        df["기수"] = df["기수"].fillna("").astype(str).str.strip()
    else:
        df["기수"] = ""
    if "마체중_raw" in df.columns:
        df["마체중_raw"] = df["마체중_raw"].astype(str).str.strip()
        df["마체중증감"] = (
            df["마체중_raw"]
            .str.extract(r"([+-]\s*\d+)")
            .iloc[:, 0]
            .str.replace(" ", "", regex=False)
        )
        df["마체중증감"] = pd.to_numeric(df["마체중증감"], errors="coerce")
    else:
        df["마체중증감"] = pd.NA

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
    df["복승식배당율"] = pd.to_numeric(df["복승식배당율"], errors="coerce").fillna(0.0)
    df["tot_score"] = pd.to_numeric(df["tot_score"], errors="coerce")
    df["s1f_per"] = pd.to_numeric(df["s1f_per"], errors="coerce")
    df["g3f_per"] = pd.to_numeric(df["g3f_per"], errors="coerce")
    df["g1f_per"] = pd.to_numeric(df["g1f_per"], errors="coerce")
    # 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    anchor1_24_57_bet_unit = 200
    anchor1_24_57_bet_per_race = 9 * anchor1_24_57_bet_unit  # 3 * 3
    anchor1_24_bet_unit = 200
    anchor1_24_bet_per_race = 6 * anchor1_24_bet_unit  # 3P2
    r_pop4_8_anchor_1_3_trio_bet_unit = 200
    r_pop4_8_anchor_1_3_trio_bet_per_race = (
        15 * r_pop4_8_anchor_1_3_trio_bet_unit
    )  # 5 * C(3,2)
    total_races_bet = 0
    excluded_races = 0
    anchor1_24_57_total_bet = 0.0
    anchor1_24_57_total_refund = 0.0
    anchor1_24_57_total_hits = 0
    anchor1_24_57_races = 0
    anchor1_24_total_bet = 0.0
    anchor1_24_total_refund = 0.0
    anchor1_24_total_hits = 0
    anchor1_24_races = 0
    r_pop4_8_anchor_1_3_trio_total_bet = 0.0
    r_pop4_8_anchor_1_3_trio_total_refund = 0.0
    r_pop4_8_anchor_1_3_trio_total_hits = 0
    r_pop4_8_anchor_1_3_trio_races = 0
    total_hits_any = 0
    total_holes_all = 0
    total_refund_all = 0.0
    month_summary_raw = {}
    race_bet_summaries = []
    r_pop1_rank4plus_r_pop2_win = 0
    r_pop1_rank4plus_r_pop3_win = 0
    r_pop1_rank4plus_r_pop4_win = 0
    r_pop1_or_r_pop2_win = 0
    r_pop1_or_r_pop2_top3 = 0
    r_pop1_or_r_pop2_top2 = 0
    r_pop1_win = 0
    r_pop2_win = 0
    r_pop1_3_top2_two_plus = 0
    r_pop1_rank4plus_burden = Counter()
    r_pop1_rank4plus_distance = Counter()
    r_pop1_rank4plus_grade = Counter()
    r_pop1_rank4plus_weight_change = Counter()
    r_pop1_rank4plus_jockey = Counter()
    r_pop1_jockey_stats = {}
    # ROI 제외 외 환수율 집계 제거로 r_pop1_rank4plus_bets 사용하지 않음

    def compute_combo_totals():
        combo_totals = {}
        for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
            g = g.copy()
            if len(g) >= 13:
                continue
            new_cnt = int(g["신마"].sum())
            if new_cnt >= 3:
                continue
            distance = g["경주거리"].iloc[0]
            grade = g["등급"].iloc[0]
            dividing = g["부담방식"].iloc[0] if "부담방식" in g.columns else ""
            g_sorted = g.sort_values("r_pop", ascending=True)
            rank_sorted = g.sort_values("rank", ascending=True)
            anchor_burden = g_sorted.iloc[0]["부담중량"] if len(g_sorted) > 0 else None
            if anchor_burden is None or pd.isna(anchor_burden) or anchor_burden < 48.5:
                continue
            top4 = g_sorted.head(4)["마번"].tolist()
            rank_top4 = rank_sorted.head(4)["마번"].tolist()
            anchor_gate = top4[0] if top4 else None
            top2_4 = g_sorted.iloc[1:4]["마번"].tolist()
            top5_7 = g_sorted.iloc[4:7]["마번"].tolist()
            top2_4_set = set(top2_4)
            top5_7_set = set(top5_7)
            top1_4_set = set(top4)
            top1_3 = g_sorted.iloc[0:3]["마번"].tolist()
            top4_7 = g_sorted.iloc[3:7]["마번"].tolist()
            top1_3_set = set(top1_3)
            top4_7_set = set(top4_7)
            top4_8 = g_sorted.iloc[3:8]["마번"].tolist()
            top4_8_set = set(top4_8)
            rank_anchor = rank_top4[0] if rank_top4 else None
            rank2_4 = rank_top4[1:4] if len(rank_top4) >= 4 else []
            rank2_4_set = set(rank2_4)
            actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()
            actual_top2 = g[g["r_rank"] <= 2].sort_values("r_rank")["마번"].tolist()
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
            r_pop4_8_anchor_1_3_trio_valid = len(top1_3) == 3 and len(top4_8) == 5
            r_pop4_8_anchor_1_3_trio_hit_flag = int(
                r_pop4_8_anchor_1_3_trio_valid
                and len(actual_top3) == 3
                and actual_set.issubset(top1_3_set | top4_8_set)
                and len(actual_set & top4_8_set) == 1
                and len(actual_set & top1_3_set) == 2
            )
            r_pop4_8_anchor_1_3_trio_refund = (
                odds_trio * r_pop4_8_anchor_1_3_trio_bet_unit
                if r_pop4_8_anchor_1_3_trio_hit_flag == 1
                else 0.0
            )
            race_total_bet = (
                (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
                + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
                + (
                    r_pop4_8_anchor_1_3_trio_bet_per_race
                    if r_pop4_8_anchor_1_3_trio_valid
                    else 0.0
                )
            )
            race_total_refund = (
                anchor1_24_57_refund
                + anchor1_24_refund
                + r_pop4_8_anchor_1_3_trio_refund
            )
            race_hit_any = int(
                anchor1_24_57_hit_flag
                or anchor1_24_hit_flag
                or r_pop4_8_anchor_1_3_trio_hit_flag
            )
            combo_key = (
                f"{track}/"
                f"{distance if distance is not None and not pd.isna(distance) else '미상'}/"
                f"{grade if grade != '' else '미상'}/"
                f"{dividing if dividing != '' else '미상'}"
            )
            stats = combo_totals.setdefault(
                combo_key, {"bet": 0.0, "refund": 0.0, "races": 0, "hits": 0}
            )
            stats["bet"] += race_total_bet
            stats["refund"] += race_total_refund
            stats["races"] += 1
            stats["hits"] += race_hit_any

        return combo_totals

    combo_totals = compute_combo_totals()
    insert_rows = []
    for key, data in combo_totals.items():
        if data["races"] <= 0 or data["bet"] <= 0:
            continue
        parts = key.split("/", 3)
        rcity = parts[0] if len(parts) > 0 else None
        distance_raw = parts[1] if len(parts) > 1 else None
        grade = parts[2] if len(parts) > 2 else None
        dividing = parts[3] if len(parts) > 3 else None
        distance = None
        if distance_raw and distance_raw != "미상":
            try:
                distance = int(float(distance_raw))
            except ValueError:
                distance = None
        if distance is None:
            continue
        grade = None if grade in (None, "", "미상") else grade
        dividing = None if dividing in (None, "", "미상") else dividing
        hit_rate = data["hits"] / data["races"] if data["races"] > 0 else 0.0
        roi = data["refund"] / data["bet"] if data["bet"] > 0 else 0.0
        insert_rows.append(
            (
                from_date,
                to_date,
                rcity,
                distance,
                grade,
                dividing,
                data["races"],
                data["hits"],
                hit_rate,
                roi,
                data["bet"],
                data["refund"],
            )
        )
    if insert_rows:
        insert_sql = """
        INSERT INTO `The1`.`race_roi`
        (`from_date`, `to_date`, `rcity`, `distance`, `grade`, `dividing`,
         `races`, `hits`, `hit_rate`, `roi`, `bet`, `account`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            `races` = VALUES(`races`),
            `hits` = VALUES(`hits`),
            `hit_rate` = VALUES(`hit_rate`),
            `roi` = VALUES(`roi`),
            `bet` = VALUES(`bet`),
            `account` = VALUES(`account`)
        """
        with closing(get_conn()) as conn:
            with conn.cursor() as cursor:
                cursor.executemany(insert_sql, insert_rows)
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
        distance = g["경주거리"].iloc[0]
        grade = g["등급"].iloc[0]

        dividing = g["부담방식"].iloc[0] if "부담방식" in g.columns else ""
        g_sorted = g.sort_values("r_pop", ascending=True)
        rank_sorted = g.sort_values("rank", ascending=True)
        anchor_burden = g_sorted.iloc[0]["부담중량"] if len(g_sorted) > 0 else None
        if anchor_burden is None or pd.isna(anchor_burden) or anchor_burden < 48.5:
            excluded_races += 1
            continue
        combo_key = (
            f"{track}/"
            f"{distance if distance is not None and not pd.isna(distance) else '미상'}/"
            f"{grade if grade != '' else '미상'}/"
            f"{dividing if dividing != '' else '미상'}"
        )
        total_races_bet += 1
        top4 = g_sorted.head(4)["마번"].tolist()
        rank_top4 = rank_sorted.head(4)["마번"].tolist()
        anchor_gate = top4[0] if top4 else None
        r_pop2_gate = g_sorted.iloc[1]["마번"] if len(g_sorted) > 1 else None
        r_pop3_gate = g_sorted.iloc[2]["마번"] if len(g_sorted) > 2 else None
        r_pop4_gate = g_sorted.iloc[3]["마번"] if len(g_sorted) > 3 else None
        top2_4 = g_sorted.iloc[1:4]["마번"].tolist()
        top5_7 = g_sorted.iloc[4:7]["마번"].tolist()
        top2_4_set = set(top2_4)
        top5_7_set = set(top5_7)
        top1_4_set = set(top4)
        top1_3 = g_sorted.iloc[0:3]["마번"].tolist()
        top4_7 = g_sorted.iloc[3:7]["마번"].tolist()
        top1_3_set = set(top1_3)
        top4_7_set = set(top4_7)
        top4_8 = g_sorted.iloc[3:8]["마번"].tolist()
        top4_8_set = set(top4_8)
        rank_anchor = rank_top4[0] if rank_top4 else None
        rank2_4 = rank_top4[1:4] if len(rank_top4) >= 4 else []
        rank2_4_set = set(rank2_4)
        top3_5_set = (
            set(g_sorted.iloc[2:5]["마번"].tolist()) if len(g_sorted) >= 5 else set()
        )

        actual_top3 = g[g["r_rank"] <= 3].sort_values("r_rank")["마번"].tolist()
        actual_top2 = g[g["r_rank"] <= 2].sort_values("r_rank")["마번"].tolist()
        odds = float(g["삼쌍승식배당율"].iloc[0])
        odds_trio = float(g["삼복승식배당율"].iloc[0])
        r_pop1_actual_rank = (
            int(g.loc[g["마번"] == anchor_gate, "r_rank"].iloc[0])
            if anchor_gate is not None and not g.loc[g["마번"] == anchor_gate].empty
            else None
        )
        r_pop2_actual_rank = (
            int(g.loc[g["마번"] == r_pop2_gate, "r_rank"].iloc[0])
            if r_pop2_gate is not None and not g.loc[g["마번"] == r_pop2_gate].empty
            else None
        )
        r_pop3_actual_rank = (
            int(g.loc[g["마번"] == r_pop3_gate, "r_rank"].iloc[0])
            if r_pop3_gate is not None and not g.loc[g["마번"] == r_pop3_gate].empty
            else None
        )
        r_pop4_actual_rank = (
            int(g.loc[g["마번"] == r_pop4_gate, "r_rank"].iloc[0])
            if r_pop4_gate is not None and not g.loc[g["마번"] == r_pop4_gate].empty
            else None
        )
        anchor_weight_change = None
        if anchor_gate is not None and "마체중증감" in g.columns:
            anchor_weight_change = g.loc[g["마번"] == anchor_gate, "마체중증감"].iloc[0]
            if pd.isna(anchor_weight_change):
                anchor_weight_change = None
        anchor_jockey = ""
        if anchor_gate is not None and "기수" in g.columns:
            anchor_jockey = g.loc[g["마번"] == anchor_gate, "기수"].iloc[0]
            if not isinstance(anchor_jockey, str):
                anchor_jockey = ""
        if (
            r_pop1_actual_rank is not None
            and r_pop2_actual_rank is not None
            and r_pop1_actual_rank >= 4
            and r_pop2_actual_rank == 1
        ):
            r_pop1_rank4plus_r_pop2_win += 1
        if r_pop1_actual_rank == 1:
            r_pop1_win += 1
        if r_pop2_actual_rank == 1:
            r_pop2_win += 1
        top2_count = sum(
            1
            for v in (r_pop1_actual_rank, r_pop2_actual_rank, r_pop3_actual_rank)
            if v is not None and v <= 2
        )
        if top2_count >= 2:
            r_pop1_3_top2_two_plus += 1
        if r_pop1_actual_rank == 1 or r_pop2_actual_rank == 1:
            r_pop1_or_r_pop2_win += 1
        if (r_pop1_actual_rank is not None and r_pop1_actual_rank <= 3) or (
            r_pop2_actual_rank is not None and r_pop2_actual_rank <= 3
        ):
            r_pop1_or_r_pop2_top3 += 1
        if (r_pop1_actual_rank is not None and r_pop1_actual_rank <= 2) or (
            r_pop2_actual_rank is not None and r_pop2_actual_rank <= 2
        ):
            r_pop1_or_r_pop2_top2 += 1
        if (
            r_pop1_actual_rank is not None
            and r_pop3_actual_rank is not None
            and r_pop1_actual_rank >= 4
            and r_pop3_actual_rank == 1
        ):
            r_pop1_rank4plus_r_pop3_win += 1
        if (
            r_pop1_actual_rank is not None
            and r_pop4_actual_rank is not None
            and r_pop1_actual_rank >= 4
            and r_pop4_actual_rank == 1
        ):
            r_pop1_rank4plus_r_pop4_win += 1
        if r_pop1_actual_rank is not None and r_pop1_actual_rank >= 4:
            if anchor_burden is not None and not pd.isna(anchor_burden):
                r_pop1_rank4plus_burden[anchor_burden] += 1
            if distance is not None and not pd.isna(distance):
                r_pop1_rank4plus_distance[distance] += 1
            if grade is not None and grade != "":
                r_pop1_rank4plus_grade[grade] += 1
            if anchor_weight_change is not None:
                r_pop1_rank4plus_weight_change[anchor_weight_change] += 1
            if anchor_jockey:
                r_pop1_rank4plus_jockey[anchor_jockey] += 1
        if anchor_jockey:
            stats = r_pop1_jockey_stats.setdefault(
                anchor_jockey, {"total": 0, "rank4plus": 0}
            )
            stats["total"] += 1
            if r_pop1_actual_rank is not None and r_pop1_actual_rank >= 4:
                stats["rank4plus"] += 1
        r1_s1f = g_sorted.iloc[0]["s1f_per"] if len(g_sorted) > 0 else pd.NA
        r1_g3f = g_sorted.iloc[0]["g3f_per"] if len(g_sorted) > 0 else pd.NA
        r1_g1f = g_sorted.iloc[0]["g1f_per"] if len(g_sorted) > 0 else pd.NA
        r2_s1f = g_sorted.iloc[1]["s1f_per"] if len(g_sorted) > 1 else pd.NA
        r2_g3f = g_sorted.iloc[1]["g3f_per"] if len(g_sorted) > 1 else pd.NA
        r2_g1f = g_sorted.iloc[1]["g1f_per"] if len(g_sorted) > 1 else pd.NA
        if (
            not pd.isna(r1_s1f)
            and not pd.isna(r1_g3f)
            and not pd.isna(r1_g1f)
            and not pd.isna(r2_s1f)
            and not pd.isna(r2_g3f)
            and not pd.isna(r2_g1f)
        ):
            r1_avg = (r1_s1f + r1_g3f + r1_g1f) / 3
            r2_avg = (r2_s1f + r2_g3f + r2_g1f) / 3
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
        r_pop1_top1_hit = int(len(actual_top3) >= 1 and actual_top3[0] == anchor_gate)
        r_pop1_top3_hit = int(anchor_gate is not None and anchor_gate in actual_set)
        anchor1_24_57_refund = (
            odds * anchor1_24_57_bet_unit if anchor1_24_57_hit_flag == 1 else 0.0
        )
        anchor1_24_refund = (
            odds * anchor1_24_bet_unit if anchor1_24_hit_flag == 1 else 0.0
        )
        r_pop4_8_anchor_1_3_trio_valid = len(top1_3) == 3 and len(top4_8) == 5
        r_pop4_8_anchor_1_3_trio_hit_flag = int(
            r_pop4_8_anchor_1_3_trio_valid
            and len(actual_top3) == 3
            and actual_set.issubset(top1_3_set | top4_8_set)
            and len(actual_set & top4_8_set) == 1
            and len(actual_set & top1_3_set) == 2
        )
        r_pop4_8_anchor_1_3_trio_refund = (
            odds_trio * r_pop4_8_anchor_1_3_trio_bet_unit
            if r_pop4_8_anchor_1_3_trio_hit_flag == 1
            else 0.0
        )
        hit_any = int(
            anchor1_24_57_hit_flag
            or anchor1_24_hit_flag
            or r_pop4_8_anchor_1_3_trio_hit_flag
        )
        race_total_bet = (
            (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
            + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
            + (
                r_pop4_8_anchor_1_3_trio_bet_per_race
                if r_pop4_8_anchor_1_3_trio_valid
                else 0.0
            )
        )
        race_total_refund = (
            anchor1_24_57_refund
            + anchor1_24_refund
            + r_pop4_8_anchor_1_3_trio_refund
        )
        anchor1_24_57_total_bet += (
            anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
        )
        anchor1_24_57_total_refund += anchor1_24_57_refund
        anchor1_24_57_total_hits += anchor1_24_57_hit_flag
        anchor1_24_57_races += 1 if anchor1_24_57_valid else 0
        anchor1_24_total_bet += anchor1_24_bet_per_race if anchor1_24_valid else 0.0
        r_pop4_8_anchor_1_3_trio_total_bet += (
            r_pop4_8_anchor_1_3_trio_bet_per_race
            if r_pop4_8_anchor_1_3_trio_valid
            else 0.0
        )
        r_pop4_8_anchor_1_3_trio_total_refund += r_pop4_8_anchor_1_3_trio_refund
        r_pop4_8_anchor_1_3_trio_total_hits += r_pop4_8_anchor_1_3_trio_hit_flag
        r_pop4_8_anchor_1_3_trio_races += (
            1 if r_pop4_8_anchor_1_3_trio_valid else 0
        )
        anchor1_24_total_refund += anchor1_24_refund
        anchor1_24_total_hits += anchor1_24_hit_flag
        anchor1_24_races += 1 if anchor1_24_valid else 0
        total_refund_all += race_total_refund
        total_hits_any += hit_any
        year_month = str(date)[:6]
        raw_stats = month_summary_raw.setdefault(
            year_month,
            {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
                "r_pop1_top3": 0,
            },
        )
        raw_stats["races"] += 1
        raw_stats["total_bet"] += race_total_bet
        raw_stats["total_refund"] += race_total_refund
        raw_stats["hits"] += hit_any
        raw_stats["r_pop1_top3"] += r_pop1_top3_hit
        race_bet_summaries.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "적중여부": hit_any,
                "베팅금액": race_total_bet,
                "환수금액": race_total_refund,
            }
        )

        holes_per_race = (
            (9 if anchor1_24_57_valid else 0)
            + (6 if anchor1_24_valid else 0)
            + (15 if r_pop4_8_anchor_1_3_trio_valid else 0)
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
                "4~8_마번": ",".join(map(str, top4_8)),
                "실제_top3_마번": ",".join(map(str, actual_top3)),
                "r_pop1_축_2~4_5~7_적중": anchor1_24_57_hit_flag,
                "r_pop1_축_2~4_적중": anchor1_24_hit_flag,
                "r_pop4~8_축_1~3_복조_삼복_적중": r_pop4_8_anchor_1_3_trio_hit_flag,
                "1축_2~4_5~7_베팅액": (
                    anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0
                ),
                "1축_2~4_베팅액": (
                    anchor1_24_bet_per_race if anchor1_24_valid else 0.0
                ),
                "r_pop4~8_축_1~3_복조_삼복_베팅액": (
                    r_pop4_8_anchor_1_3_trio_bet_per_race
                    if r_pop4_8_anchor_1_3_trio_valid
                    else 0.0
                ),
                "총구멍수": holes_per_race,
                "총베팅액": (
                    (anchor1_24_57_bet_per_race if anchor1_24_57_valid else 0.0)
                    + (anchor1_24_bet_per_race if anchor1_24_valid else 0.0)
                    + (
                        r_pop4_8_anchor_1_3_trio_bet_per_race
                        if r_pop4_8_anchor_1_3_trio_valid
                        else 0.0
                    )
                ),
                "삼쌍승식배당율": odds,
                "삼복승식배당율": odds_trio,
            }
        )

    race_df = pd.DataFrame(race_rows)
    summary = {
        "races": total_races_bet,
        "excluded_races": excluded_races,
        "r_pop1_rank4plus_r_pop2_win": r_pop1_rank4plus_r_pop2_win,
        "r_pop1_rank4plus_r_pop3_win": r_pop1_rank4plus_r_pop3_win,
        "r_pop1_rank4plus_r_pop4_win": r_pop1_rank4plus_r_pop4_win,
        "r_pop1_or_r_pop2_win": r_pop1_or_r_pop2_win,
        "r_pop1_or_r_pop2_top3": r_pop1_or_r_pop2_top3,
        "r_pop1_or_r_pop2_top2": r_pop1_or_r_pop2_top2,
        "r_pop1_win": r_pop1_win,
        "r_pop2_win": r_pop2_win,
        "r_pop1_3_top2_two_plus": r_pop1_3_top2_two_plus,
        "anchor1_24_57_total_bet": anchor1_24_57_total_bet,
        "anchor1_24_57_total_refund": anchor1_24_57_total_refund,
        "anchor1_24_57_races": anchor1_24_57_races,
        "anchor1_24_57_hits": anchor1_24_57_total_hits,
        "anchor1_24_57_hit_rate": (
            anchor1_24_57_total_hits / total_races_bet if total_races_bet > 0 else 0.0
        ),
        "anchor1_24_total_bet": anchor1_24_total_bet,
        "anchor1_24_total_refund": anchor1_24_total_refund,
        "anchor1_24_races": anchor1_24_races,
        "anchor1_24_hits": anchor1_24_total_hits,
        "anchor1_24_hit_rate": (
            anchor1_24_total_hits / total_races_bet if total_races_bet > 0 else 0.0
        ),
        "r_pop4_8_anchor_1_3_trio_total_bet": r_pop4_8_anchor_1_3_trio_total_bet,
        "r_pop4_8_anchor_1_3_trio_total_refund": r_pop4_8_anchor_1_3_trio_total_refund,
        "r_pop4_8_anchor_1_3_trio_races": r_pop4_8_anchor_1_3_trio_races,
        "r_pop4_8_anchor_1_3_trio_hits": r_pop4_8_anchor_1_3_trio_total_hits,
        "r_pop4_8_anchor_1_3_trio_hit_rate": (
            r_pop4_8_anchor_1_3_trio_total_hits / total_races_bet
            if total_races_bet > 0
            else 0.0
        ),
    }
    total_bet_all = (
        anchor1_24_57_total_bet
        + anchor1_24_total_bet
        + r_pop4_8_anchor_1_3_trio_total_bet
    )
    total_profit_all = total_refund_all - total_bet_all
    total_roi_all = total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
    total_hit_rate_all = (
        total_hits_any / total_races_bet if total_races_bet > 0 else 0.0
    )
    avg_holes_per_race = (
        total_holes_all / total_races_bet if total_races_bet > 0 else 0.0
    )
    avg_bet_per_race = total_bet_all / total_races_bet if total_races_bet > 0 else 0.0

    def format_top5(counter: Counter) -> str:
        if not counter:
            return "없음"

        def fmt_val(value) -> str:
            if isinstance(value, float):
                return str(int(value)) if value.is_integer() else f"{value:g}"
            return str(value)

        return "  ".join([f"{fmt_val(k)}({v})" for k, v in counter.most_common(5)])

    def format_jockey_rank4plus_top5(stats: dict) -> str:
        if not stats:
            return "없음"
        items = []
        for jockey, data in stats.items():
            total = data["total"]
            if total < 10:
                continue
            rate = data["rank4plus"] / total
            items.append((rate, jockey, total, data["rank4plus"]))
        items.sort(key=lambda x: x[0], reverse=True)
        top = items[:5]
        return "  ".join([f"{j} {r:.3f}({rk}/{t})" for r, j, t, rk in top])


    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    print(
        f"경주수: {total_races_bet}  제외(신마 3두 이상/13두↑): {excluded_races}"
    )
    print(
        f"[총 베팅]  총베팅액: {int(total_bet_all):,}원  "
        f"총환수액: {total_refund_all:,.1f}원  "
        f"총손익: {total_profit_all:,.1f}원  "
        f"ROI: {total_roi_all:.3f}  "
        f"적중경주수: {total_hits_any}  적중율: {total_hit_rate_all:.3f}"
    )
    print(
        f"[경주당]  총구멍수: {avg_holes_per_race:.1f}  "
        f"총베팅액: {avg_bet_per_race:,.1f}원"
    )
    print(f"[경주별 총베팅액]  {int(total_bet_all):,}원")
    print(
        "[r_pop 1축(2~4) 2등/5~7 3등 삼쌍승식]  "
        f"경주수: {summary['anchor1_24_57_races']}  "
        f"적중경주수: {summary['anchor1_24_57_hits']}  "
        f"적중율: {summary['anchor1_24_57_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_24_57_total_bet):,}원  "
        f"총환수액: {summary['anchor1_24_57_total_refund']:,.1f}원  "
        f"ROI: {(summary['anchor1_24_57_total_refund'] / anchor1_24_57_total_bet if anchor1_24_57_total_bet > 0 else 0.0):.3f}"
    )
    print(
        "[r_pop 1축(2~4) 3복조 삼쌍승식]  "
        f"경주수: {summary['anchor1_24_races']}  "
        f"적중경주수: {summary['anchor1_24_hits']}  "
        f"적중율: {summary['anchor1_24_hit_rate']:.3f}  "
        f"총베팅액: {int(anchor1_24_total_bet):,}원  "
        f"총환수액: {summary['anchor1_24_total_refund']:,.1f}원  "
        f"ROI: {(summary['anchor1_24_total_refund'] / anchor1_24_total_bet if anchor1_24_total_bet > 0 else 0.0):.3f}"
    )
    print(
        "[r_pop 4~8 1축 + r_pop 1~3 복조 삼복승식]  "
        f"경주수: {summary['r_pop4_8_anchor_1_3_trio_races']}  "
        f"적중경주수: {summary['r_pop4_8_anchor_1_3_trio_hits']}  "
        f"적중율: {summary['r_pop4_8_anchor_1_3_trio_hit_rate']:.3f}  "
        f"총베팅액: {int(r_pop4_8_anchor_1_3_trio_total_bet):,}원  "
        f"총환수액: {summary['r_pop4_8_anchor_1_3_trio_total_refund']:,.1f}원  "
        f"ROI: {(summary['r_pop4_8_anchor_1_3_trio_total_refund'] / r_pop4_8_anchor_1_3_trio_total_bet if r_pop4_8_anchor_1_3_trio_total_bet > 0 else 0.0):.3f}"
    )
    for ym in sorted(month_summary_raw.keys()):
        m = month_summary_raw[ym]
        month_profit = m["total_refund"] - m["total_bet"]
        month_roi = m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        month_hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        r_pop1_top3_rate = (
            m["r_pop1_top3"] / m["races"] if m["races"] > 0 else 0.0
        )
        print(
            f"[월별 총환수 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  "
            f"총환수액: {m['total_refund']:,.1f}원  "
            f"총손익: {month_profit:,.1f}원  "
            f"ROI: {month_roi:.3f}  "
            f"적중경주수: {m['hits']}  적중율: {month_hit_rate:.3f}  "
            f"r_pop1 3위내: {r_pop1_top3_rate:.3f}"
        )
    print("===================================")

    return race_df, summary


if __name__ == "__main__":
    from_date = "20250207"

    to_date = "20250209"


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
