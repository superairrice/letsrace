import pandas as pd


def make_final_summary_with_groups(df):
    """
    df 컬럼 가정:
    - '경마장', '경주일', '경주번호', '마번'
    - '경주거리'
    - '예상순위1', '예상순위2', '실제순위'
    - '삼복승식배당율', '복승식배당율'
    """

    df = df.copy()
    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)
    df["경주거리"] = df["경주거리"].astype(int)
    df["예상순위1"] = df["예상순위1"].astype(int)
    df["예상순위2"] = df["예상순위2"].astype(int)
    df["실제순위"] = df["실제순위"].astype(int)

    group_cols = ["경마장", "경주일", "경주번호", "경주거리"]

    def _agg_one_race(g: pd.DataFrame) -> pd.Series:
        # 🔹 신마수 (예상순위1 == 98 기준)
        new_count = int((g["예상순위1"] == 98).sum())

        # 🔹 실제 1~3위 마번 그룹
        actual_top3 = (
            g[g["실제순위"].between(1, 3)].sort_values("실제순위")["마번"].tolist()
        )
        actual_top3_str = ",".join(map(str, actual_top3)) if actual_top3 else ""

        # 🔹 실제 1~2위 (복승용)
        actual_top2 = (
            g[g["실제순위"].between(1, 2)].sort_values("실제순위")["마번"].tolist()
        )

        # 🔹 예상1 1~6위 마번 그룹
        rank1_top6 = (
            g[g["예상순위1"].between(1, 6)].sort_values("예상순위1")["마번"].tolist()
        )
        rank1_top6_str = ",".join(map(str, rank1_top6)) if rank1_top6 else ""

        # 🔹 예상2 1~6위 마번 그룹
        rank2_top6 = (
            g[g["예상순위2"].between(1, 6)].sort_values("예상순위2")["마번"].tolist()
        )
        rank2_top6_str = ",".join(map(str, rank2_top6)) if rank2_top6 else ""

        # 🔹 예상1+2 합산 상위 6두 (새로 추가 부분)
        g_tmp = g.copy()
        g_tmp["예상합산"] = g_tmp["예상순위1"] + g_tmp["예상순위2"]
        # 합산 순위 → 같으면 예상1,2,마번으로 tie-break
        sum_top6 = (
            g_tmp.sort_values(["예상합산", "예상순위1", "예상순위2", "마번"])["마번"]
            .head(6)
            .tolist()
        )
        sum_top6_str = ",".join(map(str, sum_top6)) if sum_top6 else ""

        # 🔹 세트 변환
        actual_top3_set = set(actual_top3)
        actual_top2_set = set(actual_top2)
        rank1_top6_set = set(rank1_top6)
        rank2_top6_set = set(rank2_top6)
        sum_top6_set = set(sum_top6)

        # 🔹 삼복 / 복승 적중여부
        삼복_rank1_적중 = (
            int(actual_top3_set.issubset(rank1_top6_set)) if actual_top3_set else 0
        )
        삼복_rank2_적중 = (
            int(actual_top3_set.issubset(rank2_top6_set)) if actual_top3_set else 0
        )
        삼복_sum6_적중 = (
            int(actual_top3_set.issubset(sum_top6_set)) if actual_top3_set else 0
        )

        복승_rank1_적중 = (
            int(actual_top2_set.issubset(rank1_top6_set)) if actual_top2_set else 0
        )
        복승_rank2_적중 = (
            int(actual_top2_set.issubset(rank2_top6_set)) if actual_top2_set else 0
        )
        복승_sum6_적중 = (
            int(actual_top2_set.issubset(sum_top6_set)) if actual_top2_set else 0
        )

        # 🔹 경주별 원 배당(배당율)
        삼복원배당 = (
            g["삼복승식배당율"].iloc[0] if "삼복승식배당율" in g.columns else 0.0
        )
        복승원배당 = g["복승식배당율"].iloc[0] if "복승식배당율" in g.columns else 0.0

        # 🔹 적중 시 적용 배당
        삼복_rank1_배당 = 삼복원배당 if 삼복_rank1_적중 else 0.0
        삼복_rank2_배당 = 삼복원배당 if 삼복_rank2_적중 else 0.0
        삼복_sum6_배당 = 삼복원배당 if 삼복_sum6_적중 else 0.0

        복승_rank1_배당 = 복승원배당 if 복승_rank1_적중 else 0.0
        복승_rank2_배당 = 복승원배당 if 복승_rank2_적중 else 0.0
        복승_sum6_배당 = 복승원배당 if 복승_sum6_적중 else 0.0

        return pd.Series(
            {
                "신마수_예상1_코드98기준": new_count,
                # 👉 그룹 정보
                "실제순위_1_3_마번그룹": actual_top3_str,
                "rank1_1_6_마번그룹": rank1_top6_str,
                "rank2_1_6_마번그룹": rank2_top6_str,
                "rank12합산_1_6_마번그룹": sum_top6_str,  # 🔥 추가
                # 👉 경주 원 배당(공식 배당율)
                "경주_삼복승식_배당율": 삼복원배당,
                "경주_복승식_배당율": 복승원배당,
                # 👉 예상1 단독
                "삼복_rank1_적중": 삼복_rank1_적중,
                "삼복_rank1_배당": 삼복_rank1_배당,
                "복승_rank1_적중": 복승_rank1_적중,
                "복승_rank1_배당": 복승_rank1_배당,
                # 👉 예상2 단독
                "삼복_rank2_적중": 삼복_rank2_적중,
                "삼복_rank2_배당": 삼복_rank2_배당,
                "복승_rank2_적중": 복승_rank2_적중,
                "복승_rank2_배당": 복승_rank2_배당,
                # 👉 예상1+2 합산 상위6두 전략
                "삼복_rank12합산_적중": 삼복_sum6_적중,
                "삼복_rank12합산_배당": 삼복_sum6_배당,
                "복승_rank12합산_적중": 복승_sum6_적중,
                "복승_rank12합산_배당": 복승_sum6_배당,
            }
        )

    summary = df.groupby(group_cols).apply(_agg_one_race).reset_index()
    return summary


# 사용 예시
df = pd.read_csv("/Users/Super007/Documents/new_races_20231201_20251130.csv")
race_result = make_final_summary_with_groups(df)

print(race_result.head())

race_result.to_csv(
    "/Users/Super007/Documents/newcount_20231201_dist_with_sum6.csv",
    index=False,
)
