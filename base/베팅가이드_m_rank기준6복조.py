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
    "출주수",  # ← 통산 출주횟수
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
        "출주수",  # ← 추가
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
# 2. 기본 능력 점수 (r_pop 몸통 비슷)
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


def ability_score(h: Dict[str, Any]) -> float:
    """
    편성 내 비교용 '능력 점수':
    - compute_base_score(h)에
    - m_rank를 약한 페널티로 반영.
    """
    base = compute_base_score(h)
    mr = float(h.get("m_rank", 99) or 99)

    # m_rank 1위면 0, 2위 -0.5, 3위 -1.0 ... 살짝만 반영
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

    # gap=0 → 50점, +5점 → 62.5, +10점 → 75, +20점 → 100 근처
    dom = 50 + 2.5 * gap
    return max(0.0, min(100.0, dom))


def form_domination(anchor: Dict[str, Any], horses: List[Dict[str, Any]]) -> float:
    """
    2024~2025 한국경마 거리별 '착순 기여도 비중' 반영 폼/스피드 우위:
      - short(1000~1200m), middle(1300~1600m), long(1700m↑) 별로
        초반/종반/트렌드/기록 가중치를 다르게 적용.
    """
    dist = float(anchor.get("경주거리") or 1200)
    zone = get_distance_zone(dist)
    w = DIST_WEIGHTS[zone]

    e_a = float(anchor.get("초반200", 0.0))
    g3_a = float(anchor.get("종반600", 0.0))
    g1_a = float(anchor.get("종반200", 0.0))
    t_a = float(anchor.get("최근8경주트렌드점수", 0.0))
    r_a = float(anchor.get("기록점수", 0.0))

    # 편성 평균
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

    # 거리 기반 가중치 적용
    score_raw = (
        w["early"] * (e_a - avg_e)
        + w["g3f"] * (g3_a - avg_g3)
        + w["g1f"] * (g1_a - avg_g1)
        + w["trend"] * (t_a - avg_t)
        + w["rec"] * (r_a - avg_r)
    )

    # 스케일 매핑 (0~100 근처)
    score = 50 + score_raw / 2.5
    return max(0.0, min(100.0, score))


def competition_pressure(anchor: Dict[str, Any], horses: List[Dict[str, Any]]) -> float:
    """
    경쟁 압박:
      - 나와 ability_score 차이가 3점 이내인 '강한 라이벌' 수.
      - 많을수록 압박↑, 점수는 내려감.
      - 이 함수에서는 '편하게 뛸 수 있는 정도'를 0~100으로 표현.
    """
    a_score = ability_score(anchor)
    scores = [ability_score(h) for h in horses if h["horse"] != anchor["horse"]]

    strong_rivals = [s for s in scores if s >= a_score - 3.0]
    n = len(strong_rivals)

    if n == 0:
        pressure = 90  # 편하게 뛸 수 있음 (독주)
    elif n == 1:
        pressure = 70  # 2강
    elif n == 2:
        pressure = 50  # 3강
    else:
        pressure = 30  # 4강 이상 혼전

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
    a_dom = ability_domination(anchor, horses)  # 실력 우위
    f_dom = form_domination(anchor, horses)  # 폼/스피드 우위(거리 반영)
    comp = competition_pressure(anchor, horses)  # 경쟁 압박(높을수록 편한 편성)

    trust_score = 0.45 * a_dom + 0.35 * f_dom + 0.20 * comp

    if trust_score >= 80:
        level = "강축"
    elif trust_score >= 60:
        level = "보통축"
    else:
        level = "불안축"

    return {
        "ability_domination": round(a_dom, 1),
        "form_domination": round(f_dom, 1),
        "competition_pressure": round(comp, 1),
        "trust_score": round(trust_score, 1),
        "trust_level": level,
    }


# ==============================
# 4. 경주 분석 (m_rank 기반)
# ==============================


