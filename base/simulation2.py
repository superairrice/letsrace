import datetime
import json
from django.db import connection
import pandas as pd
import numpy as np
from requests import session

from django.db.models import Count, Max, Min, Q
from base.models import Exp011


# 경주 시뮬레이션 가중치 get
def get_weight2(rcity, rdate, rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert, 0 w_flag, wdate
            from weight_s2
            where rcity =  '"""
            + rcity
            + """'
            and rdate = '"""
            + rdate
            + """'
            and rno =  """
            + str(rno)
            + """
            and wdate = ( select max(wdate) from weight_s2 where rcity =  '"""
            + rcity
            + """'
                                                                and rdate = '"""
            + rdate
            + """'
                                                                and rno =  """
            + str(rno)
            + """ )
            
            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        weight = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        connection.rollback()
        print("Failed inserting in h_weight")

    if weight:
        return weight
    else:

        try:
            cursor = connection.cursor()

            strSql = """ 
                select w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert, 1 w_flag, now() wdate
                from weight
                where wdate = ( select max(wdate) from weight )
                
                ; """

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            weight = cursor.fetchall()

            # connection.commit()
            # connection.close()

        except:
            connection.rollback()
            print("Failed inserting in weight")

    return weight


# 경주 시뮬레이션 Data 입력
def mock_insert2(rcity, rdate, rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
            select count(*) FROM exp011s2
            WHERE rcity = %s
            AND rdate = %s
            AND rno = %s
            ; """
        params = (rcity, rdate, rno)
        r_cnt = cursor.execute(strSql, params)  # 결과값 개수 반환
        result = cursor.fetchall()

    except:
        print("Failed selecting in exp011s2")
    finally:
        cursor.close()

    # print("exp011s2 count:", r_cnt, result[0][0])

    if result[0][0] == 0:

        try:
            cursor = connection.cursor()

            strSql = (
                """ 
                insert into exp011s2
                SELECT * FROM exp011
                where rcity =  '"""
                + rcity
                + """'
                and rdate = '"""
                + rdate
                + """'
                and rno =  """
                + str(rno)
                + """
                ; """
            )

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            result = cursor.fetchall()

        except:
            print("Failed inserting in exp011s2")
        finally:
            cursor.close()
    else:

        try:
            cursor = connection.cursor()

            strSql = """
                UPDATE exp011s2 s
                JOIN exp011 e
                ON  s.rcity = e.rcity
                AND s.rdate = e.rdate
                AND s.rno   = e.rno
                AND s.gate  = e.gate
                SET 
                    s.r_rank     = e.r_rank,
                    s.jockey     = e.jockey,
                    s.h_weight     = e.h_weight,
                    s.handycap     = e.handycap,
                    s.jt_per    = e.jt_per,
                    s.jt_cnt    = e.jt_cnt,
                    s.jt_1st    = e.jt_1st,
                    s.jt_2nd    = e.jt_2nd,
                    s.jt_3rd    = e.jt_3rd,
                    s.j_per    = e.j_per,
                    s.t_per    = e.t_per,
                    s.r_record   = e.r_record,
                    s.jockey_old = e.jockey_old,
                    s.reason     = e.reason,
                    s.alloc1r    = e.alloc1r,
                    s.alloc3r    = e.alloc3r,
                    s.m_rank     = e.m_rank,
                    s.m_score    = e.m_score
                WHERE 
                    s.rcity = %s
                AND s.rdate = %s
                AND s.rno   = %s
            """

            params = (rcity, rdate, rno)

            affected_rows = cursor.execute(strSql, params)
            connection.commit()

            print("업데이트된 행:", affected_rows)

        except Exception as e:
            print("Failed updating exp011s2:", e)

        finally:
            cursor.close()

    return result


def mock_traval2(r_condition, weight):

    for i in range(1, int(r_condition.rcount) + 1):

        # 게이트별 경주조건 query
        try:
            cursor = connection.cursor()

            # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey
            strSql = (
                """ 
                SELECT grade,	distance,	horse, handycap, jockey, trainer,
                    ( select year_per from jockey_w where a.jockey = jockey and wdate = ( select max(wdate) from jockey_w where wdate < '"""
                + r_condition.rdate
                + """' and weekday(wdate) = 6 ) ),
                    ( select year_per from trainer_w where a.trainer = trainer and wdate = ( select max(wdate) from trainer_w where wdate < '"""
                + r_condition.rdate
                + """' and weekday(wdate) = 6 ) )
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

        except:
            print(
                "Failed selecting in 게이트별 조건 Query, 등급, 거리, 경주마, 부담중량, 기수, 마방, 기수복승률, 조교사 복승률 등"
            )
        finally:
            cursor.close()

        # 기수 역량 가중치 쿼리 : 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey Query
        i_jockey = get_jockey_ability2(
            r_condition.rdate,  # 경주일
            str(gate_con[0][3]),  # 부담중량
            str(gate_con[0][1]),  # 경주거리
            gate_con[0][4],  # 기수
            i,  # 게이트
        )

        # print(gate_con[0][4], i_jockey)
        i_avg, i_fast, i_slow = set_common2(
            r_condition.rcity,
            r_condition.rdate,
            gate_con[0][1],
            gate_con[0][2],
            i_jockey[0][0],
        )  # 경마장, 경주일, 경주거리, 경주마, 경주역량
        furlong_cnt = set_record2(
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

        # print(common)
        # print(furlong)

    set_rank2(
        r_condition.rcity, r_condition.rdate, r_condition.rno
    )  # 경마장, 경주일, 경주번호 => race rank set

    return furlong_cnt


# i_jockey : 기수의 거리별 게이트별 부담중량 대비 가중치 Query
def get_jockey_ability2(rdate, handycap, distance, jockey, gate):
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

        # connection.commit()
        # connection.close()

    except:
        connection.rollback()
        print(
            "Failed selecting 거리별 게이트별 기수 역량 Query : adv_jockey + f_burden_w"
        )

    # print(jockey, i_jockey, r_cnt)

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

            # print(r_cnt)

            # connection.commit()
            # connection.close()

        except:
            connection.rollback()
            print("Failed selecting 게이트별 기수 역량 Query : adv_jockey + f_burden_w")

        # print(jockey, "none>", i_jockey[0][0], r_cnt)

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

                # connection.commit()
                # connection.close()

            except:
                connection.rollback()
                print("Failed selecting 기수 역량 Query : f_burden_w only")

    return i_jockey


# 최고 , 최고, 평균 기록, 코너별 기록 : common, furlong환산
def set_common2(rcity, rdate, distance, horse, i_jockey):

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

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
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
                UPDATE exp011s2  
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
                    
                    -- recent3 = :ls_recent3,	recent5 = :ls_recent5, 	complex = :ls_complex,	convert_r = :ls_convert,                
                    -- i_complex = :i_complex,		i_jockey = :i_jockey,
                    -- i_cycle = f_rcycle( :as_rcity, :as_rdate, :ls_horse ),
                    -- i_prehandy = f_prehandy( :as_rcity, :as_rdate, :ls_horse ),
                    -- remark = :ls_remark,
                    -- h_weight = :ll_weight,
                    -- j_per = :ld_jockey_per,
                    -- t_per = :ld_trainer_per,
                    -- jt_per = :ld_per,
                    -- jt_cnt = :li_rcnt,
                    -- jt_1st = :li_1st,
                    -- jt_2nd = :li_2nd,
                    -- jt_3rd = :li_3rd
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
def set_record2(rcity, rdate, distance, horse, i_jockey, weight, i_avg, i_fast, i_slow):

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

        # connection.commit()
        # connection.close()

    except:
        connection.rollback()
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

        mock_update(horse, i_rdate, i_100m, connection)

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

        # print(i, 'array', horse, i_array[i], f_t2s(int(i_array[i])))

        tval = i_array[i]
        if max < tval:  # 최대값 비교
            max = tval

        if min > tval:  # 최소값 비교
            min = tval

    if i_cnt > 0:

        i_recent = i_recent5/i_cnt

        if max > i_recent + 60:  # 제일 느린 기록이 평균기록보다 1초 이상 느리면 제외
            i_recent5 = i_recent5 - max
            i_cnt = i_cnt - 1

            # print("max", horse, max, f_t2s(int(i_recent)),'---', i_cnt, f_t2s(int(max)))
            # print(i_recent5, i_cnt)

        if i_cnt >= 3:               # 최소 3건 이상일때만 min 체크    - 나머지 2경주 중 특정 경주를 제외할 수 없을때
            if min < i_recent - 60:  # 제일 빠른 기록이 평균기록보다 1초이상 빠르면 제외
                i_recent5 = i_recent5 - min
                i_cnt = i_cnt - 1

                # print("min", horse, min, f_t2s(int(i_recent)),'---', i_cnt, f_t2s(int(min)))

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

    ls_remark = get_remark2(rdate, horse)  # 경주마 최근 7경주 코멘트
    # ls_remark = ls_remark + " (" + str(r_cnt) + ")"
    # print(horse, i_recent3, i_recent5, i_convert, i_complex, ls_remark)

    try:
        cursor = connection.cursor()
        strSql = """
            select %s, gate, horse, rdate '과거경주일', distance, rank, 
            
            -- i_convert '부담중량 주로상태 반영 환산기록', 
            
            ( ( i_convert )/a.distance ) * %s + 
                    ifnull( ( select adv_dist from adv_distance 
                                where rcity = %s and grade = a.grade and dist1 = %s and dist2 = a.distance ), 
            ( select ifnull(avg( adv_dist ),0) from adv_distance where rcity = %s and dist1 = %s and dist2 = a.distance ) )	,
            
            ifnull( ( (i_s1f * (i_convert ) )/i_record ), 0) +
                        ( ifnull( ( select adv_s1f from adv_furlong where rcity = %s and grade = a.grade and dist1 = %s and dist2 = a.distance ), 
                        ( select ifnull( avg( adv_s1f ), 0) from adv_furlong where rcity = %s and dist1 = %s and dist2 = a.distance ) ) ),
                        
            ifnull( ( (i_g3f * (i_convert) )/i_record ), 0) +
                        ( ifnull( ( select adv_g3f from adv_furlong where rcity = %s and grade = a.grade and dist1 = %s and dist2 = a.distance ), 
                    ( select ifnull( avg( adv_g3f ), 0) from adv_furlong where rcity = %s and dist1 = %s and dist2 = a.distance ) ) ),
            
            -- i_s1f '초반 200m', 
            -- i_g3f '종반 600m', 
            
            h_weight, w_change, grade, r_judge '경주등급별 편성강도', alloc3r
            from The1.record a
            where horse = %s 
            and r_judge is not null
            -- and ( r_flag = '0' or r_flag is null ) 
            and rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 365 DAY), '%%Y%%m%%d') from record where horse = a.horse and rdate < %s )         
                            and ( select max(rdate) from record where horse = a.horse and rdate < %s )
            and rank < 98
            -- and r_flag = '0'
            order by rdate desc
            limit 8

            ;
        """

        r_cnt = cursor.execute(
            strSql,
            (   
                rdate,
                distance, rcity, distance, rcity, distance,
                rcity, distance, rcity, distance,
                rcity, distance, rcity, distance,
                horse,
                rdate,
                rdate,
            ),
        )  # 결과값 개수 반환
        races = cursor.fetchall()

        (trend, trend_numeric), detail = judge_horse_trend_7level(races)

        # print(horse, trend, trend_numeric)

        print(horse, trend, trend_numeric, detail["reasons"])  # '상승세' / '하락세' / '보합세'

        s1f_rank = trend_numeric
        g3f_rank = round( detail["pos_votes"], 1)*5
        g1f_rank = round( detail["neg_votes"], 1)*5

        net = round( detail["net"], 1)*5

        # 1) 사유(reasons) 부분
        reason_lines = detail.get("reasons", [])
        reason_block = "\n".join(reason_lines) if reason_lines else ""

        # 2) 경주(races) 부분
        race_lines = []
        for r in races:
            # r[3] : race_date, r[5] : rank, r[6] : i_convert
            racedate = " '" + r[3][2:4] + "." + r[3][4:6] + "." + r[3][6:8]
            rec = f_t2s(int(r[6]))
            s1f = f_t2s(int(r[7]))[2:]
            g3f = f_t2s(int(r[8]))[2:]
            # grade = r[11][0:2]           # 원본 "국5" / "혼2" / "O4" / "5등" 등

            grade = (
                r[11][0:2]
                .replace("혼", "")
                .replace("국", "")
                .replace("등", "")
                .replace("O", "0")
            )

            alloc3r = r[13]
            # 필요하면 정수 변환도 가능
            # clean_int = int(clean)

            race_lines.append(
                f"{racedate} ... G{grade} ... {s1f} ... {g3f}  ... {rec} ... 순위: {r[5]} ... {alloc3r} ... {r[12]}"
            )

        race_block = "\n".join(race_lines) if race_lines else ""

        # 3) 최종 g2f_rank 조합
        if reason_block and race_block:
            # 사유 + 빈 줄 + [최근 경주] + 경주목록
            g2f_rank = reason_block + "\n\n'경주 일자 ... 등급 ... S1F ... G3F ... 환산기록 ... 순위 ... 연식 ... 강도 \n" + race_block
        elif reason_block:
            g2f_rank = reason_block
        elif race_block:
            g2f_rank = race_block
        else:
            g2f_rank = "(사유 및 최근 경주 데이터 없음)"

        # print(g2f_rank)
        # print(horse, result["category"], result["diff"], s1f_rank)
        # print("                    사용된 경주 수:", result["used_count"], g3f_rank)
        # print("                    지표별 변화:", result["components"])

    except Exception as e:
        print("Failed selecting 경주마 최근 1년간 8경주 성적 :", horse, e)
    finally:
        if cursor:
            cursor.close()

    try:

        # print("=== 최종 g2f_rank ===")
        # print(repr(g2f_rank))   # repr 로 줄바꿈 포함 전체 확인
        # print("====================")

        cursor = connection.cursor()
        strSql = """
            UPDATE exp011s2
            SET recent3   = The1.f_t2s(%s),
                recent5   = The1.f_t2s(%s),
                complex   = The1.f_t2s(%s),
                convert_r = The1.f_t2s(%s),
                
                i_complex = %s, 
                
                s1f_rank = %s,
                g3f_rank = %s,
                g2f_rank = %s,
                g1f_rank = %s,
                
                bet = %s,
                remark    = %s
            WHERE rdate = %s
            AND horse = %s
        """
        params = (i_recent3, i_recent5, i_complex, i_convert, i_complex, s1f_rank, g3f_rank, g2f_rank, g1f_rank, i_cnt, ls_remark, rdate, horse)

        # 디버깅용 실제 SQL문 출력
        # print("Executing SQL:", strSql % ( params))

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
def set_rank2(rcity, rdate, rno):

    # 경주마 기수역량 감안된 평균기록
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
        strSql = (
            """ 
            SELECT i_complex, gate
            FROM exp011s2
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
                    UPDATE exp011s2  															
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
                    UPDATE exp011s2  															
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
            UPDATE exp011s2  a
            SET complex5 = ( select min(complex) from exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank  = 4 ),
                gap = a.i_complex - ( select min(i_complex) from exp011s2 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = a.rank - 1 ),
                gap_back = ( select min(i_complex) from exp011s2 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = a.rank + 1 ) - a.i_complex 
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
        print("Failed Update exp011s2 i_complex5 등 :", e, strSql)
    finally:
        if cursor:
            cursor.close()

    # try:
    #     cursor = connection.cursor()

    #     # complex5 update
    #     strSql = (
    #         """ 
    #         UPDATE exp011  a
    #         SET rank = ( select rank from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             complex = ( select complex from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             recent3 = ( select recent3 from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             recent5 = ( select recent5 from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             convert_r = ( select convert_r from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             rs1f = ( select rs1f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             rg3f = ( select rg3f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             rg2f = ( select rg2f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             rg1f = ( select rg1f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             cs1f = ( select cs1f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             cg3f = ( select cg3f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             cg2f = ( select cg2f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             cg1f = ( select cg1f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             i_s1f = ( select i_s1f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             i_g3f = ( select i_g3f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             i_g2f = ( select i_g2f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             i_g1f = ( select i_g1f from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             remark = ( select remark from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             bet = ( select bet from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             complex5 = ( select complex5 from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             gap = ( select gap from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
    #             gap_back = ( select gap_back from The1.exp011s2 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate )
    #         WHERE rcity = '"""
    #         + rcity
    #         + """'
    #         AND rdate = '"""
    #         + rdate
    #         + """'
    #         AND rno  = """
    #         + str(rno)
    #         + """
    #         ; """
    #     )

    #     # print(strSql)

    #     r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
    #     # connection.commit()

    # except Exception as e:
    #     connection.rollback()
    #     print("Failed Update exp011 all :", e, strSql)
    # finally:
    #     if cursor:
    #         cursor.close()

    return


