#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import calendar
import pymysql
import pandas as pd
from contextlib import closing
from math import comb
from typing import Tuple, Dict, Any, Optional, List


# =========================================================
# 0) DB 설정
#   - 1순위: 환경변수 MYSQL_HOST/USER/PASSWORD/DB/PORT
#   - 2순위: 아래 DB_CONF (필요시 직접 채워도 됨)
# =========================================================
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


# =========================================================
# 1) 유틸: 배당 파싱
# =========================================================
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


# =========================================================
# 2) 기간 데이터 로드
# =========================================================
def load_result_data_from_db(conn, from_date: str, to_date: str) -> pd.DataFrame:
    """
    exp011 + rec010 + exp010 조인
    - 삼복 배당: r.r333alloc1 (환경 따라 컬럼명 다를 수 있음)
    """
    sql = """
    SELECT
        e.rcity AS 경마장,
        e.rdate AS 경주일,
        e.rno   AS 경주번호,
        e.gate  AS 마번,
        e.horse AS 마명,

        x.grade AS 등급,

        e.rank        AS rank,
        e.r_pop       AS r_pop,
        e.m_rank      AS m_rank,
        e.m_score     AS m_score,
        e.f_rank      AS f_rank,
        e.f_score     AS f_score,
        e.trust_score AS trust_score,

        e.s1f_per AS 초반200,
        e.g1f_per AS 종반200,

        r.distance AS 경주거리,

        r.r333alloc1 AS 삼복승식배당율,
        e.r_rank AS r_rank
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


# =========================================================
# 3) 축(앵커) 선정: m_rank 1~3 중 “실패 냄새 필터 + 우위(갭)”
# =========================================================
def choose_anchor_from_top3(
    g: pd.DataFrame,
    distance: float,
    # ---- 필터 컷(보수적으로 시작)
    min_anchor_trust: float = 65.0,
    max_fr_mismatch: int = 2,  # f_rank - m_rank <= 2만 허용
    # pace_imb = 초반200 - 종반200 (클수록 초반 과열 후 붕괴 위험)
    pace_cut_1400p: float = 35.0,  # 1400m 이상
    pace_cut_1200m: float = 55.0,  # 1200m 이하
    # ---- “우위(갭)” 조건
    min_trust_gap: float = 8.0,  # trust 1위-2위
    min_fscore_gap12: float = 2.0,  # f_score 1위-2위
) -> Tuple[Optional[int], Dict[str, Any]]:
    """
    반환: (anchor_gate or None, debug_info)

    필요 컬럼:
      마번, m_rank, f_rank, f_score, trust_score, 초반200, 종반200
    """
    dbg: Dict[str, Any] = {
        "chosen": None,
        "reason": "",
        "distance": distance,
        "fs_gap12": 0.0,
        "trust_gap12": 0.0,
        "gap_ok": 0,
        "candidates": [],
    }

    if g.empty:
        dbg["reason"] = "EMPTY_RACE"
        return None, dbg

    gg = g.copy()
    for col in ["m_rank", "f_rank"]:
        gg[col] = pd.to_numeric(gg[col], errors="coerce").fillna(999).astype(int)
    for col in ["f_score", "trust_score", "초반200", "종반200"]:
        gg[col] = pd.to_numeric(gg[col], errors="coerce").fillna(0.0).astype(float)
    gg["마번"] = pd.to_numeric(gg["마번"], errors="coerce").fillna(0).astype(int)

    cand = gg[gg["m_rank"].isin([1, 2, 3])].copy()
    if cand.empty:
        dbg["reason"] = "NO_TOP3_CAND"
        return None, dbg

    dist = float(distance) if (distance and not pd.isna(distance)) else 0.0
    if dist >= 1400:
        pace_cut = pace_cut_1400p
    elif 0 < dist <= 1200:
        pace_cut = pace_cut_1200m
    else:
        pace_cut = (pace_cut_1400p + pace_cut_1200m) / 2.0

    def ok_filter(row) -> Tuple[bool, List[str]]:
        reasons = []
        trust = float(row["trust_score"])
        mismatch = int(row["f_rank"]) - int(row["m_rank"])
        pace_imb = float(row["초반200"]) - float(row["종반200"])

        if trust < min_anchor_trust:
            reasons.append(f"LOW_TRUST<{min_anchor_trust}")
        if mismatch >= (max_fr_mismatch + 1):
            reasons.append(f"FR_MISMATCH>={max_fr_mismatch+1}")
        if pace_imb > pace_cut:
            reasons.append(f"PACE_IMB>{pace_cut:.1f}")
        return (len(reasons) == 0), reasons

    cand_rows = []
    for _, r in cand.iterrows():
        passed, reasons = ok_filter(r)
        cand_rows.append(
            {
                "gate": int(r["마번"]),
                "m_rank": int(r["m_rank"]),
                "f_rank": int(r["f_rank"]),
                "f_score": float(r["f_score"]),
                "trust": float(r["trust_score"]),
                "pace_imb": float(r["초반200"]) - float(r["종반200"]),
                "passed": int(passed),
                "fail_reasons": ",".join(reasons),
            }
        )
    dbg["candidates"] = cand_rows

    passed = [x for x in cand_rows if x["passed"] == 1]
    if not passed:
        dbg["reason"] = "ALL_CAND_FILTERED"
        return None, dbg

    # 우위(갭) 계산
    gg_fs = gg.sort_values(["f_score", "m_rank"], ascending=[False, True]).copy()
    fs_gap12 = (
        float(gg_fs.iloc[0]["f_score"] - gg_fs.iloc[1]["f_score"])
        if len(gg_fs) >= 2
        else 0.0
    )

    gg_tr = gg.sort_values(["trust_score", "m_rank"], ascending=[False, True]).copy()
    trust_gap12 = (
        float(gg_tr.iloc[0]["trust_score"] - gg_tr.iloc[1]["trust_score"])
        if len(gg_tr) >= 2
        else 0.0
    )

    dbg["fs_gap12"] = fs_gap12
    dbg["trust_gap12"] = trust_gap12
    gap_ok = (trust_gap12 >= min_trust_gap) or (fs_gap12 >= min_fscore_gap12)
    dbg["gap_ok"] = int(gap_ok)

    if not gap_ok:
        dbg["reason"] = "NO_CLEAR_GAP"
        return None, dbg

    passed_df = pd.DataFrame(passed).sort_values(
        ["trust", "f_score", "m_rank"], ascending=[False, False, True]
    )
    chosen_gate = int(passed_df.iloc[0]["gate"])
    dbg["chosen"] = chosen_gate
    dbg["reason"] = "CHOSEN_OK"
    return chosen_gate, dbg


# =========================================================
# 4) 축 + m_rank 상위6 삼복(10구멍) 환수 계산
# =========================================================
def calc_anchor_top6_trifecta(
    g: pd.DataFrame,
    anchor_gate: Optional[int],
    odds: float,
    actual_set: set,
    bet_unit: int = 100,
) -> Dict[str, Any]:
    """
    축(anchor) + m_rank 상위6(축 포함)을 기반으로 삼복승식:
      - 조합수 = C(5,2) = 10
      - bet = 10 * bet_unit
      - 적중: (축 ∈ 실제top3) AND (실제top3 ⊆ top6)
      - 환수: odds * bet_unit (삼복 1구멍 적중 가정)
    """
    if anchor_gate is None:
        return {"status": "NOBET", "bet": 0.0, "hit": None, "refund": None, "top6": []}
    if odds <= 0 or len(actual_set) != 3:
        return {
            "status": "PENDING",
            "bet": float(comb(5, 2) * bet_unit),
            "hit": None,
            "refund": None,
            "top6": [],
        }

    top6 = g.sort_values("m_rank").head(6)["마번"].astype(int).tolist()
    if anchor_gate not in top6:
        return {
            "status": "NOBET",
            "bet": 0.0,
            "hit": None,
            "refund": None,
            "top6": top6,
        }

    partners = [x for x in top6 if x != anchor_gate]
    holes = comb(len(partners), 2)  # 10
    bet = float(holes * bet_unit)

    hit = int((anchor_gate in actual_set) and actual_set.issubset(set(top6)))
    refund = float(odds * bet_unit) if hit else 0.0
    return {"status": "SETTLED", "bet": bet, "hit": hit, "refund": refund, "top6": top6}


# =========================================================
# 5) 계산 본체 (v4 + 축TOP6 추가)
# =========================================================
def calc_full_raw_v4_with_anchor_top6(
    from_date: str,
    to_date: str,
    top6_bet_unit: int = 100,
    # PLANB_fs 파라미터
    min_anchor_trust_planB: float = 40.0,
    min_fs_gap12_planB: float = 2.0,
    # 축 선정 파라미터
    anchor_select_min_trust: float = 65.0,
    anchor_select_max_fr_mismatch: int = 2,
    anchor_select_pace_cut_1400p: float = 35.0,
    anchor_select_pace_cut_1200m: float = 55.0,
    anchor_select_min_trust_gap: float = 8.0,
    anchor_select_min_fscore_gap12: float = 2.0,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:

    PLAN_B = {
        "BOX4": {"total": 2000, "per": 500},
        "A15": {
            "total": 4500,
            "per": 300,
        },  # (삼복에서는 성능 나쁘면 추후 BOX5/TOP6로 대체 추천)
        "TOP6": {"total": 4000, "per": 200},
    }

    with closing(get_conn()) as conn:
        df = load_result_data_from_db(conn, from_date, to_date)

    if df.empty:
        print(f"▶ [{from_date}~{to_date}] 데이터 없음")
        return pd.DataFrame(), {}

    df = df.copy()
    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = (
        pd.to_numeric(df["경주번호"], errors="coerce").fillna(0).astype(int)
    )
    df["마번"] = pd.to_numeric(df["마번"], errors="coerce").fillna(0).astype(int)

    for c in ["rank", "r_pop", "m_rank", "f_rank", "r_rank"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(999).astype(int)

    for c in ["m_score", "f_score", "trust_score", "초반200", "종반200", "경주거리"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["등급"] = df["등급"].fillna("")
    df["삼복승식배당율"] = df["삼복승식배당율"].apply(parse_odds)
    df["년월"] = df["경주일"].str.slice(0, 6)
    df["신마"] = (df["rank"] >= 98).astype(int)

    COMB_6_3 = comb(6, 3)  # 20
    top6_bet_per_race = float(COMB_6_3 * top6_bet_unit)

    def make_block():
        return {
            "bet_exec": 0.0,
            "bet_settled": 0.0,
            "refund_settled": 0.0,
            "hit_settled": 0,
            "n_settled": 0,
            "n_pending": 0,
        }

    summary: Dict[str, Any] = {
        "rank_top6": make_block(),
        "r_pop_top6": make_block(),
        "m_rank_top6": make_block(),
        "PLANB_fs": make_block(),
        "PLANB_fs_BOX4": make_block(),
        "PLANB_fs_A15": make_block(),
        "PLANB_fs_TOP6": make_block(),
        "PLANB_fs_NOBET": {"count": 0},
        "PLANB_fr": make_block(),
        "PLANB_fr_BOX4": make_block(),
        "PLANB_fr_A15": make_block(),
        "PLANB_fr_TOP6": make_block(),
        "PLANB_fr_NOBET": {"count": 0},
        # ✅ 축 + m_rank TOP6 (10구멍)
        "ANCHOR_TOP6": make_block(),
        "ANCHOR_TOP6_NOBET": {"count": 0},
    }

    def is_settled(odds: float, actual_set: set) -> bool:
        return (odds > 0) and (len(actual_set) == 3)

    def add_settled(
        block: Dict[str, Any], bet: float, refund: float, hit: int, settled: bool
    ):
        if settled:
            block["bet_settled"] += bet
            block["refund_settled"] += refund
            block["hit_settled"] += int(hit)
            block["n_settled"] += 1
        else:
            block["n_pending"] += 1

    def finalize(block: Dict[str, Any]):
        b = float(block.get("bet_settled", 0.0))
        r = float(block.get("refund_settled", 0.0))
        block["환수율_정산기준"] = (r / b) if b > 0 else 0.0
        block["순ROI_정산기준"] = ((r - b) / b) if b > 0 else 0.0

    # -----------------------------
    # 공통: “전략 선택 + 정산(hit/refund)”
    # -----------------------------
    def run_planB(
        mode: str,  # "fs" or "fr"
        g: pd.DataFrame,
        settled: bool,
        odds: float,
        actual_set: set,
        field: int,
        new_cnt: int,
        anchor_gate: Optional[int],
        anchor_f: int,
        anchor_fS: int,
        anchor_trust: float,
        fs_gap12: float,
        overlap4_fr: int,
        overlap4_fs: int,
        box4_picks: list,
        top6_picks: list,
        a15_partners_fr: list,
        a15_partners_fs: list,
    ) -> Dict[str, Any]:

        # 신마 2두 이상이면 집행 X + 축이 없으면 집행 X
        if new_cnt >= 2 or anchor_gate is None:
            summary[f"PLANB_{mode}_NOBET"]["count"] += 1
            return {
                "strategy": "NO BET",
                "bet": 0,
                "per": 0,
                "hit": None,
                "refund": None,
                "status": "NOBET",
                "partners": [],
            }

        # ✅ 전략 선택
        if mode == "fr":
            box4_ok = field <= 11 and overlap4_fr >= 3 and anchor_f <= 2
            a15_ok = anchor_f <= 4
            partners = a15_partners_fr
            anchor_rank_used = anchor_f
            overlap4_used = overlap4_fr
        else:
            box4_ok = (
                field <= 11
                and overlap4_fs >= 3
                and anchor_fS <= 2
                and anchor_trust >= min_anchor_trust_planB
                and fs_gap12 >= min_fs_gap12_planB
            )
            a15_ok = anchor_fS <= 4 and anchor_trust >= min_anchor_trust_planB
            partners = a15_partners_fs
            anchor_rank_used = anchor_fS
            overlap4_used = overlap4_fs

        if box4_ok:
            strategy = "BOX4"
        elif a15_ok:
            strategy = "A15"
        else:
            strategy = "TOP6"

        bet = float(PLAN_B[strategy]["total"])
        per = float(PLAN_B[strategy]["per"])

        summary[f"PLANB_{mode}"]["bet_exec"] += bet
        summary[f"PLANB_{mode}_{strategy}"]["bet_exec"] += bet

        if settled:
            if strategy == "BOX4":
                hit = int(actual_set.issubset(set(box4_picks)))
                refund = odds * per if hit else 0.0
            elif strategy == "A15":
                partners_set = set(partners)
                if anchor_gate in actual_set:
                    remain = actual_set - {anchor_gate}
                    hit = int(len(remain) == 2 and remain.issubset(partners_set))
                else:
                    hit = 0
                refund = odds * per if hit else 0.0
            else:
                hit = int(actual_set.issubset(set(top6_picks)))
                refund = odds * per if hit else 0.0

            add_settled(summary[f"PLANB_{mode}"], bet, refund, hit, True)
            add_settled(summary[f"PLANB_{mode}_{strategy}"], bet, refund, hit, True)

            return {
                "strategy": strategy,
                "bet": bet,
                "per": per,
                "hit": int(hit),
                "refund": float(refund),
                "status": "SETTLED",
                "partners": partners,
                "overlap4_used": overlap4_used,
                "anchor_rank_used": anchor_rank_used,
            }

        # pending
        add_settled(summary[f"PLANB_{mode}"], bet, 0.0, 0, False)
        add_settled(summary[f"PLANB_{mode}_{strategy}"], bet, 0.0, 0, False)
        return {
            "strategy": strategy,
            "bet": bet,
            "per": per,
            "hit": None,
            "refund": None,
            "status": "PENDING",
            "partners": partners,
            "overlap4_used": overlap4_used,
            "anchor_rank_used": anchor_rank_used,
        }

    rows: List[Dict[str, Any]] = []

    for (track, date, rno), g in df.groupby(
        ["경마장", "경주일", "경주번호"], sort=False
    ):
        g = g.copy()

        ym = g["년월"].iloc[0]
        distance = g["경주거리"].iloc[0]
        grade = g["등급"].iloc[0]
        field = int(g["마번"].nunique())
        new_cnt = int(g["신마"].sum())

        odds = (
            float(g["삼복승식배당율"].iloc[0])
            if g["삼복승식배당율"].notna().any()
            else 0.0
        )
        actual = g[g["r_rank"] <= 3]["마번"].astype(int).tolist()
        actual_set = set(actual)
        settled = is_settled(odds, actual_set)

        # -------------------------
        # (A) top6 3모델
        # -------------------------
        top6_map = {}
        for basis, keyname in [
            ("rank", "rank_top6"),
            ("r_pop", "r_pop_top6"),
            ("m_rank", "m_rank_top6"),
        ]:
            top6 = g.sort_values(basis).head(6)["마번"].astype(int).tolist()
            summary[keyname]["bet_exec"] += top6_bet_per_race

            if settled:
                hit = int(actual_set.issubset(set(top6)))
                refund = float(odds * top6_bet_unit) if hit else 0.0
                add_settled(summary[keyname], top6_bet_per_race, refund, hit, True)
            else:
                hit = None
                refund = None
                add_settled(summary[keyname], top6_bet_per_race, 0.0, 0, False)

            top6_map[keyname] = {"picks": top6, "hit": hit, "refund": refund}

        # -------------------------
        # (B) 축(앵커) 선정 (m_rank 1~3 중)
        # -------------------------
        anchor_gate, anchor_dbg = choose_anchor_from_top3(
            g=g,
            distance=float(distance) if pd.notna(distance) else 0.0,
            min_anchor_trust=anchor_select_min_trust,
            max_fr_mismatch=anchor_select_max_fr_mismatch,
            pace_cut_1400p=anchor_select_pace_cut_1400p,
            pace_cut_1200m=anchor_select_pace_cut_1200m,
            min_trust_gap=anchor_select_min_trust_gap,
            min_fscore_gap12=anchor_select_min_fscore_gap12,
        )

        if anchor_gate is not None:
            arow = g[g["마번"] == anchor_gate]
            if not arow.empty:
                anchor_f = int(
                    pd.to_numeric(arow.iloc[0]["f_rank"], errors="coerce")
                    if pd.notna(arow.iloc[0]["f_rank"])
                    else 999
                )
                anchor_trust = float(
                    pd.to_numeric(arow.iloc[0]["trust_score"], errors="coerce")
                    if pd.notna(arow.iloc[0]["trust_score"])
                    else 0.0
                )
            else:
                anchor_f = 999
                anchor_trust = 0.0
        else:
            anchor_f = 999
            anchor_trust = 0.0

        # m_rank 기반 picks
        g_m = g.sort_values("m_rank")
        box4_picks = g_m.head(4)["마번"].astype(int).tolist()
        top6_picks = g_m.head(6)["마번"].astype(int).tolist()

        # -------------------------
        # (C) ANCHOR + m_rank TOP6 (10구멍) 정산/요약
        # -------------------------
        anchor_top6 = calc_anchor_top6_trifecta(
            g=g,
            anchor_gate=anchor_gate,
            odds=odds,
            actual_set=actual_set,
            bet_unit=top6_bet_unit,  # 구멍당 동일 단위 사용
        )

        # 집행/정산 누적(축이 None이면 NOBET로 처리)
        if anchor_top6["status"] == "NOBET":
            summary["ANCHOR_TOP6_NOBET"]["count"] += 1
        else:
            # 집행은 pending/settled 모두 포함한다고 가정
            summary["ANCHOR_TOP6"]["bet_exec"] += float(anchor_top6["bet"])

            if anchor_top6["status"] == "SETTLED":
                add_settled(
                    summary["ANCHOR_TOP6"],
                    float(anchor_top6["bet"]),
                    float(anchor_top6["refund"]),
                    int(anchor_top6["hit"]),
                    True,
                )
            else:
                # pending
                add_settled(
                    summary["ANCHOR_TOP6"], float(anchor_top6["bet"]), 0.0, 0, False
                )

        # -------------------------
        # (D) PLANB용 메타 계산 (기존 v4 유지)
        # -------------------------
        # f_rank 기반 overlap4, partners
        g_f = g.sort_values("f_rank")
        overlap4_fr = len(
            set(box4_picks) & set(g_f.head(4)["마번"].astype(int).tolist())
        )
        a15_partners_fr = []
        if anchor_gate is not None:
            tmp = g[g["마번"] != anchor_gate].copy()
            tmp["mix_fr"] = 0.7 * tmp["m_rank"].astype(float) + 0.3 * tmp[
                "f_rank"
            ].astype(float)
            a15_partners_fr = (
                tmp.sort_values(["mix_fr", "m_rank", "f_rank"])
                .head(6)["마번"]
                .astype(int)
                .tolist()
            )

        # f_score 기반 fS_rank, overlap4, partners
        g_fs = g.copy()
        g_fs["_fs"] = pd.to_numeric(g_fs["f_score"], errors="coerce").fillna(-1e18)
        g_fs = g_fs.sort_values(["_fs", "m_rank"], ascending=[False, True])
        g_fs["fS_rank"] = range(1, len(g_fs) + 1)

        if anchor_gate is not None:
            arow = g_fs[g_fs["마번"] == anchor_gate]
            anchor_fS = int(arow["fS_rank"].iloc[0]) if not arow.empty else 999
        else:
            anchor_fS = 999

        top2_fs = g_fs.head(2)["_fs"].tolist()
        if len(top2_fs) == 2 and pd.notna(top2_fs[0]) and pd.notna(top2_fs[1]):
            fs_gap12 = float(top2_fs[0] - top2_fs[1])
        else:
            fs_gap12 = 0.0

        overlap4_fs = len(
            set(box4_picks) & set(g_fs.head(4)["마번"].astype(int).tolist())
        )

        a15_partners_fs = []
        if anchor_gate is not None:
            tmp = g.merge(g_fs[["마번", "fS_rank"]], on="마번", how="left")
            tmp = tmp[tmp["마번"] != anchor_gate].copy()
            tmp["fS_rank"] = (
                pd.to_numeric(tmp["fS_rank"], errors="coerce").fillna(999).astype(int)
            )
            tmp["mix_fs"] = 0.7 * tmp["m_rank"].astype(float) + 0.3 * tmp[
                "fS_rank"
            ].astype(float)
            a15_partners_fs = (
                tmp.sort_values(["mix_fs", "m_rank", "fS_rank"])
                .head(6)["마번"]
                .astype(int)
                .tolist()
            )

        # -------------------------
        # (E) PLANB 두 버전 동시 실행
        # -------------------------
        out_fr = run_planB(
            mode="fr",
            g=g,
            settled=settled,
            odds=odds,
            actual_set=actual_set,
            field=field,
            new_cnt=new_cnt,
            anchor_gate=anchor_gate,  # ✅ "선정된 축" 사용
            anchor_f=anchor_f,
            anchor_fS=anchor_fS,
            anchor_trust=anchor_trust,
            fs_gap12=fs_gap12,
            overlap4_fr=overlap4_fr,
            overlap4_fs=overlap4_fs,
            box4_picks=box4_picks,
            top6_picks=top6_picks,
            a15_partners_fr=a15_partners_fr,
            a15_partners_fs=a15_partners_fs,
        )
        out_fs = run_planB(
            mode="fs",
            g=g,
            settled=settled,
            odds=odds,
            actual_set=actual_set,
            field=field,
            new_cnt=new_cnt,
            anchor_gate=anchor_gate,  # ✅ "선정된 축" 사용
            anchor_f=anchor_f,
            anchor_fS=anchor_fS,
            anchor_trust=anchor_trust,
            fs_gap12=fs_gap12,
            overlap4_fr=overlap4_fr,
            overlap4_fs=overlap4_fs,
            box4_picks=box4_picks,
            top6_picks=top6_picks,
            a15_partners_fr=a15_partners_fr,
            a15_partners_fs=a15_partners_fs,
        )

        rows.append(
            {
                "년월": ym,
                "경마장": track,
                "경주일": date,
                "경주번호": int(rno),
                "등급": grade,
                "경주거리": float(distance) if pd.notna(distance) else None,
                "출주두수": field,
                "신마수": new_cnt,
                "삼복승식배당율": odds,
                "정산여부": "SETTLED" if settled else "PENDING",
                "실제_top3_마번": (
                    ",".join(map(str, sorted(actual_set))) if actual_set else ""
                ),
                # m_rank top6 baseline
                "m_rank_top6_마번": ",".join(
                    map(str, top6_map["m_rank_top6"]["picks"])
                ),
                "m_rank_top6_적중": top6_map["m_rank_top6"]["hit"],
                "m_rank_top6_환수금": top6_map["m_rank_top6"]["refund"],
                "top6_구멍당": top6_bet_unit,
                "top6_경주당총베팅": top6_bet_per_race,
                # ✅ 축 선정 디버그
                "anchor_gate": anchor_gate if anchor_gate is not None else "",
                "anchor_selected": 1 if anchor_gate is not None else 0,
                "anchor_reason": anchor_dbg.get("reason", ""),
                "anchor_dbg": json.dumps(anchor_dbg, ensure_ascii=False),
                # ✅ 축 + m_rank 상위6 (10구멍)
                "ANCHOR_TOP6_상태": anchor_top6["status"],
                "ANCHOR_TOP6_베팅액": anchor_top6["bet"],
                "ANCHOR_TOP6_적중": anchor_top6["hit"],
                "ANCHOR_TOP6_환수금": anchor_top6["refund"],
                "ANCHOR_TOP6_top6": ",".join(map(str, anchor_top6.get("top6", []))),
                # 공통 메타
                "anchor_f": anchor_f,
                "anchor_fS": anchor_fS,
                "anchor_trust": anchor_trust,
                "fs_gap12": fs_gap12,
                "overlap4_fr(m_vs_f_ranktop4)": overlap4_fr,
                "overlap4_fs(m_vs_f_scoretop4)": overlap4_fs,
                "BOX4_4두(m_top4)": ",".join(map(str, box4_picks)),
                "TOP6_6두(m_top6)": ",".join(map(str, top6_picks)),
                "A15_partners_fr": ",".join(map(str, a15_partners_fr)),
                "A15_partners_fs": ",".join(map(str, a15_partners_fs)),
                # PLANB_fr
                "PLANB_fr_전략": out_fr["strategy"],
                "PLANB_fr_정산상태": out_fr["status"],
                "PLANB_fr_베팅액": out_fr["bet"],
                "PLANB_fr_구멍당": out_fr["per"],
                "PLANB_fr_적중": out_fr["hit"],
                "PLANB_fr_환수금": out_fr["refund"],
                # PLANB_fs
                "PLANB_fs_전략": out_fs["strategy"],
                "PLANB_fs_정산상태": out_fs["status"],
                "PLANB_fs_베팅액": out_fs["bet"],
                "PLANB_fs_구멍당": out_fs["per"],
                "PLANB_fs_적중": out_fs["hit"],
                "PLANB_fs_환수금": out_fs["refund"],
                # 파라미터 기록
                "min_anchor_trust_planB": float(min_anchor_trust_planB),
                "min_fs_gap12_planB": float(min_fs_gap12_planB),
                "anchor_select_min_trust": float(anchor_select_min_trust),
                "anchor_select_max_fr_mismatch": int(anchor_select_max_fr_mismatch),
                "anchor_select_pace_cut_1400p": float(anchor_select_pace_cut_1400p),
                "anchor_select_pace_cut_1200m": float(anchor_select_pace_cut_1200m),
                "anchor_select_min_trust_gap": float(anchor_select_min_trust_gap),
                "anchor_select_min_fscore_gap12": float(anchor_select_min_fscore_gap12),
            }
        )

    race_df = pd.DataFrame(rows)

    for k in [
        "rank_top6",
        "r_pop_top6",
        "m_rank_top6",
        "PLANB_fr",
        "PLANB_fr_BOX4",
        "PLANB_fr_A15",
        "PLANB_fr_TOP6",
        "PLANB_fs",
        "PLANB_fs_BOX4",
        "PLANB_fs_A15",
        "PLANB_fs_TOP6",
        "ANCHOR_TOP6",
    ]:
        finalize(summary[k])

    return race_df, summary


# =========================================================
# 6) 실행
# =========================================================
if __name__ == "__main__":
    from_date = "20231201"
    to_date = "20251221"

    race_df, summary = calc_full_raw_v4_with_anchor_top6(
        from_date,
        to_date,
        top6_bet_unit=100,
        # PLANB_fs 기준(기존)
        min_anchor_trust_planB=40.0,
        min_fs_gap12_planB=2.0,
        # 축 선정 기준(새 설계)
        anchor_select_min_trust=65.0,
        anchor_select_max_fr_mismatch=2,
        anchor_select_pace_cut_1400p=35.0,
        anchor_select_pace_cut_1200m=55.0,
        anchor_select_min_trust_gap=8.0,
        anchor_select_min_fscore_gap12=2.0,
    )

    print("===================================")
    print(f"기간: {from_date} ~ {to_date} (PENDING=배당/결과 결측)")
    keys = [
        "m_rank_top6",
        "ANCHOR_TOP6",
        "PLANB_fr",
        "PLANB_fr_BOX4",
        "PLANB_fr_A15",
        "PLANB_fr_TOP6",
        "PLANB_fs",
        "PLANB_fs_BOX4",
        "PLANB_fs_A15",
        "PLANB_fs_TOP6",
    ]
    for k in keys:
        s = summary[k]
        print(
            f"[{k}] "
            f"집행:{int(s['bet_exec']):,} "
            f"정산경주:{s['n_settled']} / PENDING:{s['n_pending']} "
            f"정산베팅:{int(s['bet_settled']):,} "
            f"정산환수:{s['refund_settled']:,.1f} "
            f"환수율(정산):{s['환수율_정산기준']:.3f} "
            f"순ROI(정산):{s['순ROI_정산기준']:.3f}"
        )
    print(f"[PLANB_fr_NOBET] count={summary['PLANB_fr_NOBET']['count']}")
    print(f"[PLANB_fs_NOBET] count={summary['PLANB_fs_NOBET']['count']}")
    print(f"[ANCHOR_TOP6_NOBET] count={summary['ANCHOR_TOP6_NOBET']['count']}")
    print("===================================")

    out_path = "/Users/Super007/Documents/full_raw_with_planB_v4_plus_anchor_top6.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 저장 완료: {out_path}")
