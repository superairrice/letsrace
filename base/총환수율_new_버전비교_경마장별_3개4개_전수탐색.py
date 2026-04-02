"""v0/v1/v2/v4 최고 ROI 조합을 한 번에 비교 출력하는 통합 스크립트."""

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


def build_compare_df() -> pd.DataFrame:
    rows = []
    for profile in PROFILES:
        race_df = load_race_df_for_profile(profile)
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

                result = top_results[0]
                rows.append(
                    {
                        "버전": profile,
                        "설명": PROFILE_DESCRIPTIONS.get(profile, profile),
                        "경마장": track_name,
                        "조합수": combo_size,
                        "ROI": result["roi"],
                        "총베팅액": int(result["bet"]),
                        "총환수액": float(result["refund"]),
                        "이익금액": float(result["profit"]),
                        "적중율": result["hit_rate"],
                        "전략조합": " + ".join(result["keys"]),
                    }
                )

    if not rows:
        return pd.DataFrame(
            columns=[
                "버전",
                "설명",
                "경마장",
                "조합수",
                "ROI",
                "총베팅액",
                "총환수액",
                "이익금액",
                "적중율",
                "전략조합",
            ]
        )

    compare_df = pd.DataFrame(rows)
    compare_df = compare_df.sort_values(
        by=["버전", "경마장", "조합수"],
        ascending=[True, True, True],
    ).reset_index(drop=True)
    return compare_df


def print_compare_df(compare_df: pd.DataFrame) -> None:
    print(
        f"[기간] {DEFAULT_FROM_DATE} ~ {DEFAULT_TO_DATE}  "
        "(총환수율_new.py 기본 규칙: 13두 이상 / 신마 3두 이상 제외)"
    )
    print("[주의] v0 는 UI 기준 내부적으로 v5 엔진에 매핑됩니다.")

    if compare_df.empty:
        print("비교할 데이터가 없습니다.")
        return

    display_df = compare_df.copy()
    display_df["ROI"] = display_df["ROI"].map(lambda x: f"{x:.6f}")
    display_df["적중율"] = display_df["적중율"].map(lambda x: f"{x:.6f}")
    display_df["총베팅액"] = display_df["총베팅액"].map(lambda x: f"{int(x):,}")
    display_df["총환수액"] = display_df["총환수액"].map(lambda x: f"{x:,.1f}")
    display_df["이익금액"] = display_df["이익금액"].map(lambda x: f"{x:,.1f}")

    print("[비교표]")
    print(display_df.to_string(index=False))


def main() -> None:
    compare_df = build_compare_df()
    print_compare_df(compare_df)


if __name__ == "__main__":
    main()
