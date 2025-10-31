import pymysql
from datetime import datetime, timedelta


def baseline_compute(connection, as_rdate):
    """
    PowerBuilder 함수 wf_compute_adv()를 Python으로 완전 변환한 버전
    :param connection: pymysql.connect()로 생성된 연결 객체
    :param as_rcity: 지역명 (예: '서울')
    :param as_rdate: 기준일자 (예: '20251019')
    :return: 성공시 1, 실패시 0
    """

    try:
        cursor = connection.cursor()

        ls_from = '20180101'

        # 3일 전 날짜 (PowerBuilder의 subdate 3일)
        cursor.execute(
            "SELECT DATE_FORMAT(SUBDATE(STR_TO_DATE(%s, '%%Y%%m%%d'), 3), '%%Y%%m%%d')",
            (as_rdate,),
        )

        ls_to = cursor.fetchone()[0]

        print("ls_to:", as_rdate , ls_to)
        # ls_from = cursor.fetchone()


        print(f"{ls_to}  award Table Computing...")
        cursor.execute("DELETE FROM award WHERE rmonth = SUBSTR(%s,1,6)", (as_rdate,))
        connection.commit()

        # ✅ 1. award 테이블 생성
        sql_award = """
        INSERT INTO award  
        SELECT SUBSTR(rdate,1,6) rmonth, jockey, trainer, host,
              SUM(IF(a.rank=1,1,0)) r1_cnt,
              SUM(IF(a.rank=2,1,0)) r2_cnt,
              SUM(IF(a.rank=3,1,0)) r3_cnt,
              SUM(IF(a.rank=4,1,0)) r4_cnt,
              SUM(IF(a.rank=5,1,0)) r5_cnt,
              COUNT(*) r_cnt,
              SUM(
                  IF(a.rank=1,r1award+sub1award,0) +
                  IF(a.rank=2,r2award+sub2award,0) +
                  IF(a.rank=3,r3award+sub3award,0) +
                  IF(a.rank=4,r4award,0) +
                  IF(a.rank=5,r5award,0)
              ) award
        FROM record a
        WHERE a.rank <= 5
          AND grade <> '주행검사'
          AND SUBSTR(a.rdate,1,6) = SUBSTR(%s,1,6)
        GROUP BY SUBSTR(rdate,1,6), jockey, trainer, host
        """
        r_cnt = cursor.execute(sql_award, (as_rdate,))
        print(f"Inserted {r_cnt} rows INSERT INTO award table.")
        connection.commit()

        print(f"{ls_to} adv_jockey Table Computing...")

        # ✅ 2. adv_jockey
        cursor.execute("DELETE FROM adv_jockey")
        connection.commit()

        sql_adv_jockey = """
        INSERT INTO adv_jockey
        SELECT 
            a.jockey,
            a.distance,
            a.gate,
            ROUND(b.avg_rec, 4) AS avg,
            ROUND(a.i_record, 4) AS i_record,
            ROUND(b.avg_rec - a.i_record, 4) AS adv_gate,
            a.rcnt,
            ROUND(a.jockey_w, 4) AS joc_rate,
            -- IFNULL(ROUND(((b.avg_rec - a.i_record) / a.distance) * 1400, 4), 0) AS adv_jockey
            IFNULL(
              ROUND(
                  (
                      (
                          (((b.avg_rec - a.i_record) / a.distance) * 1400) - (-200)
                      ) / (200 - (-200))
                  ) * 160 - 80,
                  4
              )
            , 0) AS adv_norm
        FROM (
            SELECT 
                jockey,
                distance,
                gate,
                SUM(i_record + burden_w) / COUNT(*) AS i_record,
                COUNT(*) AS rcnt,
                AVG(jockey_w) AS jockey_w
            FROM record_s
            WHERE rdate BETWEEN %s AND %s
              AND rank BETWEEN 1 AND 7
            GROUP BY jockey, distance, gate
        ) a
        JOIN (
            SELECT 
                jockey,
                distance,
                SUM(i_record + burden_w) / COUNT(*) AS avg_rec
            FROM record_s
            WHERE rdate BETWEEN %s AND %s
              AND rank BETWEEN 1 AND 7
            GROUP BY jockey, distance
        ) b
        ON a.jockey = b.jockey
        AND a.distance = b.distance
        WHERE a.rcnt > 1;
        """
        r_cnt = cursor.execute(sql_adv_jockey, (ls_from, ls_to, ls_from, ls_to))
        print(f"Inserted {r_cnt} rows INSERT INTO adv_jockey table.")
        # print(sql_adv_jockey)
        connection.commit()

        print(f"{ls_to} adv_track Table Computing...")

        # ✅ 3. adv_track
        cursor.execute("DELETE FROM adv_track")
        connection.commit()

        sql_adv_track = """
        INSERT INTO adv_track
        WITH base AS ( 
          SELECT 
              a.rcity, a.rdate, a.rno, a.grade, a.distance, 
              a.jockey, a.gate,
              (a.i_record + a.burden_w + IFNULL(j.adv_jockey, 0)) AS rec
          FROM record_s a
          LEFT JOIN adv_jockey j
            ON j.jockey = a.jockey
          AND j.gate = a.gate
          AND j.distance = a.distance
          WHERE a.rdate BETWEEN %s AND %s
            AND a.rank BETWEEN 1 AND 7
        ),
        aa AS (
            SELECT 
                rcity, rdate, rno, grade, distance,
                AVG(rec) AS rec
            FROM base
            GROUP BY rcity, rdate, rno, grade, distance
        ),
        bb AS (
            SELECT 
                rcity, grade, distance,
                AVG(rec) AS avg
            FROM base
            GROUP BY rcity, grade, distance
        )
        SELECT 
            aa.rcity, aa.rdate, aa.rno, aa.grade, aa.distance,
            ROUND(aa.rec,4) AS record,
            ROUND(bb.avg,4) AS avg_rec,
            ROUND(bb.avg - aa.rec,4) AS adv_flag,
            -- ROUND(((bb.avg - aa.rec) / aa.distance) * 1400,4) AS adv_track
            ROUND(
                (
                    (
                        (((bb.avg - aa.rec)/aa.distance)*1400) - (-200)
                    ) / (200 - (-200))
                ) * 160 - 80,
                4
            ) AS adv_norm
        FROM aa
        JOIN bb
          ON aa.rcity = bb.rcity
        AND aa.grade = bb.grade
        AND aa.distance = bb.distance;
        """
        r_cnt = cursor.execute(sql_adv_track, (ls_from, ls_to))
        print(f"Inserted {r_cnt} rows INSERT INTO adv_track table.")
        connection.commit()

        print(f"{ls_to} adv_track Table Completed! adv_jockey Column Updating...")

        # ✅ 4. rec011 & record_s 업데이트
        update_jockey_sql = """
        UPDATE rec011 a
          SET adv_jockey = IFNULL((
                  SELECT adv_jockey
                    FROM adv_jockey
                  WHERE jockey = a.jockey
                    AND distance = a.distance_w
                    AND gate = a.gate),0),
              adv_track = IFNULL((
                  SELECT adv_track
                    FROM adv_track
                  WHERE rcity=a.rcity
                    AND rdate=a.rdate
                    AND rno=a.rno),0)
        WHERE rdate >= '20180101'
        """

        r_cnt = cursor.execute(update_jockey_sql)
        print(f"Inserted {r_cnt} rows UPDATE rec011 table. adv_jockey & adv_track columns.")
        connection.commit()

        # cursor.execute(update_jockey_sql.replace("rec011", "record_s"))
        # connection.commit()

        print(f"{ls_to} adv_jockey Column Completed! i_convert Column Computing...")

        # ✅ 5. i_convert 업데이트
        r_cnt = cursor.execute(
            """
        UPDATE rec011
          SET i_convert = i_record + IFNULL(adv_jockey,0) + IFNULL(adv_track,0) + burden_w
        WHERE rdate >= '20180101'
        """
        )
        print(f"Inserted {r_cnt} rows UPDATE rec011 table. i_convert column.")
        connection.commit()

        # r_cnt = cursor.execute(
        #     """
        # UPDATE record_s
        #   SET i_convert = i_record + IFNULL(adv_jockey,0) + IFNULL(adv_track,0) + burden_w
        # WHERE rdate >= '20180101'
        # """
        # )
        # print(f"Inserted {r_cnt} rows UPDATE record_s table. i_convert column.")
        # connection.commit()

        print(f"{ls_to} i_convert Column Completed! adv_distance Table Computing...")

        # ✅ 6. adv_distance
        cursor.execute("DELETE FROM adv_distance")
        connection.commit()

        sql_adv_distance = """
        INSERT INTO adv_distance
        SELECT aa.rcity, aa.grade, aa.distance dist1, bb.distance dist2,
              aa.rec i_100m1, bb.rec i_100m2,
              (aa.rec - bb.rec)*(aa.distance/100) adv_dist,
              aa.rcnt rcnt1, bb.rcnt rcnt2
        FROM (
              SELECT rcity, grade, distance,
                      SUM(i_convert)/COUNT(*)/(distance/100) rec,
                      COUNT(*) rcnt
                FROM record_s a
                WHERE rdate BETWEEN %s AND %s
                  AND rank BETWEEN 1 AND 7
                GROUP BY rcity, grade, distance
              ) aa,
              (
              SELECT rcity, grade, distance,
                      SUM(i_convert)/COUNT(*)/(distance/100) rec,
                      COUNT(*) rcnt
                FROM record_s a
                WHERE rdate BETWEEN %s AND %s
                  AND rank BETWEEN 1 AND 7
                GROUP BY rcity, grade, distance
              ) bb
        WHERE aa.rcity=bb.rcity
          AND aa.grade=bb.grade
        """
        r_cnt = cursor.execute(sql_adv_distance, (ls_from, ls_to, ls_from, ls_to))
        print(f"Inserted {r_cnt} rows INSERT INTO adv_distance table.")
        connection.commit()

        print(f"{ls_to} adv_distance Completed! adv_furlong Computing...")

        # ✅ 7. adv_furlong
        cursor.execute("DELETE FROM adv_furlong")
        connection.commit()

        sql_adv_furlong = """
        INSERT INTO adv_furlong
        SELECT aa.rcity, aa.grade, aa.distance dist1, bb.distance dist2,
              aa.s1f, bb.s1f, aa.s1f - bb.s1f,
              aa.g1f, bb.g1f, aa.g1f - bb.g1f,
              aa.g2f, bb.g2f, aa.g2f - bb.g2f,
              aa.g3f, bb.g3f, aa.g3f - bb.g3f,
              aa.rcnt rcnt1, bb.rcnt rcnt2
        FROM (
              SELECT rcity, grade, distance,
                      AVG(i_s1f) s1f, AVG(i_g1f) g1f,
                      AVG(i_g2f) g2f, AVG(i_g3f) g3f, COUNT(*) rcnt
                FROM record_s a
                WHERE rdate BETWEEN %s AND %s
                  AND rank BETWEEN 1 AND 7
                GROUP BY rcity, grade, distance
              ) aa,
              (
              SELECT rcity, grade, distance,
                      AVG(i_s1f) s1f, AVG(i_g1f) g1f,
                      AVG(i_g2f) g2f, AVG(i_g3f) g3f, COUNT(*) rcnt
                FROM record_s a
                WHERE rdate BETWEEN %s AND %s
                  AND rank BETWEEN 1 AND 7
                GROUP BY rcity, grade, distance
              ) bb
        WHERE aa.rcity=bb.rcity
          AND aa.grade=bb.grade
        """
        r_cnt = cursor.execute(sql_adv_furlong, (ls_from, ls_to, ls_from, ls_to))
        print(f"Inserted {r_cnt} rows INSERT INTO adv_furlong table.")
        connection.commit()

        print("✅ All Computation Completed Successfully!")
        return 1

    except Exception as e:
        print("❌ Error in wf_compute_adv:", e)
        connection.rollback()
        return 0

    finally:
        cursor.close()