def get_remark2(rdate, horse):

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

        # connection.commit()
        # connection.close()

    except:
        connection.rollback()
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


def compute_recent_average(horse, i_array):
    """
    최근 6경주의 기록 배열(i_array)을 기반으로
    평균기록(i_recent5)을 계산하되,
    평균 대비 ±60초 이상 차이 나는 기록은 제외한다.
    """

    if not i_array:
        return 0

    # 1️⃣ 정렬 및 기초 통계
    i_array.sort()
    i_cnt = len(i_array)
    avg = sum(i_array) / i_cnt
    max_val = max(i_array)
    min_val = min(i_array)

    print(f"[{horse}] 전체기록: {i_array}")
    print(f"평균: {avg:.2f}, 최소: {min_val}, 최대: {max_val}")

    # 2️⃣ 기준값 설정
    # 절대값 ±60이 아니라, 평균 ±60초 이내만 허용
    upper_limit = avg + 60
    lower_limit = avg - 60

    # 3️⃣ 허용범위 내의 기록만 필터링
    filtered = [v for v in i_array if lower_limit <= v <= upper_limit]

    print(f"허용범위: {lower_limit:.1f} ~ {upper_limit:.1f}")
    print(f"필터링 후: {filtered}")

    # 4️⃣ 최소 3건 이상 남을 경우에만 평균 계산
    if len(filtered) >= 3:
        i_recent5 = sum(filtered) / len(filtered)
    else:
        # 데이터가 너무 적으면 원래 평균 유지
        i_recent5 = avg

    print(f"최종 평균 ({horse}): {i_recent5:.2f} ({len(filtered)}건 유효)\n")

    return i_recent5


