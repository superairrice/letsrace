from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from contextlib import closing
import os

import pandas as pd
import pymysql

DB_CONF = {
    "host": os.getenv(
        "LETSRACE_DB_HOST",
        "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com",
    ),
    "port": int(os.getenv("LETSRACE_DB_PORT", "3306")),
    "user": os.getenv("LETSRACE_DB_USER", "letslove"),
    "password": os.getenv("LETSRACE_DB_PASSWORD", "Ruddksp!23"),
    "db": os.getenv("LETSRACE_DB_NAME", "The1"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}


def get_conn():
    return pymysql.connect(**DB_CONF)


# =========================
# 1) 판정 규칙 (미세조정 버전)
# =========================
def long_grade(long_top3_rate: float) -> str:
    """
    장기 기본 등급
    - PASS : 장기 3위내율 >= 0.65
    - WATCH: 0.55 ~ 0.65
    - STOP : < 0.55
    """
    if long_top3_rate >= 0.65:
        return "PASS"
    if long_top3_rate >= 0.55:
        return "WATCH"
    return "STOP"


def short_state(short_fail_cnt: int) -> str:
    """
    단기 컨디션(최근 10회 기준 실패 횟수)
    - HOT  : 실패 0~1
    - WARM : 실패 2
    - COLD : 실패 >=3
    """
    if short_fail_cnt <= 1:
        return "HOT"
    if short_fail_cnt == 2:
        return "WARM"
    return "COLD"


def final_decision(long_g: str, short_fail_cnt: int) -> Tuple[str, int]:
    """
    최종 스위치 (final_switch 숫자 포함)
    - +1 : PASS(축 가능)
    -  0 : WATCH(축 주의)
    - -1 : STOP(축 금지/단기악화)
    규칙:
    1) 단기 실패 >= 3 이면 무조건 STOP(단기악화)
    2) 그 외에는 장기 등급에 따라 PASS/WATCH/STOP
       - 장기 PASS + 단기 실패 0~1 => PASS
       - 장기 PASS + 단기 실패 2   => WATCH
       - 장기 WATCH                => WATCH (단기 실패 0~2인 경우)
       - 장기 STOP                 => STOP
    """
    # 단기 붕괴면 장기 상관없이 컷
    if short_fail_cnt >= 3:
        return "STOP(단기악화)", -1

    # 단기 0~2 범위
    if long_g == "STOP":
        return "STOP(축 금지)", -1

    if long_g == "WATCH":
        return "WATCH(축 주의)", 0

    # long_g == "PASS"
    if short_fail_cnt == 2:
        return "WATCH(단기경고)", 0
    return "PASS(축 OK)", +1


# =========================
# 2) 입력/출력 구조
# =========================
@dataclass
class JockeyStat:
    name: str

    # 장기(전체)
    long_n: int
    long_win: int
    long_top3: int
    long_top3_rate: float
    long_fail4: int
    long_fail4_rate: float
    long_avg_odds: float
    long_avg_pop: float

    # 단기(최근10 등)
    short_n: int
    short_win: int
    short_top3: int
    short_top3_rate: float
    short_fail4: int
    short_fail4_rate: float
    short_avg_odds: float
    short_avg_pop: float

    # 파생
    long_grade: str
    short_state: str
    final_label: str
    final_switch: int


def compute_jockey(row: Dict[str, Any]) -> JockeyStat:
    """
    row 예시(키):
      name,
      long_n,long_win,long_top3,long_top3_rate,long_fail4,long_fail4_rate,long_avg_odds,long_avg_pop,
      short_n,short_win,short_top3,short_top3_rate,short_fail4,short_fail4_rate,short_avg_odds,short_avg_pop
    """
    lg = long_grade(float(row["long_top3_rate"]))
    ss = short_state(int(row["short_fail4"]))
    flabel, fswitch = final_decision(lg, int(row["short_fail4"]))

    return JockeyStat(
        name=str(row["name"]),
        long_n=int(row["long_n"]),
        long_win=int(row["long_win"]),
        long_top3=int(row["long_top3"]),
        long_top3_rate=float(row["long_top3_rate"]),
        long_fail4=int(row["long_fail4"]),
        long_fail4_rate=float(row["long_fail4_rate"]),
        long_avg_odds=float(row["long_avg_odds"]),
        long_avg_pop=float(row["long_avg_pop"]),
        short_n=int(row["short_n"]),
        short_win=int(row["short_win"]),
        short_top3=int(row["short_top3"]),
        short_top3_rate=float(row["short_top3_rate"]),
        short_fail4=int(row["short_fail4"]),
        short_fail4_rate=float(row["short_fail4_rate"]),
        short_avg_odds=float(row["short_avg_odds"]),
        short_avg_pop=float(row["short_avg_pop"]),
        long_grade=lg,
        short_state=ss,
        final_label=flabel,
        final_switch=fswitch,
    )


def fetch_jockey_condition_by_race(
    from_date: str,
    to_date: str,
    history_from: Optional[str] = None,
    history_to: Optional[str] = None,
    conn: Optional[pymysql.connections.Connection] = None,
    debug: bool = False,
    entity: str = "jockey",
) -> pd.DataFrame:
    if history_from is None:
        history_from = "20231201"
    if history_to is None:
        history_to = from_date

    if entity not in ("jockey", "trainer"):
        raise ValueError("entity must be 'jockey' or 'trainer'")

    sql = f"""
    WITH race_new AS (
      SELECT
        e.rcity,
        e.rdate,
        e.rno,
        SUM(e.rank >= 98) AS new_cnt
      FROM The1.exp011 e
      GROUP BY e.rcity, e.rdate, e.rno
    ),
    target AS (
      SELECT
        e.rcity,
        e.rdate,
        e.rno,
        e.{entity} AS entity_name
      FROM The1.exp011 e
      WHERE e.rdate BETWEEN %s AND %s
        AND e.r_pop = 1
    ),
    base AS (
      SELECT
        e.{entity} AS entity_name,
        e.rdate,
        e.rno,
        e.r_rank,
        e.alloc3r,
        ROW_NUMBER() OVER (
          PARTITION BY e.{entity}
          ORDER BY e.rdate DESC, e.rno DESC
        ) AS rn
      FROM The1.exp011 e
      JOIN race_new rn
        ON rn.rcity = e.rcity
       AND rn.rdate = e.rdate
       AND rn.rno = e.rno
      WHERE e.rdate < %s
        AND e.rdate >= %s
        AND e.r_pop = 1
        AND e.r_rank BETWEEN 1 AND 12
        AND e.alloc3r IS NOT NULL
        AND rn.new_cnt < 3
    ),
    long_agg AS (
      SELECT
        entity_name,
        COUNT(*) AS rides_l,
        SUM(r_rank = 1) AS win_l,
        SUM(r_rank <= 3) AS top3_l,
        ROUND(SUM(r_rank <= 3)/COUNT(*), 3) AS top3_rate_l,
        SUM(r_rank >= 4) AS fail4_l,
        ROUND(SUM(r_rank >= 4)/COUNT(*), 3) AS fail4_rate_l,
        ROUND(AVG(r_rank), 2) AS avg_rank_l,
        ROUND(AVG(alloc3r), 2) AS avg_place_odds_l,
        CASE
          WHEN COUNT(*) < 5 THEN 'WATCH(표본부족)'
          WHEN (SUM(r_rank >= 4)/COUNT(*)) >= 0.30 THEN 'STOP(축 금지)'
          WHEN (SUM(r_rank <= 3)/COUNT(*)) >= 0.60
               AND (SUM(r_rank >= 4)/COUNT(*)) <= 0.10
            THEN 'PASS(축 OK)'
          ELSE 'WATCH(축 주의)'
        END AS grade_long
      FROM base
      GROUP BY entity_name
    ),
    short_agg AS (
      SELECT
        entity_name,
        COUNT(*) AS rides_s,
        SUM(r_rank = 1) AS win_s,
        SUM(r_rank <= 3) AS top3_s,
        ROUND(SUM(r_rank <= 3)/COUNT(*), 3) AS top3_rate_s,
        SUM(r_rank >= 4) AS fail4_s,
        ROUND(SUM(r_rank >= 4)/COUNT(*), 3) AS fail4_rate_s,
        ROUND(AVG(r_rank), 2) AS avg_rank_s,
        ROUND(AVG(alloc3r), 2) AS avg_place_odds_s,
        CASE
          WHEN COUNT(*) < 5 THEN 'NA(표본부족)'
          WHEN SUM(r_rank >= 4) >= 3 THEN 'COLD'
          WHEN (SUM(r_rank <= 3)/COUNT(*)) >= 0.60 AND SUM(r_rank >= 4) <= 1 THEN 'HOT'
          ELSE 'WARM'
        END AS grade_short
      FROM base
      WHERE rn <= 10
      GROUP BY entity_name
    )
    SELECT
      t.rcity,
      t.rdate,
      t.rno,
      t.entity_name AS {entity},

      COALESCE(l.rides_l, 0) AS rides_l,
      COALESCE(l.win_l, 0) AS win_l,
      COALESCE(l.top3_l, 0) AS top3_l,
      COALESCE(l.top3_rate_l, 0) AS top3_rate_l,
      COALESCE(l.fail4_l, 0) AS fail4_l,
      COALESCE(l.fail4_rate_l, 0) AS fail4_rate_l,
      l.avg_rank_l, l.avg_place_odds_l,
      COALESCE(l.grade_long, 'WATCH(표본부족)') AS grade_long,

      COALESCE(s.rides_s, 0) AS rides_s,
      COALESCE(s.win_s, 0) AS win_s,
      COALESCE(s.top3_s, 0) AS top3_s,
      COALESCE(s.top3_rate_s, 0) AS top3_rate_s,
      COALESCE(s.fail4_s, 0) AS fail4_s,
      COALESCE(s.fail4_rate_s, 0) AS fail4_rate_s,
      s.avg_rank_s, s.avg_place_odds_s,
      COALESCE(s.grade_short, 'NA(표본부족)') AS grade_short,

      CASE
        WHEN COALESCE(l.grade_long, 'WATCH(표본부족)') LIKE 'STOP%%' THEN 'STOP(축 금지)'
        WHEN COALESCE(s.rides_s,0) >= 5 AND s.fail4_s >= 3 THEN 'STOP(단기악화)'
        WHEN COALESCE(s.rides_s,0) >= 5 AND s.fail4_s = 2 THEN 'WATCH(단기경고)'
        WHEN COALESCE(l.grade_long, 'WATCH(표본부족)') LIKE 'PASS%%'
             AND COALESCE(l.rides_l,0) >= 30
             AND COALESCE(s.rides_s,0) >= 5
             AND s.fail4_s <= 1
          THEN 'PASS(축 OK)'
        WHEN COALESCE(l.grade_long, 'WATCH(표본부족)') LIKE 'PASS%%'
             AND COALESCE(l.rides_l,0) < 30
          THEN 'WATCH(PASS-표본적음)'
        ELSE COALESCE(l.grade_long, 'WATCH(표본부족)')
      END AS final_switch

    FROM target t
    LEFT JOIN long_agg l ON l.entity_name = t.entity_name
    LEFT JOIN short_agg s ON s.entity_name = t.entity_name
    ORDER BY t.rdate, t.rno, t.entity_name
    """

    params = [from_date, to_date, history_to, history_from]
    if conn is None:
        with closing(get_conn()) as conn:
            df = pd.read_sql(sql, conn, params=params)
            if debug:
                debug_sql = """
                SELECT e.rdate, COUNT(*) AS cnt
                FROM The1.exp011 e
                WHERE e.rdate BETWEEN %s AND %s
                  AND e.r_pop = 1
                GROUP BY e.rdate
                ORDER BY e.rdate
                """
                debug_df = pd.read_sql(debug_sql, conn, params=[from_date, to_date])
                print(f"[DEBUG] entity: {entity}")
                print(f"[DEBUG] target 기간: {from_date}~{to_date}")
                print(f"[DEBUG] target 건수: {len(df)}")
                print(debug_df.to_string(index=False))
            return df
    return pd.read_sql(sql, conn, params=params)


# =========================
# 3) 네가 올린 "한 줄" 형태 파서 (옵션)
# =========================
def parse_line_csvlike(line: str) -> Dict[str, Any]:
    """
    입력 예시 (쉼표로 구분된 한 줄):
      다나카, 78, 37, 60, 0.769, 4, 0.051, 2.59, 1.74, PASS(축 OK), 10, 5, 6, 0.600, 1, 0.100, 3.30, 1.46, HOT, PASS(축 OK)

    여기서 우리는:
      - 앞의 9개: 장기 지표
      - 그 다음 텍스트 1개는 기존 라벨이라 무시(있어도 됨)
      - 다음 8개: 단기 지표
      - 뒤의 텍스트들은 무시(있어도 됨)
    """
    parts = [p.strip() for p in line.split(",")]
    # 최소: name + 8(long nums) + 1(long label optional) + 8(short nums) = 18 이상이 보통
    # name + 8 long + 8 short = 17 이면 라벨 없이 온 케이스도 처리
    name = parts[0]

    # 장기 숫자 8개 + 비율 1개 포함 총 8? (네 포맷은 long이 8개 숫자 + top3_rate 등 총 8개? 실제는 8개+??)
    # 네 데이터는 장기: n, win, top3, top3_rate, fail4, fail4_rate, avg_odds, avg_pop (총 8개) -> name 포함하면 9칸
    # 즉 parts[1:9]가 장기 8개
    long_vals = parts[1:9]

    # 다음이 라벨일 수도 있고, 곧바로 short_n(숫자)일 수도 있음
    cursor = 9
    if cursor < len(parts) and not parts[cursor].replace(".", "", 1).isdigit():
        # 라벨 한 칸 스킵
        cursor += 1

    short_vals = parts[cursor : cursor + 8]
    if len(short_vals) < 8:
        raise ValueError(
            f"short 값이 부족합니다. cursor={cursor}, len(parts)={len(parts)}"
        )

    row = {
        "name": name,
        "long_n": long_vals[0],
        "long_win": long_vals[1],
        "long_top3": long_vals[2],
        "long_top3_rate": long_vals[3],
        "long_fail4": long_vals[4],
        "long_fail4_rate": long_vals[5],
        "long_avg_odds": long_vals[6],
        "long_avg_pop": long_vals[7],
        "short_n": short_vals[0],
        "short_win": short_vals[1],
        "short_top3": short_vals[2],
        "short_top3_rate": short_vals[3],
        "short_fail4": short_vals[4],
        "short_fail4_rate": short_vals[5],
        "short_avg_odds": short_vals[6],
        "short_avg_pop": short_vals[7],
    }
    return row


# =========================
# 4) 사용 예시
# =========================
if __name__ == "__main__":
    jockey_df = fetch_jockey_condition_by_race(
        "20260123", "20260125", debug=True, entity="jockey"
    )
    print("=== JOCKEY ===")
    print(jockey_df.head(40).to_string(index=False))

    trainer_df = fetch_jockey_condition_by_race(
        "20260123", "20260125", entity="trainer"
    )
    print("=== TRAINER ===")
    print(trainer_df.head(40).to_string(index=False))
