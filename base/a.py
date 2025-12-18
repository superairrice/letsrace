#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
[복병 최소 로직 vNEW]
- 기존 복병(darkhorse_score) 로직 전부 제거
- 복병 점수는 딱 2가지 축으로만 만든다.

(1) 선행형(FRONT): "거리 단축" + "선행지표 좋음" (+ 종반600 개선이면 추가 가점)
(2) 추입형(CLOSER): "거리 연장" (+ 종반600 개선이면 추가 가점)
(3) MID: 종반600 개선만 반영(약하게)

+ 혼재 경주 우선순위 규칙:
- 기본은 점수순 TOP3
- 단, TOP3가 전부 FRONT(또는 전부 CLOSER)로 쏠리면
  상대 스타일에서 1두를 끼워 넣어 (혼재 보험)
- 그래도 부족하면 MID 중 종반개선 우수로 채움

필수: exp011.g2f_rank 텍스트를 "최근 8경주 라인"에서 정밀 파싱해서
      종반600초(G3F sec) 개선치(Δ초)를 계산한다.
"""

from __future__ import annotations

from contextlib import closing
from typing import List, Dict, Any, Optional, Tuple
import os
import re
import pymysql
import pandas as pd


# =========================================================
# 0) DB
# =========================================================


def get_conn():
    """
    ✅ 보안상: 가능하면 환경변수 사용 권장
      MYSQL_HOST / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DB / MYSQL_PORT
    """
    host = os.getenv(
        "MYSQL_HOST", "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com"
    )
    user = os.getenv("MYSQL_USER", "letslove")
    password = os.getenv("MYSQL_PASSWORD", "Ruddksp!23")
    db = os.getenv("MYSQL_DB", "The1")
    port = int(os.getenv("MYSQL_PORT", "3306"))

    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        db=db,
        port=port,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def load_race(rcity: str, rdate: str, rno: int) -> List[Dict[str, Any]]:
    """
    - 경주거리(exp010)
    - 직전경주거리(record_s 최신 1개)
    - g2f_rank(최근8경주 텍스트) 포함
    """
    sql = """
        SELECT 
            e.rcity, e.rdate, e.rno,
            (SELECT distance 
             FROM The1.exp010 t 
             WHERE t.rcity=e.rcity AND t.rdate=e.rdate AND t.rno=e.rno
            ) AS 경주거리,

            (SELECT distance 
             FROM The1.record_s k 
             WHERE k.horse = e.horse
               AND k.rdate = (
                   SELECT MAX(rdate)
                   FROM The1.record_s
                   WHERE horse = k.horse AND rdate < %s
               )
            ) AS 직전경주거리,

            e.gate, e.horse,
            e.h_weight AS 마체중,
            e.h_age AS 마령,
            e.i_cycle AS 출주갭,
            e.rank AS 예상1,
            e.r_pop AS 예상2,
            e.m_rank,
            e.s1f_per AS 초반200,
            e.g3f_per AS 종반600,
            e.g1f_per AS 종반200,
            e.rec_per AS 기록점수,
            e.rec8_trend AS 최근8,
            e.jt_score AS 연대,
            e.year_race AS 출주수,
            e.g2f_rank
        FROM The1.exp011 e
        WHERE e.rcity=%s AND e.rdate=%s AND e.rno=%s
        ORDER BY e.gate
    """
    with closing(get_conn()) as conn:
        df = pd.read_sql(sql, conn, params=(rdate, rcity, rdate, rno))

    # NaN → 0
    return df.fillna(0).to_dict("records")


# =========================================================
# 1) g2f_rank 정밀 파서
# =========================================================

# 예시 라인:
# '25.11.07 ... G6 ... 14.6 ... 39.4  ... 1:30.5 ... 순위: 6 ... 3.3 ... -6
RE_G2F_ROW = re.compile(
    r"'\s*(\d{2}\.\d{2}\.\d{2})\s*\.\.\.\s*([A-Za-z0-9]+)\s*\.\.\.\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*\.\.\.\s*([0-9]+(?:\.[0-9]+)?)"
)


def parse_g2f_rank_rows(text: str) -> List[Dict[str, Any]]:
    """
    g2f_rank 텍스트에서 (date, class, s1f_sec, g3f_sec)를 추출.
    텍스트에 적힌 순서(최신→과거)를 그대로 유지한다고 가정.
    """
    if not text:
        return []

    rows: List[Dict[str, Any]] = []
    for line in str(text).splitlines():
        m = RE_G2F_ROW.search(line)
        if not m:
            continue
        rows.append(
            {
                "date": m.group(1),
                "cls": m.group(2),
                "s1f_sec": float(m.group(3)),
                "g3f_sec": float(m.group(4)),
            }
        )
    return rows


def calc_g3f_improve_sec(rows: List[Dict[str, Any]]) -> float:
    """
    Δ종반600(초) 개선치(+) = (이전2 평균) - (최근2 평균)
    - rows가 3개 미만이면 0
    """
    if len(rows) < 3:
        return 0.0

    g3 = [r["g3f_sec"] for r in rows if r.get("g3f_sec") is not None]
    if len(g3) < 3:
        return 0.0

    recent = g3[:2]
    prev = g3[2:4] if len(g3) >= 4 else g3[2:3]
    if not prev:
        return 0.0

    improve = (sum(prev) / len(prev)) - (sum(recent) / len(recent))
    return round(improve, 2)


# =========================================================
# 2) 스타일 판정 + 복병점수(최소 로직)
# =========================================================


def detect_style(s1f_per: float) -> str:
    """
    - 초반200 퍼센트 지표 기반 (0은 결측 가능성이 높으므로 UNK 처리)
    """
    try:
        v = float(s1f_per)
    except Exception:
        return "UNK"

    if v <= 0:
        return "UNK"
    if v >= 70:
        return "FRONT"
    if v <= 30:
        return "CLOSER"
    return "MID"


def _dist_num(x: Any) -> int:
    try:
        return int(float(x))
    except Exception:
        return 0


def compute_dark_pick_score(h: Dict[str, Any]) -> float:
    """
    [복병점수] = 거리변화 시그널 + 종반600 개선 시그널

    - FRONT:
        - 거리 단축이면 강하게 +
        - 선행지표(초반200)가 높을수록 +
        - 종반600 개선(초)이 있으면 추가 +
    - CLOSER:
        - 거리 연장이면 +
        - 종반600 개선이 있으면 추가 +
    - MID:
        - 종반600 개선만 약하게 +
    - UNK:
        - 종반600 개선만 아주 약하게 +
    """
    style = h.get("style", "UNK")
    cur_dist = _dist_num(h.get("경주거리"))
    prev_dist = _dist_num(h.get("직전경주거리"))

    s1f = float(h.get("초반200") or 0.0)
    g3f_imp = float(h.get("g3f_improve_sec") or 0.0)

    # 거리변화
    dist_delta = cur_dist - prev_dist  # +면 연장, -면 단축
    shortened = prev_dist > 0 and dist_delta < 0
    stretched = prev_dist > 0 and dist_delta > 0

    score = 0.0

    # 1) 종반600 개선(초) 점수화: 1.0초 개선이면 +2.0 정도 (너무 과하지 않게)
    #    개선이 음수면(악화) 패널티는 일단 넣지 않는다(최소 로직 유지).
    improve_part = max(0.0, g3f_imp) * 2.0

    # 2) 스타일별 거리 시그널
    if style == "FRONT":
        if shortened:
            score += 3.0
        # 선행지표 보정 (70~100 구간이면 +0.0~+1.5 정도)
        score += max(0.0, (s1f - 70.0)) / 20.0 * 1.5
        score += improve_part * 0.8  # FRONT는 종반개선도 반영하되 살짝 약하게

    elif style == "CLOSER":
        if stretched:
            score += 3.0
        score += improve_part * 1.0  # 추입은 종반개선이 핵심

    elif style == "MID":
        score += improve_part * 0.7

    else:  # UNK
        score += improve_part * 0.4

    return round(score, 2)


def make_pick_comment(h: Dict[str, Any]) -> str:
    style = h.get("style", "UNK")
    cur_dist = _dist_num(h.get("경주거리"))
    prev_dist = _dist_num(h.get("직전경주거리"))
    s1f = float(h.get("초반200") or 0.0)
    g3 = float(h.get("g3f_improve_sec") or 0.0)

    dist_part = ""
    if prev_dist > 0:
        if cur_dist < prev_dist:
            dist_part = f"단축 {prev_dist}->{cur_dist}"
        elif cur_dist > prev_dist:
            dist_part = f"연장 {prev_dist}->{cur_dist}"
        else:
            dist_part = f"동일 {prev_dist}->{cur_dist}"
    else:
        dist_part = f"직전거리없음->{cur_dist}"

    imp_part = f"Δ종반600 +{g3:.2f}s" if g3 > 0 else f"Δ종반600 {g3:.2f}s"

    if style == "FRONT":
        return f"선행형 / S1F {s1f:.1f} + {dist_part} / {imp_part}"
    if style == "CLOSER":
        return f"추입형 / {dist_part} / {imp_part}"
    if style == "MID":
        return f"중위형 / {dist_part} / {imp_part}"
    return f"미분류 / {dist_part} / {imp_part}"


# =========================================================
# 3) 혼재 경주 우선순위 규칙 (TOP3 선정)
# =========================================================


def pick_top3(horses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    - 기본: dark_pick_score 내림차순 TOP3
    - 혼재 룰:
        TOP3가 FRONT만(>=2) + CLOSER 0이면 -> CLOSER 1두를 끼워넣기
        TOP3가 CLOSER만(>=2) + FRONT 0이면 -> FRONT 1두를 끼워넣기
    - 끼워넣을 후보는 해당 스타일 중 점수 최상위 1두
    - 부족하면 MID 중 점수 높은 순으로 채움
    """
    sorted_all = sorted(
        horses, key=lambda x: float(x.get("dark_pick_score") or 0.0), reverse=True
    )
    top3 = sorted_all[:3]

    def count_style(lst, st):
        return sum(1 for h in lst if h.get("style") == st)

    front_n = count_style(top3, "FRONT")
    closer_n = count_style(top3, "CLOSER")

    # 스타일별 풀
    fronts = [h for h in sorted_all if h.get("style") == "FRONT"]
    closers = [h for h in sorted_all if h.get("style") == "CLOSER"]
    mids = [h for h in sorted_all if h.get("style") == "MID"]
    unks = [h for h in sorted_all if h.get("style") == "UNK"]

    def replace_one(target_style: str, candidate_pool: List[Dict[str, Any]]):
        nonlocal top3
        # 후보가 없으면 패스
        if not candidate_pool:
            return
        cand = candidate_pool[0]
        # 이미 top3에 있으면 패스
        if any((cand["gate"], cand["horse"]) == (h["gate"], h["horse"]) for h in top3):
            return
        # 교체 대상은 "가장 점수 낮은 말" 중에서 반대 스타일/UNK/MID 우선
        top3_sorted_low = sorted(
            top3, key=lambda x: float(x.get("dark_pick_score") or 0.0)
        )
        # 가능하면 target_style이 아닌 말 중 최저를 교체
        victim = None
        for v in top3_sorted_low:
            if v.get("style") != target_style:
                victim = v
                break
        if victim is None:
            victim = top3_sorted_low[0]
        top3 = [
            cand if (h["gate"], h["horse"]) == (victim["gate"], victim["horse"]) else h
            for h in top3
        ]

    # 혼재 강제: FRONT 쏠림이면 CLOSER 한두
    if front_n >= 2 and closer_n == 0:
        replace_one("CLOSER", closers)

    # CLOSER 쏠림이면 FRONT 한두
    if closer_n >= 2 and front_n == 0:
        replace_one("FRONT", fronts)

    # 그래도 3두가 모자라지는 않지만, 혹시 중복/이상치 대비해 유니크 보정
    uniq = []
    seen = set()
    for h in top3:
        k = (h.get("gate"), h.get("horse"))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(h)
    top3 = uniq

    # 3두 미만이면 MID → UNK 순으로 채움
    if len(top3) < 3:
        for pool in (mids, unks, sorted_all):
            for h in pool:
                k = (h.get("gate"), h.get("horse"))
                if k in seen:
                    continue
                seen.add(k)
                top3.append(h)
                if len(top3) == 3:
                    break
            if len(top3) == 3:
                break

    # 최종 정렬(점수순)
    top3 = sorted(
        top3, key=lambda x: float(x.get("dark_pick_score") or 0.0), reverse=True
    )
    return top3[:3]


