import pymysql
import pandas as pd
from contextlib import closing
import math

# =========================
# 0. DB 설정
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
    conn = pymysql.connect(**DB_CONF)
    try:
        conn.ping(reconnect=True)
    except Exception:
        pass
    return conn


def safe_float(x, default=0.0) -> float:
    try:
        v = float(x)
        if not math.isfinite(v):
            return float(default)
        return v
    except Exception:
        return float(default)


def nC3(n: int) -> int:
    if n < 3:
        return 0
    return n * (n - 1) * (n - 2) // 6


def nP3(n: int) -> int:
    if n < 3:
        return 0
    return n * (n - 1) * (n - 2)


# =========================
# 1. 데이터 로드 (삼복+삼쌍 배당 포함)
# =========================
def load_data(conn, from_date: str, to_date: str) -> pd.DataFrame:
    sql = """
SELECT
    e.rcity AS 경마장,
    e.rdate AS 경주일,
    e.rno   AS 경주번호,
    e.gate  AS 마번,
    x.grade AS 등급,
    r.distance AS 경주거리,
    e.rank,
    e.r_pop,
    e.m_rank,
    e.r_rank,
    e.f_score,
    e.m_score,
    e.trust_score,
    CAST(SUBSTRING(r.r333alloc,4) AS DECIMAL(10,0)) AS 삼복승식배당율,
    CAST(SUBSTRING(r.r123alloc,4) AS DECIMAL(10,0)) AS 삼쌍승식배당율
FROM The1.exp011 e
LEFT JOIN The1.exp010 x
 ON x.rcity=e.rcity AND x.rdate=e.rdate AND x.rno=e.rno
LEFT JOIN The1.rec010 r
 ON r.rcity=e.rcity AND r.rdate=e.rdate AND r.rno=e.rno
WHERE e.rdate BETWEEN %s AND %s
ORDER BY e.rcity, e.rdate, e.rno, e.gate
"""
    return pd.read_sql(sql, conn, params=[from_date, to_date])


