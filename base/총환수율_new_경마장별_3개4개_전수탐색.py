"""총환수율_new.py 전체 전략의 경마장별 3개/4개 최고 ROI 조합 재현 스크립트."""

import contextlib
import io
import os
from itertools import combinations

import numpy as np
import pandas as pd

import 총환수율_new as base_mod


DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260315"
DEFAULT_TOP_N = 3
COMBO_SIZES = (3, 4)
TRACK_ORDER = ("서울", "부산")
EXPECTED_TOP_COMBOS = {
    "서울": {
        3: ("anchor1_25", "anchor1_23_46", "anchor1_23_47"),
        4: ("anchor1_25", "anchor1_23_46", "anchor1_23_47", "anchor1_23_48"),
    },
    "부산": {
        3: ("anchor1_57_24", "anchor3_24", "anchor1_23_46"),
        4: ("anchor1_57_24", "anchor3_24", "anchor1_69_25", "anchor1_23_46"),
    },
}
ALL_STRATEGY_RESULT_COLUMNS = {
    "anchor1_24_57": {
        "bet": "1축_2~4_5~7_베팅액",
        "refund": "1축_2~4_5~7_환수액",
        "hit": "r_pop1_축_2~4_5~7_적중",
    },
    "anchor1_24_quinella": {
        "bet": "1축_2~4_복승_베팅액",
        "refund": "1축_2~4_복승_환수액",
        "hit": "r_pop1_축_2~4_복승_적중",
    },
    "anchor1_26_quinella": {
        "bet": "1축_2~6_복승_베팅액",
        "refund": "1축_2~6_복승_환수액",
        "hit": "r_pop1_축_2~6_복승_적중",
    },
    "top3pair_46_quinella": {
        "bet": "1~3_복조축_4~6_복승_베팅액",
        "refund": "1~3_복조축_4~6_복승_환수액",
        "hit": "r_pop1~3_복조축_4~6_복승_적중",
    },
    "anchor12_3_4_quinella": {
        "bet": "1,2축_3~4_복승_베팅액",
        "refund": "1,2축_3~4_복승_환수액",
        "hit": "r_pop1,2_축_3~4_복승_적중",
    },
    "anchor12_3_5_quinella": {
        "bet": "1,2축_3~5_복승_베팅액",
        "refund": "1,2축_3~5_복승_환수액",
        "hit": "r_pop1,2_축_3~5_복승_적중",
    },
    "anchor12_3_6_quinella": {
        "bet": "1,2축_3~6_복승_베팅액",
        "refund": "1,2축_3~6_복승_환수액",
        "hit": "r_pop1,2_축_3~6_복승_적중",
    },
    "anchor12_3_7_quinella": {
        "bet": "1,2축_3~7_복승_베팅액",
        "refund": "1,2축_3~7_복승_환수액",
        "hit": "r_pop1,2_축_3~7_복승_적중",
    },
    "anchor12_3_8_quinella": {
        "bet": "1,2축_3~8_복승_베팅액",
        "refund": "1,2축_3~8_복승_환수액",
        "hit": "r_pop1,2_축_3~8_복승_적중",
    },
    "anchor12_3_12_quinella": {
        "bet": "1,2축_3~12_복승_베팅액",
        "refund": "1,2축_3~12_복승_환수액",
        "hit": "r_pop1,2_축_3~12_복승_적중",
    },
    "anchor1_24_58": {
        "bet": "1축_2~4_5~8_베팅액",
        "refund": "1축_2~4_5~8_환수액",
        "hit": "r_pop1_축_2~4_5~8_적중",
    },
    "top4_box_trifecta": {
        "bet": "1~4_4복_베팅액",
        "refund": "1~4_4복_환수액",
        "hit": "r_pop1~4_4복_적중",
    },
    "top5_box_trifecta": {
        "bet": "1~5_5복_베팅액",
        "refund": "1~5_5복_환수액",
        "hit": "r_pop1~5_5복_적중",
    },
    "top6_trio": {
        "bet": "1~6_6복조_삼복_베팅액",
        "refund": "1~6_6복조_삼복_환수액",
        "hit": "r_pop1~6_6복조_삼복_적중",
    },
    "top3pair_46_trio": {
        "bet": "1~3_복조_4~6_삼복_베팅액",
        "refund": "1~3_복조_4~6_삼복_환수액",
        "hit": "r_pop1~3_복조_4~6_삼복_적중",
    },
    "top3pair_47_trio": {
        "bet": "1~3_복조_4~7_삼복_베팅액",
        "refund": "1~3_복조_4~7_삼복_환수액",
        "hit": "r_pop1~3_복조_4~7_삼복_적중",
    },
    "top3pair_49_trio": {
        "bet": "1~3_복조_4~9_삼복_베팅액",
        "refund": "1~3_복조_4~9_삼복_환수액",
        "hit": "r_pop1~3_복조_4~9_삼복_적중",
    },
    "top4pair_58_trio": {
        "bet": "1~4_복조_5~8_삼복_베팅액",
        "refund": "1~4_복조_5~8_삼복_환수액",
        "hit": "r_pop1~4_복조_5~8_삼복_적중",
    },
    "top12anchor_3_10_trio": {
        "bet": "1~2_복조축_3~10_삼복_베팅액",
        "refund": "1~2_복조축_3~10_삼복_환수액",
        "hit": "r_pop1~2_복조축_3~10_삼복_적중",
    },
    "top12anchor_3_8_12_trio": {
        "bet": "1~2_복조축_3~8,12_삼복_베팅액",
        "refund": "1~2_복조축_3~8,12_삼복_환수액",
        "hit": "r_pop1~2_복조축_3~8,12_삼복_적중",
    },
    "top12anchor_3_12_trio": {
        "bet": "1~2_복조축_3~12_삼복_베팅액",
        "refund": "1~2_복조축_3~12_삼복_환수액",
        "hit": "r_pop1~2_복조축_3~12_삼복_적중",
    },
    "anchor1_57_24": {
        "bet": "1축_5~7_2~4_베팅액",
        "refund": "1축_5~7_2~4_환수액",
        "hit": "r_pop1_축_5~7_2~4_적중",
    },
    "anchor1_58_24": {
        "bet": "1축_5~8_2~4_베팅액",
        "refund": "1축_5~8_2~4_환수액",
        "hit": "r_pop1_축_5~8_2~4_적중",
    },
    "anchor3_24": {
        "bet": "3축_2~4_베팅액",
        "refund": "3축_2~4_환수액",
        "hit": "r_pop1_3축_2~4_적중",
    },
    "anchor2_24": {
        "bet": "2축_2~4_베팅액",
        "refund": "2축_2~4_환수액",
        "hit": "r_pop1_2축_2~4_적중",
    },
    "anchor1_24": {
        "bet": "1축_2~4_베팅액",
        "refund": "1축_2~4_환수액",
        "hit": "r_pop1_축_2~4_적중",
    },
    "anchor1_25": {
        "bet": "1축_2~5_베팅액",
        "refund": "1축_2~5_환수액",
        "hit": "r_pop1_축_2~5_적중",
    },
    "anchor1_25_68": {
        "bet": "1축_2~5_6~8_베팅액",
        "refund": "1축_2~5_6~8_환수액",
        "hit": "r_pop1_축_2~5_6~8_적중",
    },
    "anchor1_25_69": {
        "bet": "1축_2~5_6~9_베팅액",
        "refund": "1축_2~5_6~9_환수액",
        "hit": "r_pop1_축_2~5_6~9_적중",
    },
    "anchor1_69_25": {
        "bet": "1축_6~9_2~5_베팅액",
        "refund": "1축_6~9_2~5_환수액",
        "hit": "r_pop1_축_6~9_2~5_적중",
    },
    "anchor1_23_46": {
        "bet": "1축_2~3_4~6_베팅액",
        "refund": "1축_2~3_4~6_환수액",
        "hit": "r_pop1_축_2~3_4~6_적중",
    },
    "anchor1_23_47": {
        "bet": "1축_2~3_4~7_베팅액",
        "refund": "1축_2~3_4~7_환수액",
        "hit": "r_pop1_축_2~3_4~7_적중",
    },
    "anchor1_23_48": {
        "bet": "1축_2~3_4~8_베팅액",
        "refund": "1축_2~3_4~8_환수액",
        "hit": "r_pop1_축_2~3_4~8_적중",
    },
    "anchor1_23_49": {
        "bet": "1축_2~3_4~9_베팅액",
        "refund": "1축_2~3_4~9_환수액",
        "hit": "r_pop1_축_2~3_4~9_적중",
    },
    "anchor12_3_7": {
        "bet": "1축_2축_3~7_베팅액",
        "refund": "1축_2축_3~7_환수액",
        "hit": "r_pop1_1축_r_pop2_2축_3~7_적중",
    },
    "anchor12_3_10": {
        "bet": "1축_2축_3~10_베팅액",
        "refund": "1축_2축_3~10_환수액",
        "hit": "r_pop1_1축_r_pop2_2축_3~10_적중",
    },
}