# =========================================================
# 4) (선택) final_score / trust_score는 기존 그대로 두되,
#    여기서는 "복병 최소 로직"에 직접 영향은 주지 않음.
# =========================================================


def compute_final_score(h: Dict[str, Any]) -> float:
    rec = float(h.get("기록점수") or 0.0)
    g3f = float(h.get("종반600") or 0.0)
    g1f = float(h.get("종반200") or 0.0)
    trend = float(h.get("최근8") or 0.0)
    jt = float(h.get("연대") or 0.0)

    base = 0.25 * rec + 0.25 * g3f + 0.15 * g1f + 0.15 * trend + 0.20 * jt

    dist = _dist_num(h.get("경주거리")) or 1200
    s1 = float(h.get("초반200") or 0.0)

    if dist <= 1200:
        style = 0.55 * s1 + 0.30 * g3f + 0.15 * trend
    elif dist <= 1600:
        style = 0.40 * s1 + 0.40 * g3f + 0.20 * trend
    else:
        style = 0.25 * s1 + 0.55 * g3f + 0.20 * trend

    mr = int(h.get("m_rank") or 10)
    mr_bonus = max(0, (10 - mr)) * 0.4

    final_score = base * 0.6 + style * 0.4 + mr_bonus
    h["final_score"] = round(final_score, 2)
    return float(h["final_score"])


