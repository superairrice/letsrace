"""부산 전용 r_pop 환수율 집계 실행 파일."""

import pandas as pd

import 총환수율_new as base_mod


TRACK_NAME = "부산"
DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260330"
DEFAULT_OUTPUT_PATH = "/Users/Super007/Documents/r_pop_total_new_부산.csv"


_base_load_result_data_from_db = base_mod.load_result_data_from_db


def load_result_data_from_db(engine, from_date: str, to_date: str) -> pd.DataFrame:
    """원본 로더 결과에서 부산 경주만 남긴다."""
    df = _base_load_result_data_from_db(engine, from_date=from_date, to_date=to_date)
    if df.empty:
        return df
    return df[df["경마장"] == TRACK_NAME].copy()


def save_race_df(race_df: pd.DataFrame, output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """경주별 결과를 부산 전용 CSV로 저장한다."""
    if race_df.empty:
        return
    race_df = race_df.drop_duplicates(subset=["경마장", "경주일", "경주번호"])
    race_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"▶ {TRACK_NAME} 경주별 raw 데이터 CSV 저장: {output_path}")


def main() -> None:
    """부산 전용 집계를 실행한다."""
    base_mod.load_result_data_from_db = load_result_data_from_db
    base_mod.STRATEGY_TRACK_SECTION_LABEL = "[베팅방법별]"
    base_mod.SHOW_TRACK_NAME_IN_STRATEGY_SECTION = False
    base_mod.COMBINE_STRATEGY_AND_TRACK_LINE = True
    base_mod.SHOW_MONTHLY_STRATEGY_OUTPUT = False
    base_mod.EXCLUDED_STRATEGY_KEYS = {
        "anchor1_24_quinella",
        "anchor1_26_quinella",
        "top3pair_46_quinella",
        "anchor12_3_4_quinella",
        "anchor12_3_5_quinella",
        "anchor12_3_6_quinella",
        "anchor12_3_7_quinella",
        "anchor12_3_8_quinella",
        "anchor12_3_12_quinella",
        "anchor1_24_57",
        "top4_box_trifecta",
        "top12anchor_3_10_trio",
        "top12anchor_3_12_trio",
        "anchor3_24",
        "anchor2_24",
        "anchor1_25_68",
        "anchor1_25_69",
        "anchor1_69_25",
        "anchor12_3_10",
    }
    race_df, _summary = base_mod.calc_rpop_anchor_26_trifecta(
        from_date=DEFAULT_FROM_DATE,
        to_date=DEFAULT_TO_DATE,
        bet_unit=100,
        apply_odds_filter=False,
    )
    base_mod.print_saturday_combo_backtest(
        race_df, section_title=f"[{TRACK_NAME} 토요일 기준 전략 조합 백테스트]"
    )
    base_mod.print_saturday_combo_optimizer(
        race_df, section_title=f"[{TRACK_NAME} 토요일 기준 최적 조합 탐색]"
    )
    save_race_df(race_df)


get_engine = base_mod.get_engine
upsert_weekly_betting_summary = base_mod.upsert_weekly_betting_summary
calc_rpop_anchor_26_trifecta = base_mod.calc_rpop_anchor_26_trifecta


if __name__ == "__main__":
    main()
