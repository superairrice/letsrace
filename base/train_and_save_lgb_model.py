import pandas as pd
import lightgbm as lgb


def train_and_save_lgb_model(train_csv_path: str, model_path: str):
    """
    과거 경주 데이터를 이용해 LightGBM 학습 후,
    모델을 model_path 경로에 저장.

    train_csv_path 예시 컬럼:
      - '경마장', '경주일', '경주번호', '경주거리', '마번'
      - '예상순위1', '예상순위2', '실제순위'
      - (삼복승식배당율, 복승식배당율 등은 학습 필수 아님)
    """

    df = pd.read_csv(train_csv_path)

    # 기본 형변환
    df = df.copy()
    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)

    # 필수 컬럼 체크
    required_cols = ["예상순위1", "예상순위2", "실제순위"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"다음 컬럼이 누락되었습니다: {missing}")

    df["예상순위1"] = df["예상순위1"].astype(int)
    df["예상순위2"] = df["예상순위2"].astype(int)
    df["실제순위"] = df["실제순위"].astype(int)

    # 🔹 피처 엔지니어링
    # 신마 여부 (예상순위1 또는 2가 98 이상이면 신마로 간주)
    df["is_new"] = ((df["예상순위1"] >= 98) | (df["예상순위2"] >= 98)).astype(int)
    # 순위 차이
    df["rank_gap"] = df["예상순위2"] - df["예상순위1"]

    # 경주거리 옵션
    feature_cols = ["예상순위1", "예상순위2", "rank_gap", "is_new"]
    if "경주거리" in df.columns:
        df["경주거리"] = df["경주거리"].astype(int)
        feature_cols.append("경주거리")

    # 🔹 라벨: 실제 1~3위 안에 들었는지 (삼복용)
    df["label_sb"] = (df["실제순위"] <= 3).astype(int)

    train_set = lgb.Dataset(df[feature_cols], label=df["label_sb"])

    params = dict(
        objective="binary",
        boosting_type="gbdt",
        learning_rate=0.03,
        num_leaves=31,
        feature_fraction=0.9,
        bagging_fraction=0.9,
        bagging_freq=3,
        verbose=-1,
    )

    print("▶ LightGBM 학습 시작...")
    model = lgb.train(params, train_set, num_boost_round=400)
    print("▶ 학습 완료.")

    # 🔹 모델 저장
    model.save_model(model_path)
    print(f"▶ 모델 저장 완료: {model_path}")

    print("▶ 사용한 feature_cols:", feature_cols)

    return model, feature_cols


def load_model_and_select_top6(
    model_path: str,
    new_race_csv_path: str,
    feature_cols: list = None,
):
    """
    저장된 LightGBM 모델(model_path)과
    새 경주 데이터(new_race_csv_path, 실제순위 없이도 OK)를 사용해서
    경주별 p_sb 상위 6두를 선정.

    new_race_csv 예시 컬럼:
      - '경마장', '경주일', '경주번호', '경주거리', '마번'
      - '예상순위1', '예상순위2'
      (실제순위, 배당율은 없어도 됨)
    """

    # 1) 모델 로드
    model = lgb.Booster(model_file=model_path)

    # 2) 새 데이터 로드
    df_new = pd.read_csv(new_race_csv_path)
    df_new = df_new.copy()
    df_new["경주일"] = df_new["경주일"].astype(str)
    df_new["경주번호"] = df_new["경주번호"].astype(int)
    df_new["마번"] = df_new["마번"].astype(int)

    df_new["예상순위1"] = df_new["예상순위1"].astype(int)
    df_new["예상순위2"] = df_new["예상순위2"].astype(int)

    # 3) 피처 재구성 (학습 시와 동일 로직)
    df_new["is_new"] = (
        (df_new["예상순위1"] >= 98) | (df_new["예상순위2"] >= 98)
    ).astype(int)
    df_new["rank_gap"] = df_new["예상순위2"] - df_new["예상순위1"]

    auto_feature_cols = ["예상순위1", "예상순위2", "rank_gap", "is_new"]
    if "경주거리" in df_new.columns:
        df_new["경주거리"] = df_new["경주거리"].astype(int)
        auto_feature_cols.append("경주거리")

    # 만약 train 때 feature_cols를 저장해 두었다면, 그걸 우선 사용
    if feature_cols is None:
        feature_cols = auto_feature_cols
    else:
        # new 데이터에 없는 feature가 있으면 에러 방지
        missing_f = [c for c in feature_cols if c not in df_new.columns]
        if missing_f:
            raise ValueError(f"새 데이터에 다음 feature가 없습니다: {missing_f}")

    # 4) p_sb 예측
    df_new["p_sb"] = model.predict(df_new[feature_cols])

    # 5) 경주별 상위 6두 선정
    results = []

    for (track, date, rno), g in df_new.groupby(["경마장", "경주일", "경주번호"]):
        g = g.copy()
        top6 = g.sort_values("p_sb", ascending=False).head(6)

        top6_list = top6[["마번", "p_sb"]].sort_values("p_sb", ascending=False)

        results.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "상위6_마번리스트": ",".join(map(str, top6_list["마번"].tolist())),
                "상위6_p_sb리스트": ",".join(
                    [f"{v:.4f}" for v in top6_list["p_sb"].tolist()]
                ),
            }
        )

    result_df = pd.DataFrame(results)
    return result_df, df_new


if __name__ == "__main__":
    # 1) 학습 및 저장
    train_csv = "/Users/Super007/Documents/20241130_20251130_dist.csv"
    model_path = "/Users/Super007/Documents/lgb_model_20241130.txt"

    model, feature_cols = train_and_save_lgb_model(train_csv, model_path)

    # 2) 새 경주 데이터에 상위 6두 선정
    new_race_csv = "/Users/Super007/Documents/new_races_20251201.csv"
    top6_df, df_with_prob = load_model_and_select_top6(
        model_path=model_path,
        new_race_csv_path=new_race_csv,
        feature_cols=feature_cols,  # 학습 때 쓴 feature를 그대로 사용
    )

    print(top6_df.head())

    # 필요시 CSV 저장
    out_top6_path = "/Users/Super007/Documents/new_races_top6_by_lgb.csv"
    top6_df.to_csv(out_top6_path, index=False, encoding="utf-8-sig")
    print("▶ 새 경주 상위6두 결과 저장:", out_top6_path)