def ability_score(h: Dict[str, Any]) -> float:
    base = (
        0.4 * float(h.get("기록점수") or 0.0)
        + 0.4 * float(h.get("종반600") or 0.0)
        + 0.2 * float(h.get("최근8") or 0.0)
    )
    mr = int(h.get("m_rank") or 10)
    return base + max(0, (10 - mr)) * 0.2


def calc_trust_score(anchor: Dict[str, Any], horses: List[Dict[str, Any]]) -> float:
    scores = sorted([ability_score(h) for h in horses], reverse=True)
    my = ability_score(anchor)

    if len(scores) >= 3:
        rival_avg = (scores[1] + scores[2]) / 2.0
    elif len(scores) == 2:
        rival_avg = scores[1]
    else:
        rival_avg = scores[0]

    a_dom = 50 + 2.5 * (my - rival_avg)
    avg_g3 = sum(float(h.get("종반600") or 0.0) for h in horses) / max(1, len(horses))
    f_dom = 50 + (float(anchor.get("종반600") or 0.0) - avg_g3) / 2.5
    comp = 70 if my >= rival_avg + 2 else 40

    trust = 0.45 * a_dom + 0.35 * f_dom + 0.20 * comp
    trust = max(0, min(100, trust))
    return round(trust, 1)


def trust_label(score: float) -> str:
    if score >= 90:
        return "초강축"
    if score >= 75:
        return "강축"
    if score >= 60:
        return "보통축"
    if score >= 45:
        return "약한축"
    return "위험축"


