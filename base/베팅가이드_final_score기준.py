from __future__ import annotations
from typing import List, Tuple, Dict, Any, Set
from itertools import combinations
from contextlib import closing
import math

import pymysql
import pandas as pd


# ==============================
# 0. 기본 설정
# ==============================

COLUMNS = [
    "rcity",
    "rdate",
    "rno",
    "경주거리",
    "gate",
    "horse",
    "마체중",
    "마령",
    "성별",
    "출주갭",
    "예상1",
    "예상2",
    "m_rank",
    "초반200",
    "종반600",
    "종반200",
    "기록점수",
    "최근8경주트렌드점수",
    "기수 조교사 연대점수",
    "코멘트",
    "최근8경주 요약",
    "출주수",  # year_race
]

# 거리 구간별 기록 기여도 가중치 (2024~2025 패턴 반영)
DIST_WEIGHTS = {
    "short": {  # 1000~1200m
        "early": 0.45,
        "g3f": 0.28,
        "g1f": 0.12,
        "trend": 0.10,
        "rec": 0.05,
    },
    "middle": {  # 1300~1600m
        "early": 0.33,
        "g3f": 0.35,
        "g1f": 0.16,
        "trend": 0.10,
        "rec": 0.06,
    },
    "long": {  # 1700m 이상
        "early": 0.22,
        "g3f": 0.45,
        "g1f": 0.18,
        "trend": 0.10,
        "rec": 0.05,
    },
}


def get_distance_zone(dist: float) -> str:
    """경주거리 구간 분류."""
    if dist <= 1200:
        return "short"
    elif dist <= 1600:
        return "middle"
    else:
        return "long"


# ==============================
# 1. 공통 유틸
# ==============================


def tuple_to_dict(row: Tuple[Any, ...]) -> Dict[str, Any]:
    """SELECT 결과 튜플을 컬럼명 딕셔너리로 변환."""
    d = {col: row[i] for i, col in enumerate(COLUMNS)}

    # 숫자형 캐스팅
    for num_col in [
        "경주거리",
        "gate",
        "마령",
        "출주갭",
        "예상1",
        "예상2",
        "m_rank",
        "초반200",
        "종반600",
        "종반200",
        "기록점수",
        "최근8경주트렌드점수",
        "기수 조교사 연대점수",
        "출주수",
    ]:
        v = d.get(num_col)
        if v is not None:
            try:
                d[num_col] = float(v)
            except (ValueError, TypeError):
                pass

    return d


def summarize_pace(horses: List[Dict[str, Any]]) -> str:
    """초반200 지수 기반 전개 요약."""
    vals = [h["초반200"] for h in horses if isinstance(h.get("초반200"), (int, float))]
    if not vals:
        return "초반 지표 부족으로 전개 판단 불가"

    avg = sum(vals) / len(vals)
    fronts = [h for h in horses if h.get("초반200", 0) >= 80]
    mids = [h for h in horses if 40 <= h.get("초반200", 0) < 80]
    closers = [h for h in horses if h.get("초반200", 0) < 40]

    if avg >= 80:
        desc = "매우 빠른 페이스(선행 과포화) 예상"
    elif avg >= 60:
        desc = "빠른 편 페이스 예상"
    elif avg >= 40:
        desc = "보통~중간 페이스 예상"
    else:
        desc = "느린 페이스(선행 부족) 예상"

    front_gates = ", ".join(str(int(h["gate"])) for h in fronts) if fronts else "없음"
    closer_gates = (
        ", ".join(str(int(h["gate"])) for h in closers) if closers else "거의 없음"
    )

    lines = [
        f"▶ 예상 페이스: {desc}",
        f"  - 평균 초반200 지수: {avg:.1f}",
        f"  - 선행형(초반200≥80): {len(fronts)}두",
        f"  - 중위권(40≤초반200<80): {len(mids)}두",
        f"  - 추입형(초반200<40): {len(closers)}두",
        "",
        f"  선행형 마번: {front_gates}",
        f"  추입형 마번: {closer_gates}",
    ]
    return "\n".join(lines)


# ==============================
# 2. 기본 능력 / final_score
# ==============================


