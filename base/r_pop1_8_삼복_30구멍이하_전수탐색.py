import os
from contextlib import closing
from pathlib import Path
from typing import Iterable

import pandas as pd
import pymysql


DB_CONF = {
    "host": "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",
    "port": 3306,
    "user": "letslove",
    "password": "Ruddksp!23",
    "db": "The1",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260420"
DEFAULT_BET_UNIT = 100
MAX_HOLES = 30
DEFAULT_OUTPUT_PATH = (
    Path("/Users/Super007/Documents") / "r_pop1_8_삼복_30구멍이하_전수탐색.csv"
)


def get_conn():
    conn = pymysql.connect(**DB_CONF)
    try:
        conn.ping(reconnect=True)
    except Exception:
        pass
    return conn


def load_result_data_from_db(conn, from_date: str, to_date: str) -> pd.DataFrame:
    sql = """
    SELECT
        e.rcity AS 경마장,
        e.rdate AS 경주일,
        e.rno AS 경주번호,
        e.gate AS 마번,
        x.grade AS 등급,
        e.rank AS rank,
        e.r_pop AS r_pop,
        e.r_rank AS r_rank,
        r.r333alloc1 AS 삼복승식배당율
    FROM The1.exp011 AS e
    LEFT JOIN The1.rec010 AS r
           ON r.rcity = e.rcity
          AND r.rdate = e.rdate
          AND r.rno   = e.rno
    LEFT JOIN The1.exp010 AS x
           ON x.rcity = e.rcity
          AND x.rdate = e.rdate
          AND x.rno   = e.rno
    WHERE e.rdate >= %s
      AND e.rdate <= %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    return pd.read_sql(sql, conn, params=[from_date, to_date])


def _format_rank_group(values: Iterable[int]) -> str:
    nums = sorted(set(int(v) for v in values))
    if not nums:
        return "-"
    chunks = []
    start = nums[0]
    prev = nums[0]
    for num in nums[1:]:
        if num == prev + 1:
            prev = num
            continue
        chunks.append(f"{start}~{prev}" if start != prev else str(start))
        start = prev = num
    chunks.append(f"{start}~{prev}" if start != prev else str(start))
    return ",".join(chunks)


def _strategy_label(first: tuple[int, ...], second: tuple[int, ...], third: tuple[int, ...]) -> str:
    return (
        f"1군({_format_rank_group(first)}) / "
        f"2군({_format_rank_group(second)}) / "
        f"3군({_format_rank_group(third)}) 삼복"
    )


def _generate_strategies(max_rank: int = 8, max_holes: int = MAX_HOLES):
    strategies = []

    def walk(rank: int, first: list[int], second: list[int], third: list[int]) -> None:
        if rank > max_rank:
            if not first or not second or not third:
                return
            holes = len(first) * len(second) * len(third)
            if holes > max_holes:
                return
            first_t = tuple(first)
            second_t = tuple(second)
            third_t = tuple(third)
            strategies.append(
                {
                    "first": first_t,
                    "second": second_t,
                    "third": third_t,
                    "holes": holes,
                    "label": _strategy_label(first_t, second_t, third_t),
                    "max_rank": max(first_t[-1], second_t[-1], third_t[-1]),
                }
            )
            return

        walk(rank + 1, first, second, third)

        first.append(rank)
        if len(first) * max(1, len(second)) * max(1, len(third)) <= max_holes:
            walk(rank + 1, first, second, third)
        first.pop()

        second.append(rank)
        if max(1, len(first)) * len(second) * max(1, len(third)) <= max_holes:
            walk(rank + 1, first, second, third)
        second.pop()

        third.append(rank)
        if max(1, len(first)) * max(1, len(second)) * len(third) <= max_holes:
            walk(rank + 1, first, second, third)
        third.pop()

    walk(1, [], [], [])
    strategies.sort(
        key=lambda item: (
            item["holes"],
            len(item["first"]) + len(item["second"]) + len(item["third"]),
            item["first"],
            item["second"],
            item["third"],
        )
    )
    return strategies


def _load_race_rows(from_date: str, to_date: str) -> list[dict]:
    with closing(get_conn()) as conn:
        df = load_result_data_from_db(conn, from_date=from_date, to_date=to_date)

    if df.empty:
        return []

    df = df.copy()
    if "등급" in df.columns:
        df["등급"] = df["등급"].fillna("")
    else:
        df["등급"] = ""
    df = df[
        ~df["등급"].str.contains(r"(?:국OPEN|혼OPEN)", case=False, na=False, regex=True)
    ]
    df["경주일"] = df["경주일"].astype(str)
    df["경주번호"] = pd.to_numeric(df["경주번호"], errors="coerce").astype("Int64")
    df["마번"] = pd.to_numeric(df["마번"], errors="coerce").astype("Int64")

    for col in ["rank", "r_pop", "r_rank"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["경주번호", "마번", "rank", "r_pop", "r_rank"]).copy()

    df["경주번호"] = df["경주번호"].astype(int)
    df["마번"] = df["마번"].astype(int)
    df["rank"] = df["rank"].astype(int)
    df["r_pop"] = df["r_pop"].replace(0, 99).astype(int)
    df["r_rank"] = df["r_rank"].astype(int)
    df["삼복승식배당율"] = pd.to_numeric(df["삼복승식배당율"], errors="coerce").fillna(0.0)
    df["신마"] = (df["rank"] >= 98).astype(int)

    race_rows = []
    for (track, date, rno), g in df.groupby(["경마장", "경주일", "경주번호"], sort=False):
        g = g.copy()
        if len(g) >= 13:
            continue
        if int(g["신마"].sum()) >= 2:
            continue

        top_by_pop = g.sort_values(["r_pop", "마번"], ascending=[True, True])["마번"].tolist()
        actual_top3 = (
            g[g["r_rank"] <= 3]
            .sort_values(["r_rank", "마번"], ascending=[True, True])["마번"]
            .tolist()
        )
        if len(actual_top3) != 3:
            continue

        race_rows.append(
            {
                "경마장": track,
                "경주일": date,
                "경주번호": rno,
                "top_by_pop": top_by_pop,
                "actual_top3": tuple(actual_top3),
                "actual_top3_set": set(actual_top3),
                "odds": float(g["삼복승식배당율"].iloc[0] or 0.0),
            }
        )
    return race_rows


def _evaluate_strategies(race_rows: list[dict], strategies: list[dict], bet_unit: int) -> pd.DataFrame:
    results = []
    total_races = len(race_rows)
    for strategy in strategies:
        first = strategy["first"]
        second = strategy["second"]
        third = strategy["third"]
        holes = strategy["holes"]
        max_rank = strategy["max_rank"]
        first_idx = tuple(rank - 1 for rank in first)
        second_idx = tuple(rank - 1 for rank in second)
        third_idx = tuple(rank - 1 for rank in third)

        valid_races = 0
        hits = 0
        total_bet = 0.0
        total_refund = 0.0
        hit_examples = []

        for race in race_rows:
            top_by_pop = race["top_by_pop"]
            if len(top_by_pop) < max_rank:
                continue

            valid_races += 1
            total_bet += holes * bet_unit

            first_set = {top_by_pop[idx] for idx in first_idx}
            second_set = {top_by_pop[idx] for idx in second_idx}
            third_set = {top_by_pop[idx] for idx in third_idx}
            if not (first_set and second_set and third_set):
                continue

            actual = race["actual_top3_set"]
            if (
                actual & first_set
                and actual & second_set
                and actual & third_set
            ):
                hits += 1
                refund = race["odds"] * bet_unit
                total_refund += refund
                if len(hit_examples) < 3:
                    hit_examples.append(
                        f"{race['경마장']} {race['경주일']} {race['경주번호']}R {race['actual_top3']} @{race['odds']:.1f}"
                    )

        if valid_races == 0:
            continue

        profit = total_refund - total_bet
        results.append(
            {
                "전략명": strategy["label"],
                "1군": _format_rank_group(first),
                "2군": _format_rank_group(second),
                "3군": _format_rank_group(third),
                "구멍수": holes,
                "적용경주수": valid_races,
                "전체기준경주수": total_races,
                "적중수": hits,
                "적중률": (hits / valid_races) if valid_races > 0 else 0.0,
                "총베팅액": total_bet,
                "총환수액": total_refund,
                "이익금": profit,
                "환수율": (total_refund / total_bet) if total_bet > 0 else 0.0,
                "적중예시": " | ".join(hit_examples),
            }
        )

    result_df = pd.DataFrame(results)
    if result_df.empty:
        return result_df
    return result_df.sort_values(
        ["환수율", "이익금", "적중수", "구멍수"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)


def main():
    from_date = os.getenv("FROM_DATE", DEFAULT_FROM_DATE)
    to_date = os.getenv("TO_DATE", DEFAULT_TO_DATE)
    bet_unit = int(os.getenv("BET_UNIT", str(DEFAULT_BET_UNIT)))
    output_path = Path(os.getenv("OUTPUT_PATH", str(DEFAULT_OUTPUT_PATH)))

    race_rows = _load_race_rows(from_date=from_date, to_date=to_date)
    if not race_rows:
        print(f"▶ [{from_date} ~ {to_date}] 조건에 맞는 경주 데이터가 없습니다.")
        return

    strategies = _generate_strategies(max_rank=8, max_holes=MAX_HOLES)
    result_df = _evaluate_strategies(race_rows, strategies, bet_unit=bet_unit)
    if result_df.empty:
        print("▶ 평가 가능한 전략 결과가 없습니다.")
        return

    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 240)
    pd.set_option("display.max_colwidth", 120)

    print(
        f"[r_pop 1~8 삼복 전수탐색] 기간 {from_date}~{to_date}  "
        f"경주수 {len(race_rows)}  전략수 {len(result_df)}  구멍수<= {MAX_HOLES}"
    )
    print(result_df.to_string(index=False))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\nCSV 저장: {output_path}")


if __name__ == "__main__":
    main()