# =========================================================
# 5) 엔진: 요약표 + TOP3 복병
# =========================================================


def build_table_and_picks(
    horses: List[Dict[str, Any]],
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], str]:
    # 점수(기존 유지: final/trust)
    for h in horses:
        compute_final_score(h)
    for h in horses:
        ts = calc_trust_score(h, horses)
        h["trust_score"] = ts
        h["trust_label"] = trust_label(ts)

    # g2f_rank 파싱 + Δ종반600(초)
    for h in horses:
        rows = parse_g2f_rank_rows(h.get("g2f_rank") or "")
        h["g3f_improve_sec"] = calc_g3f_improve_sec(rows)

    # 스타일 + 복병점수
    for h in horses:
        h["style"] = detect_style(h.get("초반200") or 0.0)
        h["dark_pick_score"] = compute_dark_pick_score(h)
        h["dark_comment"] = make_pick_comment(h)

    # TOP3 선정 (혼재 룰)
    top3 = pick_top3(horses)

    # 아이콘/코멘트
    top_keys = {(h["gate"], h["horse"]) for h in top3}
    for h in horses:
        if (h["gate"], h["horse"]) in top_keys:
            # 진짜복병(🔥): FRONT+단축 or CLOSER+연장 같은 "방향성"이 맞고 점수가 높은 경우
            cur_dist = _dist_num(h.get("경주거리"))
            prev_dist = _dist_num(h.get("직전경주거리"))
            dist_delta = cur_dist - prev_dist if prev_dist > 0 else 0
            stretched = prev_dist > 0 and dist_delta > 0
            shortened = prev_dist > 0 and dist_delta < 0
            g3imp = float(h.get("g3f_improve_sec") or 0.0)
            s1f = float(h.get("초반200") or 0.0)

            is_true = False
            if h["style"] == "FRONT" and shortened and s1f >= 70:
                is_true = True
            if h["style"] == "CLOSER" and stretched and g3imp > 0:
                is_true = True

            if is_true and h["dark_pick_score"] >= 4.5:
                h["pick_mark"] = "🔥"
                h["pick_note"] = f"🔥 진짜복병: {h['dark_comment']}"
            else:
                h["pick_mark"] = "⭐"
                h["pick_note"] = f"⭐ 후보: {h['dark_comment']}"
        else:
            h["pick_mark"] = ""
            h["pick_note"] = ""

    # 요약표
    rows = []
    for h in sorted(
        horses, key=lambda x: float(x.get("dark_pick_score") or 0.0), reverse=True
    ):
        rows.append(
            {
                "gate": h.get("gate"),
                "horse": h.get("horse"),
                "style": h.get("style"),
                "직전": _dist_num(h.get("직전경주거리")),
                "이번": _dist_num(h.get("경주거리")),
                "초반200": round(float(h.get("초반200") or 0.0), 1),
                "Δ종반600": round(float(h.get("g3f_improve_sec") or 0.0), 2),
                "복병점수": round(float(h.get("dark_pick_score") or 0.0), 2),
            }
        )
    df = pd.DataFrame(rows)

    # 총평
    total = len(horses)
    front_n = sum(1 for h in horses if h.get("style") == "FRONT")
    closer_n = sum(1 for h in horses if h.get("style") == "CLOSER")
    unk_n = sum(1 for h in horses if h.get("style") == "UNK")

    if front_n >= 3 and closer_n >= 2:
        pace = "선행·추입 혼재(경합 가능) — 전개 변동성 큼"
    elif front_n >= 3:
        pace = "선행 다수 — 경합 시 종반형(추입/선입) 유리"
    elif closer_n >= 3:
        pace = "추입 다수 — 초반 느리면 선행/선입 유리"
    else:
        pace = "혼전(평균 페이스) — 말별 거리변화/개선치가 관건"

    # TOP3 문장
    pick_lines = []
    for h in top3:
        pick_lines.append(
            f"- {h['horse']}({h['gate']}) : {h.get('style')} / score {h.get('dark_pick_score'):.2f} / {h.get('pick_note')}"
        )

    overview = (
        f"- 총두수: {total}\n"
        f"- 스타일 분포: FRONT {front_n}, CLOSER {closer_n}, UNK {unk_n}\n"
        f"- 페이스 전망: {pace}\n"
        f"- 복병 TOP3(최소 로직: '거리변화+종반개선'):\n" + "\n".join(pick_lines)
    )

    return df, top3, overview


# =========================================================
# 6) 실행
# =========================================================

if __name__ == "__main__":
    rcity = "부산"
    rdate = "20251205"
    rno = 4

    horses = load_race(rcity, rdate, rno)
    if not horses:
        print("데이터 없음")
        raise SystemExit(0)

    df, top3, overview = build_table_and_picks(horses)

    print("[요약] 핵심 지표")
    print(df.to_string(index=False))

    print("\n[복병 추천 TOP3]")
    for h in top3:
        print(
            f"- {h['horse']}({h['gate']}) : {h.get('style')} / score {h.get('dark_pick_score'):.2f}"
        )

    print("\n[경주 총평]")
    print(overview)
