import pandas as pd

# =========================
# 0) 설정: 네 raw CSV 경로
# =========================
RAW_PATH = "/Users/Super007/Documents/box4_tri333_tri123_rank_rpop_mrank_raw_with_hit_refund_month_grade_distance.csv"

OUT_SWITCH_RPOP = "/Users/Super007/Documents/sim_switch_RPOP.csv"
OUT_SWITCH_MRANK = "/Users/Super007/Documents/sim_switch_MRANK.csv"


# =========================
# 1) 유틸
# =========================
def max_losing_streak(hit_series):
    mx = 0
    cur = 0
    for h in hit_series:
        if int(h) == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


def choose_product(
    row, weak_grades=None, weak_distances=None, require_new_cnt_zero=True
):
    """
    반환: "삼쌍" or "삼복"
    - 취약 구간이면 삼복
    - 그 외 삼쌍
    """
    if weak_grades is None:
        # ✅ 취약 등급(네 데이터 표기대로 확장 가능)
        weak_grades = {
            "국6",
            "OPEN",
            "국OPEN",
            "혼OPEN",
            "혼합",
            "혼3",
            "혼4",
        }  # 필요시 정리
    if weak_distances is None:
        # ✅ 취약 거리
        weak_distances = {1200}

    grade = str(row.get("등급", "")).strip()
    dist = row.get("경주거리", None)
    new_cnt = int(row.get("신마수", 0))

    # 거리 NaN 방어
    try:
        dist_int = int(dist) if pd.notna(dist) else None
    except Exception:
        dist_int = None

    # 1) 신마 0두만 삼쌍 허용(권장)
    if require_new_cnt_zero and new_cnt != 0:
        return "삼복"

    # 2) 취약 등급 제외
    if grade in weak_grades:
        return "삼복"

    # 3) 취약 거리 제외
    if dist_int in weak_distances:
        return "삼복"

    return "삼쌍"


def simulate_switching(
    out_df: pd.DataFrame,
    basis="RPOP",  # "RPOP" or "MRANK"
    weak_grades=None,
    weak_distances=None,
    require_new_cnt_zero=True,
):
    """
    out_df: raw (경주별)
    basis: "RPOP" 또는 "MRANK"
    결과: (경주별 선택전략/환급/베팅 포함 df, 월별 요약 monthly, 전체요약 summary)
    """
    df = out_df.copy()

    # 정렬(연속미적중 계산용)
    df = df.sort_values(["년월", "경주일", "경주번호"]).reset_index(drop=True)

    hit_333 = f"{basis}_삼복_hit"
    refund_333 = f"{basis}_삼복_환급"
    bet_333 = f"{basis}_삼복_경주당베팅액"

    hit_123 = f"{basis}_삼쌍_hit"
    refund_123 = f"{basis}_삼쌍_환급"
    bet_123 = f"{basis}_삼쌍_경주당베팅액"

    needed = {
        "년월",
        "등급",
        "경주거리",
        "신마수",
        "경주일",
        "경주번호",
        hit_333,
        refund_333,
        bet_333,
        hit_123,
        refund_123,
        bet_123,
    }
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise RuntimeError(f"raw에 필요한 컬럼이 없습니다: {missing}")

    # 경주별 선택
    df["선택전략"] = df.apply(
        choose_product,
        axis=1,
        weak_grades=weak_grades,
        weak_distances=weak_distances,
        require_new_cnt_zero=require_new_cnt_zero,
    )

    # 선택된 전략의 bet/refund/hit
    df["bet"] = df.apply(
        lambda r: r[bet_123] if r["선택전략"] == "삼쌍" else r[bet_333], axis=1
    )
    df["refund"] = df.apply(
        lambda r: r[refund_123] if r["선택전략"] == "삼쌍" else r[refund_333], axis=1
    )
    df["hit"] = df.apply(
        lambda r: r[hit_123] if r["선택전략"] == "삼쌍" else r[hit_333], axis=1
    )

    # 월별 요약
    monthly = (
        df.groupby("년월")
        .agg(
            races=("년월", "count"),
            hits=("hit", "sum"),
            bet=("bet", "sum"),
            refund=("refund", "sum"),
            tri123_races=("선택전략", lambda s: int((s == "삼쌍").sum())),
            tri333_races=("선택전략", lambda s: int((s == "삼복").sum())),
        )
        .reset_index()
        .sort_values("년월")
    )
    monthly["hit_rate"] = monthly["hits"] / monthly["races"]
    monthly["refund_rate"] = monthly["refund"] / monthly["bet"]
    monthly["roi"] = (monthly["refund"] - monthly["bet"]) / monthly["bet"]

    # 월별 최대 연속 미적중
    monthly_ls = (
        df.groupby("년월")["hit"]
        .apply(lambda s: max_losing_streak(s.tolist()))
        .reset_index(name="max_losing_streak")
    )
    monthly = monthly.merge(monthly_ls, on="년월", how="left")

    # 전체 요약
    total_bet = float(df["bet"].sum())
    total_refund = float(df["refund"].sum())
    total_hits = int(df["hit"].sum())
    total_races = int(len(df))
    refund_rate = total_refund / total_bet if total_bet > 0 else 0.0
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    hit_rate = total_hits / total_races if total_races > 0 else 0.0
    overall_max_ls = max_losing_streak(df["hit"].tolist())
    tri123_share = float((df["선택전략"] == "삼쌍").mean())

    summary = {
        "basis": basis,
        "races": total_races,
        "hits": total_hits,
        "hit_rate": hit_rate,
        "total_bet": total_bet,
        "total_refund": total_refund,
        "refund_rate": refund_rate,
        "roi": roi,
        "max_losing_streak_overall": overall_max_ls,
        "tri123_share": tri123_share,
    }
    return df, monthly, summary