def compute_base_score(h: Dict[str, Any]) -> float:
    """
    기본 능력 점수.
    (기록/종반/트렌드/기수·조교사 연대)
    """
    rec = h.get("기록점수") or 0.0
    last600 = h.get("종반600") or 0.0
    last200 = h.get("종반200") or 0.0
    trend = h.get("최근8경주트렌드점수") or 0.0
    jt = h.get("기수 조교사 연대점수") or 0.0

    return 0.25 * rec + 0.25 * last600 + 0.15 * last200 + 0.15 * trend + 0.20 * jt


def compute_final_score(h: Dict[str, Any]) -> float:
    """
    final_score = 기본 능력 + 폼 + 약간의 m_rank 보정
    (축/상대마 선정에 사용하는 핵심 점수)
    """
    base = compute_base_score(h)
    trend = float(h.get("최근8경주트렌드점수") or 0.0)
    last600 = float(h.get("종반600") or 0.0)
    mr = float(h.get("m_rank", 99) or 99)

    score = base + 0.2 * trend + 0.2 * last600 - 0.3 * (mr - 1)
    return score


def ability_score(h: Dict[str, Any]) -> float:
    """
    편성 내 비교용 '능력 점수':
    - compute_base_score(h)에
    - m_rank를 약한 페널티로 반영.
    (축 신뢰도 계산용)
    """
    base = compute_base_score(h)
    mr = float(h.get("m_rank", 99) or 99)
    mr_penalty = 0.5 * (mr - 1)
    return base - mr_penalty


# ==============================
# 3. 상대 비교 기반 축 신뢰도 (경주거리별 가중치 반영)
# ==============================


def ability_domination(anchor: Dict[str, Any], horses: List[Dict[str, Any]]) -> float:
    """
    실력 우위:
      - 앵커 ability_score vs (2~3위 평균) 차이를 0~100 점수로 매핑.
    """
    scores = [(h, ability_score(h)) for h in horses]
    scores_sorted = sorted(scores, key=lambda x: x[1], reverse=True)

    a_score = next(s for h, s in scores if h["horse"] == anchor["horse"])

    rivals = [s for h, s in scores_sorted[1:3]]  # 2~3위 점수
    if not rivals:
        return 100.0  # 단독출전급

    avg_rivals = sum(rivals) / len(rivals)
    gap = a_score - avg_rivals  # +면 축이 우위

    dom = 50 + 2.5 * gap  # gap=0 → 50점
    return max(0.0, min(100.0, dom))


def form_domination(anchor: Dict[str, Any], horses: List[Dict[str, Any]]) -> float:
    """
    거리별 착순 기여도 반영 폼/스피드 우위.
    """
    dist = float(anchor.get("경주거리") or 1200)
    zone = get_distance_zone(dist)
    w = DIST_WEIGHTS[zone]

    e_a = float(anchor.get("초반200", 0.0))
    g3_a = float(anchor.get("종반600", 0.0))
    g1_a = float(anchor.get("종반200", 0.0))
    t_a = float(anchor.get("최근8경주트렌드점수", 0.0))
    r_a = float(anchor.get("기록점수", 0.0))

    early_vals = [float(h.get("초반200") or 0.0) for h in horses]
    g3_vals = [float(h.get("종반600") or 0.0) for h in horses]
    g1_vals = [float(h.get("종반200") or 0.0) for h in horses]
    trend_vals = [float(h.get("최근8경주트렌드점수") or 0.0) for h in horses]
    rec_vals = [float(h.get("기록점수") or 0.0) for h in horses]

    avg_e = sum(early_vals) / len(early_vals) if early_vals else 0.0
    avg_g3 = sum(g3_vals) / len(g3_vals) if g3_vals else 0.0
    avg_g1 = sum(g1_vals) / len(g1_vals) if g1_vals else 0.0
    avg_t = sum(trend_vals) / len(trend_vals) if trend_vals else 0.0
    avg_r = sum(rec_vals) / len(rec_vals) if rec_vals else 0.0

    score_raw = (
        w["early"] * (e_a - avg_e)
        + w["g3f"] * (g3_a - avg_g3)
        + w["g1f"] * (g1_a - avg_g1)
        + w["trend"] * (t_a - avg_t)
        + w["rec"] * (r_a - avg_r)
    )

    score = 50 + score_raw / 2.5
    return max(0.0, min(100.0, score))


