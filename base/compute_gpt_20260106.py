# compute_gpt.py
"""
exp011 결과를 입력받아
경주마별 종합 점수 / 예상 순위 / 기습선행 시 입상 가능성 / 코멘트
를 계산해 주는 모듈.

▶ 입력: exp011 SELECT 결과(cursor.fetchall() 튜플 리스트)
▶ 출력: 리스트[dict, dict, ...]  (예측 결과)

리턴 포맷 예시:
[
  {
    "rcity": "서울",
    "rdate": "20251123",
    "rno": 11,
    "gate": 4,
    "horse": "만대로",
    "expected_rank": 1,
    "score": 70.56,
    "front_run_place_prob": 70.56,
    "reason": "... 긴 코멘트 ...",
    "one_line_comment": "초반 59.5(양호), 막판 81.8(강점), 스피드 85.9(초강점), 최근 폼 60.0(보통)",
    "early_score": 59.47,
    "late_score": 81.83,       # 종반 600m
    "late200_score": 85.98,    # 종반 200m (i_g1f)
    "speed_score": 85.98,
    "form_score": 60.07,
    "s1f_trend": 16.67,
    "g2f_trend": 0.0,
    "conn_score": 47.26,
  },
  ...
]

※ 특이 규칙
- tot_race == 0  → 신마(데뷔전), 예상순위 99, 점수/코멘트 없음
- recent5 가 빈 문자열("") → 신마(데뷔전급)으로 간주, 위와 동일 처리
"""

from typing import List, Tuple, Any, Dict, Optional
import math
import re


# ---------------------------
# 1. 컬럼 인덱스 정의 (exp011 SELECT 순서 기준)
# ---------------------------

IDX_RCITY = 0
IDX_RDATE = 1
IDX_RNO = 2
IDX_GATE = 3
IDX_HORSE = 4
IDX_BIRTHPLACE = 5
IDX_H_SEX = 6
IDX_H_AGE = 7
IDX_HANDYCAP = 8
IDX_JOC_ADV = 9
IDX_JOCKEY = 10
IDX_TRAINER = 11
IDX_HOST = 12
IDX_RATING = 13
IDX_PRIZE_TOT = 14
IDX_PRIZE_YEAR = 15
IDX_PRIZE_HALF = 16
IDX_TOT_1ST = 17
IDX_TOT_2ND = 18
IDX_TOT_3RD = 19
IDX_TOT_RACE = 20
IDX_YEAR_1ST = 21
IDX_YEAR_2ND = 22
IDX_YEAR_3RD = 23
IDX_YEAR_RACE = 24
IDX_RECENT3 = 25
IDX_RECENT5 = 26
IDX_FAST_R = 27
IDX_SLOW_R = 28
IDX_AVG_R = 29

IDX_RS1F = 30
IDX_R1C = 31
IDX_R2C = 32
IDX_R3C = 33
IDX_R4C = 34
IDX_RG3F = 35
IDX_RG2F = 36
IDX_RG1F = 37

IDX_CS1F = 38
IDX_CG3F = 39
IDX_CG2F = 40
IDX_CG1F = 41
IDX_RANK = 42  # 프로그램 예상 순위(기존 룰 기반)

IDX_I_S1F = 43  # cs1f를 초로 환산한 지표 (스타트/초반 200m)
IDX_I_G3F = 44  # cg3f를 초로 환산한 지표 (종반 600m)
IDX_I_G2F = 45
IDX_I_G1F = 46  # 종반 200m

IDX_I_JOCKEY = 47
IDX_I_CYCLE = 48
IDX_I_PREHANDY = 49

IDX_REMARK = 50  # 기존: 최근 7경주 순위 문자열 (이제 폼 계산에는 사용 안 함)
IDX_S1F_RANK = 51
IDX_G2F_RANK = 52  # 최근 8경주 상세 문자열 (등급, 순위, 연식, 강도 포함)

IDX_H_WEIGHT = 53
IDX_J_PER = 54
IDX_T_PER = 55
IDX_JT_PER = 56
IDX_JT_CNT = 57
IDX_JT_1ST = 58
IDX_JT_2ND = 59
IDX_JT_3RD = 60
IDX_DISTANCE = 61


# ---------------------------
# 2. 유틸 함수들
# ---------------------------


def safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if s == "" or s.upper() == "NULL":
            return default
        return float(s)
    except Exception:
        return default


