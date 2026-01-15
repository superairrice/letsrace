#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_meta_box_guide.py

META(rcity, grade, distance)별로
  rBOX4 / rBOX5 / rBOX6 / A4 / A5 / A6
6개 케이스의 삼복승식 성과를 계산하여 The1.meta_box_guide에 저장.

- 실제순위: rec011.rank (1~3위 게이트)
- 삼복승식 배당률(odds): rec010.r333alloc1  ✅ (환급금이 아니라 "배당률")
- 예측순위: exp011.r_pop (작을수록 좋음)

저장 단위:
  (rcity, grade, distance, rec) 1행

베팅금 계산(기본 bet_unit=100):
  BOX4 : C(4,3)=4  -> 400
  BOX5 : C(5,3)=10 -> 1000
  BOX6 : C(6,3)=20 -> 2000
  A4   : C(4,2)=6  -> 600   (anchor 포함 조합)
  A5   : C(5,2)=10 -> 1000
  A6   : C(6,2)=15 -> 1500

HIT 조건:
  BOXn: top3 ⊆ selected
  An  : anchor ∈ top3 AND (top3 - {anchor}) ⊆ followers

Refund(환급금):
  ✅ hit 시 refund += (bet_unit * r333alloc1)
     (r333alloc1이 "배당률"이므로 bet_unit을 곱해 환급금으로 변환)

RR(refund_rate) = refund / bet
ROI = RR - 1
HR = hit / races

Usage:
  - 기간(dry):   python make_meta_box_guide.py --from_date 20231201 --to_date 20251130 --dry_run
  - 기간(commit):python make_meta_box_guide.py --from_date 20231201 --to_date 20251130
"""

import os
import argparse
from contextlib import closing
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any

import pymysql


# =========================
# 0) DB
# =========================
DB_CONF = {
    "host": os.getenv(
        "MYSQL_HOST", "database-1.c35iunxhbvd4.ap-northeast-2.rds.amazonaws.com"
    ),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "letslove"),
    "password": os.getenv("MYSQL_PASSWORD", "Ruddksp!23"),
    "db": os.getenv("MYSQL_DB", "The1"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}


def get_conn():
    conn = pymysql.connect(**DB_CONF)
    try:
        conn.ping(reconnect=True)
    except Exception:
        pass
    return conn


def get_conn():
    conn = pymysql.connect(**DB_CONF)
    try:
        conn.ping(reconnect=True)
    except Exception:
        pass
    return conn


def log(msg: str) -> None:
    print(msg, flush=True)


# =========================
# 1) Schema utils
# =========================
def has_column(conn, table: str, column: str, schema: Optional[str] = None) -> bool:
    db = schema or DB_CONF["db"]
    sql = """
        SELECT 1
          FROM information_schema.COLUMNS
         WHERE TABLE_SCHEMA=%s
           AND TABLE_NAME=%s
           AND COLUMN_NAME=%s
         LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, (db, table, column))
        return cur.fetchone() is not None


