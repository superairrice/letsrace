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


def summarize_pace(horses: List[Dict[str, Any]]) -> str:
    """초반200 지수 기반 전개 요약 (NaN/None 방어 포함)."""
    vals: List[float] = []
    for h in horses:
        v = h.get("초반200")
        if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
            vals.append(float(v))

    if not vals:
        return "초반 지표 부족으로 전개 판단 불가"

    avg = sum(vals) / len(vals)

    fronts = []
    mids = []
    closers = []
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
    return "\n".join(lines)


def classify_pace_tag(horses: List[Dict[str, Any]]) -> str:
    """
    전체 말의 초반200 평균으로 페이스 태그 분류
    - very_fast / fast / normal / slow / unknown
    """
    vals: List[float] = []
    for h in horses:
        v = h.get("초반200")
        if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
            vals.append(float(v))

    if not vals:
        return "unknown"

    avg = sum(vals) / len(vals)

    if avg >= 80:
        return "very_fast"
    elif avg >= 60:
        return "fast"
    elif avg >= 40:
        return "normal"
    else:
        return "slow"


# ==============================
# 2. final_score / ability / style
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


def compute_style_score(
    h: Dict[str, Any],
    dist_zone: str,
    pace_tag: str,
) -> float:
    """
    거리(zone: short/middle/long) + 페이스(pace_tag)에 따라
    초반/종반 가중치를 다르게 주는 스타일/폼 점수.
    - s1f, g3f, g1f + trend/rec/jt 조합
    """
    s1f = float(h.get("초반200") or 0.0)
    g3f = float(h.get("종반600") or 0.0)
    g1f = float(h.get("종반200") or 0.0)
    trend = float(h.get("최근8경주트렌드점수") or 0.0)
    rec = float(h.get("기록점수") or 0.0)
    jt = float(h.get("기수 조교사 연대점수") or 0.0)

    # 공통(거리/페이스와 무관한) 부분 가중치
    w_trend = 0.15
    w_rec = 0.10
    w_jt = 0.10

    # ---------------------------
    # 거리 + 페이스별 초반/종반 가중치 세팅
    # ---------------------------
    if dist_zone == "short":  # 1200m 이하
        if pace_tag in ("fast", "very_fast"):
            # 빠른 단거리 → 선행전 무너질 수 있으니 종반/폼 비중↑
            w_s1f = 0.15
            w_g3f = 0.30
            w_g1f = 0.20
        else:
            # 느린/보통 단거리 → 선입/초반 비중↑
            w_s1f = 0.25
            w_g3f = 0.25
            w_g1f = 0.15

    elif dist_zone == "middle":  # 1300~1600m
        if pace_tag in ("fast", "very_fast"):
            # 중거리 + 빠른 페이스 → 종반 쪽 조금 더
            w_s1f = 0.18
            w_g3f = 0.32
            w_g1f = 0.20
        else:
            # 중거리 + 보통/느린 → 비교적 밸런스
            w_s1f = 0.20
            w_g3f = 0.30
            w_g1f = 0.15

    else:  # long: 1700m 이상
        if pace_tag in ("fast", "very_fast"):
            # 장거리 + 빠른 페이스 → 초반 비중↓, 막판 비중↑
            w_s1f = 0.10
            w_g3f = 0.37
            w_g1f = 0.18
        else:
            # 장거리 + 느린/보통 → 그래도 종반이 핵심
            w_s1f = 0.15
            w_g3f = 0.33
            w_g1f = 0.17

    style = (
        w_s1f * s1f
        + w_g3f * g3f
        + w_g1f * g1f
        + w_trend * trend
        + w_rec * rec
        + w_jt * jt
    )
    return style


def compute_final_score(h: Dict[str, Any]) -> float:
    """
    final_score:
      - 기본 능력(base)
      - 폼(트렌드 + 종반600 가중)
      - m_rank 가점 (상위일수록 플러스)
    """
    base = compute_base_score(h)
    trend = float(h.get("최근8경주트렌드점수") or 0.0)
    last600 = float(h.get("종반600") or 0.0)
    mr_raw = float(h.get("m_rank") or 99.0)

    # 폼 보정
    form_part = 0.2 * trend + 0.2 * last600

    # m_rank 가점: 1위 가장 큰 가점, 10위 이상은 거의 없음
    if 1 <= mr_raw <= 10:
        mr_bonus = max(0.0, 10.0 - mr_raw)  # 1→9, 2→8, ... 9→1, 10→0
    else:
        mr_bonus = 0.0

    score = base + form_part + mr_bonus
    return score