# =========================
# 2. BOX4/5/6 삼복+삼쌍 비교 raw 생성 + 요약
# =========================
def calc_boxN_trifecta_and_tricast(
    df: pd.DataFrame,
    bet_unit: int = 100,
    box_sizes=(4, 5, 6),
    exclude_newhorse_ge2: bool = True,
):
    """
    - box_sizes: (4,5,6) 등
    - 각 box_size에 대해:
        삼복(333): C(n,3) 구멍 / 적중: 실제 top3(집합)이 boxN에 포함
        삼쌍(123): P(n,3) 구멍 / 적중: 실제 1-2-3의 3두가 boxN에 포함(순서는 자동 포함)
    - rank/r_pop/m_rank 각각에 대해 계산
    - raw(out_df)에 (BOX별 hit/refund/bet_amount/box_gates) 컬럼 추가
    """

    df = df.copy()

    # 타입 정리
    df["경주일"] = df["경주일"].astype(str)
    df["년월"] = df["경주일"].str[:6]
    df["경주번호"] = (
        pd.to_numeric(df["경주번호"], errors="coerce").fillna(0).astype(int)
    )
    df["마번"] = pd.to_numeric(df["마번"], errors="coerce").fillna(0).astype(int)

    for c in ["rank", "r_pop", "m_rank", "r_rank"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["삼복승식배당율"] = pd.to_numeric(df["삼복승식배당율"], errors="coerce")
    df["삼쌍승식배당율"] = pd.to_numeric(df["삼쌍승식배당율"], errors="coerce")
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")

    bases = [("rank", "RANK"), ("r_pop", "RPOP"), ("m_rank", "MRANK")]

    # 요약 집계 dict 초기화
    summary = {}
    for n in box_sizes:
        for _c, B in bases:
            summary[f"{B}_BOX{n}_TRI333"] = {
                "bet": 0.0,
                "refund": 0.0,
                "hits": 0,
                "races": 0,
            }
            summary[f"{B}_BOX{n}_TRI123"] = {
                "bet": 0.0,
                "refund": 0.0,
                "hits": 0,
                "races": 0,
            }

    rows = []
    excluded_races = 0
    total_races = 0

    # 경주 단위 루프
    for (rcity, rdate, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        total_races += 1
        g = g.copy()

        # ✅ 신마 2두 이상 경주 제외 (신마 정의: rank>=98)
        new_cnt = int((g["rank"].fillna(0) >= 98).sum())
        if exclude_newhorse_ge2 and new_cnt >= 2:
            excluded_races += 1
            continue

        # odds NaN-safe
        odds333_s = g["삼복승식배당율"].dropna()
        odds123_s = g["삼쌍승식배당율"].dropna()
        odds333 = safe_float(odds333_s.iloc[0] if len(odds333_s) > 0 else 0.0, 0.0)
        odds123 = safe_float(odds123_s.iloc[0] if len(odds123_s) > 0 else 0.0, 0.0)

        # 실제 결과
        gv = g.dropna(subset=["r_rank"]).copy()
        gv["r_rank"] = (
            pd.to_numeric(gv["r_rank"], errors="coerce").fillna(999).astype(int)
        )

        actual_top3_set = set(gv[gv["r_rank"] <= 3]["마번"].astype(int).tolist())
        has_trifecta_result = len(actual_top3_set) == 3

        top123 = gv[gv["r_rank"].isin([1, 2, 3])].copy()
        if len(top123) == 3:
            actual_123 = top123.sort_values("r_rank")["마번"].astype(int).tolist()
            has_tricast_result = True
        else:
            actual_123 = []
            has_tricast_result = False

        # 공통 raw 컬럼
        row = {
            "년월": g["년월"].iloc[0],
            "경마장": rcity,
            "경주일": rdate,
            "경주번호": rno,
            "등급": g["등급"].iloc[0] if "등급" in g.columns else "",
            "경주거리": safe_float(g["경주거리"].iloc[0], 0.0),
            "신마수": new_cnt,
            "구멍당_베팅금액": bet_unit,
            "삼복승식배당율": odds333,
            "삼쌍승식배당율": odds123,
            "실제_top3_삼복": (
                ",".join(map(str, sorted(actual_top3_set)))
                if has_trifecta_result
                else ""
            ),
            "실제_1_2_3_삼쌍": (
                ",".join(map(str, actual_123)) if has_tricast_result else ""
            ),
        }

        # BOX 크기별 조합수/경주당 베팅액(공통으로 기록)
        for n in box_sizes:
            row[f"삼복_BOX{n}_구멍수"] = nC3(n)
            row[f"삼쌍_BOX{n}_구멍수"] = nP3(n)
            row[f"삼복_BOX{n}_경주당베팅액"] = nC3(n) * bet_unit
            row[f"삼쌍_BOX{n}_경주당베팅액"] = nP3(n) * bet_unit

        # 기준별 / BOX별 계산
        for col, B in bases:
            gg = g.sort_values(col, ascending=True)

            for n in box_sizes:
                boxN = gg.head(n)["마번"].astype(int).tolist()
                box_set = set(boxN)

                # --- 삼복(333) ---
                hit333 = int(has_trifecta_result and actual_top3_set.issubset(box_set))
                refund333 = (odds333 * bet_unit) if hit333 else 0.0
                bet333 = nC3(n) * bet_unit

                k333 = f"{B}_BOX{n}_TRI333"
                summary[k333]["bet"] += bet333
                summary[k333]["refund"] += refund333
                summary[k333]["hits"] += hit333
                summary[k333]["races"] += 1

                # --- 삼쌍(123) ---
                hit123 = int(has_tricast_result and set(actual_123).issubset(box_set))
                refund123 = (odds123 * bet_unit) if hit123 else 0.0
                bet123 = nP3(n) * bet_unit

                k123 = f"{B}_BOX{n}_TRI123"
                summary[k123]["bet"] += bet123
                summary[k123]["refund"] += refund123
                summary[k123]["hits"] += hit123
                summary[k123]["races"] += 1

                # raw 컬럼(BOX별)
                row[f"{B}_BOX{n}_gates"] = ",".join(map(str, boxN))

                row[f"{B}_BOX{n}_삼복_hit"] = hit333
                row[f"{B}_BOX{n}_삼복_환급"] = refund333
                row[f"{B}_BOX{n}_삼복_경주당베팅액"] = bet333

                row[f"{B}_BOX{n}_삼쌍_hit"] = hit123
                row[f"{B}_BOX{n}_삼쌍_환급"] = refund123
                row[f"{B}_BOX{n}_삼쌍_경주당베팅액"] = bet123

        rows.append(row)

    out_df = pd.DataFrame(rows)

    # =========================
    # 요약 출력
    # =========================
    print("\n================== BOXN 삼복(333) + 삼쌍(123) 요약 ==================")
    if exclude_newhorse_ge2:
        print(f"[필터] 신마 2두 이상 제외: {excluded_races} / 전체 {total_races} 경주")
        print(f"[필터] 분석 대상 경주수: {total_races - excluded_races}")

    def print_line(k: str):
        v = summary[k]
        bet = safe_float(v["bet"], 0.0)
        refund = safe_float(v["refund"], 0.0)
        races = int(v["races"])
        hits = int(v["hits"])
        hit_rate = (hits / races) if races > 0 else 0.0
        refund_rate = (refund / bet) if bet > 0 else 0.0
        roi = (refund - bet) / bet if bet > 0 else 0.0
        print(
            f"{k:20s} | Races {races:4d} | Hit {hits:4d} | "
            f"HitRate {hit_rate:.3f} | RefundRate {refund_rate:.3f} | ROI {roi:.3f}"
        )

    for n in box_sizes:
        print(f"\n--- BOX{n} 삼복승식(333) 조합=C({n},3)={nC3(n)} ---")
        for _c, B in bases:
            print_line(f"{B}_BOX{n}_TRI333")

        print(f"\n--- BOX{n} 삼쌍승식(123) 조합=P({n},3)={nP3(n)} ---")
        for _c, B in bases:
            print_line(f"{B}_BOX{n}_TRI123")

    return out_df, summary


# =========================
# 실행
# =========================
if __name__ == "__main__":
    from_date = "20231201"
    to_date = "20251221"
    bet_unit = 100

    with closing(get_conn()) as conn:
        df = load_data(conn, from_date, to_date)

    out_df, summary = calc_boxN_trifecta_and_tricast(
        df,
        bet_unit=bet_unit,
        box_sizes=(4, 5, 6),  # ✅ BOX4/5/6 비교
        exclude_newhorse_ge2=True,  # ✅ 신마 2두 이상 제외
    )

    out_path = (
        "/Users/Super007/Documents/box4_5_6_tri333_tri123_rank_rpop_mrank_raw.csv"
    )
    if not out_df.empty:
        out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"\n▶ CSV 저장: {out_path}")
