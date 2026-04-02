"""서울/부산 보조베팅 토요일 기준 통합 적중/환수 현황 실행 파일."""

import contextlib
import io
import os
import pandas as pd

import 총환수율_new as base_mod


DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260330"
DEFAULT_OUTPUT_PATH = "/Users/Super007/Documents/r_pop_total_new_보조_토요일_통합.csv"
SUPPORT_STRATEGY_KEYS_BY_TRACK = {
    "서울": [
        "anchor1_24_57",
        "anchor1_57_24",
        "anchor1_58_24",
        "anchor1_24",
    ],
    "부산": [
        "top4_box_trifecta",
        "anchor1_57_24",
        "anchor1_69_25",
        "anchor1_23_47",
    ],
}
ALLOWED_TRACKS = set(SUPPORT_STRATEGY_KEYS_BY_TRACK.keys())
STRATEGY_RESULT_COLUMNS = {
    **base_mod.STRATEGY_RESULT_COLUMNS,
    "anchor1_24_57": {
        "bet": "1축_2~4_5~7_베팅액",
        "refund": "1축_2~4_5~7_환수액",
        "hit": "r_pop1_축_2~4_5~7_적중",
    },
    "anchor1_57_24": {
        "bet": "1축_5~7_2~4_베팅액",
        "refund": "1축_5~7_2~4_환수액",
        "hit": "r_pop1_축_5~7_2~4_적중",
    },
    "anchor1_24": {
        "bet": "1축_2~4_베팅액",
        "refund": "1축_2~4_환수액",
        "hit": "r_pop1_축_2~4_적중",
    },
    "anchor1_69_25": {
        "bet": "1축_6~9_2~5_베팅액",
        "refund": "1축_6~9_2~5_환수액",
        "hit": "r_pop1_축_6~9_2~5_적중",
    },
    "anchor2_24": {
        "bet": "2축_2~4_베팅액",
        "refund": "2축_2~4_환수액",
        "hit": "r_pop1_2축_2~4_적중",
    },
}


_base_load_result_data_from_db = base_mod.load_result_data_from_db


def get_nearest_saturday(dt: pd.Timestamp) -> pd.Timestamp:
    """기준일과 가장 가까운 토요일을 반환한다. 동일 거리면 과거 토요일 우선."""
    days_since_sat = (dt.weekday() - 5) % 7
    prev_sat = dt - pd.Timedelta(days=days_since_sat)
    next_sat = prev_sat + pd.Timedelta(days=7)
    if (dt - prev_sat) <= (next_sat - dt):
        return prev_sat
    return next_sat


def load_result_data_from_db(engine, from_date: str, to_date: str) -> pd.DataFrame:
    """원본 로더 결과에서 서울/부산 경주만 남긴다."""
    df = _base_load_result_data_from_db(engine, from_date=from_date, to_date=to_date)
    if df.empty:
        return df
    return df[df["경마장"].isin(ALLOWED_TRACKS)].copy()


