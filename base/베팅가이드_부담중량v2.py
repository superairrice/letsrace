#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from contextlib import closing
from itertools import combinations

import pymysql
import pandas as pd
import numpy as np


# =========================================
# 0. 전역 설정(가중치/파라미터 한 곳에 모으기)
# =========================================

# 스타일 점수(섹션+트렌드) 기본 가중치
STYLE_WEIGHTS = dict(
    w_s1f=0.35,  # 초반 200
    w_g3f=0.35,  # 종반 600
    w_g1f=0.15,  # 종반 200
    w_trend=0.15,  # 최근8 트렌드
)

# 최종 점수 가중치
FINAL_WEIGHTS = dict(
    w_rec=0.45,  # 기록점수
    w_style=0.35,  # 스타일(style_new)
    w_trend=0.20,  # 최근8 트렌드 (※ style_old에도 들어가 있으니 사실상 더블카운트 구조)
)

# 부담중량 보정 파라미터
BURDEN_PARAMS = dict(
    up_per_kg=-1.0,  # 증량 1kg당 -1점
    up_cap=6.0,  # 최대 6kg까지만 페널티
    down_per_kg=0.7,  # 감량 1kg당 +0.7점
    down_cap=5.0,  # 최대 5kg까지만 보너스
)


# ==============================
# 1. DB 연결 & 데이터 로드
# ==============================


def get_conn():
    """MySQL 접속 정보."""
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
    """
    exp011 + exp010(경주거리)까지 포함해서 로드.
    handycap_delta = handycap - i_prehandy
    """
    sql = """
    SELECT
        e.rcity,
        e.rdate,
        e.rno,
        (SELECT distance
         FROM The1.exp010 x
         WHERE x.rcity = e.rcity
           AND x.rdate = e.rdate
           AND x.rno   = e.rno
         LIMIT 1) AS 경주거리,
        e.gate,
        e.horse,
        e.h_weight AS 마체중,
        e.h_age    AS 마령,
        e.h_sex    AS 성별,
        e.i_cycle  AS 출주갭,
        e.rank     AS 예상1,
        e.r_pop    AS 예상2,
        e.m_rank,
        e.s1f_per  AS 초반200,
        e.g3f_per  AS 종반600,
        e.g1f_per  AS 종반200,
        e.rec_per  AS 기록점수,
        e.rec8_trend AS 최근8경주트렌드점수,
        e.jt_score AS 기수조교사연대점수,
        e.comment_one AS 코멘트,
        e.g2f_rank AS 최근8경주요약,
        (e.handycap - e.i_prehandy) AS 부담중량증감
    FROM The1.exp011 e
    WHERE e.rcity = %s
      AND e.rdate = %s
      AND e.rno   = %s
    ORDER BY e.gate
    """

    with closing(get_conn()) as conn, conn.cursor() as cur:
        cur.execute(sql, (rcity, rdate, rno))
        rows = cur.fetchall()

    if not rows:
        raise ValueError(f"해당 경주 데이터를 찾을 수 없습니다: {rcity} {rdate} R{rno}")

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


# ==============================
# 2. 페이스 / 스타일 분석
# ==============================


def classify_run_style(s1f: float) -> str:
    """
    초반200 지수 기준 스타일 분류
    """
    if s1f >= 80:
        return "front"  # 선행형
    elif s1f >= 40:
        return "mid"  # 중위권
    else:
        return "closer"  # 추입형