def to_optional_float(val: Any) -> Optional[float]:
    """빈 문자열/NULL이면 None, 그 외에는 float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s == "" or s.upper() == "NULL":
        return None
    try:
        return float(s)
    except Exception:
        return None


def normalize_inverse(value: Optional[float], v_min: float, v_max: float) -> float:
    """
    기록(시간)처럼 '작을수록 좋은 값'을 0~100 점수로 변환.
    v_min ~ v_max 범위 안에서 선형 스케일링.
    """
    if value is None:
        return 50.0
    v = float(value)
    if v_max <= v_min:
        return 50.0
    ratio = (v - v_min) / (v_max - v_min)
    score = (1.0 - ratio) * 100.0
    return max(0.0, min(100.0, score))


def normalize_direct(value: Optional[float], v_min: float, v_max: float) -> float:
    """
    퍼센트, 지수 등 '클수록 좋은 값'을 0~100 점수로 변환.
    """
    if value is None:
        return 50.0
    v = float(value)
    if v_max <= v_min:
        return 50.0
    ratio = (v - v_min) / (v_max - v_min)
    score = ratio * 100.0
    return max(0.0, min(100.0, score))


def label_from_score(score: float) -> str:
    """
    7단계 등급 라벨링
      90~100 : 초강점
      75~89  : 강점
      60~74  : 양호
      50~59  : 보통
      35~49  : 약간 약함
      20~34  : 약함
      0~19   : 취약
    """
    s = float(score)
    if s >= 90:
        return "초강점"
    if s >= 75:
        return "강점"
    if s >= 60:
        return "양호"
    if s >= 50:
        return "보통"
    if s >= 35:
        return "약간 약함"
    if s >= 20:
        return "약함"
    return "취약"


def fmt_score_with_label(score: float) -> str:
    """예: 60.2(양호)"""
    return f"{score:.1f}({label_from_score(score)})"


# ---------------------------
# 3. 시계열 트렌드 계산 유틸
# ---------------------------


def compute_series_trend(
    values: List[float],
    better_when_lower: bool,
    max_delta: float,
) -> float:
    """
    최근(맨 앞) ~ 과거(맨 뒤) 값의 변화를 0~100 스케일로 환산.

    - better_when_lower=True  → 값이 감소할수록(작아질수록) 개선으로 봄 (등급, 순위, 연식)
    - better_when_lower=False → 값이 증가할수록 개선으로 봄 (편성강도 등)
    - max_delta: '이 정도 변화면 풀스코어(±100)'라고 보는 기준 폭
    """
    vals = [safe_float(v, None) for v in values if to_optional_float(v) is not None]
    if len(vals) < 2:
        return 50.0

    # g2f_rank는 '앞이 최근'이라고 가정
    recent = float(vals[0])
    old = float(vals[-1])

    if better_when_lower:
        raw_delta = old - recent  # 과거 - 최근 (최근이 더 작으면 +)
    else:
        raw_delta = recent - old  # 최근 - 과거 (최근이 더 크면 +)

    if max_delta <= 0:
        return 50.0

    norm = raw_delta / max_delta
    norm = max(-1.0, min(1.0, norm))  # -1 ~ +1 클램프

    score = 50.0 + 50.0 * norm  # -1 → 0점, 0 → 50점, +1 → 100점
    return max(0.0, min(100.0, score))


# ---------------------------
# 4. g2f_rank 기반 폼(트렌드) 점수
#     - 기록(S1F/G3F/환산기록)은 완전히 배제
#     - 등급/순위/연식/편성강도만 사용
# ---------------------------


def compute_trend_from_g2f_only_meta(g2f_raw: str) -> float:
    """
    g2f_rank 문자열을 파싱해서 '폼 트렌드' 점수(0~100)를 계산.

    사용 항목:
      - 등급 (G4, G5, G6 ... → 숫자 작을수록 높은 등급)
      - 순위 (1등이 가장 좋은 값)
      - 연식 (연승식 배당률, 작을수록 인기마)
      - 강도 (편성강도, 숫자 클수록 강편성)

    기록(시간, S1F, G3F, 환산기록)은 전부 무시.
    """
    if not g2f_raw:
        return 50.0

    lines = [ln.strip() for ln in str(g2f_raw).splitlines() if ln.strip()]
    recs = []

    # 각 라인 파싱
    for ln in lines:
        # 헤더 라인 같은 것은 스킵
        if "경주" in ln:
            continue

        # 예: 25.10.19 ... G4 ... 13.4 ... 38.7 ... 1:27.5 ... 순위: 1 ... 5.3 ... -7
        m = re.search(
            r"(?P<date>\d{2}\.\d{2}\.\d{2}).*?"
            r"G(?P<grade>\d+).*?"
            r"순위[: ]*(?P<rank>\d+).*?"
            r"(?P<yunsik>\d+\.\d+).*?"
            r"(?P<strength>-?\d+)\s*$",
            ln,
        )
        if not m:
            continue

        recs.append(
            {
                "date": m.group("date"),
                "grade": int(m.group("grade")),
                "rank": int(m.group("rank")),
                "yunsik": float(m.group("yunsik")),
                "strength": int(m.group("strength")),
            }
        )

    if len(recs) < 2:
        return 50.0

    # g2f_rank는 "앞이 최근"이라고 가정한 리스트
    grade_list = [r["grade"] for r in recs]
    rank_list = [r["rank"] for r in recs]
    yunsik_list = [r["yunsik"] for r in recs]
    strength_list = [r["strength"] for r in recs]

    # ① 등급 트렌드: 등급 숫자 ↓ → 상향 편성 출전 → 상승
    grade_trend = compute_series_trend(
        values=grade_list,
        better_when_lower=True,
        max_delta=2.0,
    )

    # ② 순위 트렌드: 순위 ↓ → 성적 개선 → 상승
    rank_trend = compute_series_trend(
        values=rank_list,
        better_when_lower=True,
        max_delta=5.0,
    )

    # ③ 연식(연승식 배당률) 트렌드: 연식 ↓ → 인기 상승 → 상승
    yunsik_trend = compute_series_trend(
        values=yunsik_list,
        better_when_lower=True,
        max_delta=4.0,
    )

    # ④ 편성강도 트렌드: 강도 ↑ (편성 강해짐) → 동일 성적이면 기량 상승 신호
    strength_trend = compute_series_trend(
        values=strength_list,
        better_when_lower=False,
        max_delta=10.0,
    )

    # 가중합 (필요시 조정 가능)
    w_grade = 0.30
    w_rank = 0.35
    w_yunsik = 0.20
    w_strength = 0.15

    combined = (
        grade_trend * w_grade
        + rank_trend * w_rank
        + yunsik_trend * w_yunsik
        + strength_trend * w_strength
    )

    return max(0.0, min(100.0, combined))


# ---------------------------
# 5. 세부 점수 계산 함수들
# ---------------------------


def compute_early_scores(rows: List[Tuple[Any, ...]]) -> Dict[int, float]:
    """
    초반 선행력 점수 계산 (게이트별).
    i_s1f(시간) 기준으로 작을수록 좋은 값.
    """
    values = []
    for row in rows:
        v = to_optional_float(row[IDX_I_S1F])
        if v is not None:
            values.append(v)
    if not values:
        return {int(row[IDX_GATE]): 50.0 for row in rows}

    v_min, v_max = min(values), max(values)
    result = {}
    for row in rows:
        gate = int(row[IDX_GATE])
        v = to_optional_float(row[IDX_I_S1F])
        score = normalize_inverse(v, v_min, v_max) if v is not None else 50.0
        result[gate] = score
    return result


def compute_late_scores(rows: List[Tuple[Any, ...]]) -> Dict[int, float]:
    """
    막판 탄력(종반 600m) 점수 계산 (게이트별).
    i_g3f(시간) 기준으로 작을수록 좋은 값.
    """
    values = []
    for row in rows:
        v = to_optional_float(row[IDX_I_G3F])
        if v is not None:
            values.append(v)
    if not values:
        return {int(row[IDX_GATE]): 50.0 for row in rows}

    v_min, v_max = min(values), max(values)
    result = {}
    for row in rows:
        gate = int(row[IDX_GATE])
        v = to_optional_float(row[IDX_I_G3F])
        score = normalize_inverse(v, v_min, v_max) if v is not None else 50.0
        result[gate] = score
    return result


def compute_late200_scores(rows: List[Tuple[Any, ...]]) -> Dict[int, float]:
    """
    종반 200m(i_g1f) 점수 계산 (게이트별).
    작을수록 좋은 기록 → inverse 스케일.
    """
    values = []
    for row in rows:
        v = to_optional_float(row[IDX_I_G1F])
        if v is not None:
            values.append(v)
    if not values:
        return {int(row[IDX_GATE]): 50.0 for row in rows}

    v_min, v_max = min(values), max(values)
    result = {}
    for row in rows:
        gate = int(row[IDX_GATE])
        v = to_optional_float(row[IDX_I_G1F])
        score = normalize_inverse(v, v_min, v_max) if v is not None else 50.0
        result[gate] = score
    return result


def compute_speed_scores(rows: List[Tuple[Any, ...]]) -> Dict[int, float]:
    """
    최근 거리적응/기록 기반 스피드 점수 (A안 유지, 스케일링 개선 버전).

    - recent3: 출주거리 기준 최근 3경주 기록(초/또는 ms 환산)
    - recent5: 최근 6경주를 출주거리로 환산한 기록
    - fast_r : 출주거리 기준 최고 좋은 기록
    - slow_r : 출주거리 기준 최저 기록
    - avg_r  : 출주거리 기준 평균 기록

    ✅ 변경점 1: 원시 ms/초 단위 그대로 사용하되,
                레이스 내 전체 기록의 min/max로 0~100 스케일링 (동적 스케일)
    ✅ 변경점 2: 해당 거리 전적이 없으면 recent5로 치환해서 사용
                (각 말의 recent3/avg_r/fast_r/slow_r가 0 또는 None이면 recent5를 대신 사용)
    """

    # ---------------------------
    # 1) 보조 함수: 주 기록이 없으면 recent5로 대체
    # ---------------------------
    def pick_time(main_val: Any, fallback_recent5: Any) -> Optional[float]:
        """
        main_val(예: recent3, avg_r, fast_r, slow_r)이 없으면
        fallback_recent5(해당 말의 recent5)를 대신 사용.
        둘 다 없으면 None.
        """
        m = to_optional_float(main_val)
        if m is not None and m > 0:
            return m

        fb = to_optional_float(fallback_recent5)
        if fb is not None and fb > 0:
            return fb

        return None

    # ---------------------------
    # 2) 레이스 전체에서 사용할 min/max 기록 구하기
    #    (단위가 초든 ms든 상관없이, 분포 기준으로만 스케일링)
    # ---------------------------
    all_times: List[float] = []

    for row in rows:
        recent5_raw = row[IDX_RECENT5]

        t_recent3 = pick_time(row[IDX_RECENT3], recent5_raw)
        t_recent5 = to_optional_float(recent5_raw)
        t_avg_r = pick_time(row[IDX_AVG_R], recent5_raw)
        t_fast_r = pick_time(row[IDX_FAST_R], recent5_raw)
        t_slow_r = pick_time(row[IDX_SLOW_R], recent5_raw)

        for t in [t_recent3, t_recent5, t_avg_r, t_fast_r, t_slow_r]:
            if t is not None and t > 0:
                all_times.append(t)

    # 기록이 하나도 없으면 전원 50점(중립) 처리
    if not all_times:
        return {int(row[IDX_GATE]): 50.0 for row in rows}

    base_min = min(all_times)
    base_max = max(all_times)

    # min == max 이면 전부 같은 기록 → 모두 50점
    if base_max <= base_min:
        return {int(row[IDX_GATE]): 50.0 for row in rows}

    # ---------------------------
    # 3) 동적 스케일링을 사용하는 norm_time
    # ---------------------------
    def norm_time_direct(sec: Optional[float]) -> float:
        if sec is None or sec <= 0:
            return 50.0
        # 작을수록 좋은 값 → inverse 스케일 (0~100)
        return normalize_inverse(sec, base_min, base_max)

    # ---------------------------
    # 4) 가중치 (A안 유지)
    # ---------------------------
    W_RECENT3 = 0.20
    W_RECENT5 = 0.50
    W_AVG_R = 0.10
    W_FAST_R = 0.08
    W_SLOW_R = 0.02
    CORRECTION = 0.10  # 보정계수 (원래 그대로 유지)

    result: Dict[int, float] = {}

    for row in rows:
        gate = int(row[IDX_GATE])
        recent5_raw = row[IDX_RECENT5]

        # 거리 전적 없으면 recent5로 치환
        recent3_sec = pick_time(row[IDX_RECENT3], recent5_raw)
        recent5_sec = to_optional_float(recent5_raw)
        avg_sec = pick_time(row[IDX_AVG_R], recent5_raw)
        fast_sec = pick_time(row[IDX_FAST_R], recent5_raw)
        slow_sec = pick_time(row[IDX_SLOW_R], recent5_raw)

        recent3_s = norm_time_direct(recent3_sec)
        recent5_s = norm_time_direct(recent5_sec)
        avg_s = norm_time_direct(avg_sec)
        fast_s = norm_time_direct(fast_sec)
        slow_s = norm_time_direct(slow_sec)

        base = (
            W_RECENT3 * recent3_s
            + W_RECENT5 * recent5_s
            + W_AVG_R * avg_s
            + W_FAST_R * fast_s
            + W_SLOW_R * slow_s
        )

        score = base * (1.0 + CORRECTION)
        score = max(0.0, min(100.0, score))
        result[gate] = score

    return result


def compute_form_scores(rows: List[Tuple[Any, ...]]) -> Dict[int, float]:
    """
    '폼 점수'는 remark(최근7경주 순위 문자열)를 쓰지 않고,
    ▶ g2f_rank(최근 8경주 상세정보 문자열)를 파싱해 만든 trend_score 를 사용.
      - 등급, 순위, 연식, 편성강도 기반 0~100 스케일.
    """
    result: Dict[int, float] = {}
    for row in rows:
        gate = int(row[IDX_GATE])
        g2f_raw = row[IDX_G2F_RANK]
        score = compute_trend_from_g2f_only_meta(g2f_raw if g2f_raw is not None else "")
        result[gate] = score
    return result


def compute_trend_scores(
    rows: List[Tuple[Any, ...]],
    early_scores: Dict[int, float],
    late_scores: Dict[int, float],
) -> Dict[int, Dict[str, float]]:
    """
    s1f_trend / g2f_trend 를 '트렌드 보조지표'로 0~100 스케일로 계산.
    여기서는 단순히:
    - s1f_trend: early_score 기준 필드 내 백분위
    - g2f_trend: late_score  기준 필드 내 백분위
    """
    gates = [int(row[IDX_GATE]) for row in rows]
    if not gates:
        return {}

    early_vals = [early_scores[g] for g in gates]
    late_vals = [late_scores[g] for g in gates]

    e_min, e_max = min(early_vals), max(early_vals)
    l_min, l_max = min(late_vals), max(late_vals)

    trends = {}
    for g in gates:
        e = early_scores[g]
        l = late_scores[g]
        s1f_trend = normalize_direct(e, e_min, e_max) if e_max > e_min else 50.0
        g2f_trend = normalize_direct(l, l_min, l_max) if l_max > l_min else 50.0
        trends[g] = {
            "s1f_trend": round(s1f_trend, 2),
            "g2f_trend": round(g2f_trend, 2),
        }
    return trends


# def compute_connection_scores(rows: List[Tuple[Any, ...]]) -> Dict[int, float]:
#     """
#     기수/조교사/복승 조합 점수.
#     - j_per, t_per, jt_per 를 기본 사용 (퍼센트라고 가정)
#     - 없으면 jt_cnt, jt_1st, jt_2nd, jt_3rd로 대략 추정
#     """
#     result = {}
#     for row in rows:
#         gate = int(row[IDX_GATE])

