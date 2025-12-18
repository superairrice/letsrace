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

# 거리 구간별 기록 기여도 가중치 (착순 기여도 기반)
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
# 1. 공통 유틸 + 신마 판단
# ==============================


def _norm_num(v):
    """숫자 컬럼용: NaN -> None, 나머지는 float 캐스팅."""
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    return x


def is_empty_val(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return False


def is_new_horse(h: Dict[str, Any]) -> bool:
    """
    신마 / 데이터 부족 말 판단:
    - 초반200, 종반600, 기록점수, 트렌드가 전부 비어있으면 신마로 간주
    """
    keys = ["초반200", "종반600", "기록점수", "최근8경주트렌드점수"]
    return all(is_empty_val(h.get(k)) for k in keys)


def tuple_to_dict(row: Tuple[Any, ...]) -> Dict[str, Any]:
    """SELECT 결과 튜플을 컬럼명 딕셔너리로 변환."""
    d = {col: row[i] for i, col in enumerate(COLUMNS)}

    num_cols = [
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
    ]
    for num_col in num_cols:
        d[num_col] = _norm_num(d.get(num_col))

    return d


def summarize_pace(
    horses: List[Dict[str, Any]],
) -> Tuple[str, float, List[int], List[int]]:
    """
    초반200 지수 기반 전개 요약 (NaN/None 방어 포함).
    반환: (문자열 요약, 평균 초반200, 선행 게이트 리스트, 추입 게이트 리스트)
    """
    vals: List[float] = []
    for h in horses:
        v = h.get("초반200")
        if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
            vals.append(float(v))

    if not vals:
        text = "초반 지표 부족으로 전개 판단 불가"
        return text, float("nan"), [], []

    avg = sum(vals) / len(vals)

    fronts: List[Dict[str, Any]] = []
    mids: List[Dict[str, Any]] = []
    closers: List[Dict[str, Any]] = []
    for h in horses:
        v = h.get("초반200")
        if not isinstance(v, (int, float)) or (isinstance(v, float) and math.isnan(v)):
            continue
        v = float(v)
        if v >= 80:
            fronts.append(h)
        elif v >= 40:
            mids.append(h)
        else:
            closers.append(h)

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
    return (
        "\n".join(lines),
        avg,
        [int(h["gate"]) for h in fronts],
        [int(h["gate"]) for h in closers],
    )


# ==============================
# 2. 기본 능력 / 스타일 / final_score
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


def compute_style_score(h: Dict[str, Any]) -> float:
    """
    스타일 점수: 경주거리 / 페이스에 따라 초반/종반 가중치 차등.
    (페이스는 직접 안 넘기고, 거리 기반으로만 단순화)
    """
    dist = float(h.get("경주거리") or 1200)
    zone = get_distance_zone(dist)

    early = float(h.get("초반200") or 0.0)
    late = float(h.get("종반600") or 0.0)
    trend = float(h.get("최근8경주트렌드점수") or 0.0)

    if zone == "short":
        # 단거리: 초반 비중↑
        w_e, w_l, w_t = 0.55, 0.30, 0.15
    elif zone == "middle":
        # 중거리: 초반/종반 균형
        w_e, w_l, w_t = 0.40, 0.40, 0.20
    else:
        # 장거리: 종반 비중↑
        w_e, w_l, w_t = 0.25, 0.55, 0.20

    return w_e * early + w_l * late + w_t * trend


def compute_final_score(h: Dict[str, Any]) -> float:
    """
    final_score = 기본 능력 + 스타일 + (약한 m_rank 가점)

    ▸ m_rank가 좋을수록(1위에 가까울수록) 약하게 보너스.
    """
    base = compute_base_score(h)
    style = compute_style_score(h)

    mr = h.get("m_rank")
    if mr is None or math.isnan(mr):
        mr = 10.0
    mr = float(mr)

    # m_rank 1위일수록 보너스, 10위 이후는 거의 영향 x
    mr_bonus = max(0.0, (10.0 - mr)) * 0.4

    score = base * 0.6 + style * 0.4 + mr_bonus
    return score


def ability_score(h: Dict[str, Any]) -> float:
    """
    편성 내 비교용 '능력 점수':
    - compute_base_score(h)을 기반으로,
    - m_rank에 약한 보너스를 주는 버전 (축 신뢰도 계산용)
    """
    base = compute_base_score(h)
    mr = h.get("m_rank")
    if mr is None or math.isnan(mr):
        mr = 10.0
    mr = float(mr)
    mr_bonus = max(0.0, (10.0 - mr)) * 0.2
    return base + mr_bonus


# ==============================
# 3. 상대 비교 기반 축 신뢰도
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
    거리별 착순 기여도 비중 반영 폼/스피드 우위.
    """
    dist = float(anchor.get("경주거리") or 1200)
    zone = get_distance_zone(dist)
    w = DIST_WEIGHTS[zone]

    e_a = float(anchor.get("초반200", 0.0) or 0.0)
    g3_a = float(anchor.get("종반600", 0.0) or 0.0)
    g1_a = float(anchor.get("종반200", 0.0) or 0.0)
    t_a = float(anchor.get("최근8경주트렌드점수", 0.0) or 0.0)
    r_a = float(anchor.get("기록점수", 0.0) or 0.0)

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
    경쟁 압박 (강한 라이벌 수가 많을수록 점수↓).
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
    축 신뢰도

    축_신뢰도 =
        0.45 × Ability Domination
      + 0.35 × Form Domination
      + 0.20 × Competition Pressure
    """
    a_dom = ability_domination(anchor, horses)  # 실력 우위
    f_dom = form_domination(anchor, horses)  # 폼/스피드 우위
    comp = competition_pressure(anchor, horses)  # 경쟁 압박

    trust_score = 0.45 * a_dom + 0.35 * f_dom + 0.20 * comp

    # 5단계 축 신뢰도 구간
    if trust_score >= 90:
        level = "초강축"  # 거의 필승/철벽 축 느낌
    elif trust_score >= 75:
        level = "강축"  # 믿을만한 강축
    elif trust_score >= 60:
        level = "보통축"  # 평범한 축, 기본 승부
    elif trust_score >= 45:
        level = "약한축"  # 애매한 축, 소액 분산
    else:
        level = "위험축"  # 축 자체가 불안, 관망/소액

    return {
        "ability_domination": round(a_dom, 1),
        "form_domination": round(f_dom, 1),
        "competition_pressure": round(comp, 1),
        "trust_score": round(trust_score, 1),
        "trust_level": level,
    }


# ==============================
# 4. m_rank / final_score 혼합 6복조 라인
# ==============================


def get_top6_by_mrank(horses: List[Dict[str, Any]]) -> List[int]:
    """m_rank 기준 상위 6두 gate 리턴."""
    valid = [h for h in horses if h.get("m_rank") is not None]
    sorted_m = sorted(valid, key=lambda x: float(x.get("m_rank") or 99))
    gates: List[int] = []
    for h in sorted_m:
        g = int(h.get("gate", 0))
        if g not in gates:
            gates.append(g)
        if len(gates) >= 6:
            break
    return gates


def determine_race_regime_and_top6(
    horses: List[Dict[str, Any]], anchor_gate: int
) -> Dict[str, Any]:
    """
    m_rank 기준 top6를 기본으로 두고,
    final_score를 이용해 약간 조정.

    - regime = 'clean' : m_rank top6와 final top6가 많이 겹치는 편
    - regime = 'chaos' : 두 랭킹이 많이 다른 편
    """
    # final_score 미리 계산
    for h in horses:
        if "final_score" not in h or h["final_score"] is None:
            h["final_score"] = compute_final_score(h)

    # 1) m_rank top6
    top6_mrank = get_top6_by_mrank(horses)

    # 2) final_score top6
    sorted_by_final = sorted(horses, key=lambda x: x["final_score"], reverse=True)
    top6_final = []
    for h in sorted_by_final:
        g = int(h.get("gate", 0))
        if g not in top6_final:
            top6_final.append(g)
        if len(top6_final) >= 6:
            break

    overlap = len(set(top6_mrank) & set(top6_final))
    regime = "clean" if overlap >= 4 else "chaos"

    # 3) 기본은 m_rank top6로 시작
    adjusted = list(top6_mrank)

    # anchor가 top6에 없으면 무조건 포함
    if anchor_gate not in adjusted:
        if len(adjusted) < 6:
            adjusted.append(anchor_gate)
        else:
            # final_score 가장 낮은 말 하나를 anchor로 교체
            min_final = None
            min_gate = None
            for g in adjusted:
                h = next(hh for hh in horses if int(hh["gate"]) == g)
                fs = h["final_score"]
                if (min_final is None) or (fs < min_final and g != anchor_gate):
                    min_final = fs
                    min_gate = g
            if min_gate is not None:
                adjusted.remove(min_gate)
                adjusted.append(anchor_gate)

    # 4) final_score 관점에서 너무 좋은데 m_rank top6에 없는 말이 있으면 한두 마리 교체
    candidate_new = [g for g in top6_final if g not in adjusted]
    if candidate_new:
        threshold_gap = 8.0 if regime == "clean" else 4.0
        for g_new in candidate_new:
            h_new = next(hh for hh in horses if int(hh["gate"]) == g_new)
            fs_new = h_new["final_score"]

            # adjusted 중에서 final_score 최하위 말 찾기 (anchor는 교체 제외)
            min_final = None
            min_gate = None
            for g in adjusted:
                if g == anchor_gate:
                    continue
                h_old = next(hh for hh in horses if int(hh["gate"]) == g)
                fs_old = h_old["final_score"]
                if (min_final is None) or (fs_old < min_final):
                    min_final = fs_old
                    min_gate = g

            if min_gate is None:
                continue

            if fs_new - min_final >= threshold_gap:
                adjusted.remove(min_gate)
                adjusted.append(g_new)

    adjusted = sorted(set(adjusted))
    # 6두가 되도록 보정
    if len(adjusted) > 6:
        # final_score 높은 순으로 6두 선택
        sorted_adj = sorted(
            adjusted,
            key=lambda g: next(hh for hh in horses if int(hh["gate"]) == g)[
                "final_score"
            ],
            reverse=True,
        )
        adjusted = sorted(sorted_adj[:6])
    elif len(adjusted) < 6:
        # 부족하면 final_score 순으로 채워넣기
        for h in sorted_by_final:
            g = int(h.get("gate", 0))
            if g not in adjusted:
                adjusted.append(g)
            if len(adjusted) >= 6:
                break
        adjusted = sorted(adjusted)

    return {
        "race_regime": regime,
        "top6_mrank": sorted(top6_mrank),
        "top6_adjusted": adjusted,
    }


# ==============================
# 5. 경주 분석 (final_score 기준 축/동반마)
# ==============================


def analyze_race_simple(rows: List[Tuple[Any, ...]]) -> Dict[str, Any]:
    """
    - 전체 말: pace / 신마 카운트용
    - 평가/베팅 대상: 신마 제외
    - final_score 기준으로 축·동반마·전체 말 목록 정리
    """
    horses_all = [tuple_to_dict(r) for r in rows]
    horses_eval = [h for h in horses_all if not is_new_horse(h)]

    # 전개 요약 (전체 말 기준)
    pace_summary_text, avg_early, fronts, closers = summarize_pace(horses_all)

    if not horses_eval:
        raise ValueError("평가 가능한 말이 없습니다. (모두 신마/데이터 부족)")

    # final_score / style_score 계산
    for h in horses_eval:
        h["style_score"] = compute_style_score(h)
        h["final_score"] = compute_final_score(h)

    sorted_by_f = sorted(horses_eval, key=lambda h: h["final_score"], reverse=True)
    key_horse = sorted_by_f[0]

    companions = []
    # 2~6위까지만 동반 입상마 참고
    for h in sorted_by_f[1:6]:
        companions.append(
            {
                "마번": int(h["gate"]),
                "마명": h["horse"],
                "final_score": round(h["final_score"], 3),
                "예상1": int(h.get("예상1") or 99),
                "예상2": int(h.get("예상2") or 99),
                "m_rank": int(h.get("m_rank") or 99),
                "트렌드": float(h.get("최근8경주트렌드점수") or 0.0),
                "종반600": float(h.get("종반600") or 0.0),
            }
        )

    return {
        "pace_summary": pace_summary_text,
        "avg_early": avg_early,
        "front_gates": fronts,
        "closer_gates": closers,
        "total_horses": len(horses_all),
        "eval_horses_count": len(horses_eval),
        "key_horse": {
            "마번": int(key_horse["gate"]),
            "마명": key_horse["horse"],
            "final_score": round(key_horse["final_score"], 3),
            "예상1": int(key_horse.get("예상1") or 99),
            "예상2": int(key_horse.get("예상2") or 99),
            "m_rank": int(key_horse.get("m_rank") or 99),
            "트렌드": float(key_horse.get("최근8경주트렌드점수") or 0.0),
            "종반600": float(key_horse.get("종반600") or 0.0),
            "style_score": round(key_horse["style_score"], 2),
            "축_신뢰도": "미정",
        },
        "companions": companions,
        "horses_all": horses_all,
        "horses_eval": horses_eval,
    }


# ==============================
# 6. 상위 N두 선정 (final_score 기준) – 보조용
# ==============================


def select_top_n_by_final_score(horses: List[Dict[str, Any]], n: int = 6) -> List[int]:
    """final_score 기준 상위 N두 gate 리턴."""
    tmp: List[Dict[str, Any]] = []
    for h in horses:
        if "final_score" not in h or h["final_score"] is None:
            h["final_score"] = compute_final_score(h)
        tmp.append(h)

    sorted_by_f = sorted(tmp, key=lambda h: h["final_score"], reverse=True)

    gates: List[int] = []
    for h in sorted_by_f:
        g = int(h.get("gate", 0))
        if g not in gates:
            gates.append(g)
        if len(gates) >= n:
            break
    return sorted(gates)


# ==============================
# 7. 복병 선정 (선행 1, 추입 1, final_score 1 중 최종 1두)
# ==============================


def find_dark_horses_simple(
    horses: List[Dict[str, Any]],
    main_gates: Set[int],
) -> List[Dict[str, Any]]:
    """
    - main_gates(6복조 라인) 밖에서 복병 '최종 1두' 선정
      ▸ 선행 복병 후보 1두(front)
      ▸ 추입 복병 후보 1두(closer)
      ▸ 6복조 라인 밖 말 중 final_score 1위(value)
      ▸ 세 후보 중 score가 가장 좋은 1두만 최종 복병으로 사용
    """
    # 6복조에 포함되지 않은 말들만 후보
    others = [h for h in horses if int(h.get("gate", 0)) not in main_gates]
    if not others:
        return []

    # 편성 기준 평균값 계산 (horses 전체 = 평가대상 말들)
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

    # final_score 평균 준비 (value 타입 후보용)
    for h in horses:
        if "final_score" not in h or h["final_score"] is None:
            h["final_score"] = compute_final_score(h)
    avg_final = sum(h["final_score"] for h in horses) / len(horses)

    # 1) 선행 복병 스코어
    def score_front(h: Dict[str, Any]) -> float:
        s1f = float(h.get("초반200") or 0.0)
        g3f = float(h.get("종반600") or 0.0)
        trend = float(h.get("최근8경주트렌드점수") or 0.0)
        age = float(h.get("마령") or 0.0)
        pop = float(h.get("예상2") or 99.0)
        rec = float(h.get("기록점수") or 0.0)
        starts = float(h.get("출주수") or 0.0)

        score = 0.0

        score += 0.06 * (s1f - avg_s1f)
        score += 0.03 * (g3f - avg_g3f)
        score += 0.04 * (trend - avg_trend)

        if rec < avg_rec - 15:
            score -= 2.0 + (avg_rec - rec) / 20.0

        if age >= 7.0:
            score -= 0.5 * (age - 6.0)

        if trend < 35.0:
            score -= 1.0

        if pop <= 2:
            score -= 0.5

        if starts <= 2:
            score += 1.0
        elif starts <= 3:
            score += 0.5

        return score

    # 2) 추입 복병 스코어
    def score_closer(h: Dict[str, Any]) -> float:
        s1f = float(h.get("초반200") or 0.0)
        g3f = float(h.get("종반600") or 0.0)
        trend = float(h.get("최근8경주트렌드점수") or 0.0)
        age = float(h.get("마령") or 0.0)
        pop = float(h.get("예상2") or 99.0)
        rec = float(h.get("기록점수") or 0.0)
        starts = float(h.get("출주수") or 0.0)

        score = 0.0

        score += 0.07 * (g3f - avg_g3f)
        score += 0.07 * (trend - avg_trend)

        if s1f < 15.0:
            score -= 1.0

        if rec < avg_rec - 10:
            score -= 1.0 + (avg_rec - rec) / 25.0

        if age >= 7.0:
            score -= 2.0 + 0.5 * (age - 7.0)

        if trend < 35.0:
            score -= 1.5

        if pop <= 2:
            score -= 0.5

        if starts <= 2:
            score += 1.0
        elif starts <= 3:
            score += 0.5

        return score

    # 3) 선행/추입 후보 각각 1두씩 선정
    front_candidates = [h for h in others if h.get("초반200") is not None]
    best_front = None
    best_front_score = -999.0

    for h in front_candidates:
        s1f = float(h.get("초반200") or 0.0)
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
        if g3f < max(65.0, avg_g3f + 3.0):
            continue

        s = score_closer(h)
        if s > best_closer_score:
            best_closer = h
            best_closer_score = s

    candidates: List[Dict[str, Any]] = []

    # 선행 복병 후보 추가
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
                "final_score": float(best_front.get("final_score") or 0.0),
                "score": round(best_front_score, 2),
            }
        )

    # 추입 복병 후보 추가
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
                "final_score": float(best_closer.get("final_score") or 0.0),
                "score": round(best_closer_score, 2),
            }
        )

    # 4) 6복조 라인 밖에서 final_score가 가장 높은 말(value 후보) 추가
    others_sorted_by_final = sorted(
        others, key=lambda h: float(h.get("final_score") or 0.0), reverse=True
    )
    if others_sorted_by_final:
        best_val = others_sorted_by_final[0]
        fs_new = float(best_val.get("final_score") or 0.0)
        diff = fs_new - avg_final
        # final_score 기준으로 평균 대비 얼마나 좋은지 → 대략 5로 나눠서 스케일 맞춤
        value_score = diff / 5.0
        if value_score >= 0.0:  # 평균 이상일 때만 value 복병 후보로 인정
            candidates.append(
                {
                    "gate": int(best_val["gate"]),
                    "마명": best_val["horse"],
                    "type": "value",
                    "초반200": float(best_val.get("초반200") or 0.0),
                    "종반600": float(best_val.get("종반600") or 0.0),
                    "트렌드": float(best_val.get("최근8경주트렌드점수") or 0.0),
                    "마령": float(best_val.get("마령") or 0.0),
                    "예상2": float(best_val.get("예상2") or 0.0),
                    "기록점수": float(best_val.get("기록점수") or 0.0),
                    "출주수": float(best_val.get("출주수") or 0.0),
                    "final_score": fs_new,
                    "score": round(value_score, 2),
                }
            )

    if not candidates:
        return []

    # 5) 최종 1두 선택 + 추천 이유 생성
    best_one = max(candidates, key=lambda x: x["score"])

    # 추천 이유 텍스트
    if best_one["type"] == "front":
        reason = (
            "6복조 라인 밖 말 중 선행력이 가장 뛰어나고 "
            "종반·트렌드도 어느 정도 받쳐주는 선행 복병."
        )
    elif best_one["type"] == "closer":
        reason = (
            "6복조 라인 밖 말 중 종반600과 트렌드가 가장 우수한 추입형 복병으로, "
            "막판 한 발이 기대되는 유형."
        )
    else:  # value
        reason = (
            "6복조 라인에는 없지만, 메인 편성 밖 말들 중 final_score(종합 능력)가 "
            "가장 높은 말로, 능력 자체가 숨겨진 복병 자원."
        )

    best_one["reason"] = reason
    return [best_one]