def summarize_pace(df: pd.DataFrame) -> dict:
    """
    경주 전체의 페이스 요약.
    """
    s1f_values = df["초반200"]
    avg_s1f = float(s1f_values.mean())

    styles = df["초반200"].apply(classify_run_style)
    d = df.copy()
    d["style_type"] = styles

    front_mask = d["style_type"] == "front"
    mid_mask = d["style_type"] == "mid"
    closer_mask = d["style_type"] == "closer"

    n_front = int(front_mask.sum())
    n_mid = int(mid_mask.sum())
    n_closer = int(closer_mask.sum())

    if n_front == 0:
        pace_desc = "느린 페이스(선행 부족) 예상"
    elif n_front == 1:
        pace_desc = "느린~보통 페이스(단독/소수 선행) 예상"
    elif n_front <= 3:
        pace_desc = "보통~중간 페이스 예상"
    else:
        pace_desc = "빠른 페이스(선행 다수) 예상"

    front_gates = d.loc[front_mask, "gate"].tolist()
    closer_gates = d.loc[closer_mask, "gate"].tolist()

    info = {
        "avg_s1f": avg_s1f,
        "n_front": n_front,
        "n_mid": n_mid,
        "n_closer": n_closer,
        "pace_desc": pace_desc,
        "front_gates": front_gates,
        "closer_gates": closer_gates,
    }
    return info


def distance_type(dist: int) -> str:
    """
    1400까지 단거리로 취급 (요청 반영).
    현재는 경주 전개/설명에만 활용 중이고,
    가중치는 모든 거리에서 동일하게 사용 중.
    """
    if dist <= 1400:
        return "short"
    elif dist <= 1800:
        return "middle"
    else:
        return "long"


# ==============================
# 3. 섹션 도미넌스(상위 5두 기준) & 스타일 점수
# ==============================


def dominance_by_top5(value: float, top5_mean: float) -> float:
    """
    value가 상위5 평균 대비 얼마나 좋은지/나쁜지에 따라 보너스/페널티.

    (현재 수치는 기존 로직 유지: ±10/±20 기준으로 ±4/±8점)
    """
    diff = value - top5_mean
    if diff >= 20:
        return 8.0
    elif diff >= 10:
        return 4.0
    elif diff <= -20:
        return -8.0
    elif diff <= -10:
        return -4.0
    else:
        return 0.0


def compute_style_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    style_old  : 섹션 + 트렌드 가중합
    style_new  : style_old + 상위5 평균 대비 도미넌스(S1F/G3F/G1F) 보정
    """
    d = df.copy()

    # --- style_old (기존 가중치 그대로 사용) ---
    w_s1f = STYLE_WEIGHTS["w_s1f"]
    w_g3f = STYLE_WEIGHTS["w_g3f"]
    w_g1f = STYLE_WEIGHTS["w_g1f"]
    w_trend = STYLE_WEIGHTS["w_trend"]

    d["style_old"] = (
        d["초반200"] * w_s1f
        + d["종반600"] * w_g3f
        + d["종반200"] * w_g1f
        + d["최근8경주트렌드점수"] * w_trend
    )

    # --- 상위5 평균 계산 (평균 대신 상위5 기준) ---
    top_k = min(5, len(d))

    s1f_top5_mean = d["초반200"].nlargest(top_k).mean()
    g3f_top5_mean = d["종반600"].nlargest(top_k).mean()
    g1f_top5_mean = d["종반200"].nlargest(top_k).mean()

    s1f_dom_list = []
    g3f_dom_list = []
    g1f_dom_list = []
    style_new_list = []

    for _, row in d.iterrows():
        s1f = row["초반200"]
        g3f = row["종반600"]
        g1f = row["종반200"]

        s1f_dom = dominance_by_top5(s1f, s1f_top5_mean)
        g3f_dom = dominance_by_top5(g3f, g3f_top5_mean)
        g1f_dom = dominance_by_top5(g1f, g1f_top5_mean)

        style_new = row["style_old"] + s1f_dom + g3f_dom + g1f_dom
        style_new = max(0.0, min(100.0, style_new))

        s1f_dom_list.append(s1f_dom)
        g3f_dom_list.append(g3f_dom)
        g1f_dom_list.append(g1f_dom)
        style_new_list.append(style_new)

    d["s1f_dom"] = s1f_dom_list
    d["g3f_dom"] = g3f_dom_list
    d["g1f_dom"] = g1f_dom_list
    d["style_new"] = style_new_list

    return d


# ==============================
# 4. 부담중량 보정
# ==============================


def extra_burden_delta(dw: float) -> float:
    """
    직전대비 부담중량 증감(dw)에 따른 추가 점수조정.

    현재 규칙:
    - 증량: kg당 -1점, 최대 -6점
    - 감량: kg당 +0.7점, 최대 +3.5점
    """
    if dw > 0:
        return BURDEN_PARAMS["up_per_kg"] * min(dw, BURDEN_PARAMS["up_cap"])
    elif dw < 0:
        return BURDEN_PARAMS["down_per_kg"] * min(-dw, BURDEN_PARAMS["down_cap"])
    else:
        return 0.0


# ==============================
# 5. 최종 점수, 축 신뢰도
# ==============================


def compute_final_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    style_old/style_new를 이용해 final_old / final_score 계산.
    final_score = final_old + extra_burden_delta(부담중량증감)
    """
    d = compute_style_scores(df)

    # final_old: 부담중량 보정 전
    w_rec = FINAL_WEIGHTS["w_rec"]
    w_style = FINAL_WEIGHTS["w_style"]
    w_trend = FINAL_WEIGHTS["w_trend"]

    d["final_old"] = (
        d["기록점수"] * w_rec
        + d["style_new"] * w_style
        + d["최근8경주트렌드점수"] * w_trend
    )

    # 부담중량 보정
    burden_adj_list = []
    final_new_list = []
    for _, row in d.iterrows():
        dw = row["부담중량증감"]
        delta = extra_burden_delta(dw)
        f_new = row["final_old"] + delta
        burden_adj_list.append(delta)
        final_new_list.append(f_new)

    d["부담중량보정"] = burden_adj_list
    d["final_score"] = final_new_list

    return d


