import pymysql
import pandas as pd
from contextlib import closing

# =========================
# DB
# =========================
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


def get_conn():
    return pymysql.connect(**DB_CONF)


def load_data(conn, from_date, to_date):
    sql = """
    SELECT
        e.rcity AS 경마장,
        e.rdate AS 경주일,
        e.rno   AS 경주번호,
        e.gate  AS 마번,
        e.rank,
        e.r_pop,
        e.r_rank,
        x.grade AS 등급,
        r.distance AS 경주거리,
        CAST(SUBSTRING(r.r333alloc,4) AS DECIMAL(10,0)) AS 삼복배당
    FROM The1.exp011 e
    LEFT JOIN The1.exp010 x
      ON x.rcity=e.rcity AND x.rdate=e.rdate AND x.rno=e.rno
    LEFT JOIN The1.rec010 r
      ON r.rcity=e.rcity AND r.rdate=e.rdate AND r.rno=e.rno
    WHERE e.rdate BETWEEN %s AND %s
    ORDER BY e.rcity, e.rdate, e.rno, e.gate
    """
    return pd.read_sql(sql, conn, params=[from_date, to_date])


# =========================
# RAW 생성 (A4/A5/A6)
# =========================
def build_A456_raw(df, bet_unit=100):
    rows = []
    total, excluded = 0, 0

    for (rcity, rdate, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        total += 1

        # 신마 필터
        new_cnt = int((g["rank"] >= 98).sum())
        if new_cnt >= 2:
            excluded += 1
            continue

        # 실제 TOP3
        gv = g.dropna(subset=["r_rank"]).copy()
        gv["r_rank"] = gv["r_rank"].astype(int)
        actual = gv[gv["r_rank"] <= 3]["마번"].astype(int).tolist()
        if len(actual) != 3:
            continue
        actual_set = set(actual)

        odds = pd.to_numeric(g["삼복배당"], errors="coerce").dropna()
        odds = float(odds.iloc[0]) if len(odds) else 0.0

        gg = g.sort_values("r_pop")
        anchor = int(gg.iloc[0]["마번"])
        anchor_in_top3 = int(anchor in actual_set)

        row = {
            "년월": str(rdate)[:6],
            "경마장": rcity,
            "경주일": rdate,
            "경주번호": int(rno),
            "등급": g["등급"].iloc[0],
            "경주거리": g["경주거리"].iloc[0],
            "신마수": new_cnt,
            "삼복배당": odds,
            "actual_top3": ",".join(map(str, actual)),
            "anchor": anchor,
            "anchor_in_top3": anchor_in_top3,
        }

        for n, bet in [(4, 600), (5, 1000), (6, 1500)]:
            followers = gg.iloc[1 : n + 1]["마번"].astype(int).tolist()
            hit = 0
            if anchor_in_top3:
                others = [x for x in actual if x != anchor]
                if set(others).issubset(set(followers)):
                    hit = 1

            row[f"A{n}_followers"] = ",".join(map(str, followers))
            row[f"A{n}_hit"] = hit
            row[f"A{n}_bet"] = bet
            row[f"A{n}_refund"] = odds * bet_unit if hit else 0.0

        rows.append(row)

    raw = pd.DataFrame(rows)

    print("\n[필터 요약]")
    print(f"전체 경주: {total}")
    print(f"신마 제외: {excluded}")
    print(f"RAW 경주수: {len(raw)}")

    return raw


# =========================
# 실행
# =========================
if __name__ == "__main__":
    from_date = "20231201"
    to_date = "20251221"

    with closing(get_conn()) as conn:
        df = load_data(conn, from_date, to_date)

    raw = build_A456_raw(df)

    path = "/Users/Super007/Documents/rpop_A4_A5_A6_raw.csv"
    raw.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"\n▶ RAW CSV 저장 완료: {path}")
