"""지정한 주력/보조 전략만으로 rank 기준 별도 수익 분석을 출력한다."""

import copy
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import 베팅방법별_환수율_rank기준 as rank_base_mod


PROFILE_NAME = "별도_수익분석_주력보조_rank기준_무캡"
DEFAULT_FROM_DATE = "20260101"
DEFAULT_TO_DATE = "20261231"
DEFAULT_OUTPUT_PATH = (
    "/Users/Super007/Documents/rank_total_new_별도_수익분석_주력보조_rank기준_무캡.csv"
)
DEFAULT_SATURDAY_WINDOW_OUTPUT_PATH = (
    "/Users/Super007/Documents/rank_total_new_별도_수익분석_주력보조_rank기준_무캡_토요일pm2일.csv"
)

PRIMARY_STRATEGY_KEYS = [
    "top3pair_46_trio",
    "anchor1_26",
    "anchor1_23_47",
    "anchor1_24_58",
    "anchor1_58_24",
]

SUPPORT_STRATEGY_KEYS = [
    "top4pair_56_trio",
    "anchor1_25",
    "anchor1_23_46",
    "anchor1_24_57",
    "anchor1_57_24",
    "anchor2_37_trifecta",
]

RANK_STRATEGY_LABELS = {
    "top3pair_46_trio": "rank 1~3 복조 / 4~6 삼복",
    "anchor1_26": "rank 1 축 rank 2~6 삼쌍",
    "anchor1_23_47": "rank 1 축 rank 2~3 / 4~7 삼쌍",
    "anchor1_24_58": "rank 1 축 rank 2~4 / 5~8 삼쌍",
    "anchor1_58_24": "rank 1 축 rank 5~8 / 2~4 삼쌍",
    "top4pair_56_trio": "rank 1~4 복조 / 5~6 삼복",
    "anchor1_25": "rank 1 축 rank 2~5 삼쌍",
    "anchor1_23_46": "rank 1 축 rank 2~3 / 4~6 삼쌍",
    "anchor1_24_57": "rank 1 축 rank 2~4 / 5~7 삼쌍",
    "anchor1_57_24": "rank 1 축 rank 5~7 / 2~4 삼쌍",
    "anchor2_37_trifecta": "rank 2 축 rank 3~7 삼쌍",
}


def _build_saturday_pm2_dates(from_date: str, to_date: str) -> Set[str]:
    start = datetime.strptime(from_date, "%Y%m%d").date()
    end = datetime.strptime(to_date, "%Y%m%d").date()
    allowed_dates: Set[str] = set()

    current = start
    while current <= end:
        if current.weekday() == 5:
            for offset in range(-2, 3):
                candidate = current + timedelta(days=offset)
                if start <= candidate <= end:
                    allowed_dates.add(candidate.strftime("%Y%m%d"))
        current += timedelta(days=1)

    return allowed_dates