def build_track_weekly_summary(race_df: pd.DataFrame, track_name: str) -> pd.DataFrame:
    """경마장별 보조베팅 토요일 기준 적중/환수 현황을 만든다."""
    if race_df.empty:
        return pd.DataFrame()

    strategy_keys = SUPPORT_STRATEGY_KEYS_BY_TRACK[track_name]
    bet_cols = [STRATEGY_RESULT_COLUMNS[key]["bet"] for key in strategy_keys]
    refund_cols = [STRATEGY_RESULT_COLUMNS[key]["refund"] for key in strategy_keys]
    hit_cols = [STRATEGY_RESULT_COLUMNS[key]["hit"] for key in strategy_keys]

    df = race_df[race_df["경마장"] == track_name].copy()
    if df.empty:
        return pd.DataFrame()

    df["경주일"] = pd.to_datetime(df["경주일"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["경주일"]).copy()
    df["토요일기준일"] = df["경주일"].apply(get_nearest_saturday)
    df["적중경주"] = df[hit_cols].fillna(0).astype(int).gt(0).any(axis=1).astype(int)
    df["총베팅액"] = df[bet_cols].fillna(0).sum(axis=1)
    df["총환수액"] = df[refund_cols].fillna(0).sum(axis=1)

    weekly = (
        df.groupby("토요일기준일", dropna=False)[["적중경주", "총베팅액", "총환수액"]]
        .sum()
        .reset_index()
        .sort_values("토요일기준일")
    )
    weekly = weekly[weekly["총베팅액"] > 0].copy()
    if weekly.empty:
        return weekly

    race_counts = df.groupby("토요일기준일", dropna=False).size().reset_index(name="경주수")
    weekly = weekly.merge(race_counts, on="토요일기준일", how="left")
    weekly["이익금액"] = weekly["총환수액"] - weekly["총베팅액"]
    weekly["적중율"] = weekly["적중경주"] / weekly["경주수"]
    weekly["환수율"] = weekly["총환수액"] / weekly["총베팅액"]
    weekly["토요일기준일"] = weekly["토요일기준일"].dt.strftime("%Y%m%d")
    weekly["경마장"] = track_name
    weekly = weekly.rename(columns={"적중경주": "적중경주수"})
    return weekly[
        ["경마장", "토요일기준일", "경주수", "적중경주수", "적중율", "총베팅액", "총환수액", "이익금액", "환수율"]
    ]


def build_combined_weekly_summary(race_df: pd.DataFrame) -> pd.DataFrame:
    """서울/부산 보조베팅 토요일 기준 통합 현황을 만든다."""
    frames = []
    for track_name in ["서울", "부산"]:
        weekly = build_track_weekly_summary(race_df, track_name)
        if not weekly.empty:
            frames.append(weekly)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def print_combined_weekly_summary(weekly_df: pd.DataFrame) -> None:
    """서울/부산 통합 토요일 기준 현황 출력."""
    print("[서울/부산 보조베팅 토요일 기준 통합 적중/환수 현황]")
    if weekly_df.empty:
        print("데이터가 없습니다.")
        return

    for track_name in ["서울", "부산"]:
        track_df = weekly_df[weekly_df["경마장"] == track_name].copy()
        if track_df.empty:
            continue
        print(f"[{track_name}]")
        for row in track_df.itertuples(index=False):
            print(
                f"[토요일기준 {row.토요일기준일}]  경주수: {row.경주수}  "
                f"적중경주수: {row.적중경주수}  적중율: {row.적중율:.3f}  "
                f"총베팅액: {int(row.총베팅액):,}원  총환수액: {row.총환수액:,.1f}원  "
                f"이익금액: {row.이익금액:,.1f}원  환수율: {row.환수율:.3f}"
            )

    summary = (
        weekly_df.groupby("토요일기준일", dropna=False)[["경주수", "적중경주수", "총베팅액", "총환수액", "이익금액"]]
        .sum()
        .reset_index()
        .sort_values("토요일기준일")
    )
    summary["적중율"] = summary["적중경주수"] / summary["경주수"]
    summary["환수율"] = summary["총환수액"] / summary["총베팅액"]

    print("[통합]")
    for row in summary.itertuples(index=False):
        print(
            f"[토요일기준 {row.토요일기준일}]  경주수: {row.경주수}  "
            f"적중경주수: {row.적중경주수}  적중율: {row.적중율:.3f}  "
            f"총베팅액: {int(row.총베팅액):,}원  총환수액: {row.총환수액:,.1f}원  "
            f"이익금액: {row.이익금액:,.1f}원  환수율: {row.환수율:.3f}"
        )


def save_weekly_df(weekly_df: pd.DataFrame, output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """서울/부산 통합 토요일 기준 현황 CSV 저장."""
    if weekly_df.empty:
        return
    weekly_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"▶ 서울/부산 보조베팅 토요일 기준 통합 CSV 저장: {output_path}")


def main() -> None:
    """서울/부산 보조베팅 토요일 기준 통합 집계를 실행한다."""
    os.environ["DJANGO_SETTINGS_MODULE"] = "letsrace.settings"
    base_mod.load_result_data_from_db = load_result_data_from_db
    allowed_strategy_keys = {
        key
        for strategy_keys in SUPPORT_STRATEGY_KEYS_BY_TRACK.values()
        for key in strategy_keys
    }
    base_mod.EXCLUDED_STRATEGY_KEYS = set(base_mod.STRATEGY_LABELS.keys()) - allowed_strategy_keys
    original_upsert = base_mod.upsert_weekly_betting_summary
    original_to_csv = pd.DataFrame.to_csv
    try:
        base_mod.upsert_weekly_betting_summary = lambda *args, **kwargs: None
        pd.DataFrame.to_csv = lambda self, *args, **kwargs: None
        with contextlib.redirect_stdout(io.StringIO()):
            race_df, _summary = base_mod.calc_rpop_anchor_26_trifecta(
                from_date=DEFAULT_FROM_DATE,
                to_date=DEFAULT_TO_DATE,
                bet_unit=100,
                apply_odds_filter=False,
            )
    finally:
        base_mod.upsert_weekly_betting_summary = original_upsert
        pd.DataFrame.to_csv = original_to_csv
    weekly_df = build_combined_weekly_summary(race_df)
    print_combined_weekly_summary(weekly_df)
    save_weekly_df(weekly_df)


if __name__ == "__main__":
    main()