def ability_score(h: Dict[str, Any]) -> float:
    """
    편성 내 비교용 '능력 점수':
    - compute_base_score(h)에
    - m_rank를 약한 페널티(=좋은 m_rank에 보너스)로 반영.
    """
    base = compute_base_score(h)
    mr = float(h.get("m_rank", 99) or 99)

    # m_rank 1위면 0, 2위 -0.5, 3위 -1.0 ... (좋은 m_rank일수록 유리)
    mr_penalty = 0.5 * (mr - 1)
    return base - mr_penalty


def _norm_m_rank(h: Dict[str, Any]) -> float:
    v = h.get("m_rank")
    if v is None:
        return 99.0
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 99.0
    if x <= 0:
        return 99.0
    return x


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
    (DIST_WEIGHTS 사용)
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
        level = "약한축"

    return {
        "ability_domination": round(a_dom, 1),
        "form_domination": round(f_dom, 1),
        "competition_pressure": round(comp, 1),
        "trust_score": round(trust_score, 1),
        "trust_level": level,
    }


# ==============================
# 4. 경주 분석 (final_score 기준 축/동반마)
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
    pace_summary = summarize_pace(horses_all)

    if not horses_eval:
        raise ValueError("평가 가능한 말이 없습니다. (모두 신마/데이터 부족)")

    # final_score 계산
    for h in horses_eval:
        h["final_score"] = compute_final_score(h)

    sorted_by_f = sorted(horses_eval, key=lambda h: h["final_score"], reverse=True)
    key_horse = sorted_by_f[0]

    companions = []
    # 🔹 동반 입상마: 2위 ~ 6위까지 참고용
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
        "pace_summary": pace_summary,
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
            "축_신뢰도": "미정",
        },
        "companions": companions,
        "horses_all": horses_all,
        "horses_eval": horses_eval,
    }


# ==============================
# 5. 상위 N두 선정 (final_score / 하이브리드)
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


def select_top6_hybrid_by_m_and_style(
    horses_eval: List[Dict[str, Any]],
    anchor_gate: int | None,
    dist_zone: str,
    pace_tag: str,
    pool_extra: int = 2,
    final_n: int = 6,
) -> List[int]:
    """
    m_rank 상위 풀(pool)에서 스타일 점수(거리+페이스 반영)로 다시 뽑는 하이브리드 6복조.
    - 1단계: m_rank 기준 상위 (final_n + pool_extra)두 풀 구성
    - 2단계: compute_style_score로 재정렬 → 상위 final_n두 선택
    - 3단계: anchor_gate가 풀에서 너무 밀려 있으면 조건부 포함
    """
    if not horses_eval:
        return []

    # 1) m_rank 기준 후보 풀
    sorted_by_m = sorted(horses_eval, key=_norm_m_rank)
    pool_size = min(len(sorted_by_m), final_n + pool_extra)
    pool = sorted_by_m[:pool_size]

    # 2) 거리+페이스 반영 스타일 점수 계산
    for h in pool:
        h["style_score"] = compute_style_score(h, dist_zone, pace_tag)

    pool_sorted = sorted(pool, key=lambda h: h["style_score"], reverse=True)
    top = pool_sorted[: min(final_n, len(pool_sorted))]
    top_gates = [int(h["gate"]) for h in top]

    # 3) anchor 강제 포함(조건부)
    if anchor_gate is not None:
        anchor_gate = int(anchor_gate)
        if anchor_gate not in top_gates:
            anchor_obj = next(
                (h for h in horses_eval if int(h.get("gate", 0)) == anchor_gate),
                None,
            )
            if anchor_obj is not None:
                if "style_score" not in anchor_obj:
                    anchor_obj["style_score"] = compute_style_score(
                        anchor_obj, dist_zone, pace_tag
                    )
                worst = min(top, key=lambda h: h["style_score"])
                if anchor_obj["style_score"] > worst["style_score"]:
                    top.remove(worst)
                    top.append(anchor_obj)
                    top_gates = [int(h["gate"]) for h in top]

    return sorted(set(top_gates))


# ==============================
# 6. 복병 선정 (선행 1, 추입 1 중 최종 1두)
# ==============================


