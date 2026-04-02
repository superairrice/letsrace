"""서울/부산 공통 주력베팅 토요일 기준 통합 현황 실행 파일."""

import pandas as pd

import 총환수율_new_주력_토요일_통합 as base_script


OUTPUT_PATH = "/Users/Super007/Documents/r_pop_total_new_주력_토요일_통합_12457_5724_124_4복삼쌍_126삼쌍.csv"
base_script.DEFAULT_OUTPUT_PATH = OUTPUT_PATH
base_script.PRIMARY_STRATEGY_KEYS_BY_TRACK = {
    "서울": [
        "anchor1_24_57",
        "anchor1_57_24",
        "anchor1_24",
        "anchor1_26",
        "top4_box_trifecta",
    ],
    "부산": [
        "anchor1_24_57",
        "anchor1_57_24",
        "anchor1_24",
        "anchor1_26",
        "top4_box_trifecta",
    ],
}
base_script.ALLOWED_TRACKS = set(base_script.PRIMARY_STRATEGY_KEYS_BY_TRACK.keys())
base_script.STRATEGY_RESULT_COLUMNS = {
    **base_script.STRATEGY_RESULT_COLUMNS,
    "anchor1_24_57": {
        "bet": "1축_2~4_5~7_베팅액",
        "refund": "1축_2~4_5~7_환수액",
        "hit": "r_pop1_축_2~4_5~7_적중",
    },
    "anchor1_26": {
        "bet": "1축_2~6_삼쌍_베팅액",
        "refund": "1축_2~6_삼쌍_환수액",
        "hit": "r_pop1_축_2~6_삼쌍_적중",
    },
}

_original_calc_rpop_anchor_26_trifecta = base_script.base_mod.calc_rpop_anchor_26_trifecta
_original_save_weekly_df = base_script.save_weekly_df


def _parse_gate_list(value) -> list[int]:
    if pd.isna(value):
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, (list, tuple, set)):
        parts = list(value)
    else:
        parts = [value]
    parsed: list[int] = []
    for part in parts:
        try:
            parsed.append(int(part))
        except (TypeError, ValueError):
            continue
    return parsed


def _augment_anchor1_26_trifecta(race_df: pd.DataFrame, bet_unit: int = 100) -> pd.DataFrame:
    if race_df.empty:
        return race_df
    if "r_pop1_축_2~6_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 20 * bet_unit  # 5P2

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor_list = _parse_gate_list(row.get("축마"))
        anchor_gate = anchor_list[0] if anchor_list else None
        top2_6 = _parse_gate_list(row.get("2~6_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        valid = anchor_gate is not None and len(top2_6) == 5
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_6
            and actual_top3[2] in top2_6
            and actual_top3[1] != actual_top3[2]
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_축_2~6_삼쌍_적중": hit,
                "r_pop1_축_2~6_삼쌍_환수액": refund,
                "1축_2~6_삼쌍_베팅액": bet,
                "1축_2~6_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _calc_with_anchor1_26_trifecta(*args, **kwargs):
    race_df, summary = _original_calc_rpop_anchor_26_trifecta(*args, **kwargs)
    bet_unit = kwargs.get("bet_unit", 100)
    race_df = _augment_anchor1_26_trifecta(race_df, bet_unit=bet_unit)
    return race_df, summary


def _save_weekly_df_with_output_path(weekly_df: pd.DataFrame, output_path: str = OUTPUT_PATH) -> None:
    _original_save_weekly_df(weekly_df, output_path=output_path)


def main() -> None:
    base_script.base_mod.calc_rpop_anchor_26_trifecta = _calc_with_anchor1_26_trifecta
    base_script.save_weekly_df = _save_weekly_df_with_output_path
    base_script.main()


if __name__ == "__main__":
    main()