def compute_trust_level(df: pd.DataFrame) -> dict:
    """
    최종 점수 분포로 축 신뢰도 산출.
    - ability_domination : 1위 vs 3위 점수차
    - form_domination    : 트렌드 최고 vs 평균
    - competition_pressure: 상위5두 점수 폭 좁을수록(혼전) ↑
    """
    scores = df["final_score"].values
    top = float(scores.max())
    sorted_scores = np.sort(scores)[::-1]
    if len(sorted_scores) >= 3:
        third = float(sorted_scores[2])
    else:
        third = float(sorted_scores[-1])

    # 상위 vs 3위 차이 비율
    ability_domination = max(0.0, min(100.0, (top - third) * 4.0))

    # 최근 폼은 트렌드 기반
    trend_vals = df["최근8경주트렌드점수"].values
    form_domination = max(
        0.0, min(100.0, (np.max(trend_vals) - np.mean(trend_vals)) * 2.0)
    )

    # 경쟁 압박: 상위5두 점수 범위가 좁을수록 압박↑
    top5 = sorted_scores[:5] if len(sorted_scores) >= 5 else sorted_scores
    if len(top5) > 1:
        spread = top5[0] - top5[-1]
        competition_pressure = max(0.0, min(100.0, 100.0 - spread * 2.0))
    else:
        competition_pressure = 0.0

    # 종합 trust_score (기존 방식 유지)
    trust_score = (
        ability_domination * 0.5
        + form_domination * 0.2
        + (100.0 - competition_pressure) * 0.3
    )

    if trust_score >= 75:
        level = "강축"
    elif trust_score >= 55:
        level = "보통축"
    else:
        level = "약한축"

    return dict(
        ability_domination=round(ability_domination, 1),
        form_domination=round(form_domination, 1),
        competition_pressure=int(round(competition_pressure)),
        trust_score=round(trust_score, 1),
        trust_level=level,
    )


def get_6복조_line(df: pd.DataFrame) -> list:
    """
    m_rank 기준 상위6두 -> 게이트 번호 리스트.
    동순위일 땐 final_score 높은 말 우선.
    """
    top6 = (
        df.sort_values(["m_rank", "final_score"], ascending=[True, False])
        .head(6)["gate"]
        .tolist()
    )
    return top6


# ==============================
# 5-1. 복병 선정 로직 (2번 + 3번 기준)
# ==============================


