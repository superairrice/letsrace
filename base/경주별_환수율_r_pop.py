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
        CAST(r.r333alloc1 AS DECIMAL(10, 1)) AS 삼복승식배당율,
        CAST(r.r2alloc1 AS DECIMAL(10, 1)) AS 복승식배당율
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
    df["복승식배당율"] = df["복승식배당율"].astype(float)

    # ★ 경주거리 숫자형 변환 (NULL 있으면 NaN -> 그대로 두고, 그룹 첫 값 사용)
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")

    # ★ 년월 컬럼 추가 (YYYYMMDD → YYYYMM)
    df["년월"] = df["경주일"].str.slice(0, 6)

    # ★ 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    # 복조 조합 수 (N마리 중 3마리)
    comb_by_n = {4: 4, 5: 10, 6: 20}
    # 케이스별 구멍당 베팅 금액
    bet_unit_by_n = {4: 500, 5: 0, 6: 0}
    bet_unit_anchor = {
        "r_pop_anchor_234": 500,
        "r_pop_anchor_25": 300,
        "r_pop_anchor_26": 300,
        "r_pop_anchor_27": 0,
    }
    exacta_anchor_24_unit = 500

    race_rows = []

    # 누적 합계용
    summary = {}
    for n in [4, 5, 6]:
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
    summary["r_pop_anchor_27"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop_exacta_anchor_24"] = {
        "total_bet": 0.0,
        "total_refund": 0.0,
        "total_hits": 0,
    }
    summary["r_pop1_ge4_r_pop2_top3"] = {"races": 0, "hits": 0}
    summary["r_pop12_ge4_r_pop3_top3"] = {"races": 0, "hits": 0}
    total_races = 0
    excluded_races = 0
    month_summary = {}
    bucket_summary = {
        "0~20": {"races": 0, "total_bet": 0.0, "total_refund": 0.0, "hits": 0},
        "21~50": {"races": 0, "total_bet": 0.0, "total_refund": 0.0, "hits": 0},
        "51~100": {"races": 0, "total_bet": 0.0, "total_refund": 0.0, "hits": 0},
        "100+": {"races": 0, "total_bet": 0.0, "total_refund": 0.0, "hits": 0},
    }
    track_grade_distance_summary = {}

    # 경주 단위 루프
    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()

        # ▶ 년월, 경주거리, 신마수
        year_month = g["년월"].iloc[0]  # ★ 년월
        distance = g["경주거리"].iloc[0]  # ★ 경주거리
        grade = (g["등급"].iloc[0] or "").strip()
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
        # 실제 1~2위 (복승식)
        actual_top2 = g[g["r_rank"] <= 2]["마번"].tolist()
        actual_set_2 = set(actual_top2)

        # 배당 (경주별 동일 가정)
        odds = (
            float(g["삼복승식배당율"].iloc[0])
            if not g["삼복승식배당율"].isna().all()
            else 0.0
        )
        odds_exacta = (
            float(g["복승식배당율"].iloc[0])
            if not g["복승식배당율"].isna().all()
            else 0.0
        )

        # 각 기준별 처리
        result_per_basis = {}
        result_per_basis["r_pop"] = {}
        g_sorted = g.sort_values("r_pop", ascending=True)
        r_pop1_gate = g_sorted.head(1)["마번"].iloc[0] if not g_sorted.empty else None
        top3_candidates = g_sorted.head(3)["마번"].tolist()
        r_pop2_gate = top3_candidates[1] if len(top3_candidates) >= 2 else None
        r_pop3_gate = top3_candidates[2] if len(top3_candidates) >= 3 else None
        bet_per_race_4 = 0
        bet_per_race_5 = 0
        for n in [4, 5, 6]:
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
            if n == 5:
                bet_per_race_5 = bet_per_race
            summary[f"r_pop_{n}"]["total_bet"] += bet_per_race
            summary[f"r_pop_{n}"]["total_refund"] += refund
            summary[f"r_pop_{n}"]["total_hits"] += hit_flag

        # r_pop 1 축 + r_pop 2~4 중 2두 조합 (C(3,2)=3)
        anchor = g_sorted.head(1)["마번"].tolist()
        top234 = g_sorted.head(4)["마번"].tolist()[1:]
        anchor_gate = anchor[0] if anchor else None
        top234_set = set(top234)
        unit_anchor_234 = bet_unit_anchor["r_pop_anchor_234"]
        hit_anchor_234 = int(
            unit_anchor_234 > 0
            and bool(actual_set)
            and (anchor_gate is not None)
            and (anchor_gate in actual_set)
            and actual_set.issubset({anchor_gate, *top234_set})
        )
        refund_anchor_234 = odds * unit_anchor_234 if hit_anchor_234 == 1 else 0.0
        anchor_234_bet = 3 * unit_anchor_234
        summary["r_pop_anchor_234"]["total_bet"] += anchor_234_bet
        summary["r_pop_anchor_234"]["total_refund"] += refund_anchor_234
        summary["r_pop_anchor_234"]["total_hits"] += hit_anchor_234

        # r_pop 1 축 + r_pop 2~5 중 2두 조합 (C(4,2)=6)
        top25 = g_sorted.head(5)["마번"].tolist()[1:]
        top25_set = set(top25)
        unit_anchor_25 = bet_unit_anchor["r_pop_anchor_25"]
        hit_anchor_25 = int(
            unit_anchor_25 > 0
            and bool(actual_set)
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
        unit_anchor_26 = bet_unit_anchor["r_pop_anchor_26"]
        hit_anchor_26 = int(
            unit_anchor_26 > 0
            and bool(actual_set)
            and (anchor_gate is not None)
            and (anchor_gate in actual_set)
            and actual_set.issubset({anchor_gate, *top26_set})
        )
        refund_anchor_26 = odds * unit_anchor_26 if hit_anchor_26 == 1 else 0.0
        anchor_26_bet = 10 * unit_anchor_26
        summary["r_pop_anchor_26"]["total_bet"] += anchor_26_bet
        summary["r_pop_anchor_26"]["total_refund"] += refund_anchor_26
        summary["r_pop_anchor_26"]["total_hits"] += hit_anchor_26

        # r_pop 1 축 + r_pop 2~7 중 2두 조합 (C(6,2)=15)
        top27 = g_sorted.head(7)["마번"].tolist()[1:]
        top27_set = set(top27)
        unit_anchor_27 = bet_unit_anchor["r_pop_anchor_27"]
        hit_anchor_27 = int(
            unit_anchor_27 > 0
            and bool(actual_set)
            and (anchor_gate is not None)
            and (anchor_gate in actual_set)
            and actual_set.issubset({anchor_gate, *top27_set})
        )
        refund_anchor_27 = odds * unit_anchor_27 if hit_anchor_27 == 1 else 0.0
        anchor_27_bet = 15 * unit_anchor_27
        summary["r_pop_anchor_27"]["total_bet"] += anchor_27_bet
        summary["r_pop_anchor_27"]["total_refund"] += refund_anchor_27
        summary["r_pop_anchor_27"]["total_hits"] += hit_anchor_27
        # 복승식 1축 2~4
        hit_exacta_24 = int(
            exacta_anchor_24_unit > 0
            and bool(actual_set_2)
            and (anchor_gate is not None)
            and (anchor_gate in actual_set_2)
            and actual_set_2.issubset({anchor_gate, *top234_set})
        )
        refund_exacta_24 = (
            odds_exacta * exacta_anchor_24_unit if hit_exacta_24 == 1 else 0.0
        )
        exacta_24_bet = 3 * exacta_anchor_24_unit
        summary["r_pop_exacta_anchor_24"]["total_bet"] += exacta_24_bet
        summary["r_pop_exacta_anchor_24"]["total_refund"] += refund_exacta_24
        summary["r_pop_exacta_anchor_24"]["total_hits"] += hit_exacta_24
        if r_pop1_gate is not None:
            r_pop1_rank = g.loc[g["마번"] == r_pop1_gate, "r_rank"]
            if not r_pop1_rank.empty and int(r_pop1_rank.iloc[0]) >= 4:
                summary["r_pop1_ge4_r_pop2_top3"]["races"] += 1
                if r_pop2_gate is not None:
                    r_pop2_rank = g.loc[g["마번"] == r_pop2_gate, "r_rank"]
                    if not r_pop2_rank.empty and int(r_pop2_rank.iloc[0]) <= 3:
                        summary["r_pop1_ge4_r_pop2_top3"]["hits"] += 1
            if r_pop2_gate is not None:
                r_pop2_rank = g.loc[g["마번"] == r_pop2_gate, "r_rank"]
                if not r_pop2_rank.empty and int(r_pop2_rank.iloc[0]) >= 4:
                    summary["r_pop12_ge4_r_pop3_top3"]["races"] += 1
                    if r_pop3_gate is not None:
                        r_pop3_rank = g.loc[g["마번"] == r_pop3_gate, "r_rank"]
                        if not r_pop3_rank.empty and int(r_pop3_rank.iloc[0]) <= 3:
                            summary["r_pop12_ge4_r_pop3_top3"]["hits"] += 1
        total_bet_race = bet_per_race_4 + anchor_234_bet + anchor_25_bet + anchor_26_bet
        total_refund_race = (
            result_per_basis["r_pop"][4]["refund"]
            + refund_anchor_234
            + refund_anchor_25
            + refund_anchor_26
        )
        total_bet_race_with_exacta = total_bet_race + exacta_24_bet
        total_refund_race_with_exacta = total_refund_race + refund_exacta_24
        hit_any = int(
            result_per_basis["r_pop"][4]["hit"]
            or hit_anchor_234
            or hit_anchor_25
            or hit_anchor_26
        )
        hit_any_with_exacta = int(hit_any or hit_exacta_24)
        if year_month not in month_summary:
            month_summary[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
            }
        month_summary[year_month]["races"] += 1
        month_summary[year_month]["total_bet"] += total_bet_race_with_exacta
        month_summary[year_month]["total_refund"] += total_refund_race_with_exacta
        if odds <= 20:
            bucket = "0~20"
        elif odds <= 50:
            bucket = "21~50"
        elif odds <= 100:
            bucket = "51~100"
        else:
            bucket = "100+"
        bucket_summary[bucket]["races"] += 1
        bucket_summary[bucket]["total_bet"] += total_bet_race_with_exacta
        bucket_summary[bucket]["total_refund"] += total_refund_race_with_exacta
        bucket_summary[bucket]["hits"] += hit_any_with_exacta
        tgd_key = (track, grade, distance)
        if tgd_key not in track_grade_distance_summary:
            track_grade_distance_summary[tgd_key] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        track_grade_distance_summary[tgd_key]["races"] += 1
        track_grade_distance_summary[tgd_key]["total_bet"] += total_bet_race_with_exacta
        track_grade_distance_summary[tgd_key]["total_refund"] += total_refund_race_with_exacta
        track_grade_distance_summary[tgd_key]["hits"] += hit_any_with_exacta

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
                "r_pop_top5_마번": ",".join(
                    map(str, result_per_basis["r_pop"][5]["topn"])
                ),
                "r_pop_top6_마번": ",".join(
                    map(str, result_per_basis["r_pop"][6]["topn"])
                ),
                # 기준별 적중/환수
                "r_pop4_적중": result_per_basis["r_pop"][4]["hit"],
                "r_pop4_환수금": result_per_basis["r_pop"][4]["refund"],
                "r_pop5_적중": result_per_basis["r_pop"][5]["hit"],
                "r_pop5_환수금": result_per_basis["r_pop"][5]["refund"],
                "r_pop6_적중": result_per_basis["r_pop"][6]["hit"],
                "r_pop6_환수금": result_per_basis["r_pop"][6]["refund"],
                "r_pop1_축_마번": anchor_gate if anchor_gate is not None else "",
                "r_pop2_마번": top234[0] if len(top234) > 0 else "",
                "r_pop3_마번": top234[1] if len(top234) > 1 else "",
                "r_pop4_마번": top234[2] if len(top234) > 2 else "",
                "r_pop1_축_234_적중": hit_anchor_234,
                "r_pop1_축_234_환수금": refund_anchor_234,
                "r_pop1_축_25_적중": hit_anchor_25,
                "r_pop1_축_25_환수금": refund_anchor_25,
                "r_pop1_축_26_적중": hit_anchor_26,
                "r_pop1_축_26_환수금": refund_anchor_26,
                "r_pop1_축_27_적중": hit_anchor_27,
                "r_pop1_축_27_환수금": refund_anchor_27,
                "r_pop1_축_2_4_복승_적중": hit_exacta_24,
                "r_pop1_축_2_4_복승_환수금": refund_exacta_24,
                # 공통 베팅 정보
                "4복조_조합수": comb_by_n[4],
                "5복조_조합수": comb_by_n[5],
                "6복조_조합수": comb_by_n[6],
                "r_pop1_축_234_조합수": 3,
                "r_pop1_축_25_조합수": 6,
                "r_pop1_축_26_조합수": 10,
                "r_pop1_축_27_조합수": 15,
                "r_pop4_베팅금액": comb_by_n[4] * bet_unit_by_n[4],
                "r_pop5_베팅금액": comb_by_n[5] * bet_unit_by_n[5],
                "r_pop6_베팅금액": comb_by_n[6] * bet_unit_by_n[6],
                "r_pop1_축_234_베팅금액": 3 * bet_unit_anchor["r_pop_anchor_234"],
                "r_pop1_축_25_베팅금액": 6 * bet_unit_anchor["r_pop_anchor_25"],
                "r_pop1_축_26_베팅금액": 10 * bet_unit_anchor["r_pop_anchor_26"],
                "r_pop1_축_27_베팅금액": 15 * bet_unit_anchor["r_pop_anchor_27"],
                "r_pop1_축_2_4_복승_베팅금액": 3 * exacta_anchor_24_unit,
                "총베팅액": total_bet_race_with_exacta,
                "총환급금": total_refund_race_with_exacta,
                "적중여부": hit_any_with_exacta,
                "구멍당_베팅금액": bet_unit,
                "삼복승식배당율": odds,
                "복승식배당율": odds_exacta,
            }
        )

    race_df = pd.DataFrame(race_rows)
    monthly_report = pd.DataFrame()
    if not race_df.empty:
        month_check = (
            race_df.groupby("년월", as_index=False)
            .agg(
                races=("경주일", "size"),
                total_bet=("총베팅액", "sum"),
                total_refund=("총환급금", "sum"),
                hits=("적중여부", "sum"),
            )
            .set_index("년월")
        )
        monthly_report = month_check.copy()
        monthly_report["refund_rate"] = monthly_report["total_refund"] / monthly_report[
            "total_bet"
        ].replace(0, pd.NA)
        monthly_report["hit_rate"] = monthly_report["hits"] / monthly_report[
            "races"
        ].replace(0, pd.NA)
        monthly_report = monthly_report.reset_index()

    # 기준별 ROI 계산
    for n in [4, 5, 6]:
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
    total_bet = summary["r_pop_anchor_27"]["total_bet"]
    total_refund = summary["r_pop_anchor_27"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_anchor_27"]["roi"] = roi
    summary["r_pop_anchor_27"]["hit_rate"] = (
        summary["r_pop_anchor_27"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )
    total_bet = summary["r_pop_exacta_anchor_24"]["total_bet"]
    total_refund = summary["r_pop_exacta_anchor_24"]["total_refund"]
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    summary["r_pop_exacta_anchor_24"]["roi"] = roi
    summary["r_pop_exacta_anchor_24"]["hit_rate"] = (
        summary["r_pop_exacta_anchor_24"]["total_hits"] / total_races
        if total_races > 0
        else 0.0
    )

    # 결과 출력
    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    print(f"경주수: {total_races}  제외(신마 2두 이상): {excluded_races}")
    total_bet_all = (
        summary["r_pop_4"]["total_bet"]
        + summary["r_pop_anchor_234"]["total_bet"]
        + summary["r_pop_anchor_25"]["total_bet"]
        + summary["r_pop_anchor_26"]["total_bet"]
    )
    total_refund_all = (
        summary["r_pop_4"]["total_refund"]
        + summary["r_pop_anchor_234"]["total_refund"]
        + summary["r_pop_anchor_25"]["total_refund"]
        + summary["r_pop_anchor_26"]["total_refund"]
    )
    total_refund_rate = total_refund_all / total_bet_all if total_bet_all > 0 else 0.0
    print(
        f"[총 환수율]  총베팅액: {int(total_bet_all):,}원  "
        f"총환수액: {total_refund_all:,.1f}원  환수율: {total_refund_rate:.3f}"
    )
    for n in [4, 5, 6]:
        s = summary[f"r_pop_{n}"]
        refund_rate = (
            s["total_refund"] / s["total_bet"] if s["total_bet"] > 0 else 0.0
        )
        print(
            f"[예상순위(r_pop) - {n}복조]  적중율: {s['hit_rate']:.3f}  "
            f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
            f"  환수율: {refund_rate:.3f}"
        )
    s = summary["r_pop_anchor_234"]
    refund_rate = (
        s["total_refund"] / s["total_bet"] if s["total_bet"] > 0 else 0.0
    )
    print(
        f"[예상순위(r_pop) - 1축(2~4) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
        f"  환수율: {refund_rate:.3f}"
    )
    s = summary["r_pop_anchor_25"]
    refund_rate = (
        s["total_refund"] / s["total_bet"] if s["total_bet"] > 0 else 0.0
    )
    print(
        f"[예상순위(r_pop) - 1축(2~5) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
        f"  환수율: {refund_rate:.3f}"
    )
    s = summary["r_pop_anchor_26"]
    refund_rate = (
        s["total_refund"] / s["total_bet"] if s["total_bet"] > 0 else 0.0
    )
    print(
        f"[예상순위(r_pop) - 1축(2~6) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
        f"  환수율: {refund_rate:.3f}"
    )
    s = summary["r_pop_anchor_27"]
    refund_rate = (
        s["total_refund"] / s["total_bet"] if s["total_bet"] > 0 else 0.0
    )
    print(
        f"[예상순위(r_pop) - 1축(2~7) 삼복조]  적중율: {s['hit_rate']:.3f}  "
        f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
        f"  환수율: {refund_rate:.3f}"
    )
    s = summary["r_pop_exacta_anchor_24"]
    refund_rate = (
        s["total_refund"] / s["total_bet"] if s["total_bet"] > 0 else 0.0
    )
    print(
        "[복승식(r_pop) - 1축 2~4]  "
        f"적중율: {s['hit_rate']:.3f}  총베팅액: {int(s['total_bet']):,}원  "
        f"총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}  환수율: {refund_rate:.3f}"
    )
    r2 = summary["r_pop1_ge4_r_pop2_top3"]
    r2_rate = r2["hits"] / r2["races"] if r2["races"] > 0 else 0.0
    print(
        "[r_pop1 4위 이상일 때 r_pop2 3위내 적중율]  "
        f"경주수: {r2['races']}  적중: {r2['hits']}  적중율: {r2_rate:.3f}"
    )
    r3 = summary["r_pop12_ge4_r_pop3_top3"]
    r3_rate = r3["hits"] / r3["races"] if r3["races"] > 0 else 0.0
    print(
        "[r_pop1·2 4위 이상일 때 r_pop3 3위내 적중율]  "
        f"경주수: {r3['races']}  적중: {r3['hits']}  적중율: {r3_rate:.3f}"
    )
    for ym in sorted(month_summary.keys()):
        m = month_summary[ym]
        refund_rate = m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        print(
            f"[월별 환수율 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {refund_rate:.3f}"
        )
    if not race_df.empty:
        mismatches = 0
        print("[월별 집계 검증]")
        for ym in sorted(month_summary.keys()):
            m = month_summary[ym]
            if ym not in month_check.index:
                print(f"[불일치 {ym}] race_df 월별 없음")
                mismatches += 1
                continue
            c = month_check.loc[ym]
            bet_diff = abs(c["total_bet"] - m["total_bet"])
            refund_diff = abs(c["total_refund"] - m["total_refund"])
            race_diff = int(c["races"]) - int(m["races"])
            if race_diff != 0 or bet_diff > 0.01 or refund_diff > 0.01:
                print(
                    f"[불일치 {ym}] races {int(c['races'])} vs {m['races']}, "
                    f"bet {c['total_bet']:.1f} vs {m['total_bet']:.1f}, "
                    f"refund {c['total_refund']:.1f} vs {m['total_refund']:.1f}"
                )
                mismatches += 1
        if mismatches == 0:
            print("[월별 집계 검증] 모든 월별 합계 일치")
    for label in ["0~20", "21~50", "51~100", "100+"]:
        b = bucket_summary[label]
        refund_rate = b["total_refund"] / b["total_bet"] if b["total_bet"] > 0 else 0.0
        hit_rate = b["hits"] / b["races"] if b["races"] > 0 else 0.0
        print(
            f"[배당율 {label}]  경주수: {b['races']}  "
            f"총베팅액: {int(b['total_bet']):,}원  총환수액: {b['total_refund']:,.1f}원  "
            f"환수율: {refund_rate:.3f}  적중율: {hit_rate:.3f}"
        )
    print("[경마장/등급/거리별 환수율]")
    for (track, grade, distance), s in sorted(
        track_grade_distance_summary.items(),
        key=lambda x: (x[0][0], x[0][1], x[0][2]),
    ):
        refund_rate = s["total_refund"] / s["total_bet"] if s["total_bet"] > 0 else 0.0
        hit_rate = s["hits"] / s["races"] if s["races"] > 0 else 0.0
        print(
            f"[{track} | {grade or '-'} | {distance}]  경주수: {s['races']}  "
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
        bet_unit=100,  # 한 구멍당 100원
    )

    # raw 데이터 CSV 저장 (원하면 경로만 바꿔서 사용)
    out_path = "/Users/Super007/Documents/r_pop_reward.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
