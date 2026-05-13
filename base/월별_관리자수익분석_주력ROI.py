"""관리자 수익 분석 팝업 기준 주력베팅 월별/주별 ROI를 출력한다."""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


PROFILE_NAME = "관리자수익분석_주력_월주별ROI"
DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260420"
DEFAULT_OUTPUT_PATH = "/Users/Super007/Documents/admin_profit_primary_monthly_weekly_roi.csv"


def _parse_yyyymmdd(value: str):
    return datetime.strptime(str(value), "%Y%m%d").date()


def _format_yyyymmdd(value) -> str:
    return value.strftime("%Y%m%d")


def _calc_hit_rate(hits, races) -> float:
    try:
        hits_value = int(hits or 0)
        races_value = int(races or 0)
    except Exception:
        return 0.0
    return (hits_value / races_value) if races_value > 0 else 0.0


def _method_display_sort_key(label: str):
    text = str(label or "").strip()
    if "삼복" in text:
        return (0, text)
    if "삼쌍" in text:
        return (1, text)
    return (2, text)


def _iter_saturdays(from_date: str, to_date: str):
    start_date = _parse_yyyymmdd(from_date)
    end_date = _parse_yyyymmdd(to_date)
    if start_date > end_date:
        return []

    cursor = start_date
    while cursor.weekday() != 5:
        cursor += timedelta(days=1)
        if cursor > end_date:
            return []

    saturdays = []
    while cursor <= end_date:
        saturdays.append(cursor)
        cursor += timedelta(days=7)
    return saturdays


def _extract_primary_group_rows(payload: dict, period_type: str, period_label: str) -> list[dict]:
    rows = []
    combined_methods = {}
    combined_groups = {}

    for track in payload.get("method_bet_by_track") or []:
        track_name = track.get("track")
        current_group_label = None
        for method in track.get("methods") or []:
            if method.get("is_group"):
                label = str(method.get("label", "") or "").strip()
                if not label:
                    continue
                current_group_label = label
                amount = float(method.get("amount", 0.0) or 0.0)
                refund = float(method.get("refund", 0.0) or 0.0)
                hits = int(method.get("hits", 0) or 0)
                profit = float(method.get("profit", 0.0) or 0.0)
                rows.append(
                    {
                        "집계단위": period_type,
                        "기간": period_label,
                        "기준일": payload.get("i_rdate"),
                        "집계시작일": payload.get("from_date"),
                        "집계종료일": payload.get("to_date"),
                        "경마장": track_name,
                        "그룹명": label,
                        "구분": "그룹합계",
                        "전략명": label,
                        "경주수": int(track.get("total_races", 0) or 0),
                        "적중경주수": hits,
                        "적중율": _calc_hit_rate(hits, track.get("total_races", 0)),
                        "총베팅액": amount,
                        "총환수액": refund,
                        "이익금액": profit,
                        "환수율": (refund / amount) if amount > 0 else 0.0,
                        "환수율_pct": ((refund / amount) * 100.0) if amount > 0 else 0.0,
                        "구멍수": method.get("holes_per_race"),
                    }
                )
                group_item = combined_groups.setdefault(
                    label,
                    {
                        "amount": 0.0,
                        "refund": 0.0,
                        "profit": 0.0,
                        "hits": 0,
                        "races": 0,
                        "holes": set(),
                    },
                )
                group_item["amount"] += amount
                group_item["refund"] += refund
                group_item["profit"] += profit
                group_item["hits"] += hits
                group_item["races"] += int(track.get("total_races", 0) or 0)
                if method.get("holes_per_race") is not None:
                    group_item["holes"].add(method.get("holes_per_race"))
                continue
            label = str(method.get("label", "") or "").strip()
            if not label:
                continue
            amount = float(method.get("amount", 0.0) or 0.0)
            refund = float(method.get("refund", 0.0) or 0.0)
            hits = int(method.get("hits", 0) or 0)
            profit = float(method.get("profit", 0.0) or 0.0)
            method_item = combined_methods.setdefault(
                (current_group_label, label),
                {
                    "amount": 0.0,
                    "refund": 0.0,
                    "profit": 0.0,
                    "hits": 0,
                    "races": 0,
                    "holes": set(),
                },
            )
            method_item["amount"] += amount
            method_item["refund"] += refund
            method_item["profit"] += profit
            method_item["hits"] += hits
            method_item["races"] += int(track.get("total_races", 0) or 0)
            if method.get("holes_per_race") is not None:
                method_item["holes"].add(method.get("holes_per_race"))

    for label in sorted(combined_groups.keys()):
        item = combined_groups[label]
        amount = float(item["amount"])
        refund = float(item["refund"])
        rows.append(
            {
                "집계단위": period_type,
                "기간": period_label,
                "기준일": payload.get("i_rdate"),
                "집계시작일": payload.get("from_date"),
                "집계종료일": payload.get("to_date"),
                "경마장": "서울부산 통합",
                "그룹명": label,
                "구분": "그룹합계",
                "전략명": label,
                "경주수": int(item["races"]),
                "적중경주수": int(item["hits"]),
                "적중율": _calc_hit_rate(item["hits"], item["races"]),
                "총베팅액": amount,
                "총환수액": refund,
                "이익금액": float(item["profit"]),
                "환수율": (refund / amount) if amount > 0 else 0.0,
                "환수율_pct": ((refund / amount) * 100.0) if amount > 0 else 0.0,
                "구멍수": next(iter(item["holes"])) if len(item["holes"]) == 1 else None,
            }
        )
    for (group_name, label), item in sorted(
        combined_methods.items(),
        key=lambda x: (str(x[0][0] or ""),) + _method_display_sort_key(x[0][1]),
    ):
        amount = float(item["amount"])
        refund = float(item["refund"])
        holes = item["holes"]
        rows.append(
            {
                "집계단위": period_type,
                "기간": period_label,
                "기준일": payload.get("i_rdate"),
                "집계시작일": payload.get("from_date"),
                "집계종료일": payload.get("to_date"),
                "경마장": "서울부산 통합",
                "그룹명": group_name,
                "구분": "베팅방법총합",
                "전략명": label,
                "경주수": int(item["races"]),
                "적중경주수": int(item["hits"]),
                "적중율": _calc_hit_rate(item["hits"], item["races"]),
                "총베팅액": amount,
                "총환수액": refund,
                "이익금액": float(item["profit"]),
                "환수율": (refund / amount) if amount > 0 else 0.0,
                "환수율_pct": ((refund / amount) * 100.0) if amount > 0 else 0.0,
                "구멍수": next(iter(holes)) if len(holes) == 1 else None,
            }
        )
    return rows


