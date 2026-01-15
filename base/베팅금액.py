#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import pymysql
import pandas as pd
from contextlib import closing
from math import comb
from typing import Dict, Any, List, Tuple

# =========================
# 0) DB 설정
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


# =========================
# 1) 배당 파싱(안전)
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
    m = re.findall(r"\d+(\.\d+)?", s.replace(",", ""))
    return float(m[0]) if m else 0.0


# =========================
# 2) 데이터 로드
# =========================
def load_data(conn, from_date: str, to_date: str) -> pd.DataFrame:
    sql = """
    SELECT
        e.rcity      AS 경마장,
        e.rdate      AS 경주일,
        e.rno        AS 경주번호,
        e.gate       AS 마번,
        e.horse      AS 마명,

        x.grade      AS 등급,
        r.distance   AS 경주거리,

        e.rank       AS rank,
        e.r_pop      AS r_pop,
        e.m_rank     AS m_rank,
        e.r_rank     AS r_rank,

        r.r333alloc1 AS 삼복승식배당율
    FROM The1.exp011 e
    LEFT JOIN The1.rec010 r
      ON r.rcity = e.rcity
     AND r.rdate = e.rdate
     AND r.rno   = e.rno
    LEFT JOIN The1.exp010 x
      ON x.rcity = e.rcity
     AND x.rdate = e.rdate
     AND x.rno   = e.rno
    WHERE e.rdate >= %s
      AND e.rdate <= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    return pd.read_sql(sql, conn, params=[from_date, to_date])


# =========================
# 3) 집계 유틸
# =========================
def safe_num(x, default=0.0) -> float:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def safe_int(x, default=0) -> int:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return int(default)
        return int(float(x))
    except Exception:
        return int(default)


def safe_refund_rate(refund: float, bet: float) -> float:
    refund = safe_num(refund, 0.0)
    bet = safe_num(bet, 0.0)
    return (refund / bet) if bet > 0 else 0.0


def safe_roi(refund: float, bet: float) -> float:
    refund = safe_num(refund, 0.0)
    bet = safe_num(bet, 0.0)
    return ((refund - bet) / bet) if bet > 0 else 0.0


def agg(df_in: pd.DataFrame, by_cols: List[str]) -> pd.DataFrame:
    agg_map = dict(
        races=("race_key", "nunique"),
        TOTAL_bet=("TOTAL_bet", "sum"),
        TOTAL_refund=("TOTAL_refund", "sum"),
        r_BOX4_bet=("r_BOX4_bet", "sum"),
        r_BOX4_refund=("r_BOX4_refund", "sum"),
        r_BOX4_hit=("r_BOX4_hit", "sum"),
        m_BOX4_bet=("m_BOX4_bet", "sum"),
        m_BOX4_refund=("m_BOX4_refund", "sum"),
        m_BOX4_hit=("m_BOX4_hit", "sum"),
        r_BOX6_bet=("r_BOX6_bet", "sum"),
        r_BOX6_refund=("r_BOX6_refund", "sum"),
        r_BOX6_hit=("r_BOX6_hit", "sum"),
        m_BOX6_bet=("m_BOX6_bet", "sum"),
        m_BOX6_refund=("m_BOX6_refund", "sum"),
        m_BOX6_hit=("m_BOX6_hit", "sum"),
    )

    if not by_cols:
        out = df_in.agg(**agg_map)
        s = (
            out.to_frame().T
            if isinstance(out, pd.Series)
            else out.reset_index(drop=True)
        )
    else:
        s = df_in.groupby(by_cols, dropna=False, as_index=False).agg(**agg_map)

    # NaN 방어
    for c in [x[0] for x in agg_map.values()]:
        if c in s.columns:
            s[c] = pd.to_numeric(s[c], errors="coerce").fillna(0)

    s["TOTAL_refund_rate"] = s.apply(
        lambda x: safe_refund_rate(x["TOTAL_refund"], x["TOTAL_bet"]), axis=1
    )
    s["TOTAL_roi"] = s.apply(
        lambda x: safe_roi(x["TOTAL_refund"], x["TOTAL_bet"]), axis=1
    )

    for prefix in ["r_BOX4", "m_BOX4", "r_BOX6", "m_BOX6"]:
        s[f"{prefix}_refund_rate"] = s.apply(
            lambda x: safe_refund_rate(x[f"{prefix}_refund"], x[f"{prefix}_bet"]),
            axis=1,
        )
        s[f"{prefix}_roi"] = s.apply(
            lambda x: safe_roi(x[f"{prefix}_refund"], x[f"{prefix}_bet"]), axis=1
        )

    return s


# =========================
# 4) 본 백테스트
# =========================
def backtest_fourway_box46(
    from_date: str,
    to_date: str,
    r_box4_unit: int = 500,
    m_box4_unit: int = 500,
    r_box6_unit: int = 100,
    m_box6_unit: int = 100,
    exclude_new2plus: bool = True,
    new_def_rank_ge: int = 98,
    out_prefix: str = "fourway_box46",
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:

    COMB_4_3 = comb(4, 3)  # 4
    COMB_6_3 = comb(6, 3)  # 20

    with closing(get_conn()) as conn:
        df = load_data(conn, from_date, to_date)

    if df.empty:
        raise RuntimeError(f"데이터 없음: {from_date}~{to_date}")

    df = df.copy()
    df["경주일"] = df["경주일"].astype(str)
    df["년월"] = df["경주일"].str.slice(0, 6)

    df["경주번호"] = (
        pd.to_numeric(df["경주번호"], errors="coerce").fillna(0).astype(int)
    )
    df["마번"] = pd.to_numeric(df["마번"], errors="coerce").fillna(0).astype(int)

    for c in ["rank", "r_pop", "m_rank", "r_rank"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["등급"] = df["등급"].fillna("")
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")
    df["삼복승식배당율"] = df["삼복승식배당율"].apply(parse_odds)

    df["신마"] = (df["rank"].fillna(0) >= new_def_rank_ge).astype(int)

    df["race_key"] = (
        df["경마장"].astype(str)
        + "_"
        + df["경주일"].astype(str)
        + "_"
        + df["경주번호"].astype(int).astype(str)
    )

    excluded_new2plus = 0
    excluded_pending = 0
    rows = []

    for (track, date, rno), g in df.groupby(
        ["경마장", "경주일", "경주번호"], sort=False
    ):
        g = g.copy()

        ym = g["년월"].iloc[0]
        grade = g["등급"].iloc[0]
        dist = g["경주거리"].iloc[0]
        race_key = g["race_key"].iloc[0]
        new_cnt = int(g["신마"].sum())

        if exclude_new2plus and new_cnt >= 2:
            excluded_new2plus += 1
            continue

        odds = (
            float(g["삼복승식배당율"].iloc[0])
            if g["삼복승식배당율"].notna().any()
            else 0.0
        )

        gv = g.dropna(subset=["r_rank"]).copy()
        gv["r_rank"] = pd.to_numeric(gv["r_rank"], errors="coerce").astype("Int64")
        actual_top3 = gv[gv["r_rank"] <= 3]["마번"].astype(int).tolist()
        actual_set = set(actual_top3)

        if not (odds > 0 and len(actual_set) == 3):
            excluded_pending += 1
            continue

        # picks
        g_r = g.sort_values("r_pop", ascending=True)
        g_m = g.sort_values("m_rank", ascending=True)

        r_top4 = g_r.head(4)["마번"].astype(int).tolist()
        m_top4 = g_m.head(4)["마번"].astype(int).tolist()
        r_top6 = g_r.head(6)["마번"].astype(int).tolist()
        m_top6 = g_m.head(6)["마번"].astype(int).tolist()

        # bet
        r_BOX4_bet = COMB_4_3 * r_box4_unit
        m_BOX4_bet = COMB_4_3 * m_box4_unit
        r_BOX6_bet = COMB_6_3 * r_box6_unit
        m_BOX6_bet = COMB_6_3 * m_box6_unit

        # hit
        r_BOX4_hit = int(actual_set.issubset(set(r_top4)))
        m_BOX4_hit = int(actual_set.issubset(set(m_top4)))
        r_BOX6_hit = int(actual_set.issubset(set(r_top6)))
        m_BOX6_hit = int(actual_set.issubset(set(m_top6)))

        # refund
        r_BOX4_refund = (odds * r_box4_unit) if r_BOX4_hit else 0.0
        m_BOX4_refund = (odds * m_box4_unit) if m_BOX4_hit else 0.0
        r_BOX6_refund = (odds * r_box6_unit) if r_BOX6_hit else 0.0
        m_BOX6_refund = (odds * m_box6_unit) if m_BOX6_hit else 0.0

        TOTAL_bet = float(r_BOX4_bet + m_BOX4_bet + r_BOX6_bet + m_BOX6_bet)
        TOTAL_refund = float(
            r_BOX4_refund + m_BOX4_refund + r_BOX6_refund + m_BOX6_refund
        )

        rows.append(
            {
                "race_key": race_key,
                "경마장": track,
                "경주일": date,
                "년월": ym,
                "경주번호": int(rno),
                "등급": grade,
                "경주거리": dist,
                "신마수": new_cnt,
                "삼복승식배당율": odds,
                "실제_top3_마번": ",".join(map(str, sorted(actual_set))),
                "r_pop_top4": ",".join(map(str, r_top4)),
                "m_rank_top4": ",".join(map(str, m_top4)),
                "r_pop_top6": ",".join(map(str, r_top6)),
                "m_rank_top6": ",".join(map(str, m_top6)),
                "r_BOX4_unit": r_box4_unit,
                "m_BOX4_unit": m_box4_unit,
                "r_BOX6_unit": r_box6_unit,
                "m_BOX6_unit": m_box6_unit,
                "r_BOX4_bet": float(r_BOX4_bet),
                "r_BOX4_hit": int(r_BOX4_hit),
                "r_BOX4_refund": float(r_BOX4_refund),
                "m_BOX4_bet": float(m_BOX4_bet),
                "m_BOX4_hit": int(m_BOX4_hit),
                "m_BOX4_refund": float(m_BOX4_refund),
                "r_BOX6_bet": float(r_BOX6_bet),
                "r_BOX6_hit": int(r_BOX6_hit),
                "r_BOX6_refund": float(r_BOX6_refund),
                "m_BOX6_bet": float(m_BOX6_bet),
                "m_BOX6_hit": int(m_BOX6_hit),
                "m_BOX6_refund": float(m_BOX6_refund),
                "TOTAL_bet": TOTAL_bet,
                "TOTAL_refund": TOTAL_refund,
            }
        )

    race_raw = pd.DataFrame(rows)

    # ✅ 숫자형 강제 + NaN 방어(여기가 핵심)
    num_cols = [
        "삼복승식배당율",
        "r_BOX4_bet",
        "r_BOX4_refund",
        "r_BOX4_hit",
        "m_BOX4_bet",
        "m_BOX4_refund",
        "m_BOX4_hit",
        "r_BOX6_bet",
        "r_BOX6_refund",
        "r_BOX6_hit",
        "m_BOX6_bet",
        "m_BOX6_refund",
        "m_BOX6_hit",
        "TOTAL_bet",
        "TOTAL_refund",
    ]
    for c in num_cols:
        if c in race_raw.columns:
            race_raw[c] = pd.to_numeric(race_raw[c], errors="coerce").fillna(0)

    print("===================================")
    print(f"기간: {from_date} ~ {to_date} (정산가능 + 신마<2 경주만)")
    print(f"[USED] races={len(race_raw):,}")
    print(f"[EXCLUDED_NEW2PLUS] races={excluded_new2plus:,}")
    print(f"[EXCLUDED_PENDING]  races={excluded_pending:,}")

    if race_raw.empty:
        print("▶ 사용 가능한 경주가 없습니다.")
        return race_raw, {}

    overall = agg(race_raw, [])
    by_month = agg(race_raw, ["년월"])
    by_grade = agg(race_raw, ["등급"])
    by_dist = agg(race_raw, ["경주거리"])
    by_track = agg(race_raw, ["경마장"])

    o = overall.iloc[0].to_dict()
    total_bet_i = safe_int(o.get("TOTAL_bet", 0), 0)
    total_refund_f = safe_num(o.get("TOTAL_refund", 0.0), 0.0)
    total_rate = safe_num(o.get("TOTAL_refund_rate", 0.0), 0.0)
    total_roi = safe_num(o.get("TOTAL_roi", 0.0), 0.0)

    print(
        f"[OVERALL] bet={total_bet_i:,} refund={total_refund_f:,.1f} "
        f"환수율={total_rate:.3f} ROI={total_roi:.3f}"
    )
    print("===================================")

    # 저장
    raw_path = f"./{out_prefix}_raw_{from_date}_{to_date}.csv"
    overall_path = f"./{out_prefix}_overall_{from_date}_{to_date}.csv"
    month_path = f"./{out_prefix}_month_{from_date}_{to_date}.csv"
    grade_path = f"./{out_prefix}_grade_{from_date}_{to_date}.csv"
    dist_path = f"./{out_prefix}_distance_{from_date}_{to_date}.csv"
    track_path = f"./{out_prefix}_track_{from_date}_{to_date}.csv"

    race_raw.to_csv(raw_path, index=False, encoding="utf-8-sig")
    overall.to_csv(overall_path, index=False, encoding="utf-8-sig")
    by_month.to_csv(month_path, index=False, encoding="utf-8-sig")
    by_grade.to_csv(grade_path, index=False, encoding="utf-8-sig")
    by_dist.to_csv(dist_path, index=False, encoding="utf-8-sig")
    by_track.to_csv(track_path, index=False, encoding="utf-8-sig")

    print("Saved:")
    print(f" - RAW    : {raw_path}")
    print(f" - OVERALL: {overall_path}")
    print(f" - MONTH  : {month_path}")
    print(f" - GRADE  : {grade_path}")
    print(f" - DIST   : {dist_path}")
    print(f" - TRACK  : {track_path}")

    return race_raw, {
        "overall": overall,
        "month": by_month,
        "grade": by_grade,
        "distance": by_dist,
        "track": by_track,
    }


# =========================
# 5) 실행
# =========================
if __name__ == "__main__":
    from_date = "20231201"
    to_date = "20251221"

    backtest_fourway_box46(
        from_date=from_date,
        to_date=to_date,
        r_box4_unit=500,
        m_box4_unit=500,
        r_box6_unit=100,
        m_box6_unit=100,
        exclude_new2plus=True,
        out_prefix="fourway_rpop_mrank_box46_units",
    )
