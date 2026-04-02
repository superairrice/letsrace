"""2026년 관리자 수익 분석 전략 조합의 최고 ROI를 전수탐색한다."""

import os
from itertools import combinations
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from 총환수율_new_균형주력_ROI보조 import (
    _build_admin_profit_runtime_config,
    _load_augmented_admin_profit_race_df,
)


DEFAULT_FROM_DATE = "20260101"
DEFAULT_TO_DATE = "20260324"
COMBO_SIZES = (1, 2, 3, 4, 5, 6)
TOP_N = 5
TRACKS = ("서울", "부산", "서울부산 통합")
MAX_CANDIDATES_FOR_LARGE_COMBOS = 15
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "tmp_betting_2026_combo_search_top5.csv"
)
PRESET_COMBOS = {
    "안정형": (
        "anchor1_57_24",
        "anchor1_58_24",
    ),
    "균형형": (
        "anchor1_57_24",
        "anchor1_24_58",
        "anchor1_58_24",
        "anchor1_25",
    ),
    "공격형": (
        "anchor1_57_24",
        "anchor1_58_24",
        "anchor1_25",
        "anchor1_24_58",
        "anchor1_25_68",
        "anchor12_3_7",
    ),
}


def _calc_hit_rate(hits: int, races: int) -> float:
    return (hits / races) if races > 0 else 0.0


def _get_candidate_keys(track_df: pd.DataFrame, strategy_columns: dict) -> list[str]:
    keys = []
    for key, meta in strategy_columns.items():
        bet_col = meta.get("bet")
        refund_col = meta.get("refund")
        hit_col = meta.get("hit")
        if not bet_col or not refund_col or not hit_col:
            continue
        if (
            bet_col not in track_df.columns
            or refund_col not in track_df.columns
            or hit_col not in track_df.columns
        ):
            continue
        if float(track_df[bet_col].fillna(0).sum()) <= 0:
            continue
        keys.append(key)
    return keys


def _build_strategy_arrays(track_df: pd.DataFrame, strategy_columns: dict) -> dict:
    candidate_keys = _get_candidate_keys(track_df, strategy_columns)
    if not candidate_keys:
        return {}
    bet_matrix = np.vstack(
        [
            track_df[strategy_columns[key]["bet"]].fillna(0).to_numpy(dtype=float)
            for key in candidate_keys
        ]
    )
    refund_matrix = np.vstack(
        [
            track_df[strategy_columns[key]["refund"]].fillna(0).to_numpy(dtype=float)
            for key in candidate_keys
        ]
    )
    hit_matrix = np.vstack(
        [
            track_df[strategy_columns[key]["hit"]].fillna(0).to_numpy(dtype=int)
            for key in candidate_keys
        ]
    )
    holes = np.array(
        [int(strategy_columns[key].get("holes_per_race", 0) or 0) for key in candidate_keys],
        dtype=int,
    )
    return {
        "candidate_keys": candidate_keys,
        "bet_matrix": bet_matrix,
        "refund_matrix": refund_matrix,
        "hit_matrix": hit_matrix,
        "holes": holes,
    }


def _select_candidate_keys_for_combo_size(
    track_df: pd.DataFrame,
    strategy_columns: dict,
    combo_size: int,
) -> list[str]:
    candidate_keys = _get_candidate_keys(track_df, strategy_columns)
    if combo_size <= 4 or len(candidate_keys) <= MAX_CANDIDATES_FOR_LARGE_COMBOS:
        return candidate_keys

    ranked = []
    for key in candidate_keys:
        meta = strategy_columns[key]
        bet = float(track_df[meta["bet"]].fillna(0).sum())
        refund = float(track_df[meta["refund"]].fillna(0).sum())
        hit = int(track_df[meta["hit"]].fillna(0).astype(int).gt(0).sum())
        roi = (refund / bet) if bet > 0 else 0.0
        ranked.append((key, roi, refund - bet, hit))
    ranked.sort(key=lambda item: (item[1], item[2], item[3]), reverse=True)
    return [item[0] for item in ranked[:MAX_CANDIDATES_FOR_LARGE_COMBOS]]


