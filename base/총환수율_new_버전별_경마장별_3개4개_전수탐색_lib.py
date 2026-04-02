"""총환수율_new.py 베팅 로직을 버전별 예상순위로 재계산하는 공용 유틸."""

import contextlib
import io
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import 총환수율_new as base_mod
import 총환수율_new_경마장별_3개4개_전수탐색 as combo_mod
from apps.domains.prediction.compute_gpt import (
    process_race,
    process_race_v2,
    process_race_v4,
    process_race_v5,
)


DEFAULT_FROM_DATE = combo_mod.DEFAULT_FROM_DATE
DEFAULT_TO_DATE = combo_mod.DEFAULT_TO_DATE
TRACK_ORDER = combo_mod.TRACK_ORDER
COMBO_SIZES = combo_mod.COMBO_SIZES
DEFAULT_TOP_N = combo_mod.DEFAULT_TOP_N

PROFILE_PROCESSORS = {
    "v0": process_race_v5,
    "v1": process_race,
    "v2": process_race_v2,
    "v4": process_race_v4,
}

PROFILE_DESCRIPTIONS = {
    "v0": "v0(UI) == 내부 v5 expected_rank 기준",
    "v1": "v1 expected_rank 기준",
    "v2": "v2 expected_rank 기준",
    "v4": "v4 expected_rank 기준",
}

