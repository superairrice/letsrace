#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
from contextlib import closing
from typing import Optional, Dict, Any, List, Tuple

import pymysql
import pandas as pd


# =========================
# 0) 베팅안 (균등 분배 고정)
#   - BOX4:  2,000  (4구멍 × 500)
#   - A15 :  4,500  (15구멍 × 300)
#   - TOP6:  4,000  (20구멍 × 200)
# =========================
BET_PLAN = {
    "BOX4": {"total": 2000, "per": 500, "n_slots": 4},
    "A15": {"total": 4500, "per": 300, "n_slots": 15},
    "TOP6": {"total": 4000, "per": 200, "n_slots": 20},
}


# =========================
# 1) DB 설정 (환경변수 권장)
# =========================
DB_CONF = {
    "host": os.getenv(
        "MYSQL_HOST", "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com"
    ),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "letslove"),
    "password": os.getenv("MYSQL_PASSWORD", "Ruddksp!23"),
    "db": os.getenv("MYSQL_DB", "The1"),
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


# =========================
# 2) 데이터 로드
# =========================
def load_today_cards(conn, rdate: str, rcity: Optional[str] = None) -> pd.DataFrame:
    where_city = ""
    params = [rdate]
    if rcity:
        where_city = " AND e.rcity = %s "
        params.append(rcity)

    sql = f"""
    SELECT
        e.rcity      AS 경마장,
        e.rdate      AS 경주일,
        e.rno        AS 경주번호,
        e.gate       AS 마번,
        e.horse      AS 마명,

        e.rank       AS rank,
        e.m_rank     AS m_rank,
        e.f_rank     AS f_rank,

        e.s1f_per    AS 초반200,
        e.g1f_per    AS 종반200,

        r.distance   AS 경주거리
    FROM The1.exp011 e
    LEFT JOIN The1.rec010 r
           ON r.rcity = e.rcity
          AND r.rdate = e.rdate
          AND r.rno   = e.rno
    WHERE e.rdate = %s
      {where_city}
    ORDER BY e.rcity, e.rno, e.gate
    """
    df = pd.read_sql(sql, conn, params=params)
    if df.empty:
        return df

    # 타입 정리
    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = (
        pd.to_numeric(df["경주번호"], errors="coerce").fillna(0).astype(int)
    )
    df["마번"] = pd.to_numeric(df["마번"], errors="coerce").fillna(0).astype(int)

    for c in ["rank", "m_rank", "f_rank"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(999).astype(int)

    for c in ["초반200", "종반200", "경주거리"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


# =========================
# 3) 조합 유틸
# =========================
def comb2(lst: List[int]) -> List[Tuple[int, int]]:
    out = []
    n = len(lst)
    for i in range(n):
        for j in range(i + 1, n):
            out.append((lst[i], lst[j]))
    return out


def comb3(lst: List[int]) -> List[Tuple[int, int, int]]:
    out = []
    n = len(lst)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                out.append((lst[i], lst[j], lst[k]))
    return out


# =========================
# 4) 전략 판단 (강화 BOX4)
# =========================
def decide_strategy(race_df: pd.DataFrame) -> Dict[str, Any]:
    new_cnt = int((race_df["rank"] >= 98).sum())
    field = int(race_df["마번"].nunique())

    g_m = race_df.sort_values("m_rank")
    anchor = g_m.head(1)
    if anchor.empty:
        return {
            "strategy": "NO BET",
            "horses": None,
            "reason": "m_rank=1 없음",
            "meta": {
                "신마수": new_cnt,
                "두수": field,
                "anchor_f": None,
                "overlap4": None,
            },
        }

    anchor_gate = int(anchor["마번"].iloc[0])
    anchor_f = int(anchor["f_rank"].iloc[0])

    top4_m = set(g_m.head(4)["마번"])
    top4_f = set(race_df.sort_values("f_rank").head(4)["마번"])
    overlap4 = len(top4_m & top4_f)

    meta = {
        "신마수": new_cnt,
        "두수": field,
        "anchor_f": anchor_f,
        "overlap4": overlap4,
    }

    # 공통 필터
    if new_cnt >= 2:
        return {
            "strategy": "NO BET",
            "horses": None,
            "reason": f"신마 {new_cnt}두(>=2)",
            "meta": meta,
        }

    # ✅ BOX4 조건 강화
    if field <= 11 and overlap4 >= 3 and anchor_f <= 2:
        horses = g_m.head(4)["마번"].tolist()
        return {
            "strategy": "BOX4",
            "horses": horses,
            "reason": "서열고정(두수≤11, overlap4≥3, anchor_f≤2)",
            "meta": meta,
        }

    # A15 조건
    if anchor_f <= 4:
        tmp = race_df[race_df["마번"] != anchor_gate].copy()
        tmp["mix"] = 0.7 * tmp["m_rank"].astype(float) + 0.3 * tmp["f_rank"].astype(
            float
        )
        partners = tmp.sort_values(["mix", "m_rank", "f_rank"]).head(6)["마번"].tolist()
        return {
            "strategy": "A15",
            "horses": {"anchor": anchor_gate, "partners": partners},
            "reason": "강축유지(anchor_f≤4, 상대 0.7m+0.3f 상위6)",
            "meta": meta,
        }

    # TOP6
    horses = g_m.head(6)["마번"].tolist()
    return {
        "strategy": "TOP6",
        "horses": horses,
        "reason": "혼전/보험(anchor_f>4)",
        "meta": meta,
    }


# =========================
# 5) 구멍(조합) 생성 (균등 금액)
# =========================
def make_bets(strategy: str, horses) -> Dict[str, Any]:
    if strategy == "NO BET":
        return {"total": 0, "per": 0, "n_slots": 0, "slots": []}

    if strategy == "BOX4":
        picks = list(map(int, horses))
        combos = comb3(picks)  # 4 slots
        per = BET_PLAN["BOX4"]["per"]
        slots = [(c, per) for c in combos]
        return {
            "total": per * len(slots),
            "per": per,
            "n_slots": len(slots),
            "slots": slots,
        }

    if strategy == "TOP6":
        picks = list(map(int, horses))
        combos = comb3(picks)  # 20 slots
        per = BET_PLAN["TOP6"]["per"]
        slots = [(c, per) for c in combos]
        return {
            "total": per * len(slots),
            "per": per,
            "n_slots": len(slots),
            "slots": slots,
        }

    if strategy == "A15":
        anchor = int(horses["anchor"])
        partners = list(map(int, horses["partners"]))
        pairs = comb2(partners)  # 15 slots
        combos = [(anchor, a, b) for (a, b) in pairs]
        per = BET_PLAN["A15"]["per"]
        slots = [(c, per) for c in combos]
        return {
            "total": per * len(slots),
            "per": per,
            "n_slots": len(slots),
            "slots": slots,
        }

    return {"total": 0, "per": 0, "n_slots": 0, "slots": []}


def format_horses(strategy: str, horses) -> str:
    if strategy == "A15" and isinstance(horses, dict):
        return f"축:{horses['anchor']} / 상대:{','.join(map(str, horses['partners']))}"
    if isinstance(horses, list):
        return ",".join(map(str, horses))
    return ""


# =========================
# 6) main
# =========================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="20251220", help="YYYYMMDD")
    ap.add_argument("--rcity", default="", help="서울/부산 등 (optional)")
    ap.add_argument("--out", default="", help="결과 CSV 저장 경로 (optional)")
    ap.add_argument("--detail", action="store_true", help="구멍(조합) 상세 CSV도 저장")
    args = ap.parse_args()

    rcity = args.rcity.strip() or None

    with closing(get_conn()) as conn:
        df = load_today_cards(conn, rdate=args.date, rcity=rcity)

    if df.empty:
        print(f"[{args.date}] 데이터 없음 (rcity={rcity})")
        return

    out_rows = []
    detail_rows = []

    for (track, date, rno), g in df.groupby(
        ["경마장", "경주일", "경주번호"], sort=False
    ):
        dec = decide_strategy(g)
        strategy = dec["strategy"]
        horses = dec["horses"]
        meta = dec.get("meta", {}) or {}

        bet = make_bets(strategy, horses)

        out_rows.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": int(rno),
                "경주거리": g["경주거리"].iloc[0],
                "출주두수": int(g["마번"].nunique()),
                "신마수": int((g["rank"] >= 98).sum()),
                "anchor_f": meta.get("anchor_f", ""),
                "overlap4": meta.get("overlap4", ""),
                "전략": strategy,
                "베팅말": format_horses(strategy, horses),
                "총베팅": bet["total"],
                "구멍당": bet["per"],
                "구멍수": bet["n_slots"],
                "사유": dec.get("reason", ""),
            }
        )

        if args.detail and bet["n_slots"] > 0:
            for combo, amt in bet["slots"]:
                detail_rows.append(
                    {
                        "경마장": track,
                        "경주일": date,
                        "경주번호": int(rno),
                        "전략": strategy,
                        "조합": "-".join(map(str, combo)),
                        "금액": int(amt),
                    }
                )

    out_df = (
        pd.DataFrame(out_rows)
        .sort_values(["경마장", "경주번호"])
        .reset_index(drop=True)
    )

    print("===================================")
    print(f"자동 베팅 카드(PLAN B): {args.date} (rcity={rcity or 'ALL'})")
    print("===================================")
    print(out_df.to_string(index=False))

    if args.out.strip():
        out_df.to_csv(args.out, index=False, encoding="utf-8-sig")
        print(f"\n▶ 저장 완료: {args.out}")

        if args.detail and detail_rows:
            det_path = os.path.splitext(args.out)[0] + "_detail.csv"
            pd.DataFrame(detail_rows).to_csv(
                det_path, index=False, encoding="utf-8-sig"
            )
            print(f"▶ 구멍 상세 저장: {det_path}")


if __name__ == "__main__":
    main()