def competition_pressure(anchor: Dict[str, Any], horses: List[Dict[str, Any]]) -> float:
    """
    경쟁 압박:
      - 나와 ability_score 차이가 3점 이내인 '강한 라이벌' 수.
      - 많을수록 압박↑, 점수는 내려감.
      - 여기서는 '편하게 뛸 수 있는 정도'(높을수록 좋음)를 0~100으로 표현.
    """
    a_score = ability_score(anchor)
    scores = [ability_score(h) for h in horses if h["horse"] != anchor["horse"]]

    strong_rivals = [s for s in scores if s >= a_score - 3.0]
    n = len(strong_rivals)

    if n == 0:
        pressure = 90  # 독주
    elif n == 1:
        pressure = 70  # 2강
    elif n == 2:
        pressure = 50  # 3강
    else:
        pressure = 30  # 다수 강자 존재

    return pressure


def calc_anchor_trust(
    anchor: Dict[str, Any], horses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    축 신뢰도 (경주거리별 기여도 반영 최종 구조)

    축_신뢰도 =
        0.45 × Ability Domination
      + 0.35 × Form Domination
      + 0.20 × Competition Pressure
    """
    a_dom = ability_domination(anchor, horses)
    f_dom = form_domination(anchor, horses)
    comp = competition_pressure(anchor, horses)

    trust_score = 0.45 * a_dom + 0.35 * f_dom + 0.20 * comp

    if trust_score >= 80:
        level = "강축"
    elif trust_score >= 60:
        level = "보통축"
    else:
        level = "불안축"  # = 약한축

    return {
        "ability_domination": round(a_dom, 1),
        "form_domination": round(f_dom, 1),
        "competition_pressure": round(comp, 1),
        "trust_score": round(trust_score, 1),
        "trust_level": level,
    }


# ==============================
# 4. 경주 분석 (축/동반마 요약) – 축은 final_score 1위 사용
# ==============================


def analyze_race_simple(rows: List[Tuple[Any, ...]]) -> Dict[str, Any]:
    """
    - final_score 기준으로 축·동반마·전체 말 목록 정리.
    - 축_신뢰도는 calc_anchor_trust에서 별도 계산.
    """
    horses = [tuple_to_dict(r) for r in rows]

    # final_score 계산
    for h in horses:
        h["final_score"] = compute_final_score(h)

    # final_score 기준 정렬
    sorted_by_f = sorted(horses, key=lambda h: h["final_score"], reverse=True)
    key_horse = sorted_by_f[0]  # final_score 1위

    # 전개 요약
    pace_summary = summarize_pace(horses)

    # 동반마: final_score 2~5위
    companions = []
    for h in sorted_by_f[1:5]:
        companions.append(
            {
                "마번": int(h["gate"]),
                "마명": h["horse"],
                "final_score": round(h["final_score"], 2),
                "예상1": int(h.get("예상1", 99)),
                "예상2": int(h.get("예상2", 99)),
                "m_rank": int(h.get("m_rank", 99)),
                "트렌드": float(h.get("최근8경주트렌드점수") or 0.0),
                "종반600": float(h.get("종반600") or 0.0),
            }
        )

    return {
        "pace_summary": pace_summary,
        "key_horse": {
            "마번": int(key_horse["gate"]),
            "마명": key_horse["horse"],
            "final_score": round(key_horse["final_score"], 2),
            "m_rank": int(key_horse.get("m_rank", 0)),
            "예상1": int(key_horse.get("예상1", 99)),
            "예상2": int(key_horse.get("예상2", 99)),
            "트렌드": float(key_horse.get("최근8경주트렌드점수") or 0.0),
            "종반600": float(key_horse.get("종반600") or 0.0),
            "축_신뢰도": "미정",
        },
        "companions": companions,
        "horses_all": horses,
    }


# ==============================
# 5. 상위마 6두 (final_score 기준)
# ==============================


def select_six_by_final_score(horses: List[Dict[str, Any]]) -> List[int]:
    """final_score 기준 상위 6두 gate 리턴."""
    tmp = []
    for h in horses:
        if "final_score" not in h:
            h["final_score"] = compute_final_score(h)
        tmp.append(h)

    sorted_by_f = sorted(tmp, key=lambda h: h["final_score"], reverse=True)

    gates: List[int] = []
    for h in sorted_by_f:
        g = int(h.get("gate", 0))
        if g not in gates:
            gates.append(g)
        if len(gates) >= 6:
            break
    return sorted(gates)


# ==============================
# 6. 복병 선정 (선행 1, 추입 1 중 최종 1두) – 출주수 가산 포함
# ==============================


def find_dark_horses_simple(
    horses: List[Dict[str, Any]],
    main_gates: Set[int],
) -> List[Dict[str, Any]]:
    """
    - main_gates(상위 6두 등) 밖에서 복병 '최종 1두' 선정
      ▸ 선행 복병 후보 1두(front)
      ▸ 추입 복병 후보 1두(closer)
      ▸ 둘 중 score가 더 높은 한 마리만 최종 복병으로 사용
    - 출주수(통산 출주횟수) 3회 이하 말에게 약간의 가산점 부여
    """

    # main_gates에 포함되지 않은 말들만 후보
    others = [h for h in horses if int(h.get("gate", 0)) not in main_gates]
    if not others:
        return []

    # 편성 기준 평균값 계산
    early_vals = [h.get("초반200") for h in horses if h.get("초반200") is not None]
    last_vals = [h.get("종반600") for h in horses if h.get("종반600") is not None]
    trend_vals = [
        h.get("최근8경주트렌드점수")
        for h in horses
        if h.get("최근8경주트렌드점수") is not None
    ]
    rec_vals = [h.get("기록점수") for h in horses if h.get("기록점수") is not None]

    if not early_vals or not last_vals or not trend_vals or not rec_vals:
        return []

    avg_s1f = sum(early_vals) / len(early_vals)
    avg_g3f = sum(last_vals) / len(last_vals)
    avg_trend = sum(trend_vals) / len(trend_vals)
    avg_rec = sum(rec_vals) / len(rec_vals)

    # -----------------------------
    # 1) 선행 복병 스코어
    # -----------------------------
    def score_front(h: Dict[str, Any]) -> float:
        s1f = float(h.get("초반200") or 0.0)
        g3f = float(h.get("종반600") or 0.0)
        trend = float(h.get("최근8경주트렌드점수") or 0.0)
        age = float(h.get("마령") or 0.0)
        pop = float(h.get("예상2") or 99.0)
        rec = float(h.get("기록점수") or 0.0)
        starts = float(h.get("출주수") or 0.0)

        score = 0.0

        # 초반 스피드 우위
        score += 0.06 * (s1f - avg_s1f)
        # 막판도 어느 정도 받쳐주면 가산
        score += 0.03 * (g3f - avg_g3f)
        # 폼(트렌드)
        score += 0.04 * (trend - avg_trend)

        # 기록이 평균보다 많이 떨어지면 강한 감점
        if rec < avg_rec - 15:
            score -= 2.0 + (avg_rec - rec) / 20.0

        # 노장 선행 감점
        if age >= 7.0:
            score -= 0.5 * (age - 6.0)

        # 트렌드 너무 낮으면 감점
        if trend < 35.0:
            score -= 1.0

        # 인기 1~2위는 복병 느낌이 아니니까 살짝 감점
        if pop <= 2:
            score -= 0.5

        # 출주 3회 이하 가산
        if starts <= 2:
            score += 1.0
        elif starts <= 3:
            score += 0.5

        return score

    # -----------------------------
    # 2) 추입 복병 스코어
    # -----------------------------
    def score_closer(h: Dict[str, Any]) -> float:
        s1f = float(h.get("초반200") or 0.0)
        g3f = float(h.get("종반600") or 0.0)
        trend = float(h.get("최근8경주트렌드점수") or 0.0)
        age = float(h.get("마령") or 0.0)
        pop = float(h.get("예상2") or 99.0)
        rec = float(h.get("기록점수") or 0.0)
        starts = float(h.get("출주수") or 0.0)

        score = 0.0

        # 종반 + 폼을 강하게 가중
        score += 0.07 * (g3f - avg_g3f)
        score += 0.07 * (trend - avg_trend)

        # 초반 너무 느리면 감점
        if s1f < 15.0:
            score -= 1.0

        # 기록이 평균보다 많이 떨어지면 감점
        if rec < avg_rec - 10:
            score -= 1.0 + (avg_rec - rec) / 25.0

        # 노장 추입 감점
        if age >= 7.0:
            score -= 2.0 + 0.5 * (age - 7.0)

        # 폼 너무 나쁘면 감점
        if trend < 35.0:
            score -= 1.5

        # 인기 1~2위는 복병 느낌 아님
        if pop <= 2:
            score -= 0.5

        # 출주 3회 이하 가산
        if starts <= 2:
            score += 1.0
        elif starts <= 3:
            score += 0.5

        return score

    # -----------------------------
    # 3) 선행/추입 후보 각각 1두씩 선정
    # -----------------------------
    front_candidates = [h for h in others if h.get("초반200") is not None]
    best_front = None
    best_front_score = -999.0

    for h in front_candidates:
        s1f = float(h.get("초반200") or 0.0)
        # 선행 복병 최소 조건
        if s1f < max(75.0, avg_s1f + 5.0):
            continue

        s = score_front(h)
        if s > best_front_score:
            best_front = h
            best_front_score = s

    closer_candidates = [h for h in others if h.get("종반600") is not None]
    best_closer = None
    best_closer_score = -999.0

    for h in closer_candidates:
        g3f = float(h.get("종반600") or 0.0)
        # 추입 복병 최소 조건
        if g3f < max(65.0, avg_g3f + 3.0):
            continue

        s = score_closer(h)
        if s > best_closer_score:
            best_closer = h
            best_closer_score = s

    # -----------------------------
    # 4) 두 후보 중 score가 가장 좋은 한 마리만 최종 복병으로 선택
    # -----------------------------
    candidates: List[Dict[str, Any]] = []

    if best_front is not None and best_front_score >= 0.0:
        candidates.append(
            {
                "gate": int(best_front["gate"]),
                "마명": best_front["horse"],
                "type": "front",
                "초반200": float(best_front.get("초반200") or 0.0),
                "종반600": float(best_front.get("종반600") or 0.0),
                "트렌드": float(best_front.get("최근8경주트렌드점수") or 0.0),
                "마령": float(best_front.get("마령") or 0.0),
                "예상2": float(best_front.get("예상2") or 0.0),
                "기록점수": float(best_front.get("기록점수") or 0.0),
                "출주수": float(best_front.get("출주수") or 0.0),
                "score": round(best_front_score, 2),
            }
        )

    if best_closer is not None and best_closer_score >= -1.0:
        candidates.append(
            {
                "gate": int(best_closer["gate"]),
                "마명": best_closer["horse"],
                "type": "closer",
                "초반200": float(best_closer.get("초반200") or 0.0),
                "종반600": float(best_closer.get("종반600") or 0.0),
                "트렌드": float(best_closer.get("최근8경주트렌드점수") or 0.0),
                "마령": float(best_closer.get("마령") or 0.0),
                "예상2": float(best_closer.get("예상2") or 0.0),
                "기록점수": float(best_closer.get("기록점수") or 0.0),
                "출주수": float(best_closer.get("출주수") or 0.0),
                "score": round(best_closer_score, 2),
            }
        )

    if not candidates:
        return []

    # 최종 1두만 반환
    best_one = max(candidates, key=lambda x: x["score"])
    return [best_one]


# ==============================
# 7. 복조 베팅 플랜 (축 신뢰도 기반 전략 통합)
# ==============================


def make_quinella_plan_with_trust(
    horses: List[Dict[str, Any]],
    anchor_gate: int,
    trust_info: Dict[str, Any],
    dark_horses: List[Dict[str, Any]] | None,
    total_budget: int = 10000,
    unit: int = 100,
) -> Dict[str, Any]:
    """
    축 신뢰도별 전략:

    ▸ 강축:
        - 메인 80%: 축마 기준 상위마 5복조 (축-Top5 복조)
        - 서브 20%: (축-복병), (복병-Top5 복조)

    ▸ 보통축:
        - 메인 80%: 축마 상관 없이 final_score 상위 6두 복조 BOX
        - 서브 20%: 복병을 축으로 두고, 복병-Top6 복조

    ▸ 불안축(약한축):
        - 메인 60%: 축 없이 상위 6두 복조 BOX
        - 서브 40%: 복병축-Top6 복조

    dark_horses: find_dark_horses_simple() 결과 (최대 1두 가정)
    """
    anchor_gate = int(anchor_gate)
    trust_level = trust_info.get("trust_level", "보통축")
    trust_score = trust_info.get("trust_score", 0.0)

    # final_score 미계산 말 있으면 채우기
    for h in horses:
        if "final_score" not in h:
            h["final_score"] = compute_final_score(h)

    # gate → 말 dict 매핑
    by_gate: Dict[int, Dict[str, Any]] = {int(h["gate"]): h for h in horses}

    # 상위 6두 (final_score)
    top6_gates = select_six_by_final_score(horses)

    # 강축용: 축 제외 상위 5두
    others_sorted = sorted(
        [h for h in horses if int(h["gate"]) != anchor_gate],
        key=lambda x: x["final_score"],
        reverse=True,
    )
    top5_gates = [int(h["gate"]) for h in others_sorted[:5]]

    dark = dark_horses[0] if dark_horses else None
    dark_gate = int(dark["gate"]) if dark is not None else None

    main_tickets: List[Dict[str, Any]] = []
    sub_tickets: List[Dict[str, Any]] = []

    # -----------------------------
    # 전략별 티켓 생성
    # -----------------------------
    if trust_level == "강축":
        # ===== 강축: 축-Top5 복조 80% + (축-복병, 복병-Top5) 20% =====
        strategy_desc = "강축: 축-상대 5복조 80% + 축·복병 연계 20%"

        # 메인: 축-Top5 복조
        for g in top5_gates:
            combo = tuple(sorted((anchor_gate, g)))
            main_tickets.append(
                {
                    "combo": combo,
                    "type": "main",
                    "desc": "축-Top5 복조",
                }
            )

        # 서브: 축-복병, 복병-Top5
        if dark is not None:
            # (1) 축-복병
            if dark_gate != anchor_gate:
                sub_tickets.append(
                    {
                        "combo": tuple(sorted((anchor_gate, dark_gate))),
                        "type": "sub",
                        "desc": "축-복병 복조",
                    }
                )
            # (2) 복병-Top5
            for g in top5_gates:
                if g == dark_gate:
                    continue
                sub_tickets.append(
                    {
                        "combo": tuple(sorted((dark_gate, g))),
                        "type": "sub",
                        "desc": "복병-Top5 복조",
                    }
                )

        # 비율
        main_ratio = 0.80
        sub_ratio = 0.20

    elif trust_level == "보통축":
        # ===== 보통축: 상위 6복조 80% + 복병축-6복조 20% =====
        strategy_desc = "보통축: 상위 6복조 80% + 복병축-6복조 20% (축은 참고만)"

        # 메인: Top6 BOX 복조 (축 여부 상관 없음)
        for a, b in combinations(top6_gates, 2):
            combo = tuple(sorted((a, b)))
            main_tickets.append(
                {
                    "combo": combo,
                    "type": "main",
                    "desc": "Top6 복조",
                }
            )

        # 서브: 복병축-Top6 복조
        if dark is not None:
            for g in top6_gates:
                if g == dark_gate:
                    continue
                sub_tickets.append(
                    {
                        "combo": tuple(sorted((dark_gate, g))),
                        "type": "sub",
                        "desc": "복병축-Top6 복조",
                    }
                )

        main_ratio = 0.80
        sub_ratio = 0.20

    else:
        # ===== 불안축(약한축): 상위 6복조 60% + 복병축-6복조 40% =====
        strategy_desc = "약한축: 상위 6복조 60% + 복병축-6복조 40% (축 배제 전략)"

        # 메인: Top6 BOX 복조 (축 신뢰 낮으므로 축 개념 없이)
        for a, b in combinations(top6_gates, 2):
            combo = tuple(sorted((a, b)))
            main_tickets.append(
                {
                    "combo": combo,
                    "type": "main",
                    "desc": "Top6 복조",
                }
            )

        # 서브: 복병축-Top6 복조 (복병에 무게)
        if dark is not None:
            for g in top6_gates:
                if g == dark_gate:
                    continue
                sub_tickets.append(
                    {
                        "combo": tuple(sorted((dark_gate, g))),
                        "type": "sub",
                        "desc": "복병축-Top6 복조",
                    }
                )

        main_ratio = 0.60
        sub_ratio = 0.40

    # 복병 없으면 서브 티켓 제거하고 메인에 전부 배분
    if dark is None or not sub_tickets:
        main_ratio = 1.0
        sub_ratio = 0.0

    # -----------------------------
    # 금액 배분
    # -----------------------------
    main_budget = int(total_budget * main_ratio)
    sub_budget = total_budget - main_budget

    n_main = len(main_tickets)
    n_sub = len(sub_tickets)

    # 메인
    if n_main > 0 and main_budget > 0:
        per_main = main_budget / n_main
        for t in main_tickets:
            stake = int(per_main // unit * unit)
            t["stake"] = stake
    else:
        for t in main_tickets:
            t["stake"] = 0

    # 서브
    if n_sub > 0 and sub_budget > 0:
        per_sub = sub_budget / n_sub
        for t in sub_tickets:
            stake = int(per_sub // unit * unit)
            t["stake"] = stake
    else:
        for t in sub_tickets:
            t["stake"] = 0

    return {
        "anchor_gate": anchor_gate,
        "trust_level": trust_level,
        "trust_score": trust_score,
        "strategy_desc": strategy_desc,
        "top6_gates": top6_gates,
        "top5_gates": top5_gates,
        "dark_horse": dark,
        "total_budget": total_budget,
        "main_ratio": main_ratio,
        "sub_ratio": sub_ratio,
        "main_tickets": main_tickets,
        "sub_tickets": sub_tickets,
    }


def print_quinella_plan(
    horses: List[Dict[str, Any]],
    anchor_info: Dict[str, Any],
    plan: Dict[str, Any],
) -> None:
    anchor_gate = plan["anchor_gate"]
    trust_level = plan["trust_level"]
    trust_score = plan["trust_score"]

    print("\n==============================")
    print(f"=== 복조 베팅 플랜 (총 {plan['total_budget']}원) ===")
    print("==============================")
    print(
        f"축마: {anchor_gate}번 {anchor_info['마명']} "
        f"(final_score={anchor_info['final_score']:.2f})"
    )
    print(
        f"축 신뢰도: {trust_level} ({trust_score}점) "
        f"→ 전략: {plan['strategy_desc']}"
    )
    print(
        f"  · 메인 비중: {int(plan['main_ratio'] * 100)}% "
        f"/ 서브(보조) 비중: {int(plan['sub_ratio'] * 100)}%\n"
    )

    # 상위 final_score 리스트 출력
    print("▶ final_score 순위표")
    sorted_all = sorted(horses, key=lambda h: h["final_score"], reverse=True)
    for h in sorted_all:
        mark = ""
        g = int(h["gate"])
        if g == anchor_gate:
            mark = " (축)"
        if plan.get("dark_horse") and g == plan["dark_horse"]["gate"]:
            mark += " (복병)"
        print(
            f"  게이트 {g:2d} | {h['horse']:<10} | "
            f"final_score={h['final_score']:.2f}{mark}"
        )

    # 복병 정보
    print("\n▶ 복병 정보")
    dark = plan.get("dark_horse")
    if not dark:
        print("  복병 없음 (데이터/조건 미충족)")
    else:
        print(
            f"  복병: {dark['gate']}번 {dark['마명']} "
            f"({dark['type']}, 종반600={dark['종반600']:.1f}, "
            f"트렌드={dark['트렌드']:.1f}, 출주수={dark['출주수']:.0f}, "
            f"score={dark['score']:.2f})"
        )

    # 메인 티켓
    print("\n▶ 메인 베팅 (Main Tickets)")
    if not plan["main_tickets"]:
        print("  메인 베팅 없음")
    else:
        for t in plan["main_tickets"]:
            if t.get("stake", 0) <= 0:
                continue
            a, b = t["combo"]
            desc = t.get("desc", "")
            print(f"  {a} - {b}  복조 : {t['stake']}원  ({desc})")

    # 서브 티켓
    print("\n▶ 서브(보조) 베팅 (Sub Tickets)")
    if not plan["sub_tickets"]:
        print("  서브 베팅 없음")
    else:
        for t in plan["sub_tickets"]:
            if t.get("stake", 0) <= 0:
                continue
            a, b = t["combo"]
            desc = t.get("desc", "")
            print(f"  {a} - {b}  복조 : {t['stake']}원  ({desc})")


# ==============================
# 8. DB 연결 & 로더
# ==============================


def get_conn():
    """MySQL 접속 정보 (환경에 맞게 수정)."""
    return pymysql.connect(
        host="database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",
        user="letslove",
        password="Ruddksp!23",
        db="The1",
        port=3306,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def load_race_exp011(rcity: str, rdate: str, rno: int) -> pd.DataFrame:
    query = """
        SELECT 
            e.rcity,
            e.rdate,
            e.rno,
            (
                SELECT distance
                FROM The1.exp010 t
                WHERE t.rcity = e.rcity
                  AND t.rdate = e.rdate
                  AND t.rno   = e.rno
            ) AS `경주거리`,
            e.gate,
            e.horse,
            e.h_weight AS `마체중`,
            e.h_age    AS `마령`,
            e.h_sex    AS `성별`,
            e.i_cycle  AS `출주갭`,
            e.rank     AS `예상1`,
            e.r_pop    AS `예상2`,
            e.m_rank,
            e.s1f_per  AS `초반200`,
            e.g3f_per  AS `종반600`,
            e.g1f_per  AS `종반200`,
            e.rec_per  AS `기록점수`,
            e.rec8_trend AS `최근8경주트렌드점수`,
            e.jt_score AS `기수 조교사 연대점수`,
            e.comment_one AS `코멘트`,
            e.g2f_rank AS `최근8경주 요약`,
            e.year_race AS `출주수`
        FROM The1.exp011 e
        WHERE e.rcity = %s
          AND e.rdate = %s
          AND e.rno   = %s
    """
    with closing(get_conn()) as conn:
        df = pd.read_sql(query, conn, params=(rcity, rdate, rno))
    return df


# ==============================
# 9. 메인 실행 예시
# ==============================

if __name__ == "__main__":
    # 예: 서울 2025-12-07 6R
    rcity = "부산"
    rdate = "20251205"
    rno = 4

    df = load_race_exp011(rcity, rdate, rno)

    if df.empty:
        print("데이터 없음")
    else:
        rows: List[Tuple[Any, ...]] = list(df.itertuples(index=False, name=None))

        # 1) 경주 분석 (final_score 기준 축/동반마 + 전개 요약)
        analysis = analyze_race_simple(rows)
        print("=== 경주 전개 요약 ===")
        print(analysis["pace_summary"])

        print("\n=== 축마 추천 (final_score 기준) ===")
        print(
            f"축마 게이트: {analysis['key_horse']['마번']}, "
            f"마명: {analysis['key_horse']['마명']}, "
            f"final_score: {analysis['key_horse']['final_score']}"
        )

        print("\n=== 동반 입상마(참고용, final_score 2~5위) ===")
        for c in analysis["companions"]:
            print(c)

        # 2) 축 신뢰도 (편성 내 상대 비교 + 경주거리별 가중치 반영)
        horses_dict_list = analysis["horses_all"]
        anchor_gate = analysis["key_horse"]["마번"]
        anchor = next(h for h in horses_dict_list if int(h["gate"]) == anchor_gate)

        trust = calc_anchor_trust(anchor, horses_dict_list)
        analysis["key_horse"]["축_신뢰도"] = trust["trust_level"]

        print("\n=== 축 신뢰도 (상대 비교 + 거리 가중치) ===")
        print(trust)

        # 3) final_score 기준 상위 6두 (복병 선정용)
        six_gates = set(select_six_by_final_score(horses_dict_list))
        print("\n=== 상위 final_score 기준 6두 (게이트) ===")
        print(sorted(list(six_gates)))

        # 4) 복병 1두 선정
        dark_horses = find_dark_horses_simple(horses_dict_list, six_gates)

        print("\n=== 복병 후보 ===")
        if not dark_horses:
            print("복병 없음")
        else:
            d = dark_horses[0]
            print(
                f"복병: 마번 {d['gate']} {d['마명']} "
                f"({d['type']}, 종반600={d['종반600']:.1f}, "
                f"트렌드={d['트렌드']:.1f}, 출주수={d['출주수']:.0f}, "
                f"score={d['score']:.2f})"
            )

        # 5) 복조 베팅 플랜 생성 (총 10,000원, 축/복병/상위마 전략 자동 반영)
        plan = make_quinella_plan_with_trust(
            horses=horses_dict_list,
            anchor_gate=anchor_gate,
            trust_info=trust,
            dark_horses=dark_horses,
            total_budget=10000,
            unit=100,
        )

        # 6) 사람용 가이드 출력
        print_quinella_plan(horses_dict_list, analysis["key_horse"], plan)
