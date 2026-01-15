#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Overlap 기반 삼복승식 전략 백테스트 (m_rank BOX4 vs r_pop BOX4 조합)

정산 가능(배당>0 AND 실제 top3 존재) + 신마<2 경주만 포함.

전략(사용자 요구 반영):
- overlap=4 (m_top4 == r_pop_top4):
    * BOX4 (4C3=4구멍), 구멍당 600원  -> 총 2,400원
- overlap=3:
    * m_rank BOX4 (구멍당 300원, 총 1,200원)
    * r_pop  BOX4 (구멍당 300원, 총 1,200원)
    -> 동시 베팅, 총 2,400원
- overlap=2:
    * m_top4 ∪ r_top4 합집합 6두 구성 -> BOX6 (6C3=20구멍), 구멍당 100원 -> 총 2,000원
- overlap=0/1:
    * NO_BET (원하면 여기서 기본전략 추가 가능)

출력:
- 전체 환수율/ROI + overlap별 요약
- raw/summary CSV 저장
"""

import os
import re
import pandas as pd
import pymysql
from contextlib import closing
from typing import Dict, Any, List, Tuple

# =========================
# 0) DB 설정 (권장: 환경변수)
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
# 1) 유틸: 배당 파싱
# =========================
def parse_odds(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return 0.0
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", s):
        return float(s)
    m = re.findall(r"\d+(?:\.\d+)?", s.replace(",", ""))
    return float(m[0]) if m else 0.0

# =========================
# 2) 데이터 로드
# =========================
def load_df(conn, from_date: str, to_date: str) -> pd.DataFrame:
    sql = """
    SELECT
        e.rcity AS 경마장,
        e.rdate AS 경주일,
        e.rno   AS 경주번호,
        e.gate  AS 마번,

        x.grade AS 등급,
        r.distance AS 경주거리,

        e.rank   AS rank,
        e.r_pop  AS r_pop,
        e.m_rank AS m_rank,
        e.r_rank AS r_rank,

        r.r333alloc1 AS 삼복승식배당율
    FROM The1.exp011 e
    LEFT JOIN The1.exp010 x
      ON x.rcity=e.rcity AND x.rdate=e.rdate AND x.rno=e.rno
    LEFT JOIN The1.rec010 r
      ON r.rcity=e.rcity AND r.rdate=e.rdate AND r.rno=e.rno
    WHERE e.rdate >= %s
      AND e.rdate <= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    return pd.read_sql(sql, conn, params=[from_date, to_date])

# =========================
# 3) overlap=2 합집합 6두 구성
# =========================
def build_union6(g: pd.DataFrame, m_top4: List[int], r_top4: List[int]) -> List[int]:
    union = list(dict.fromkeys(m_top4 + r_top4))  # 순서 유지 중복 제거

    if len(union) == 6:
        return union

    if len(union) < 6:
        # m_rank 우선 채움
        m_more = g.sort_values("m_rank", ascending=True)["마번"].astype(int).tolist()
        for x in m_more:
            if x not in union:
                union.append(x)
            if len(union) == 6:
                return union
        # r_pop로도 채움(안전장치)
        r_more = g.sort_values("r_pop", ascending=True)["마번"].astype(int).tolist()
        for x in r_more:
            if x not in union:
                union.append(x)
            if len(union) == 6:
                return union
        return union[:6]

    # len(union) > 6
    tmp = g[["마번", "m_rank", "r_pop"]].copy()
    tmp["마번"] = tmp["마번"].astype(int)
    tmp = tmp[tmp["마번"].isin(union)].copy()
    tmp["mix_rank"] = (tmp["m_rank"].astype(float) + tmp["r_pop"].astype(float)) / 2.0
    picked = tmp.sort_values(["mix_rank", "m_rank", "r_pop"], ascending=[True, True, True])["마번"].astype(int).tolist()
    return picked[:6]

