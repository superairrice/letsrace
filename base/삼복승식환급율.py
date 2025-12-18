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
    rank(예상1), r_pop(예상2), m_rank(예상3), r_rank(실제순위), 삼복승식 배당 포함.
    """
    sql = """
    SELECT
        e.rcity      AS 경마장,
        e.rdate      AS 경주일,
        e.rno        AS 경주번호,
        e.gate       AS 마번,
        r.distance   AS 경주거리,   -- ★ 경주거리 추가
        e.rank       AS rank,       -- 예상순위1
        e.r_pop      AS r_pop,      -- 예상순위2
        e.m_rank     AS m_rank,     -- 예상순위3
        e.r_rank     AS r_rank,     -- 실제순위
        CAST(SUBSTRING(r.r333alloc, 4) AS DECIMAL(10, 0)) AS 삼복승식배당율
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
# 2. rank / r_pop / m_rank 상위6 → 6복조 환수 raw 계산
# =========================
def calc_top6_trifecta_raw(
    from_date: str,
    to_date: str,
    bet_unit: int = 100,  # 한 구멍당 베팅 금액 (원)
) -> tuple[pd.DataFrame, dict]:
    """
    기간(from_date ~ to_date) 동안,
    - 각 경주에 대해
      - rank  기준 상위 6마리
      - r_pop 기준 상위 6마리
      - m_rank 기준 상위 6마리
      를 각각 6복조(조합 20개)로 삼복승식 베팅했다고 가정.
    - 실제 1~3위(r_rank 1~3)를 기준으로 적중 여부 판단.
    - 기준별( rank / r_pop / m_rank ) 환수금, ROI 계산.

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

    for col in ["rank", "r_pop", "m_rank", "r_rank"]:
        df[col] = df[col].astype(int)

    df["삼복승식배당율"] = df["삼복승식배당율"].astype(float)

    # ★ 경주거리 숫자형 변환 (NULL 있으면 NaN -> 그대로 두고, 그룹 첫 값 사용)
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")

    # ★ 년월 컬럼 추가 (YYYYMMDD → YYYYMM)
    df["년월"] = df["경주일"].str.slice(0, 6)

    # ★ 신마 판정: rank >= 98
    df["신마"] = (df["rank"] >= 98).astype(int)

    # 6복조 → 6마리 중 3마리 조합 = 20구멍
    COMB_6_3 = 20
    bet_per_race = COMB_6_3 * bet_unit

    race_rows = []

    # 누적 합계용
    summary = {
        "rank": {"total_bet": 0.0, "total_refund": 0.0},
        "r_pop": {"total_bet": 0.0, "total_refund": 0.0},
        "m_rank": {"total_bet": 0.0, "total_refund": 0.0},
    }

    # 경주 단위 루프
    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()

        # ▶ 년월, 경주거리, 신마수
        year_month = g["년월"].iloc[0]  # ★ 년월
        distance = g["경주거리"].iloc[0]  # ★ 경주거리
        new_cnt = int(g["신마"].sum())  # ★ 신마 수

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

        for basis in ["rank", "r_pop", "m_rank"]:
            # 해당 기준으로 오름차순 정렬 → 상위 6두
            g_sorted = g.sort_values(basis, ascending=True)
            top6 = g_sorted.head(6)["마번"].tolist()
            top6_set = set(top6)

            # 적중 조건: 실제 상위3마리가 모두 top6 안에 있으면,
            # 6복조 20구멍 중 1구멍 적중
            hit_flag = int(bool(actual_set) and actual_set.issubset(top6_set))

            # 환수금: 적중 시 배당 * bet_unit
            refund = odds * bet_unit if hit_flag == 1 else 0.0

            result_per_basis[basis] = {
                "top6": top6,
                "hit": hit_flag,
                "refund": refund,
            }

            # 요약 누적
            summary[basis]["total_bet"] += bet_per_race
            summary[basis]["total_refund"] += refund

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
                # 기준별 1~6위 마번 목록
                "rank_top6_마번": ",".join(map(str, result_per_basis["rank"]["top6"])),
                "r_pop_top6_마번": ",".join(
                    map(str, result_per_basis["r_pop"]["top6"])
                ),
                "m_rank_top6_마번": ",".join(
                    map(str, result_per_basis["m_rank"]["top6"])
                ),
                # 기준별 적중/환수
                "rank_적중": result_per_basis["rank"]["hit"],
                "rank_환수금": result_per_basis["rank"]["refund"],
                "r_pop_적중": result_per_basis["r_pop"]["hit"],
                "r_pop_환수금": result_per_basis["r_pop"]["refund"],
                "m_rank_적중": result_per_basis["m_rank"]["hit"],
                "m_rank_환수금": result_per_basis["m_rank"]["refund"],
                # 공통 베팅 정보
                "6복조_조합수": COMB_6_3,
                "구멍당_베팅금액": bet_unit,
                "경주당_총베팅금액": bet_per_race,
                "삼복승식배당율": odds,
            }
        )

    race_df = pd.DataFrame(race_rows)

    # 기준별 ROI 계산
    for basis in ["rank", "r_pop", "m_rank"]:
        total_bet = summary[basis]["total_bet"]
        total_refund = summary[basis]["total_refund"]
        roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
        summary[basis]["roi"] = roi

    # 결과 출력
    print("===================================")
    print(f"기간: {from_date} ~ {to_date}")
    for basis, label in [
        ("rank", "예상순위1(rank)"),
        ("r_pop", "예상순위2(r_pop)"),
        ("m_rank", "예상순위3(m_rank)"),
    ]:
        s = summary[basis]
        print(
            f"[{label}]  총베팅액: {int(s['total_bet']):,}원  "
            f"총환수액: {s['total_refund']:,.1f}원  ROI: {s['roi']:.3f}"
        )
    print("===================================")

    return race_df, summary


# =========================
# 3. 예시 실행
# =========================
if __name__ == "__main__":
    # 예시: 2023-12-01 ~ 2025-11-30
    from_date = "20231201"
    to_date = "20251207"

    race_df, summary = calc_top6_trifecta_raw(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,  # 한 구멍당 100원
    )

    # raw 데이터 CSV 저장 (원하면 경로만 바꿔서 사용)
    out_path = "/Users/Super007/Documents/top6_raw_20241129_20251130_20251207_v1.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 경주별 raw 데이터 CSV 저장: {out_path}")
