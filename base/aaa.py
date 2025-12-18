#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import os
import math

import pymysql
import pandas as pd


# =========================================================
# 0) DB
# =========================================================


def get_conn():
    # ⚠️ 운영에서는 환경변수/시크릿 사용 권장 (여긴 네 기존 코드 그대로 유지)
    return pymysql.connect(
        host="database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",
        user="letslove",
        password="Ruddksp!23",
        db="The1",
        port=3306,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def load_race(rcity: str, rdate: str, rno: int) -> List[Dict[str, Any]]:
    """
    한 경주 데이터 로드
    """
    sql = """
        SELECT
            e.rcity, e.rdate, e.rno,
            t.distance AS 경주거리,

            e.gate AS 마번,
            e.horse AS 경주마,

            e.rank  AS 프로그램예상순위1,
            e.r_pop AS 프로그램최근8경주기준예상순위,
            e.m_rank AS 프로그램최종예상순위,

            e.s1f_per AS 초반200,
            e.g3f_per AS 종반600,
            e.g1f_per AS 종반200,
            e.rec_per AS 기록점수,
            e.rec8_trend AS 최근8,
            e.jt_score   AS 연대,

            e.j_per AS 기수복승율,
            e.t_per AS 조교사복승율,

            e.r_rank AS 실제순위,
            e.alloc1r AS 단승식배당율,
            e.alloc3r AS 연승식배당율
        FROM The1.exp011 e
        JOIN The1.exp010 t
          ON t.rcity = e.rcity AND t.rdate = e.rdate AND t.rno = e.rno
        WHERE e.rcity=%s AND e.rdate=%s AND e.rno=%s
        ORDER BY e.gate
    """
    with closing(get_conn()) as conn:
        df = pd.read_sql(sql, conn, params=(rcity, rdate, rno))
    return df.fillna(0).to_dict("records")


# =========================================================
# 1) 퍼센타일(Best Percentile): 0~100, 높을수록 좋음
# =========================================================


def best_pct(values: List[float], v: float) -> float:
    """
    내림차순 기준 '좋은쪽 퍼센타일'
    - 100: 최상위 (나보다 큰 값이 거의 없음)
    - 0: 최하위
    """
    if not values:
        return 0.0
    s = sorted(values, reverse=True)
    better = sum(1 for x in s if x > v)
    return 100.0 * (1.0 - better / max(1, len(s)))


def pct_label(p: float) -> str:
    # 보기용 라벨
    top = max(1, int(round(100.0 - float(p))))
    if top <= 50:
        return f"상위{top}%"
    return f"하위{top}%"


# =========================================================
# 2) 복병 점수(v2): 마체중변화 X, m_rank 구간 가점 X
# =========================================================


@dataclass
class DarkScoreConfig:
    # B(퍼포먼스)에서 "상위 perf_top_pct" 기준
    perf_top_pct: float = 30.0  # 기본: 상위 30%면 점수 시작
    # C(바닥회피)에서 "하위 bottom_guard_pct" 기준
    bottom_guard_pct: float = 30.0
    # D(사람)에서 "상위 people_top_pct" 기준 (예: 상위 60%면 통과)
    people_top_pct: float = 60.0

    # 가중치(총 70점)
    w_disagree: float = 15.0  # ① 평가 불일치
    w_perf: float = 30.0  # ② 퍼포먼스 원툴
    w_stable: float = 15.0  # ③ 바닥회피(최근8/연대)
    w_people: float = 10.0  # ④ 기수/조교


def score_disagreement(rank1: float, rank2: float, w: float) -> Tuple[float, float]:
    """
    ① 평가 불일치 점수 (0~w)
    - |rank - r_pop| 크면 복병 신호
    - diff >= 6이면 만점(캡)
    """
    diff = abs(float(rank1) - float(rank2))
    capped = min(diff, 6.0)
    score = w * (capped / 6.0)
    return score, diff


def score_perf_best(
    h: Dict[str, Any], horses: List[Dict[str, Any]], perf_top_pct: float, w: float
) -> Tuple[float, Dict[str, float]]:
    """
    ② 퍼포먼스 점수 (0~w)
    - (초반200/종반600/종반200/기록점수) 중 1개라도 레이스 내 상위 perf_top_pct면 점수 부여
    - 상위 커트라인부터 100까지 선형으로 w 환산
    """
    s1f_list = [float(x.get("초반200") or 0.0) for x in horses]
    g3f_list = [float(x.get("종반600") or 0.0) for x in horses]
    g1f_list = [float(x.get("종반200") or 0.0) for x in horses]
    rec_list = [float(x.get("기록점수") or 0.0) for x in horses]

    s1f_p = best_pct(s1f_list, float(h.get("초반200") or 0.0))
    g3f_p = best_pct(g3f_list, float(h.get("종반600") or 0.0))
    g1f_p = best_pct(g1f_list, float(h.get("종반200") or 0.0))
    rec_p = best_pct(rec_list, float(h.get("기록점수") or 0.0))

    perf_best = max(s1f_p, g3f_p, g1f_p, rec_p)

    # 상위 perf_top_pct => best_pct 기준으로는 perf_cut 이상
    perf_cut = 100.0 - float(perf_top_pct)

    if perf_best < perf_cut:
        return 0.0, {
            "perf_best": perf_best,
            "perf_cut": perf_cut,
            "s1f_p": s1f_p,
            "g3f_p": g3f_p,
            "g1f_p": g1f_p,
            "rec_p": rec_p,
        }

    # perf_cut~100 구간을 0~w로 선형 변환
    strength = (perf_best - perf_cut) / max(1e-9, (100.0 - perf_cut))
    strength = max(0.0, min(1.0, strength))
    score = w * strength

    return score, {
        "perf_best": perf_best,
        "perf_cut": perf_cut,
        "s1f_p": s1f_p,
        "g3f_p": g3f_p,
        "g1f_p": g1f_p,
        "rec_p": rec_p,
    }


def score_stability(
    h: Dict[str, Any], horses: List[Dict[str, Any]], bottom_guard_pct: float, w: float
) -> Tuple[float, Dict[str, float]]:
    """
    ③ 폼/연대 바닥회피 (0 or w)
    - 최근8 & 연대 둘 다 하위 bottom_guard_pct면 0점
    - 아니면 w점
    """
    trend_list = [float(x.get("최근8") or 0.0) for x in horses]
    jt_list = [float(x.get("연대") or 0.0) for x in horses]

    trend_p = best_pct(trend_list, float(h.get("최근8") or 0.0))
    jt_p = best_pct(jt_list, float(h.get("연대") or 0.0))

    # 하위 bottom_guard_pct => best_pct 기준으로는 <= bottom_guard_pct
    trend_bottom = trend_p <= float(bottom_guard_pct)
    jt_bottom = jt_p <= float(bottom_guard_pct)

    both_bottom = bool(trend_bottom and jt_bottom)
    score = 0.0 if both_bottom else float(w)

    return score, {
        "trend_p": trend_p,
        "jt_p": jt_p,
        "trend_bottom": float(trend_bottom),
        "jt_bottom": float(jt_bottom),
    }


def score_people(
    h: Dict[str, Any], horses: List[Dict[str, Any]], people_top_pct: float, w: float
) -> Tuple[float, Dict[str, float]]:
    """
    ④ 기수/조교 신뢰 (0 or w)
    - 둘 중 하나라도 레이스 내 상위 people_top_pct면 w점
    - best_pct로 보면 커트는 100 - people_top_pct
      예) people_top_pct=60 => perf_cut=40 이상이면 상위60%로 인정
    """
    j_list = [float(x.get("기수복승율") or 0.0) for x in horses]
    t_list = [float(x.get("조교사복승율") or 0.0) for x in horses]

    j_p = best_pct(j_list, float(h.get("기수복승율") or 0.0))
    t_p = best_pct(t_list, float(h.get("조교사복승율") or 0.0))

    cut = 100.0 - float(people_top_pct)  # 상위60%면 cut=40

    ok = (j_p >= cut) or (t_p >= cut)
    score = float(w) if ok else 0.0

    return score, {"j_p": j_p, "t_p": t_p, "cut": cut, "ok": float(ok)}


def build_perf_tags(p: Dict[str, float]) -> str:
    """
    어떤 지표가 '원툴(상위권)'인지 태그로 표시
    """
    perf_cut = p["perf_cut"]
    tags = []
    if p["s1f_p"] >= perf_cut:
        tags.append(f"초반({pct_label(p['s1f_p'])})")
    if p["g3f_p"] >= perf_cut:
        tags.append(f"종반600({pct_label(p['g3f_p'])})")
    if p["g1f_p"] >= perf_cut:
        tags.append(f"종반200({pct_label(p['g1f_p'])})")
    if p["rec_p"] >= perf_cut:
        tags.append(f"기록({pct_label(p['rec_p'])})")
    return "/".join(tags)


def compute_darkhorse_scores_for_race(
    horses: List[Dict[str, Any]],
    cfg: DarkScoreConfig = DarkScoreConfig(),
    *,
    require_m_rank_ge_4: bool = True,
) -> pd.DataFrame:
    """
    ✅ 한 경주 입력 -> 각 말의 복병점수 계산
    - 전제: 복병 후보는 m_rank >= 4 (필터)
    - 마체중변화 관련 없음
    - m_rank 구간 가점 없음
    """
    rows: List[Dict[str, Any]] = []

    for h in horses:
        mr = int(h.get("프로그램최종예상순위") or 99)
        if require_m_rank_ge_4 and mr < 4:
            # 후보 제외: 점수는 0 처리(또는 NaN 처리하고 싶으면 바꿔도 됨)
            rows.append(
                {
                    "마번": int(h.get("마번") or 0),
                    "경주마": str(h.get("경주마") or ""),
                    "m_rank": mr,
                    "dark_score": 0.0,
                    "dark_label": "제외(m_rank<4)",
                    "근거": "복병 후보 전제(m_rank≥4) 미충족",
                }
            )
            continue

        # ① 평가 불일치
        s_dis, diff = score_disagreement(
            float(h.get("프로그램예상순위1") or 0.0),
            float(h.get("프로그램최근8경주기준예상순위") or 0.0),
            cfg.w_disagree,
        )

        # ② 퍼포먼스 원툴
        s_perf, p_perf = score_perf_best(h, horses, cfg.perf_top_pct, cfg.w_perf)
        perf_tags = build_perf_tags(p_perf)

        # ③ 바닥 회피(최근8/연대)
        s_stb, p_stb = score_stability(h, horses, cfg.bottom_guard_pct, cfg.w_stable)

        # ④ 기수/조교
        s_ppl, p_ppl = score_people(h, horses, cfg.people_top_pct, cfg.w_people)

        total = s_dis + s_perf + s_stb + s_ppl
        total = max(0.0, min(70.0, total))

        # 라벨(권장 구간)
        if total >= 55:
            label = "복병강"
        elif total >= 45:
            label = "복병유력"
        elif total >= 35:
            label = "참고"
        else:
            label = "약함"

        # 근거 문자열
        reason = (
            f"불일치(diff={diff:.0f}) {s_dis:.1f}/{cfg.w_disagree:.0f} + "
            f"원툴({perf_tags or '없음'}, best={p_perf['perf_best']:.1f}) {s_perf:.1f}/{cfg.w_perf:.0f} + "
            f"바닥회피(최근8 {pct_label(p_stb['trend_p'])}, 연대 {pct_label(p_stb['jt_p'])}) {s_stb:.1f}/{cfg.w_stable:.0f} + "
            f"사람(기수 {pct_label(p_ppl['j_p'])}, 조교 {pct_label(p_ppl['t_p'])}) {s_ppl:.1f}/{cfg.w_people:.0f}"
        )

        rows.append(
            {
                "마번": int(h.get("마번") or 0),
                "경주마": str(h.get("경주마") or ""),
                "m_rank": mr,
                "dark_score": round(total, 2),
                "dark_label": label,
                "근거": reason,
                # 참고로 원자료도 같이 싣기
                "프로그램예상순위1": int(h.get("프로그램예상순위1") or 0),
                "최근8예상순위": int(h.get("프로그램최근8경주기준예상순위") or 0),
                "초반200": float(h.get("초반200") or 0.0),
                "종반600": float(h.get("종반600") or 0.0),
                "종반200": float(h.get("종반200") or 0.0),
                "기록점수": float(h.get("기록점수") or 0.0),
                "최근8": float(h.get("최근8") or 0.0),
                "연대": float(h.get("연대") or 0.0),
                "기수복승율": float(h.get("기수복승율") or 0.0),
                "조교사복승율": float(h.get("조교사복승율") or 0.0),
            }
        )

    df = pd.DataFrame(rows)

    # 점수 높은 순으로 정렬(동점이면 m_rank 낮은 순은 참고용으로만)
    if not df.empty and "dark_score" in df.columns:
        df = df.sort_values(
            ["dark_score", "m_rank"], ascending=[False, True]
        ).reset_index(drop=True)

    return df


# =========================================================
# 3) 실행 예시(main)
# =========================================================

if __name__ == "__main__":
    # 입력
    rcity = "서울"
    rdate = "20251206"
    rno = 3

    horses = load_race(rcity, rdate, rno)
    if not horses:
        print("데이터 없음")
        raise SystemExit(0)

    cfg = DarkScoreConfig(
        perf_top_pct=30.0,  # 원툴 상위30%
        bottom_guard_pct=30.0,  # 최근8+연대 동시하위30%면 바닥
        people_top_pct=60.0,  # 기수/조교 상위60%면 통과
    )

    df = compute_darkhorse_scores_for_race(
        horses,
        cfg=cfg,
        require_m_rank_ge_4=True,  # ✅ 복병 후보: m_rank>=4
    )

    pd.set_option("display.max_colwidth", 200)
    print(f"\n[{rcity} {rdate} R{rno}] 복병 점수 결과(마체중변화X / m_rank가점X)")
    cols = ["마번", "경주마", "m_rank", "dark_score", "dark_label", "근거"]
    print(df[cols].to_string(index=False))
