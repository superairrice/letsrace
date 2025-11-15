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

        ls_to = as_rdate

        # 3일 전 날짜 (PowerBuilder의 subdate 3일)
        cursor.execute(
            "SELECT DATE_FORMAT(SUBDATE(STR_TO_DATE(%s, '%%Y%%m%%d'), 3), '%%Y%%m%%d')",
            (as_rdate,),
        )

        print("ls_to:", ls_to)
        ls_to = cursor.fetchone()[0]
        # ls_from = cursor.fetchone()[0]

        ls_from = '20180101'

        print(f"{ls_to}  award Table Computing...")
        cursor.execute("DELETE FROM award WHERE rmonth = SUBSTR(%s,1,6)", (ls_to,))
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
        r_cnt = cursor.execute(sql_award, (ls_to,))
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

        # print(sql_adv_track)
        r_cnt = cursor.execute(sql_adv_track, (ls_from, ls_to))
        print(f"Inserted {r_cnt} rows INSERT INTO adv_track table.")
        connection.commit()

        print(f"{ls_to} adv_track Table Completed! adv_jockey Column Updating...")

        # ✅ 4. rec011 & record_s 업데이트
        update_jockey_sql = """
        UPDATE rec011 a
        LEFT JOIN adv_jockey j
            ON j.jockey = a.jockey
        AND j.distance = a.distance_w
        AND j.gate = a.gate
        LEFT JOIN adv_track t
            ON t.rcity = a.rcity
        AND t.rdate = a.rdate
        AND t.rno   = a.rno
        SET
            a.adv_jockey = IFNULL(j.adv_jockey, 0),
            a.adv_track  = IFNULL(t.adv_track, 0)
        WHERE a.rdate >= '20180101';
        """
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


def create_record(connection, r_condition, weight):

    # i_mock clear
    try:
        with connection.cursor() as cursor:

            strSql = """
                UPDATE rec011
                SET i_mock = null
                WHERE horse in (select horse from exp011 where rcity = %s and rdate = %s and rno = %s)
            """
            r_cnt = cursor.execute(strSql, (r_condition.rcity, r_condition.rdate, r_condition.rno))
            # connection.commit()

    except Exception as e:
        print(
            "❌ Failed updating rec011 i_mock:",
            r_condition.rcity,
            r_condition.rdate,
            r_condition.rno,
            "| Error:",
            e,
        )
        connection.rollback()

    for i in range(1, int(r_condition.rcount) + 1):

        # 게이트별 경주조건 query
        try:
            cursor = connection.cursor()

            # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey
            strSql = (
                """ 
                SELECT grade, distance, horse, handycap, jockey, trainer
                FROM expect a
                where a.rcity = '"""
                + r_condition.rcity
                + """'
                AND a.rdate = '"""
                + r_condition.rdate
                + """'
                AND a.rno = """
                + str(r_condition.rno)
                + """
                AND a.gate = """
                + str(i)
                + """
            ; """
            )

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            gate_con = cursor.fetchall()

            # print("Gate Condition Query Result:", gate_con)

        except:
            print(
                "Failed selecting in 게이트별 조건 Query, 등급, 거리, 경주마, 부담중량, 기수, 마방, 기수복승률, 조교사 복승률 등"
            )
        finally:
            cursor.close()

        # 기수 역량 가중치 쿼리 : 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey Query
        i_jockey = jockey_ability(
            connection,
            r_condition.rdate,  # 경주일
            str(gate_con[0][3]),  # 부담중량
            str(gate_con[0][1]),  # 경주거리
            gate_con[0][4],  # 기수
            i,  # 게이트
        )

        print("Jockey Ability Query Result:", i_jockey, gate_con[0][4])

        # print(gate_con[0][4], i_jockey)
        i_avg, i_fast, i_slow = set_common(
            connection,
            r_condition.rcity,
            r_condition.rdate,
            gate_con[0][1],
            gate_con[0][2],
            i_jockey[0][0],
        )  # 경마장, 경주일, 경주거리, 경주마, 경주역량
        furlong_cnt = set_record(
            connection,
            r_condition.rcity,
            r_condition.rdate,
            gate_con[0][1],
            gate_con[0][2],
            i_jockey[0][0],
            weight,
            i_avg,
            i_fast,
            i_slow,
        )  # 경마장, 경주일, 경주거리, 경주마, 기수역량, 가중치

    #     # print(common)
    #     # print(furlong)

    set_rank(
        connection, r_condition.rcity, r_condition.rdate, r_condition.rno
    )  # 경마장, 경주일, 경주번호 => race rank set

    return