V4_LIKE_EXP011_SQL = text(
    """
    SELECT
        e.rcity, e.rdate, e.rno, e.gate, e.horse, e.birthplace, e.h_sex, e.h_age, e.handycap,
        e.joc_adv, e.jockey, e.trainer, e.host, e.rating, e.prize_tot, e.prize_year, e.prize_half,
        e.tot_1st, e.tot_2nd, e.tot_3rd, e.tot_race, e.year_1st, e.year_2nd, e.year_3rd, e.year_race,
        IF(f_s2t(e.recent3) = 0, f_s2t(e.recent5), f_s2t(e.recent3)) AS recent3,
        f_s2t(e.recent5) AS recent5,
        IF(f_s2t(e.fast_r) = 0, f_s2t(e.recent5), f_s2t(e.fast_r)) AS fast_r,
        IF(f_s2t(e.slow_r) = 0, f_s2t(e.recent5), f_s2t(e.slow_r)) AS slow_r,
        IF(f_s2t(e.avg_r) = 0, f_s2t(e.recent5), f_s2t(e.avg_r)) AS avg_r,
        e.rs1f, e.r1c, e.r2c, e.r3c, e.r4c, e.rg3f, e.rg2f, e.rg1f,
        e.cs1f, e.cg3f, e.cg2f, e.cg1f, e.rank, e.i_s1f, e.i_g3f, e.i_g2f, e.i_g1f,
        e.i_jockey, e.i_cycle, e.i_prehandy, e.remark, e.s1f_rank, e.g2f_rank,
        e.h_weight, e.j_per, e.t_per, e.jt_per, e.jt_cnt, e.jt_1st, e.jt_2nd, e.jt_3rd,
        x.distance
    FROM The1.exp011 AS e
    JOIN The1.exp010 AS x
      ON x.rcity = e.rcity
     AND x.rdate = e.rdate
     AND x.rno = e.rno
    WHERE e.rdate BETWEEN :from_date AND :to_date
      AND e.rank < 98
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
)


def get_processor(profile: str):
    normalized = str(profile or "").strip().lower()
    if normalized not in PROFILE_PROCESSORS:
        raise ValueError(f"unsupported profile: {profile}")
    return normalized, PROFILE_PROCESSORS[normalized]


def load_prediction_df(
    profile: str,
    from_date: str = DEFAULT_FROM_DATE,
    to_date: str = DEFAULT_TO_DATE,
) -> pd.DataFrame:
    """기간 내 exp011 raw row를 지정 프로파일로 재계산해 gate별 expected_rank를 만든다."""
    normalized, processor = get_processor(profile)
    engine = base_mod.get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            V4_LIKE_EXP011_SQL,
            {"from_date": from_date, "to_date": to_date},
        ).fetchall()

    grouped_rows = {}
    for row in rows:
        row_tuple = tuple(row)
        race_key = (str(row_tuple[0]), str(row_tuple[1]), int(row_tuple[2]))
        grouped_rows.setdefault(race_key, []).append(row_tuple)

    predictions = []
    for exp011_rows in grouped_rows.values():
        for item in processor(exp011_rows):
            predictions.append(
                {
                    "경마장": str(item["rcity"]),
                    "경주일": str(item["rdate"]),
                    "경주번호": int(item["rno"]),
                    "마번": int(item["gate"]),
                    f"r_pop_{normalized}": int(item["expected_rank"]),
                }
            )

    return pd.DataFrame(
        predictions,
        columns=["경마장", "경주일", "경주번호", "마번", f"r_pop_{normalized}"],
    )


def build_result_df(
    profile: str,
    from_date: str = DEFAULT_FROM_DATE,
    to_date: str = DEFAULT_TO_DATE,
) -> pd.DataFrame:
    """총환수율_new.py 결과 테이블에 지정 버전 예상순위를 주입한다."""
    normalized, _processor = get_processor(profile)
    rank_col = f"r_pop_{normalized}"

    engine = base_mod.get_engine()
    base_df = base_mod.load_result_data_from_db(
        engine, from_date=from_date, to_date=to_date
    )
    if base_df.empty:
        return base_df

    pred_df = load_prediction_df(
        normalized,
        from_date=from_date,
        to_date=to_date,
    )
    merged = base_df.merge(
        pred_df,
        on=["경마장", "경주일", "경주번호", "마번"],
        how="left",
    )

    missing_mask = merged[rank_col].isna() & (
        pd.to_numeric(merged["rank"], errors="coerce") < 98
    )
    missing_count = int(missing_mask.sum())
    if missing_count:
        missing_rows = merged.loc[
            missing_mask,
            ["경마장", "경주일", "경주번호", "마번", "rank"],
        ].head(10)
        raise RuntimeError(
            f"{normalized} 예상순위 생성 누락 "
            f"{missing_count}건\n{missing_rows.to_string(index=False)}"
        )

    merged["r_pop"] = (
        pd.to_numeric(merged[rank_col], errors="coerce")
        .fillna(pd.to_numeric(merged["rank"], errors="coerce"))
        .astype(int)
    )
    return merged.drop(columns=[rank_col])


def load_race_df_for_profile(
    profile: str,
    from_date: str = DEFAULT_FROM_DATE,
    to_date: str = DEFAULT_TO_DATE,
) -> pd.DataFrame:
    """지정 버전 예상순위를 사용해 총환수율_new.py의 베팅 계산 결과를 만든다."""
    os.environ["DJANGO_SETTINGS_MODULE"] = "letsrace.settings"

    injected_df = build_result_df(
        profile=profile,
        from_date=from_date,
        to_date=to_date,
    )

    original_loader = base_mod.load_result_data_from_db
    original_upsert = base_mod.upsert_weekly_betting_summary
    original_to_csv = pd.DataFrame.to_csv
    original_excluded = base_mod.EXCLUDED_STRATEGY_KEYS

    try:
        base_mod.load_result_data_from_db = (
            lambda engine, from_date, to_date: injected_df.copy()
        )
        base_mod.upsert_weekly_betting_summary = lambda *args, **kwargs: None
        pd.DataFrame.to_csv = lambda self, *args, **kwargs: None
        base_mod.EXCLUDED_STRATEGY_KEYS = set()
        with contextlib.redirect_stdout(io.StringIO()):
            race_df, _summary = base_mod.calc_rpop_anchor_26_trifecta(
                from_date=from_date,
                to_date=to_date,
                bet_unit=100,
                apply_odds_filter=False,
            )
        return race_df
    finally:
        base_mod.load_result_data_from_db = original_loader
        base_mod.upsert_weekly_betting_summary = original_upsert
        pd.DataFrame.to_csv = original_to_csv
        base_mod.EXCLUDED_STRATEGY_KEYS = original_excluded


def run_profile(profile: str) -> None:
    normalized, _processor = get_processor(profile)
    race_df = load_race_df_for_profile(normalized)
    profile_desc = PROFILE_DESCRIPTIONS[normalized]
    print(
        f"[기간] {DEFAULT_FROM_DATE} ~ {DEFAULT_TO_DATE}  "
        f"({profile_desc}, 총환수율_new.py 기본 규칙: 13두 이상 / 신마 3두 이상 제외)"
    )

    for track_name in TRACK_ORDER:
        track_df = race_df[race_df["경마장"] == track_name].copy()
        if track_df.empty:
            continue

        print(f"[{track_name}]")
        for combo_size in COMBO_SIZES:
            top_results = combo_mod.find_top_combos(
                track_df,
                combo_size=combo_size,
                top_n=DEFAULT_TOP_N,
            )
            if not top_results:
                continue
            combo_mod.print_combo_result(
                f"[{normalized} {combo_size}개 최고 ROI]",
                top_results[0],
            )
            combo_mod.print_saturday_summary(
                track_name,
                combo_size,
                track_df,
                top_results[0],
            )
        print()
