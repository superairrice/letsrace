"""월분할_환수율.py 기반 + 기수별 r_pop 1 단승식 환수율 집계 추가."""

import os
import re
import importlib.util
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_SCRIPT_PATH = Path(__file__).resolve().with_name("월분할_환수율.py")
DEFAULT_JOCKEY_OUTPUT_PATH = "/Users/Super007/Documents/r_pop1_기수별_환수율.csv"
BET_UNIT = 100


def _load_base_module():
    spec = importlib.util.spec_from_file_location("monthly_roi_base", BASE_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_r1alloc_odds(value) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)$", text)
    if not match:
        return 0.0
    try:
        return float(match.group(1))
    except Exception:
        return 0.0


def build_jockey_rpop1_roi_df(from_date: str, to_date: str) -> pd.DataFrame:
    from django.db import connection

    sql = """
        SELECT
            b.jockey,
            b.r_rank,
            c.r1alloc
        FROM exp011 b
        JOIN rec010 c
          ON b.rcity = c.rcity
         AND b.rdate = c.rdate
         AND b.rno = c.rno
        WHERE b.rdate BETWEEN %s AND %s
          AND b.r_pop = 1
          AND b.r_rank BETWEEN 1 AND 99
          AND b.jockey IS NOT NULL
          AND b.jockey <> ''
        ORDER BY b.jockey, b.rdate, b.rno
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, (from_date, to_date))
        fetched = cursor.fetchall()

    stats = {}
    for jockey, r_rank, r1alloc in fetched:
        item = stats.setdefault(
            str(jockey).strip(),
            {
                "기수": str(jockey).strip(),
                "출주수": 0,
                "1위수": 0,
                "총베팅액": 0.0,
                "총환수액": 0.0,
            },
        )
        item["출주수"] += 1
        item["총베팅액"] += BET_UNIT
        if int(r_rank or 0) == 1:
            item["1위수"] += 1
            item["총환수액"] += _parse_r1alloc_odds(r1alloc) * BET_UNIT

    rows = []
    for item in stats.values():
        total_bet = float(item["총베팅액"])
        total_refund = float(item["총환수액"])
        starts = int(item["출주수"])
        wins = int(item["1위수"])
        roi = (total_refund / total_bet) if total_bet > 0 else 0.0
        rows.append(
            {
                **item,
                "적중률": (wins / starts) if starts > 0 else 0.0,
                "적중률_pct": ((wins / starts) * 100.0) if starts > 0 else 0.0,
                "이익금액": total_refund - total_bet,
                "환수율": roi,
                "환수율_pct": roi * 100.0,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values(
        by=["출주수", "환수율_pct", "1위수", "기수"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    return df


def print_jockey_rpop1_roi(df: pd.DataFrame, from_date: str, to_date: str) -> None:
    print(f"[기수별 r_pop 1 단승식 환수율]  집계기간: {from_date} ~ {to_date}")
    if df.empty:
        print("데이터 없음")
        return

    for row in df.to_dict("records"):
        print(
            f"{row['기수']}  "
            f"출주수: {int(row['출주수'])}  "
            f"1위수: {int(row['1위수'])}  "
            f"적중률: {float(row['적중률_pct']):.1f}%  "
            f"총베팅액: {float(row['총베팅액']):,.0f}원  "
            f"총환수액: {float(row['총환수액']):,.0f}원  "
            f"이익금액: {float(row['이익금액']):,.0f}원  "
            f"환수율: {float(row['환수율']):.3f}"
        )


def save_jockey_rpop1_roi_df(
    df: pd.DataFrame, output_path: str = DEFAULT_JOCKEY_OUTPUT_PATH
) -> None:
    if df.empty:
        return
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"▶ 기수별 r_pop 1 환수율 CSV 저장: {output_path}")


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "letsrace.settings")

    import django
    from django.db import connections

    django.setup()

    base_module = _load_base_module()
    base_module.main()

    df = build_jockey_rpop1_roi_df(
        base_module.DEFAULT_FROM_DATE,
        base_module.DEFAULT_TO_DATE,
    )
    print_jockey_rpop1_roi(
        df,
        base_module.DEFAULT_FROM_DATE,
        base_module.DEFAULT_TO_DATE,
    )
    save_jockey_rpop1_roi_df(df)
    connections.close_all()


if __name__ == "__main__":
    main()