def build_weekly_primary_roi(from_date: str, to_date: str) -> pd.DataFrame:
    from django.db import connections
    from apps.core.views import _build_admin_profit_analysis_payload

    rows = []
    for sat_date in _iter_saturdays(from_date, to_date):
        payload = _build_admin_profit_analysis_payload(_format_yyyymmdd(sat_date))
        iso_year, iso_week, _ = sat_date.isocalendar()
        period_label = f"{iso_year}-W{int(iso_week):02d}"
        rows.extend(_extract_primary_group_rows(payload, "주별", period_label))
        connections.close_all()

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    track_order = {"서울부산 통합": 0, "서울": 1, "부산": 2}
    group_order = {"그룹합계": 0, "베팅방법총합": 1}
    df["_track_order"] = df["경마장"].map(track_order).fillna(9)
    df["_group_order"] = df["구분"].map(group_order).fillna(9)
    df = df.sort_values(
        ["기간", "_track_order", "그룹명", "_group_order", "전략명", "경마장"]
    ).drop(columns=["_track_order", "_group_order"])
    return df.reset_index(drop=True)


def build_monthly_primary_roi(weekly_df: pd.DataFrame) -> pd.DataFrame:
    if weekly_df.empty:
        return pd.DataFrame()

    monthly_source = weekly_df.copy()
    monthly_source["년월"] = monthly_source["기준일"].astype(str).str.slice(0, 4) + "-" + monthly_source["기준일"].astype(str).str.slice(4, 6)

    grouped = (
        monthly_source.groupby(["년월", "경마장", "그룹명", "구분", "전략명"], dropna=False)
        .agg(
            집계시작일=("집계시작일", "min"),
            집계종료일=("집계종료일", "max"),
            경주수=("경주수", "sum"),
            적중경주수=("적중경주수", "sum"),
            총베팅액=("총베팅액", "sum"),
            총환수액=("총환수액", "sum"),
            이익금액=("이익금액", "sum"),
            구멍수=("구멍수", "first"),
        )
        .reset_index()
    )
    grouped["집계단위"] = "월별"
    grouped["기간"] = grouped["년월"]
    grouped["기준일"] = grouped["년월"].str.replace("-", "", regex=False) + "01"
    grouped["적중율"] = grouped.apply(
        lambda row: _calc_hit_rate(row["적중경주수"], row["경주수"]),
        axis=1,
    )
    grouped["환수율"] = grouped.apply(
        lambda row: (float(row["총환수액"]) / float(row["총베팅액"])) if float(row["총베팅액"]) > 0 else 0.0,
        axis=1,
    )
    grouped["환수율_pct"] = grouped["환수율"] * 100.0
    grouped = grouped[
        [
            "집계단위",
            "기간",
            "기준일",
            "집계시작일",
            "집계종료일",
            "경마장",
            "그룹명",
            "구분",
            "전략명",
            "경주수",
            "적중경주수",
            "적중율",
            "총베팅액",
            "총환수액",
            "이익금액",
            "환수율",
            "환수율_pct",
            "구멍수",
        ]
    ].copy()

    track_order = {"서울부산 통합": 0, "서울": 1, "부산": 2}
    group_order = {"그룹합계": 0, "베팅방법총합": 1}
    grouped["_track_order"] = grouped["경마장"].map(track_order).fillna(9)
    grouped["_group_order"] = grouped["구분"].map(group_order).fillna(9)
    grouped = grouped.sort_values(
        ["기간", "_track_order", "그룹명", "_group_order", "전략명", "경마장"]
    ).drop(columns=["_track_order", "_group_order"])
    return grouped.reset_index(drop=True)