def _compute_pace_advantage(style_type: str, n_front: int) -> float:
    """
    페이스(선행마 수)와 스타일 타입을 이용해 유불리 점수 계산.
    """
    # 페이스 타입 설정
    if n_front >= 4:
        pace_type = "fast"
    elif n_front >= 2:
        pace_type = "normal"
    elif n_front == 1:
        pace_type = "slowish"
    else:
        pace_type = "slow"

    # 페이스 / 스타일 매칭
    if pace_type == "fast":
        if style_type == "closer":
            return 6.0
        elif style_type == "mid":
            return 2.0
        else:  # front
            return -4.0
    elif pace_type in ("slow", "slowish"):
        if style_type == "front":
            return 6.0
        elif style_type == "mid":
            return 2.0
        else:
            return -4.0
    else:  # normal
        if style_type == "front":
            return 2.0
        elif style_type == "mid":
            return 2.0
        else:
            return 0.0


def _compute_burden_advantage(dw: float) -> float:
    """
    부담중량 증감에 따른 복병 관점의 유불리 점수.
    (final_score와는 별개로, 복병에서는 감량 말을 조금 더 우대)
    """
    if dw <= -4:
        return 3.0
    elif dw <= -2:
        return 2.0
    elif dw <= -1:
        return 1.0
    elif dw == 0:
        return 0.0
    elif dw <= 2:
        return -1.0
    elif dw <= 4:
        return -2.0
    else:
        return -3.0


def select_dark_horses(df_scored: pd.DataFrame):
    """
    2번(페이스·부담중량) + 3번(m_rank vs final_score 괴리)를 모두 반영해서
    - 추천 복병 1두
    - 복병 후보군(나머지)
    을 반환.

    반환:
        main_dark (Series),
        others (DataFrame),
        debug_df (DataFrame: 전체 복병 관련 지표 포함)
    """
    d = df_scored.copy()

    # 스타일 타입 추가
    d["style_type"] = d["초반200"].apply(classify_run_style)

    # 페이스 정보
    pace_info = summarize_pace(df_scored)
    n_front = pace_info["n_front"]

    # final_score 순위 (fs_rank: 1위가 가장 강한 말)
    d = d.sort_values("final_score", ascending=False)
    d["fs_rank"] = np.arange(1, len(d) + 1)

    # m_rank vs fs_rank 괴리
    d["rank_gap"] = d["m_rank"] - d["fs_rank"]

    # 페이스 유불리 / 부담중량 유불리
    d["pace_adv"] = d["style_type"].apply(
        lambda st: _compute_pace_advantage(st, n_front)
    )
    d["burden_adv"] = d["부담중량증감"].apply(_compute_burden_advantage)

    # 기본 복병 점수
    d["dark_score_raw"] = (
        d["rank_gap"] * 3.0  # m_rank 대비 저평가 정도(3배 가중)
        + d["pace_adv"] * 1.0
        + d["burden_adv"] * 1.0
    )

    # 복병 후보 필터링:
    #  - m_rank 3위 이하 (1~2위는 정면 승부축/강축 라인으로 보고 제외)
    #  - final_score 하위 40% 이하는 컷
    fs_cut = d["final_score"].quantile(0.4)
    candidate_mask = (d["m_rank"] >= 3) & (d["final_score"] >= fs_cut)
    candidates = d[candidate_mask].copy()

    # 만약 너무 빡세서 한 마리도 안 남으면 m_rank>=3만 사용
    if candidates.empty:
        candidates = d[d["m_rank"] >= 3].copy()

    # 최종 dark_score (필요 시 clip)
    candidates["dark_score"] = candidates["dark_score_raw"]
    # 정렬
    candidates = candidates.sort_values("dark_score", ascending=False)

    # 메인 복병 1두
    main_dark = candidates.iloc[0]
    others = candidates.iloc[1:].copy()

    return main_dark, others, candidates


# ==============================
# 6. 베팅 플랜
# ==============================


