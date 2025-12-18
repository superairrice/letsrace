#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import combinations
from contextlib import closing

import pymysql
import pandas as pd
import numpy as np


# ============================================================
# 0. 전역 설정(가중치/파라미터)
# ============================================================

STYLE_WEIGHTS = dict(
    w_s1f=0.45,  # 초반200
    w_g3f=0.35,  # 종반600
    w_g1f=0.20,  # 종반200
)

FINAL_WEIGHTS = dict(
    w_rec=0.50,  # 기록
    w_style=0.30,  # 스타일
    w_trend=0.20,  # 트렌드 (최종에서 1회만 반영)
)

BURDEN_PARAMS = dict(
    up_per_kg=-1.0,
    up_cap=6.0,
    down_per_kg=0.7,
    down_cap=5.0,
)


# ============================================================
# 1. DB 연결 & 데이터 로드
# ============================================================


def get_conn():
    """MySQL 접속 정보"""
    return pymysql.connect(
        host="database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",
        user="letslove",
        password="Ruddksp!23",
        db="The1",
        port=3306,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def load_race_exp011(rcity, rdate, rno):
    sql = """
    SELECT
        e.rcity, e.rdate, e.rno,
        (SELECT distance FROM The1.exp010 x
         WHERE x.rcity=e.rcity AND x.rdate=e.rdate AND x.rno=e.rno LIMIT 1) AS 경주거리,
        e.gate, e.horse, e.h_weight AS 마체중, e.h_age AS 마령, e.h_sex AS 성별,
        e.i_cycle AS 출주갭, e.rank AS 예상1, e.r_pop AS 예상2, e.m_rank,
        e.s1f_per AS 초반200, e.g3f_per AS 종반600, e.g1f_per AS 종반200,
        e.rec_per AS 기록점수, e.rec8_trend AS 최근8경주트렌드점수,
        e.jt_score AS 기수조교사연대점수,
        e.comment_one AS 코멘트, e.g2f_rank AS 최근8경주요약,
        (e.handycap - e.i_prehandy) AS 부담중량증감
    FROM The1.exp011 e
    WHERE e.rcity=%s AND e.rdate=%s AND e.rno=%s
    ORDER BY e.gate
    """

    with closing(get_conn()) as conn, conn.cursor() as cur:
        cur.execute(sql, (rcity, rdate, rno))
        rows = cur.fetchall()

    if not rows:
        raise ValueError("해당 경주 데이터 없음")

    df = pd.DataFrame(rows)

    # 타입 정리
    df["경주거리"] = df["경주거리"].astype(int)
    df["gate"] = df["gate"].astype(int)
    df["마령"] = df["마령"].astype(float)
    df["출주갭"] = df["출주갭"].astype(float)
    df["예상1"] = df["예상1"].astype(int)
    df["예상2"] = df["예상2"].astype(int)
    df["m_rank"] = df["m_rank"].astype(int)
    df["초반200"] = df["초반200"].astype(float)
    df["종반600"] = df["종반600"].astype(float)
    df["종반200"] = df["종반200"].astype(float)
    df["기록점수"] = df["기록점수"].astype(float)
    df["최근8경주트렌드점수"] = df["최근8경주트렌드점수"].astype(float)
    df["기수조교사연대점수"] = df["기수조교사연대점수"].astype(float)
    df["부담중량증감"] = df["부담중량증감"].astype(float)

    return df


# ============================================================
# 2. 페이스 분석
# ============================================================


def classify_run_style(s1f):
    if s1f >= 80:
        return "front"
    elif s1f >= 40:
        return "mid"
    return "closer"


def summarize_pace(df):
    avg_s1f = df["초반200"].mean()

    df2 = df.copy()
    df2["style"] = df2["초반200"].apply(classify_run_style)

    n_front = (df2["style"] == "front").sum()
    n_mid = (df2["style"] == "mid").sum()
    n_closer = (df2["style"] == "closer").sum()

    # 페이스 해석
    if n_front == 0:
        pace = "느린 페이스(선행 부족)"
    elif n_front == 1:
        pace = "느린~보통 페이스"
    elif n_front <= 3:
        pace = "보통~중간 페이스"
    else:
        pace = "빠른 페이스"

    return dict(
        avg_s1f=float(avg_s1f),
        n_front=int(n_front),
        n_mid=int(n_mid),
        n_closer=int(n_closer),
        pace_desc=pace,
        front_gates=df2.loc[df2["style"] == "front", "gate"].tolist(),
        closer_gates=df2.loc[df2["style"] == "closer", "gate"].tolist(),
    )


# ============================================================
# 3. 스타일 점수 + 도미넌스
# ============================================================


def dominance_by_top5(val, mean5):
    diff = val - mean5
    if diff >= 20:
        return 8
    if diff >= 10:
        return 4
    if diff <= -20:
        return -8
    if diff <= -10:
        return -4
    return 0


def compute_style_scores(df):
    d = df.copy()

    # style_old = 트렌드 제외, 순수 섹션만
    d["style_old"] = (
        d["초반200"] * STYLE_WEIGHTS["w_s1f"]
        + d["종반600"] * STYLE_WEIGHTS["w_g3f"]
        + d["종반200"] * STYLE_WEIGHTS["w_g1f"]
    )

    top5 = min(5, len(d))
    mean_s1f = d["초반200"].nlargest(top5).mean()
    mean_g3f = d["종반600"].nlargest(top5).mean()
    mean_g1f = d["종반200"].nlargest(top5).mean()

    s1f_dom, g3f_dom, g1f_dom, style_new = [], [], [], []

    for _, row in d.iterrows():
        s_dom = dominance_by_top5(row["초반200"], mean_s1f)
        g_dom = dominance_by_top5(row["종반600"], mean_g3f)
        r_dom = dominance_by_top5(row["종반200"], mean_g1f)

        new_style = row["style_old"] + s_dom + g_dom + r_dom
        new_style = min(100.0, max(0.0, new_style))

        s1f_dom.append(s_dom)
        g3f_dom.append(g_dom)
        g1f_dom.append(r_dom)
        style_new.append(new_style)

    d["s1f_dom"] = s1f_dom
    d["g3f_dom"] = g3f_dom
    d["g1f_dom"] = g1f_dom
    d["style_new"] = style_new

    return d


# ============================================================
# 4. 부담중량 보정
# ============================================================


def extra_burden_delta(dw):
    if dw > 0:
        return BURDEN_PARAMS["up_per_kg"] * min(dw, BURDEN_PARAMS["up_cap"])
    if dw < 0:
        return BURDEN_PARAMS["down_per_kg"] * min(-dw, BURDEN_PARAMS["down_cap"])
    return 0.0


# ============================================================
# 5. 최종 점수 계산
# ============================================================


def compute_final_scores(df):
    d = compute_style_scores(df)

    d["final_old"] = (
        d["기록점수"] * FINAL_WEIGHTS["w_rec"]
        + d["style_new"] * FINAL_WEIGHTS["w_style"]
        + d["최근8경주트렌드점수"] * FINAL_WEIGHTS["w_trend"]
    )

    deltas, finals = [], []
    for _, row in d.iterrows():
        delta = extra_burden_delta(row["부담중량증감"])
        deltas.append(delta)
        finals.append(row["final_old"] + delta)

    d["부담중량보정"] = deltas
    d["final_score"] = finals

    return d


# ============================================================
# 6. 축 신뢰도
# ============================================================


def compute_trust_level(df):
    scores = df["final_score"].sort_values(ascending=False).values

    top = float(scores[0])
    third = float(scores[2]) if len(scores) >= 3 else float(scores[-1])

    ability = max(0.0, min(100.0, (top - third) * 3.0))

    top5 = scores[:5] if len(scores) >= 5 else scores
    if len(top5) > 1:
        clarity = max(0.0, min(100.0, (float(top5[0]) - float(top5[-1])) * 2.0))
    else:
        clarity = 100.0

    trust = ability * 0.6 + clarity * 0.4

    if trust >= 75:
        level = "강축"
    elif trust >= 55:
        level = "보통축"
    else:
        level = "약한축"

    return dict(
        ability_domination=round(ability, 1),
        field_clarity=round(clarity, 1),
        trust_score=round(trust, 1),
        trust_level=level,
    )


# ============================================================
# 7. 6복조 라인
# ============================================================


def get_6복조_line(df):
    return (
        df.sort_values(["final_score", "m_rank"], ascending=[False, True])
        .head(6)["gate"]
        .tolist()
    )


# ============================================================
# 8. 복병 선정 로직
# ============================================================


def compute_darkhorse_score(row, df_scored, pace_info, top6_df):
    """복병 점수 계산"""

    base_g3f = float(top6_df["종반600"].min())
    base_s1f = float(top6_df["초반200"].min())

    g3f_dom = (float(row["종반600"]) - base_g3f) * 0.40
    s1f_dom = (float(row["초반200"]) - base_s1f) * 0.20

    trend_mean = float(df_scored["최근8경주트렌드점수"].mean())
    trend_dom = (float(row["최근8경주트렌드점수"]) - trend_mean) * 0.20

    # 부담중량
    dw = float(row["부담중량증감"])
    if dw <= -2:
        weight_score = 10 * 0.20
    elif dw <= -1:
        weight_score = 5 * 0.20
    else:
        weight_score = 0.0

    # 전개 보정
    pace = pace_info["pace_desc"]
    s1f = float(row["초반200"])

    if s1f >= 80:
        style = "front"
    elif s1f >= 40:
        style = "mid"
    else:
        style = "closer"

    pace_bonus = 0.0
    if "빠른" in pace and style == "closer":
        pace_bonus = 10.0
    elif ("느린" in pace or "보통" in pace) and style == "front":
        pace_bonus = 7.0

    return g3f_dom + s1f_dom + trend_dom + weight_score + pace_bonus


def get_darkhorse_candidates(df_scored, pace_info, trust_level):
    """
    복병 후보 리스트 전체 반환:
    [{'gate', 'horse', 'final_score', 'darkhorse_score'}, ...]
    """
    df_sorted = df_scored.sort_values("final_score", ascending=False)
    top6_df = df_sorted.head(6)

    candidates = []

    for _, row in df_sorted.iloc[6:].iterrows():  # 7위 이하
        # 최소 전력 필터
        if float(row["final_score"]) < 40:
            continue
        if float(row["style_new"]) < 40:
            continue

        score = compute_darkhorse_score(row, df_scored, pace_info, top6_df)

        candidates.append(
            {
                "gate": int(row["gate"]),
                "horse": row["horse"],
                "final_score": float(row["final_score"]),
                "darkhorse_score": float(score),
            }
        )

    candidates = sorted(candidates, key=lambda x: x["darkhorse_score"], reverse=True)
    return candidates


def get_darkhorse(df_scored, pace_info, trust_level):
    """6복조 제외 → 복병 1마리 선정 (trust_level에 따라 임계값 달리 적용)"""

    df_sorted = df_scored.sort_values("final_score", ascending=False)
    top6_df = df_sorted.head(6)

    candidates_raw = []

    for _, row in df_sorted.iloc[6:].iterrows():  # 7위 이하
        if float(row["final_score"]) < 40:
            continue
        if float(row["style_new"]) < 40:
            continue
        score = compute_darkhorse_score(row, df_scored, pace_info, top6_df)
        candidates_raw.append((row, score))

    # 후보 자체가 없으면: 약한축일 때는 fallback으로 final_score 7위 복병 선정
    if not candidates_raw:
        if trust_level == "약한축" and len(df_sorted) > 6:
            fallback_row = df_sorted.iloc[6]  # final_score 7위
            return fallback_row, 0.0
        return None, None

    best_row, best_score = max(candidates_raw, key=lambda x: x[1])

    # trust_level 별 임계값
    if trust_level == "강축":
        threshold = 12.0
    elif trust_level == "보통축":
        threshold = 10.0
    else:  # 약한축
        threshold = 6.0

    if best_score < threshold:
        if trust_level == "약한축":
            # 약한축에서는 일단 복병 한두는 선정
            return best_row, best_score
        else:
            return None, None

    return best_row, best_score


# ============================================================
# 9. 삼복조 티켓 생성
# ============================================================


def make_trifecta_tickets(top6_gates, anchor_gate, trust_level, total_budget=10000):
    tickets = []

    if trust_level == "강축":
        others = [g for g in top6_gates if g != anchor_gate]
        combs = list(combinations(others, 2))
        n = len(combs)
        unit = total_budget // n if n > 0 else 0
        for a, b in combs:
            trio = sorted([anchor_gate, a, b])
            tickets.append({"gates": trio, "amount": unit})
    else:
        combs = list(combinations(top6_gates, 3))
        n = len(combs)
        unit = total_budget // n if n > 0 else 0
        for a, b, c in combs:
            trio = sorted([a, b, c])
            tickets.append({"gates": trio, "amount": unit})

    return tickets


def make_darkhorse_tickets(top6_gates, anchor_gate, darkhorse_gate, total_budget=3000):
    """
    복병 라인 삼복승식 티켓 생성.
    형태: (축마, 복병, top6의 다른 말)
    """
    tickets = []

    candidates = [g for g in top6_gates if g not in (anchor_gate, darkhorse_gate)]
    if not candidates:
        return tickets

    n = len(candidates)
    unit = total_budget // n if n > 0 else 0

    for g in candidates:
        trio = sorted([anchor_gate, darkhorse_gate, g])
        tickets.append({"gates": trio, "amount": unit})

    return tickets


# ============================================================
# 10. 출력 함수들
# ============================================================


def print_pace_summary(df):
    info = summarize_pace(df)
    print("=== 경주 전개 요약 ===")
    print(f"▶ {info['pace_desc']}")
    print(f"선행: {info['n_front']} 중위: {info['n_mid']} 추입: {info['n_closer']}")
    print(f"선행마: {info['front_gates']}")
    print(f"추입마: {info['closer_gates']} \n")


def print_scores_and_anchor(df):
    d = df.sort_values("final_score", ascending=False)
    a = d.iloc[0]
    print("=== 축마 추천 ===")
    print(f"Gate {int(a['gate'])} / {a['horse']} / Score {a['final_score']:.2f}\n")


def print_trust_and_betting(df_scored):
    d = df_scored.sort_values("final_score", ascending=False)
    anchor = d.iloc[0]
    trust = compute_trust_level(d)
    pace_info = summarize_pace(d)

    print("=== 축 신뢰도 ===")
    print(trust, "\n")

    # 6복조 라인
    top6_gates = get_6복조_line(d)
    print("=== 6복조 라인 ===")
    print("Top6:", top6_gates, "\n")

    # 복병 선정
    darkhorse, dh_score = get_darkhorse(d, pace_info, trust["trust_level"])

    print("=== 복병 선정 ===")
    if darkhorse is None:
        print("복병 없음\n")
    else:
        msg = (
            f"복병: 게이트 {int(darkhorse['gate'])} / {darkhorse['horse']} "
            f"/ 점수 {dh_score:.2f}"
        )
        if dh_score <= 0:
            msg += "  (약한축 Fallback 복병)"
        elif trust["trust_level"] == "약한축" and dh_score < 6:
            msg += "  (약한축 완화 기준 복병)"
        print(msg + "\n")

    # 복병 후보 리스트
    print("=== 복병 후보 리스트 ===")
    candidates = get_darkhorse_candidates(d, pace_info, trust["trust_level"])
    if candidates:
        for c in candidates:
            print(
                f"게이트 {c['gate']} / {c['horse']} / "
                f"final_score={c['final_score']:.2f} / "
                f"darkhorse_score={c['darkhorse_score']:.2f}"
            )
        print()
    else:
        print("정규 후보 없음 (필터 미통과)\n")

    # Fallback 복병도 후보 정보로 표시
    if darkhorse is not None and dh_score == 0:
        print("※ Fallback 복병 (정규 후보 조건 미통과):")
        print(
            f"게이트 {int(darkhorse['gate'])} / {darkhorse['horse']} / "
            f"final_score={float(darkhorse['final_score']):.2f} / "
            f"style={float(darkhorse['style_new']):.2f}"
        )
        print()

    # 전체 final_score 리스트
    print("=== 전체 final_score 리스트 ===")
    df_ranked = d.sort_values("final_score", ascending=False)
    for _, row in df_ranked.iterrows():
        print(
            f"게이트 {int(row['gate'])} / {row['horse']} / "
            f"final_score={row['final_score']:.2f} / "
            f"style={row['style_new']:.2f} / "
            f"trend={row['최근8경주트렌드점수']:.1f}"
        )
    print()

    # 메인 삼복 티켓
    anchor_gate = int(anchor["gate"])
    main_tickets = make_trifecta_tickets(
        top6_gates, anchor_gate, trust["trust_level"], total_budget=10000
    )

    print("=== 메인 삼복승식 티켓 (6복조 기반) ===")
    for t in main_tickets:
        print(t)
    print()

    # 복병 라인 티켓
    print("=== 복병 라인 삼복승식 티켓 ===")
    if darkhorse is not None:
        darkhorse_gate = int(darkhorse["gate"])
        darkhorse_tickets = make_darkhorse_tickets(
            top6_gates, anchor_gate, darkhorse_gate, total_budget=3000
        )
        if not darkhorse_tickets:
            print("  생성된 복병 조합 없음\n")
        else:
            for t in darkhorse_tickets:
                print(t)
            print()
    else:
        print("  복병 없음 (조합 미생성)\n")


# ============================================================
# 11. 메인 실행부
# ============================================================

if __name__ == "__main__":
    # 테스트용 기본 값
    rcity = "부산"
    rdate = "20251205"
    rno = 4

    df = load_race_exp011(rcity, rdate, rno)
    print_pace_summary(df)

    df_scored = compute_final_scores(df)

    print_scores_and_anchor(df_scored)
    print_trust_and_betting(df_scored)
