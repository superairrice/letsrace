"""서울 추천 조합 전용 r_pop 환수율 집계 실행 파일."""

import pandas as pd

import 총환수율_new as base_mod


TRACK_NAME = "서울"
DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260330"
DEFAULT_OUTPUT_PATH = "/Users/Super007/Documents/r_pop_total_new_서울_추천조합.csv"
PRIMARY_STRATEGY_KEYS = [
    "anchor1_25",
    "anchor1_23_46",
    "anchor1_23_47",
    "anchor1_23_48",
]
SUPPORT_STRATEGY_KEYS = [
    "anchor1_24_58",
    "anchor1_58_24",
]
ALLOWED_STRATEGY_KEYS = {
    *PRIMARY_STRATEGY_KEYS,
    *SUPPORT_STRATEGY_KEYS,
}


_base_load_result_data_from_db = base_mod.load_result_data_from_db


def load_result_data_from_db(engine, from_date: str, to_date: str) -> pd.DataFrame:
    """원본 로더 결과에서 서울 경주만 남긴다."""
    df = _base_load_result_data_from_db(engine, from_date=from_date, to_date=to_date)
    if df.empty:
        return df
    return df[df["경마장"] == TRACK_NAME].copy()


def save_race_df(race_df: pd.DataFrame, output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """경주별 결과를 서울 추천 조합 CSV로 저장한다."""
    if race_df.empty:
        return
    race_df = race_df.drop_duplicates(subset=["경마장", "경주일", "경주번호"])
    race_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"▶ {TRACK_NAME} 추천 조합 경주별 raw 데이터 CSV 저장: {output_path}")


def calculate_group_stats(race_df: pd.DataFrame, strategy_keys: list) -> dict:
    """전략 묶음 단위 소계 계산."""
    bet_cols = [base_mod.STRATEGY_RESULT_COLUMNS[key]["bet"] for key in strategy_keys]
    refund_cols = [base_mod.STRATEGY_RESULT_COLUMNS[key]["refund"] for key in strategy_keys]
    hit_cols = [base_mod.STRATEGY_RESULT_COLUMNS[key]["hit"] for key in strategy_keys]

    total_bet = float(race_df[bet_cols].sum().sum())
    total_refund = float(race_df[refund_cols].sum().sum())
    hit_races = int((race_df[hit_cols].sum(axis=1) > 0).sum())
    total_races = len(race_df)
    profit = total_refund - total_bet
    refund_rate = total_refund / total_bet if total_bet > 0 else 0.0
    hit_rate = hit_races / total_races if total_races > 0 else 0.0
    return {
        "total_races": total_races,
        "hit_races": hit_races,
        "hit_rate": hit_rate,
        "total_bet": total_bet,
        "total_refund": total_refund,
        "profit": profit,
        "refund_rate": refund_rate,
    }


def print_primary_summary(race_df: pd.DataFrame) -> None:
    """최상단 주력베팅 요약 출력."""
    if race_df.empty:
        return
    stats = calculate_group_stats(race_df, PRIMARY_STRATEGY_KEYS)
    print("[주력베팅 결과]")
    print(
        f"경주수: {stats['total_races']}  적중경주수: {stats['hit_races']}  "
        f"적중율: {stats['hit_rate']:.3f}  총베팅액: {int(stats['total_bet']):,}원  "
        f"총환수액: {stats['total_refund']:,.1f}원  이익금액: {stats['profit']:,.1f}원  "
        f"환수율: {stats['refund_rate']:.3f}"
    )


def print_group_summary(
    race_df: pd.DataFrame,
    group_label: str,
    strategy_keys: list,
) -> None:
    """전략 묶음 단위로 환수율/적중율을 출력한다."""
    if race_df.empty:
        return

    stats = calculate_group_stats(race_df, strategy_keys)
    total_races = stats["total_races"]
    strategy_names = ", ".join(base_mod.STRATEGY_LABELS[key] for key in strategy_keys)

    print(f"[{group_label}] {strategy_names}")
    print(
        f"경주수: {total_races}  적중경주수: {stats['hit_races']}  "
        f"적중율: {stats['hit_rate']:.3f}  총베팅액: {int(stats['total_bet']):,}원  "
        f"총환수액: {stats['total_refund']:,.1f}원  이익금액: {stats['profit']:,.1f}원  "
        f"환수율: {stats['refund_rate']:.3f}"
    )
    for key in strategy_keys:
        bet_col = base_mod.STRATEGY_RESULT_COLUMNS[key]["bet"]
        refund_col = base_mod.STRATEGY_RESULT_COLUMNS[key]["refund"]
        hit_col = base_mod.STRATEGY_RESULT_COLUMNS[key]["hit"]
        bet_amount = float(race_df[bet_col].sum())
        refund_amount = float(race_df[refund_col].sum())
        hit_count = int(race_df[hit_col].sum())
        strategy_profit = refund_amount - bet_amount
        strategy_refund_rate = refund_amount / bet_amount if bet_amount > 0 else 0.0
        strategy_hit_rate = hit_count / total_races if total_races > 0 else 0.0
        print(
            f"  {base_mod.STRATEGY_LABELS[key]}  "
            f"적중율: {strategy_hit_rate:.3f}  "
            f"총베팅액: {int(bet_amount):,}원  "
            f"총환수액: {refund_amount:,.1f}원  "
            f"이익금액: {strategy_profit:,.1f}원  "
            f"환수율: {strategy_refund_rate:.3f}"
        )
    print(
        f"  [소계] 적중경주수: {stats['hit_races']}  적중율: {stats['hit_rate']:.3f}  "
        f"총베팅액: {int(stats['total_bet']):,}원  총환수액: {stats['total_refund']:,.1f}원  "
        f"이익금액: {stats['profit']:,.1f}원  환수율: {stats['refund_rate']:.3f}"
    )


def main() -> None:
    """서울 추천 조합 전용 집계를 실행한다."""
    base_mod.load_result_data_from_db = load_result_data_from_db
    base_mod.STRATEGY_TRACK_SECTION_LABEL = "[베팅방법별]"
    base_mod.SHOW_TRACK_NAME_IN_STRATEGY_SECTION = False
    base_mod.COMBINE_STRATEGY_AND_TRACK_LINE = True
    base_mod.SHOW_MONTHLY_STRATEGY_OUTPUT = False
    base_mod.EXCLUDED_STRATEGY_KEYS = (
        set(base_mod.STRATEGY_LABELS.keys()) - ALLOWED_STRATEGY_KEYS
    )
    race_df, _summary = base_mod.calc_rpop_anchor_26_trifecta(
        from_date=DEFAULT_FROM_DATE,
        to_date=DEFAULT_TO_DATE,
        bet_unit=100,
        apply_odds_filter=False,
    )
    print_primary_summary(race_df)
    print_group_summary(race_df, "주력베팅 집계", PRIMARY_STRATEGY_KEYS)
    print_group_summary(race_df, "보조베팅 집계", SUPPORT_STRATEGY_KEYS)
    save_race_df(race_df)


get_engine = base_mod.get_engine
upsert_weekly_betting_summary = base_mod.upsert_weekly_betting_summary
calc_rpop_anchor_26_trifecta = base_mod.calc_rpop_anchor_26_trifecta


if __name__ == "__main__":
    main()