#         j_per = to_optional_float(row[IDX_J_PER])
#         t_per = to_optional_float(row[IDX_T_PER])
#         jt_per = to_optional_float(row[IDX_JT_PER])

#         if j_per is None and t_per is None and jt_per is None:
#             # 복승률 직접 계산 시도
#             jt_cnt = safe_float(row[IDX_JT_CNT], 0.0)
#             jt_1 = safe_float(row[IDX_JT_1ST], 0.0)
#             jt_2 = safe_float(row[IDX_JT_2ND], 0.0)
#             jt_3 = safe_float(row[IDX_JT_3RD], 0.0)
#             if jt_cnt > 0:
#                 jt_in = (jt_1 + jt_2 + jt_3) / jt_cnt * 100.0
#                 base = jt_in
#             else:
#                 base = 50.0
#         else:
#             vals = []
#             for v in [j_per, t_per, jt_per]:
#                 if v is not None and v > 0:
#                     vals.append(float(v))
#             base = sum(vals) / len(vals) if vals else 50.0

#         base = max(0.0, min(100.0, base))
#         result[gate] = base

#     return result


def _to_percent(x) -> float:
    """0~1 스케일이 들어온 경우 0~100으로 자동 변환."""
    if x is None:
        return None
    v = float(x)
    if 0.0 <= v <= 1.0:
        return v * 100.0
    return v  # 이미 퍼센트라고 보고 그대로 사용


