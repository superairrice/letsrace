"""동일 조합 고정 기준으로 v0/v1/v2/v4 순수 모델 비교표를 출력하는 스크립트."""

import pandas as pd

import 총환수율_new_경마장별_3개4개_전수탐색 as combo_mod
from 총환수율_new_버전별_경마장별_3개4개_전수탐색_lib import (
    COMBO_SIZES,
    DEFAULT_FROM_DATE,
    DEFAULT_TO_DATE,
    PROFILE_DESCRIPTIONS,
    TRACK_ORDER,
    load_race_df_for_profile,
)


PROFILES = ("v0", "v1", "v2", "v4")


def _collect_profile_race_dfs() -> dict[str, pd.DataFrame]:
    return {profile: load_race_df_for_profile(profile) for profile in PROFILES}


def _collect_reference_combos(profile_race_dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """각 버전 최고 조합의 합집합을 고정 비교 대상 조합으로 만든다."""
    rows = []
    for profile, race_df in profile_race_dfs.items():
        for track_name in TRACK_ORDER:
            track_df = race_df[race_df["경마장"] == track_name].copy()
            if track_df.empty:
                continue

            for combo_size in COMBO_SIZES:
                top_results = combo_mod.find_top_combos(
                    track_df,
                    combo_size=combo_size,
                    top_n=1,
                )
                if not top_results:
                    continue

                top = top_results[0]
                rows.append(
                    {
                        "기준버전": profile,
                        "경마장": track_name,
                        "조합수": combo_size,
                        "전략조합": " + ".join(top["keys"]),
                        "전략키목록": tuple(top["keys"]),
                    }
                )

    if not rows:
        return pd.DataFrame(
            columns=["기준버전", "경마장", "조합수", "전략조합", "전략키목록"]
        )

    ref_df = pd.DataFrame(rows).drop_duplicates(
        subset=["경마장", "조합수", "전략조합"]
    )
    ref_df = ref_df.sort_values(
        by=["경마장", "조합수", "기준버전", "전략조합"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)
    return ref_df


def build_pure_model_compare_df() -> tuple[pd.DataFrame, pd.DataFrame]:
    profile_race_dfs = _collect_profile_race_dfs()
    ref_df = _collect_reference_combos(profile_race_dfs)

    rows = []
    for ref in ref_df.itertuples(index=False):
        combo_keys = tuple(ref.전략키목록)
        for profile in PROFILES:
            race_df = profile_race_dfs[profile]
            track_df = race_df[race_df["경마장"] == ref.경마장].copy()
            if track_df.empty:
                continue

            summary = combo_mod.summarize_combo(track_df, combo_keys)
            rows.append(
                {
                    "경마장": ref.경마장,
                    "조합수": ref.조합수,
                    "고정조합": ref.전략조합,
                    "기준버전": ref.기준버전,
                    "비교버전": profile,
                    "비교버전설명": PROFILE_DESCRIPTIONS.get(profile, profile),
                    "ROI": summary["roi"],
                    "총베팅액": int(summary["bet"]),
                    "총환수액": float(summary["refund"]),
                    "이익금액": float(summary["profit"]),
                    "적중율": float(summary["hit_rate"]),
                    "적중경주수": int(summary["hit_races"]),
                    "경주수": int(summary["races"]),
                }
            )

    if not rows:
        return pd.DataFrame(), ref_df

    detail_df = pd.DataFrame(rows).sort_values(
        by=["경마장", "조합수", "고정조합", "비교버전"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)
    return detail_df, ref_df


def build_roi_pivot(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame()

    pivot = (
        detail_df.pivot_table(
            index=["경마장", "조합수", "고정조합", "기준버전"],
            columns="비교버전",
            values="ROI",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    for profile in PROFILES:
        if profile not in pivot.columns:
            pivot[profile] = pd.NA

    pivot["최고버전"] = pivot[list(PROFILES)].astype(float).idxmax(axis=1)
    pivot["최고ROI"] = pivot[list(PROFILES)].astype(float).max(axis=1)
    return pivot[
        ["경마장", "조합수", "고정조합", "기준버전", *PROFILES, "최고버전", "최고ROI"]
    ].sort_values(
        by=["경마장", "조합수", "고정조합", "기준버전"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)


def build_win_summary(pivot_df: pd.DataFrame) -> pd.DataFrame:
    if pivot_df.empty:
        return pd.DataFrame()

    rows = []
    scopes = [("전체", pivot_df)] + [
        (track_name, pivot_df[pivot_df["경마장"] == track_name].copy())
        for track_name in TRACK_ORDER
    ]

    for scope_name, scope_df in scopes:
        if scope_df.empty:
            continue

        for profile in PROFILES:
            win_count = 0
            sole_win_count = 0
            shared_win_count = 0
            for row in scope_df.itertuples(index=False):
                roi_map = {
                    current_profile: float(getattr(row, current_profile))
                    for current_profile in PROFILES
                }
                top_roi = max(roi_map.values())
                winners = [
                    current_profile
                    for current_profile, roi in roi_map.items()
                    if abs(roi - top_roi) <= 1e-12
                ]
                if profile in winners:
                    win_count += 1
                    if len(winners) == 1:
                        sole_win_count += 1
                    else:
                        shared_win_count += 1

            rows.append(
                {
                    "구분": scope_name,
                    "버전": profile,
                    "비교조합수": int(len(scope_df)),
                    "1위횟수(공동포함)": win_count,
                    "단독1위횟수": sole_win_count,
                    "공동1위횟수": shared_win_count,
                    "평균ROI": float(
                        pd.to_numeric(scope_df[profile], errors="coerce").mean()
                    ),
                }
            )

    return pd.DataFrame(rows).sort_values(
        by=["구분", "버전"],
        ascending=[True, True],
    ).reset_index(drop=True)


def build_track_top_summary(pivot_df: pd.DataFrame) -> pd.DataFrame:
    if pivot_df.empty:
        return pd.DataFrame()

    rows = []
    scopes = [("전체", pivot_df)] + [
        (track_name, pivot_df[pivot_df["경마장"] == track_name].copy())
        for track_name in TRACK_ORDER
    ]

    for scope_name, scope_df in scopes:
        if scope_df.empty:
            continue

        avg_roi_map = {
            profile: float(pd.to_numeric(scope_df[profile], errors="coerce").mean())
            for profile in PROFILES
        }
        top_avg_roi = max(avg_roi_map.values())
        top_profiles = [
            profile
            for profile, roi in avg_roi_map.items()
            if abs(roi - top_avg_roi) <= 1e-12
        ]

        rows.append(
            {
                "구분": scope_name,
                "비교조합수": int(len(scope_df)),
                "v0_평균ROI": avg_roi_map["v0"],
                "v1_평균ROI": avg_roi_map["v1"],
                "v2_평균ROI": avg_roi_map["v2"],
                "v4_평균ROI": avg_roi_map["v4"],
                "1위버전": "/".join(top_profiles),
                "1위평균ROI": top_avg_roi,
            }
        )

    return pd.DataFrame(rows).sort_values(
        by=["구분"],
        ascending=[True],
    ).reset_index(drop=True)


def build_recommendation_lines(
    track_top_df: pd.DataFrame,
    win_summary_df: pd.DataFrame,
) -> list[str]:
    if track_top_df.empty or win_summary_df.empty:
        return []

    lines = []
    for track_name in TRACK_ORDER:
        track_row_df = track_top_df[track_top_df["구분"] == track_name].copy()
        if track_row_df.empty:
            continue
        track_row = track_row_df.iloc[0]

        top_versions = str(track_row["1위버전"]).split("/")
        best_avg_roi = float(track_row["1위평균ROI"])
        combo_count = int(track_row["비교조합수"])

        win_df = win_summary_df[
            (win_summary_df["구분"] == track_name)
            & (win_summary_df["버전"].isin(top_versions))
        ].copy()
        win_df = win_df.sort_values(
            by=["단독1위횟수", "1위횟수(공동포함)", "평균ROI", "버전"],
            ascending=[False, False, False, True],
        )

        best_versions_text = "/".join(top_versions)
        if len(top_versions) == 1:
            best_version_text = top_versions[0]
        else:
            best_version_text = f"{best_versions_text}(공동)"

        win_text = ""
        if not win_df.empty:
            top_win = win_df.iloc[0]
            win_text = (
                f", 1위 {int(top_win['1위횟수(공동포함)'])}/{combo_count}"
                f", 단독1위 {int(top_win['단독1위횟수'])}/{combo_count}"
            )

        lines.append(
            f"- {track_name}: {best_version_text} 추천 "
            f"(고정조합 {combo_count}개 평균 ROI {best_avg_roi:.6f}{win_text})"
        )

    overall_df = track_top_df[track_top_df["구분"] == "전체"].copy()
    if not overall_df.empty:
        overall_row = overall_df.iloc[0]
        lines.append(
            f"- 전체: {overall_row['1위버전']} "
            f"(평균 ROI {float(overall_row['1위평균ROI']):.6f})"
        )
    return lines


def _format_number_df(df: pd.DataFrame, roi_columns: list[str]) -> pd.DataFrame:
    formatted = df.copy()
    for col in roi_columns:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(
                lambda x: "" if pd.isna(x) else f"{float(x):.6f}"
            )
    if "최고ROI" in formatted.columns:
        formatted["최고ROI"] = formatted["최고ROI"].map(
            lambda x: "" if pd.isna(x) else f"{float(x):.6f}"
        )
    if "적중율" in formatted.columns:
        formatted["적중율"] = formatted["적중율"].map(lambda x: f"{float(x):.6f}")
    if "총베팅액" in formatted.columns:
        formatted["총베팅액"] = formatted["총베팅액"].map(lambda x: f"{int(x):,}")
    if "총환수액" in formatted.columns:
        formatted["총환수액"] = formatted["총환수액"].map(lambda x: f"{float(x):,.1f}")
    if "이익금액" in formatted.columns:
        formatted["이익금액"] = formatted["이익금액"].map(lambda x: f"{float(x):,.1f}")
    return formatted


def print_compare_tables(detail_df: pd.DataFrame, pivot_df: pd.DataFrame) -> None:
    print(
        f"[기간] {DEFAULT_FROM_DATE} ~ {DEFAULT_TO_DATE}  "
        "(동일 조합 고정 기준, 총환수율_new.py 기본 규칙: 13두 이상 / 신마 3두 이상 제외)"
    )
    print("[주의] v0 는 UI 기준 내부적으로 v5 엔진에 매핑됩니다.")

    if detail_df.empty:
        print("비교할 데이터가 없습니다.")
        return

    win_summary_df = build_win_summary(pivot_df)
    track_top_df = build_track_top_summary(pivot_df)
    recommendation_lines = build_recommendation_lines(track_top_df, win_summary_df)

    print("[순수 모델 비교표: ROI Pivot]")
    formatted_pivot = _format_number_df(pivot_df, list(PROFILES))
    print(formatted_pivot.to_string(index=False))

    print("[버전별 승수 요약]")
    formatted_win = _format_number_df(win_summary_df, ["평균ROI"])
    print(formatted_win.to_string(index=False))

    print("[경마장별 평균 ROI 1위 요약]")
    formatted_track_top = _format_number_df(
        track_top_df,
        ["v0_평균ROI", "v1_평균ROI", "v2_평균ROI", "v4_평균ROI"],
    )
    print(formatted_track_top.to_string(index=False))

    print("[자동 결론]")
    for line in recommendation_lines:
        print(line)

    print("[순수 모델 비교표: 상세]")
    formatted_detail = _format_number_df(detail_df, ["ROI"])
    print(formatted_detail.to_string(index=False))


def main() -> None:
    detail_df, _ref_df = build_pure_model_compare_df()
    pivot_df = build_roi_pivot(detail_df)
    print_compare_tables(detail_df, pivot_df)


if __name__ == "__main__":
    main()