# i_jockey : 기수의 거리별 게이트별 부담중량 대비 가중치 Query
def jockey_ability(connection, rdate, handycap, distance, jockey, gate):
    # 기수 역량 가중치 쿼리 : 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey Query
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
        strSql = (
            """ 
                select adv_jockey  +  f_burden_w('"""
            + rdate
            + """', """
            + handycap
            + """, """
            + distance
            + """, '"""
            + jockey
            + """' )   
                   -- /* + f_burden( :ld_handycap, :ll_distance, :ls_jockey ) */ into :i_jockey					// 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey
                from adv_jockey
                where jockey = '"""
            + jockey
            + """'
                AND distance = """
            + distance
            + """
                AND gate = """
            + str(gate)
            + """
            ; """
        )
        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        i_jockey = cursor.fetchall()

        # print("Jockey Ability Query Result:", i_jockey)

    except:
        print(
            "Failed selecting 거리별 게이트별 기수 역량 Query : adv_jockey + f_burden_w"
        )

    if r_cnt == 0:
        try:
            cursor = connection.cursor()

            # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
            strSql = (
                """ 
                select avg( adv_jockey  +  f_burden_w('"""
                + rdate
                + """', """
                + handycap
                + """, """
                + distance
                + """, '"""
                + jockey
                + """' ) )
                    -- /* + f_burden( :ld_handycap, :ll_distance, :ls_jockey ) */ into :i_jockey					// 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey
                from adv_jockey
                where jockey = '"""
                + jockey
                + """'
                AND gate = """
                + str(gate)
                + """
                ; """
            )
            # print(strSql)
            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            i_jockey = cursor.fetchall()

        except:
            print("Failed selecting 게이트별 기수 역량 Query : adv_jockey + f_burden_w")

        if i_jockey[0][0]:  # select avg 는 1건 반환 (None)
            pass
        else:
            try:
                cursor = connection.cursor()

                # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
                strSql = (
                    """ 
                    select f_burden_w('"""
                    + rdate
                    + """', """
                    + handycap
                    + """, """
                    + distance
                    + """, '"""
                    + jockey
                    + """' )   
                    from dual
                    ; """
                )

                # print(strSql)

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                i_jockey = cursor.fetchall()

            except:
                connection.rollback()
                print("Failed selecting 기수 역량 Query : f_burden_w only")

    return i_jockey


