import pymysql
import pandas as pd
from contextlib import closing
from math import comb

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


def load_df(from_date, to_date):
    sql = """
    SELECT
        e.rcity AS 경마장,
        e.rdate AS 경주일,
        e.rno   AS 경주번호,
        e.gate  AS 마번,
        x.grade AS 등급,
        r.distance AS 경주거리,
        e.m_rank,
        e.r_pop,
        e.r_rank,
        e.rank,
        r.r333alloc1 AS odds
    FROM exp011 e
    LEFT JOIN exp010 x ON x.rcity=e.rcity AND x.rdate=e.rdate AND x.rno=e.rno
    LEFT JOIN rec010 r ON r.rcity=e.rcity AND r.rdate=e.rdate AND r.rno=e.rno
    WHERE e.rdate BETWEEN %s AND %s
    """
    with closing(get_conn()) as conn:
        return pd.read_sql(sql, conn, params=[from_date, to_date])


def build_raw(from_date, to_date):
    df = load_df(from_date, to_date)

    df["경주일"] = df["경주일"].astype(str)
    df["년월"] = df["경주일"].str[:6]
    df["신마"] = (df["rank"] >= 98).astype(int)
    df["odds"] = pd.to_numeric(df["odds"], errors="coerce")

    rows = []

    for (rcity, rdate, rno), g in df.groupby(["경마장", "경주일", "경주번호"]):
        if g["신마"].sum() >= 2:
            continue

        actual = g[g["r_rank"] <= 3]["마번"].astype(int).tolist()
        if len(actual) != 3:
            continue

        odds = g["odds"].iloc[0]
        if pd.isna(odds) or odds <= 0:
            continue

        m4 = g.sort_values("m_rank").head(4)["마번"].astype(int).tolist()
        r4 = g.sort_values("r_pop").head(4)["마번"].astype(int).tolist()
        m6 = g.sort_values("m_rank").head(6)["마번"].astype(int).tolist()
        r6 = g.sort_values("r_pop").head(6)["마번"].astype(int).tolist()

        overlap = len(set(m4) & set(r4))

        rows.append(
            {
                "경마장": rcity,
                "경주일": rdate,
                "년월": g["년월"].iloc[0],
                "경주번호": rno,
                "등급": g["등급"].iloc[0],
                "경주거리": g["경주거리"].iloc[0],
                "출주두수": g["마번"].nunique(),
                "신마수": g["신마"].sum(),
                "정산여부": "SETTLED",
                "actual_top3": ",".join(map(str, actual)),
                "m_rank_top4": ",".join(map(str, m4)),
                "r_pop_top4": ",".join(map(str, r4)),
                "m_rank_top6": ",".join(map(str, m6)),
                "r_pop_top6": ",".join(map(str, r6)),
                "overlap_1to4": overlap,
                "m_BOX4_hit": int(set(actual).issubset(m4)),
                "m_BOX4_refund": odds * 100 if set(actual).issubset(m4) else 0,
                "m_BOX4_bet": 400,
                "r_BOX4_hit": int(set(actual).issubset(r4)),
                "r_BOX4_refund": odds * 100 if set(actual).issubset(r4) else 0,
                "r_BOX4_bet": 400,
                "m_BOX6_hit": int(set(actual).issubset(m6)),
                "m_BOX6_refund": odds * 100 if set(actual).issubset(m6) else 0,
                "m_BOX6_bet": 2000,
                "r_BOX6_hit": int(set(actual).issubset(r6)),
                "r_BOX6_refund": odds * 100 if set(actual).issubset(r6) else 0,
                "r_BOX6_bet": 2000,
            }
        )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    raw = build_raw("20231201", "20251221")
    out = "./race_raw_mrank_rpop_box46.csv"
    raw.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"▶ RAW 저장 완료: {out}")
