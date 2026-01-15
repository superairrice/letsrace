#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import argparse
from contextlib import closing
from typing import Any, Dict, List, Optional, Tuple

import pymysql
import pandas as pd


# =========================
# 0) DB
# =========================
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


# =========================
# 1) g2f_rank 정밀 파싱 (최근8 G3F/S1F)
# =========================
_ELLIPSIS = r"(?:\.\.\.|…)"
_G3F_RE = re.compile(
    rf"(?:{_ELLIPSIS}\s*)?G3F(?:\s*{_ELLIPSIS})?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE
)
_S1F_RE = re.compile(
    rf"(?:{_ELLIPSIS}\s*)?S1F(?:\s*{_ELLIPSIS})?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE
)

_NO_LABEL_PAIR_RE = re.compile(
    rf"{_ELLIPSIS}\s*([A-Za-z]?\d+|국\d+|혼\d+|G\d+)\s*{_ELLIPSIS}\s*"
    rf"([0-9]+(?:\.[0-9]+)?)\s*{_ELLIPSIS}\s*"
    rf"([0-9]+(?:\.[0-9]+)?)\s*{_ELLIPSIS}\s*"
    rf"(?:[0-9]+:[0-9]+\.[0-9]+)",
    re.IGNORECASE,
)


def _parse_line_s1f_g3f(line: str) -> Tuple[Optional[float], Optional[float]]:
    s = line.replace("…", "...")
    ms = _S1F_RE.search(s)
    mg = _G3F_RE.search(s)
    if ms or mg:
        s1f = float(ms.group(1)) if ms else None
        g3f = float(mg.group(1)) if mg else None
        return s1f, g3f

    m2 = _NO_LABEL_PAIR_RE.search(s)
    if m2:
        try:
            return float(m2.group(2)), float(m2.group(3))
        except Exception:
            return None, None
    return None, None


def parse_recent8_seconds(
    text: Optional[str], kind: str = "G3F", limit: int = 8
) -> List[float]:
    if not text:
        return []
    out: List[float] = []
    k = kind.upper()

    for line in str(text).splitlines():
        s1f, g3f = _parse_line_s1f_g3f(line)
        v = g3f if k == "G3F" else s1f
        if v is not None:
            out.append(float(v))
        if len(out) >= limit:
            break
    return out


def g3f_improve_sec(
    g2f_rank_text: Optional[str],
) -> Tuple[float, Optional[float], Optional[float], int]:
    g3fs = parse_recent8_seconds(g2f_rank_text, kind="G3F", limit=8)
    n = len(g3fs)
    if n < 2:
        return 0.0, None, (g3fs[0] if n == 1 else None), n
    recent = g3fs[0]
    prev = g3fs[1]
    return float(prev - recent), prev, recent, n


# =========================
# 2) 스타일 분류
# =========================
def infer_style(s1f_per: float) -> str:
    if s1f_per >= 80:
        return "FRONT"
    if s1f_per <= 30:
        return "CLOSER"
    return "MID"


# =========================
# 3) 축 강도(5단계) / 복병 강도(3단계)
# =========================
def anchor_strength_5(anchor_score: float) -> str:
    if anchor_score >= 75:
        return "S(최강)"
    if anchor_score >= 65:
        return "A(강)"
    if anchor_score >= 55:
        return "B(보통)"
    if anchor_score >= 45:
        return "C(약)"
    return "D(불안)"


def dark_strength_3(dark_score: float) -> str:
    if dark_score >= 6.0:
        return "강"
    if dark_score >= 3.0:
        return "중"
    return "약"


# =========================
# 4) trust_score / label
# =========================
def trust_label_from_score(x: float) -> str:
    if x >= 75:
        return "강축"
    if x >= 60:
        return "보통축"
    if x >= 45:
        return "약한축"
    return "위험축"


def calc_anchor_score(
    final_score: float,
    trust_score: float,
    rec_cv: float,
    trend_bonus: float,
    low_race_penalty: float,
) -> float:
    base = 0.55 * final_score + 0.45 * trust_score
    stability_pen = min(20.0, rec_cv * 400.0)
    return float(max(0.0, base + trend_bonus - stability_pen - low_race_penalty))


