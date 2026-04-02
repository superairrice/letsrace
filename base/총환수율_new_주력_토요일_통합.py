"""서울/부산 주력베팅 토요일 기준 통합 적중/환수 현황 실행 파일."""

import contextlib
import io
import os
import pandas as pd

import 총환수율_new as base_mod


DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260318"
DEFAULT_OUTPUT_PATH = "/Users/Super007/Documents/r_pop_total_new_주력_토요일_통합.csv"
PRIMARY_STRATEGY_KEYS_BY_TRACK = {
    "서울": [
        "anchor1_25",
        "anchor1_23_46",
        "anchor1_23_47",
        "anchor1_23_48",
    ],
    "부산": [
        "anchor3_24",
        "anchor1_24",
        "anchor1_23_46",
        "anchor12_3_7",
    ],
}
ALLOWED_TRACKS = set(PRIMARY_STRATEGY_KEYS_BY_TRACK.keys())
STRATEGY_RESULT_COLUMNS = {
    **base_mod.STRATEGY_RESULT_COLUMNS,
    "anchor1_24": {
        "bet": "1축_2~4_베팅액",
        "refund": "1축_2~4_환수액",
        "hit": "r_pop1_축_2~4_적중",
    },
    "anchor1_57_24": {
        "bet": "1축_5~7_2~4_베팅액",
        "refund": "1축_5~7_2~4_환수액",
        "hit": "r_pop1_축_5~7_2~4_적중",
    },
    "anchor3_24": {
        "bet": "3축_2~4_베팅액",
        "refund": "3축_2~4_환수액",
        "hit": "r_pop1_3축_2~4_적중",
    },
    "anchor1_69_25": {
        "bet": "1축_6~9_2~5_베팅액",
        "refund": "1축_6~9_2~5_환수액",
        "hit": "r_pop1_축_6~9_2~5_적중",
    },
}
STRATEGY_LABELS = {
    **base_mod.STRATEGY_LABELS,
    "anchor1_24": "1축(2~4) 삼쌍",
    "anchor1_57_24": "1축(5~7) / 2~4 삼쌍",
    "anchor3_24": "1을 3축 / 2~4를 1~2축 삼쌍",
    "anchor1_69_25": "1축(6~9) / 2~5 삼쌍",
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
    """경마장별 주력베팅 토요일 기준 적중/환수 현황을 만든다."""
    if race_df.empty:
        return pd.DataFrame()

    strategy_keys = PRIMARY_STRATEGY_KEYS_BY_TRACK[track_name]
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
    """서울/부산 주력베팅 토요일 기준 통합 현황을 만든다."""
    frames = []
    for track_name in ["서울", "부산"]:
        weekly = build_track_weekly_summary(race_df, track_name)
        if not weekly.empty:
            frames.append(weekly)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_track_monthly_summary(race_df: pd.DataFrame, track_name: str) -> pd.DataFrame:
    """경마장별 주력베팅 월별 적중/환수 현황을 만든다."""
    if race_df.empty:
        return pd.DataFrame()

    strategy_keys = PRIMARY_STRATEGY_KEYS_BY_TRACK[track_name]
    bet_cols = [STRATEGY_RESULT_COLUMNS[key]["bet"] for key in strategy_keys]
    refund_cols = [STRATEGY_RESULT_COLUMNS[key]["refund"] for key in strategy_keys]
    hit_cols = [STRATEGY_RESULT_COLUMNS[key]["hit"] for key in strategy_keys]

    df = race_df[race_df["경마장"] == track_name].copy()
    if df.empty:
        return pd.DataFrame()

    df["경주일"] = pd.to_datetime(df["경주일"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["경주일"]).copy()
    df["년월"] = df["경주일"].dt.strftime("%Y%m")
    df["적중경주"] = df[hit_cols].fillna(0).astype(int).gt(0).any(axis=1).astype(int)
    df["총베팅액"] = df[bet_cols].fillna(0).sum(axis=1)
    df["총환수액"] = df[refund_cols].fillna(0).sum(axis=1)

    monthly = (
        df.groupby("년월", dropna=False)[["적중경주", "총베팅액", "총환수액"]]
        .sum()
        .reset_index()
        .sort_values("년월")
    )
    monthly = monthly[monthly["총베팅액"] > 0].copy()
    if monthly.empty:
        return monthly

    race_counts = df.groupby("년월", dropna=False).size().reset_index(name="경주수")
    monthly = monthly.merge(race_counts, on="년월", how="left")
    monthly["이익금액"] = monthly["총환수액"] - monthly["총베팅액"]
    monthly["적중율"] = monthly["적중경주"] / monthly["경주수"]
    monthly["환수율"] = monthly["총환수액"] / monthly["총베팅액"]
    monthly["경마장"] = track_name
    monthly = monthly.rename(columns={"적중경주": "적중경주수"})
    return monthly[
        ["경마장", "년월", "경주수", "적중경주수", "적중율", "총베팅액", "총환수액", "이익금액", "환수율"]
    ]


def build_combined_monthly_summary(race_df: pd.DataFrame) -> pd.DataFrame:
    """서울/부산 주력베팅 월별 통합 현황을 만든다."""
    frames = []
    for track_name in ["서울", "부산"]:
        monthly = build_track_monthly_summary(race_df, track_name)
        if not monthly.empty:
            frames.append(monthly)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_track_method_summary(race_df: pd.DataFrame, track_name: str) -> pd.DataFrame:
    """경마장별 주력 베팅방법 환수율/적중율 집계를 만든다."""
    if race_df.empty:
        return pd.DataFrame()

    df = race_df[race_df["경마장"] == track_name].copy()
    if df.empty:
        return pd.DataFrame()

    total_races = len(df)
    rows = []
    for key in PRIMARY_STRATEGY_KEYS_BY_TRACK[track_name]:
        meta = STRATEGY_RESULT_COLUMNS.get(key, {})
        bet_col = meta.get("bet")
        refund_col = meta.get("refund")
        hit_col = meta.get("hit")
        if not bet_col or not refund_col or not hit_col:
            continue
        if bet_col not in df.columns or refund_col not in df.columns or hit_col not in df.columns:
            continue

        total_bet = float(df[bet_col].fillna(0).sum())
        total_refund = float(df[refund_col].fillna(0).sum())
        hits = int(df[hit_col].fillna(0).astype(int).gt(0).sum())
        rows.append(
            {
                "경마장": track_name,
                "전략키": key,
                "베팅방법": STRATEGY_LABELS.get(key, key),
                "경주수": total_races,
                "적중경주수": hits,
                "적중율": (hits / total_races) if total_races > 0 else 0.0,
                "총베팅액": total_bet,
                "총환수액": total_refund,
                "이익금액": total_refund - total_bet,
                "환수율": (total_refund / total_bet) if total_bet > 0 else 0.0,
            }
        )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["경마장", "환수율"], ascending=[True, False]).reset_index(drop=True)


def build_combined_method_summary(race_df: pd.DataFrame) -> pd.DataFrame:
    """서울/부산 주력 베팅방법 환수율/적중율 통합 집계를 만든다."""
    frames = []
    for track_name in ["서울", "부산"]:
        method_df = build_track_method_summary(race_df, track_name)
        if not method_df.empty:
            frames.append(method_df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_track_rpop_rank_summary(raw_df: pd.DataFrame, race_df: pd.DataFrame, track_name: str) -> pd.DataFrame:
    """경마장별 r_pop 1~12의 실제 1/2/3위 비율을 만든다."""
    if race_df.empty or raw_df.empty:
        return pd.DataFrame()

    included_races = race_df[race_df["경마장"] == track_name][["경마장", "경주일", "경주번호"]].drop_duplicates()
    if included_races.empty:
        return pd.DataFrame()

    df = raw_df[raw_df["경마장"] == track_name].copy()
    if df.empty:
        return pd.DataFrame()

    df = df.merge(included_races, on=["경마장", "경주일", "경주번호"], how="inner")
    if df.empty:
        return pd.DataFrame()

    df["r_pop"] = pd.to_numeric(df["r_pop"], errors="coerce")
    df["r_rank"] = pd.to_numeric(df["r_rank"], errors="coerce")
    df = df[df["r_pop"].between(1, 12)].copy()
    if df.empty:
        return pd.DataFrame()

    summary_rows = []
    for r_pop in range(1, 13):
        pop_df = df[df["r_pop"] == r_pop].copy()
        entries = len(pop_df)
        if entries == 0:
            summary_rows.append(
                {
                    "경마장": track_name,
                    "r_pop": r_pop,
                    "건수": 0,
                    "1위건수": 0,
                    "1위율": 0.0,
                    "2위건수": 0,
                    "2위율": 0.0,
                    "3위건수": 0,
                    "3위율": 0.0,
                }
            )
            continue

        rank1_hits = int((pop_df["r_rank"] == 1).sum())
        rank2_hits = int((pop_df["r_rank"] == 2).sum())
        rank3_hits = int((pop_df["r_rank"] == 3).sum())
        summary_rows.append(
            {
                "경마장": track_name,
                "r_pop": r_pop,
                "건수": entries,
                "1위건수": rank1_hits,
                "1위율": rank1_hits / entries,
                "2위건수": rank2_hits,
                "2위율": rank2_hits / entries,
                "3위건수": rank3_hits,
                "3위율": rank3_hits / entries,
            }
        )

    return pd.DataFrame(summary_rows)


def print_combined_weekly_summary(weekly_df: pd.DataFrame) -> None:
    """서울/부산 통합 토요일 기준 현황 출력."""
    print("[서울/부산 주력베팅 토요일 기준 통합 적중/환수 현황]")
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
        track_races = int(track_df["경주수"].sum())
        track_hits = int(track_df["적중경주수"].sum())
        track_bet = float(track_df["총베팅액"].sum())
        track_refund = float(track_df["총환수액"].sum())
        track_profit = track_refund - track_bet
        track_hit_rate = track_hits / track_races if track_races > 0 else 0.0
        track_refund_rate = track_refund / track_bet if track_bet > 0 else 0.0
        print(
            f"[{track_name} 소계]  경주수: {track_races}  적중경주수: {track_hits}  "
            f"적중율: {track_hit_rate:.3f}  총베팅액: {int(track_bet):,}원  "
            f"총환수액: {track_refund:,.1f}원  이익금액: {track_profit:,.1f}원  "
            f"환수율: {track_refund_rate:.3f}"
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

    total_races = int(summary["경주수"].sum())
    total_hits = int(summary["적중경주수"].sum())
    total_bet = float(summary["총베팅액"].sum())
    total_refund = float(summary["총환수액"].sum())
    total_profit = total_refund - total_bet
    total_hit_rate = total_hits / total_races if total_races > 0 else 0.0
    total_refund_rate = total_refund / total_bet if total_bet > 0 else 0.0
    print(
        f"[총계]  경주수: {total_races}  적중경주수: {total_hits}  "
        f"적중율: {total_hit_rate:.3f}  총베팅액: {int(total_bet):,}원  "
        f"총환수액: {total_refund:,.1f}원  이익금액: {total_profit:,.1f}원  "
        f"환수율: {total_refund_rate:.3f}"
    )


def print_combined_monthly_summary(monthly_df: pd.DataFrame) -> None:
    """서울/부산 월별 현황 출력."""
    print("[서울/부산 주력베팅 월별 집계]")
    if monthly_df.empty:
        print("데이터가 없습니다.")
        return

    for track_name in ["서울", "부산"]:
        track_df = monthly_df[monthly_df["경마장"] == track_name].copy()
        if track_df.empty:
            continue
        print(f"[{track_name}]")
        for row in track_df.itertuples(index=False):
            print(
                f"[월별 {row.년월}]  경주수: {row.경주수}  "
                f"적중경주수: {row.적중경주수}  적중율: {row.적중율:.3f}  "
                f"총베팅액: {int(row.총베팅액):,}원  총환수액: {row.총환수액:,.1f}원  "
                f"이익금액: {row.이익금액:,.1f}원  환수율: {row.환수율:.3f}"
            )

    summary = (
        monthly_df.groupby("년월", dropna=False)[["경주수", "적중경주수", "총베팅액", "총환수액", "이익금액"]]
        .sum()
        .reset_index()
        .sort_values("년월")
    )
    summary["적중율"] = summary["적중경주수"] / summary["경주수"]
    summary["환수율"] = summary["총환수액"] / summary["총베팅액"]

    print("[월별 통합]")
    for row in summary.itertuples(index=False):
        print(
            f"[월별 {row.년월}]  경주수: {row.경주수}  "
            f"적중경주수: {row.적중경주수}  적중율: {row.적중율:.3f}  "
            f"총베팅액: {int(row.총베팅액):,}원  총환수액: {row.총환수액:,.1f}원  "
            f"이익금액: {row.이익금액:,.1f}원  환수율: {row.환수율:.3f}"
        )


def print_track_rpop_rank_summary(raw_df: pd.DataFrame, race_df: pd.DataFrame) -> None:
    """경마장별 r_pop 1~12 실제 1/2/3위 비율 출력."""
    print("[경마장별 r_pop 1~12 실제순위 1위/2위/3위 비율]")
    if race_df.empty or raw_df.empty:
        print("데이터가 없습니다.")
        return

    for track_name in ["서울", "부산"]:
        summary_df = build_track_rpop_rank_summary(raw_df, race_df, track_name)
        if summary_df.empty:
            continue
        print(f"[{track_name}]")
        for _, row in summary_df.iterrows():
            print(
                f"[r_pop {int(row['r_pop'])}]  건수: {int(row['건수'])}  "
                f"1위: {int(row['1위건수'])} ({row['1위율']:.3f})  "
                f"2위: {int(row['2위건수'])} ({row['2위율']:.3f})  "
                f"3위: {int(row['3위건수'])} ({row['3위율']:.3f})"
            )


def print_method_summary(method_df: pd.DataFrame) -> None:
    """경마장별/통합 베팅방법 환수율 출력."""
    print("[베팅방법별 환수율]")
    if method_df.empty:
        print("데이터가 없습니다.")
        return

    for track_name in ["서울", "부산"]:
        track_df = method_df[method_df["경마장"] == track_name].copy()
        if track_df.empty:
            continue
        print(f"[{track_name}]")
        for row in track_df.itertuples(index=False):
            print(
                f"[{row.베팅방법}]  경주수: {row.경주수}  적중경주수: {row.적중경주수}  "
                f"적중율: {row.적중율:.3f}  총베팅액: {int(row.총베팅액):,}원  "
                f"총환수액: {row.총환수액:,.1f}원  이익금액: {row.이익금액:,.1f}원  "
                f"환수율: {row.환수율:.3f}"
            )

    combined = (
        method_df.groupby(["전략키", "베팅방법"], dropna=False)[["경주수", "적중경주수", "총베팅액", "총환수액"]]
        .sum()
        .reset_index()
    )
    combined["이익금액"] = combined["총환수액"] - combined["총베팅액"]
    combined["적중율"] = combined["적중경주수"] / combined["경주수"]
    combined["환수율"] = combined["총환수액"] / combined["총베팅액"]
    combined = combined.sort_values("환수율", ascending=False)

    print("[통합]")
    for row in combined.itertuples(index=False):
        print(
            f"[{row.베팅방법}]  경주수: {row.경주수}  적중경주수: {row.적중경주수}  "
            f"적중율: {row.적중율:.3f}  총베팅액: {int(row.총베팅액):,}원  "
            f"총환수액: {row.총환수액:,.1f}원  이익금액: {row.이익금액:,.1f}원  "
            f"환수율: {row.환수율:.3f}"
        )


def save_weekly_df(weekly_df: pd.DataFrame, output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """서울/부산 통합 토요일 기준 현황 CSV 저장."""
    if weekly_df.empty:
        return
    weekly_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"▶ 서울/부산 주력베팅 토요일 기준 통합 CSV 저장: {output_path}")


def main() -> None:
    """서울/부산 주력베팅 토요일 기준 통합 집계를 실행한다."""
    os.environ["DJANGO_SETTINGS_MODULE"] = "letsrace.settings"
    base_mod.load_result_data_from_db = load_result_data_from_db
    allowed_strategy_keys = {
        key
        for strategy_keys in PRIMARY_STRATEGY_KEYS_BY_TRACK.values()
        for key in strategy_keys
    }
    base_mod.EXCLUDED_STRATEGY_KEYS = set(base_mod.STRATEGY_LABELS.keys()) - allowed_strategy_keys
    original_upsert = base_mod.upsert_weekly_betting_summary
    original_to_csv = pd.DataFrame.to_csv
    try:
        # Suppress base-side reporting/output because this wrapper needs
        # track-specific primary sets, not the union of both tracks' keys.
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
    engine = base_mod.get_engine()
    raw_df = load_result_data_from_db(engine, from_date=DEFAULT_FROM_DATE, to_date=DEFAULT_TO_DATE)
    weekly_df = build_combined_weekly_summary(race_df)
    monthly_df = build_combined_monthly_summary(race_df)
    method_df = build_combined_method_summary(race_df)
    print_combined_weekly_summary(weekly_df)
    print_combined_monthly_summary(monthly_df)
    print_method_summary(method_df)
    print_track_rpop_rank_summary(raw_df, race_df)
    save_weekly_df(weekly_df)


if __name__ == "__main__":
    main()