def to_percent(v):
    if v is None:
        return None
    v = float(v)
    if 0 <= v <= 1:
        return v * 100.0
    return v


def shrink(value, cnt, scale=20.0):
    """
    샘플 수가 적으면 50에 가깝게 수축.
    cnt=0 → 무조건 50
    cnt=20 이상 → 거의 value 그대로
    """
    if value is None:
        return None

    strength = min(cnt / scale, 1.0)  # 0~1
    return 50.0 + strength * (value - 50.0)  # 50 쪽으로 당김


from typing import Any, Dict, List, Tuple


def compute_connection_scores(rows: List[Tuple[Any, ...]]) -> Dict[int, float]:
    """
    기수/조교사/복승 조합 점수.
    - j_per, t_per, jt_per 를 기본 사용 (퍼센트라고 가정, 0~1 또는 0~100 둘 다 허용 가능)
    - 없으면 jt_cnt, jt_1st, jt_2nd, jt_3rd로 대략 추정
    - 이후 경주 내에서 min-max 스케일링으로 0~100 변환 (변별력/100점 확보)
    """
    raw_base: Dict[int, float] = {}

    for row in rows:
        gate = int(row[IDX_GATE])

        j_per = to_optional_float(row[IDX_J_PER])
        t_per = to_optional_float(row[IDX_T_PER])
        jt_per = to_optional_float(row[IDX_JT_PER])

        # 0~1 비율이면 0~100으로 변환
        def to_percent(v):
            if v is None:
                return None
            v = float(v)
            if 0.0 <= v <= 1.0:
                return v * 100.0
            return v

        j_per = to_percent(j_per)
        t_per = to_percent(t_per)
        jt_per = to_percent(jt_per)

        if j_per is None and t_per is None and jt_per is None:
            # 복승률 직접 계산 시도
            jt_cnt = safe_float(row[IDX_JT_CNT], 0.0)
            jt_1 = safe_float(row[IDX_JT_1ST], 0.0)
            jt_2 = safe_float(row[IDX_JT_2ND], 0.0)
            jt_3 = safe_float(row[IDX_JT_3RD], 0.0)
            if jt_cnt > 0:
                jt_in = (jt_1 + jt_2 + jt_3) / jt_cnt * 100.0
                base = jt_in
            else:
                base = 10.0  # 정보 없으면 살짝 낮게
        else:
            vals = []
            weights = []

            if j_per is not None and j_per > 0:
                vals.append(j_per)
                weights.append(0.25)
            if t_per is not None and t_per > 0:
                vals.append(t_per)
                weights.append(0.25)
            if jt_per is not None and jt_per > 0:
                vals.append(jt_per)
                weights.append(0.5)

            if vals:
                wsum = sum(weights)
                base = sum(v * w for v, w in zip(vals, weights)) / wsum
            else:
                base = 10.0  # 혹시라도 전부 0이하/None이면

        base = max(0.0, min(100.0, base))
        raw_base[gate] = base

    # === 여기까지는 "절대 연결 점수" ===
    if not raw_base:
        return {}

    # === 경주 내에서 0~100으로 펴주기 (min-max 스케일링) ===
    bases = list(raw_base.values())
    min_b = min(bases)
    max_b = max(bases)

    result: Dict[int, float] = {}

    if max_b == min_b:
        # 전부 같은 값이면 50으로 통일
        for gate in raw_base:
            result[gate] = 50.0
        return result

    for gate, base in raw_base.items():
        # (base - min) / (max - min) → 0~1
        norm = (base - min_b) / (max_b - min_b)
        score = norm * 100.0
        result[gate] = score

    return result