# 최고 , 최고, 평균 기록, 코너별 기록 : common, furlong환산
def set_common(connection, rcity, rdate, distance, horse, i_jockey):

    # 경주마 기수역량 감안된 평균기록
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
        strSql = (
            """ 
            SELECT ifnull( avg( (i_s1f * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0),
                ifnull( avg( (i_r1c * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0),
                ifnull( avg( (i_r2c * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0),
                ifnull( avg( (i_r3c * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0),
                ifnull( avg( (i_r4c * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0),
                ifnull( avg( (i_g3f * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0),
                ifnull( avg( (i_g2f * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0),
                ifnull( avg( (i_g1f * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0),
                ifnull( avg( i_convert - """
            + str(i_jockey)
            + """ ), 0),
                ifnull( max( i_convert - """
            + str(i_jockey)
            + """ ), 0),
                ifnull( min( i_convert - """
            + str(i_jockey)
            + """ ), 0)
            from record_s a
            WHERE a.rdate between '20180722' and '"""
            + rdate
            + """'
            and a.rdate < '"""
            + rdate
            + """'
            AND a.horse  = '"""
            + horse
            + """'
            AND a.distance = """
            + str(distance)
            + """
            and ( r_flag = '0' or r_flag = 'W' )  -- and race_speed not in ( '①', '⑨', '⑩' ) 
            and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 365 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < '"""
            + rdate
            + """'  )         
                            and ( select max(rdate) from record_s where horse = a.horse and rdate < '"""
            + rdate
            + """' )
            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환

        common = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print(
            "Failed selecting 거리별 경주마 평균.최고.최저기록. 코너링 평균 - set_common()",
            horse,
        )
    finally:
        cursor.close()

    # print("common" , common[0][0])
    i_s1f = common[0][0]
    i_r1c = common[0][1]
    i_r2c = common[0][2]
    i_r3c = common[0][3]
    i_r4c = common[0][4]
    i_g3f = common[0][5]
    i_g2f = common[0][6]
    i_g1f = common[0][7]
    i_avg = common[0][8]
    i_slow = common[0][9]
    i_fast = common[0][10]

    # 경주마 furlong 기록 환산
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey
        strSql = (
            """ 
            SELECT 
                ifnull( avg( (i_s1f * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0) +
                        avg( ifnull( ( select adv_s1f from adv_furlong where rcity = '"""
            + rcity
            + """' and grade = a.grade and dist1 = """
            + str(distance)
            + """ and dist2 = a.distance ), 
                    ( select avg( adv_s1f ) from adv_furlong where rcity = '"""
            + rcity
            + """' and dist1 = """
            + str(distance)
            + """ and dist2 = a.distance ) ) ),
                ifnull( avg( (i_g1f * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0) +
                        avg( ifnull( ( select adv_g1f from adv_furlong where rcity = '"""
            + rcity
            + """' and grade = a.grade and dist1 = """
            + str(distance)
            + """ and dist2 = a.distance ), 
                    ( select avg( adv_g1f ) from adv_furlong where rcity = '"""
            + rcity
            + """' and dist1 = """
            + str(distance)
            + """ and dist2 = a.distance ) ) ),
                ifnull( avg( (i_g2f * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0) +
                        avg( ifnull( ( select adv_g2f from adv_furlong where rcity = '"""
            + rcity
            + """' and grade = a.grade and dist1 = """
            + str(distance)
            + """ and dist2 = a.distance ), 
                    ( select avg( adv_g2f ) from adv_furlong where rcity = '"""
            + rcity
            + """' and dist1 = """
            + str(distance)
            + """ and dist2 = a.distance ) ) ),
                ifnull( avg( (i_g3f * (i_convert - """
            + str(i_jockey)
            + """) )/i_record ), 0) +
                        avg( ifnull( ( select adv_g3f from adv_furlong where rcity = '"""
            + rcity
            + """' and grade = a.grade and dist1 = """
            + str(distance)
            + """ and dist2 = a.distance ), 
                    ( select avg( adv_g3f ) from adv_furlong where rcity = '"""
            + rcity
            + """' and dist1 = """
            + str(distance)
            + """ and dist2 = a.distance ) ) )
            from record_s a
            WHERE a.rdate between '20180722' and '"""
            + rdate
            + """'
            and a.rdate < '"""
            + rdate
            + """'
            AND a.horse  = '"""
            + horse
            + """'
            and ( r_flag = '0' or r_flag = 'W' )  -- and race_speed not in ( '①', '⑨', '⑩' ) 
            and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 365 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < '"""
            + rdate
            + """'  )         
                            and ( select max(rdate) from record_s where horse = a.horse and rdate < '"""
            + rdate
            + """' )

            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        furlong = cursor.fetchall()

    except:

        print(
            "Failed selecting 거리별 경주마 평균.최고.최저기록. 코너링 평균 set_common - furlong 환산",
            horse,
        )
    finally:
        cursor.close()

    i_cs1f = furlong[0][0]
    i_cg1f = furlong[0][1]
    i_cg2f = furlong[0][2]
    i_cg3f = furlong[0][3]

    if i_cs1f:  # Query 결과가 있을때만 update
        # 경주마 furlong 기록 환산
        # print("furlong", i_cs1f, i_cg1f, i_cg2f, i_cg3f, r_cnt)
        try:
            cursor = connection.cursor()

            # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey
            strSql = (
                """ 
                UPDATE exp011
                SET rs1f = substr(The1.f_t2s("""
                + str(i_s1f)
                + """), -4),	
                    r1c = The1.f_t2s("""
                + str(i_r1c)
                + """),	
                    r2c = The1.f_t2s("""
                + str(i_r2c)
                + """),	
                    r3c = The1.f_t2s("""
                + str(i_r3c)
                + """),	
                    r4c = The1.f_t2s("""
                + str(i_r4c)
                + """),
                    rg3f = substr(The1.f_t2s("""
                + str(i_g3f)
                + """), -4),	
                    rg2f = substr(The1.f_t2s("""
                + str(i_g2f)
                + """), -4),	
                    rg1f = substr(The1.f_t2s("""
                + str(i_g1f)
                + """), -4),
                    fast_r = The1.f_t2s("""
                + str(i_fast)
                + """),	
                    slow_r = The1.f_t2s("""
                + str(i_slow)
                + """),
                    avg_r = The1.f_t2s("""
                + str(i_avg)
                + """),
                    cs1f = substr(The1.f_t2s("""
                + str(i_cs1f)
                + """), -4),	
                    cg3f = substr(The1.f_t2s("""
                + str(i_cg3f)
                + """), -4),	
                    cg2f = substr(The1.f_t2s("""
                + str(i_cg2f)
                + """), -4),	
                    cg1f = substr(The1.f_t2s("""
                + str(i_cg1f)
                + """), -4),
                    i_s1f = """
                + str(i_cs1f)
                + """,			
                    i_g3f = """
                + str(i_cg3f)
                + """,			
                    i_g2f = """
                + str(i_cg2f)
                + """,			
                    i_g1f = """
                + str(i_cg1f)
                + """,
                    i_jockey = """
                + str(i_jockey)
                + """
                WHERE rdate = '"""
                + rdate
                + """'
                AND horse  = '"""
                + horse
                + """'
            ; """
            )

            # print(strSql)
            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            furlong = cursor.fetchall()

            # connection.commit()
            # connection.close()

        except:
            # connection.rollback()
            print(
                "Failed uptating 경주마 평균.최고.최저기록. 코너링 평균 set_common update",
                horse,
            )
        finally:
            cursor.close()

    return i_avg, i_fast, i_slow  # 거리별 평균, 최고, 최저기록


# 최고 , 최고, 평균 기록, 코너별 기록 : common, furlong환산
def set_record(connection, rcity, rdate, distance, horse, i_jockey, weight, i_avg, i_fast, i_slow):

    # print(weight)
    iw_avg = weight[0][0]
    iw_fast = weight[0][1]
    iw_slow = weight[0][2]
    iw_recent3 = weight[0][3]
    iw_recent5 = weight[0][4]
    iw_convert = weight[0][5]
    # 경주마 기수역량 감안된 평균기록
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
        strSql = (
            """ 
            SELECT distance, i_s1f + i_g1f + adv_track, rank, i_convert - """
            + str(i_jockey)
            + """, rstate, rdate,
                ( ( i_convert )/a.distance ) * """
            + str(distance)
            + """ - """
            + str(i_jockey)
            + """ + 
                    ifnull( ( select adv_dist from adv_distance where rcity = '"""
            + rcity
            + """'
                                                                and grade = a.grade 
                                                                and dist1 = """
            + str(distance)
            + """
                                                                and dist2 = a.distance ), 
            ( select avg( adv_dist ) from adv_distance where dist1 = """
            + str(distance)
            + """
                                                            and dist2 = a.distance ) )		-- 해당경주의 등급별 기록이 없으면, 평균값 치환
            FROM record_s 	a  
            WHERE a.rdate between '20180722' and '"""
            + rdate
            + """' and a.rdate < '"""
            + rdate
            + """'
            AND a.horse  = '"""
            + horse
            + """'
            and ( r_flag = '0' or r_flag = 'W' ) -- and race_speed not in ( '①', '⑨', '⑩' ) 
            and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 365 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < '"""
            + rdate
            + """'  )         
                            and ( select max(rdate) from record_s where horse = a.horse and rdate < '"""
            + rdate
            + """' )
            ORDER BY a.rdate DESC 
            limit 6
            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        recent_race = cursor.fetchall()

    except:
        print("Failed setting 경주마 최근 7경주 query ", horse, strSql)

    finally:
        cursor.close()

    # print(horse, r_cnt)
    i_cnt = 0
    i_cnt3 = 0
    ls_remark = ""
    i_recent3 = 0
    i_recent5 = 0
    i_array = []

    for index, r in enumerate(recent_race):
        i_compare = r[0]
        i_flag = r[1]
        i_rank = r[2]
        i_recent = r[3]
        i_rstate = r[4]
        i_rdate = r[5]
        i_100m = r[6]

        # print(index, horse, i_rdate, i_100m)

        mock_update(horse, i_rdate, i_100m, connection)    # 경주마 최근 6경주 환산기록 update

        i_cnt = i_cnt + 1

        if i_compare == distance:  # 해당거리 최근 경주만 합산
            i_cnt3 = i_cnt3 + 1
            i_recent3 = i_recent3 + i_recent

        # i_100m이 null 이면 거리 환산 기록이 없는 경우 발생 -- 예외처리 필요
        if i_100m:
            i_recent5 = i_recent5 + i_100m
            i_array.append(i_100m)  # 배열 추가
        else:
            i_cnt = (
                i_cnt - 1
            )  # 	/* 환산기록이 없는 경주는 스킵하고 진행 ?(로직 고민 필요 )     이 경주 이후에는 기록이 생성됨   adv_distance Table 집계 */

        if i_cnt == 6:
            break

    # print(ls_remark)
    # print(horse, i_array)

    tval = 0
    max = 0
    min = 30000
    # if i_cnt >= 3:

    for i in range(0, i_cnt):

        # print(i, "array", horse, i_array[i], f_t2s(int(i_array[i])))

        tval = i_array[i]
        if max < tval:  # 최대값 비교
            max = tval

        if min > tval:  # 최소값 비교
            min = tval

    if i_cnt > 0:

        i_recent = i_recent5 / i_cnt

        if max > i_recent + 60:  # 제일 느린 기록이 평균기록보다 1초 이상 느리면 제외
            i_recent5 = i_recent5 - max
            i_cnt = i_cnt - 1

            # print(
            #     "max", horse, max, f_t2s(int(i_recent)), "---", i_cnt, f_t2s(int(max))
            # )
            # print(i_recent5, i_cnt)

        if (
            i_cnt >= 3
        ):  # 최소 3건 이상일때만 min 체크    - 나머지 2경주 중 특정 경주를 제외할 수 없을때
            if min < i_recent - 60:  # 제일 빠른 기록이 평균기록보다 1초이상 빠르면 제외
                i_recent5 = i_recent5 - min
                i_cnt = i_cnt - 1

                # print(
                #     "min",
                #     horse,
                #     min,
                #     f_t2s(int(i_recent)),
                #     "---",
                #     i_cnt,
                #     f_t2s(int(min)),
                # )

        # print(i_recent5, i_cnt)
        # print("  ")

        if i_cnt > 0:
            i_recent5 = i_recent5 / i_cnt

    else:
        i_recent5 = 0

    # i_recent5 = compute_recent_average(horse, i_array)

    # print("Final Recent5", horse, i_recent5, ii_cnt)

    if i_cnt3 >= 1:
        i_recent3 = i_recent3 / i_cnt3
    else:
        i_recent3 = 0

    i_convert = (i_avg * iw_avg + i_fast * iw_fast + i_slow * iw_slow) / 100

    if i_convert == 0:
        i_convert = i_recent5
    if i_recent3 == 0:
        i_recent3 = i_recent5

    i_complex = (
        i_recent3 * iw_recent3 + i_recent5 * iw_recent5 + i_convert * iw_convert
    ) / 100

    # 경주마 furlong 기록 환산
    # print(horse, i_convert, i_complex, r_cnt)

    ls_remark = get_remark(connection, rdate, horse)  # 경주마 최근 7경주 코멘트
    # ls_remark = ls_remark + " (" + str(r_cnt) + ")"
    # print(horse, i_recent3, i_recent5, i_convert, i_complex, ls_remark)

    try:
        cursor = connection.cursor()
        strSql = """
            select count(0) AS r_cnt,sum(a.r_1st) AS r_1st, sum(a.r_2nd) AS r_2nd,sum(a.r_3rd) AS r_3rd, round(sum(a.r_3rd) / count(0) * 100,1) AS r_per
            from
            (
                select a.jockey AS jockey,a.trainer AS trainer,a.rank AS rank,
                            if(a.rank <= 1,1,0) AS r_1st,
                            if(a.rank <= 2,1,0) AS r_2nd,
                            if(a.rank <= 3,1,0) AS r_3rd
                from rec011 a
                where  (a.rcity,a.rdate,a.rno) in (
                                    select rcity, rdate,rno
                                    from rec010
                                    where rdate between date_format(DATE_ADD( %s, INTERVAL - 372 DAY), '%%Y%%m%%d') and %s
                                    and grade <> '주행검사'
                                )
                and a.rank <= 20
                and a.jockey = (select jockey from exp011 where rdate = %s and horse = %s)
                and a.trainer = (select trainer from exp011 where rdate = %s and horse = %s)
                ) a
            ;
        """
        r_cnt = cursor.execute(
            strSql,
            (rdate,
            rdate,
            rdate,
            horse,
            rdate,
            horse,))  # 결과값 개수 반환
        jockey_trainer = cursor.fetchall()

        jt_cnt = jockey_trainer[0][0]
        jt_1st = jockey_trainer[0][1]
        jt_2nd = jockey_trainer[0][2]
        jt_3rd = jockey_trainer[0][3]
        jt_per = jockey_trainer[0][4]

    except Exception as e:
        print("Failed selecting 경주마 기수 조교사 최근 1년간 성적 :", horse, e)
    finally:
        if cursor:
            cursor.close()

    try:
        cursor = connection.cursor()
        strSql = """
            UPDATE exp011 a
            SET i_cycle = f_rcycle(%s, %s, %s),
                i_prehandy = f_prehandy(%s, %s, %s),
                j_per =( select year_per from jockey_w where jockey = a.jockey and wdate = ( select max(wdate) from jockey_w where wdate < %s and weekday(wdate) = 6 ) ),
                t_per =( select year_per from trainer_w where trainer = a.trainer and wdate = ( select max(wdate) from trainer_w where wdate < %s and weekday(wdate) = 6 ) ),
                
                h_weight = ( select h_weight from rec011 where horse = a.horse and rdate = ( select max(rdate) from rec011 where horse = a.horse and rdate < %s ) ),
                
                jt_cnt = %s,
                jt_1st = %s,
                jt_2nd = %s,
                jt_3rd = %s,
                jt_per = %s,
                
                recent3   = The1.f_t2s(%s),
                recent5   = The1.f_t2s(%s),
                complex   = The1.f_t2s(%s),
                convert_r = The1.f_t2s(%s),
                i_complex = %s,
                bet = %s,
                remark    = %s
            WHERE rdate = %s
            AND horse = %s
        """
        params = (
            rcity, rdate, horse,
            rcity, rdate, horse,
            rdate,
            rdate,
            rdate,
            
            jt_cnt,
            jt_1st,
            jt_2nd,
            jt_3rd,
            jt_per,
            
            i_recent3,
            i_recent5,
            i_complex,
            i_convert,
            i_complex,
            i_cnt,
            ls_remark,
            rdate,
            horse,
        )

        # 디버깅용 실제 SQL문 출력
        # print("Executing SQL:", strSql % tuple(repr(p) for p in params))

        r_cnt = cursor.execute(strSql, params)
        # connection.commit()

    except Exception as e:
        connection.rollback()
        print("Failed updating 경주마 데이터:", horse, e)

    finally:
        if cursor:
            cursor.close()

    return r_cnt


# 경주 rank set
def set_rank(connection, rcity, rdate, rno):

    # 경주마 기수역량 감안된 평균기록
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
        strSql = (
            """ 
            SELECT i_complex, gate
            FROM exp011
            WHERE rcity = '"""
            + rcity
            + """'
            AND rdate = '"""
            + rdate
            + """'
            AND rno  = """
            + str(rno)
            + """
            -- AND rank < 99 
            ORDER BY if( i_complex = 0, 100000, i_complex) ASC, gate      ASC
            ; """
        )

        # print(strSql)
        cursor.execute(strSql)  # 결과값 개수 반환
        race = cursor.fetchall()

    except Exception as e:
        print("Failed setting 경주 rank :", e)
    finally:
        cursor.close()

    # print(race)
    # rank = 0
    for index, r in enumerate(race):
        i_complex = r[0]
        gate = r[1]

        index = index + 1
        # print(index, i_complex, gate)

        if i_complex == 0:
            try:
                cursor = connection.cursor()

                # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
                strSql = (
                    """ 
                    UPDATE exp011  															
                    SET rank = 98
                    WHERE rcity = '"""
                    + rcity
                    + """'
                    AND rdate = '"""
                    + rdate
                    + """'
                    AND rno  = """
                    + str(rno)
                    + """
                    AND gate  = """
                    + str(gate)
                    + """
                    ; """
                )

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                # connection.commit()

            except Exception as e:
                connection.rollback()
                print("Failed setting 경주 rank , i_complex = 0 :", e, strSql)
            finally:
                if cursor:
                    cursor.close()

        else:
            try:
                cursor = connection.cursor()

                # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
                strSql = (
                    """ 
                    UPDATE exp011  															
                    SET rank = if(r_rank = 99, 99,  """
                    + str(index)
                    + """ ) 
                    WHERE rcity = '"""
                    + rcity
                    + """'
                    AND rdate = '"""
                    + rdate
                    + """'
                    AND rno  = """
                    + str(rno)
                    + """
                    AND gate  = """
                    + str(gate)
                    + """
                    ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                # connection.commit()

            except Exception as e:
                connection.rollback()
                print("Failed setting 경주 rank , i_complex = 0 :", e, strSql)
            finally:
                if cursor:
                    cursor.close()

    try:
        cursor = connection.cursor()

        # complex5 update
        strSql = (
            """ 
            UPDATE exp011  a
            SET complex5 = ( select min(complex) from exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank  = 4 ),
                gap = a.i_complex - ( select min(i_complex) from exp011 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = a.rank - 1 ),
                gap_back = ( select min(i_complex) from exp011 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = a.rank + 1 ) - a.i_complex 
            WHERE rcity = '"""
            + rcity
            + """'
                    AND rdate = '"""
            + rdate
            + """'
                    AND rno  = """
            + str(rno)
            + """
        ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        # connection.commit()

    except Exception as e:
        connection.rollback()
        print("Failed Update exp011 i_complex5 등 :", e, strSql)
    finally:
        if cursor:
            cursor.close()

    return


def get_remark(connection, rdate, horse):

    # 경주마 기수역량 감안된 평균기록
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
        strSql = (
            """ 
            SELECT rank
            FROM rec011 	a  
            WHERE a.rdate between '20180722' and '"""
            + rdate
            + """' and a.rdate < '"""
            + rdate
            + """'
            AND a.horse  = '"""
            + horse
            + """'
            and i_convert >= 1000
            
            ORDER BY a.rdate DESC 
            ; """
        )

        # print(strSql)
        cursor.execute(strSql)  # 결과값 개수 반환
        races = cursor.fetchall()

    except:
        print("Failed setting 경주마 최근 7경주 query ", horse, strSql)

    finally:
        cursor.close()

    # print(races)
    ls_remark = ""
    i_cnt = 0

    for r in races:
        i_rank = r[0]

        # print(i_rank, horse)

        if i_cnt <= 6:
            ls_remark = ls_remark + str(i_rank) + "-"

        i_cnt = i_cnt + 1

        if i_cnt == 7:
            break

    # print(ls_remark[0:-1])

    return ls_remark[0:-1]


def mock_update(horse, i_rdate, i_100m, connection):
    """경주마 최근 6경주 환산기록 update"""

    r_cnt = 0  # 기본값 설정

    try:
        with connection.cursor() as cursor:

            strSql = """
                UPDATE rec011
                SET i_mock = %s
                WHERE rdate = %s
                AND horse = %s
            """
            r_cnt = cursor.execute(strSql, (i_100m, i_rdate, horse))
            # connection.commit()

    except Exception as e:
        print("❌ Failed updating rec011 i_mock:", horse, "| Error:", e)
        connection.rollback()

    return r_cnt


def f_t2s(ai_record: int) -> str:
    """
    MySQL FUNCTION f_t2s(ai_record)의 Python 버전
    초 단위 정수를 'H:MM.S' 형태의 문자열로 변환

    예:
        5023  → '1:23.8'
        0     → ''
        3660  → '1:01.0'
    """
    if ai_record == 0 or ai_record is None:
        return ""

    # 총초 → 시, 분, 초 계산
    hours = ai_record // 3600
    minutes = (ai_record // 60) % 60
    # MySQL 버전처럼 "소수점 한자리"로 표현 (초를 6으로 나눈 몫을 0.1초 단위로 표현)
    tenth = (ai_record % 60) / 6  # MySQL의 Mod(ai_record,60)/6과 동일

    # MySQL은 mid(...,1,1) 형태로 초 첫 자리만 추출하므로 int 변환
    tenth = int(tenth)

    # 시:분.초 형식 조립
    return f"{hours}:{minutes:02d}.{tenth}"