# =========================
# 5) 복병 점수
# =========================
def calc_dark_score(
    style: str,
    s1f: float,
    prev_dist: Optional[int],
    cur_dist: int,
    g3f_delta_sec: float,
    g3f_n: int,
) -> float:
    prev_dist = (
        int(prev_dist) if prev_dist is not None and pd.notna(prev_dist) else None
    )
    dist_diff = (cur_dist - prev_dist) if prev_dist is not None else 0

    score = 0.0

    # 거리/스타일 시너지
    if style == "FRONT":
        score += 3.5 if dist_diff < 0 else (0.8 if dist_diff > 0 else 0.8)
    elif style == "CLOSER":
        score += 3.5 if dist_diff > 0 else (0.8 if dist_diff < 0 else 0.8)
    else:
        score += 1.2 if dist_diff != 0 else 0.4

    # 초반 스피드
    if s1f >= 85:
        score += 1.5
    elif s1f >= 70:
        score += 1.0
    elif s1f <= 20:
        score -= 0.5

    # 종반(최근 vs 직전) 개선
    if g3f_n >= 2:
        if g3f_delta_sec > 0:
            score += min(6.0, g3f_delta_sec * 2.4)
        elif g3f_delta_sec < 0:
            score += max(-2.0, g3f_delta_sec * 1.2)

    # 표본 페널티
    if g3f_n <= 1:
        score -= 0.2
    elif g3f_n == 2:
        score -= 0.1

    return float(round(score, 2))


# =========================
# 6) 최근 폼/출주수 가감점
# =========================
def trend_bonus_from_rec8(rec8: float) -> float:
    if rec8 >= 65:
        return 3.0
    if rec8 >= 55:
        return 1.5
    if rec8 <= 40:
        return -1.5
    return 0.0


def low_race_penalty(year_race: int) -> float:
    return 6.0 if int(year_race) <= 2 else 0.0