def compute_front_run_prob(
    rows: List[Tuple[Any, ...]],
    early_scores: Dict[int, float],
    total_scores: Dict[int, float],
) -> Dict[int, float]:
    """
    기습 선행 성공 시 3위 이내 가능성 (0~100 스케일 대략 값).
    - 초반 선행력 우수할수록 ↑
    - 종합점수 높을수록 ↑
    """
    gates = [int(row[IDX_GATE]) for row in rows]
    gates = [g for g in gates if g in total_scores]  # 신마 제외
    if not gates:
        return {}

    early_vals = [early_scores[g] for g in gates]
    total_vals = [total_scores[g] for g in gates]

    e_min, e_max = min(early_vals), max(early_vals)
    t_min, t_max = min(total_vals), max(total_vals)

    probs = {}
    for g in gates:
        e = early_scores[g]
        t = total_scores[g]

        early_pct = normalize_direct(e, e_min, e_max) if e_max > e_min else 50.0
        total_pct = normalize_direct(t, t_min, t_max) if t_max > t_min else 50.0

        prob = 0.6 * early_pct + 0.4 * total_pct
        prob = max(0.0, min(100.0, prob))
        probs[g] = round(prob, 2)

    return probs


# ---------------------------
# 6. 신마(데뷔전/데뷔전급) 판별
# ---------------------------