def find_dark_horses_simple(
    horses: List[Dict[str, Any]],
    main_gates: Set[int],
) -> List[Dict[str, Any]]:
    """
    - main_gates(상위 6복조 라인) 밖에서 복병 '최종 1두' 선정
      ▸ 선행 복병 후보 1두(front)
      ▸ 추입 복병 후보 1두(closer)
      ▸ 둘 중 score가 더 높은 한 마리만 최종 복병으로 사용
    - 출주수(통산 출주횟수) 3회 이하 말에게 약간의 가산점 부여
    - 신마는 이미 horses에서 제외되어 있다고 가정
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

    # 3) 선행/추입 후보 각각 1두씩 선정
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

    # 4) 두 후보 중 score가 가장 좋은 한 마리만 최종 복병으로 선택
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
# 7. 삼복승식 베팅 플랜 (강/보통/약한축 로직)
# ==============================


def make_trifecta_plan_with_trust(
    horses_eval: List[Dict[str, Any]],
    anchor_gate: int,
    trust_info: Dict[str, Any],
    dark_horses: List[Dict[str, Any]] | None,
    total_budget: int = 10000,
    unit: int = 100,
) -> Dict[str, Any]:
    """
    삼복승식 베팅안:

    ▸ 강축일 때
       - 축마를 기준으로 상위 5마리 → 5복조(축 고정) 80%
       - 강축-복병-상위5마리 → 복병 라인 20%

    ▸ 보통축일 때
       - 상위 6마리 → 6복조(축 고정 아님, 20구멍) 80%
       - 복병축-상위6마리 → 복병 라인 20%

    ▸ 약한축일 때
       - 상위 6마리 → 6복조 60%
       - 복병축-상위6마리 → 40%

    ▸ 복병이 없으면: 메인 비중 100%, 복병 0%
    """
    trust_level = trust_info.get("trust_level", "보통축")
    trust_score = trust_info.get("trust_score", 0.0)
    anchor_gate = int(anchor_gate)

    # final_score 보정
    for h in horses_eval:
        if "final_score" not in h or h["final_score"] is None:
            h["final_score"] = compute_final_score(h)

    # anchor 확인
    sorted_by_f = sorted(horses_eval, key=lambda h: h["final_score"], reverse=True)
    anchor = None
    for h in sorted_by_f:
        if int(h.get("gate", 0)) == anchor_gate:
            anchor = h
            break
    if anchor is None:
        raise ValueError(f"anchor_gate={anchor_gate} 에 해당하는 말이 없습니다.")

    # 거리 / 페이스 → 하이브리드 6복조용
    race_dist = float(horses_eval[0].get("경주거리") or 1200)
    dist_zone = get_distance_zone(race_dist)
    pace_tag = classify_pace_tag(horses_eval)

    # 하이브리드 6복조 상위 6두
    top6_gates = select_top6_hybrid_by_m_and_style(
        horses_eval=horses_eval,
        anchor_gate=anchor_gate,
        dist_zone=dist_zone,
        pace_tag=pace_tag,
        pool_extra=2,
        final_n=6,
    )

    # anchor가 top6에 없으면 anchor 포함(이론상 거의 없겠지만 방어)
    if anchor_gate not in top6_gates:
        if len(top6_gates) >= 6:
            top6_gates[0] = anchor_gate
            top6_gates = sorted(set(top6_gates))
        else:
            top6_gates.append(anchor_gate)
            top6_gates = sorted(set(top6_gates))

    # 상위 5마리 (anchor 제외)
    opponents5: List[int] = [g for g in top6_gates if g != anchor_gate]
    opponents5 = opponents5[:5]  # 안전하게 자르기

    # -----------------
    # 비율 설정
    # -----------------
    if trust_level == "강축":
        base_main_ratio, base_dark_ratio, mode = 0.80, 0.20, "강축"
    elif trust_level == "보통축":
        base_main_ratio, base_dark_ratio, mode = 0.80, 0.20, "보통축"
    else:  # 약한축
        base_main_ratio, base_dark_ratio, mode = 0.60, 0.40, "약한축"

    # 복병
    dark = dark_horses[0] if dark_horses else None
    dark_gate = int(dark["gate"]) if dark else None

    # 🔹 복병이 없으면 100% 메인 비중
    if dark is None:
        main_ratio, dark_ratio = 1.0, 0.0
    else:
        main_ratio, dark_ratio = base_main_ratio, base_dark_ratio

    # -----------------------------
    # 1) 메인 삼복조 티켓
    # -----------------------------
    main_combos: List[Tuple[int, int, int]] = []

    if mode == "강축":
        # 축마 고정 + 상위5마리 → 5복조 (C(5,2)=10)
        if len(opponents5) >= 2:
            for a, b in combinations(opponents5, 2):
                combo = tuple(sorted((anchor_gate, a, b)))
                main_combos.append(combo)
    else:
        # 보통/약한축: 상위6마리 6복조 (C(6,3)=20)
        if len(top6_gates) >= 3:
            for a, b, c in combinations(top6_gates, 3):
                combo = tuple(sorted((a, b, c)))
                main_combos.append(combo)

    # -----------------------------
    # 2) 복병 라인 삼복조 티켓
    # -----------------------------
    dark_combos: List[Tuple[int, int, int]] = []
    if dark is not None and dark_ratio > 0:
        dg = dark_gate

        if mode == "강축":
            # 강축-복병-상위5마리 → (anchor, dg, x) 형태
            pool = [g for g in opponents5 if g != dg]
            for g in pool:
                combo = tuple(sorted((anchor_gate, dg, g)))
                dark_combos.append(combo)
        else:
            # 보통/약한축: 복병축-상위6마리 → (dg, a, b), a,b in top6
            pool = [g for g in top6_gates if g != dg]
            if len(pool) >= 2:
                for a, b in combinations(pool, 2):
                    combo = tuple(sorted((dg, a, b)))
                    dark_combos.append(combo)

    # 중복 제거(혹시 모를 케이스 방어)
    main_combos = sorted(set(main_combos))
    dark_combos = sorted(set(dark_combos))

    # -----------------------------
    # 3) 금액 배분
    # -----------------------------
    main_budget = int(total_budget * main_ratio)
    dark_budget = total_budget - main_budget

    main_tickets: List[Dict[str, Any]] = []
    dark_tickets: List[Dict[str, Any]] = []

    # 메인
    n_main = len(main_combos)
    per_main = main_budget / n_main if n_main > 0 else 0.0
    for combo in main_combos:
        raw = per_main
        stake = int(raw // unit * unit)
        main_tickets.append(
            {
                "combo": combo,
                "stake": stake,
                "type": "main",
            }
        )

    # 복병
    n_dark = len(dark_combos)
    per_dark = dark_budget / n_dark if n_dark > 0 else 0.0
    for combo in dark_combos:
        raw = per_dark
        stake = int(raw // unit * unit)
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
        "top6_gates": top6_gates,
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
# 8. 출주마 final_score 리스트 출력
# ==============================


def print_final_scores(horses_eval: List[Dict[str, Any]]) -> None:
    print("\n=== 출주마 final_score 목록 ===")
    temp = []
    for h in horses_eval:
        if "final_score" not in h or h["final_score"] is None:
            h["final_score"] = compute_final_score(h)
        temp.append(
            {
                "gate": int(h.get("gate", 0)),
                "horse": h["horse"],
                "final_score": h["final_score"],
                "예상1": int(h.get("예상1") or 99),
                "예상2": int(h.get("예상2") or 99),
                "m_rank": int(h.get("m_rank") or 99),
            }
        )

    temp_sorted = sorted(temp, key=lambda x: x["final_score"], reverse=True)
    for t in temp_sorted:
        print(
            f"게이트 {t['gate']:>2} / {t['horse']}  "
            f"final_score={t['final_score']:.2f}  "
            f"(예상1={t['예상1']}, 예상2={t['예상2']}, m_rank={t['m_rank']})"
        )


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
    # 예: 부산 2025-12-05 2R / 필요시 수정
    rcity = "부산"
    rdate = "20251205"
    rno = 4

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

        # 2) 축 신뢰도 (편성 내 상대 비교 + 경주거리별 가중치 반영)
        horses_eval = analysis["horses_eval"]
        anchor_gate = key["마번"]
        anchor = next(h for h in horses_eval if int(h["gate"]) == anchor_gate)

        trust = calc_anchor_trust(anchor, horses_eval)
        analysis["key_horse"]["축_신뢰도"] = trust["trust_level"]

        print("\n=== 축 신뢰도 (상대 비교 + 거리 가중치) ===")
        print(trust)

        # 2-1) 출주마 final_score 전체 출력
        print_final_scores(horses_eval)

        # 3) 거리/페이스 기반 하이브리드 6복조
        race_dist = float(horses_eval[0].get("경주거리") or 1200)
        dist_zone = get_distance_zone(race_dist)
        pace_tag = classify_pace_tag(horses_eval)

        six_gates_list = select_top6_hybrid_by_m_and_style(
            horses_eval=horses_eval,
            anchor_gate=anchor_gate,
            dist_zone=dist_zone,
            pace_tag=pace_tag,
            pool_extra=2,
            final_n=6,
        )
        six_gates = set(six_gates_list)

        print(
            f"\n=== 6복조 기준 추천 마번(게이트, m_rank+스타일 하이브리드 / dist={race_dist}, zone={dist_zone}, pace={pace_tag}) ==="
        )
        print("6복조 마번:", sorted(six_gates))

        # 4) 복병 1두 선정 (6복조 라인 밖에서)
        dark_horses = find_dark_horses_simple(horses_eval, six_gates)

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

        # 5) 삼복승식 베팅 플랜 생성
        plan = make_trifecta_plan_with_trust(
            horses_eval=horses_eval,
            anchor_gate=anchor_gate,
            trust_info=trust,
            dark_horses=dark_horses,
            total_budget=10000,
            unit=100,
        )

        print()
        print_trifecta_plan(plan, horses_eval)