# ==============================
# 8. 삼복승식 베팅 플랜 (강/보통/약한축 로직)
# ==============================


def make_trifecta_plan_with_trust(
    horses_eval: List[Dict[str, Any]],
    anchor_gate: int,
    trust_info: Dict[str, Any],
    dark_horses: List[Dict[str, Any]] | None,
    top6_gates: List[int],
    total_budget: int = 10000,
    unit: int = 100,
) -> Dict[str, Any]:
    """
    삼복승식 베팅안 (총 베팅금은 total_budget 기준, 기본 10000원):

    trust_level 별 조합/비율:

    ▸ 초강축
       - 메인  : 축-상위5두 5복조  (90%)
       - 복병  : 축-복병-상위5두 (10%)

    ▸ 강축
       - 메인  : 축-상위5두 5복조  (80%)
       - 복병  : 축-복병-상위5두 (20%)

    ▸ 보통축
       - 메인  : 상위6두 6복조        (80%)
       - 복병  : 복병-상위6두 6복조형 (20%)

    ▸ 약한축
       - 메인  : 상위6두 6복조        (60%)
       - 복병  : 복병-상위6두        (40%)

    ▸ 위험축
       - 메인  : 상위6두 6복조        (40%)
       - 복병  : 복병-상위6두        (60%)
    """
    trust_level = trust_info.get("trust_level", "보통축")
    trust_score = trust_info.get("trust_score", 0.0)
    anchor_gate = int(anchor_gate)

    # final_score 보정 (혹시 없는 말 있으면 계산)
    for h in horses_eval:
        if "final_score" not in h or h["final_score"] is None:
            h["final_score"] = compute_final_score(h)

    has_dark = bool(dark_horses)
    dark = dark_horses[0] if has_dark else None
    dark_gate = int(dark["gate"]) if dark else None

    # -----------------------------
    # 1) trust_level → 메인/복병 비율
    # -----------------------------
    if not has_dark:
        # 복병이 없으면 무조건 메인 100%
        main_ratio, dark_ratio = 1.0, 0.0
    else:
        if trust_level == "초강축":
            main_ratio, dark_ratio = 0.90, 0.10
        elif trust_level == "강축":
            main_ratio, dark_ratio = 0.80, 0.20
        elif trust_level == "보통축":
            main_ratio, dark_ratio = 0.80, 0.20
        elif trust_level == "약한축":
            main_ratio, dark_ratio = 0.60, 0.40
        else:  # "위험축"
            main_ratio, dark_ratio = 0.40, 0.60

    # 출력용 모드 이름은 trust_level 그대로 사용
    mode = trust_level

    # -----------------------------
    # 2) 조합 스타일 결정
    # -----------------------------
    t6 = sorted(set(top6_gates))
    main_combos: List[Tuple[int, int, int]] = []
    dark_combos: List[Tuple[int, int, int]] = []

    strong_anchor = trust_level in ("초강축", "강축")

    # 메인 조합
    if strong_anchor:
        # 축-상위5두 5복조
        opponents = [g for g in t6 if g != anchor_gate]
        opponents = opponents[:5]
        if len(opponents) >= 2:
            for a, b in combinations(opponents, 2):
                combo = tuple(sorted((anchor_gate, a, b)))
                main_combos.append(combo)
    else:
        # 상위6두 6복조
        if len(t6) >= 3:
            for a, b, c in combinations(t6, 3):
                combo = tuple(sorted((a, b, c)))
                main_combos.append(combo)

    # 복병 조합
    if dark is not None and dark_ratio > 0:
        dg = dark_gate
        if strong_anchor:
            # 축-복병-상위5두
            opponents = [g for g in t6 if g not in (anchor_gate, dg)]
            if opponents:
                for g in opponents:
                    combo = tuple(sorted((anchor_gate, dg, g)))
                    dark_combos.append(combo)
        else:
            # 복병-상위6두 (복병 + 상위6 중 2두)
            pool = [g for g in t6 if g != dg]
            if len(pool) >= 2:
                for a, b in combinations(pool, 2):
                    combo = tuple(sorted((dg, a, b)))
                    dark_combos.append(combo)

    # 중복 제거
    main_combos = sorted(set(main_combos))
    dark_combos = sorted(set(dark_combos))

    # -----------------------------
    # 3) 금액 배분 (총액은 total_budget 고정)
    # -----------------------------
    main_budget = int(total_budget * main_ratio)
    dark_budget = total_budget - main_budget

    main_tickets: List[Dict[str, Any]] = []
    dark_tickets: List[Dict[str, Any]] = []

    # 메인 티켓
    n_main = len(main_combos)
    per_main = main_budget / n_main if n_main > 0 else 0.0
    for combo in main_combos:
        raw = per_main
        stake = int(raw // unit * unit)
        if stake <= 0:
            continue
        main_tickets.append(
            {
                "combo": combo,
                "stake": stake,
                "type": "main",
            }
        )

    # 복병 티켓
    n_dark = len(dark_combos)
    per_dark = dark_budget / n_dark if n_dark > 0 else 0.0
    for combo in dark_combos:
        raw = per_dark
        stake = int(raw // unit * unit)
        if stake <= 0:
            continue
        dark_tickets.append(
            {
                "combo": combo,
                "stake": stake,
                "type": "dark",
            }
        )

    return {
        "mode": mode,
        "anchor_gate": anchor_gate,
        "trust_level": trust_level,
        "trust_score": trust_score,
        "top6_gates": t6,
        "main_tickets": main_tickets,
        "dark_tickets": dark_tickets,
        "dark_horse": dark,
        "total_budget": total_budget,
        "main_ratio": main_ratio,
        "dark_ratio": dark_ratio,
    }


def print_trifecta_plan(
    plan: Dict[str, Any], horses_eval: List[Dict[str, Any]]
) -> None:
    gate2name = {int(h["gate"]): h["horse"] for h in horses_eval}

    print(f"=== 삼복승식 베팅 플랜 (총 {plan['total_budget']}원 기준) ===")
    print(
        f"모드: {plan['mode']} / 축마: {plan['anchor_gate']} / "
        f"축 신뢰도: {plan['trust_level']} ({plan['trust_score']}점)"
    )
    print(
        f"  → 메인 비중: {int(plan['main_ratio']*100)}% / "
        f"복병 라인: {int(plan['dark_ratio']*100)}%\n"
    )

    dark = plan["dark_horse"]
    if dark:
        print(
            f"복병: 마번 {dark['gate']} {dark['마명']} "
            f"({dark['type']}, 종반600={dark['종반600']:.1f}, "
            f"트렌드={dark['트렌드']:.1f}, 출주수={dark['출주수']:.0f}, "
            f"score={dark['score']})"
        )
        reason = dark.get("reason")
        if reason:
            print(f"    추천 이유: {reason}")
    else:
        print("복병: 선정되지 않음")

    print("\n▶ 메인 삼복조 티켓")
    if not plan["main_tickets"]:
        print("  메인 삼복조 없음")
    else:
        for t in plan["main_tickets"]:
            if t["stake"] <= 0:
                continue
            a, b, c = t["combo"]
            names = f"[{gate2name.get(a,'?')}, {gate2name.get(b,'?')}, {gate2name.get(c,'?')}]"
            print(f"  ({a}-{b}-{c})  삼복조 : {t['stake']}원  {names}")

    print("\n▶ 복병 라인 삼복조 티켓")
    if not plan["dark_tickets"]:
        print("  복병 조합 없음")
    else:
        for t in plan["dark_tickets"]:
            if t["stake"] <= 0:
                continue
            a, b, c = t["combo"]
            names = f"[{gate2name.get(a,'?')}, {gate2name.get(b,'?')}, {gate2name.get(c,'?')}]"
            print(f"  ({a}-{b}-{c})  삼복조 : {t['stake']}원  [복병 포함] {names}")


# ==============================
# 9. DB 연결 & 로더
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
# 10. 메인 실행 예시
# ==============================

if __name__ == "__main__":
    # 예: 서울 2025-12-07 6R
    rcity = "부산"
    rdate = "20251213"
    rno = 7

    df = load_race_exp011(rcity, rdate, rno)

    if df.empty:
        print("데이터 없음")
    else:
        rows: List[Tuple[Any, ...]] = list(df.itertuples(index=False, name=None))

        # 1) 경주 분석
        analysis = analyze_race_simple(rows)
        print("=== 경주 전개 요약 ===")
        print(analysis["pace_summary"])
        print()
        print(
            f"총 출전마 수: {analysis['total_horses']}두\n"
            f"평가/베팅 대상(신마 제외): {analysis['eval_horses_count']}두\n"
        )

        key = analysis["key_horse"]
        print("=== 축마 추천 (final_score 기준) ===")
        print(
            f"축마 게이트: {key['마번']}, 마명: {key['마명']}, "
            f"final_score: {key['final_score']}"
        )

        print("\n=== 동반 입상마(참고용, final_score 2~6위) ===")
        for c in analysis["companions"]:
            print(c)

        # 1-1) 출주마 전체 final_score / m_rank / 스타일 점수
        print("\n=== 출주마 전체 final_score / m_rank / 스타일 점수 ===")
        horses_eval = analysis["horses_eval"]
        for h in sorted(horses_eval, key=lambda x: x["final_score"], reverse=True):
            print(
                f"게이트 {int(h['gate'])} / {h['horse']} / "
                f"m_rank={h.get('m_rank')} / "
                f"final={h['final_score']:.2f} / "
                f"style={h['style_score']:.2f}"
            )

        # 2) 축 신뢰도
        anchor_gate = key["마번"]
        anchor = next(h for h in horses_eval if int(h["gate"]) == anchor_gate)

        trust = calc_anchor_trust(anchor, horses_eval)
        analysis["key_horse"]["축_신뢰도"] = trust["trust_level"]

        print("\n=== 축 신뢰도 (상대 비교 + 거리 가중치) ===")
        print(trust)

        # 3) m_rank + final_score 혼합 6복조 라인 결정
        mix_info = determine_race_regime_and_top6(horses_eval, anchor_gate)
        race_regime = mix_info["race_regime"]
        top6_mrank = mix_info["top6_mrank"]
        top6_adjusted = mix_info["top6_adjusted"]

        print("\n=== 편성 상태 / 6복조 라인 ===")
        print(f"편성 상태(race_regime): {race_regime}")
        print(f"m_rank 기준 top6: {top6_mrank}")
        print(f"조정 후(top6, anchor 포함): {top6_adjusted}")

        six_gates_set = set(top6_adjusted)

        # 4) 복병 1두 선정 (6복조 라인 밖에서)
        dark_horses = find_dark_horses_simple(horses_eval, six_gates_set)

        print("\n=== 복병 선정 결과 ===")
        if not dark_horses:
            print("복병 없음")
        else:
            d = dark_horses[0]
            print(
                f"복병 마번: {d['gate']} / 마명: {d['마명']} / 타입: {d['type']} / "
                f"종반600: {d['종반600']} / 트렌드: {d['트렌드']} / 출주수: {d['출주수']} / "
                f"score: {d['score']}"
            )
            if "reason" in d:
                print(f"  ▶ 추천 이유: {d['reason']}")

        # 5) 삼복승식 베팅 플랜 생성
        plan = make_trifecta_plan_with_trust(
            horses_eval=horses_eval,
            anchor_gate=anchor_gate,
            trust_info=trust,
            dark_horses=dark_horses,
            top6_gates=top6_adjusted,
            total_budget=10000,
            unit=100,
        )

        print()
        print_trifecta_plan(plan, horses_eval)