def load_race_df(from_date: str = DEFAULT_FROM_DATE, to_date: str = DEFAULT_TO_DATE) -> pd.DataFrame:
    """총환수율_new.py 계산 결과를 부수효과 없이 로드한다."""
    os.environ["DJANGO_SETTINGS_MODULE"] = "letsrace.settings"
    original_upsert = base_mod.upsert_weekly_betting_summary
    original_to_csv = pd.DataFrame.to_csv
    original_excluded = base_mod.EXCLUDED_STRATEGY_KEYS
    try:
        base_mod.upsert_weekly_betting_summary = lambda *args, **kwargs: None
        pd.DataFrame.to_csv = lambda self, *args, **kwargs: None
        base_mod.EXCLUDED_STRATEGY_KEYS = set()
        with contextlib.redirect_stdout(io.StringIO()):
            race_df, _summary = base_mod.calc_rpop_anchor_26_trifecta(
                from_date=from_date,
                to_date=to_date,
                bet_unit=100,
                apply_odds_filter=False,
            )
        return race_df
    finally:
        base_mod.upsert_weekly_betting_summary = original_upsert
        pd.DataFrame.to_csv = original_to_csv
        base_mod.EXCLUDED_STRATEGY_KEYS = original_excluded


def summarize_combo(track_df: pd.DataFrame, combo_keys: tuple[str, ...]) -> dict:
    """조합별 환수 요약."""
    bet_matrix = np.vstack(
        [track_df[ALL_STRATEGY_RESULT_COLUMNS[key]["bet"]].to_numpy(dtype=float) for key in combo_keys]
    )
    refund_matrix = np.vstack(
        [track_df[ALL_STRATEGY_RESULT_COLUMNS[key]["refund"]].to_numpy(dtype=float) for key in combo_keys]
    )
    hit_matrix = np.vstack(
        [track_df[ALL_STRATEGY_RESULT_COLUMNS[key]["hit"]].to_numpy(dtype=int) for key in combo_keys]
    )
    total_bet = float(bet_matrix.sum())
    total_refund = float(refund_matrix.sum())
    hit_any = hit_matrix.max(axis=0)
    return {
        "keys": combo_keys,
        "labels": [base_mod.STRATEGY_LABELS.get(key, key) for key in combo_keys],
        "races": int(len(track_df)),
        "hit_races": int(hit_any.sum()),
        "hit_rate": (float(hit_any.sum()) / len(track_df)) if len(track_df) > 0 else 0.0,
        "bet": total_bet,
        "refund": total_refund,
        "profit": total_refund - total_bet,
        "roi": (total_refund / total_bet) if total_bet > 0 else 0.0,
    }


