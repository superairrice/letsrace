#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
exp010.r_guide 업데이트 스크립트 (r_pop only) — 운영 안전버전

- exp011에서 r_pop로 R4/R5/R6 + ANCH + A4/A5/A6 구성을 만들어 exp010.r_guide에 저장
- meta_box_guide(메타 성적표)에서 (rcity,grade,distance) 기준으로 추천 REC를 선택
- ✅ r_guide에 적중율(HR) 추가 로직 삭제
- ✅ CMT에 meta_hr/meta_hit 추가 로직 삭제

추가 보강:
- ✅ meta_box_guide 필수 컬럼 전체 체크
- ✅ meta_box_guide rec 빈값 행 제외
- ✅ r_pop 이상치(<=0, 변환 실패) 방어
- ✅ 출주두수 부족 시에도 안전하게 문자열 생성
- ✅ dry_run 샘플/경고 로그 강화

사용:
- 기간 모드(샘플만): python make_rguide_from_meta.py --from_date 20231201 --to_date 20251221 --dry_run
- 기간 모드(커밋):    python make_rguide_from_meta.py --from_date 20231201 --to_date 20251221
- 단일 경주(샘플):    python make_rguide_from_meta.py --rcity 부산 --rdate 20251221 --rno 8 --dry_run
"""

import os
import argparse
from contextlib import closing
from typing import Dict, List, Tuple, Optional, Any

import pymysql


# =========================
# 0) DB 설정
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
# 0.5) 스키마 유틸
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


def require_columns(
    conn, table: str, cols: List[str], schema: Optional[str] = None
) -> Tuple[bool, List[str]]:
    missing = []
    for c in cols:
        if not has_column(conn, table, c, schema=schema):
            missing.append(c)
    return (len(missing) == 0), missing


def get_distance_select_expr(conn) -> str:
    """
    rec010.distance가 NULL일 수 있어서,
    exp010.distance가 있으면 COALESCE로 보강.
    """
    if has_column(conn, "exp010", "distance"):
        return "COALESCE(r.distance, x.distance)"
    return "r.distance"


# =========================
# 1) meta_box_guide 로드
# =========================
def load_meta_box_guide_map(conn) -> Dict[Tuple[str, str, int], dict]:
    """
    out[(rcity, grade, distance)] = {
        "rec": str,
        "refund_rate": float,
        "roi": float,
        "races": int,
        "sample_from": Optional[str],
        "sample_to": Optional[str],
    }

    최소 컬럼이 없으면 {} 반환.
    """
    must_cols = ["rcity", "grade", "distance", "rec", "refund_rate", "roi", "races"]
    ok, missing = require_columns(
        conn, "meta_box_guide", must_cols, schema=DB_CONF["db"]
    )
    if not ok:
        log(f"[WARN] meta_box_guide missing columns: {missing} -> meta disabled")
        return {}

    cols = must_cols[:]  # base
    if has_column(conn, "meta_box_guide", "sample_from"):
        cols.append("sample_from")
    if has_column(conn, "meta_box_guide", "sample_to"):
        cols.append("sample_to")

    # rec 빈 값 제외 (맵 오염 방지)
    sql = f"""
        SELECT {', '.join(cols)}
          FROM The1.meta_box_guide
         WHERE rec IS NOT NULL
           AND TRIM(rec) <> ''
    """

    out: Dict[Tuple[str, str, int], dict] = {}
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
        except Exception:
            continue

        out[key] = {
            "rec": str(row.get("rec") or "").strip(),
            "refund_rate": float(row.get("refund_rate") or 0.0),
            "roi": float(row.get("roi") or 0.0),
            "races": int(row.get("races") or 0),
            "sample_from": row.get("sample_from"),
            "sample_to": row.get("sample_to"),
        }

    log(f"[INFO] meta_box_guide loaded: {len(out)} keys")
    return out


# =========================
# 2) exp011 로드 (+ exp010 등급/거리 조인)
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
    """
    r_pop만 사용 (m_rank 없음)
    """
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
            raise ValueError("기간 업데이트는 --from_date/--to_date 필요")
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
    """
    exp011 join에서 grade/distance가 비었을 때 exp010(+rec010)로 보강.
    """
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
# 3) 추천(REC) + 코멘트(CMT)
# =========================
def recommend_strategy_with_comment(
    *,
    rcity: str,
    grade: str,
    distance: Optional[int],
    meta_map: Dict[Tuple[str, str, int], dict],
) -> Tuple[str, str]:
    rc = (rcity or "").strip()
    gd = (grade or "").strip()
    dist = int(distance) if distance is not None else None

    tags: List[str] = []

    # dist tag
    if dist is None:
        tags.append("dist_na")
    elif dist <= 1300:
        tags.append("short_dist")
    elif dist <= 1800:
        tags.append("mid_dist")
    else:
        tags.append("long_dist")

    # track tag
    if rc == "부산":
        tags.append("busan")
    elif rc == "서울":
        tags.append("seoul")
    else:
        tags.append("etc")

    # meta 우선
    if dist is not None and gd:
        info = meta_map.get((rc, gd, dist))
        if info and info.get("rec"):
            rec = str(info["rec"]).strip()
            tags.append("meta")
            tags.append(f"meta_races={int(info.get('races', 0))}")
            tags.append(f"meta_rr={float(info.get('refund_rate', 0.0)):.3f}")
            tags.append(f"meta_roi={float(info.get('roi', 0.0)):.3f}")
            return rec, "&".join(tags)

    # fallback
    tags.append("fallback")
    tags.append("rule=default->rBOX6")
    return "rBOX6", "&".join(tags)


# =========================
# 4) r_guide 생성 (r_pop only)
# =========================
def build_rguide_for_race(
    *,
    conn,
    distance_expr: str,
    g: List[dict],
    meta_map: Dict[Tuple[str, str, int], dict],
) -> str:
    def to_int(v, default=999999) -> int:
        """
        r_pop/gate 정렬용 안전 변환.
        """
        try:
            if v is None:
                return default
            # 공백/문자도 방어
            s = str(v).strip()
            if s == "":
                return default
            return int(float(s))  # "3.0" 같은 것도 방어
        except Exception:
            return default

    def safe_rpop(v) -> int:
        """
        r_pop이 1..N 범위를 벗어나거나 0/음수면 뒤로 보냄.
        """
        n = to_int(v, default=999999)
        if n <= 0:
            return 999999
        return n

    if not g:
        return ""

    rcity = str(g[0].get("rcity") or "").strip()
    rdate = str(g[0].get("rdate") or "").strip()
    rno = int(g[0].get("rno") or 0)

    grade = str(g[0].get("grade") or "").strip()
    dist_raw = g[0].get("distance", None)
    distance = int(dist_raw) if dist_raw is not None else None

    # grade/distance 보강
    if not grade or distance is None:
        fb_grade, fb_dist = load_race_meta_fallback(
            conn, distance_expr, rcity, rdate, rno
        )
        if not grade:
            grade = fb_grade
        if distance is None:
            distance = fb_dist

    if not grade:
        log(f"[WARN] grade missing even after fallback: {rcity} {rdate} R{rno}")
    if distance is None:
        log(f"[WARN] distance missing even after fallback: {rcity} {rdate} R{rno}")

    # r_pop 기반 picks (이상치 방어)
    g_r = sorted(g, key=lambda x: (safe_rpop(x.get("r_pop")), to_int(x.get("gate"))))

    # gate list (출주두수 부족 방어)
    gates = [int(x["gate"]) for x in g_r if x.get("gate") is not None]

    def take(n: int) -> List[int]:
        return gates[:n] if len(gates) >= n else gates[:]

    def take_after_anchor(n: int) -> List[int]:
        return gates[1 : 1 + n] if len(gates) > 1 else []

    r4 = take(4)
    r5 = take(5)
    r6 = take(6)

    anchor = gates[0] if gates else 0
    f4 = take_after_anchor(4)
    f5 = take_after_anchor(5)
    f6 = take_after_anchor(6)

    rec, cmt = recommend_strategy_with_comment(
        rcity=rcity,
        grade=grade,
        distance=distance,
        meta_map=meta_map,
    )

    def fmt(arr: List[int]) -> str:
        return ",".join(map(str, arr))

    meta_str = f"({rcity},{grade},{distance})"

    parts = [
        f"R4[{fmt(r4)}]",
        f"R5[{fmt(r5)}]",
        f"R6[{fmt(r6)}]",
        f"ANCH[{anchor}]",
        f"A4[{fmt(f4)}]",
        f"A5[{fmt(f5)}]",
        f"A6[{fmt(f6)}]",
        f"META={meta_str}",
        f"REC={rec}",
        f"CMT={cmt}",
    ]
    return " ".join(parts)


# =========================
# 5) 업데이트 목록 만들기
# =========================
def build_rguide_updates(
    conn,
    distance_expr: str,
    meta_map: Dict[Tuple[str, str, int], dict],
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
            meta_map=meta_map,
        )
        updates.append((r_guide, rc, rd, rn))

    return updates


# =========================
# 6) exp010.r_guide 업데이트
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
# 7) 실행 엔진 (기간/단일)
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
            "단일(rcity,rdate,rno) 또는 기간(from_date,to_date) 중 하나는 필수입니다."
        )

    with closing(get_conn()) as conn:
        try:
            distance_expr = get_distance_select_expr(conn)
            meta_map = load_meta_box_guide_map(conn)

            updates = build_rguide_updates(
                conn,
                distance_expr=distance_expr,
                meta_map=meta_map,
                from_date=from_date,
                to_date=to_date,
                rcity=rcity,
                rdate=rdate,
                rno=rno,
            )

            info = update_exp010_rguide(
                conn,
                updates=updates,
                dry_run=dry_run,
                batch_size=batch_size,
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
# 8) CLI
# =========================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from_date", help="YYYYMMDD (기간 업데이트용)")
    ap.add_argument("--to_date", help="YYYYMMDD (기간 업데이트용)")
    ap.add_argument("--rcity", help="경마장 (단일 경주 업데이트용) ex) 서울/부산")
    ap.add_argument("--rdate", help="YYYYMMDD (단일 경주 업데이트용)")
    ap.add_argument("--rno", type=int, help="경주번호 (단일 경주 업데이트용)")
    ap.add_argument(
        "--dry_run", action="store_true", help="실제 업데이트 없이 샘플만 출력"
    )
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
            raise SystemExit("기간 모드는 --from_date, --to_date가 필요합니다.")
        run_rguide_update(
            from_date=args.from_date,
            to_date=args.to_date,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
        )


if __name__ == "__main__":
    main()
