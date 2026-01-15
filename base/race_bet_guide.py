#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_rguide_from_meta.py

exp010.r_guide update (META-only) from The1.meta_box_guide

Stored example:
META:서울,혼3등급,1800m | BEST:A4(52r,21.2%,RR1.526,ROI0.526) | ALT:A5(52r,19.2%,RR1.410,ROI0.410)

Selection rule (Option B: profit-first):
1) ROI desc
2) RR desc
3) HR desc
4) races desc
5) rBOX* preferred (tie-break)

Notes:
- Stored string is META + BEST (+ ALT if exists), delimiter " | "
- No Korean labels in stored string
- BOX5 supported (rBOX5 -> BOX5 display)
- exp010.distance exists? Use COALESCE(rec010.distance, exp010.distance)
"""

import os
import argparse
from contextlib import closing
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


def log(msg: str) -> None:
    print(msg, flush=True)


# =========================
# schema utils
# =========================
def has_column(conn, table: str, column: str, schema: Optional[str] = None) -> bool:
    db = schema or DB_CONF["db"]
    sql = """
        SELECT 1
          FROM information_schema.COLUMNS
         WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
         LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, (db, table, column))
        return cur.fetchone() is not None


def pick_existing_col(conn, table: str, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if has_column(conn, table, c, schema=DB_CONF["db"]):
            return c
    return None


def get_distance_select_expr(conn) -> str:
    """
    rec010.distance can be NULL.
    If exp010.distance exists, use COALESCE(rec010.distance, exp010.distance).
    """
    if has_column(conn, "exp010", "distance"):
        return "COALESCE(r.distance, x.distance)"
    return "r.distance"


def fmt3(x: Any) -> str:
    try:
        return f"{float(x):.3f}"
    except Exception:
        return "NA"


def humanize_case(case: str) -> str:
    """
    Display normalization:
      rBOX4/rBOX5/rBOX6 -> BOX4/BOX5/BOX6
      A4/A5/A6 -> as-is
    """
    if not case or str(case).strip() == "":
        return "-"
    s = str(case).strip()
    if s.startswith("rBOX"):
        return "BOX" + s[len("rBOX") :]
    return s


# =========================
# 1) meta stats map for BEST/ALT
# =========================
def load_meta_box_stats_map(conn) -> Dict[Tuple[str, str, int], Dict[str, dict]]:
    """
    out[(rcity, grade, distance)][rec] = {
        "races": int,
        "hit": Optional[int],
        "hr": Optional[float],
        "rr": Optional[float],   # refund_rate
        "roi": Optional[float],
    }

    Column flexibility:
      hit: hit / meta_hit / hits
      hr : hr  / meta_hr / hit_rate
    """
    base_cols = ["rcity", "grade", "distance", "rec", "races", "refund_rate", "roi"]
    missing = [c for c in base_cols if not has_column(conn, "meta_box_guide", c)]
    if missing:
        log(f"[WARN] meta_box_guide missing columns: {missing} -> BEST/ALT disabled")
        return {}

    hit_col = pick_existing_col(conn, "meta_box_guide", ["hit", "meta_hit", "hits"])
    hr_col = pick_existing_col(conn, "meta_box_guide", ["hr", "meta_hr", "hit_rate"])

    cols = base_cols[:]
    if hit_col:
        cols.append(hit_col)
    if hr_col:
        cols.append(hr_col)

    sql = f"""
        SELECT {', '.join(cols)}
          FROM The1.meta_box_guide
         WHERE rec IS NOT NULL
           AND TRIM(rec) <> ''
    """

    out: Dict[Tuple[str, str, int], Dict[str, dict]] = {}
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall() or []

    for row in rows:
        try:
            key = (
                str(row["rcity"]).strip(),
                str(row["grade"]).strip(),
                int(row["distance"]),
            )
            rec = str(row["rec"]).strip()

            races = int(row.get("races") or 0)

            hit = None
            if hit_col and row.get(hit_col) is not None:
                hit = int(row[hit_col])

            hr = None
            if hr_col and row.get(hr_col) is not None:
                hr = float(row[hr_col])

            if hr is None and hit is not None and races > 0:
                hr = hit / races

            rr = row.get("refund_rate")
            rr = float(rr) if rr is not None else None

            roi = row.get("roi")
            roi = float(roi) if roi is not None else None

            out.setdefault(key, {})[rec] = {
                "races": races,
                "hit": hit,
                "hr": hr,
                "rr": rr,
                "roi": roi,
            }
        except Exception:
            continue

    log(
        f"[INFO] meta_box_stats loaded: keys={len(out)} rows={sum(len(v) for v in out.values())}"
    )
    return out


# =========================
# 1.5) BEST/ALT picker (Option B)
# =========================
def pick_best_two_meta_cases(meta_stats: Dict[str, dict]) -> List[Tuple[str, dict]]:
    """
    Option B (profit-first):
      1) ROI desc
      2) RR desc
      3) HR desc
      4) races desc
      5) rBOX* preferred (tie-break)
    Return up to 2: [(rec, stat_dict), (rec, stat_dict)]
    """
    cand = []
    for rec, d in (meta_stats or {}).items():
        races = int(d.get("races") or 0)
        roi = d.get("roi")
        rr = d.get("rr")
        hr = d.get("hr")

        # 최소한 races>0은 필요. roi/rr/hr가 None이면 정렬 하위로 보냄
        if races <= 0:
            continue

        roi_v = float(roi) if roi is not None else -1e18
        rr_v = float(rr) if rr is not None else -1e18
        hr_v = float(hr) if hr is not None else -1e18

        cand.append(
            (
                rec,
                roi_v,
                rr_v,
                hr_v,
                races,
                1 if str(rec).startswith("rBOX") else 0,
            )
        )

    if not cand:
        return []

    cand.sort(
        key=lambda x: (
            x[1],  # roi
            x[2],  # rr
            x[3],  # hr
            x[4],  # races
            x[5],  # rBOX preferred
        ),
        reverse=True,
    )

    picked: List[Tuple[str, dict]] = []
    for rec, *_ in cand:
        picked.append((rec, meta_stats[rec]))
        if len(picked) == 2:
            break
    return picked


# =========================
# 2) exp011 rows (+exp010 grade/distance join)
# =========================
def load_exp011_rows(
    conn,
    distance_expr: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    rcity: Optional[str] = None,
    rdate: Optional[str] = None,
    rno: Optional[int] = None,
) -> List[dict]:
    sql = f"""
        SELECT
            e.rcity,
            e.rdate,
            e.rno,
            e.gate,
            e.r_pop,
            x.grade AS grade,
            {distance_expr} AS distance
        FROM The1.exp011 e
        LEFT JOIN The1.exp010 x
          ON x.rcity = e.rcity AND x.rdate = e.rdate AND x.rno = e.rno
        LEFT JOIN The1.rec010 r
          ON r.rcity = e.rcity AND r.rdate = e.rdate AND r.rno = e.rno
        WHERE 1=1
    """
    params: List[Any] = []

    if rcity is not None and rdate is not None and rno is not None:
        sql += " AND e.rcity=%s AND e.rdate=%s AND e.rno=%s "
        params += [rcity, rdate, int(rno)]
    else:
        if from_date is None or to_date is None:
            raise ValueError("Period update requires --from_date/--to_date")
        sql += " AND e.rdate >= %s AND e.rdate <= %s "
        params += [from_date, to_date]

    sql += " ORDER BY e.rcity, e.rdate, e.rno, e.gate "

    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall() or []


def load_race_meta_fallback(
    conn,
    distance_expr: str,
    rcity: str,
    rdate: str,
    rno: int,
) -> Tuple[str, Optional[int]]:
    sql = f"""
        SELECT
            x.grade AS grade,
            {distance_expr} AS distance
        FROM The1.exp010 x
        LEFT JOIN The1.rec010 r
          ON r.rcity = x.rcity AND r.rdate = x.rdate AND r.rno = x.rno
        WHERE x.rcity=%s AND x.rdate=%s AND x.rno=%s
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, (rcity, rdate, int(rno)))
        row = cur.fetchone() or {}

    grade = str(row.get("grade") or "").strip()
    dist = row.get("distance")
    dist_i = int(dist) if dist is not None else None
    return grade, dist_i


# =========================
# 3) Build r_guide (META-only, BEST+ALT each with HR+RR+ROI)
# =========================
def build_rguide_for_race(
    *,
    conn,
    distance_expr: str,
    g: List[dict],
    meta_stats_map: Dict[Tuple[str, str, int], Dict[str, dict]],
) -> str:
    if not g:
        return ""

    rcity = str(g[0].get("rcity") or "").strip()
    rdate = str(g[0].get("rdate") or "").strip()
    rno = int(g[0].get("rno") or 0)

    grade = str(g[0].get("grade") or "").strip()
    dist_raw = g[0].get("distance", None)
    distance = int(dist_raw) if dist_raw is not None else None

    # fallback grade/distance
    if not grade or distance is None:
        fb_grade, fb_dist = load_race_meta_fallback(
            conn, distance_expr, rcity, rdate, rno
        )
        if not grade:
            grade = fb_grade
        if distance is None:
            distance = fb_dist

    dist_txt = f"{distance}m" if distance is not None else "NA"
    meta_key = (rcity, grade, int(distance)) if distance is not None else None

    def pack_block(label: str, rec: str, d: dict) -> str:
        races = int(d.get("races") or 0)
        hr = d.get("hr")
        rr = d.get("rr")
        roi = d.get("roi")

        hr_txt = f"{float(hr) * 100:.1f}%" if hr is not None else "NA"
        rr_txt = fmt3(rr) if rr is not None else "NA"
        roi_txt = fmt3(roi) if roi is not None else "NA"
        rec_disp = humanize_case(rec)

        return f"{label}:{rec_disp}({races}r,{hr_txt},RR{rr_txt},ROI{roi_txt})"

    best_block = "BEST:-"
    alt_block = None

    if meta_key is not None:
        meta_stats = meta_stats_map.get(meta_key, {})
        picked2 = pick_best_two_meta_cases(meta_stats)
        if picked2:
            best_rec, best_d = picked2[0]
            best_block = pack_block("BEST", best_rec, best_d)
            if len(picked2) > 1:
                alt_rec, alt_d = picked2[1]
                if alt_rec != best_rec:
                    alt_block = pack_block("ALT", alt_rec, alt_d)

    parts = [f"META:{rcity},{grade},{dist_txt}", best_block]
    if alt_block:
        parts.append(alt_block)

    return " | ".join(parts)


# =========================
# 4) Build updates
# =========================
def build_rguide_updates(
    conn,
    distance_expr: str,
    meta_stats_map: Dict[Tuple[str, str, int], Dict[str, dict]],
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    rcity: Optional[str] = None,
    rdate: Optional[str] = None,
    rno: Optional[int] = None,
) -> List[Tuple[str, str, str, int]]:
    rows = load_exp011_rows(
        conn,
        distance_expr=distance_expr,
        from_date=from_date,
        to_date=to_date,
        rcity=rcity,
        rdate=rdate,
        rno=rno,
    )
    if not rows:
        return []

    races: Dict[Tuple[str, str, int], List[dict]] = {}
    for r in rows:
        key = (str(r["rcity"]), str(r["rdate"]), int(r["rno"]))
        races.setdefault(key, []).append(r)

    updates: List[Tuple[str, str, str, int]] = []
    for (rc, rd, rn), g in races.items():
        r_guide = build_rguide_for_race(
            conn=conn,
            distance_expr=distance_expr,
            g=g,
            meta_stats_map=meta_stats_map,
        )
        updates.append((r_guide, rc, rd, rn))
    return updates


# =========================
# 5) Update exp010.r_guide
# =========================
def update_exp010_rguide(
    conn,
    updates: List[Tuple[str, str, str, int]],
    dry_run: bool = True,
    batch_size: int = 2000,
) -> Dict[str, int]:
    total = len(updates)
    if total == 0:
        return {"total_races": 0, "updated_rows": 0}

    if dry_run:
        log(f"[DRY_RUN] would update races={total}")
        for i, (rg, rc, rd, rn) in enumerate(updates[:10], start=1):
            log(f"  sample{i}: {rc} {rd} R{rn} -> {rg}")
        return {"total_races": total, "updated_rows": 0}

    sql_update = """
        UPDATE The1.exp010
           SET r_guide = %s
         WHERE rcity = %s
           AND rdate = %s
           AND rno   = %s
    """

    updated_rows = 0
    with conn.cursor() as cur:
        for i in range(0, total, batch_size):
            chunk = updates[i : i + batch_size]
            cur.executemany(sql_update, chunk)
            updated_rows += cur.rowcount

    return {"total_races": total, "updated_rows": updated_rows}


# =========================
# 6) Runner
# =========================
def run_rguide_update(
    *,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    rcity: Optional[str] = None,
    rdate: Optional[str] = None,
    rno: Optional[int] = None,
    dry_run: bool = True,
    batch_size: int = 2000,
) -> Dict[str, int]:
    is_single = rcity is not None and rdate is not None and rno is not None
    if not is_single and (from_date is None or to_date is None):
        raise ValueError(
            "Either single(rcity,rdate,rno) or period(from_date,to_date) is required."
        )

    with closing(get_conn()) as conn:
        try:
            distance_expr = get_distance_select_expr(conn)
            meta_stats_map = load_meta_box_stats_map(conn)

            updates = build_rguide_updates(
                conn,
                distance_expr=distance_expr,
                meta_stats_map=meta_stats_map,
                from_date=from_date,
                to_date=to_date,
                rcity=rcity,
                rdate=rdate,
                rno=rno,
            )

            info = update_exp010_rguide(
                conn, updates=updates, dry_run=dry_run, batch_size=batch_size
            )

            if dry_run:
                conn.rollback()
                log("[DRY_RUN] done (rollback)")
            else:
                conn.commit()
                log("[COMMIT] done")

            mode = "SINGLE" if is_single else "PERIOD"
            log(
                f"[{mode}] total_races={info['total_races']}, updated_rows={info['updated_rows']}"
            )
            return info
        except Exception:
            conn.rollback()
            raise


# =========================
# 7) CLI
# =========================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from_date", help="YYYYMMDD (period)")
    ap.add_argument("--to_date", help="YYYYMMDD (period)")
    ap.add_argument("--rcity", help="track (single) ex) 서울/부산")
    ap.add_argument("--rdate", help="YYYYMMDD (single)")
    ap.add_argument("--rno", type=int, help="race no (single)")
    ap.add_argument("--dry_run", action="store_true", help="print samples only")
    ap.add_argument("--batch_size", type=int, default=2000)
    args = ap.parse_args()

    is_single = (
        args.rcity is not None and args.rdate is not None and args.rno is not None
    )

    if is_single:
        run_rguide_update(
            rcity=args.rcity,
            rdate=args.rdate,
            rno=args.rno,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
        )
    else:
        if not args.from_date or not args.to_date:
            raise SystemExit("Period mode requires --from_date and --to_date")
        run_rguide_update(
            from_date=args.from_date,
            to_date=args.to_date,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
        )


if __name__ == "__main__":
    main()