def classify_new_horse(row: Tuple[Any, ...]) -> Optional[str]:
    """
    신마 여부 및 타입 판별.
    - tot_race == 0          → 'debut' (완전 신마)
    - recent5 가 '' 또는 NULL → 'debut_like' (데뷔전급: 데이터 부족)
    - 그 외                  → None (보통 말)
    """
    tot_race = safe_float(row[IDX_TOT_RACE], 0.0)
    if tot_race <= 0:
        return "debut"

    recent5_raw = row[IDX_RECENT5]
    if recent5_raw == 0 or recent5_raw is None or str(recent5_raw).strip() == "":
        return "debut_like"

    return None


# ---------------------------
# 7. 코멘트 생성
# ---------------------------


def build_reason(
    gate: int,
    horse: str,
    expected_rank: int,
    early_score: float,
    late_score: float,
    late200_score: float,
    speed_score: float,
    form_score: float,
    conn_score: float,
    front_prob: float,
) -> str:
    early_str = fmt_score_with_label(early_score)
    late_str = fmt_score_with_label(late_score)  # 600m
    late200_str = fmt_score_with_label(late200_score)  # 200m
    speed_str = fmt_score_with_label(speed_score)
    form_str = fmt_score_with_label(form_score)
    conn_str = fmt_score_with_label(conn_score)

    reason = (
        f"[{gate}번 {horse}]\n"
        f"- 최근 8경주 기준(r_pop): {expected_rank}위권\n"
        f"- 초반 선행력: {early_str}\n"
        f"- 막판 탄력(600m): {late_str}\n"
        f"- 종반 200m: {late200_str}\n"
        f"- 거리 적응 및 최근 기록(recent3/recent5/avg_r 등): {speed_str}\n"
        f"- 최근 8경주 트렌드(g2f_rank 기반 등급/순위/연식/편성강도): {form_str}\n"
        f"- 기수·조교사·복승 조합: {conn_str}\n"
        f"- 기습 선행 성공 시 3위 이내 입상 가능성(모델 추정): 약 {front_prob:.1f}점(0~100 스케일)"
    )
    return reason


def build_one_line_comment(
    early_score: float,
    late_score: float,
    speed_score: float,
    form_score: float,
) -> str:
    return (
        f"초반 {fmt_score_with_label(early_score)}, "
        f"막판 {fmt_score_with_label(late_score)}, "
        f"스피드 {fmt_score_with_label(speed_score)}, "
        f"트렌드 {fmt_score_with_label(form_score)}"
    )