from datetime import datetime
from statistics import pstdev
from typing import List, Tuple, Any, Dict


def _linear_trend(values: List[float]):
    n = len(values)
    if n < 2:
        return 0.0, 0.0, 0.0, 0.0

    xs = list(range(n))
    ys = values

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)

    if den == 0:
        return 0.0, 0.0, 0.0, 0.0

    slope = num / den
    total_change = slope * (n - 1)
    std = pstdev(ys) if n > 1 else 0.0
    strength = abs(total_change) / std if std != 0 else 0.0

    return slope, total_change, std, strength

from datetime import datetime
from typing import Any, List, Tuple
import math


def _weighted_trend(values: List[float], decay: float = 0.5):
    """
    시간축 x = 0..n-1 에 대해
    w_i = decay**(경과경주수) = decay**((n-1)-i) 로 가중치를 두고
    가중 선형회귀를 수행.
    """
    n = len(values)
    if n < 2:
        return 0.0, 0.0, 0.0, 0.0

    x = list(range(n))
    # 가장 최근(인덱스 n-1)이 weight 1.0, 그 이전은 0.5, 0.25, ...
    w = [decay ** ((n - 1) - i) for i in range(n)]
    w_sum = sum(w)
    if w_sum == 0:
        return 0.0, 0.0, 0.0, 0.0

    mean_x = sum(w[i] * x[i] for i in range(n)) / w_sum
    mean_y = sum(w[i] * values[i] for i in range(n)) / w_sum

    cov_xy = (
        sum(w[i] * (x[i] - mean_x) * (values[i] - mean_y) for i in range(n)) / w_sum
    )
    var_x = sum(w[i] * (x[i] - mean_x) ** 2 for i in range(n)) / w_sum
    var_y = sum(w[i] * (values[i] - mean_y) ** 2 for i in range(n)) / w_sum

    if var_x == 0:
        slope = 0.0
    else:
        slope = cov_xy / var_x

    intercept = mean_y - slope * mean_x

    if var_x > 0 and var_y > 0:
        r = cov_xy / math.sqrt(var_x * var_y)
        strength = abs(r)
    else:
        r = 0.0
        strength = 0.0

    return slope, intercept, r, strength


