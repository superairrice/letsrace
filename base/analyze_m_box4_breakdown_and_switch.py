#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
m_rank BOX4가 "깨지는 구간"을 월/등급/거리로 찾아내고,
그 구간에서만 BOX6(또는 다른 타입)으로 스위치하는 룰을 만들기 위한 분석 스크립트.

입력:
  - 이전에 생성한 RAW CSV: m_f_BOX4_BOX6_raw.csv
    (m_rank_f_rank_box4_box6_compare.py가 저장한 파일)

출력:
  - breakdown_month.csv          : 월별 ROI/환수율
  - breakdown_grade.csv          : 등급별 ROI/환수율
  - breakdown_distance.csv       : 거리별 ROI/환수율
  - breakdown_month_grade.csv    : 월x등급 ROI/환수율
  - switch_rule_preview.csv      : (예시) 월x등급에서 BOX4가 나쁘면 BOX6로 스위치했을 때의 성과
"""

from __future__ import annotations
import argparse
import pandas as pd


def _roi(refund: float, bet: float) -> float:
    return (refund - bet) / bet if bet > 0 else 0.0


def _rate(refund: float, bet: float) -> float:
    return refund / bet if bet > 0 else 0.0


def summarize(df: pd.DataFrame, by_cols: list[str], prefix: str) -> pd.DataFrame:
    g = (
        df.groupby(by_cols, dropna=False)
          .agg(
              races=("경주번호", "count"),
              m_BOX4_bet=("m_BOX4_bet", "sum"),
              m_BOX4_refund=("m_BOX4_refund", "sum"),
              m_BOX4_hit=("m_BOX4_hit", "sum"),
              m_BOX6_bet=("m_BOX6_bet", "sum"),
              m_BOX6_refund=("m_BOX6_refund", "sum"),
              m_BOX6_hit=("m_BOX6_hit", "sum"),
          )
          .reset_index()
    )
    g["m_BOX4_refund_rate"] = g.apply(lambda r: _rate(r["m_BOX4_refund"], r["m_BOX4_bet"]), axis=1)
    g["m_BOX4_roi"] = g.apply(lambda r: _roi(r["m_BOX4_refund"], r["m_BOX4_bet"]), axis=1)
    g["m_BOX6_refund_rate"] = g.apply(lambda r: _rate(r["m_BOX6_refund"], r["m_BOX6_bet"]), axis=1)
    g["m_BOX6_roi"] = g.apply(lambda r: _roi(r["m_BOX6_refund"], r["m_BOX6_bet"]), axis=1)

    # 정렬: BOX4 ROI가 나쁜 순 (깨지는 구간 찾기)
    g = g.sort_values(["m_BOX4_roi", "races"], ascending=[True, False]).reset_index(drop=True)
    return g


def switch_rule_preview(
    df: pd.DataFrame,
    rule_df: pd.DataFrame,
    key_cols: list[str],
    bad_roi_threshold: float = 0.0,
) -> pd.DataFrame:
    """
    예시 룰:
      - key_cols(예: ['년월','등급']) 단위로 BOX4 ROI가 threshold 이하이면 BOX6로 스위치
      - 그 외는 BOX4 유지
    """
    # 룰 테이블: key → use_box6 (bool)
    rule_df = rule_df.copy()
    rule_df["use_box6"] = rule_df["m_BOX4_roi"] <= bad_roi_threshold
    keep = key_cols + ["use_box6"]
    rule_map = rule_df[keep].drop_duplicates()

    merged = df.merge(rule_map, on=key_cols, how="left")
    merged["use_box6"] = merged["use_box6"].fillna(False)

    # 선택 성과
    merged["sel_bet"] = merged.apply(lambda r: r["m_BOX6_bet"] if r["use_box6"] else r["m_BOX4_bet"], axis=1)
    merged["sel_refund"] = merged.apply(lambda r: r["m_BOX6_refund"] if r["use_box6"] else r["m_BOX4_refund"], axis=1)
    merged["sel_hit"] = merged.apply(lambda r: r["m_BOX6_hit"] if r["use_box6"] else r["m_BOX4_hit"], axis=1)
    merged["sel_type"] = merged["use_box6"].map(lambda x: "BOX6" if x else "BOX4")

    overall = pd.DataFrame([{
        "rule": f"switch_if_BOX4_ROI<={bad_roi_threshold}",
        "races": int(len(merged)),
        "bet": float(merged["sel_bet"].sum()),
        "refund": float(merged["sel_refund"].sum()),
        "refund_rate": _rate(float(merged["sel_refund"].sum()), float(merged["sel_bet"].sum())),
        "roi": _roi(float(merged["sel_refund"].sum()), float(merged["sel_bet"].sum())),
        "box6_used_races": int((merged["sel_type"] == "BOX6").sum()),
        "box4_used_races": int((merged["sel_type"] == "BOX4").sum()),
    }])

    return overall, merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="m_f_BOX4_BOX6_raw.csv 경로")
    ap.add_argument("--out_dir", default=".", help="결과 저장 폴더")
    ap.add_argument("--threshold", type=float, default=0.0, help="BOX4 ROI가 이 값 이하이면 BOX6로 스위치")
    args = ap.parse_args()

    df = pd.read_csv(args.raw, dtype={"년월": str, "등급": str, "경주일": str})
    # 안전: 결측 처리
    df["등급"] = df["등급"].fillna("")
    df["경주거리"] = pd.to_numeric(df["경주거리"], errors="coerce")

    os = __import__("os")
    os.makedirs(args.out_dir, exist_ok=True)

    # 1) breakdown
    month = summarize(df, ["년월"], "month")
    grade = summarize(df, ["등급"], "grade")
    dist = summarize(df, ["경주거리"], "distance")
    mg = summarize(df, ["년월", "등급"], "month_grade")

    month.to_csv(os.path.join(args.out_dir, "breakdown_month.csv"), index=False, encoding="utf-8-sig")
    grade.to_csv(os.path.join(args.out_dir, "breakdown_grade.csv"), index=False, encoding="utf-8-sig")
    dist.to_csv(os.path.join(args.out_dir, "breakdown_distance.csv"), index=False, encoding="utf-8-sig")
    mg.to_csv(os.path.join(args.out_dir, "breakdown_month_grade.csv"), index=False, encoding="utf-8-sig")

    # 2) 스위치 룰 예시 (월x등급 기준)
    overall, merged = switch_rule_preview(df, mg, ["년월", "등급"], bad_roi_threshold=args.threshold)
    overall.to_csv(os.path.join(args.out_dir, "switch_rule_overall.csv"), index=False, encoding="utf-8-sig")
    merged.to_csv(os.path.join(args.out_dir, "switch_rule_preview.csv"), index=False, encoding="utf-8-sig")

    print("===================================")
    print("Saved breakdown files to:", args.out_dir)
    print("Worst segments (BOX4 ROI lowest) - month:")
    print(month.head(10).to_string(index=False))
    print("Worst segments (BOX4 ROI lowest) - month x grade:")
    print(mg.head(10).to_string(index=False))
    print("Switch rule overall:")
    print(overall.to_string(index=False))
    print("===================================")


if __name__ == "__main__":
    main()