def make_trifecta_tickets(top6_gates, anchor_gate, trust_level, total_budget=10000):
    """
    삼복승식 티켓 생성.

    - 강축: anchor 포함 + 나머지 5두 중 2두 조합 → C(5,2)=10구멍
    - 그 외(보통축/약한축): 6복조 풀조합 → C(6,3)=20구멍
    """
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


# ==============================
# 7. 출력 유틸
# ==============================


def print_pace_summary(df: pd.DataFrame):
    info = summarize_pace(df)
    n_total = len(df)

    print("=== 경주 전개 요약 ===")
    print(f"▶ 예상 페이스: {info['pace_desc']}")
    print(f"  - 평균 초반200 지수: {info['avg_s1f']:.1f}")
    print(f"  - 선행형(초반200≥80): {info['n_front']}두")
    print(f"  - 중위권(40≤초반200<80): {info['n_mid']}두")
    print(f"  - 추입형(초반200<40): {info['n_closer']}두")
    print()
    print(
        f"  선행형 마번: {', '.join(map(str, info['front_gates'])) if info['front_gates'] else '없음'}"
    )
    print(
        f"  추입형 마번: {', '.join(map(str, info['closer_gates'])) if info['closer_gates'] else '없음'}"
    )
    print()
    print(f"총 출전마 수: {n_total}두")
    print(f"평가/베팅 대상(신마 제외): {n_total}두")
    print()


def print_scores_and_anchor(df_scored: pd.DataFrame):
    """
    final_score 기준 상위마/출주마 전체 출력
    """
    d = df_scored.copy()
    d = d.sort_values("final_score", ascending=False)

    # 축마
    anchor_row = d.iloc[0]
    anchor_gate = int(anchor_row["gate"])
    anchor_name = anchor_row["horse"]
    anchor_score = anchor_row["final_score"]

    print("=== 축마 추천 (final_score 기준) ===")
    print(
        f"축마 게이트: {anchor_gate}, 마명: {anchor_name}, final_score: {anchor_score:.3f}"
    )
    print()

    print("=== 동반 입상마(참고용, final_score 2~6위) ===")
    for _, row in d.iloc[1:6].iterrows():
        print(
            {
                "마번": int(row["gate"]),
                "마명": row["horse"],
                "final_score": round(float(row["final_score"]), 3),
                "예상1": int(row["예상1"]),
                "예상2": int(row["예상2"]),
                "m_rank": int(row["m_rank"]),
                "트렌드": round(float(row["최근8경주트렌드점수"]), 1),
                "종반600": round(float(row["종반600"]), 1),
            }
        )
    print()

    print("=== 출주마 전체 final_score / m_rank / 스타일 점수 ===")
    for _, row in d.iterrows():
        print(
            f"게이트 {int(row['gate'])} / {row['horse']} / "
            f"m_rank={row['m_rank']:.1f} / final={row['final_score']:.2f} / "
            f"style={row['style_new']:.2f}"
        )
    print()


def print_debug_style_final(df_scored: pd.DataFrame):
    """
    style_old/style_new, final_old/final_score 디버그용 테이블 출력.
    """
    d = df_scored.copy().sort_values("gate")

    print()
    print("=== [디버그] 스타일/최종점수 전/후 비교 ===")
    print("게이트 | 마명       | dist | style_old | style_new | final_old | final_new")
    print("----------------------------------------------------------------------")
    for _, row in d.iterrows():
        gate = int(row["gate"])
        name = row["horse"]
        dist = int(row["경주거리"])
        s_old = row["style_old"]
        s_new = row["style_new"]
        f_old = row["final_old"]
        f_new = row["final_score"]
        print(
            f"{gate:3d}   | {name:<10} | {dist:4d} | "
            f"{s_old:9.2f} | {s_new:9.2f} | {f_old:9.2f} | {f_new:9.2f}"
        )
    print()