def _build_strategy_arrays_from_keys(
    track_df: pd.DataFrame,
    strategy_columns: dict,
    candidate_keys: list[str],
) -> dict:
    if not candidate_keys:
        return {}
    bet_matrix = np.vstack(
        [
            track_df[strategy_columns[key]["bet"]].fillna(0).to_numpy(dtype=float)
            for key in candidate_keys
        ]
    )
    refund_matrix = np.vstack(
        [
            track_df[strategy_columns[key]["refund"]].fillna(0).to_numpy(dtype=float)
            for key in candidate_keys
        ]
    )
    hit_matrix = np.vstack(
        [
            track_df[strategy_columns[key]["hit"]].fillna(0).to_numpy(dtype=int)
            for key in candidate_keys
        ]
    )
    holes = np.array(
        [int(strategy_columns[key].get("holes_per_race", 0) or 0) for key in candidate_keys],
        dtype=int,
    )
    return {
        "candidate_keys": candidate_keys,
        "bet_matrix": bet_matrix,
        "refund_matrix": refund_matrix,
        "hit_matrix": hit_matrix,
        "holes": holes,
    }


def _summarize_combo_from_indices(
    combo_indices: tuple[int, ...],
    races: int,
    strategy_arrays: dict,
    strategy_labels: dict,
) -> dict:
    candidate_keys = strategy_arrays["candidate_keys"]
    bet_matrix = strategy_arrays["bet_matrix"]
    refund_matrix = strategy_arrays["refund_matrix"]
    hit_matrix = strategy_arrays["hit_matrix"]
    holes_array = strategy_arrays["holes"]

    combo_keys = tuple(candidate_keys[idx] for idx in combo_indices)
    hits = int(hit_matrix[list(combo_indices)].max(axis=0).sum())
    bet = float(bet_matrix[list(combo_indices)].sum())
    refund = float(refund_matrix[list(combo_indices)].sum())
    return {
        "keys": combo_keys,
        "labels": tuple(strategy_labels.get(key, key) for key in combo_keys),
        "races": races,
        "hits": hits,
        "hit_rate": _calc_hit_rate(hits, races),
        "bet": bet,
        "refund": refund,
        "profit": refund - bet,
        "roi": (refund / bet) if bet > 0 else 0.0,
        "holes_per_race": int(holes_array[list(combo_indices)].sum()),
    }


def _find_top_combos(
    track_df: pd.DataFrame,
    combo_size: int,
    strategy_columns: dict,
    strategy_labels: dict,
    top_n: int = TOP_N,
) -> list[dict]:
    candidate_keys = _select_candidate_keys_for_combo_size(
        track_df, strategy_columns, combo_size
    )
    strategy_arrays = _build_strategy_arrays_from_keys(
        track_df, strategy_columns, candidate_keys
    )
    candidate_keys = strategy_arrays.get("candidate_keys", [])
    races = int(
        track_df[["경마장", "경주일", "경주번호"]].drop_duplicates().shape[0]
        if {"경마장", "경주일", "경주번호"}.issubset(track_df.columns)
        else len(track_df)
    )
    results = []
    for combo_indices in combinations(range(len(candidate_keys)), combo_size):
        results.append(
            _summarize_combo_from_indices(
                combo_indices,
                races,
                strategy_arrays,
                strategy_labels,
            )
        )
    results.sort(
        key=lambda item: (item["roi"], item["profit"], item["hit_rate"]),
        reverse=True,
    )
    return results[:top_n]


def _print_result(track_name: str, combo_size: int, result: dict) -> None:
    print(
        f"[{track_name} {combo_size}개] ROI {result['roi']:.6f}  "
        f"이익 {result['profit']:,.0f}원  적중율 {result['hit_rate']:.6f}  "
        f"경주수 {result['races']}  적중경주수 {result['hits']}  "
        f"총베팅 {result['bet']:,.0f}원  총환수 {result['refund']:,.0f}원  "
        f"구멍수 {result['holes_per_race']}"
    )
    print(f"  keys   : {' + '.join(result['keys'])}")
    print(f"  labels : {' + '.join(result['labels'])}")


def _print_preset_result(preset_name: str, track_name: str, result: dict) -> None:
    print(
        f"[{track_name} {preset_name}] ROI {result['roi']:.6f}  "
        f"이익 {result['profit']:,.0f}원  적중율 {result['hit_rate']:.6f}  "
        f"경주수 {result['races']}  적중경주수 {result['hits']}  "
        f"총베팅 {result['bet']:,.0f}원  총환수 {result['refund']:,.0f}원  "
        f"구멍수 {result['holes_per_race']}"
    )
    print(f"  keys   : {' + '.join(result['keys'])}")
    print(f"  labels : {' + '.join(result['labels'])}")