def renewal_record_s(connection, as_rdate):
    """
    rec011 테이블의 adv_jockey, adv_track, i_convert 컬럼을 record_s 테이블에 업데이트
    :param connection: pymysql.connect()로 생성된 연결 객체
    :param as_rdate: 기준일자 (예: '20251019')
    :return: 없음
    """
    try:
        cursor = connection.cursor()

        update_sql = """
        update rec011 a set r_flag = '0'
        where rdate <= %s --  and rno = 1
        and r_flag in ( 'X', 'Y', 'Z' ) 
        """

        r_cnt = cursor.execute(update_sql, (as_rdate,))
        print(f"Updated {r_cnt} rows in rec011 table 'X', 'Y', 'Z' Clear")
        connection.commit()

    except Exception as e:
        print("❌ Error in rec011 table 'X', 'Y', 'Z' Clear:", e)
        connection.rollback()

    finally:
        cursor.close()

    try:
        cursor = connection.cursor()

        update_sql = """
        update The1.rec011 a set r_flag = 'X'
        where rdate <= %s --  and rno = 1
        and ( rcity, rdate, rno ) in ( select rcity, rdate, rno from The1.rec010 where race_speed in ( '①', '②' ))
        and ( adv_track >= 50 )
        and ( r_flag = '0' or r_flag is null ) 
        """

        r_cnt = cursor.execute(update_sql, (as_rdate,))
        print(f"Updated {r_cnt} rows in rec011 table 'X' Set")
        connection.commit()

    except Exception as e:
        print("❌ Error in rec011 table 'X' Set", e)
        connection.rollback()

    finally:
        cursor.close()
    try:
        cursor = connection.cursor()

        update_sql = """
        update The1.rec011 a set r_flag = 'Y'
        where rdate <= %s --  and rno = 1
        and ( rcity, rdate, rno ) in ( select rcity, rdate, rno from The1.rec010 where race_speed in ( '⑨', '⑩') )
        and ( adv_track <= -50 )
        and ( r_flag = '0' or r_flag is null ) 
        """

        r_cnt = cursor.execute(update_sql, (as_rdate,))
        print(f"Updated {r_cnt} rows in rec011 table 'Y' Set")
        connection.commit()

    except Exception as e:
        print("❌ Error in rec011 table 'Y' Set", e)
        connection.rollback()

    finally:
        cursor.close()
    try:
        cursor = connection.cursor()

        update_sql = """
        update The1.rec011 a set r_flag = 'Z'
        where rdate <= %s --  and rno = 1
        and i_convert -  ( select min(i_convert) from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank = 1  ) > 300 
        and ( r_flag = '0' or r_flag is null ) 
        """

        r_cnt = cursor.execute(update_sql, (as_rdate,))
        print(f"Updated {r_cnt} rows in rec011 table 'Z' Set")
        connection.commit()

    except Exception as e:
        print("❌ Error in rec011 table 'Z' Set:", e)
        connection.rollback()

    finally:
        cursor.close()

    print("truncate table The1.record_s;")
    cursor = connection.cursor()
    cursor.execute("truncate table record_s")
    connection.commit()

    try:
        cursor = connection.cursor()

        update_sql = """
        insert into The1.record_s 
        SELECT rcity,
            rdate,
            rno,
            rday,
            rseq,
            distance,
            grade,
            dividing,
            rname,
            rcon1,
            rcon2,
            weather,
            rstate,
            rmoisture,
            rtime,
            gate,
            rank,
            horse,
            birthplace,
            h_sex,
            h_age,
            handycap,
            jockey,
            joc_adv,
            trainer,
            host,
            rating,
            h_weight,
            w_change,
            record,
            gap,
            corners,
            rs1f,
            r1c,
            r2c,
            r3c,
            r4c,
            rg3f,
            rg2f,
            rg1f,
            i_s1f,
            i_r1c,
            i_r2c,
            i_r3c,
            i_r4c,
            i_g3f,
            i_g2f,
            i_g1f,
            i_record,
            jockey_w,
            burden_w,
            adv_jockey,
            adv_track,
            i_convert, if( isnull(r_flag), '0', r_flag), race_speed
        FROM The1.record
        where rname <> '주행검사'
        and rank < 90
        and rdate between '20140101' and %s

        """

        r_cnt = cursor.execute(update_sql, (as_rdate,))
        print(f"Insert {r_cnt} rows in record_s table")
        connection.commit()

    except Exception as e:
        print("❌ Error in record_s table Insert", e)
        connection.rollback()

    finally:
        cursor.close()
