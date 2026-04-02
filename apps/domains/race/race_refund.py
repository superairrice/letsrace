import pandas as pd

from base import 총환수율_new as base_mod


STRATEGY_TRACK_SECTION_LABEL = base_mod.STRATEGY_TRACK_SECTION_LABEL
SHOW_TRACK_NAME_IN_STRATEGY_SECTION = base_mod.SHOW_TRACK_NAME_IN_STRATEGY_SECTION
COMBINE_STRATEGY_AND_TRACK_LINE = base_mod.COMBINE_STRATEGY_AND_TRACK_LINE
SHOW_MONTHLY_STRATEGY_OUTPUT = base_mod.SHOW_MONTHLY_STRATEGY_OUTPUT
STRATEGY_RESULT_COLUMNS = base_mod.STRATEGY_RESULT_COLUMNS
STRATEGY_LABELS = base_mod.STRATEGY_LABELS
SATURDAY_COMBO_PRESETS = base_mod.SATURDAY_COMBO_PRESETS


def __getattr__(name):
    if name == "EXCLUDED_STRATEGY_KEYS":
        return base_mod.EXCLUDED_STRATEGY_KEYS
    raise AttributeError(name)


def get_engine():
    return base_mod.get_engine()


def load_result_data_from_db(
    engine,
    from_date: str,
    to_date: str,
) -> pd.DataFrame:
    return base_mod.load_result_data_from_db(
        engine,
        from_date=from_date,
        to_date=to_date,
    )


def upsert_weekly_betting_summary(engine, week_df: pd.DataFrame) -> None:
    base_mod.upsert_weekly_betting_summary(engine, week_df)


def calc_rpop_anchor_26_trifecta(
    from_date: str,
    to_date: str,
    bet_unit: int = 100,
    apply_odds_filter: bool = False,
) -> tuple[pd.DataFrame, dict]:
    return base_mod.calc_rpop_anchor_26_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=bet_unit,
        apply_odds_filter=apply_odds_filter,
    )


if __name__ == "__main__":
    from_date = "20260116"
    to_date = "20260118"

    race_df, summary = calc_rpop_anchor_26_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,
        apply_odds_filter=False,
    )
    print(summary)