def print_trust_and_betting(df_scored: pd.DataFrame):
    d = df_scored.copy()
    d = d.sort_values("final_score", ascending=False)
    anchor_row = d.iloc[0]
    anchor_gate = int(anchor_row["gate"])
    anchor_name = anchor_row["horse"]

    trust = compute_trust_level(d)

    print("=== 축 신뢰도 (상대 비교 + 거리 가중치) ===")
    print(trust)
    print()

    # 6복조 라인
    top6_gates = get_6복조_line(d)
    print("=== 편성 상태 / 6복조 라인 ===")
    print("편성 상태(race_regime): clean")
    print(f"m_rank 기준 top6: {top6_gates}")
    print(f"조정 후(top6, anchor 포함): {sorted(set(top6_gates + [anchor_gate]))}")
    print()

    # =============================
    #   복병 선정 (2번 + 3번 기반)
    # =============================
    main_dark, others_dark, debug_dark = select_dark_horses(d)

    print("=== 복병 선정 결과 ===")
    print(
        f"추천 복병: 게이트 {int(main_dark['gate'])} / {main_dark['horse']} "
        f"(dark_score={main_dark['dark_score']:.1f}, "
        f"m_rank={int(main_dark['m_rank'])}, fs_rank={int(main_dark['fs_rank'])}, "
        f"style={main_dark['style_type']}, "
        f"pace_adv={main_dark['pace_adv']:.1f}, burden_adv={main_dark['burden_adv']:.1f})"
    )
    print()

    if not others_dark.empty:
        print("복병 후보군:")
        for _, row in others_dark.iterrows():
            print(
                f"  - 게이트 {int(row['gate'])} / {row['horse']} "
                f"(dark_score={row['dark_score']:.1f}, "
                f"m_rank={int(row['m_rank'])}, fs_rank={int(row['fs_rank'])}, "
                f"style={row['style_type']}, "
                f"pace_adv={row['pace_adv']:.1f}, burden_adv={row['burden_adv']:.1f}, "
                f"rank_gap={row['rank_gap']:.1f})"
            )
    else:
        print("복병 후보군: 없음")
    print()

    # (원하면 여기서 복병을 베팅 플랜에 섞어 넣는 것도 가능)

    mode = trust["trust_level"]
    print(f"=== 삼복승식 베팅 플랜 (총 10000원 기준) ===")
    print(
        f"모드: {mode} / 축마: {anchor_gate} / 축 신뢰도: {mode} ({trust['trust_score']}점)"
    )

    if mode == "강축":
        print("  → 메인 비중: 100% / 복병 라인: 0%")
    elif mode == "보통축":
        print("  → 메인 비중: 100% / 복병 라인: 0% (6복조 풀조합 분산)")
    else:
        print("  → 메인 비중: 100% / 복병 라인: 0% (약한축 분산 플레이)")
    print()
    print("복병: 위 추천 복병 + 후보군 참고")
    print()

    tickets = make_trifecta_tickets(
        top6_gates, anchor_gate, trust["trust_level"], total_budget=10000
    )

    print("▶ 메인 삼복조 티켓")
    for t in tickets:
        g1, g2, g3 = t["gates"]
        amount = t["amount"]
        h1 = d.loc[d["gate"] == g1, "horse"].iloc[0]
        h2 = d.loc[d["gate"] == g2, "horse"].iloc[0]
        h3 = d.loc[d["gate"] == g3, "horse"].iloc[0]
        print(f"  ({g1}-{g2}-{g3})  삼복조 : {amount}원  [{h1}, {h2}, {h3}]")
    print()
    print("▶ 복병 라인 삼복조 티켓")
    print("  (필요 시 추천 복병/후보군을 활용해 별도 구성 가능)")


# ==============================
# 8. 메인 실행부
# ==============================

if __name__ == "__main__":
    # 테스트용 기본 값 (여기만 바꿔서 재활용)
    rcity = "부산"
    rdate = "20251205"
    rno = 4

    df = load_race_exp011(rcity, rdate, rno)

    print_pace_summary(df)

    df_scored = compute_final_scores(df)

    print_scores_and_anchor(df_scored)
    print_debug_style_final(df_scored)
    print_trust_and_betting(df_scored)
