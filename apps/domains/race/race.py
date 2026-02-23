from django.db import connection


# 경주별 출전마 경주성적 Query
def recordsByHorse(rcity, rdate, rno, hname):

    # print(f"recordsByHorse: {rcity}, {rdate}, {rno}, {hname}")
    if hname == "None":

        try:
            # with connection.cursor() as cursor:를 사용하면 자동으로 close() 처리됨
            with connection.cursor() as cursor:
                strSql = """ 
                    SELECT a.rcity, a.rdate, a.rno, a.rday, a.rseq, a.distance, a.grade, r1award, 
                        a.dividing, a.rname, a.rcon1, a.rcon2, a.weather, a.rstate, a.rmoisture, 
                        a.race_speed, a.r_judge, a.r2alloc1, a.r2alloc2,a.r333alloc1, a.r333alloc2,
                        b.gate, b.rank, b.horse, b.birthplace, b.h_sex, 
                        b.h_age, b.handycap, b.jockey, b.joc_adv, b.trainer, b.host, 
                        b.rating, b.h_weight, b.w_change, b.record, b.gap, replace( b.corners, ' ', '') as corners,
                        b.rs1f, b.r1c, b.r2c, b.r3c, b.r4c, b.rg3f, b.rg2f, b.rg1f, 
                        b.alloc1r, b.alloc3r, b.judge, b.judge_reason, b.audit_reason, 
                        b.i_s1f, b.i_g3f, b.i_g2f, b.i_g1f, b.i_record, b.jockey_w, 
                        b.burden_w, b.adv_jockey, b.adv_track, b.i_convert, b.r_start, 
                        b.r_corners, b.r_finish, b.r_wrapup, b.r_etc, b.r_flag, 
                        b.p_rank, b.p_record, b.pop_rank, b.s1f_rank, b.g3f_rank, 
                        b.g2f_rank, b.g1f_rank, b.recent3, b.recent5, b.fast_r, 
                        b.slow_r, b.avg_r, b.convert_r, b.i_cycle, b.gap_b, 
                        b.jockey_old, b.reason, b.r_pop, b.jt_per, b.jt_cnt, 
                        b.jt_1st, b.jt_2nd, b.jt_3rd, b.h_cnt, b.h_mare, if(isnull(b.i_prehandy), 0, b.handycap - b.i_prehandy) AS prehandy, b.i_mock,
                        c.s1f_per, c.g3f_per, c.g1f_per, c.start_score,c.tot_score
                    FROM rec010 a
                    JOIN rec011 b ON a.rcity = b.rcity 
                                AND a.rdate = b.rdate 
                                AND a.rno = b.rno
                    LEFT OUTER JOIN exp011 c ON c.rcity = b.rcity 
                                            AND c.rdate = b.rdate 
                                            AND c.rno = b.rno
                                            AND c.gate = b.gate 
                    WHERE b.horse IN (
                        SELECT horse 
                        FROM exp011 
                        WHERE rcity = %s
                        AND rdate = %s
                        AND rno = %s
                    )
                    AND b.rdate < %s
                    ORDER BY a.rdate DESC;
                """

                cursor.execute(strSql, (rcity, rdate, rno, rdate))
                result = cursor.fetchall()
                return result

        except Exception as e:
            print(f"❌ Failed executing recordsByHorse: {e}")
            return None
    else:

        try:
            # with connection.cursor() as cursor:를 사용하면 자동으로 close() 처리됨
            with connection.cursor() as cursor:
                strSql = """ 
                SELECT a.rcity, a.rdate, a.rno, a.rday, a.rseq, a.distance, a.grade, r1award, 
                        a.dividing, a.rname, a.rcon1, a.rcon2, a.weather, a.rstate, a.rmoisture, 
                        a.race_speed, a.r_judge, a.r2alloc1, a.r2alloc2,a.r333alloc1, a.r333alloc2,
                        b.gate, b.rank, b.horse, b.birthplace, b.h_sex, 
                        b.h_age, b.handycap, b.jockey, b.joc_adv, b.trainer, b.host, 
                        b.rating, b.h_weight, b.w_change, b.record, b.gap, replace( b.corners, ' ', '') as corners,
                        b.rs1f, b.r1c, b.r2c, b.r3c, b.r4c, b.rg3f, b.rg2f, b.rg1f, 
                        b.alloc1r, b.alloc3r, b.judge, b.judge_reason, b.audit_reason, 
                        b.i_s1f, b.i_g3f, b.i_g2f, b.i_g1f, b.i_record, b.jockey_w, 
                        b.burden_w, b.adv_jockey, b.adv_track, b.i_convert, b.r_start, 
                        b.r_corners, b.r_finish, b.r_wrapup, b.r_etc, b.r_flag, 
                        b.p_rank, b.p_record, b.pop_rank, b.s1f_rank, b.g3f_rank, 
                        b.g2f_rank, b.g1f_rank, b.recent3, b.recent5, b.fast_r, 
                        b.slow_r, b.avg_r, b.convert_r, b.i_cycle, b.gap_b, 
                        b.jockey_old, b.reason, b.r_pop, b.jt_per, b.jt_cnt, 
                        b.jt_1st, b.jt_2nd, b.jt_3rd, b.h_cnt, b.h_mare, if(isnull(b.i_prehandy), 0, b.handycap - b.i_prehandy) AS prehandy, b.i_mock,
                        c.s1f_per, c.g3f_per, c.g1f_per, c.start_score,c.tot_score
                    FROM rec010 a
                    JOIN rec011 b ON a.rcity = b.rcity 
                                AND a.rdate = b.rdate 
                                AND a.rno = b.rno
                    LEFT OUTER JOIN exp011 c ON c.rcity = b.rcity
                                            AND c.rdate = b.rdate
                                            AND c.rno = b.rno
                                            AND c.gate = b.gate
                    WHERE b.horse = %s
                    
                    AND b.rdate < %s
                    ORDER BY a.rdate DESC;
                """

                # print(strSql % (hname, rdate))  # SQL문 출력
                # print(strSql % (i_rdate, i_rdate, i_rdate, i_rdate, i_rcity, i_rdate, i_rno))  # SQL문 출력
                cursor.execute(strSql, (hname, rdate))
                result = cursor.fetchall()
                return result

        except Exception as e:
            print(f"❌ Failed executing recordsByHorse: {e}")
            return None