def print_primary_roi(df: pd.DataFrame) -> None:
    if df.empty:
        print("집계 결과가 없습니다.")
        return

    for row in df.itertuples(index=False):
        prefix = f"[{row.집계단위} {row.기간}]  {row.경마장}  {row.구분}"
        if str(row.전략명 or "").strip():
            prefix += f"  {row.전략명}"
        print(
            f"{prefix}  "
            f"경주수: {int(row.경주수)}  "
            f"적중경주수: {int(row.적중경주수)}  "
            f"적중율: {float(row.적중율):.3f}  "
            f"총베팅액: {float(row.총베팅액):,.0f}원  "
            f"총환수액: {float(row.총환수액):,.0f}원  "
            f"이익금액: {float(row.이익금액):,.0f}원  "
            f"환수율: {float(row.환수율):.3f}"
        )


def print_monthly_combined_group_summary(df: pd.DataFrame) -> None:
    if df.empty:
        return

    filtered = df[
        (df["집계단위"] == "월별")
        & (df["경마장"] == "서울부산 통합")
    ].copy()
    if filtered.empty:
        return

    for group_name in ["주력베팅", "보조베팅"]:
        group_df = filtered[filtered["그룹명"] == group_name].copy()
        if group_df.empty:
            continue
        print(f"[서울부산 통합 {group_name} 월별]")
        print_primary_roi(group_df)


def print_weekly_combined_group_summary(df: pd.DataFrame) -> None:
    if df.empty:
        return

    filtered = df[
        (df["집계단위"] == "주별")
        & (df["경마장"] == "서울부산 통합")
    ].copy()
    if filtered.empty:
        return

    for group_name in ["주력베팅", "보조베팅"]:
        group_df = filtered[filtered["그룹명"] == group_name].copy()
        if group_df.empty:
            continue
        print(f"[서울부산 통합 {group_name} 주별]")
        print_primary_roi(group_df)


def save_primary_roi(df: pd.DataFrame, output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    if df.empty:
        return
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"▶ {PROFILE_NAME} CSV 저장: {output_path}")


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "letsrace.settings")

    import django

    django.setup()

    weekly_df = build_weekly_primary_roi(DEFAULT_FROM_DATE, DEFAULT_TO_DATE)
    monthly_df = build_monthly_primary_roi(weekly_df)
    combined_df = pd.concat([monthly_df, weekly_df], ignore_index=True)

    print(f"[{PROFILE_NAME}]")
    print_monthly_combined_group_summary(monthly_df)
    print_weekly_combined_group_summary(weekly_df)
    save_primary_roi(combined_df)


if __name__ == "__main__":
    main()