# =========================
# 4) 전략 백테스트
# =========================
def backtest_overlap_strategy(
    from_date: str,
    to_date: str,
    out_raw: str,
    out_summary: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    # 조합 수
    COMB_4_3 = 4
    COMB_6_3 = 20

    with closing(get_conn()) as conn:
        df = load_df(conn, from_date, to_date)

    if df.empty:
        raise ValueError("데이터가 없습니다.")

    d = df.copy()
    d["경주일"] = d["경주일"].astype(str)
    d["년월"] = d["경주일"].str.slice(0, 6)

    d["경주번호"] = pd.to_numeric(d["경주번호"], errors="coerce").fillna(0).astype(int)
    d["마번"] = pd.to_numeric(d["마번"], errors="coerce").fillna(0).astype(int)
    for c in ["rank", "r_pop", "m_rank", "r_rank"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")

    d["등급"] = d["등급"].fillna("")
    d["경주거리"] = pd.to_numeric(d["경주거리"], errors="coerce")
    d["삼복승식배당율"] = d["삼복승식배당율"].apply(parse_odds)

    # 신마: rank >= 98
    d["신마"] = (pd.to_numeric(d["rank"], errors="coerce").fillna(0) >= 98).astype(int)

    rows: List[Dict[str, Any]] = []

    sum_bet = 0.0
    sum_refund = 0.0
    sum_hits = 0
    sum_races = 0

    excluded_new2 = 0
    excluded_pending = 0

    # overlap별 요약
    bucket = {}  # overlap -> dict

    def bucket_add(overlap_key: int, bet: float, refund: float, hits: int):
        if overlap_key not in bucket:
            bucket[overlap_key] = {"races": 0, "bet": 0.0, "refund": 0.0, "hits": 0}
        bucket[overlap_key]["races"] += 1
        bucket[overlap_key]["bet"] += bet
        bucket[overlap_key]["refund"] += refund
        bucket[overlap_key]["hits"] += hits

    for (track, date, rno), g in d.groupby(["경마장", "경주일", "경주번호"], sort=False):
        g = g.copy()

        # 신마 2두 이상 제외
        new_cnt = int(g["신마"].sum())
        if new_cnt >= 2:
            excluded_new2 += 1
            continue

        odds = float(g["삼복승식배당율"].iloc[0]) if g["삼복승식배당율"].notna().any() else 0.0
        g_valid = g.dropna(subset=["r_rank"]).copy()
        actual = g_valid[pd.to_numeric(g_valid["r_rank"], errors="coerce") <= 3]["마번"].astype(int).tolist()
        actual_set = set(actual)

        settled = (odds > 0) and (len(actual_set) == 3)
        if not settled:
            excluded_pending += 1
            continue

        m_top4 = g.sort_values("m_rank", ascending=True).head(4)["마번"].astype(int).tolist()
        r_top4 = g.sort_values("r_pop", ascending=True).head(4)["마번"].astype(int).tolist()
        overlap = len(set(m_top4) & set(r_top4))

        # 전략 적용
        bet = 0.0
        refund = 0.0
        hits = 0
        strat = "NO_BET"
        detail = []

        if overlap == 4:
            # BOX4, per=600 (총 2400)
            per = 600
            bet = COMB_4_3 * per
            hit = int(actual_set.issubset(set(m_top4)))  # == r_top4
            refund = odds * per if hit else 0.0
            hits = hit
            strat = "OVERLAP4_BOX4_per600"
            detail = [{"leg": "BOX4", "picks": m_top4, "per": per, "hit": hit, "refund": refund}]

        elif overlap == 3:
            # m_BOX4 per300 + r_BOX4 per300
            per = 300
            bet = 2 * (COMB_4_3 * per)  # 2400
            hit_m = int(actual_set.issubset(set(m_top4)))
            hit_r = int(actual_set.issubset(set(r_top4)))
            refund_m = odds * per if hit_m else 0.0
            refund_r = odds * per if hit_r else 0.0
            refund = refund_m + refund_r
            hits = hit_m + hit_r  # 레그별 적중 수(0~2)
            strat = "OVERLAP3_mBOX4_per300_plus_rBOX4_per300"
            detail = [
                {"leg": "m_BOX4", "picks": m_top4, "per": per, "hit": hit_m, "refund": refund_m},
                {"leg": "r_BOX4", "picks": r_top4, "per": per, "hit": hit_r, "refund": refund_r},
            ]

        elif overlap == 2:
            # UNION-BOX6 per100 (총 2000)
            per = 100
            union6 = build_union6(g, m_top4, r_top4)
            bet = COMB_6_3 * per
            hit = int(actual_set.issubset(set(union6)))
            refund = odds * per if hit else 0.0
            hits = hit
            strat = "OVERLAP2_unionBOX6_per100"
            detail = [{"leg": "UNION_BOX6", "picks": union6, "per": per, "hit": hit, "refund": refund}]
        else:
            # overlap 0/1 -> NO_BET
            bet = 0.0
            refund = 0.0
            hits = 0
            strat = f"NO_BET_overlap{overlap}"
            detail = []

        # 누적
        sum_races += 1
        sum_bet += bet
        sum_refund += refund
        sum_hits += hits
        bucket_add(overlap, bet, refund, hits)

        rows.append({
            "년월": g["년월"].iloc[0],
            "경마장": track,
            "경주일": date,
            "경주번호": int(rno),
            "등급": g["등급"].iloc[0],
            "경주거리": g["경주거리"].iloc[0],
            "출주두수": int(g["마번"].nunique()),
            "신마수": new_cnt,
            "삼복승식배당율": odds,
            "실제_top3": ",".join(map(str, sorted(actual_set))),
            "m_top4": ",".join(map(str, m_top4)),
            "r_pop_top4": ",".join(map(str, r_top4)),
            "overlap": overlap,
            "strategy": strat,
            "bet": bet,
            "refund": float(refund),
            "hits": hits,
            "detail_json": str(detail),
        })

    raw = pd.DataFrame(rows)

    overall_refund_rate = (sum_refund / sum_bet) if sum_bet > 0 else 0.0
    overall_roi = ((sum_refund - sum_bet) / sum_bet) if sum_bet > 0 else 0.0

    # overlap 요약
    bucket_rows = []
    for ov in sorted(bucket.keys()):
        b = bucket[ov]["bet"]
        r = bucket[ov]["refund"]
        bucket_rows.append({
            "overlap": ov,
            "races": bucket[ov]["races"],
            "bet": b,
            "refund": r,
            "refund_rate": (r / b) if b > 0 else 0.0,
            "roi": ((r - b) / b) if b > 0 else 0.0,
            "hits": bucket[ov]["hits"],
        })
    by_overlap = pd.DataFrame(bucket_rows)

    summary = pd.DataFrame([{
        "from_date": from_date,
        "to_date": to_date,
        "races": sum_races,
        "bet": sum_bet,
        "refund": sum_refund,
        "refund_rate": overall_refund_rate,
        "roi": overall_roi,
        "excluded_new2plus_races": excluded_new2,
        "excluded_pending_races": excluded_pending,
        "note": "정산가능 + 신마<2 경주만 포함. overlap=4:BOX4(per600), overlap=3:mBOX4(per300)+rBOX4(per300), overlap=2:unionBOX6(per100)",
    }])

    # 저장
    raw.to_csv(out_raw, index=False, encoding="utf-8-sig")
    # summary는 2장(전체 + overlap별)을 같이 저장: 한 파일에 붙이기 위해 concat
    out_sum = pd.concat(
        [summary.assign(section="OVERALL"), by_overlap.assign(section="BY_OVERLAP")],
        ignore_index=True
    )
    out_sum.to_csv(out_summary, index=False, encoding="utf-8-sig")

    # 콘솔 출력
    print("===================================")
    print(f"기간: {from_date} ~ {to_date} (정산가능 + 신마<2 경주만)")
    print(f"[OVERALL] races={sum_races} bet={sum_bet:,.0f} refund={sum_refund:,.1f} "
          f"환수율={overall_refund_rate:.3f} ROI={overall_roi:.3f}")
    print("--- BY OVERLAP ---")
    for _, row in by_overlap.iterrows():
        print(f"[overlap={int(row['overlap'])}] races={int(row['races'])} bet={row['bet']:,.0f} "
              f"refund={row['refund']:,.1f} 환수율={row['refund_rate']:.3f} ROI={row['roi']:.3f}")
    print(f"[EXCLUDED_NEW2PLUS] races={excluded_new2}")
    print(f"[EXCLUDED_PENDING]  races={excluded_pending}")
    print("Saved:")
    print(f" - RAW     : {out_raw}")
    print(f" - SUMMARY : {out_summary}")
    print("===================================")

    return raw, out_sum


if __name__ == "__main__":
    from_date = "20231201"
    to_date = "20251221"

    out_raw = "./overlap_strategy_raw_20231201_20251221.csv"
    out_summary = "./overlap_strategy_summary_20231201_20251221.csv"

    backtest_overlap_strategy(from_date, to_date, out_raw, out_summary)