from datetime import datetime
import math

def judge_horse_trend_7level(rows: List[Tuple[Any, ...]]):
    """
    경주거리 무시.
    i_convert / 초반200 / 종반600 / 순위 / 편성강도 기반 7단계 트렌드 판단.
    (강상승세/상승세/강보합세/보합세/약보합세/하락세/강하락세)

    ▸ 회귀 시 최근 경주에 가중치 적용 (0.5^(경과경주수))  → _weighted_trend 사용
    ▸ 지표별 가중치:
        - i_convert : 0.4
        - 조정순위 : 0.3
        - 종반600   : 0.2
        - 초반200   : 0.1
      → 표 개수가 아니라 가중치 합으로 상승/하락 판단

    ▸ 조정순위(adj_rank) 쪽은
        - 기울기 절대값이 일정 이상일 때만
        - 표준편차가 어느 정도 이상일 때만
        - 상관계수 강도도 더 높은 기준을 만족할 때만
      '추세로 인정'하도록 강화 (점순이고 같은 과긴 평가 방지)
    """

    # ======== 헬퍼: 가중 회귀 =========
    # 이미 프로젝트에 정의되어 있다면 이 부분은 중복 정의하지 말고 기존 것을 사용하세요.
    def _weighted_trend(values: List[float], decay: float = 0.5):
        """
        최근값에 더 높은 가중치를 주는 선형 추세 계산.
        반환: (slope, intercept, r, strength)
        strength = abs(r)
        """
        vals = [float(v) for v in values if v is not None]
        n = len(vals)
        if n < 2:
            return 0.0, 0.0, 0.0, 0.0

        # x: 0,1,...,n-1 (과거→최근)
        xs = list(range(n))
        # 최근일수록 가중치 ↑ (가장 최근 = 1.0)
        weights = [decay ** (n - 1 - i) for i in range(n)]
        w_sum = sum(weights)
        if w_sum == 0:
            return 0.0, 0.0, 0.0, 0.0

        # 가중 평균
        x_mean = sum(w * x for w, x in zip(weights, xs)) / w_sum
        y_mean = sum(w * y for w, y in zip(weights, vals)) / w_sum

        # 가중 공분산 / 분산
        cov = sum(w * (x - x_mean) * (y - y_mean)
                  for w, x, y in zip(weights, xs, vals)) / w_sum
        var_x = sum(w * (x - x_mean) ** 2
                    for w, x in zip(weights, xs)) / w_sum
        var_y = sum(w * (y - y_mean) ** 2
                    for w, y in zip(weights, vals)) / w_sum

        if var_x == 0 or var_y == 0:
            return 0.0, y_mean, 0.0, 0.0

        slope = cov / var_x
        intercept = y_mean - slope * x_mean
        r = cov / math.sqrt(var_x * var_y)
        strength = abs(r)
        return slope, intercept, r, strength

    # ======== 컬럼 인덱스 정의 =========
    date_col = 3
    rank_col = 5
    iconv_col = 6
    early_col = 7
    last600_col = 8
    field_col = 12

    # 지표별 가중치
    W_ICONV = 0.4
    W_RANKADJ = 0.3
    W_LAST600 = 0.2
    W_EARLY = 0.1

    parsed = []
    for r in rows:
        try:
            d = datetime.strptime(str(r[date_col]), "%Y%m%d")

            # i_convert: 핵심 지표 → 없으면 스킵
            raw_iconv = r[iconv_col]
            if raw_iconv in (None, ""):
                continue
            iconv = float(raw_iconv)

            # 초반 / 종반: None 허용
            raw_early = r[early_col]
            early = float(raw_early) if raw_early not in (None, "") else None

            raw_last600 = r[last600_col]
            last600 = float(raw_last600) if raw_last600 not in (None, "") else None

            rank = int(r[rank_col])
        except Exception:
            continue

        try:
            field = float(r[field_col])
        except Exception:
            field = None

        parsed.append(
            {
                "date": d,
                "i_convert": iconv,
                "early": early,
                "last600": last600,
                "rank": rank,
                "field": field,
                "raw": r,
            }
        )

    n = len(parsed)

    # ==========================
    # 1) 1경주 이하면 보합세
    # ==========================
    if n <= 1:
        msg = f"».   {n} 경주 : 추세를 판단하기에 데이터가 부족하여 보합세로 처리"
        trend_text = "보합세"
        trend_numeric = 0
        detail = {
            "reason": msg,
            "reasons": [msg],
            "pos_votes": 0.0,
            "neg_votes": 0.0,
            "net": 0.0,
            "total_votes": 0.0,
            "rows_sorted": [p["raw"] for p in parsed],
        }
        return (trend_text, trend_numeric), detail

    # 날짜 순 정렬 (과거 → 최근)
    parsed.sort(key=lambda x: x["date"])
    n = len(parsed)

    # ==========================
    # 2) field_strength 기반 조정 순위 함수
    # ==========================
    f_values = [p["field"] for p in parsed if p["field"] is not None]
    can_adjust = len(f_values) >= 2 and (max(f_values) != min(f_values))

    if can_adjust:
        f_min = min(f_values)
        f_max = max(f_values)
        f_range = f_max - f_min if f_max != f_min else 1.0

        def adj_rank(p):
            if p["field"] is None:
                return float(p["rank"])
            norm = (p["field"] - f_min) / f_range  # 0~1
            mult = 0.5 + norm                      # 0.5~1.5
            return p["rank"] / mult

    else:

        def adj_rank(p):
            return float(p["rank"])

    # ==========================
    # 3) 경주 수 2경주 → 변화량 기반 (가중치 포함)
    # ==========================
    if n == 2:
        older, newer = parsed[0], parsed[1]
        pos_score = 0.0
        neg_score = 0.0
        reasons: List[str] = []

        def vote_metric(name: str, old, new, small_is_good: bool, weight: float):
            nonlocal pos_score, neg_score, reasons
            if old is None or new is None:
                return
            if small_is_good:
                # 숫자 감소 = 개선, 숫자 증가 = 악화
                if new < old:
                    pos_score += weight
                    reasons.append(
                        f"{name} 개선 (이전 {old} → 최근 {new}) [w={weight}]"
                    )
                elif new > old:
                    neg_score += weight
                    reasons.append(
                        f"{name} 악화 (이전 {old} → 최근 {new}) [w={weight}]"
                    )
            else:
                # 숫자 증가 = 개선, 숫자 감소 = 악화
                if new > old:
                    pos_score += weight
                    reasons.append(
                        f"{name} 개선 (이전 {old} → 최근 {new}) [w={weight}]"
                    )
                elif new < old:
                    neg_score += weight
                    reasons.append(
                        f"{name} 악화 (이전 {old} → 최근 {new}) [w={weight}]"
                    )

        # i_convert / 초반200 / 종반600 / 조정순위
        vote_metric("i_convert", f_t2s(int(older["i_convert"])), f_t2s(int(newer["i_convert"])), True, W_ICONV)
        vote_metric("초반200 기록", f_t2s(int(older["early"])), f_t2s(int(newer["early"])), True, W_EARLY)
        vote_metric("종반600 기록", f_t2s(int(older["last600"])), f_t2s(int(newer["last600"])), True, W_LAST600)
        vote_metric("조정순위", round(adj_rank(older),1), round(adj_rank(newer),1), True, W_RANKADJ)

        net = pos_score - neg_score
        total = pos_score + neg_score

        # 최대 총 가중치 = 1.0
        if pos_score >= 0.75 and net >= 0.5:
            trend_text, trend_numeric = "강상승세", 3
        elif pos_score >= 0.5 and pos_score > neg_score:
            trend_text, trend_numeric = "상승세", 2
        elif neg_score >= 0.75 and net <= -0.5:
            trend_text, trend_numeric = "강하락세", -3
        elif neg_score >= 0.5 and neg_score > pos_score:
            trend_text, trend_numeric = "하락세", -2
        elif net > 0 and total >= 0.4:
            trend_text, trend_numeric = "강보합세", 1
        elif net < 0 and total >= 0.4:
            trend_text, trend_numeric = "약보합세", -1
        else:
            trend_text, trend_numeric = "보합세", 0

        if not reasons:
            reasons.append("2경주 모두에서 주요 지표 변화가 거의 없어 보합세로 처리")

        detail = {
            "mode": "2경주-변화량기반",
            "pos_votes": pos_score,
            "neg_votes": neg_score,
            "net": net,
            "total_votes": total,
            "reasons": reasons,
            "rows_sorted": [p["raw"] for p in parsed],
        }
        return (trend_text, trend_numeric), detail

    # ==========================
    # 4) 3경주 이상 → 가중 회귀 분석 기반
    # ==========================
    # 경주 수에 따라 추세 강도 기준 완화
    if n == 3:
        strength_threshold = 0.6
    elif n <= 5:
        strength_threshold = 0.5
    else:
        strength_threshold = 0.4

    i_list = [p["i_convert"] for p in parsed]
    e_full = [p["early"] for p in parsed]       # 전체에서 None 포함
    l_full = [p["last600"] for p in parsed]
    r_adj_list = [adj_rank(p) for p in parsed]

    # None 제거한 리스트(회귀용)
    e_list = [v for v in e_full if v is not None]
    l_list = [v for v in l_full if v is not None]

    ic_slope, _, _, ic_strength = _weighted_trend(i_list)
    e_slope, _, _, e_strength = (
        _weighted_trend(e_list) if len(e_list) >= 2 else (0.0, 0.0, 0.0, 0.0)
    )
    l_slope, _, _, l_strength = (
        _weighted_trend(l_list) if len(l_list) >= 2 else (0.0, 0.0, 0.0, 0.0)
    )
    rk_slope, _, _, rk_strength = _weighted_trend(r_adj_list)

    pos_score = 0.0
    neg_score = 0.0
    reasons: List[str] = []

    # ---- i_convert (작을수록 좋음) ----
    if ic_strength >= strength_threshold:
        if ic_slope < 0:
            pos_score += W_ICONV
            reasons.append("1.   i_convert 감소 추세 → 성능 개선 [w=0.4]")
        elif ic_slope > 0:
            neg_score += W_ICONV
            reasons.append("1.   i_convert 증가 추세 → 성능 악화 [w=0.4]")

    # ---- 초반 200m (작을수록 좋음) ----
    if e_strength >= strength_threshold:
        if e_slope < 0:
            pos_score += W_EARLY
            reasons.append("2.   초반 200m 기록 감소 → 스타트 개선 [w=0.1]")
        elif e_slope > 0:
            neg_score += W_EARLY
            reasons.append("2.   초반 200m 기록 증가 → 스타트 악화 [w=0.1]")

    # ---- 종반 600m (작을수록 좋음) ----
    if l_strength >= strength_threshold:
        if l_slope < 0:
            pos_score += W_LAST600
            reasons.append("3.   종반 600m 기록 감소 → 막판 탄력 개선 [w=0.2]")
        elif l_slope > 0:
            neg_score += W_LAST600
            reasons.append("3.   종반 600m 기록 증가 → 막판 탄력 악화 [w=0.2]")

    # ---- 조정 순위 (작을수록 좋음) ----
    # 여기서 "조정순위 때문에 과도하게 강상승/강하락으로 튀는" 현상을 막기 위해
    # 추가 안전장치를 건다.
    def _std(values: List[float]) -> float:
        vals = [v for v in values if v is not None]
        if len(vals) < 2:
            return 0.0
        m = sum(vals) / len(vals)
        var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
        return math.sqrt(var)

    rk_std = _std(r_adj_list)

    # 조정순위용 별도 기준:
    #  - 상관계수 강도는 기본 threshold보다 조금 더 높게
    #  - 기울기 절대값이 너무 작으면 무시
    #  - 표준편차 자체가 너무 작으면 (거의 일정하면) 추세로 보지 않음
    RANK_STRENGTH_THRESHOLD = max(strength_threshold, 0.7)  # 최소 0.7 이상
    RANK_SLOPE_MIN = 0.05
    RANK_STD_MIN = 0.5

    rank_trend_valid = (
        rk_strength >= RANK_STRENGTH_THRESHOLD
        and abs(rk_slope) >= RANK_SLOPE_MIN
        and rk_std >= RANK_STD_MIN
    )

    if rank_trend_valid:
        if rk_slope < 0:
            pos_score += W_RANKADJ
            reasons.append("4.   조정 순위 감소 추세 → 착순/난이도 감안 개선 [w=0.3]")
        elif rk_slope > 0:
            neg_score += W_RANKADJ
            reasons.append("4.   조정 순위 증가 추세 → 착순/난이도 감안 악화 [w=0.3]")

    # ===== 7단계 트렌드 (가중치 기반) =====
    net = pos_score - neg_score
    total = pos_score + neg_score

    if pos_score >= 0.75 and net >= 0.5:
        trend_text, trend_numeric = "강상승세", 3
    elif pos_score >= 0.5 and pos_score > neg_score:
        trend_text, trend_numeric = "상승세", 2
    elif neg_score >= 0.75 and net <= -0.5:
        trend_text, trend_numeric = "강하락세", -3
    elif neg_score >= 0.5 and neg_score > pos_score:
        trend_text, trend_numeric = "하락세", -2
    elif net > 0 and total >= 0.4:
        trend_text, trend_numeric = "강보합세", 1
    elif net < 0 and total >= 0.4:
        trend_text, trend_numeric = "약보합세", -1
    else:
        trend_text, trend_numeric = "보합세", 0

    # ==========================
    # 5) 경주 기복(변동성) 보정 (기복형)
    # ==========================
    def _volatility(values: List[float]) -> float:
        vals = [v for v in values if v is not None]
        if len(vals) < 2:
            return 0.0
        m = sum(vals) / len(vals)
        if m == 0:
            return 0.0
        var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
        std = math.sqrt(var)
        return std / abs(m)

    vol_ic = _volatility(i_list)
    vol_rk = _volatility(r_adj_list)

    VOL_IC_THRESHOLD = 0.02   # 2%
    VOL_RK_THRESHOLD = 1.00   # 100%

    is_volatile = (vol_ic >= VOL_IC_THRESHOLD) or (vol_rk >= VOL_RK_THRESHOLD)

    # 기본 트렌드가 -1~+1 (보합/강보합/약보합)일 때만 "기복형" 태그 부여
    if n >= 3 and is_volatile and abs(trend_numeric) <= 1:
        if trend_numeric > 0:
            trend_text = f"기복형 {trend_text}"
        elif trend_numeric < 0:
            trend_text = f"기복형 {trend_text}"
        else:
            trend_text = "기복형 보합세"

        reasons.append(
            f"i_convert/조정순위 변동성 큼 (i_convert CV {vol_ic:.1%}, 조정순위 CV {vol_rk:.1%}) → 경주 기복 큰 편"
        )

    # ==========================
    # 6) 이유가 하나도 없으면 기본 문구
    # ==========================
    if not reasons:
        reasons.append(
            f"{n}경주 모두에서 통계적으로 유의한 지표 변화가 없어 {trend_text}로 처리"
        )

    detail = {
        "mode": "회귀분석기반" if n >= 4 else "3경주-완화기준",
        "pos_votes": pos_score,
        "neg_votes": neg_score,
        "net": net,
        "total_votes": total,
        "reasons": reasons,
        "rows_sorted": [p["raw"] for p in parsed],
        "rank_adj_values": r_adj_list,
        "volatility": {
            "i_convert_cv": vol_ic,
            "rank_adj_cv": vol_rk,
        },
    }

    return (trend_text, trend_numeric), detail