"""부산 주력베팅 토요일 기준 적중/환수 현황 실행 파일."""

import pandas as pd

import 총환수율_new as base_mod


TRACK_NAME = "부산"
DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260330"
DEFAULT_OUTPUT_PATH = "/Users/Super007/Documents/r_pop_total_new_부산_주력_토요일.csv"
PRIMARY_STRATEGY_KEYS = [
    "anchor1_24_58",
    "anchor1_58_24",
    "anchor1_25",
    "anchor12_3_7",
    "top4_box_trifecta",
]


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
    """원본 로더 결과에서 부산 경주만 남긴다."""
    df = _base_load_result_data_from_db(engine, from_date=from_date, to_date=to_date)
    if df.empty:
        return df
    return df[df["경마장"] == TRACK_NAME].copy()


def build_saturday_primary_summary(race_df: pd.DataFrame) -> pd.DataFrame:
    """부산 주력베팅을 토요일 기준으로 묶어 적중/환수 현황을 만든다."""
    if race_df.empty:
        return pd.DataFrame()

    bet_cols = [base_mod.STRATEGY_RESULT_COLUMNS[key]["bet"] for key in PRIMARY_STRATEGY_KEYS]
    refund_cols = [base_mod.STRATEGY_RESULT_COLUMNS[key]["refund"] for key in PRIMARY_STRATEGY_KEYS]
    hit_cols = [base_mod.STRATEGY_RESULT_COLUMNS[key]["hit"] for key in PRIMARY_STRATEGY_KEYS]

    df = race_df.copy()
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

    race_counts = (
        df.groupby("토요일기준일", dropna=False)
        .size()
        .reset_index(name="경주수")
    )
    weekly = weekly.merge(race_counts, on="토요일기준일", how="left")
    weekly["이익금액"] = weekly["총환수액"] - weekly["총베팅액"]
    weekly["적중율"] = weekly["적중경주"] / weekly["경주수"]
    weekly["환수율"] = weekly["총환수액"] / weekly["총베팅액"]
    weekly["토요일기준일"] = weekly["토요일기준일"].dt.strftime("%Y%m%d")
    weekly = weekly.rename(columns={"적중경주": "적중경주수"})
    return weekly[
        ["토요일기준일", "경주수", "적중경주수", "적중율", "총베팅액", "총환수액", "이익금액", "환수율"]
    ]


def print_saturday_primary_summary(weekly_df: pd.DataFrame) -> None:
    """토요일 기준 주력베팅 현황 출력."""
    print(f"[{TRACK_NAME} 주력베팅 토요일 기준 적중/환수 현황]")
    if weekly_df.empty:
        print("데이터가 없습니다.")
        return
    for row in weekly_df.itertuples(index=False):
        print(
            f"[토요일기준 {row.토요일기준일}]  경주수: {row.경주수}  "
            f"적중경주수: {row.적중경주수}  적중율: {row.적중율:.3f}  "
            f"총베팅액: {int(row.총베팅액):,}원  총환수액: {row.총환수액:,.1f}원  "
            f"이익금액: {row.이익금액:,.1f}원  환수율: {row.환수율:.3f}"
        )


def save_weekly_df(weekly_df: pd.DataFrame, output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """토요일 기준 부산 주력베팅 현황 CSV 저장."""
    if weekly_df.empty:
        return
    weekly_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"▶ {TRACK_NAME} 주력베팅 토요일 기준 CSV 저장: {output_path}")


def main() -> None:
    """부산 주력베팅 토요일 기준 집계를 실행한다."""
    base_mod.load_result_data_from_db = load_result_data_from_db
    base_mod.EXCLUDED_STRATEGY_KEYS = set(base_mod.STRATEGY_LABELS.keys()) - set(PRIMARY_STRATEGY_KEYS)
    race_df, _summary = base_mod.calc_rpop_anchor_26_trifecta(
        from_date=DEFAULT_FROM_DATE,
        to_date=DEFAULT_TO_DATE,
        bet_unit=100,
        apply_odds_filter=False,
    )
    weekly_df = build_saturday_primary_summary(race_df)
    print_saturday_primary_summary(weekly_df)
    save_weekly_df(weekly_df)


if __name__ == "__main__":
    main()