def get_nearest_saturday(dt: pd.Timestamp) -> pd.Timestamp:
    """기준일과 가장 가까운 토요일을 반환한다. 동일 거리면 과거 토요일 우선."""
    days_since_sat = (dt.weekday() - 5) % 7
    prev_sat = dt - pd.Timedelta(days=days_since_sat)
    next_sat = prev_sat + pd.Timedelta(days=7)
    if (dt - prev_sat) <= (next_sat - dt):
        return prev_sat
    return next_sat


def build_saturday_summary(track_df: pd.DataFrame, combo_keys: tuple[str, ...]) -> pd.DataFrame:
    """조합의 토요일 기준 집계."""
    df = track_df.copy()
    if df.empty:
        return pd.DataFrame()

    bet_cols = [ALL_STRATEGY_RESULT_COLUMNS[key]["bet"] for key in combo_keys]
    refund_cols = [ALL_STRATEGY_RESULT_COLUMNS[key]["refund"] for key in combo_keys]
    hit_cols = [ALL_STRATEGY_RESULT_COLUMNS[key]["hit"] for key in combo_keys]

    df["경주일"] = pd.to_datetime(df["경주일"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["경주일"]).copy()
    if df.empty:
        return pd.DataFrame()

    df["토요일기준일"] = df["경주일"].apply(get_nearest_saturday)
    df["적중경주수"] = df[hit_cols].fillna(0).astype(int).gt(0).any(axis=1).astype(int)
    df["총베팅액"] = df[bet_cols].fillna(0).sum(axis=1)
    df["총환수액"] = df[refund_cols].fillna(0).sum(axis=1)

    weekly = (
        df.groupby("토요일기준일", dropna=False)[["적중경주수", "총베팅액", "총환수액"]]
        .sum()
        .reset_index()
        .sort_values("토요일기준일")
    )
    if weekly.empty:
        return weekly

    race_counts = df.groupby("토요일기준일", dropna=False).size().reset_index(name="경주수")
    weekly = weekly.merge(race_counts, on="토요일기준일", how="left")
    weekly["이익금액"] = weekly["총환수액"] - weekly["총베팅액"]
    weekly["적중율"] = weekly["적중경주수"] / weekly["경주수"]
    weekly["ROI"] = weekly["총환수액"] / weekly["총베팅액"]
    weekly["토요일기준일"] = weekly["토요일기준일"].dt.strftime("%Y%m%d")
    return weekly[
        ["토요일기준일", "경주수", "적중경주수", "적중율", "총베팅액", "총환수액", "이익금액", "ROI"]
    ]


def get_track_candidate_keys(track_df: pd.DataFrame) -> list[str]:
    """해당 경마장에서 계산 가능한 전략 키."""
    candidate_keys = []
    for key, cols in ALL_STRATEGY_RESULT_COLUMNS.items():
        if all(col_name in track_df.columns for col_name in cols.values()):
            candidate_keys.append(key)
    return candidate_keys


def find_top_combos(track_df: pd.DataFrame, combo_size: int, top_n: int = DEFAULT_TOP_N) -> list[dict]:
    """경마장별 최고 ROI 조합 순위."""
    candidate_keys = get_track_candidate_keys(track_df)
    results = []
    for combo_keys in combinations(candidate_keys, combo_size):
        results.append(summarize_combo(track_df, combo_keys))
    results.sort(key=lambda item: (item["roi"], item["profit"], item["hit_rate"]), reverse=True)
    return results[:top_n]


def print_combo_result(title: str, result: dict) -> None:
    combo_keys = " + ".join(result["keys"])
    combo_labels = " + ".join(result["labels"])
    print(f"{title}: {combo_keys}")
    print(f"  전략: {combo_labels}")
    print(
        f"  ROI {result['roi']:.6f}  총베팅 {int(result['bet']):,}원  "
        f"총환수 {result['refund']:,.1f}원  이익 {result['profit']:,.1f}원  "
        f"적중율 {result['hit_rate']:.6f}"
    )


def print_validation(track_name: str, combo_size: int, result: dict) -> None:
    expected = EXPECTED_TOP_COMBOS.get(track_name, {}).get(combo_size)
    if not expected:
        return
    status = "OK" if tuple(result["keys"]) == expected else "MISMATCH"
    print(f"[검증 {track_name} {combo_size}개] {status}")
    print(f"  expected: {' + '.join(expected)}")
    print(f"  actual  : {' + '.join(result['keys'])}")


def print_saturday_summary(track_name: str, combo_size: int, track_df: pd.DataFrame, result: dict) -> None:
    weekly = build_saturday_summary(track_df, tuple(result["keys"]))
    if weekly.empty:
        return

    total_races = int(weekly["경주수"].sum())
    total_hits = int(weekly["적중경주수"].sum())
    total_bet = float(weekly["총베팅액"].sum())
    total_refund = float(weekly["총환수액"].sum())
    total_profit = total_refund - total_bet
    total_hit_rate = total_hits / total_races if total_races > 0 else 0.0
    total_roi = total_refund / total_bet if total_bet > 0 else 0.0

    print(f"[{track_name} 토요일기준 {combo_size}개 조합 소계]")
    print(
        f"  경주수 {total_races}  적중경주수 {total_hits}  적중율 {total_hit_rate:.6f}  "
        f"총베팅액 {int(total_bet):,}원  총환수액 {total_refund:,.1f}원  "
        f"이익금액 {total_profit:,.1f}원  ROI {total_roi:.6f}"
    )
    for row in weekly.itertuples(index=False):
        print(
            f"  [토요일기준 {row.토요일기준일}]  경주수 {row.경주수}  "
            f"적중경주수 {row.적중경주수}  적중율 {row.적중율:.6f}  "
            f"총베팅액 {int(row.총베팅액):,}원  총환수액 {row.총환수액:,.1f}원  "
            f"이익금액 {row.이익금액:,.1f}원  ROI {row.ROI:.6f}"
        )


def main() -> None:
    race_df = load_race_df()
    print(
        f"[기간] {DEFAULT_FROM_DATE} ~ {DEFAULT_TO_DATE}  "
        f"(총환수율_new.py 기본 규칙: 13두 이상 / 신마 3두 이상 제외)"
    )

    for track_name in TRACK_ORDER:
        track_df = race_df[race_df["경마장"] == track_name].copy()
        if track_df.empty:
            continue

        print(f"[{track_name}]")
        for combo_size in COMBO_SIZES:
            top_results = find_top_combos(track_df, combo_size=combo_size, top_n=DEFAULT_TOP_N)
            if not top_results:
                continue
            print_combo_result(f"[{combo_size}개 최고 ROI]", top_results[0])
            print_validation(track_name, combo_size, top_results[0])
            print_saturday_summary(track_name, combo_size, track_df, top_results[0])
        print()


if __name__ == "__main__":
    main()