def ensure_table_and_columns(conn) -> None:
    """
    meta_box_guide 테이블과 필요한 컬럼 보장.
    PK: (rcity, grade, distance, rec)
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS The1.meta_box_guide (
                rcity       VARCHAR(10)  NOT NULL,
                grade       VARCHAR(30)  NOT NULL,
                distance    INT          NOT NULL,
                rec         VARCHAR(20)  NOT NULL,

                races       INT          NOT NULL DEFAULT 0,
                bet         BIGINT       NOT NULL DEFAULT 0,
                refund      BIGINT       NOT NULL DEFAULT 0,
                hit         INT          NOT NULL DEFAULT 0,

                refund_rate DOUBLE       NOT NULL DEFAULT 0,
                roi         DOUBLE       NOT NULL DEFAULT 0,
                hr          DOUBLE       NOT NULL DEFAULT 0,

                sample_from VARCHAR(8)   NULL,
                sample_to   VARCHAR(8)   NULL,
                updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (rcity, grade, distance, rec)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

    # 구버전 테이블 방어
    need_cols = [
        ("races", "INT NOT NULL DEFAULT 0"),
        ("bet", "BIGINT NOT NULL DEFAULT 0"),
        ("refund", "BIGINT NOT NULL DEFAULT 0"),
        ("hit", "INT NOT NULL DEFAULT 0"),
        ("refund_rate", "DOUBLE NOT NULL DEFAULT 0"),
        ("roi", "DOUBLE NOT NULL DEFAULT 0"),
        ("hr", "DOUBLE NOT NULL DEFAULT 0"),
        ("sample_from", "VARCHAR(8) NULL"),
        ("sample_to", "VARCHAR(8) NULL"),
        ("updated_at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"),
    ]
    with conn.cursor() as cur:
        for col, ddl in need_cols:
            if not has_column(conn, "meta_box_guide", col, schema=DB_CONF["db"]):
                cur.execute(f"ALTER TABLE The1.meta_box_guide ADD COLUMN {col} {ddl}")
                log(f"[MIGRATE] added column: meta_box_guide.{col}")

    log("[INFO] ensured table+columns: The1.meta_box_guide")


# =========================
# 2) Load actual TOP3 from rec011.rank
# =========================
def load_top3_map(
    conn, from_date: str, to_date: str
) -> Dict[Tuple[str, str, int], List[int]]:
    """
    out[(rcity,rdate,rno)] = [gate1, gate2, gate3]
    """
    sql = """
        SELECT rcity, rdate, rno, gate, `rank`
          FROM The1.rec011
         WHERE rdate >= %s AND rdate <= %s
           AND `rank` IN (1,2,3)
    """
    tmp: Dict[Tuple[str, str, int], Dict[int, int]] = {}
    with conn.cursor() as cur:
        cur.execute(sql, (from_date, to_date))
        rows = cur.fetchall() or []

    for r in rows:
        key = (str(r["rcity"]), str(r["rdate"]), int(r["rno"]))
        rk = int(r["rank"])
        gate = int(r["gate"])
        tmp.setdefault(key, {})[rk] = gate

    out: Dict[Tuple[str, str, int], List[int]] = {}
    for k, d in tmp.items():
        if 1 in d and 2 in d and 3 in d:
            out[k] = [d[1], d[2], d[3]]

    log(f"[INFO] top3 loaded from rec011.rank: {len(out)} races")
    return out


# =========================
# 3) Load payout(odds) from rec010.r333alloc1
# =========================
def load_payout_map(
    conn, from_date: str, to_date: str
) -> Dict[Tuple[str, str, int], float]:
    """
    out[(rcity,rdate,rno)] = odds (float)  ✅ 배당률
    """
    if not has_column(conn, "rec010", "r333alloc1", schema=DB_CONF["db"]):
        raise RuntimeError("rec010.r333alloc1 column not found")

    sql = """
        SELECT rcity, rdate, rno, r333alloc1
          FROM The1.rec010
         WHERE rdate >= %s AND rdate <= %s
    """
    out: Dict[Tuple[str, str, int], float] = {}
    with conn.cursor() as cur:
        cur.execute(sql, (from_date, to_date))
        rows = cur.fetchall() or []

    for r in rows:
        key = (str(r["rcity"]), str(r["rdate"]), int(r["rno"]))
        val = r.get("r333alloc1")
        if val is None:
            continue
        try:
            out[key] = float(val)
        except Exception:
            continue

    log(f"[INFO] payout(odds) map loaded: {len(out)} races (rec010.r333alloc1)")
    return out


# =========================
# 4) Load predictions + meta from exp011 + exp010/rec010 distance fallback
# =========================
def get_distance_select_expr(conn) -> str:
    if has_column(conn, "exp010", "distance", schema=DB_CONF["db"]):
        return "COALESCE(r.distance, x.distance)"
    return "r.distance"


def load_exp011_rows(conn, from_date: str, to_date: str) -> List[dict]:
    dist_expr = get_distance_select_expr(conn)
    sql = f"""
        SELECT
            e.rcity, e.rdate, e.rno, e.gate, e.r_pop,
            x.grade AS grade,
            {dist_expr} AS distance
          FROM The1.exp011 e
          LEFT JOIN The1.exp010 x
            ON x.rcity=e.rcity AND x.rdate=e.rdate AND x.rno=e.rno
          LEFT JOIN The1.rec010 r
            ON r.rcity=e.rcity AND r.rdate=e.rdate AND r.rno=e.rno
         WHERE e.rdate >= %s AND e.rdate <= %s
         ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    with conn.cursor() as cur:
        cur.execute(sql, (from_date, to_date))
        return cur.fetchall() or []


