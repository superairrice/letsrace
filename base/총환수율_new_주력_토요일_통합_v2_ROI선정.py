"""서울/부산 주력베팅 토요일 기준 통합 현황 실행 파일 (v2 ROI 선정 조합)."""

import 총환수율_new_주력_토요일_통합 as base_script


base_script.DEFAULT_OUTPUT_PATH = (
    "/Users/Super007/Documents/r_pop_total_new_주력_토요일_통합_v2_ROI선정.csv"
)
base_script.PRIMARY_STRATEGY_KEYS_BY_TRACK = {
    "서울": [
        "anchor1_23_46",
        "anchor1_25",
        "anchor1_23_47",
        "anchor1_58_24",
    ],
    "부산": [
        "anchor1_24",
        "top4_box_trifecta",
        "anchor1_23_46",
        "anchor1_69_25",
    ],
}
base_script.ALLOWED_TRACKS = set(base_script.PRIMARY_STRATEGY_KEYS_BY_TRACK.keys())


def main() -> None:
    base_script.main()


if __name__ == "__main__":
    main()
