#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import pymysql
import pandas as pd
from contextlib import closing
from math import comb
from typing import Tuple, Dict, Any, Optional


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
# 1) 유틸: 배당 파싱 (숫자 / 'R=12345' 모두 대응)
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
# 2) 기간 데이터 로드 (네 SQL 적용)
# =========================
def load_result_data_from_db(conn, from_date: str, to_date: str) -> pd.DataFrame:
    sql = """
    SELECT
        e.rcity AS 경마장,
        e.rdate AS 경주일,
        e.rno   AS 경주번호,
        e.gate  AS 마번,
        e.horse AS 마명,

        x.grade AS 등급,

        e.rank  AS rank,
        e.r_pop AS r_pop,
        e.m_rank AS m_rank,
        e.f_rank AS f_rank,
        
        e.f_Score as f_score,
        e.trust_score as trust_score,
        
        e.s1f_per AS 초반200,
        e.g1f_per AS 종반200,

        r.distance AS 경주거리,

        e.alloc1r AS 단승식배당율,
        e.alloc3r AS 연승식배당율,
        r.r2alloc1 AS 복승식배당율,
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


# =========================
# 3) 계산 본체 (실전형 v2: 배당 결측=PENDING)
# =========================
def calc_full_raw_v2(
    from_date: str,
    to_date: str,
    top6_bet_unit: int = 100,  # rank/r_pop/m_rank top6(20조합) 구멍당
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    (A) rank/r_pop/m_rank top6(20조합) raw (정산 가능할 때만 hit/refund)
    (B) PLAN B 스위칭(집행은 항상, 정산은 가능할 때만):
        - BOX4:  2,000 (4조합×500)  조건: 두수<=11 & overlap4>=3 & anchor_f<=2
        - A15 :  4,500 (15조합×300) 조건: anchor_f<=4
        - TOP6:  4,000 (20조합×200) 그 외
      + 공통필터: 신마수>=2 => NO BET (집행 자체를 안 함)

    odds(삼복배당율) 결측/0 => "PENDING" 으로 보고
      - 베팅액은 집행으로 잡되
      - 적중/환수는 None으로 두고 summary 정산에는 포함하지 않음
    """

    PLAN_B = {
        "BOX4": {"total": 2000, "per": 500},
        "A15": {"total": 4500, "per": 300},
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

    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")
    df["등급"] = df["등급"].fillna("")
    df["삼복승식배당율"] = df["삼복승식배당율"].apply(parse_odds)

    df["년월"] = df["경주일"].str.slice(0, 6)
    df["신마"] = (df["rank"] >= 98).astype(int)

    COMB_6_3 = comb(6, 3)  # 20
    top6_bet_per_race = COMB_6_3 * top6_bet_unit

    rows = []

    # summary를 "집행(Execution)"과 "정산(Settled)"으로 분리
    summary = {
        # top6 3모델
        "rank_top6": {
            "bet_exec": 0.0,
            "refund_settled": 0.0,
            "bet_settled": 0.0,
            "hit_settled": 0,
            "n_settled": 0,
            "n_pending": 0,
        },
        "r_pop_top6": {
            "bet_exec": 0.0,
            "refund_settled": 0.0,
            "bet_settled": 0.0,
            "hit_settled": 0,
            "n_settled": 0,
            "n_pending": 0,
        },
        "m_rank_top6": {
            "bet_exec": 0.0,
            "refund_settled": 0.0,
            "bet_settled": 0.0,
            "hit_settled": 0,
            "n_settled": 0,
            "n_pending": 0,
        },
        # PLAN B
        "PLAN_B": {
            "bet_exec": 0.0,
            "refund_settled": 0.0,
            "bet_settled": 0.0,
            "hit_settled": 0,
            "n_settled": 0,
            "n_pending": 0,
        },
        "PLAN_B_BOX4": {
            "bet_exec": 0.0,
            "refund_settled": 0.0,
            "bet_settled": 0.0,
            "hit_settled": 0,
            "n_settled": 0,
            "n_pending": 0,
        },
        "PLAN_B_A15": {
            "bet_exec": 0.0,
            "refund_settled": 0.0,
            "bet_settled": 0.0,
            "hit_settled": 0,
            "n_settled": 0,
            "n_pending": 0,
        },
        "PLAN_B_TOP6": {
            "bet_exec": 0.0,
            "refund_settled": 0.0,
            "bet_settled": 0.0,
            "hit_settled": 0,
            "n_settled": 0,
            "n_pending": 0,
        },
        "PLAN_B_NOBET": {"count": 0},
    }

    def is_settled(odds: float, actual_set: set) -> bool:
        # 배당 확정 + 실제 1~3위가 존재할 때만 정산 가능
        return (odds > 0) and (len(actual_set) == 3)

    def add_settled_block(
        block: Dict[str, Any], bet: float, refund: float, hit: int, settled: bool
    ):
        if settled:
            block["bet_settled"] += bet
            block["refund_settled"] += refund
            block["hit_settled"] += int(hit)
            block["n_settled"] += 1
        else:
            block["n_pending"] += 1

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

        actual = g[g["r_rank"] <= 3]["마번"].tolist()
        actual_set = set(actual)
        settled = is_settled(odds, actual_set)

        # -------------------------
        # (A) 3개 모델 top6(20조합): "집행 bet_exec"은 항상 잡고,
        #     hit/refund는 settled일 때만 계산
        # -------------------------
        top6_map = {}
        for basis, keyname in [
            ("rank", "rank_top6"),
            ("r_pop", "r_pop_top6"),
            ("m_rank", "m_rank_top6"),
        ]:
            top6 = g.sort_values(basis).head(6)["마번"].tolist()
            bet_exec = top6_bet_per_race
            summary[keyname]["bet_exec"] += bet_exec

            if settled:
                hit = int(actual_set.issubset(set(top6)))
                refund = odds * top6_bet_unit if hit == 1 else 0.0
            else:
                hit = None
                refund = None

            top6_map[keyname] = {"picks": top6, "hit": hit, "refund": refund}

            # 정산 통계 반영(정산 가능할 때만)
            if settled:
                add_settled_block(
                    summary[keyname], bet_exec, float(refund), int(hit), True
                )
            else:
                add_settled_block(summary[keyname], bet_exec, 0.0, 0, False)

        # -------------------------
        # (B) PLAN B (odds 결측이어도 "전략 결정/집행"은 진행)
        # -------------------------
        g_m = g.sort_values("m_rank")
        g_f = g.sort_values("f_rank")

        anchor_gate = int(g_m.iloc[0]["마번"]) if len(g_m) else None
        anchor_f = int(g_m.iloc[0]["f_rank"]) if len(g_m) else 999

        box4_picks = g_m.head(4)["마번"].tolist()
        top6_picks = g_m.head(6)["마번"].tolist()
        overlap4 = len(set(box4_picks) & set(g_f.head(4)["마번"].tolist()))

        # A15 상대6 (mix)
        a15_partners = []
        if anchor_gate is not None:
            tmp = g[g["마번"] != anchor_gate].copy()
            tmp["mix"] = 0.7 * tmp["m_rank"].astype(float) + 0.3 * tmp["f_rank"].astype(
                float
            )
            a15_partners = (
                tmp.sort_values(["mix", "m_rank", "f_rank"]).head(6)["마번"].tolist()
            )

        plan_strategy = "NO BET"
        plan_bet = 0
        plan_per = 0
        plan_hit: Optional[int] = 0
        plan_refund: Optional[float] = 0.0
        plan_settle_status = "PENDING" if not settled else "SETTLED"

        # 공통 필터: 신마 2두 이상이면 아예 집행 안 함
        if new_cnt >= 2:
            plan_strategy = "NO BET"
            plan_bet = 0
            plan_per = 0
            plan_hit = None if settled else None
            plan_refund = None if settled else None
            plan_settle_status = "NOBET"
            summary["PLAN_B_NOBET"]["count"] += 1
        else:
            # 전략 선택(집행은 odds와 무관)
            if field <= 11 and overlap4 >= 3 and anchor_f <= 2:
                plan_strategy = "BOX4"
            elif anchor_f <= 4 and anchor_gate is not None:
                plan_strategy = "A15"
            else:
                plan_strategy = "TOP6"

            plan_bet = PLAN_B[plan_strategy]["total"]
            plan_per = PLAN_B[plan_strategy]["per"]

            # 집행액 누적(항상)
            summary["PLAN_B"]["bet_exec"] += plan_bet
            summary[f"PLAN_B_{plan_strategy}"]["bet_exec"] += plan_bet

            # 정산 가능할 때만 hit/refund 계산
            if settled:
                if plan_strategy == "BOX4":
                    hit = int(actual_set.issubset(set(box4_picks)))
                    refund = odds * plan_per if hit else 0.0

                elif plan_strategy == "A15":
                    partners_set = set(a15_partners)
                    if anchor_gate in actual_set:
                        remain = actual_set - {anchor_gate}
                        hit = int(len(remain) == 2 and remain.issubset(partners_set))
                    else:
                        hit = 0
                    refund = odds * plan_per if hit else 0.0

                else:  # TOP6
                    hit = int(actual_set.issubset(set(top6_picks)))
                    refund = odds * plan_per if hit else 0.0

                plan_hit = int(hit)
                plan_refund = float(refund)

                # 정산 통계 반영
                add_settled_block(
                    summary["PLAN_B"], plan_bet, plan_refund, plan_hit, True
                )
                add_settled_block(
                    summary[f"PLAN_B_{plan_strategy}"],
                    plan_bet,
                    plan_refund,
                    plan_hit,
                    True,
                )
            else:
                # 미정산
                plan_hit = None
                plan_refund = None
                add_settled_block(summary["PLAN_B"], plan_bet, 0.0, 0, False)
                add_settled_block(
                    summary[f"PLAN_B_{plan_strategy}"], plan_bet, 0.0, 0, False
                )

        rows.append(
            {
                "년월": ym,
                "경마장": track,
                "경주일": date,
                "경주번호": int(rno),
                "등급": grade,
                "경주거리": distance,
                "출주두수": field,
                "신마수": new_cnt,
                "삼복승식배당율": odds,
                "정산여부": (
                    "SETTLED"
                    if settled
                    else (
                        "NOBET"
                        if plan_strategy == "NO BET" and new_cnt >= 2
                        else "PENDING"
                    )
                ),
                "실제_top3_마번": (
                    ",".join(map(str, sorted(actual_set))) if actual_set else ""
                ),
                # top6(20)
                "rank_top6_마번": ",".join(map(str, top6_map["rank_top6"]["picks"])),
                "r_pop_top6_마번": ",".join(map(str, top6_map["r_pop_top6"]["picks"])),
                "m_rank_top6_마번": ",".join(
                    map(str, top6_map["m_rank_top6"]["picks"])
                ),
                "rank_top6_적중": top6_map["rank_top6"]["hit"],
                "rank_top6_환수금": top6_map["rank_top6"]["refund"],
                "r_pop_top6_적중": top6_map["r_pop_top6"]["hit"],
                "r_pop_top6_환수금": top6_map["r_pop_top6"]["refund"],
                "m_rank_top6_적중": top6_map["m_rank_top6"]["hit"],
                "m_rank_top6_환수금": top6_map["m_rank_top6"]["refund"],
                "top6_조합수": COMB_6_3,
                "top6_구멍당": top6_bet_unit,
                "top6_경주당총베팅": top6_bet_per_race,
                # PLAN B
                "anchor_gate": anchor_gate if anchor_gate is not None else "",
                "anchor_f": anchor_f,
                "overlap4": overlap4,
                "PLANB_BOX4_4두": ",".join(map(str, box4_picks)),
                "PLANB_A15_축": anchor_gate if anchor_gate is not None else "",
                "PLANB_A15_상대6": ",".join(map(str, a15_partners)),
                "PLANB_TOP6_6두": ",".join(map(str, top6_picks)),
                "PLANB_전략": plan_strategy,
                "PLANB_정산상태": plan_settle_status,
                "PLANB_베팅액": plan_bet,
                "PLANB_구멍당": plan_per,
                "PLANB_적중": plan_hit,
                "PLANB_환수금": plan_refund,
                # 정산 전이면 환수율은 None 처리(혼동 방지)
                "PLANB_환수율": (
                    (plan_refund / plan_bet)
                    if (plan_refund is not None and plan_bet > 0)
                    else None
                ),
            }
        )

    race_df = pd.DataFrame(rows)

    # 요약지표 계산: "정산 기준"만 환수율/순ROI 계산
    def finalize(block: Dict[str, Any]):
        bet_exec = block.get("bet_exec", 0.0)
        bet_settled = block.get("bet_settled", 0.0)
        refund_settled = block.get("refund_settled", 0.0)

        block["환수율_정산기준"] = (
            (refund_settled / bet_settled) if bet_settled > 0 else 0.0
        )
        block["순ROI_정산기준"] = (
            ((refund_settled - bet_settled) / bet_settled) if bet_settled > 0 else 0.0
        )

        # 참고: 집행 대비(정산분만) 커버율 느낌
        block["정산커버율(환수/집행)"] = (
            (refund_settled / bet_exec) if bet_exec > 0 else 0.0
        )

    for k in [
        "rank_top6",
        "r_pop_top6",
        "m_rank_top6",
        "PLAN_B",
        "PLAN_B_BOX4",
        "PLAN_B_A15",
        "PLAN_B_TOP6",
    ]:
        finalize(summary[k])

    return race_df, summary


# =========================
# 4) 실행
# =========================
if __name__ == "__main__":
    from_date = "20231201"
    to_date = "20251221"

    race_df, summary = calc_full_raw_v2(from_date, to_date, top6_bet_unit=100)

    print("===================================")
    print(f"기간: {from_date} ~ {to_date}  (odds 결측=배당확정전 PENDING 처리)")
    for k in [
        "rank_top6",
        "r_pop_top6",
        "m_rank_top6",
        "PLAN_B",
        "PLAN_B_BOX4",
        "PLAN_B_A15",
        "PLAN_B_TOP6",
    ]:
        s = summary[k]
        print(
            f"[{k}] "
            f"집행베팅:{int(s['bet_exec']):,} "
            f"정산경주:{s['n_settled']} / PENDING:{s['n_pending']} "
            f"정산베팅:{int(s['bet_settled']):,} "
            f"정산환수:{s['refund_settled']:,.1f} "
            f"환수율(정산):{s['환수율_정산기준']:.3f} "
            f"순ROI(정산):{s['순ROI_정산기준']:.3f}"
        )
    print(f"[PLAN_B_NOBET] count={summary['PLAN_B_NOBET']['count']}")
    print("===================================")

    out_path = "/Users/Super007/Documents/full_raw_with_planB_v2_pending.csv"
    if not race_df.empty:
        race_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"▶ 저장 완료: {out_path}")