# =========================
# 5) Strategy evaluator
# =========================
def comb(n: int, k: int) -> int:
    if n < 0 or k < 0 or n < k:
        return 0
    if k == 0 or k == n:
        return 1
    num = 1
    den = 1
    for i in range(1, k + 1):
        num *= n - (k - i)
        den *= i
    return num // den


@dataclass
class CaseResult:
    races: int = 0
    bet: int = 0
    refund: float = 0.0
    hit: int = 0


def eval_case_for_race(
    *,
    rec: str,
    sorted_gates: List[int],
    top3: List[int],
    odds: float,
    bet_unit: int,
) -> Tuple[int, int, float, int]:
    """
    return (races_inc(=1), bet_inc, refund_inc, hit_inc)

    ✅ odds는 배당률이므로, 적중 1구멍 환급금 = bet_unit * odds
    """
    rec = rec.strip()

    if not sorted_gates or len(sorted_gates) < 3 or not top3 or len(top3) != 3:
        return (1, 0, 0.0, 0)

    top3_set = set(top3)

    def add_if_hit(is_hit: bool, bet_amt: int) -> Tuple[int, int, float, int]:
        if not is_hit:
            return (1, bet_amt, 0.0, 0)
        refund_amt = float(bet_unit) * float(odds)  # ✅ 핵심 수정
        return (1, bet_amt, refund_amt, 1)

    # BOX*
    if rec.startswith("rBOX"):
        try:
            n = int(rec.replace("rBOX", ""))
        except Exception:
            return (1, 0, 0.0, 0)

        picks = sorted_gates[:n]
        bet_amt = bet_unit * comb(len(picks), 3)
        is_hit = top3_set.issubset(set(picks))
        return add_if_hit(is_hit, bet_amt)

    # A*
    if rec.startswith("A"):
        try:
            k = int(rec.replace("A", ""))
        except Exception:
            return (1, 0, 0.0, 0)

        if len(sorted_gates) < 2:
            return (1, 0, 0.0, 0)

        anchor = sorted_gates[0]
        followers = sorted_gates[1 : 1 + k]
        bet_amt = bet_unit * comb(len(followers), 2)

        if len(followers) < 2:
            return (1, bet_amt, 0.0, 0)

        if anchor not in top3_set:
            return add_if_hit(False, bet_amt)

        others = [g for g in top3 if g != anchor]
        is_hit = len(others) == 2 and set(others).issubset(set(followers))
        return add_if_hit(is_hit, bet_amt)

    return (1, 0, 0.0, 0)


# =========================
# 6) Build meta aggregates
# =========================
CASES = ["rBOX4", "rBOX5", "rBOX6", "A4", "A5", "A6"]


def safe_int(v, default=None):
    try:
        if v is None:
            return default
        s = str(v).strip()
        if s == "":
            return default
        return int(float(s))
    except Exception:
        return default


def build_meta_results(
    *,
    exp_rows: List[dict],
    top3_map: Dict[Tuple[str, str, int], List[int]],
    payout_map: Dict[Tuple[str, str, int], float],
    bet_unit: int,
) -> Dict[Tuple[str, str, int, str], CaseResult]:
    races: Dict[Tuple[str, str, int], List[dict]] = {}
    for r in exp_rows:
        key = (str(r["rcity"]), str(r["rdate"]), int(r["rno"]))
        races.setdefault(key, []).append(r)

    log(f"[INFO] races grouped={len(races)}")

    skipped_no_top3 = 0
    skipped_no_payout = 0
    skipped_no_meta = 0

    out: Dict[Tuple[str, str, int, str], CaseResult] = {}

    for (rcity, rdate, rno), rows in races.items():
        grade = (rows[0].get("grade") or "").strip()
        dist = safe_int(rows[0].get("distance"), None)
        if not grade or dist is None:
            skipped_no_meta += 1
            continue

        rk = (rcity, rdate, rno)
        top3 = top3_map.get(rk)
        if not top3:
            skipped_no_top3 += 1
            continue

        odds = payout_map.get(rk)
        if odds is None:
            skipped_no_payout += 1
            continue

        tmp = []
        for rr in rows:
            rp = safe_int(rr.get("r_pop"), 999999)
            g = safe_int(rr.get("gate"), 999999)
            if g is None:
                continue
            tmp.append((rp if rp and rp > 0 else 999999, g))
        tmp.sort()
        sorted_gates = [g for _, g in tmp]

        for rec in CASES:
            races_inc, bet_inc, refund_inc, hit_inc = eval_case_for_race(
                rec=rec,
                sorted_gates=sorted_gates,
                top3=top3,
                odds=odds,
                bet_unit=bet_unit,
            )
            mk = (rcity, grade, int(dist), rec)
            agg = out.setdefault(mk, CaseResult())
            agg.races += races_inc
            agg.bet += int(bet_inc)
            agg.refund += float(refund_inc)
            agg.hit += int(hit_inc)

    log(
        f"[INFO] skipped(no_meta)={skipped_no_meta}, skipped(no_top3)={skipped_no_top3}, skipped(no_payout)={skipped_no_payout}"
    )
    log(f"[INFO] meta keys computed={len(out)}")
    return out