# =========================
# 7) 로드
# =========================
def load_race(rcity: str, rdate: str, rno: int) -> pd.DataFrame:
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
                SELECT max(rdate)
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
    ORDER BY e.m_rank ASC
    """
    with closing(get_conn()) as conn, conn.cursor() as cur:
        cur.execute(sql, (rdate, rcity, rdate, rno))
        rows = cur.fetchall()

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("데이터가 없습니다. rcity/rdate/rno 확인")

    df["경주거리"] = (
        pd.to_numeric(df["경주거리"], errors="coerce").fillna(0).astype(int)
    )
    df["직전경주거리"] = pd.to_numeric(df["직전경주거리"], errors="coerce")
    df["gate"] = pd.to_numeric(df["gate"], errors="coerce").fillna(0).astype(int)
    df["m_rank"] = pd.to_numeric(df["m_rank"], errors="coerce").fillna(99).astype(int)

    for c in ["초반200", "종반600", "종반200", "기록점수", "최근8", "연대"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["출주수"] = pd.to_numeric(df["출주수"], errors="coerce").fillna(0).astype(int)

    return df


# =========================
# 8) 주도권(선행경합/단독선행)
# =========================
def leadership_text(df: pd.DataFrame) -> str:
    d = df.copy()
    d["lead_candidate"] = (d["style"] == "FRONT") | (
        (d["style"] == "MID") & (d["초반200"] >= 75)
    )
    cand = d[d["lead_candidate"]].copy()

    if cand.empty:
        return (
            "주도권: 선행 주도 말이 뚜렷하지 않아 중위권 주도(자리싸움/선입 혼전) 가능."
        )

    def gate_bonus(g: int) -> float:
        if g <= 4:
            return 1.2
        if g <= 8:
            return 0.6
        return 0.0

    cand["gate_bonus"] = cand["gate"].astype(int).apply(gate_bonus)
    cand["lead_score"] = (cand["초반200"] * 0.90 + cand["gate_bonus"] * 10.0).round(2)
    cand = cand.sort_values("lead_score", ascending=False).reset_index(drop=True)

    top = cand.iloc[0]
    top2 = cand.iloc[1] if len(cand) >= 2 else None
    if top2 is None:
        return f"주도권: 단독선행 가능 — {top['horse']}({int(top['gate'])}) 초반 우세."

    gap = float(top["lead_score"] - top2["lead_score"])

    if gap <= 4.0 and len(cand) >= 2:
        names = ", ".join(
            [f"{r['horse']}({int(r['gate'])})" for _, r in cand.head(3).iterrows()]
        )
        return f"주도권: 선행경합 가능성↑ (후보: {names})."

    if gap >= 6.0 and len(cand) <= 2:
        return f"주도권: 단독선행 가능 — {top['horse']}({int(top['gate'])}) 초반 우세."

    return f"주도권: {top['horse']}({int(top['gate'])}) 선행 유력, 2선 견제/가세 변수."


# =========================
# 9) 총평(컴팩트) 생성
# =========================
def make_compact_overview(
    pace: str,
    lead_line: str,
    anchor_row: Optional[pd.Series],
    dark_row: Optional[pd.Series],
) -> List[str]:
    lines: List[str] = []

    if anchor_row is not None:
        lines.append(
            f"핵심 축: {anchor_row['horse']}({int(anchor_row['gate'])}) "
            f"/ trust {anchor_row['trust_score']:.1f}({anchor_row['trust_label']}), "
            f"anchor {anchor_row['anchor_score']:.2f}({anchor_row['축강도(5)']})"
        )
    else:
        lines.append("- 핵심 축: (m_rank 1~4 부족)")

    # 총평용 복병: m_rank>=5 & dh>=3.0일 때만 언급
    if dark_row is not None and float(dark_row["복병점수"]) >= 3.0:
        style = str(dark_row["style"])
        if style == "CLOSER":
            cond = "선행경합/페이스 붕괴 시"
        elif style == "FRONT":
            cond = "단독선행/무리없는 전개 시"
        else:
            cond = "중위권 자리 선점 시"

        lines.append(
            f"복병 포인트: {dark_row['horse']}({int(dark_row['gate'])}) "
            f"/ dh {dark_row['복병점수']:.2f}({dark_row['복병강도(3)']}), {cond}"
        )
    else:
        lines.append("- 복병 포인트: 뚜렷한 복병 우위는 제한적")

    if dark_row is not None and float(dark_row["복병점수"]) >= 6.0:
        outlook = "이변 여지↑ (복병 강도 높음)"
    elif anchor_row is not None and str(anchor_row["trust_label"]) in (
        "강축",
        "보통축",
    ):
        outlook = "축 중심 구도"
    else:
        outlook = "혼전/변수 구도"

        lines.append(f"페이스: {pace}")
    lines.append(f"{lead_line}")

    lines.append(f"구도 요약: {outlook}")
    return lines


# =========================
# 10) 리포트 빌드
# =========================
def build_report(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str], Dict[str, Any]]:
    cur_dist = int(df["경주거리"].iloc[0])

    deltas, prevs, recents, ns = [], [], [], []
    for txt in df["g2f_rank"].tolist():
        d, p, r, n = g3f_improve_sec(txt)
        deltas.append(d)
        prevs.append(p)
        recents.append(r)
        ns.append(n)

    df["Δ종반600"] = deltas
    df["g3f_prev"] = prevs
    df["g3f_recent"] = recents
    df["g3f_n"] = ns

    df["style"] = df["초반200"].apply(infer_style)
    df["rec_cv"] = 0.0  # 현재 미사용

    # final_score / trust_score (기본값)
    if "final_score" not in df.columns:
        df["final_score"] = (
            0.35 * df["기록점수"]
            + 0.25 * df["종반600"]
            + 0.20 * df["최근8"]
            + 0.20 * df["연대"]
        ).round(2)

    if "trust_score" not in df.columns:
        df["trust_score"] = df["기록점수"].copy()

    df["trust_label"] = df["trust_score"].apply(trust_label_from_score)

    df["trend_bonus"] = df["최근8"].apply(trend_bonus_from_rec8)
    df["low_race_penalty"] = df["출주수"].apply(low_race_penalty)

    df["anchor_score"] = df.apply(
        lambda r: calc_anchor_score(
            final_score=float(r["final_score"]),
            trust_score=float(r["trust_score"]),
            rec_cv=float(r["rec_cv"]),
            trend_bonus=float(r["trend_bonus"]),
            low_race_penalty=float(r["low_race_penalty"]),
        ),
        axis=1,
    ).round(2)

    df["복병점수"] = df.apply(
        lambda r: calc_dark_score(
            style=str(r["style"]),
            s1f=float(r["초반200"]),
            prev_dist=r["직전경주거리"],
            cur_dist=cur_dist,
            g3f_delta_sec=float(r["Δ종반600"]),
            g3f_n=int(r["g3f_n"]),
        ),
        axis=1,
    )

    df["축강도(5)"] = df["anchor_score"].apply(anchor_strength_5)
    df["복병강도(3)"] = df["복병점수"].apply(dark_strength_3)

    def make_anchor_comment(r) -> str:
        parts = [
            f"{r['trust_label']}({r['trust_score']:.1f})",
            f"강도 {r['축강도(5)']}",
        ]
        if float(r["trend_bonus"]) > 0:
            parts.append("폼UP")
        if float(r["low_race_penalty"]) > 0:
            parts.append("WARN 출주수<=2")
        if float(r["rec_cv"]) > 0:
            parts.append(f"변동성 CV {float(r['rec_cv']):.3f}")
        return " / ".join(parts)

    def make_dark_comment(r) -> str:
        prevd = r["직전경주거리"]
        curd = int(r["경주거리"])

        if pd.notna(prevd):
            prevd_i = int(prevd)
            if prevd_i != curd:
                dist_txt = (
                    f"거리{'단축' if prevd_i > curd else '증가'} {prevd_i}->{curd}"
                )
            else:
                dist_txt = f"거리유지 {curd}"
        else:
            dist_txt = f"직전없음/이번 {curd}"

        n = int(r["g3f_n"])
        if n >= 2 and r["g3f_prev"] is not None and r["g3f_recent"] is not None:
            g3 = float(r["Δ종반600"])
            g3txt = (
                f"종반600 {float(r['g3f_prev']):.2f}->{float(r['g3f_recent']):.2f}"
                f"(Δ{g3:+.2f}s,n={n})"
            )
        elif n == 1 and r["g3f_recent"] is not None:
            g3txt = f"종반600 {float(r['g3f_recent']):.2f}s(n=1)"
        else:
            g3txt = "종반600 데이터부족(n=0)"

        warn = " / WARN 표본부족" if n <= 1 else ""
        return (
            f"{r['style']} | {dist_txt} | S1F {r['초반200']:.1f} | "
            f"강도 {r['복병강도(3)']} | {g3txt}{warn}"
        )

    df["축마코멘트"] = df.apply(make_anchor_comment, axis=1)
    df["복병코멘트"] = df.apply(make_dark_comment, axis=1)
    df["표시코멘트"] = df.apply(
        lambda r: r["축마코멘트"] if int(r["m_rank"]) <= 4 else r["복병코멘트"],
        axis=1,
    )

    df_sorted = df.sort_values(["final_score"], ascending=False).reset_index(drop=True)
    df_sorted["f_rank"] = df_sorted.index + 1

    anchor_df = (
        df_sorted[df_sorted["m_rank"].between(1, 4)]
        .copy()
        .sort_values(["anchor_score", "final_score"], ascending=[False, False])
    )

    dark_df = (
        df_sorted[df_sorted["m_rank"] >= 5]
        .copy()
        .sort_values(["복병점수", "final_score"], ascending=[False, False])
        .head(3)
    )

    styles = df_sorted["style"].value_counts().to_dict()
    n_front = styles.get("FRONT", 0)
    n_closer = styles.get("CLOSER", 0)
    n_mid = styles.get("MID", 0)

    if n_front >= 3:
        pace = "빠른 페이스(선행 다수)"
    elif n_front == 2:
        pace = "중~빠른 페이스"
    elif n_front == 1 and n_closer >= 3:
        pace = "중~느린 페이스(추입 유리 가능)"
    else:
        pace = "보통 페이스"

    lead_line = leadership_text(df_sorted)

    anchor_row = anchor_df.iloc[0] if not anchor_df.empty else None
    dark_row = dark_df.iloc[0] if not dark_df.empty else None

    compact_overview = make_compact_overview(
        pace=pace, lead_line=lead_line, anchor_row=anchor_row, dark_row=dark_row
    )
    total_summary = [f"· {x}" for x in compact_overview]

    return (
        df_sorted,
        anchor_df,
        dark_df,
        total_summary,
        {
            "pace": pace,
            "styles": styles,
            "n_front": n_front,
            "n_mid": n_mid,
            "n_closer": n_closer,
        },
    )


# =========================
# 11) 출력
# =========================
def print_report(
    df: pd.DataFrame,
    anchor_df: pd.DataFrame,
    dark_df: pd.DataFrame,
    total_summary: List[str],
):
    rcity = df["rcity"].iloc[0]
    rdate = df["rdate"].iloc[0]
    rno = int(df["rno"].iloc[0])
    dist = int(df["경주거리"].iloc[0])

    cols = [
        "gate",
        "horse",
        "m_rank",
        "final_score",
        "trust_score",
        "trust_label",
        "anchor_score",
        "축강도(5)",
        "style",
        "직전경주거리",
        "경주거리",
        "Δ종반600",
        "복병점수",
        "복병강도(3)",
        "표시코멘트",
    ]
    out = df[cols].copy()
    out.rename(columns={"직전경주거리": "직전", "경주거리": "이번"}, inplace=True)

    print(f"\n[요약] 핵심 지표 — {rcity} {rdate} R{rno} ({dist}m)")
    print(out.to_string(index=False))

    print("\n[축마감 랭킹] (m_rank 1~4만)")
    if anchor_df.empty:
        print("- (없음)")
    else:
        acols = [
            "gate",
            "horse",
            "m_rank",
            "final_score",
            "trust_score",
            "trust_label",
            "anchor_score",
            "축강도(5)",
            "축마코멘트",
        ]
        print(anchor_df[acols].to_string(index=False))

    print("\n[복병 TOP3] (m_rank 5+만)")
    if dark_df.empty:
        print("- (없음)")
    else:
        for _, r in dark_df.iterrows():
            print(
                f"{r['horse']}({int(r['gate'])}) : score {r['복병점수']:.2f}({r['복병강도(3)']}) / {r['복병코멘트']}"
            )

    print("\n[경주 총평] (컴팩트)")
    for line in total_summary:
        print(line)


# =========================
# 12) exp011 score columns ensure
# =========================
def ensure_exp011_score_columns():
    alters = [
        "ALTER TABLE The1.exp011 ADD COLUMN f_rank INT NULL",
        "ALTER TABLE The1.exp011 ADD COLUMN f_score DOUBLE NULL",
        "ALTER TABLE The1.exp011 ADD COLUMN trust_score DOUBLE NULL",
        "ALTER TABLE The1.exp011 ADD COLUMN trust_label VARCHAR(20) NULL",
        "ALTER TABLE The1.exp011 ADD COLUMN dh_score DOUBLE NULL",
        "ALTER TABLE The1.exp011 ADD COLUMN comment_dh TEXT NULL",
    ]
    with closing(get_conn()) as c:
        with c.cursor() as cur:
            for sql in alters:
                try:
                    cur.execute(sql)
                except Exception:
                    pass
        c.commit()


# =========================
# 12-2) exp010 r_overview 컬럼 보장
# =========================
def ensure_exp010_overview_column():
    alters = [
        "ALTER TABLE The1.exp010 ADD COLUMN r_overview TEXT NULL",
    ]
    with closing(get_conn()) as c:
        with c.cursor() as cur:
            for sql in alters:
                try:
                    cur.execute(sql)
                except Exception:
                    pass
        c.commit()


# =========================
# 12-3) exp010 r_overview 업데이트
# =========================
def update_exp010_overview_for_race(
    rcity: str,
    rdate: str,
    rno: int,
    overview_lines: List[str],
    ensure_column: bool = True,
    verbose: bool = False,
) -> int:
    if ensure_column:
        try:
            ensure_exp010_overview_column()
        except Exception:
            pass

    def sanitize_mysql_text(s: str) -> str:
        if s is None:
            return ""
        s = s.replace("—", "-").replace("–", "-")
        s = s.replace("…", "...")
        s = s.replace("·", "-")
        s = s.replace("↑", "UP").replace("↓", "DN")
        s = s.replace("⚠", "WARN")
        s = re.sub(r"[\U00010000-\U0010FFFF]", "", s)  # 4바이트 제거
        return s

    overview_text = sanitize_mysql_text("\n".join(overview_lines).strip())

    sql = """
        UPDATE The1.exp010
           SET r_overview = %s
         WHERE rcity = %s
           AND rdate = %s
           AND rno   = %s
    """
    with closing(get_conn()) as c:
        with c.cursor() as cur:
            cur.execute(sql, (overview_text, rcity, rdate, int(rno)))
            affected = cur.rowcount
        c.commit()

    if verbose:
        preview = overview_text.replace("\n", " / ")[:180]
        print(
            f"[exp010] {rcity} {rdate} R{rno} : overview rowcount={affected} / preview={preview}"
        )

    return int(affected)


# =========================
# 13) score 계산(단일 경주)
# =========================
def compute_scores_for_race(
    rcity: str, rdate: str, rno: int
) -> Tuple[pd.DataFrame, List[str]]:
    df = load_race(rcity, rdate, rno)
    df2, _, _, total_summary, _ = build_report(df)

    df2 = df2.sort_values("final_score", ascending=False).reset_index(drop=True)
    df2["f_rank"] = df2.index + 1
    df2["comment_dh"] = df2["표시코멘트"].astype(str)

    return df2, total_summary


# =========================
# 14) exp011만 업데이트(내부용)
# =========================
def update_exp011_table_for_race(
    rcity: str,
    rdate: str,
    rno: int,
    df_scores: Optional[pd.DataFrame] = None,
    ensure_columns: bool = True,
    verbose: bool = False,
) -> int:
    if ensure_columns:
        try:
            ensure_exp011_score_columns()
        except Exception:
            pass

    if df_scores is None:
        df_scores, _ = compute_scores_for_race(rcity, rdate, rno)
    if df_scores is None or df_scores.empty:
        return 0

    params: List[Tuple] = []
    for _, row in df_scores.iterrows():
        params.append(
            (
                int(row["f_rank"]),
                float(row["final_score"]),  # f_score
                float(row["trust_score"]),
                str(row["trust_label"]),
                float(row["복병점수"]),  # dh_score
                str(row.get("comment_dh", "")),  # comment_dh
                rcity,
                rdate,
                int(rno),
                int(row["gate"]),
            )
        )

    if verbose and params:
        print(f"[debug] where=({rcity},{rdate},R{rno}) / rows={len(params)}")

    sql = """
        UPDATE The1.exp011
           SET f_rank = %s,
               f_score = %s,
               trust_score = %s,
               trust_label = %s,
               dh_score = %s,
               comment_dh = %s
         WHERE rcity = %s
           AND rdate = %s
           AND rno   = %s
           AND gate  = %s
    """

    with closing(get_conn()) as c:
        with c.cursor() as cur:
            cur.executemany(sql, params)
            affected = cur.rowcount
        c.commit()

    if verbose:
        print(
            f"[exp011] {rcity} {rdate} R{rno} : 요청 {len(params)}행 / rowcount={affected}"
        )

    return len(params)


# =========================
# 15) exp010+exp011 같이 업데이트(외부 엔트리)
# =========================
def update_exp011_for_race(
    rcity: str, rdate: str, rno: int, verbose: bool = True
) -> Dict[str, int]:
    """
    ✅ 이 함수만 호출하면 exp011 + exp010(r_overview) 같이 업데이트
    """
    ensure_exp011_score_columns()
    ensure_exp010_overview_column()

    df_scores, total_summary = compute_scores_for_race(rcity, rdate, rno)

    exp011_rows = update_exp011_table_for_race(
        rcity,
        rdate,
        rno,
        df_scores=df_scores,
        ensure_columns=False,
        verbose=verbose,
    )

    exp010_rows = update_exp010_overview_for_race(
        rcity,
        rdate,
        rno,
        total_summary,
        ensure_column=False,
        verbose=verbose,
    )

    if verbose:
        print(
            f"[done] {rcity} {rdate} R{rno} -> exp011={exp011_rows} rows, exp010={exp010_rows} rows"
        )

    return {"exp011_rows": int(exp011_rows), "exp010_rows": int(exp010_rows)}


# =========================
# 16) 기간 업데이트
# =========================
def get_races_in_period(
    from_date: str, to_date: str, rcity: Optional[str] = None
) -> List[Tuple[str, str, int]]:
    cond = " WHERE rdate BETWEEN %s AND %s"
    params: List[Any] = [from_date, to_date]
    if rcity:
        cond += " AND rcity = %s"
        params.append(rcity)

    sql = f"""
        SELECT rcity, rdate, rno
          FROM The1.exp010
        {cond}
         ORDER BY rcity, rdate, rno
    """
    with closing(get_conn()) as c:
        with c.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [(row["rcity"], row["rdate"], int(row["rno"])) for row in rows]


def update_exp011_for_period(
    from_date: str, to_date: str, rcity: Optional[str] = None, verbose: bool = True
) -> int:
    try:
        ensure_exp011_score_columns()
    except Exception:
        pass
    try:
        ensure_exp010_overview_column()
    except Exception:
        pass

    races = get_races_in_period(from_date, to_date, rcity)
    if not races:
        if verbose:
            print(f"[{from_date}~{to_date}] 처리할 경주가 없습니다.")
        return 0

    updated = 0
    for rc, rd, rn in races:
        try:
            res = update_exp011_for_race(rc, rd, rn, verbose=verbose)
            if res["exp011_rows"] > 0:
                updated += 1
                if verbose:
                    print(
                        f"  - 업데이트 완료: {rc} {rd} R{rn} (exp011 {res['exp011_rows']}행) + overview"
                    )
        except Exception as e:
            if verbose:
                print(f"  - 건너뜀: {rc} {rd} R{rn} (사유: {e})")

    if verbose:
        print(f"▶ 기간 업데이트 완료 [{from_date}~{to_date}] — {updated}개 경주 갱신")
    return updated


# =========================
# 17) main
# =========================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--rcity",
        default="서울",
        type=str,
        help="단일 경주 처리용(기간 업데이트에서는 무시)",
    )
    ap.add_argument("--rdate", default="20251228", type=str)
    ap.add_argument("--rno", default=5, type=int)

    ap.add_argument(
        "--update",
        action="store_true",
        help="해당 경주 exp011 + exp010(r_overview) 업데이트",
    )
    ap.add_argument(
        "--update_period",
        action="store_true",
        help="기간 exp011 + exp010(r_overview) 업데이트",
    )
    ap.add_argument("--from_date", default="", type=str)
    ap.add_argument("--to_date", default="", type=str)

    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    # ✅ 기간 업데이트
    if args.update_period:
        if not args.from_date or not args.to_date:
            raise SystemExit(
                "--update_period 사용 시 --from_date YYYYMMDD --to_date YYYYMMDD 필수"
            )
        update_exp011_for_period(
            args.from_date, args.to_date, rcity=None, verbose=args.verbose
        )
        return

    # 단일 경주 리포트 출력
    df = load_race(args.rcity, args.rdate, args.rno)
    df2, anchor_df, dark_df, total_summary, _ = build_report(df)
    print_report(df2, anchor_df, dark_df, total_summary)

    # ✅ 단일 경주 업데이트 (exp011 + exp010 같이)
    if args.update:
        res = update_exp011_for_race(
            args.rcity, args.rdate, args.rno, verbose=args.verbose
        )
        print(
            f"\n▶ 업데이트 완료: exp011={res['exp011_rows']}행 / exp010={res['exp010_rows']}행"
        )


if __name__ == "__main__":
    main()
