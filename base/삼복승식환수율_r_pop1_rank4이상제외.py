import pymysql
import pandas as pd
from contextlib import closing

# =========================
# 0. DB 접속 설정 (필요에 맞게 수정)
# =========================
DB_CONF = {
    "host": "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",  # ★ 실제 DB 호스트로 수정
    "port": 3306,  # ★ 포트
    "user": "letslove",  # ★ 유저명
    "password": "Ruddksp!23",  # ★ 비밀번호
    "db": "The1",  # ★ DB명
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
        r.distance   AS 경주거리,   -- ★ 경주거리 추가
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
    df = pd.read_sql(sql, conn, params=[from_date, to_date])
    return df


# =========================
# 2. r_pop 상위6 → 4/5/6복조 + r_pop1 축(2~4) 환수 raw 계산
# =========================
def calc_top6_trifecta_raw(
    from_date: str,
    to_date: str,
    bet_unit: int = 100,  # 한 구멍당 베팅 금액 (원)
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
    - 각 경주에 대해 r_pop 기준 상위 6마리를
      4/5/6복조로 삼복승식 베팅했다고 가정.
    - 추가로 r_pop 1을 축으로 r_pop 2~4를 상대(2두 선택)로 삼복조 구성.
    - 실제 1~3위(r_rank 1~3)를 기준으로 적중 여부 판단.
    - 기준별( r_pop ) 환수금, ROI 계산.

    추가 컬럼:
      - 년월 : 경주일(YYYYMMDD) → YYYYMM
      - 신마수: 해당 경주에서 rank >= 98 인 말의 수
      - 경주거리: rec010.distance
    """
    with closing(get_conn()) as conn:
        df = load_result_data_from_db(conn, from_date=from_date, to_date=to_date)

    if df.empty:
        print(f"▶ [{from_date} ~ {to_date}] 기간 데이터가 없습니다.")
        return pd.DataFrame(), {}

    # 타입 정리
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

    # ★ 경주거리 숫자형 변환 (NULL 있으면 NaN -> 그대로 두고, 그룹 첫 값 사용)
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")

    # ★ 년월 컬럼 추가 (YYYYMMDD → YYYYMM)
    df["년월"] = df["경주일"].str.slice(0, 6)

    # ★ 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    # 복조 조합 수 (N마리 중 3마리)
    comb_by_n = {4: 4}
    # 케이스별 구멍당 베팅 금액
    bet_unit_by_n = {4: 1000}
    bet_unit_anchor = {
        "r_pop_anchor_234": 1000,
        "r_pop_anchor_25": 0,
        "r_pop_anchor_26": 0,
    }

    race_rows = []

    # 누적 합계용
    summary = {}
    for n in [4]:
        summary[f"r_pop_{n}"] = {
            "total_bet": 0.0,
            "total_refund": 0.0,
            "total_hits": 0,
        }
    summary["r_pop_anchor_234"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_anchor_25"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_anchor_26"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_top3_anchor_4_7"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_top4_anchor_5_8"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_1_2_anchor_3_8"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_1_2_anchor_3_5"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_1_2_anchor_3_4"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_1_2_anchor_3_7"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_1_2_anchor_3_6"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    total_races = 0
    a4_excluded_races = 0
    excluded_races = 0
    month_summary = {}
    bucket_summary = {
        "0~20": {"races": 0, "total_bet": 0.0, "total_refund": 0.0, "hits": 0},
        "21~50": {"races": 0, "total_bet": 0.0, "total_refund": 0.0, "hits": 0},
        "51~100": {"races": 0, "total_bet": 0.0, "total_refund": 0.0, "hits": 0},
        "100+": {"races": 0, "total_bet": 0.0, "total_refund": 0.0, "hits": 0},
    }

    # 경주 단위 루프
    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()

        # ▶ 년월, 경주거리, 신마수
        year_month = g["년월"].iloc[0]  # ★ 년월
        distance = g["경주거리"].iloc[0]  # ★ 경주거리
        if len(g) >= 13:
            excluded_races += 1
            continue
        new_cnt = int(g["신마"].sum())  # ★ 신마 수
        if new_cnt >= 2:
            excluded_races += 1
            continue
        total_races += 1

        # 실제 1~3위
        actual_top3 = g[g["r_rank"] <= 3]["마번"].tolist()
        actual_set = set(actual_top3)

        # 배당 (경주별 동일 가정)
        odds = (
            float(g["삼복승식배당율"].iloc[0])
            if not g["삼복승식배당율"].isna().all()
            else 0.0
        )

        # 각 기준별 처리
        result_per_basis = {}
        result_per_basis["r_pop"] = {}
        g_sorted = g.sort_values("r_pop", ascending=True)
        bet_per_race_4 = 0
        for n in [4]:
            topn = g_sorted.head(n)["마번"].tolist()
            topn_set = set(topn)
            unit = bet_unit_by_n[n]
            hit_flag = int(
                unit > 0 and bool(actual_set) and actual_set.issubset(topn_set)
            )
            refund = odds * unit if hit_flag == 1 else 0.0

            result_per_basis["r_pop"][n] = {
                "topn": topn,
                "hit": hit_flag,
                "refund": refund,
            }

            bet_per_race = comb_by_n[n] * unit
            if n == 4:
                bet_per_race_4 = bet_per_race
            summary[f"r_pop_{n}"]["total_bet"] += bet_per_race
            summary[f"r_pop_{n}"]["total_refund"] += refund
            summary[f"r_pop_{n}"]["total_hits"] += hit_flag

        # r_pop 1 축 + r_pop 2~4 중 2두 조합 (C(3,2)=3)
        anchor = g_sorted.head(1)["마번"].tolist()
        top234 = g_sorted.head(4)["마번"].tolist()[1:]
        anchor_gate = anchor[0] if anchor else None
        top234_set = set(top234)
        anchor_row = (
            g[g["마번"] == anchor_gate] if anchor_gate is not None else g.iloc[0:0]
        )
        anchor_rank = anchor_row.iloc[0]["rank"] if not anchor_row.empty else None
        anchor_block = False

        unit_anchor_234 = 0 if anchor_block else bet_unit_anchor["r_pop_anchor_234"]
        hit_anchor_234 = int(
            unit_anchor_234 > 0
            and len(actual_set) == 3
            and (anchor_gate is not None)
            and (anchor_gate in actual_set)
            and len(actual_set.intersection(top234_set)) == 2
        )
        refund_anchor_234 = odds * unit_anchor_234 if hit_anchor_234 == 1 else 0.0
        anchor_234_bet = 3 * unit_anchor_234
        summary["r_pop_anchor_234"]["total_bet"] += anchor_234_bet
        summary["r_pop_anchor_234"]["total_refund"] += refund_anchor_234
        summary["r_pop_anchor_234"]["total_hits"] += hit_anchor_234

        # r_pop 1 축 + r_pop 2~5 중 2두 조합 (C(4,2)=6)
        top25 = g_sorted.head(5)["마번"].tolist()[1:]
        top25_set = set(top25)
        unit_anchor_25 = 0 if anchor_block else bet_unit_anchor["r_pop_anchor_25"]
        hit_anchor_25 = int(
            unit_anchor_25 > 0
            and len(actual_set) == 3
            and (anchor_gate is not None)
            and (anchor_gate in actual_set)
            and actual_set.issubset({anchor_gate, *top25_set})
        )
        refund_anchor_25 = odds * unit_anchor_25 if hit_anchor_25 == 1 else 0.0
        anchor_25_bet = 6 * unit_anchor_25
        summary["r_pop_anchor_25"]["total_bet"] += anchor_25_bet
        summary["r_pop_anchor_25"]["total_refund"] += refund_anchor_25
        summary["r_pop_anchor_25"]["total_hits"] += hit_anchor_25

        # r_pop 1 축 + r_pop 2~6 중 2두 조합 (C(5,2)=10)
        top26 = g_sorted.head(6)["마번"].tolist()[1:]
        top26_set = set(top26)
        unit_anchor_26 = 0 if anchor_block else bet_unit_anchor["r_pop_anchor_26"]
        hit_anchor_26 = int(
            unit_anchor_26 > 0
            and len(actual_set) == 3
            and (anchor_gate is not None)
            and (anchor_gate in actual_set)
            and actual_set.issubset({anchor_gate, *top26_set})
        )
        refund_anchor_26 = odds * unit_anchor_26 if hit_anchor_26 == 1 else 0.0
        anchor_26_bet = 10 * unit_anchor_26
        summary["r_pop_anchor_26"]["total_bet"] += anchor_26_bet
        summary["r_pop_anchor_26"]["total_refund"] += refund_anchor_26
        summary["r_pop_anchor_26"]["total_hits"] += hit_anchor_26

        # r_pop 1~3 중 2두 + r_pop 4~7 중 1두 조합 (C(3,2)*4=12)
        top3 = g_sorted.head(3)["마번"].tolist()
        top3_set = set(top3)
        top4_7 = g_sorted.iloc[3:7]["마번"].tolist()
        top4_7_set = set(top4_7)
        unit_top3_anchor_4_7 = 0
        hit_top3_anchor_4_7 = int(
            unit_top3_anchor_4_7 > 0
            and len(actual_set) == 3
            and len(actual_set.intersection(top3_set)) == 2
            and len(actual_set.intersection(top4_7_set)) == 1
        )
        refund_top3_anchor_4_7 = (
            odds * unit_top3_anchor_4_7 if hit_top3_anchor_4_7 == 1 else 0.0
        )
        top3_anchor_4_7_bet = 12 * unit_top3_anchor_4_7
        summary["r_pop_top3_anchor_4_7"]["total_bet"] += top3_anchor_4_7_bet
        summary["r_pop_top3_anchor_4_7"]["total_refund"] += refund_top3_anchor_4_7
        summary["r_pop_top3_anchor_4_7"]["total_hits"] += hit_top3_anchor_4_7

        # r_pop 1~4 중 2두 + r_pop 5~8 중 1두 조합 (C(4,2)*4=24)
        top4 = g_sorted.head(4)["마번"].tolist()
        top4_set = set(top4)
        top5_8 = g_sorted.iloc[4:8]["마번"].tolist()
        top5_8_set = set(top5_8)
        unit_top4_anchor_5_8 = 0
        hit_top4_anchor_5_8 = int(
            unit_top4_anchor_5_8 > 0
            and len(actual_set) == 3
            and len(actual_set.intersection(top4_set)) == 2
            and len(actual_set.intersection(top5_8_set)) == 1
        )
        refund_top4_anchor_5_8 = (
            odds * unit_top4_anchor_5_8 if hit_top4_anchor_5_8 == 1 else 0.0
        )
        top4_anchor_5_8_bet = 24 * unit_top4_anchor_5_8
        summary["r_pop_top4_anchor_5_8"]["total_bet"] += top4_anchor_5_8_bet
        summary["r_pop_top4_anchor_5_8"]["total_refund"] += refund_top4_anchor_5_8
        summary["r_pop_top4_anchor_5_8"]["total_hits"] += hit_top4_anchor_5_8

        # r_pop 1~2 고정 + r_pop 3~8 중 1두 조합 (6구멍)
        top2 = g_sorted.head(2)["마번"].tolist()
        top2_set = set(top2)
        top3_8 = g_sorted.iloc[2:8]["마번"].tolist()
        top3_8_set = set(top3_8)
        unit_top2_anchor_3_8 = 0
        hit_top2_anchor_3_8 = int(
            unit_top2_anchor_3_8 > 0
            and len(actual_set) == 3
            and top2_set.issubset(actual_set)
            and len(actual_set.intersection(top3_8_set)) == 1
        )
        refund_top2_anchor_3_8 = (
            odds * unit_top2_anchor_3_8 if hit_top2_anchor_3_8 == 1 else 0.0
        )
        top2_anchor_3_8_bet = 6 * unit_top2_anchor_3_8
        summary["r_pop_1_2_anchor_3_8"]["total_bet"] += top2_anchor_3_8_bet
        summary["r_pop_1_2_anchor_3_8"]["total_refund"] += refund_top2_anchor_3_8
        summary["r_pop_1_2_anchor_3_8"]["total_hits"] += hit_top2_anchor_3_8

        # r_pop 1~2 고정 + r_pop 3~5 중 1두 조합 (3구멍)
        top3_5 = g_sorted.iloc[2:5]["마번"].tolist()
        top3_5_set = set(top3_5)
        unit_top2_anchor_3_5 = 0
        hit_top2_anchor_3_5 = int(
            unit_top2_anchor_3_5 > 0
            and len(actual_set) == 3
            and top2_set.issubset(actual_set)
            and len(actual_set.intersection(top3_5_set)) == 1
        )
        refund_top2_anchor_3_5 = (
            odds * unit_top2_anchor_3_5 if hit_top2_anchor_3_5 == 1 else 0.0
        )
        top2_anchor_3_5_bet = 3 * unit_top2_anchor_3_5
        summary["r_pop_1_2_anchor_3_5"]["total_bet"] += top2_anchor_3_5_bet
        summary["r_pop_1_2_anchor_3_5"]["total_refund"] += refund_top2_anchor_3_5
        summary["r_pop_1_2_anchor_3_5"]["total_hits"] += hit_top2_anchor_3_5

        # r_pop 1~2 고정 + r_pop 3~4 중 1두 조합 (2구멍)
        top3_4 = g_sorted.iloc[2:4]["마번"].tolist()
        top3_4_set = set(top3_4)
        unit_top2_anchor_3_4 = 0
        hit_top2_anchor_3_4 = int(
            unit_top2_anchor_3_4 > 0
            and len(actual_set) == 3
            and top2_set.issubset(actual_set)
            and len(actual_set.intersection(top3_4_set)) == 1
        )
        refund_top2_anchor_3_4 = (
            odds * unit_top2_anchor_3_4 if hit_top2_anchor_3_4 == 1 else 0.0
        )
        top2_anchor_3_4_bet = 2 * unit_top2_anchor_3_4
        summary["r_pop_1_2_anchor_3_4"]["total_bet"] += top2_anchor_3_4_bet
        summary["r_pop_1_2_anchor_3_4"]["total_refund"] += refund_top2_anchor_3_4
        summary["r_pop_1_2_anchor_3_4"]["total_hits"] += hit_top2_anchor_3_4

        # r_pop 1~2 고정 + r_pop 3~7 중 1두 조합 (5구멍)
        top3_7 = g_sorted.iloc[2:7]["마번"].tolist()
        top3_7_set = set(top3_7)
        unit_top2_anchor_3_7 = 0
        hit_top2_anchor_3_7 = int(
            unit_top2_anchor_3_7 > 0
            and len(actual_set) == 3
            and top2_set.issubset(actual_set)
            and len(actual_set.intersection(top3_7_set)) == 1
        )
        refund_top2_anchor_3_7 = (
            odds * unit_top2_anchor_3_7 if hit_top2_anchor_3_7 == 1 else 0.0
        )
        top2_anchor_3_7_bet = 5 * unit_top2_anchor_3_7
        summary["r_pop_1_2_anchor_3_7"]["total_bet"] += top2_anchor_3_7_bet
        summary["r_pop_1_2_anchor_3_7"]["total_refund"] += refund_top2_anchor_3_7
        summary["r_pop_1_2_anchor_3_7"]["total_hits"] += hit_top2_anchor_3_7

        # r_pop 1~2 고정 + r_pop 3~6 중 1두 조합 (4구멍)
        top3_6 = g_sorted.iloc[2:6]["마번"].tolist()
        top3_6_set = set(top3_6)
        unit_top2_anchor_3_6 = 0
        hit_top2_anchor_3_6 = int(
            unit_top2_anchor_3_6 > 0
            and len(actual_set) == 3
            and top2_set.issubset(actual_set)
            and len(actual_set.intersection(top3_6_set)) == 1
        )
        refund_top2_anchor_3_6 = (
            odds * unit_top2_anchor_3_6 if hit_top2_anchor_3_6 == 1 else 0.0
        )
        top2_anchor_3_6_bet = 4 * unit_top2_anchor_3_6
        summary["r_pop_1_2_anchor_3_6"]["total_bet"] += top2_anchor_3_6_bet
        summary["r_pop_1_2_anchor_3_6"]["total_refund"] += refund_top2_anchor_3_6
        summary["r_pop_1_2_anchor_3_6"]["total_hits"] += hit_top2_anchor_3_6

        total_bet_race = (
            bet_per_race_4
            + anchor_234_bet
            + anchor_25_bet
            + anchor_26_bet
            + top3_anchor_4_7_bet
            + top4_anchor_5_8_bet
            + top2_anchor_3_8_bet
            + top2_anchor_3_5_bet
            + top2_anchor_3_4_bet
            + top2_anchor_3_7_bet
            + top2_anchor_3_6_bet
        )
        total_refund_race = (
            result_per_basis["r_pop"][4]["refund"]
            + refund_anchor_234
            + refund_anchor_25
            + refund_anchor_26
            + refund_top3_anchor_4_7
            + refund_top4_anchor_5_8
            + refund_top2_anchor_3_8
            + refund_top2_anchor_3_5
            + refund_top2_anchor_3_4
            + refund_top2_anchor_3_7
            + refund_top2_anchor_3_6
        )
        hit_any = int(
            result_per_basis["r_pop"][4]["hit"]
            or hit_anchor_234
            or hit_anchor_25
            or hit_anchor_26
            or hit_top3_anchor_4_7
            or hit_top4_anchor_5_8
            or hit_top2_anchor_3_8
            or hit_top2_anchor_3_5
            or hit_top2_anchor_3_4
            or hit_top2_anchor_3_7
            or hit_top2_anchor_3_6
        )
        if year_month not in month_summary:
            month_summary[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
            }
        month_summary[year_month]["races"] += 1
        month_summary[year_month]["total_bet"] += total_bet_race
        month_summary[year_month]["total_refund"] += total_refund_race
        if odds <= 20:
            bucket = "0~20"
        elif odds <= 50:
            bucket = "21~50"
        elif odds <= 100:
            bucket = "51~100"
        else:
            bucket = "100+"
        bucket_summary[bucket]["races"] += 1
        bucket_summary[bucket]["total_bet"] += total_bet_race
        bucket_summary[bucket]["total_refund"] += total_refund_race
        bucket_summary[bucket]["hits"] += (
            result_per_basis["r_pop"][4]["hit"]
            + hit_anchor_234
            + hit_anchor_25
            + hit_anchor_26
            + hit_top3_anchor_4_7
            + hit_top4_anchor_5_8
            + hit_top2_anchor_3_8
            + hit_top2_anchor_3_5
            + hit_top2_anchor_3_4
            + hit_top2_anchor_3_7
            + hit_top2_anchor_3_6
        )

        # 경주별 raw row 구성
        race_rows.append(
            {
                "년월": year_month,  # ★ 추가
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "경주거리": distance,  # ★ 추가
                "신마수": new_cnt,  # ★ 추가
                # 실제 1~3위
                "실제_top3_마번": (
                    ",".join(map(str, sorted(actual_set))) if actual_set else ""
                ),
                # 기준별 1~4/5/6위 마번 목록
                "r_pop_top4_마번": ",".join(
                    map(str, result_per_basis["r_pop"][4]["topn"])
                ),
                # 기준별 적중/환수
                "r_pop4_적중": result_per_basis["r_pop"][4]["hit"],
                "r_pop4_환수금": result_per_basis["r_pop"][4]["refund"],
                "r_pop1_축_마번": anchor_gate if anchor_gate is not None else "",
                "r_pop2_마번": top234[0] if len(top234) > 0 else "",
                "r_pop3_마번": top234[1] if len(top234) > 1 else "",
                "r_pop4_마번": top234[2] if len(top234) > 2 else "",
                "A4_베팅제외": 0,
                "r_pop1_축_234_적중": hit_anchor_234,
                "r_pop1_축_234_환수금": refund_anchor_234,
                "r_pop1_축_25_적중": hit_anchor_25,
                "r_pop1_축_25_환수금": refund_anchor_25,
                "r_pop1_축_26_적중": hit_anchor_26,
                "r_pop1_축_26_환수금": refund_anchor_26,
                "r_pop1~3_축_4~7_적중": hit_top3_anchor_4_7,
                "r_pop1~3_축_4~7_환수금": refund_top3_anchor_4_7,
                "r_pop1~4_축_5~8_적중": hit_top4_anchor_5_8,
                "r_pop1~4_축_5~8_환수금": refund_top4_anchor_5_8,
                "r_pop1~2_축_3~8_적중": hit_top2_anchor_3_8,
                "r_pop1~2_축_3~8_환수금": refund_top2_anchor_3_8,
                "r_pop1~2_축_3~5_적중": hit_top2_anchor_3_5,
                "r_pop1~2_축_3~5_환수금": refund_top2_anchor_3_5,
                "r_pop1~2_축_3~4_적중": hit_top2_anchor_3_4,
                "r_pop1~2_축_3~4_환수금": refund_top2_anchor_3_4,
                "r_pop1~2_축_3~7_적중": hit_top2_anchor_3_7,
                "r_pop1~2_축_3~7_환수금": refund_top2_anchor_3_7,
                "r_pop1~2_축_3~6_적중": hit_top2_anchor_3_6,
                "r_pop1~2_축_3~6_환수금": refund_top2_anchor_3_6,
                "총베팅액": total_bet_race,
                "총환급금": total_refund_race,
                "적중여부": hit_any,
                # 공통 베팅 정보
                "4복조_조합수": comb_by_n[4],
                "r_pop1_축_234_조합수": 3,
                "r_pop1_축_25_조합수": 6,
                "r_pop1_축_26_조합수": 10,
                "r_pop1~3_축_4~7_조합수": 12,
                "r_pop1~4_축_5~8_조합수": 24,
                "r_pop1~2_축_3~8_조합수": 6,
                "r_pop1~2_축_3~5_조합수": 3,
                "r_pop1~2_축_3~4_조합수": 2,
                "r_pop1~2_축_3~7_조합수": 5,
                "r_pop1~2_축_3~6_조합수": 4,
                "r_pop4_베팅금액": comb_by_n[4] * bet_unit_by_n[4],
                "r_pop1_축_234_베팅금액": 3 * bet_unit_anchor["r_pop_anchor_234"],
                "r_pop1_축_25_베팅금액": 6 * bet_unit_anchor["r_pop_anchor_25"],
                "r_pop1_축_26_베팅금액": 10 * bet_unit_anchor["r_pop_anchor_26"],
                "r_pop1~3_축_4~7_베팅금액": top3_anchor_4_7_bet,
                "r_pop1~4_축_5~8_베팅금액": top4_anchor_5_8_bet,
                "r_pop1~2_축_3~8_베팅금액": top2_anchor_3_8_bet,
                "r_pop1~2_축_3~5_베팅금액": top2_anchor_3_5_bet,
                "r_pop1~2_축_3~4_베팅금액": top2_anchor_3_4_bet,
                "r_pop1~2_축_3~7_베팅금액": top2_anchor_3_7_bet,
                "r_pop1~2_축_3~6_베팅금액": top2_anchor_3_6_bet,
                "구멍당_베팅금액": bet_unit,
                "삼복승식배당율": odds,
            }
        )

    race_df = pd.DataFrame(race_rows)

    # 기준별 ROI 계산
    for n in [4]:
        key = f"r_pop_{n}"
        total_bet = summary[key]["total_bet"]
        total_refund = summary[key]["total_refund"]
        roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
        summary[key]["roi"] = roi
        summary[key]["hit_rate"] = (
            summary[key]["total_hits"] / total_races if total_races > 0 else 0.0
        )
    total_bet = summary["r_pop_anchor_234"]["total_bet"]
    total_refund = summary["r_pop_anchor_234"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_anchor_234"]["roi"] = roi
    summary["r_pop_anchor_234"]["hit_rate"] = (
        summary["r_pop_anchor_234"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_anchor_25"]["total_bet"]
    total_refund = summary["r_pop_anchor_25"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_anchor_25"]["roi"] = roi
    summary["r_pop_anchor_25"]["hit_rate"] = (
        summary["r_pop_anchor_25"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_anchor_26"]["total_bet"]
    total_refund = summary["r_pop_anchor_26"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_anchor_26"]["roi"] = roi
    summary["r_pop_anchor_26"]["hit_rate"] = (
        summary["r_pop_anchor_26"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_top3_anchor_4_7"]["total_bet"]
    total_refund = summary["r_pop_top3_anchor_4_7"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_top3_anchor_4_7"]["roi"] = roi
    summary["r_pop_top3_anchor_4_7"]["hit_rate"] = (
        summary["r_pop_top3_anchor_4_7"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_top4_anchor_5_8"]["total_bet"]
    total_refund = summary["r_pop_top4_anchor_5_8"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_top4_anchor_5_8"]["roi"] = roi
    summary["r_pop_top4_anchor_5_8"]["hit_rate"] = (
        summary["r_pop_top4_anchor_5_8"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_1_2_anchor_3_8"]["total_bet"]
    total_refund = summary["r_pop_1_2_anchor_3_8"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_1_2_anchor_3_8"]["roi"] = roi
    summary["r_pop_1_2_anchor_3_8"]["hit_rate"] = (
        summary["r_pop_1_2_anchor_3_8"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_1_2_anchor_3_5"]["total_bet"]
    total_refund = summary["r_pop_1_2_anchor_3_5"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_1_2_anchor_3_5"]["roi"] = roi
    summary["r_pop_1_2_anchor_3_5"]["hit_rate"] = (
        summary["r_pop_1_2_anchor_3_5"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_1_2_anchor_3_4"]["total_bet"]
    total_refund = summary["r_pop_1_2_anchor_3_4"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_1_2_anchor_3_4"]["roi"] = roi
    summary["r_pop_1_2_anchor_3_4"]["hit_rate"] = (
        summary["r_pop_1_2_anchor_3_4"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_1_2_anchor_3_7"]["total_bet"]
    total_refund = summary["r_pop_1_2_anchor_3_7"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_1_2_anchor_3_7"]["roi"] = roi
    summary["r_pop_1_2_anchor_3_7"]["hit_rate"] = (
        summary["r_pop_1_2_anchor_3_7"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_1_2_anchor_3_6"]["total_bet"]
    total_refund = summary["r_pop_1_2_anchor_3_6"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_1_2_anchor_3_6"]["roi"] = roi
    summary["r_pop_1_2_anchor_3_6"]["hit_rate"] = (
        summary["r_pop_1_2_anchor_3_6"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    # 결과 출력
    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    print(
        f"경주수: {total_races}  제외(신마 2두 이상): {excluded_races}  "
        f"A4_베팅제외: {a4_excluded_races}"
    )
    total_bet_all = (
        summary["r_pop_4"]["total_bet"]
        + summary["r_pop_anchor_234"]["total_bet"]
        + summary["r_pop_anchor_25"]["total_bet"]
        + summary["r_pop_anchor_26"]["total_bet"]
        + summary["r_pop_top3_anchor_4_7"]["total_bet"]
        + summary["r_pop_top4_anchor_5_8"]["total_bet"]
        + summary["r_pop_1_2_anchor_3_8"]["total_bet"]
        + summary["r_pop_1_2_anchor_3_5"]["total_bet"]
        + summary["r_pop_1_2_anchor_3_4"]["total_bet"]
        + summary["r_pop_1_2_anchor_3_7"]["total_bet"]
        + summary["r_pop_1_2_anchor_3_6"]["total_bet"]
    )
    total_refund_all = (
        summary["r_pop_4"]["total_refund"]
        + summary["r_pop_anchor_234"]["total_refund"]
        + summary["r_pop_anchor_25"]["total_refund"]
        + summary["r_pop_anchor_26"]["total_refund"]
        + summary["r_pop_top3_anchor_4_7"]["total_refund"]
        + summary["r_pop_top4_anchor_5_8"]["total_refund"]
        + summary["r_pop_1_2_anchor_3_8"]["total_refund"]
        + summary["r_pop_1_2_anchor_3_5"]["total_refund"]
        + summary["r_pop_1_2_anchor_3_4"]["total_refund"]
        + summary["r_pop_1_2_anchor_3_7"]["total_refund"]
        + summary["r_pop_1_2_anchor_3_6"]["total_refund"]
    )
    total_refund_rate = total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
    print(
        f"[총 환수율]  총베팅액: {int(total_bet_all):,}원  "
        f"총환수액: {total_refund_all:,.1f}원  환수율: {total_refund_rate:.3f}"
    )
    for n in [4]:
        s = summary[f"r_pop_{n}"]
        print(
            f"[예상순위(r_pop) - {n}복조]  적중율: {s['hit_rate']:.3f}  "
            f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
        )
    s = summary["r_pop_anchor_234"]
    print(
        f"[예상순위(r_pop) - 1축(2~4) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_anchor_25"]
    print(
        f"[예상순위(r_pop) - 1축(2~5) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_anchor_26"]
    print(
        f"[예상순위(r_pop) - 1축(2~6) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_top3_anchor_4_7"]
    print(
        f"[예상순위(r_pop) - 1~3축(4~7) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_top4_anchor_5_8"]
    print(
        f"[예상순위(r_pop) - 1~4축(5~8) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_1_2_anchor_3_8"]
    print(
        f"[예상순위(r_pop) - 1~2축(3~8) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_1_2_anchor_3_5"]
    print(
        f"[예상순위(r_pop) - 1~2축(3~5) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_1_2_anchor_3_4"]
    print(
        f"[예상순위(r_pop) - 1~2축(3~4) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_1_2_anchor_3_7"]
    print(
        f"[예상순위(r_pop) - 1~2축(3~7) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    s = summary["r_pop_1_2_anchor_3_6"]
    print(
        f"[예상순위(r_pop) - 1~2축(3~6) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
    )
    for ym in sorted(month_summary.keys()):
        m = month_summary[ym]
        refund_rate = m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        print(
            f"[월별 환수율 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {refund_rate:.3f}"
        )
    for label in ["0~20", "21~50", "51~100", "100+"]:
        b = bucket_summary[label]
        refund_rate = b["total_refund"] / b["total_bet"] if b["total_bet"] > 0 else 0.0
        hit_rate = b["hits"] / b["races"] if b["races"] > 0 else 0.0
        print(
            f"[배당율 {label}]  경주수: {b['races']}  "
            f"총베팅액: {int(b['total_bet']):,}원  총환수액: {b['total_refund']:,.1f}원  "
            f"환수율: {refund_rate:.3f}  적중율: {hit_rate:.3f}"
        )
    print("===================================")

    return race_df, summary


# =========================
# 3. 예시 실행
# =========================
if __name__ == "__main__":
    # 예시: 2023-12-01 ~ 2025-11-30
    from_date = "20231201"

    to_date = "20251231"

    race_df, summary = calc_top6_trifecta_raw(
        from_date=from_date,
        to_date=to_date,
        bet_unit=1000,  # 한 구멍당 1000원
    )

    # raw 데이터 CSV 저장 (원하면 경로만 바꿔서 사용)
    out_path = "/Users/Super007/Documents/r_pop_reward_rank4.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
        summary_cols = [
            "경마장",
            "경주일",
            "경주번호",
            "총베팅액",
            "총환급금",
            "적중여부",
            "삼복승식배당율",
        ]
        summary_cols = [c for c in summary_cols if c in race_df.columns]
        race_summary_df = race_df[summary_cols].copy()
        summary_out_path = "/Users/Super007/Documents/r_pop_race_summary.csv"
        race_summary_df.to_csv(summary_out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 요약 CSV 저장: {summary_out_path}")
