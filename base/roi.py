import pandas as pd
from typing import List, Tuple


def evaluate_weighted_combo_roi(
    df: pd.DataFrame,
    alphas: List[float] = None,
    exclude_new2: bool = False,
) -> pd.DataFrame:

    if alphas is None:
        alphas = [i / 10 for i in range(0, 11)]

    df = df.copy()

    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)
    df["경주거리"] = df["경주거리"].astype(int)
    df["예상순위1"] = df["예상순위1"].astype(int)
    df["예상순위2"] = df["예상순위2"].astype(int)
    df["실제순위"] = df["실제순위"].astype(int)

    group_cols = ["경마장", "경주일", "경주번호", "경주거리"]

    results = []

    for alpha in alphas:
        total_races = 0

        sb_bet = 20 * 100  # 삼복 6복조
        bs_bet = 15 * 100  # 복승 6복조

        sb_total_bet = 0
        sb_total_refund = 0
        sb_hit_cnt = 0

        bs_total_bet = 0
        bs_total_refund = 0
        bs_hit_cnt = 0

        for _, g in df.groupby(group_cols):

            # 신마 2두 이상 제외
            if exclude_new2:
                if (g["예상순위1"] == 98).sum() >= 2:
                    continue

            actual_top3 = g[g["실제순위"].between(1, 3)]["마번"].tolist()
            actual_top2 = g[g["실제순위"].between(1, 2)]["마번"].tolist()

            # 가중합 score
            tmp = g.copy()
            tmp["score"] = tmp["예상순위1"] + alpha * tmp["예상순위2"]
            top6 = tmp.sort_values("score").head(6)["마번"].tolist()
            top6_set = set(top6)

            # 배당율
            sb_odds = float(g["삼복승식배당율"].iloc[0])
            bs_odds = float(g["복승식배당율"].iloc[0])

            # 적중여부
            sb_hit = int(len(actual_top3) == 3 and set(actual_top3).issubset(top6_set))
            bs_hit = int(len(actual_top2) == 2 and set(actual_top2).issubset(top6_set))

            total_races += 1

            # 삼복
            sb_total_bet += sb_bet
            if sb_hit:
                # 🔥 500배 이상이면 환급 0 처리
                if sb_odds < 500:
                    sb_total_refund += sb_odds * 100
                sb_hit_cnt += 1

            # 복승
            bs_total_bet += bs_bet
            if bs_hit:
                # 🔥 500배 이상이면 환급 0 처리
                if bs_odds < 500:
                    bs_total_refund += bs_odds * 100
                bs_hit_cnt += 1

        # 집계
        if total_races == 0:
            continue

        sb_roi = (sb_total_refund - sb_total_bet) / sb_total_bet
        bs_roi = (bs_total_refund - bs_total_bet) / bs_total_bet

        results.append(
            {
                "alpha": alpha,
                "총_경주수": total_races,
                "삼복_적중경주수": sb_hit_cnt,
                "삼복_적중률": sb_hit_cnt / total_races,
                "삼복_총베팅액": sb_total_bet,
                "삼복_총환급액": sb_total_refund,
                "삼복_ROI": sb_roi,
                "복승_적중경주수": bs_hit_cnt,
                "복승_적중률": bs_hit_cnt / total_races,
                "복승_총베팅액": bs_total_bet,
                "복승_총환급액": bs_total_refund,
                "복승_ROI": bs_roi,
            }
        )

    return pd.DataFrame(results)


# 예시: 기존에 쓰던 odds 데이터
df = pd.read_csv("/Users/Super007/Documents/20241130_20251130_dist.csv")

# 1) 신마경주 제외하지 않고, alpha 0.0~1.0 비교
res_all = evaluate_weighted_combo_roi(df)
print(res_all)

# 2) 신마(예상1=98) 2두 이상인 경주는 제외하고 비교
res_no_new2 = evaluate_weighted_combo_roi(df, exclude_new2=True)
print(res_no_new2)

# 3) 직접 alpha 후보를 지정해서 돌리고 싶으면:
alphas = [0.0, 0.3, 0.5, 0.7, 1.0]
res_custom = evaluate_weighted_combo_roi(df, alphas=alphas, exclude_new2=True)
print(res_custom)