# =========================
# 7) Upsert meta_box_guide
# =========================
def upsert_meta_box_guide(
    conn,
    meta_results: Dict[Tuple[str, str, int, str], CaseResult],
    sample_from: str,
    sample_to: str,
    dry_run: bool,
    batch_size: int = 2000,
) -> int:
    if not meta_results:
        return 0

    rows: List[Tuple[Any, ...]] = []
    for (rcity, grade, dist, rec), d in meta_results.items():
        bet = int(d.bet)
        refund = float(d.refund)
        hit = int(d.hit)
        races = int(d.races)

        rr = (refund / bet) if bet > 0 else 0.0
        roi = rr - 1.0
        hr = (hit / races) if races > 0 else 0.0

        rows.append(
            (
                rcity,
                grade,
                int(dist),
                rec,
                races,
                bet,
                int(round(refund)),  # BIGINT 저장
                hit,
                rr,
                roi,
                sample_from,
                sample_to,
                hr,
            )
        )

    if dry_run:
        log(f"[DRY_RUN] would upsert rows={len(rows)} (showing 10)")
        for s in rows[:10]:
            log(f"  {s}")
        return 0

    sql = """
        INSERT INTO The1.meta_box_guide
        (rcity, grade, distance, rec,
         races, bet, refund, hit,
         refund_rate, roi, sample_from, sample_to, hr,
         updated_at)
        VALUES
        (%s,%s,%s,%s,
         %s,%s,%s,%s,
         %s,%s,%s,%s,%s,
         NOW())
        ON DUPLICATE KEY UPDATE
            races=VALUES(races),
            bet=VALUES(bet),
            refund=VALUES(refund),
            hit=VALUES(hit),
            refund_rate=VALUES(refund_rate),
            roi=VALUES(roi),
            sample_from=VALUES(sample_from),
            sample_to=VALUES(sample_to),
            hr=VALUES(hr),
            updated_at=NOW()
    """

    affected = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            chunk = rows[i : i + batch_size]
            cur.executemany(sql, chunk)
            affected += cur.rowcount
    return affected


# =========================
# 8) Run
# =========================
def run(
    *,
    from_date: str,
    to_date: str,
    bet_unit: int,
    dry_run: bool,
    batch_size: int,
) -> None:
    with closing(get_conn()) as conn:
        try:
            ensure_table_and_columns(conn)

            top3_map = load_top3_map(conn, from_date, to_date)
            payout_map = load_payout_map(conn, from_date, to_date)
            exp_rows = load_exp011_rows(conn, from_date, to_date)

            meta_results = build_meta_results(
                exp_rows=exp_rows,
                top3_map=top3_map,
                payout_map=payout_map,
                bet_unit=bet_unit,
            )

            affected = upsert_meta_box_guide(
                conn,
                meta_results=meta_results,
                sample_from=from_date,
                sample_to=to_date,
                dry_run=dry_run,
                batch_size=batch_size,
            )

            if dry_run:
                conn.rollback()
                log("[DRY_RUN] done (rollback)")
            else:
                conn.commit()
                log(f"[COMMIT] done (affected={affected})")

        except Exception:
            conn.rollback()
            raise


# =========================
# 9) CLI
# =========================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from_date", required=True, help="YYYYMMDD")
    ap.add_argument("--to_date", required=True, help="YYYYMMDD")
    ap.add_argument("--bet_unit", type=int, default=100)
    ap.add_argument("--batch_size", type=int, default=2000)
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()

    run(
        from_date=args.from_date,
        to_date=args.to_date,
        bet_unit=args.bet_unit,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
