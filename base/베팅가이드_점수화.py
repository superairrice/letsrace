#!/usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import closing
from typing import List, Dict, Any
import os
import pymysql
import pandas as pd


# ====================================
# 1. DB
# ====================================


def get_conn():
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
    sql = """
        SELECT 
            e.rcity, e.rdate, e.rno,
            (SELECT distance 
             FROM The1.exp010 t 
             WHERE t.rcity=e.rcity AND t.rdate=e.rdate AND t.rno=e.rno
            ) AS 경주거리,
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
            e.year_race AS 출주수
        FROM The1.exp011 e
        WHERE e.rcity=%s AND e.rdate=%s AND e.rno=%s
        ORDER BY e.gate
    """
    with closing(get_conn()) as conn:
        df = pd.read_sql(sql, conn, params=(rcity, rdate, rno))

    return df.fillna(0).to_dict("records")


# ====================================
# 2. SCORE 함수들
# ====================================


def compute_final_score(h: Dict[str, Any]) -> float:
    """
    final_score = base(기록+종반+트렌드+연대) + style(거리별 초/종반+트렌드) + m_rank 보너스

    각 구성요소를 h에 저장:
      - h["final_base"]
      - h["final_style"]
      - h["final_mr_bonus"]
    """
    rec = h["기록점수"]
    g3f = h["종반600"]
    g1f = h["종반200"]
    trend = h["최근8"]
    jt = h["연대"]

    base = 0.25 * rec + 0.25 * g3f + 0.15 * g1f + 0.15 * trend + 0.20 * jt

    dist = h["경주거리"] or 1200
    if dist <= 1200:
        style = 0.55 * h["초반200"] + 0.30 * h["종반600"] + 0.15 * h["최근8"]
    elif dist <= 1600:
        style = 0.40 * h["초반200"] + 0.40 * h["종반600"] + 0.20 * h["최근8"]
    else:
        style = 0.25 * h["초반200"] + 0.55 * h["종반600"] + 0.20 * h["최근8"]

    mr = h["m_rank"] if h["m_rank"] else 10
    mr_bonus = max(0, (10 - mr)) * 0.4

    final_score = base * 0.6 + style * 0.4 + mr_bonus

    h["final_base"] = base
    h["final_style"] = style
    h["final_mr_bonus"] = mr_bonus
    h["final_score"] = final_score

    return final_score


def ability_score(h: Dict[str, Any]) -> float:
    base = 0.4 * h["기록점수"] + 0.4 * h["종반600"] + 0.2 * h["최근8"]
    mr = h["m_rank"] if h["m_rank"] else 10
    return base + max(0, (10 - mr)) * 0.2


