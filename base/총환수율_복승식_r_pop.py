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
    r_pop(예상), r_rank(실제순위), 복승식 배당 포함.
    """
    sql = """
    SELECT
        e.rcity      AS 경마장,
        e.rdate      AS 경주일,
        e.rno        AS 경주번호,
        e.gate       AS 마번,
        r.distance   AS 경주거리,   -- ★ 경주거리 추가
        e.rank       AS rank,       -- 예상순위(rank)
        e.r_pop      AS r_pop,      -- 예상순위(r_pop)
        e.r_rank     AS r_rank,     -- 실제순위
        CAST(r.r2alloc1 AS DECIMAL(10, 0)) AS 복승식배당율
    FROM The1.exp011 AS e
    LEFT JOIN The1.rec010 AS r
           ON r.rcity = e.rcity
          AND r.rdate = e.rdate
          AND r.rno   = e.rno
    WHERE e.rdate >= %s
      AND e.rdate <= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    df = pd.read_sql(sql, conn, params=[from_date, to_date])
    return df


# =========================
# 2. r_pop 기준 복승식 환수 raw 계산
# =========================
def calc_top6_trifecta_raw(
    from_date: str,
    to_date: str,
    bet_unit: int = 100,  # 한 구멍당 베팅 금액 (원)
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
      - 각 경주에 대해 r_pop 기준
        - 1축 2~4 (3복조)
        - 1축 2~5 (4복조)
        - 1축 2~6 (5복조)
        복승식 베팅했다고 가정.
    - 실제 1~2위(r_rank 1~2)를 기준으로 적중 여부 판단.
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

    df["복승식배당율"] = df["복승식배당율"].astype(float)

    # ★ 경주거리 숫자형 변환 (NULL 있으면 NaN -> 그대로 두고, 그룹 첫 값 사용)
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")

    # ★ 년월 컬럼 추가 (YYYYMMDD → YYYYMM)
    df["년월"] = df["경주일"].str.slice(0, 6)

    # ★ 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    race_rows = []

    # 누적 합계용
    summary = {}
    for n in [4, 5, 6]:
        summary[f"r_pop_anchor_2_{n}"] = {
            "total_bet": 0.0,
            "total_refund": 0.0,
            "total_hits": 0,
        }
        summary[f"r_pop_box_{n}"] = {
            "total_bet": 0.0,
            "total_refund": 0.0,
            "total_hits": 0,
        }
    summary["r_pop1_in_top2"] = {"races": 0, "hits": 0}
    summary["r_pop1_in_top3"] = {"races": 0, "hits": 0}
    summary["r_pop1_top4"] = {"races": 0, "hits": 0}
    summary["r_pop1_top5"] = {"races": 0, "hits": 0}
    summary["r_pop1_top6"] = {"races": 0, "hits": 0}
    month_bet_summary = {}
    month_case_summary = {
        4: {},
        5: {},
        6: {},
    }
    month_box_summary = {
        4: {},
        5: {},
        6: {},
    }
    month_r_pop1 = {}
    month_r_pop1_top3 = {}
    month_r_pop1_top = {}
    total_races = 0

    # 경주 단위 루프
    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()

        # ▶ 년월, 경주거리, 신마수
        year_month = g["년월"].iloc[0]  # ★ 년월
        distance = g["경주거리"].iloc[0]  # ★ 경주거리
        new_cnt = int(g["신마"].sum())  # ★ 신마 수
        if new_cnt >= 2:
            continue
        total_races += 1

        # 실제 1~2위
        actual_top2 = g[g["r_rank"] <= 2]["마번"].tolist()
        actual_set = set(actual_top2)

        # 배당 (경주별 동일 가정)
        odds = (
            float(g["복승식배당율"].iloc[0])
            if not g["복승식배당율"].isna().all()
            else 0.0
        )

        # r_pop 기준 처리
        result_per_basis = {"r_pop": {}}
        g_sorted = g.sort_values("r_pop", ascending=True)
        anchor_gate = g_sorted.head(1)["마번"].iloc[0] if not g_sorted.empty else None
        summary["r_pop1_in_top2"]["races"] += 1
        summary["r_pop1_in_top3"]["races"] += 1
        summary["r_pop1_top4"]["races"] += 1
        summary["r_pop1_top5"]["races"] += 1
        summary["r_pop1_top6"]["races"] += 1
        if year_month not in month_r_pop1:
            month_r_pop1[year_month] = {"races": 0, "hits": 0}
        month_r_pop1[year_month]["races"] += 1
        if year_month not in month_r_pop1_top3:
            month_r_pop1_top3[year_month] = {"races": 0, "hits": 0}
        month_r_pop1_top3[year_month]["races"] += 1
        if year_month not in month_r_pop1_top:
            month_r_pop1_top[year_month] = {
                "races": 0,
                "hits_4": 0,
                "hits_5": 0,
                "hits_6": 0,
            }
        month_r_pop1_top[year_month]["races"] += 1
        if anchor_gate is not None and anchor_gate in actual_set:
            summary["r_pop1_in_top2"]["hits"] += 1
        if anchor_gate is not None and anchor_gate in set(g[g["r_rank"] <= 3]["마번"].tolist()):
            summary["r_pop1_in_top3"]["hits"] += 1
        if anchor_gate is not None:
            anchor_rank = g.loc[g["마번"] == anchor_gate, "r_rank"]
            if not anchor_rank.empty:
                anchor_rank_val = int(anchor_rank.iloc[0])
                if anchor_rank_val <= 4:
                    summary["r_pop1_top4"]["hits"] += 1
                if anchor_rank_val <= 5:
                    summary["r_pop1_top5"]["hits"] += 1
                if anchor_rank_val <= 6:
                    summary["r_pop1_top6"]["hits"] += 1
        bet_per_race_4 = 0
        bet_per_race_5 = 0
        bet_per_race_6 = 0
        for n in [4, 5, 6]:
            topn = g_sorted.head(n)["마번"].tolist()
            others = topn[1:]
            hit_flag = int(
                bool(actual_set)
                and (anchor_gate is not None)
                and (anchor_gate in actual_set)
                and actual_set.issubset({anchor_gate, *others})
            )
            refund = odds * bet_unit if hit_flag == 1 else 0.0
            bet_per_race = (n - 1) * bet_unit
            if n == 4:
                bet_per_race_4 = bet_per_race
            if n == 5:
                bet_per_race_5 = bet_per_race
            if n == 6:
                bet_per_race_6 = bet_per_race
            summary[f"r_pop_anchor_2_{n}"]["total_bet"] += bet_per_race
            summary[f"r_pop_anchor_2_{n}"]["total_refund"] += refund
            summary[f"r_pop_anchor_2_{n}"]["total_hits"] += hit_flag
            result_per_basis["r_pop"][f"anchor_2_{n}"] = {
                "hit": hit_flag,
                "refund": refund,
            }
            if year_month not in month_case_summary[n]:
                month_case_summary[n][year_month] = {
                    "races": 0,
                    "total_bet": 0.0,
                    "total_refund": 0.0,
                    "hits": 0,
                }
            month_case_summary[n][year_month]["races"] += 1
            month_case_summary[n][year_month]["total_bet"] += bet_per_race
            month_case_summary[n][year_month]["total_refund"] += refund
            month_case_summary[n][year_month]["hits"] += hit_flag

            # r_pop BOX n (복승식 조합: C(n,2))
            box_hit_flag = int(
                bool(actual_set) and actual_set.issubset(set(topn))
            )
            box_refund = odds * bet_unit if box_hit_flag == 1 else 0.0
            box_bet_per_race = (n * (n - 1) // 2) * bet_unit
            summary[f"r_pop_box_{n}"]["total_bet"] += box_bet_per_race
            summary[f"r_pop_box_{n}"]["total_refund"] += box_refund
            summary[f"r_pop_box_{n}"]["total_hits"] += box_hit_flag
            result_per_basis["r_pop"][f"box_{n}"] = {
                "hit": box_hit_flag,
                "refund": box_refund,
            }
            if year_month not in month_box_summary[n]:
                month_box_summary[n][year_month] = {
                    "races": 0,
                    "total_bet": 0.0,
                    "total_refund": 0.0,
                    "hits": 0,
                }
            month_box_summary[n][year_month]["races"] += 1
            month_box_summary[n][year_month]["total_bet"] += box_bet_per_race
            month_box_summary[n][year_month]["total_refund"] += box_refund
            month_box_summary[n][year_month]["hits"] += box_hit_flag

        total_bet_race = bet_per_race_4 + bet_per_race_5 + bet_per_race_6
        total_refund_race = (
            result_per_basis["r_pop"]["anchor_2_4"]["refund"]
            + result_per_basis["r_pop"]["anchor_2_5"]["refund"]
            + result_per_basis["r_pop"]["anchor_2_6"]["refund"]
        )
        hit_any = int(
            result_per_basis["r_pop"]["anchor_2_4"]["hit"]
            or result_per_basis["r_pop"]["anchor_2_5"]["hit"]
            or result_per_basis["r_pop"]["anchor_2_6"]["hit"]
        )
        if year_month not in month_bet_summary:
            month_bet_summary[year_month] = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "hits": 0,
            }
        month_bet_summary[year_month]["races"] += 1
        month_bet_summary[year_month]["total_bet"] += total_bet_race
        month_bet_summary[year_month]["total_refund"] += total_refund_race
        month_bet_summary[year_month]["hits"] += hit_any

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
                "실제_top2_마번": (
                    ",".join(map(str, sorted(actual_set))) if actual_set else ""
                ),
                "r_pop_anchor_2_4_적중": result_per_basis["r_pop"]["anchor_2_4"]["hit"],
                "r_pop_anchor_2_4_환수금": result_per_basis["r_pop"]["anchor_2_4"]["refund"],
                "r_pop_anchor_2_5_적중": result_per_basis["r_pop"]["anchor_2_5"]["hit"],
                "r_pop_anchor_2_5_환수금": result_per_basis["r_pop"]["anchor_2_5"]["refund"],
                "r_pop_anchor_2_6_적중": result_per_basis["r_pop"]["anchor_2_6"]["hit"],
                "r_pop_anchor_2_6_환수금": result_per_basis["r_pop"]["anchor_2_6"]["refund"],
                "r_pop_box4_적중": result_per_basis["r_pop"]["box_4"]["hit"],
                "r_pop_box4_환수금": result_per_basis["r_pop"]["box_4"]["refund"],
                "r_pop_box5_적중": result_per_basis["r_pop"]["box_5"]["hit"],
                "r_pop_box5_환수금": result_per_basis["r_pop"]["box_5"]["refund"],
                "r_pop_box6_적중": result_per_basis["r_pop"]["box_6"]["hit"],
                "r_pop_box6_환수금": result_per_basis["r_pop"]["box_6"]["refund"],
                # 공통 베팅 정보
                "3복조_조합수": 3,
                "4복조_조합수": 4,
                "5복조_조합수": 5,
                "BOX4_조합수": 6,
                "BOX5_조합수": 10,
                "BOX6_조합수": 15,
                "구멍당_베팅금액": bet_unit,
                "복승식배당율": odds,
            }
        )

    race_df = pd.DataFrame(race_rows)

    # 기준별 ROI 계산
    for n in [4, 5, 6]:
        key = f"r_pop_anchor_2_{n}"
        total_bet = summary[key]["total_bet"]
        total_refund = summary[key]["total_refund"]
        roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
        summary[key]["roi"] = roi
        summary[key]["hit_rate"] = (
            summary[key]["total_hits"] / total_races if total_races > 0 else 0.0
        )
        box_key = f"r_pop_box_{n}"
        box_total_bet = summary[box_key]["total_bet"]
        box_total_refund = summary[box_key]["total_refund"]
        box_roi = (
            (box_total_refund - box_total_bet) / box_total_bet
            if box_total_bet > 0
            else 0.0
        )
        summary[box_key]["roi"] = box_roi
        summary[box_key]["hit_rate"] = (
            summary[box_key]["total_hits"] / total_races if total_races > 0 else 0.0
        )

    # 결과 출력
    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    for n in [4, 5, 6]:
        s = summary[f"r_pop_anchor_2_{n}"]
        print(
            f"[예상순위(r_pop) - 1축 2~{n}]  경주수: {total_races}  "
            f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  "
            f"적중율: {s['hit_rate']:.3f}  ROI: {s['roi']:.3f}"
        )
    for n in [4, 5, 6]:
        s = summary[f"r_pop_box_{n}"]
        print(
            f"[예상순위(r_pop) - BOX{n}]  경주수: {total_races}  "
            f"총베팅액: {int(s['total_bet']):,}원  총환수액: {s['total_refund']:,.1f}원  "
            f"적중율: {s['hit_rate']:.3f}  ROI: {s['roi']:.3f}"
        )
    for ym in sorted(month_bet_summary.keys()):
        m = month_bet_summary[ym]
        refund_rate = m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
        hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
        print(
            f"[월별 환수율 {ym}]  경주수: {m['races']}  "
            f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
            f"환수율: {refund_rate:.3f}  적중율: {hit_rate:.3f}"
        )
    for n in [4, 5, 6]:
        for ym in sorted(month_case_summary[n].keys()):
            m = month_case_summary[n][ym]
            refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            print(
                f"[예상순위(r_pop) - 1축 2~{n} 월별 {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"환수율: {refund_rate:.3f}  적중율: {hit_rate:.3f}"
            )
    for n in [4, 5, 6]:
        for ym in sorted(month_box_summary[n].keys()):
            m = month_box_summary[n][ym]
            refund_rate = (
                m["total_refund"] / m["total_bet"] if m["total_bet"] > 0 else 0.0
            )
            hit_rate = m["hits"] / m["races"] if m["races"] > 0 else 0.0
            print(
                f"[예상순위(r_pop) - BOX{n} 월별 {ym}]  경주수: {m['races']}  "
                f"총베팅액: {int(m['total_bet']):,}원  총환수액: {m['total_refund']:,.1f}원  "
                f"환수율: {refund_rate:.3f}  적중율: {hit_rate:.3f}"
            )
    r1_races = summary["r_pop1_in_top2"]["races"]
    r1_hits = summary["r_pop1_in_top2"]["hits"]
    r1_rate = r1_hits / r1_races if r1_races > 0 else 0.0
    print(
        f"[r_pop 1 실제 1~2위 적중율]  경주수: {r1_races}  적중: {r1_hits}  적중율: {r1_rate:.3f}"
    )
    r1_races_top3 = summary["r_pop1_in_top3"]["races"]
    r1_hits_top3 = summary["r_pop1_in_top3"]["hits"]
    r1_rate_top3 = r1_hits_top3 / r1_races_top3 if r1_races_top3 > 0 else 0.0
    print(
        f"[r_pop 1 실제 1~3위 적중율]  경주수: {r1_races_top3}  적중: {r1_hits_top3}  적중율: {r1_rate_top3:.3f}"
    )
    for label, key in [("4위내", "r_pop1_top4"), ("5위내", "r_pop1_top5"), ("6위내", "r_pop1_top6")]:
        races = summary[key]["races"]
        hits = summary[key]["hits"]
        rate = hits / races if races > 0 else 0.0
        print(
            f"[r_pop 1 실제 {label} 비율]  경주수: {races}  해당: {hits}  비율: {rate:.3f}"
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
    out_path = "/Users/Super007/Documents/복승식.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