def summarize_fixed(df, basis="RPOP", mode="삼쌍"):
    """비교용: 고정전략(전부 삼쌍 or 전부 삼복) 성과"""
    hit_col = f"{basis}_삼쌍_hit" if mode == "삼쌍" else f"{basis}_삼복_hit"
    refund_col = f"{basis}_삼쌍_환급" if mode == "삼쌍" else f"{basis}_삼복_환급"
    bet_col = (
        f"{basis}_삼쌍_경주당베팅액" if mode == "삼쌍" else f"{basis}_삼복_경주당베팅액"
    )

    total_bet = float(df[bet_col].sum())
    total_refund = float(df[refund_col].sum())
    total_hits = int(df[hit_col].sum())
    total_races = int(len(df))

    refund_rate = total_refund / total_bet if total_bet > 0 else 0.0
    roi = (total_refund - total_bet) / total_bet if total_bet > 0 else 0.0
    hit_rate = total_hits / total_races if total_races > 0 else 0.0

    return {
        "basis": basis,
        "mode": mode,
        "races": total_races,
        "hits": total_hits,
        "hit_rate": hit_rate,
        "total_bet": total_bet,
        "total_refund": total_refund,
        "refund_rate": refund_rate,
        "roi": roi,
    }


# =========================
# 2) 실행
# =========================
out_df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")

# 스위칭 (기본룰: 신마0 + 취약등급 + 1200 제외)
df_sw_rpop, m_sw_rpop, s_sw_rpop = simulate_switching(out_df, basis="RPOP")
df_sw_mrank, m_sw_mrank, s_sw_mrank = simulate_switching(out_df, basis="MRANK")

# 고정전략(비교)
fixed = []
fixed.append(summarize_fixed(out_df, basis="RPOP", mode="삼쌍"))
fixed.append(summarize_fixed(out_df, basis="RPOP", mode="삼복"))
fixed.append(summarize_fixed(out_df, basis="MRANK", mode="삼쌍"))
fixed.append(summarize_fixed(out_df, basis="MRANK", mode="삼복"))
fixed_df = pd.DataFrame(fixed)

# 출력
print("\n================== [스위칭 요약] ==================")
print(pd.DataFrame([s_sw_rpop, s_sw_mrank]))

print("\n================== [월별 스위칭 성과: RPOP] ==================")
print(
    m_sw_rpop[
        [
            "년월",
            "races",
            "tri123_races",
            "tri333_races",
            "hit_rate",
            "refund_rate",
            "roi",
            "max_losing_streak",
        ]
    ]
)

print("\n================== [월별 스위칭 성과: MRANK] ==================")
print(
    m_sw_mrank[
        [
            "년월",
            "races",
            "tri123_races",
            "tri333_races",
            "hit_rate",
            "refund_rate",
            "roi",
            "max_losing_streak",
        ]
    ]
)

print("\n================== [고정전략 비교] ==================")
print(fixed_df[["basis", "mode", "races", "hit_rate", "refund_rate", "roi"]])


# 개선폭(스위칭 - 고정 삼쌍)
def delta_vs_fixed_switch(s_switch, fixed_df, basis):
    fixed_tri123 = fixed_df[
        (fixed_df["basis"] == basis) & (fixed_df["mode"] == "삼쌍")
    ].iloc[0]
    return {
        "basis": basis,
        "Δrefund_rate_vs_all_tri123": s_switch["refund_rate"]
        - float(fixed_tri123["refund_rate"]),
        "Δroi_vs_all_tri123": s_switch["roi"] - float(fixed_tri123["roi"]),
        "Δhit_rate_vs_all_tri123": s_switch["hit_rate"]
        - float(fixed_tri123["hit_rate"]),
        "switch_tri123_share": s_switch["tri123_share"],
        "switch_max_losing_streak": s_switch["max_losing_streak_overall"],
    }


delta = pd.DataFrame(
    [
        delta_vs_fixed_switch(s_sw_rpop, fixed_df, "RPOP"),
        delta_vs_fixed_switch(s_sw_mrank, fixed_df, "MRANK"),
    ]
)
print("\n================== [개선폭: 스위칭 vs 전부 삼쌍] ==================")
print(delta)

# 결과 저장
df_sw_rpop.to_csv(OUT_SWITCH_RPOP, index=False, encoding="utf-8-sig")
df_sw_mrank.to_csv(OUT_SWITCH_MRANK, index=False, encoding="utf-8-sig")
print(f"\n▶ 저장 완료: {OUT_SWITCH_RPOP}")
print(f"▶ 저장 완료: {OUT_SWITCH_MRANK}")