def calc_trust_detail(
    anchor: Dict[str, Any], horses: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    trust_score 구성요소까지 함께 반환:
      - ability_domination
      - form_domination
      - competition_pressure
      - trust_score
    """
    # ability domination
    all_scores = sorted([ability_score(h) for h in horses], reverse=True)
    my = ability_score(anchor)
    if len(all_scores) >= 3:
        rival_avg = (all_scores[1] + all_scores[2]) / 2.0
    elif len(all_scores) == 2:
        rival_avg = all_scores[1]
    else:
        rival_avg = all_scores[0]

    a_dom = 50 + 2.5 * (my - rival_avg)

    # form domination (종반600 기준)
    avg_g3 = sum(h["종반600"] for h in horses) / len(horses)
    f_dom = 50 + (anchor["종반600"] - avg_g3) / 2.5

    # competition pressure
    comp = 70 if my >= rival_avg + 2 else 40

    trust = 0.45 * a_dom + 0.35 * f_dom + 0.20 * comp
    trust = max(0, min(100, trust))

    return {
        "ability_domination": a_dom,
        "form_domination": f_dom,
        "competition_pressure": comp,
        "trust_score": trust,
    }


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


def compute_darkhorse_score(h: Dict[str, Any], avg: Dict[str, float]) -> float:
    """
    darkhorse_score: 편성 평균 대비 '숨겨진 한 방' 가능성.
      - 초반/종반/트렌드가 평균보다 좋은데, 기록은 상대적으로 떨어질 때 가점.
    """
    s1f = h["초반200"]
    g3f = h["종반600"]
    trend = h["최근8"]
    rec = h["기록점수"]

    score = 0.0
    score += 0.05 * (s1f - avg["초반200"])
    score += 0.08 * (g3f - avg["종반600"])
    score += 0.06 * (trend - avg["최근8"])

    # 기록이 평균보다 확실히 나쁜데, 다른 지표가 좋은 경우 → '복병형'
    rec_penalty_boost = 0.0
    if rec < avg["기록점수"] - 10:
        rec_penalty_boost = 3.0
        score += rec_penalty_boost

    h["dark_s1f_diff"] = s1f - avg["초반200"]
    h["dark_g3f_diff"] = g3f - avg["종반600"]
    h["dark_trend_diff"] = trend - avg["최근8"]
    h["dark_rec_diff"] = rec - avg["기록점수"]
    h["dark_rec_boost"] = rec_penalty_boost

    dh = round(score, 2)
    h["darkhorse_score"] = dh
    return dh


# ====================================
# 3. COMMENT & BASIS 생성기
# ====================================


def comment_final(fs: float) -> str:
    if fs >= 70:
        return "편성 최우수급 능력. 우승권 강력."
    if fs >= 60:
        return "입상권 강력. 능력 안정적."
    if fs >= 50:
        return "입상 가능권. 전개 따라 가능."
    if fs >= 40:
        return "중위권 수준. 전개 필요."
    return "저평가 구간. 복병 정도의 가능성."


def comment_trust(label: str) -> str:
    if label == "초강축":
        return "축으로 매우 안정적. 필승축에 가까운 신뢰도."
    if label == "강축":
        return "축으로 신뢰 가능한 수준. 입상권 안정감."
    if label == "보통축":
        return "축으로 무난하나 리스크 존재."
    if label == "약한축":
        return "축 불안. 분산 베팅 권장."
    return "축으로는 위험. 축 배제도 고려할 수준."


def comment_dark(dh: float) -> str:
    if dh >= 12:
        return "복병 잠재력 매우 높음. 한 방 가능."
    if dh >= 7:
        return "복병 가능성 있음. 주의 필요."
    if dh >= 3:
        return "복병 가능성 약함. 참고용."
    return "복병감 거의 없음."


def basis_final(h: Dict[str, Any], avg: Dict[str, float]) -> str:
    """
    final_score 산출 근거 텍스트
    - 기록/종반/트렌드/연대 + 스타일 + m_rank 보너스
    """
    return (
        f"기록 {h['기록점수']:.1f}(편균 {avg['rec']:.1f}), "
        f"종반600 {h['종반600']:.1f}(편균 {avg['g3f']:.1f}), "
        f"트렌드 {h['최근8']:.1f}(편균 {avg['trend']:.1f}), 연대 {h['연대']:.1f} 기반 base {h['final_base']:.1f}, "
        f"거리 {int(h['경주거리'])}m 스타일 점수 {h['final_style']:.1f} "
        f"+ m_rank({int(h['m_rank'])}) 보정 {h['final_mr_bonus']:.1f}점 → final_score {h['final_score']:.2f}"
    )


def basis_trust(h: Dict[str, Any]) -> str:
    """
    trust_score 산출 근거:
      - ability_domination / form_domination / competition_pressure
    """
    return (
        f"ability_domination {h['trust_a_dom']:.1f}, "
        f"form_domination {h['trust_f_dom']:.1f}, "
        f"competition_pressure {h['trust_comp']:.1f}의 "
        f"가중합으로 trust_score {h['trust_score']:.1f} 산출"
    )


def basis_dark(h: Dict[str, Any]) -> str:
    """
    darkhorse_score 산출 근거:
      - 초/종반/트렌드 편성 평균 대비 차이 + 기록이 나쁠 때 복병 가점
    """
    parts = []
    parts.append(
        f"초반200 편차 {h['dark_s1f_diff']:+.1f}, "
        f"종반600 편차 {h['dark_g3f_diff']:+.1f}, "
        f"트렌드 편차 {h['dark_trend_diff']:+.1f}"
    )
    if h["dark_rec_boost"] > 0:
        parts.append(
            f"기록은 편균 대비 {h['dark_rec_diff']:.1f} 낮아 숨은 복병형으로 +{h['dark_rec_boost']:.1f}점 가산"
        )
    else:
        parts.append(f"기록 편차 {h['dark_rec_diff']:+.1f}로 별도 복병 가점 없음")

    parts.append(f"→ darkhorse_score {h['darkhorse_score']:.2f}")
    return " / ".join(parts)


# ====================================
# 4. LISTUP ENGINE
# ====================================


def listup_scores(horses: List[Dict[str, Any]]) -> pd.DataFrame:
    # 1) final_score + 구성요소
    for h in horses:
        compute_final_score(h)

    # 2) 편성 평균
    avg = {
        "s1f": sum(h["초반200"] for h in horses) / len(horses),
        "g3f": sum(h["종반600"] for h in horses) / len(horses),
        "trend": sum(h["최근8"] for h in horses) / len(horses),
        "rec": sum(h["기록점수"] for h in horses) / len(horses),
        "final": sum(h["final_score"] for h in horses) / len(horses),
    }

    # 3) trust_score + 구성요소
    for h in horses:
        detail = calc_trust_detail(h, horses)
        h["trust_a_dom"] = detail["ability_domination"]
        h["trust_f_dom"] = detail["form_domination"]
        h["trust_comp"] = detail["competition_pressure"]
        h["trust_score"] = detail["trust_score"]
        h["trust_label"] = trust_label(h["trust_score"])

    # 4) darkhorse_score + 구성요소
    avg_for_dark = {
        "초반200": avg["s1f"],
        "종반600": avg["g3f"],
        "최근8": avg["trend"],
        "기록점수": avg["rec"],
    }
    for h in horses:
        compute_darkhorse_score(h, avg_for_dark)

    # 5) 코멘트 + 산출 근거 텍스트
    for h in horses:
        h["comment_final"] = comment_final(h["final_score"])
        h["basis_final"] = basis_final(h, avg)

        h["comment_trust"] = comment_trust(h["trust_label"])
        h["basis_trust"] = basis_trust(h)

        h["comment_dark"] = comment_dark(h["darkhorse_score"])
        h["basis_dark"] = basis_dark(h)

    # 6) DataFrame 정리 (final_score 기준 내림차순)
    rows = []
    for h in sorted(horses, key=lambda x: x["final_score"], reverse=True):
        rows.append(
            {
                "gate": h["gate"],
                "horse": h["horse"],
                "final_score": round(h["final_score"], 2),
                "trust_score": round(h["trust_score"], 1),
                "trust_label": h["trust_label"],
                "darkhorse_score": h["darkhorse_score"],
                "comment_final": h["comment_final"],
                "basis_final": h["basis_final"],
                "comment_trust": h["comment_trust"],
                "basis_trust": h["basis_trust"],
                "comment_dark": h["comment_dark"],
                "basis_dark": h["basis_dark"],
            }
        )

    return pd.DataFrame(rows)


# ====================================
# 5. 실행 예시
# ====================================

if __name__ == "__main__":
    rcity = "서울"
    rdate = "20251213"
    rno = 6

    horses = load_race(rcity, rdate, rno)
    if not horses:
        print("데이터 없음")
    else:
        df = listup_scores(horses)

        # 요약 테이블: 핵심 지표만 정렬 출력
        summary_cols = [
            "gate",
            "horse",
            "final_score",
            "trust_score",
            "trust_label",
            "darkhorse_score",
        ]
        exist_cols = [c for c in summary_cols if c in df.columns]
        df_summary = df[exist_cols].copy()

        # 요약 표에 복병 코멘트 컬럼 추가
        # horses(list of dict)에서 초반/종반/기록 편차를 조회하여 간단 코멘트 생성
        try:
            by_key = {(h.get("gate"), h.get("horse")): h for h in horses}

            def _dark_comment(row):
                key = (row.get("gate"), row.get("horse")) if isinstance(row, dict) else (row["gate"], row["horse"])
                h = by_key.get(key)
                if not h:
                    # fallback: darkhorse_score만으로 간단 표기
                    ds = float(row.get("darkhorse_score", 0.0)) if isinstance(row, dict) else float(row["darkhorse_score"]) if "darkhorse_score" in row else 0.0
                    return "복병주의" if ds >= 7 else ""

                s1 = float(h.get("dark_s1f_diff") or 0.0)
                g3 = float(h.get("dark_g3f_diff") or 0.0)
                rd = h.get("dark_rec_diff")
                ds = float(h.get("darkhorse_score") or 0.0)

                if s1 >= 8 and g3 >= 10:
                    return "균형좋음 급부상 여지"
                if s1 >= 12 and g3 < 5:
                    return "선행이변, 종반리스크"
                if -3 <= s1 <= 3 and g3 >= 15:
                    return "종반한발, 빠른페이스노림"
                if g3 >= 12:
                    return "종반양호 변수"
                if rd is not None and rd <= -10:
                    return "기록낮음·스타일강점"
                if ds >= 7:
                    return "복병주의"
                return ""

            df_summary["복병코멘트"] = [
                _dark_comment(row._asdict() if hasattr(row, "_asdict") else row)
                for _, row in df.iterrows()
            ][: len(df_summary)]
        except Exception:
            # 문제 발생 시 컬럼만 생성
            df_summary["복병코멘트"] = ""
        if "final_score" in df_summary:
            df_summary["final_score"] = df_summary["final_score"].astype(float).round(2)
        if "trust_score" in df_summary:
            df_summary["trust_score"] = df_summary["trust_score"].astype(float).round(1)
        if "darkhorse_score" in df_summary:
            df_summary["darkhorse_score"] = (
                df_summary["darkhorse_score"].astype(float).round(2)
            )

        # 보기 좋게 넓은 텍스트 컬럼 줄바꿈 방지
        pd.set_option("display.max_colwidth", 120)
        summary_text = df_summary.to_string(index=False)

        # 상세 섹션: 말별 코멘트/근거를 짧은 라인으로 구성
        detail_lines = []
        for _, row in df.iterrows():
            head = (
                f"게이트 {row['gate']:>2} | {row['horse']} | "
                f"final {row['final_score']:.2f}, "
                f"trust {row['trust_score']:.1f}({row['trust_label']}), "
                f"dark {row['darkhorse_score']:.2f}"
            )
            detail_lines.append(head)
            if "comment_final" in row:
                detail_lines.append(f"  · 코멘트(final): {row['comment_final']}")
            if "comment_trust" in row:
                detail_lines.append(f"  · 코멘트(trust): {row['comment_trust']}")
            if "comment_dark" in row:
                detail_lines.append(f"  · 코멘트(dark): {row['comment_dark']}")
            if "basis_final" in row:
                detail_lines.append(f"  · 근거(final): {row['basis_final']}")
            if "basis_trust" in row:
                detail_lines.append(f"  · 근거(trust): {row['basis_trust']}")
            if "basis_dark" in row:
                detail_lines.append(f"  · 근거(dark): {row['basis_dark']}")
            detail_lines.append("")  # 말 간 구분 공백

        # 파일 헤더(타이틀 문구 제거, 메타만 유지)
        meta_header = (
            f"- 경마장: {rcity}  날짜: {rdate}  경주: R{rno}\n"
            f"- 총 출주두수: {len(df)}\n"
            + ("-" * 80)
        )

        # =========================
        # 총평 섹션 생성 (경주 전개 요약)
        # - listup_scores 호출로 horses 원본 dict에 지표가 주입되어 있음
        # =========================
        def _build_overview(horses_list, df_table):
            # 상위 3두 (final_score 기준)
            top_df = df_table.sort_values("final_score", ascending=False).head(3)
            # gate+horse로 매칭하여 s1f/g3f 편차 사용
            by_key = {(h.get("gate"), h.get("horse")): h for h in horses_list}

            def _get_h(row):
                return by_key.get((row.get("gate"), row.get("horse")))

            top_h = []
            for _, r in top_df.iterrows():
                h = _get_h(r)
                if not h:
                    # 최소한 df 정보로 구성
                    h = {
                        "gate": r.get("gate"),
                        "horse": r.get("horse"),
                        "final_score": r.get("final_score", 0.0),
                        "trust_score": r.get("trust_score", 0.0),
                        "trust_label": r.get("trust_label", ""),
                        "dark_s1f_diff": 0.0,
                        "dark_g3f_diff": 0.0,
                        "darkhorse_score": r.get("darkhorse_score", 0.0),
                    }
                top_h.append(h)

            # 평균 초반/종반 편차
            def _avg(lst):
                lst = [x for x in lst if x is not None]
                return round(sum(lst) / len(lst), 1) if lst else 0.0

            mean_s1f = _avg([h.get("dark_s1f_diff") for h in top_h])
            mean_g3f = _avg([h.get("dark_g3f_diff") for h in top_h])

            # 전체 빠른 초반/강한 종반 개수
            fast_early = sum(1 for h in horses_list if (h.get("dark_s1f_diff") or 0) >= 8)
            strong_closer = sum(1 for h in horses_list if (h.get("dark_g3f_diff") or 0) >= 15)

            # 라벨 분포
            from collections import Counter

            labels = Counter(df_table.get("trust_label", []))

            # 페이스 규칙
            if mean_s1f >= 8 and fast_early >= 3:
                pace = "초반 경합이 강할 가능성(빠른 페이스)"
            elif mean_s1f <= 0 and strong_closer >= 3:
                pace = "초반이 느리고 종반 탄력 승부(느린 페이스)"
            else:
                pace = "평균 페이스 예상, 전개 따라 혼전"

            def _fmt(h):
                final_v = h.get("final_score") if h.get("final_score") is not None else h.get("final")
                label_v = h.get("trust_label") or h.get("label") or ""
                return f"{h.get('horse')}(게이트 {h.get('gate')}, final {float(final_v):.2f}, {label_v})"

            top_line = ", ".join(_fmt(h) for h in top_h)

            risks = []
            if labels.get("위험축", 0) >= 5:
                risks.append(f"위험축 다수({labels.get('위험축', 0)}두)로 변동성 주의")
            if top_h:
                ts = top_h[0].get("trust_score") or top_h[0].get("trust") or 0.0
                if ts < 60:
                    risks.append(f"최상위 {top_h[0].get('horse')} 신뢰도 {float(ts):.1f}로 낮음")
            if len(top_h) > 1:
                ts2 = top_h[1].get("trust_score") or top_h[1].get("trust") or 0.0
                if ts2 < 60:
                    risks.append(f"상위권 {top_h[1].get('horse')} 신뢰도 {float(ts2):.1f}로 낮음")

            risk_line = "; ".join(risks) if risks else "특이 리스크 두드러지지 않음"

            if fast_early >= 3:
                scenario = "초반 경합 후 직선 종반 탄력 싸움. 선행 과열 시 추입 약진."
            else:
                scenario = "평균 페이스에서 선입/추입 혼전. 전개 따른 변동성."

            # 상위 6두 입상가능성 평가
            top6_df = df_table.sort_values("final_score", ascending=False).head(6)
            top6 = []
            for _, r in top6_df.iterrows():
                h = _get_h(r) or {
                    "gate": r.get("gate"),
                    "horse": r.get("horse"),
                    "final_score": r.get("final_score", 0.0),
                    "trust_score": r.get("trust_score", 0.0),
                    "trust_label": r.get("trust_label", ""),
                    "darkhorse_score": r.get("darkhorse_score", 0.0),
                    "dark_s1f_diff": 0.0,
                    "dark_g3f_diff": 0.0,
                }
                top6.append(h)

            def _rate(final_v: float, trust_v: float) -> str:
                # 휴리스틱 등급
                if final_v >= 78 or (final_v >= 72 and trust_v >= 65):
                    return "입상유력"
                if final_v >= 65 or trust_v >= 60:
                    return "입상권"
                if final_v >= 58 or trust_v >= 50:
                    return "가능"
                return "변수"

            top6_lines = ["- 상위6 입상가능성:"]
            for h in top6:
                fv = float(h.get("final_score", 0.0))
                tv = float(h.get("trust_score", 0.0))
                tl = h.get("trust_label", "")
                s1 = h.get("dark_s1f_diff")
                g3 = h.get("dark_g3f_diff")
                grade = _rate(fv, tv)
                top6_lines.append(
                    f"  · {h.get('horse')}({h.get('gate')}) : {grade} / final {fv:.2f}, trust {tv:.1f}({tl}), 초반 {s1:+.1f}, 종반 {g3:+.1f}"
                )

            # 복병마 후보: 상위6 외에서 darkhorse_score 높은 말 위주
            by_key_all = {(h.get("gate"), h.get("horse")): h for h in horses_list}
            top6_keys = {(h.get("gate"), h.get("horse")) for h in top6}
            dark_pool = []
            for _, r in df_table.iterrows():
                key = (r.get("gate"), r.get("horse"))
                if key in top6_keys:
                    continue
                h = by_key_all.get(key)
                if not h:
                    continue
                dark_score = float(h.get("darkhorse_score") or r.get("darkhorse_score") or 0.0)
                dark_pool.append((dark_score, h))
            dark_pool.sort(key=lambda x: x[0], reverse=True)
            dark_lines = []
            # 우선 점수 ≥7을 우선 선정, 없으면 상위 1~2두
            selected = [h for s, h in dark_pool if s >= 7][:2]
            if not selected:
                selected = [h for _, h in dark_pool[:2]]
            if selected:
                dark_lines.append("- 복병마:")
                for h in selected:
                    ds = float(h.get("darkhorse_score") or 0.0)
                    s1 = float(h.get("dark_s1f_diff") or 0.0)
                    g3 = float(h.get("dark_g3f_diff") or 0.0)
                    rd = h.get("dark_rec_diff")
                    reason = f"초반 {s1:+.1f}, 종반 {g3:+.1f}"
                    if rd is not None and rd < 0:
                        reason += f", 기록 {float(rd):+.1f} (낮음)"

                    # 선정 코멘트 규칙
                    sel_comment = []
                    if s1 >= 8 and g3 >= 10:
                        sel_comment.append("초·종반 균형 좋아 전개 유리시 급부상 가능")
                    elif s1 >= 12 and g3 < 5:
                        sel_comment.append("선행 성공 시 이변 가능하나 종반 리스크")
                    elif -3 <= s1 <= 3 and g3 >= 15:
                        sel_comment.append("종반 한발 뚜렷, 빠른 페이스 시 노림수")
                    elif g3 >= 12:
                        sel_comment.append("종반 탄력 양호, 막판 역전 변수")
                    if rd is not None and rd <= -10:
                        sel_comment.append("기록은 낮으나 스타일 강점으로 복병가치")
                    if not sel_comment:
                        sel_comment.append("전개 변수 따라 입상 여지")

                    dark_lines.append(
                        f"  · {h.get('horse')}({h.get('gate')}) : 복병지수 {ds:.2f} / {reason}"
                    )
                    dark_lines.append(
                        f"    ⤷ 선정 코멘트: {'; '.join(sel_comment)}"
                    )

            lines = [
                "- 페이스: " + pace,
                "- 상위 경쟁 축: " + top_line,
                "- 변수/리스크: " + risk_line,
                "- 전개: " + scenario,
                "- 베팅 전략: 종반 지표 우수마 중심 복·삼복식 조합, 분산 운영 권장",
            ] + top6_lines + (dark_lines if dark_lines else [])
            return lines

        overview_lines = _build_overview(horses, df)

        final_text = (
            meta_header
            + "\n[요약] 핵심 지표\n"
            + summary_text
            + "\n\n"
            + "-" * 80
            + "\n[상세] 코멘트/근거\n"
            + "\n".join(detail_lines)
            + "\n"
            + "-" * 80
            + "\n[총평]\n"
            + "\n".join(overview_lines)
        )

        # 스크립트 위치 기준으로 파일 저장
        script_dir = os.path.dirname(__file__)
        filename = f"베팅가이드_점수화_{rcity}_{rdate}_R{rno}.txt"
        out_path = os.path.join(script_dir, filename)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(final_text)

        # 터미널에도 보기 좋게 표시: 요약 테이블 + 상위 3두 상세 미리보기
        # 파일에는 메타 헤더만 기록하고, 터미널에는 별도 헤더 문구를 출력하지 않음
        print("\n[요약] 핵심 지표")
        print(summary_text)
        print("\n[상세] 코멘트/근거 (상위 3두)")
        preview = "\n".join(detail_lines[: min(len(detail_lines), 4 * 3)])
        print(preview)
        print("\n[총평]")
        print("\n".join(overview_lines[:12]))
        print(f"\n저장 완료: {out_path} (행 수: {len(df)})")