# 경주별 출전마 경주성적 Query
def resultOfRace(rcity, rdate, rno):

    try:
        # with connection.cursor() as cursor:를 사용하면 자동으로 close() 처리됨
        with connection.cursor() as cursor:
            strSql = """ 
                SELECT a.rcity, a.rdate, a.rno, a.rday, a.rseq, a.distance, a.grade, r1award, 
                    a.dividing, a.rname, a.rcon1, a.rcon2, a.weather, a.rstate, a.rmoisture, 
                    a.race_speed, a.r_judge, a.r2alloc1, a.r2alloc2,a.r333alloc1, a.r333alloc2,
                    b.gate, b.rank, b.horse, b.birthplace, b.h_sex, 
                    b.h_age, b.handycap, b.jockey, b.joc_adv, b.trainer, b.host, 
                    b.rating, b.h_weight, b.w_change, b.record, b.gap, replace( b.corners, ' ', '') as corners,
                    b.rs1f, b.r1c, b.r2c, b.r3c, b.r4c, b.rg3f, b.rg2f, b.rg1f, 
                    b.alloc1r, b.alloc3r, b.judge, b.judge_reason, b.audit_reason, 
                    b.i_s1f, b.i_g3f, b.i_g2f, b.i_g1f, b.i_record, b.jockey_w, 
                    b.burden_w, b.adv_jockey, b.adv_track, b.i_convert, b.r_start, 
                    b.r_corners, b.r_finish, b.r_wrapup, b.r_etc, b.r_flag, 
                    b.p_rank, b.p_record, b.pop_rank, b.s1f_rank, b.g3f_rank, 
                    b.g2f_rank, b.g1f_rank, b.recent3, b.recent5, b.fast_r, 
                    b.slow_r, b.avg_r, b.convert_r, b.i_cycle, b.gap_b, 
                    b.jockey_old, b.reason, b.r_pop, b.jt_per, b.jt_cnt, 
                    b.jt_1st, b.jt_2nd, b.jt_3rd, b.h_cnt, b.h_mare, if(isnull(b.i_prehandy), 0, b.handycap - b.i_prehandy) AS prehandy, b.i_mock,
                    c.s1f_per, c.g3f_per, c.g1f_per, c.start_score,c.tot_score, rec_per, rec8_trend
                FROM rec010 a
                JOIN rec011 b ON a.rcity = b.rcity 
                            AND a.rdate = b.rdate 
                            AND a.rno = b.rno
                LEFT OUTER JOIN exp011 c ON c.rcity = b.rcity 
                                        AND c.rdate = b.rdate 
                                        AND c.rno = b.rno
                                        AND c.gate = b.gate 
                WHERE a.rcity = %s
                    AND a.rdate = %s
                    AND a.rno = %s
                ORDER BY b.rank ASC, b.gate ASC;
            """

            cursor.execute(strSql, (rcity, rdate, rno))
            result = cursor.fetchall()
            return result

    except Exception as e:
        print(f"❌ Failed executing resultOfRace: {e}")
        return None