def build_admin_profit_analysis_payload_for_range(
    from_date: str, to_date: str, allowed_dates: Optional[Set[str]] = None
) -> dict:
    from apps.core.views import (
        ADMIN_PROFIT_STRATEGY_LABELS,
        ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS,
        _filter_race_df_for_admin_profit_trio_odds,
    )

    admin_profit_groups = {
        "서울": {
            "주력": list(PRIMARY_STRATEGY_KEYS),
            "보조": list(SUPPORT_STRATEGY_KEYS),
        },
        "부산": {
            "주력": list(PRIMARY_STRATEGY_KEYS),
            "보조": list(SUPPORT_STRATEGY_KEYS),
        },
    }
    admin_profit_strategy_result_columns = copy.deepcopy(
        ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS
    )
    admin_profit_strategy_labels = copy.deepcopy(ADMIN_PROFIT_STRATEGY_LABELS)

    admin_profit_strategy_result_columns["anchor1_26"] = {
        "bet": "1축_2~6_삼쌍_베팅액",
        "refund": "1축_2~6_삼쌍_환수액",
        "hit": "r_pop1_축_2~6_삼쌍_적중",
        "holes_per_race": 20,
    }
    admin_profit_strategy_result_columns["anchor2_37_trifecta"] = {
        "bet": "2축_3~7_삼쌍_베팅액",
        "refund": "2축_3~7_삼쌍_환수액",
        "hit": "r_pop2_축_3~7_삼쌍_적중",
        "holes_per_race": 20,
    }
    admin_profit_strategy_labels.update(RANK_STRATEGY_LABELS)

    summary_total = None
    method_bet_by_track = []
    metrics = {"roi": 0.0, "roi_pct": 0.0}

    try:
        race_df, _summary = rank_base_mod._run_calc_rank_anchor_26_trifecta_quietly(
            from_date=from_date,
            to_date=to_date,
            bet_unit=100,
            apply_odds_filter=False,
        )
    except Exception as exc:
        print(f"[admin_profit_analysis_range] calc failed: {exc}")
        race_df = None

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        race_df = _filter_race_df_for_admin_profit_trio_odds(race_df)
        if allowed_dates is not None and "경주일" in race_df.columns:
            race_df = race_df[
                race_df["경주일"].astype(str).isin(set(map(str, allowed_dates)))
            ].copy()
        race_df = rank_base_mod._augment_anchor1_26_trifecta(race_df, bet_unit=100)
        race_df = rank_base_mod._augment_anchor2_37_trifecta(race_df, bet_unit=100)
        race_df = rank_base_mod._augment_top4pair_56_trio(race_df, bet_unit=100)
        if race_df.empty:
            race_df = None

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        primary_total_bet = 0.0
        primary_total_refund = 0.0
        primary_total_hits = 0
        primary_total_races = 0

        for track_name in ["서울", "부산"]:
            track_df = race_df[race_df.get("경마장") == track_name].copy()
            if track_df.empty:
                continue

            track_races = int(
                track_df[["경주일", "경주번호"]].drop_duplicates().shape[0]
                if {"경주일", "경주번호"}.issubset(track_df.columns)
                else len(track_df)
            )
            methods = []
            track_bet = 0.0
            track_refund = 0.0
            hit_cols_all = []

            for group_label, strategy_keys in admin_profit_groups.get(
                track_name, {}
            ).items():
                bet_cols = []
                refund_cols = []
                hit_cols = []
                detail_methods = []

                for key in strategy_keys:
                    column_meta = admin_profit_strategy_result_columns.get(key)
                    if not column_meta:
                        continue
                    bet_col = column_meta["bet"]
                    refund_col = column_meta["refund"]
                    hit_col = column_meta["hit"]

                    if bet_col in track_df.columns:
                        bet_cols.append(bet_col)
                    if refund_col in track_df.columns:
                        refund_cols.append(refund_col)
                    if hit_col in track_df.columns:
                        hit_cols.append(hit_col)
                        hit_cols_all.append(hit_col)

                    bet_amount = (
                        float(track_df[bet_col].fillna(0).sum())
                        if bet_col in track_df.columns
                        else 0.0
                    )
                    refund_amount = (
                        float(track_df[refund_col].fillna(0).sum())
                        if refund_col in track_df.columns
                        else 0.0
                    )
                    hit_count = (
                        int(track_df[hit_col].fillna(0).astype(int).sum())
                        if hit_col in track_df.columns
                        else 0
                    )
                    detail_methods.append(
                        {
                            "label": (
                                f"  - {admin_profit_strategy_labels.get(key, key)}"
                            ),
                            "amount": bet_amount,
                            "refund": refund_amount,
                            "profit": refund_amount - bet_amount,
                            "hits": hit_count,
                            "holes_per_race": column_meta.get("holes_per_race", 0),
                        }
                    )

                detail_methods.sort(key=rank_base_mod._method_display_sort_key)
                group_bet = float(track_df[bet_cols].sum().sum()) if bet_cols else 0.0
                group_refund = (
                    float(track_df[refund_cols].sum().sum()) if refund_cols else 0.0
                )
                group_hits = (
                    int(
                        track_df[hit_cols].fillna(0).astype(int).gt(0).any(axis=1).sum()
                    )
                    if hit_cols
                    else 0
                )
                methods.append(
                    {
                        "label": group_label,
                        "amount": group_bet,
                        "refund": group_refund,
                        "profit": group_refund - group_bet,
                        "hits": group_hits,
                        "holes_per_race": int(
                            sum(
                                admin_profit_strategy_result_columns.get(
                                    key, {}
                                ).get("holes_per_race", 0)
                                for key in strategy_keys
                            )
                        ),
                        "is_group": True,
                        "is_support_group": group_label == "보조",
                    }
                )
                methods.extend(detail_methods)
                track_bet += group_bet
                track_refund += group_refund

                if group_label == "주력":
                    primary_total_bet += group_bet
                    primary_total_refund += group_refund
                    primary_total_hits += group_hits
                    primary_total_races += track_races

            track_hit_races = (
                int(
                    track_df[hit_cols_all]
                    .fillna(0)
                    .astype(int)
                    .gt(0)
                    .any(axis=1)
                    .sum()
                )
                if hit_cols_all
                else 0
            )

            method_bet_by_track.append(
                {
                    "track": track_name,
                    "methods": methods,
                    "total_races": track_races,
                    "total_bet": track_bet,
                    "total_refund": track_refund,
                    "total_profit": track_refund - track_bet,
                    "total_holes_per_race": int(
                        sum(
                            admin_profit_strategy_result_columns.get(key, {}).get(
                                "holes_per_race", 0
                            )
                            for groups in admin_profit_groups.get(track_name, {}).values()
                            for key in groups
                        )
                    ),
                    "hit_races": track_hit_races,
                    "roi": (track_refund / track_bet) if track_bet > 0 else 0.0,
                    "roi_pct": (
                        ((track_refund / track_bet) * 100.0)
                        if track_bet > 0
                        else 0.0
                    ),
                }
            )

        summary_total = {
            "races": primary_total_races,
            "hits": primary_total_hits,
            "total_bet": primary_total_bet,
            "total_refund": primary_total_refund,
            "profit": primary_total_refund - primary_total_bet,
        }
        metrics["roi"] = (
            (primary_total_refund / primary_total_bet) if primary_total_bet > 0 else 0.0
        )
        metrics["roi_pct"] = metrics["roi"] * 100.0

    return {
        "i_rdate": to_date,
        "from_date": from_date,
        "to_date": to_date,
        "summary_total": summary_total,
        "method_bet_by_track": method_bet_by_track,
        "metrics": metrics,
    }


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "letsrace.settings")

    import django

    django.setup()

    payload = build_admin_profit_analysis_payload_for_range(
        DEFAULT_FROM_DATE,
        DEFAULT_TO_DATE,
    )
    rank_base_mod.PROFILE_NAME = PROFILE_NAME
    rank_base_mod.print_payload(payload)
    rank_base_mod.save_payload_df(payload, DEFAULT_OUTPUT_PATH)

    saturday_pm2_dates = _build_saturday_pm2_dates(DEFAULT_FROM_DATE, DEFAULT_TO_DATE)
    saturday_pm2_payload = build_admin_profit_analysis_payload_for_range(
        DEFAULT_FROM_DATE,
        DEFAULT_TO_DATE,
        allowed_dates=saturday_pm2_dates,
    )
    print("\n[토요일 ±2일 기준 집계]")
    rank_base_mod.print_payload(saturday_pm2_payload)
    rank_base_mod.save_payload_df(
        saturday_pm2_payload,
        DEFAULT_SATURDAY_WINDOW_OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()