def analyze_race_simple(rows: List[Tuple[Any, ...]]) -> Dict[str, Any]:
    """
    - m_rank 기준으로 축·동반마·전체 말 목록을 정리.
    - 축_신뢰도는 calc_anchor_trust에서 별도 계산.
    """
    horses = [tuple_to_dict(r) for r in rows]

    # m_rank 기준 정렬
    def key_m(h):
        mr = h.get("m_rank", math.inf)
        try:
            mr = float(mr)
        except (ValueError, TypeError):
            mr = math.inf
        return mr

    sorted_by_m = sorted(horses, key=key_m)
    key_horse = sorted_by_m[0]  # m_rank 1위

    # 전개 요약
    pace_summary = summarize_pace(horses)

    # 동반마: m_rank 2~5위
    companions = []
    for h in sorted_by_m[1:5]:
        companions.append(
            {
                "마번": int(h["gate"]),
                "마명": h["horse"],
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
# 5. 6복조 선정 (m_rank 기준)
# ==============================


def select_six_by_mrank(horses: List[Dict[str, Any]]) -> List[int]:
    """m_rank 기준 상위 6두 gate 리턴."""
    sorted_by_m = sorted(horses, key=lambda h: h.get("m_rank", 9999))
    gates: List[int] = []
    for h in sorted_by_m:
        g = int(h.get("gate", 0))
        if g not in gates:
            gates.append(g)
        if len(gates) >= 6:
            break
    return sorted(gates)


# ==============================
# 6. 복병 (초반·막판 1두씩만, 출주수 가중치 포함)
# ==============================


def find_dark_horses_simple(
    horses: List[Dict[str, Any]],
    main_gates: Set[int],
) -> List[Dict[str, Any]]:
    """
    - 6복조(main_gates) 밖에서 복병 1~2두 선정
      ▸ 선행 복병 1두(front)
      ▸ 추입 복병 1두(closer)
    - 출주수(통산 출주횟수) 3회 이하인 말에게 약간의 가산점 부여
    """

    # 6복조 바깥 말들만 복병 후보
    others = [h for h in horses if int(h.get("gate", 0)) not in main_gates]
    if not others:
        return []

    # 편성 기준 평균값
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

    dark_list: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 1) 선행 복병 스코어 함수 (출주수 가산 포함)
    # ------------------------------------------------------------------
    def score_front(h: Dict[str, Any]) -> float:
        s1f = float(h.get("초반200") or 0.0)
        g3f = float(h.get("종반600") or 0.0)
        trend = float(h.get("최근8경주트렌드점수") or 0.0)
        age = float(h.get("마령") or 0.0)
        pop = float(h.get("예상2") or 99.0)
        rec = float(h.get("기록점수") or 0.0)
        starts = float(h.get("출주수") or 0.0)  # ★ 출주수

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

        # 인기 1~2위는 '복병' 느낌이 아니니까 살짝 감점
        if pop <= 2:
            score -= 0.5

        # ✅ 출주수 3회 이하 말에 가산점 (잠재력 보너스)
        #    - 완전 신마(1~2회)는 +1.0
        #    - 3회 정도는 +0.5 정도로 살짝
        if starts <= 2:
            score += 1.0
        elif starts <= 3:
            score += 0.5

        return score

    # ------------------------------------------------------------------
    # 2) 추입 복병 스코어 함수 (출주수 가산 포함)
    # ------------------------------------------------------------------
    def score_closer(h: Dict[str, Any]) -> float:
        s1f = float(h.get("초반200") or 0.0)
        g3f = float(h.get("종반600") or 0.0)
        trend = float(h.get("최근8경주트렌드점수") or 0.0)
        age = float(h.get("마령") or 0.0)
        pop = float(h.get("예상2") or 99.0)
        rec = float(h.get("기록점수") or 0.0)
        starts = float(h.get("출주수") or 0.0)  # ★ 출주수

        score = 0.0

        # 종반 우위 (주력)
        score += 0.07 * (g3f - avg_g3f)
        # 폼(트렌드)
        score += 0.07 * (trend - avg_trend)

        # 초반: 너무 느리면 감점만
        if s1f < 15.0:
            score -= 1.0

        # 기록이 평균보다 많이 떨어지면 감점
        if rec < avg_rec - 10:
            score -= 1.0 + (avg_rec - rec) / 25.0

        # 노장 추입 감점
        if age >= 7.0:
            score -= 2.0 + 0.5 * (age - 7.0)

        # 트렌드 너무 낮으면 폼 악화 감점
        if trend < 35.0:
            score -= 1.5

        # 인기 1~2위는 복병 느낌 아님
        if pop <= 2:
            score -= 0.5

        # ✅ 출주수 3회 이하 추입마 가산점
        if starts <= 2:
            score += 1.0
        elif starts <= 3:
            score += 0.5

        return score

    # ------------------------------------------------------------------
    # 선행 복병 선정
    # ------------------------------------------------------------------
    front_candidates = [h for h in others if h.get("초반200") is not None]
    best_front = None
    best_front_score = -999.0

    for h in front_candidates:
        s1f = float(h.get("초반200") or 0.0)
        # 선행 복병 최소 조건: 꽤 빠른 편
        if s1f < max(75.0, avg_s1f + 5.0):
            continue

        s = score_front(h)
        if s > best_front_score:
            best_front = h
            best_front_score = s

    used_gates: Set[int] = set()

    # 선행 복병은 '확실히 플러스'일 때만 선택
    if best_front is not None and best_front_score >= 0.0:
        dark_list.append(
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
        used_gates.add(int(best_front["gate"]))

    # ------------------------------------------------------------------
    # 추입 복병 선정
    # ------------------------------------------------------------------
    closer_candidates = [h for h in others if h.get("종반600") is not None]
    best_closer = None
    best_closer_score = -999.0

    for h in closer_candidates:
        gate = int(h.get("gate", 0))
        if gate in used_gates:
            continue

        g3f = float(h.get("종반600") or 0.0)
        # 추입 복병 최소 조건: 종반이 편성 평균보다 약간은 좋아야 함
        if g3f < max(65.0, avg_g3f + 3.0):
            continue

        s = score_closer(h)
        if s > best_closer_score:
            best_closer = h
            best_closer_score = s

    # 추입 복병은 살짝 마이너스까지 허용 (컷 기준 -1.0)
    if best_closer is not None and best_closer_score >= -1.0:
        dark_list.append(
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

    return dark_list


# ==============================
# 7. 6복조 + 복병 베팅 플랜 (축 신뢰도 반영)
# ==============================


def make_6box_plan_with_trust(
    analysis: Dict[str, Any],
    trust_info: Dict[str, Any],
    total_budget: int,
    unit: int = 100,
) -> Dict[str, Any]:
    """
    ▸ 기본: m_rank 기준 상위 6두로 6복조(C(6,3)=20구멍)
    ▸ trust_info['trust_level']에 따라
        - 축 포함/비축 조합 가중치 조절
        - 복병 예산 비율 조절
    """
    anchor_info = analysis["key_horse"]
    anchor_gate = int(anchor_info["마번"])
    horses = analysis["horses_all"]

    # 1) 6복조 마번 6두
    six_gates = select_six_by_mrank(horses)
    if anchor_gate not in six_gates:
        six_gates[0] = anchor_gate
        six_gates = sorted(set(six_gates))

    # 2) 복병 선정
    darks = find_dark_horses_simple(horses, set(six_gates))

    # 3) trust_level 기반 예산·가중치
    trust_level = trust_info["trust_level"]
    trust_score = trust_info["trust_score"]

    if trust_level == "강축":
        main_ratio = 0.9
        dark_ratio = 0.1
        w_anchor, w_non = 4.0, 1.0
    elif trust_level == "보통축":
        main_ratio = 0.8
        dark_ratio = 0.2
        w_anchor, w_non = 2.0, 1.5
    else:  # "불안축"
        main_ratio = 0.7
        dark_ratio = 0.3
        w_anchor, w_non = 1.5, 2.0

    # 4) 6복조 조합
    main_combos = list(combinations(six_gates, 3))
    main_infos = []
    total_weight = 0.0
    for c in main_combos:
        has_anchor = anchor_gate in c
        w = w_anchor if has_anchor else w_non
        combo = tuple(sorted(c))
        main_infos.append({"combo": combo, "has_anchor": has_anchor, "weight": w})
        total_weight += w

    main_budget = int(total_budget * main_ratio)
    stake_per_weight = main_budget / total_weight if total_weight > 0 else 0.0

    for info in main_infos:
        raw = stake_per_weight * info["weight"]
        info["stake"] = int(raw // unit * unit)

    # 5) 복병 조합: 복병 1두 + 6복조 중 2두
    dark_infos = []
    dark_budget = total_budget - main_budget
    if darks and dark_budget > 0 and dark_ratio > 0:
        temp = []
        for d in darks:
            dg = d["gate"]
            for a, b in combinations(six_gates, 2):
                combo = tuple(sorted((dg, a, b)))
                temp.append(
                    {
                        "combo": combo,
                        "dark_gate": dg,
                        "has_anchor": anchor_gate in combo,
                    }
                )

        per = dark_budget / len(temp) if temp else 0.0
        for x in temp:
            x["stake"] = int(per // unit * unit)
            dark_infos.append(x)

    return {
        "six_gates": six_gates,
        "anchor_gate": anchor_gate,
        "trust_level": trust_level,
        "trust_score": trust_score,
        "dark_horses": darks,
        "main_tickets": main_infos,
        "dark_tickets": dark_infos,
        "total_budget": total_budget,
    }


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
    # 예: 서울 2025-12-07 3R
    rcity = "부산"
    rdate = "20251205"
    rno = 4

    df = load_race_exp011(rcity, rdate, rno)

    if df.empty:
        print("데이터 없음")
    else:
        rows: List[Tuple[Any, ...]] = list(df.itertuples(index=False, name=None))

        # 1) 경주 분석 (m_rank 기준 축/동반마 + 전개 요약)
        analysis = analyze_race_simple(rows)
        print("=== 경주 전개 요약 ===")
        print(analysis["pace_summary"])

        print("\n=== 축마 추천 (m_rank 기준) ===")
        print(analysis["key_horse"])

        print("\n=== 동반 입상마(참고용, m_rank 2~5위) ===")
        for c in analysis["companions"]:
            print(c)

        # 2) 축 신뢰도 (편성 내 상대 비교 + 경주거리별 가중치 반영)
        horses_dict_list = analysis["horses_all"]
        anchor_gate = analysis["key_horse"]["마번"]
        anchor = next(h for h in horses_dict_list if int(h["gate"]) == anchor_gate)

        trust = calc_anchor_trust(anchor, horses_dict_list)
        # key_horse에 축_신뢰도 정보 반영
        analysis["key_horse"]["축_신뢰도"] = trust["trust_level"]

        print("\n=== 축 신뢰도 (상대 비교 + 거리 가중치) ===")
        print(trust)

        # 3) 6복조 + 복병 베팅 플랜 생성
        total_budget = 19000  # 총 베팅금 (예: 19,000원)
        plan = make_6box_plan_with_trust(
            analysis=analysis,
            trust_info=trust,
            total_budget=total_budget,
            unit=100,
        )

        print("\n=== 6복조 기준 추천 마번 6두 ===")
        print("6두:", plan["six_gates"])
        print(
            "축마:",
            plan["anchor_gate"],
            "/ 축 신뢰도:",
            plan["trust_level"],
            f"({plan['trust_score']}점)",
        )

        print("\n=== 복병 후보 ===")
        if not plan["dark_horses"]:
            print("복병 없음")
        else:
            for d in plan["dark_horses"]:
                print(
                    f"마번 {d['gate']} {d['마명']} ({d['type']} / 출주수 {d['출주수']}, score {d['score']})"
                )

        print("\n=== 6복조 메인 베팅 ===")
        for t in plan["main_tickets"]:
            if t["stake"] <= 0:
                continue
            tag = "★축포함" if t["has_anchor"] else "  비축"
            print(f"{tag} 조합 {t['combo']} : {t['stake']}원")

        print("\n=== 복병 조합 베팅 ===")
        if not plan["dark_tickets"]:
            print("복병 조합 없음")
        else:
            for t in plan["dark_tickets"]:
                tag = "★축포함" if t["has_anchor"] else "  비축"
                print(
                    f"{tag} [복병 {t['dark_gate']}] 조합 {t['combo']} : {t['stake']}원"
                )