def countOfRace(rcity, rdate, rno):
    try:
        cursor = connection.cursor()
        strSql = """ 
            
            SELECT horse, count(*) AS cnt
            FROM treat
            WHERE horse IN (
                SELECT horse
                FROM exp011
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s
            )
            AND tdate BETWEEN DATE_FORMAT(DATE_ADD(%s, INTERVAL -30 DAY), '%%Y%%m%%d') AND %s
            AND (disease LIKE '%%피로회복%%' )
            GROUP BY horse ;
        """
        # 안전한 SQL 파라미터 바인딩
        params = (
            rcity,
            rdate,
            rno,
            rdate,
            rdate,
        )

        cursor.execute(strSql, params)
        recovery_cnt = cursor.fetchall()

    except:
        print(f"❌ Failed selecting in horses:")  # 오류 메시지 출력
    finally:
        cursor.close()

    # print(recovery_cnt)

    try:
        cursor = connection.cursor()
        strSql = """ 
            
                    SELECT horse, count(*) AS cnt
                    FROM start_train
                    WHERE horse IN (
                        SELECT horse
                        FROM exp011
                        WHERE rcity = %s
                        AND rdate = %s
                        AND rno = %s
                    )
                    AND tdate BETWEEN DATE_FORMAT(DATE_ADD(%s, INTERVAL -30 DAY), '%%Y%%m%%d') AND %s
                    GROUP BY horse ;
        """
        # 안전한 SQL 파라미터 바인딩
        params = (
            rcity,
            rdate,
            rno,
            rdate,
            rdate,
        )

        cursor.execute(strSql, params)
        start_cnt = cursor.fetchall()

    except:
        print(f"❌ Failed selecting in horses:")  # 오류 메시지 출력
    finally:
        cursor.close()

    try:
        cursor = connection.cursor()
        strSql = """ 
            
                    SELECT horse, count(*) AS cnt
                    FROM start_audit
                    WHERE horse IN (
                        SELECT horse
                        FROM exp011
                        WHERE rcity = %s
                        AND rdate = %s
                        AND rno = %s
                    )
                    AND rdate BETWEEN DATE_FORMAT(DATE_ADD(%s, INTERVAL -30 DAY), '%%Y%%m%%d') AND %s
                    GROUP BY horse ;
        """
        # 안전한 SQL 파라미터 바인딩
        params = (
            rcity,
            rdate,
            rno,
            rdate,
            rdate,
        )

        cursor.execute(strSql, params)
        audit_cnt = cursor.fetchall()

    except:
        print(f"❌ Failed selecting in horses:")  # 오류 메시지 출력
    finally:
        cursor.close()

    return recovery_cnt, start_cnt, audit_cnt