def _rows_from_results(track_name: str, combo_size: int, results: list[dict]) -> list[dict]:
    rows = []
    for rank, result in enumerate(results, start=1):
        rows.append(
            {
                "경마장": track_name,
                "조합개수": combo_size,
                "순위": rank,
                "전략keys": " + ".join(result["keys"]),
                "전략명": " + ".join(result["labels"]),
                "경주수": result["races"],
                "적중경주수": result["hits"],
                "적중율": result["hit_rate"],
                "총베팅액": result["bet"],
                "총환수액": result["refund"],
                "이익금액": result["profit"],
                "ROI": result["roi"],
                "구멍수": result["holes_per_race"],
            }
        )
    return rows


def _summarize_preset_combo(
    track_df: pd.DataFrame,
    preset_name: str,
    preset_keys: tuple[str, ...],
    strategy_columns: dict,
    strategy_labels: dict,
) -> Optional[dict]:
    valid_keys = []
    for key in preset_keys:
        meta = strategy_columns.get(key)
        if not meta:
            return None
        if (
            meta["bet"] not in track_df.columns
            or meta["refund"] not in track_df.columns
            or meta["hit"] not in track_df.columns
        ):
            return None
        if float(track_df[meta["bet"]].fillna(0).sum()) <= 0:
            return None
        valid_keys.append(key)

    strategy_arrays = _build_strategy_arrays_from_keys(
        track_df, strategy_columns, list(valid_keys)
    )
    races = int(
        track_df[["경마장", "경주일", "경주번호"]].drop_duplicates().shape[0]
        if {"경마장", "경주일", "경주번호"}.issubset(track_df.columns)
        else len(track_df)
    )
    result = _summarize_combo_from_indices(
        tuple(range(len(valid_keys))),
        races,
        strategy_arrays,
        strategy_labels,
    )
    result["preset_name"] = preset_name
    return result


def _build_preset_rows(track_name: str, preset_results: list[dict]) -> list[dict]:
    rows = []
    for result in preset_results:
        rows.append(
            {
                "경마장": track_name,
                "조합개수": len(result["keys"]),
                "순위": 0,
                "전략keys": " + ".join(result["keys"]),
                "전략명": " + ".join(result["labels"]),
                "경주수": result["races"],
                "적중경주수": result["hits"],
                "적중율": result["hit_rate"],
                "총베팅액": result["bet"],
                "총환수액": result["refund"],
                "이익금액": result["profit"],
                "ROI": result["roi"],
                "구멍수": result["holes_per_race"],
                "프리셋": result["preset_name"],
            }
        )
    return rows


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "letsrace.settings")

    import django

    django.setup()

    (
        _admin_profit_groups,
        strategy_columns,
        strategy_labels,
    ) = _build_admin_profit_runtime_config()
    race_df = _load_augmented_admin_profit_race_df(DEFAULT_FROM_DATE, DEFAULT_TO_DATE)
    if race_df is None or race_df.empty:
        print("집계 대상 데이터가 없습니다.")
        return

    all_rows = []
    print(
        f"[기간] {DEFAULT_FROM_DATE} ~ {DEFAULT_TO_DATE}  "
        f"[대상 경주수] "
        f"{race_df[['경마장', '경주일', '경주번호']].drop_duplicates().shape[0]}"
    )

    for track_name in TRACKS:
        if track_name == "서울부산 통합":
            track_df = race_df.copy()
        else:
            track_df = race_df[race_df["경마장"] == track_name].copy()
        if track_df.empty:
            continue

        candidate_count = len(_get_candidate_keys(track_df, strategy_columns))
        print(f"[{track_name}] 후보 전략 수 {candidate_count}")
        preset_results = []
        for preset_name, preset_keys in PRESET_COMBOS.items():
            result = _summarize_preset_combo(
                track_df,
                preset_name,
                preset_keys,
                strategy_columns,
                strategy_labels,
            )
            if result is None:
                continue
            preset_results.append(result)
            _print_preset_result(preset_name, track_name, result)
        if preset_results:
            all_rows.extend(_build_preset_rows(track_name, preset_results))
        for combo_size in COMBO_SIZES:
            top_results = _find_top_combos(
                track_df,
                combo_size=combo_size,
                strategy_columns=strategy_columns,
                strategy_labels=strategy_labels,
                top_n=TOP_N,
            )
            if not top_results:
                continue
            all_rows.extend(_rows_from_results(track_name, combo_size, top_results))
            _print_result(track_name, combo_size, top_results[0])
        print()

    if all_rows:
        pd.DataFrame(all_rows).to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
        print(f"[CSV 저장] {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