# ---------------------------
# 8. 메인 함수: process_race
# ---------------------------


def process_race(exp011_rows: List[Tuple[Any, ...]]) -> List[Dict[str, Any]]:
    """
    Django view에서
    from compute_gpt import process_race
    로 불러서 사용.

    exp011_rows: cursor.fetchall() 결과
    """
    if not exp011_rows:
        return []

    # print(f"Processing {(exp011_rows.)} horses...")
    # 신마/데뷔전급 분류
    new_type_by_gate: Dict[int, Optional[str]] = {}
    normal_rows: List[Tuple[Any, ...]] = []
    for row in exp011_rows:
        gate = int(row[IDX_GATE])
        new_type = classify_new_horse(row)
        new_type_by_gate[gate] = new_type
        if new_type is None:
            normal_rows.append(row)

    # 모두 신마인 경우 → 전부 99번으로만 리턴
    if not normal_rows:
        final_results: List[Dict[str, Any]] = []
        for row in exp011_rows:
            gate = int(row[IDX_GATE])
            horse = row[IDX_HORSE]
            new_type = new_type_by_gate[gate]
            if new_type == "debut":
                reason = f"[{gate}번 {horse}] 신마(데뷔전) — 데이터 부족으로 평가 제외"
            else:
                reason = (
                    f"[{gate}번 {horse}] 신마(데뷔전급) — 데이터 부족으로 평가 제외"
                )
            final_results.append(
                {
                    "rcity": row[IDX_RCITY],
                    "rdate": row[IDX_RDATE],
                    "rno": int(row[IDX_RNO]),
                    "gate": gate,
                    "horse": horse,
                    "expected_rank": 99,
                    "score": None,
                    "front_run_place_prob": 0.0,
                    "reason": reason,
                    "one_line_comment": None,
                    "early_score": None,
                    "late_score": None,
                    "late200_score": None,
                    "speed_score": None,
                    "form_score": None,
                    "s1f_trend": None,
                    "g2f_trend": None,
                    "conn_score": None,
                }
            )
        return final_results

    # 서브 점수 계산 (신마 제외한 normal_rows 기준)
    early_scores = compute_early_scores(normal_rows)
    late_scores = compute_late_scores(normal_rows)
    late200_scores = compute_late200_scores(normal_rows)
    speed_scores = compute_speed_scores(normal_rows)
    form_scores = compute_form_scores(normal_rows)  # ⬅ g2f_rank 기반 트렌드
    trend_scores = compute_trend_scores(normal_rows, early_scores, late_scores)
    conn_scores = compute_connection_scores(normal_rows)

    # 종합 점수 가중치
    # W_EARLY = 0.25
    # W_LATE = 0.25  # 600m
    # W_SPEED = 0.25
    # W_FORM = 0.20  # ← 여기 FORM 이 g2f_rank 기반 trend_score
    # W_CONN = 0.05
    # W_EARLY = 0.2
    # W_LATE = 0.2  # 600m
    # W_SPEED = 0.2
    # W_FORM = 0.2  # ← 여기 FORM 이 g2f_rank 기반 trend_score
    # W_CONN = 0.2

    # if exp011_rows[0][IDX_DISTANCE] <= 1200:
    #     W_EARLY = 0.40
    #     W_LATE = 0.20
    #     W_SPEED = 0.25
    #     W_FORM = 0.10
    #     W_CONN = 0.05

    # elif 1300 <= exp011_rows[0][IDX_DISTANCE] <= 1600:
    #     W_EARLY = 0.30
    #     W_LATE = 0.30
    #     W_SPEED = 0.20
    #     W_FORM = 0.15
    #     W_CONN = 0.05

    # elif exp011_rows[0][IDX_DISTANCE] >= 1700:
    #     W_EARLY = 0.20
    #     W_LATE = 0.40
    #     W_SPEED = 0.15
    #     W_FORM = 0.20
    #     W_CONN = 0.05

    distance = to_optional_float(exp011_rows[0][IDX_DISTANCE])
    if distance is None:
        distance = 1400.0  # fallback to mid-distance weights if data missing

    if distance <= 1200:
        W_EARLY = 0.30
        W_LATE = 0.10
        W_SPEED = 0.30
        W_FORM = 0.10
        W_CONN = 0.20

    elif 1300 <= distance <= 1700:
        W_EARLY = 0.20
        W_LATE = 0.20
        W_SPEED = 0.20
        W_FORM = 0.20
        W_CONN = 0.20

    elif distance >= 1800:
        W_EARLY = 0.10
        W_LATE = 0.30
        W_SPEED = 0.30
        W_FORM = 0.10
        W_CONN = 0.20

    # if distance <= 1200:
    #     return dict(W_EARLY=0.40, W_LATE=0.20, W_SPEED=0.25, W_FORM=0.10, W_CONN=0.05)

    # elif 1300 <= distance <= 1600:
    #     return dict(W_EARLY=0.30, W_LATE=0.30, W_SPEED=0.20, W_FORM=0.15, W_CONN=0.05)

    # else:  # distance >= 1700
    #     return dict(W_EARLY=0.20, W_LATE=0.40, W_SPEED=0.15, W_FORM=0.20, W_CONN=0.05)

    total_scores: Dict[int, float] = {}

    # 1차: 각 말별 total score 산출 (신마 제외)
    tmp_results = []
    for row in normal_rows:
        rcity = row[IDX_RCITY]
        rdate = row[IDX_RDATE]
        rno = int(row[IDX_RNO])
        gate = int(row[IDX_GATE])
        horse = row[IDX_HORSE]

        early = early_scores[gate]
        late = late_scores[gate]
        late200 = late200_scores[gate]
        speed = speed_scores[gate]
        form = form_scores[gate]
        conn = conn_scores[gate]

        total = (
            W_EARLY * early
            + W_LATE * late
            + W_SPEED * speed
            + W_FORM * form
            + W_CONN * conn
        )

        total = max(0.0, min(100.0, total))
        total_scores[gate] = total

        s1f_trend = trend_scores[gate]["s1f_trend"]
        g2f_trend = trend_scores[gate]["g2f_trend"]

        tmp_results.append(
            {
                "rcity": rcity,
                "rdate": rdate,
                "rno": rno,
                "gate": gate,
                "horse": horse,
                "score": total,
                "early_score": early,
                "late_score": late,
                "late200_score": late200,
                "speed_score": speed,
                "form_score": form,
                "s1f_trend": s1f_trend,
                "g2f_trend": g2f_trend,
                "conn_score": conn,
            }
        )

    # 기습 선행 시 3위 이내 가능성 계산 (신마 제외)
    front_probs = compute_front_run_prob(normal_rows, early_scores, total_scores)

    # 최종 정렬: score 내림차순 → expected_rank 부여
    tmp_results.sort(key=lambda x: x["score"], reverse=True)

    final_results: List[Dict[str, Any]] = []

    # 1) 점수 있는 말들 먼저 (rank 1,2,...)
    for idx, item in enumerate(tmp_results, start=1):
        gate = item["gate"]
        horse = item["horse"]

        score = round(item["score"], 2)
        early = round(item["early_score"], 2)
        late = round(item["late_score"], 2)
        late200 = round(item["late200_score"], 2)
        speed = round(item["speed_score"], 2)
        form = round(item["form_score"], 2)
        conn = round(item["conn_score"], 2)
        s1f_trend = round(item["s1f_trend"], 2)
        g2f_trend = round(item["g2f_trend"], 2)

        front_prob = front_probs.get(gate, 50.0)

        reason = build_reason(
            gate=gate,
            horse=horse,
            expected_rank=idx,
            early_score=early,
            late_score=late,
            late200_score=late200,
            speed_score=speed,
            form_score=form,
            conn_score=conn,
            front_prob=front_prob,
        )

        one_line = build_one_line_comment(
            early_score=early,
            late_score=late,
            speed_score=speed,
            form_score=form,
        )

        final_results.append(
            {
                "rcity": item["rcity"],
                "rdate": item["rdate"],
                "rno": item["rno"],
                "gate": gate,
                "horse": horse,
                "expected_rank": idx,
                "score": score,
                "front_run_place_prob": front_prob,
                "reason": reason,
                "one_line_comment": one_line,
                "early_score": early,
                "late_score": late,
                "late200_score": late200,
                "speed_score": speed,
                "form_score": form,
                "s1f_trend": s1f_trend,
                "g2f_trend": g2f_trend,
                "conn_score": conn,
            }
        )

    # 2) 신마/데뷔전급 말들 expected_rank=99 로 뒤에 추가
    for row in exp011_rows:
        gate = int(row[IDX_GATE])
        if new_type_by_gate.get(gate) is None:
            continue

        horse = row[IDX_HORSE]
        new_type = new_type_by_gate[gate]
        if new_type == "debut":
            reason = f"[{gate}번 {horse}] 신마(데뷔전) — 데이터 부족으로 평가 제외"
        else:
            reason = f"[{gate}번 {horse}] 신마(데뷔전급) — 데이터 부족으로 평가 제외"

        final_results.append(
            {
                "rcity": row[IDX_RCITY],
                "rdate": row[IDX_RDATE],
                "rno": int(row[IDX_RNO]),
                "gate": gate,
                "horse": horse,
                "expected_rank": 99,
                "score": None,
                "front_run_place_prob": 0.0,
                "reason": reason,
                "one_line_comment": None,
                "early_score": None,
                "late_score": None,
                "late200_score": None,
                "speed_score": None,
                "form_score": None,
                "s1f_trend": None,
                "g2f_trend": None,
                "conn_score": None,
            }
        )

    return final_results
