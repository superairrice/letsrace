import datetime
import json
from django.db import connection
import pandas as pd
import numpy as np
from requests import session

from django.db.models import Count, Max, Min, Q
from base.models import Exp011


# 경주 시뮬레이션 가중치 get
def get_weight(rcity, rdate, rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert, 0 w_flag
            from weight_s1
            where rcity =  '"""
            + rcity
            + """'
            and rdate = '"""
            + rdate
            + """'
            and rno =  """
            + str(rno)
            + """
            and wdate = ( select max(wdate) from weight_s1 where rcity =  '"""
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
                select w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert, 1 w_flag
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
def mock_insert(rcity, rdate, rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            SELECT count(*) FROM exp011s1
            WHERE rcity = %s
            AND rdate = %s
            AND rno = %s
            ; """
        )
        params = (rcity, rdate, rno)
        cursor.execute(strSql, params)  # 결과값 개수 반환

        result = cursor.fetchall()

    except:
        connection.rollback()
        print("Failed selecting in exp011s1")
    finally:
        cursor.close()

    # print(result)

    if result[0][0] == 0:
        try:
            cursor = connection.cursor()

            strSql = (
                """ 
                insert into exp011s1
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
            print("Failed inserting in exp011s1")
        finally:
            cursor.close()
    else:
        try:
            cursor = connection.cursor()

            strSql = (
                """ 
                UPDATE exp011s1 a set r_pop = ( SELECT r_pop FROM exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
                r_record = ( SELECT r_record FROM exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
                h_weight = ( SELECT h_weight FROM exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
                r_rank = ( SELECT r_rank FROM exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate )
                WHERE rcity =  '"""
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
            print("Failed inserting in exp011s1")
        finally:
            cursor.close()

    return result


def mock_traval(r_condition, weight):

    for i in range(1, int(r_condition.rcount) + 1):

        # 게이트별 경주조건 query
        try:
            cursor = connection.cursor()

            # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
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
        i_jockey = get_jockey_ability(
            r_condition.rdate,            # 경주일
            str(gate_con[0][3]),          # 부담중량
            str(gate_con[0][1]),          # 경주거리
            gate_con[0][4],               # 기수
            i,                            # 게이트
        )

        # print(gate_con[0][4], i_jockey)
        i_avg, i_fast, i_slow = set_common(r_condition.rcity, r_condition.rdate, gate_con[0][1], gate_con[0][2], i_jockey[0][0])   # 경마장, 경주일, 경주거리, 경주마, 경주역량
        furlong_cnt = set_record(r_condition.rcity, r_condition.rdate, gate_con[0][1], gate_con[0][2], i_jockey[0][0], weight, i_avg, i_fast, i_slow)   # 경마장, 경주일, 경주거리, 경주마, 기수역량, 가중치

        # print(common)
        # print(furlong)
        
    set_rank(r_condition.rcity, r_condition.rdate, r_condition.rno)   # 경마장, 경주일, 경주번호 => race rank set
    

    return furlong_cnt

# i_jockey : 기수의 거리별 게이트별 부담중량 대비 가중치 Query
def get_jockey_ability(rdate, handycap, distance, jockey, gate):        
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

        if i_jockey[0][0]:       # select avg 는 1건 반환 (None)
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
def set_common(rcity, rdate, distance, horse, i_jockey):

    # 경주마 기수역량 감안된 평균기록
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
        strSql = (
            """ 
            SELECT ifnull( avg( (i_s1f * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0),
                ifnull( avg( (i_r1c * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0),
                ifnull( avg( (i_r2c * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0),
                ifnull( avg( (i_r3c * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0),
                ifnull( avg( (i_r4c * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0),
                ifnull( avg( (i_g3f * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0),
                ifnull( avg( (i_g2f * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0),
                ifnull( avg( (i_g1f * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0),
                ifnull( avg( i_convert - """ + str(i_jockey) + """ ), 0),
                ifnull( max( i_convert - """ + str(i_jockey) + """ ), 0),
                ifnull( min( i_convert - """ + str(i_jockey) + """ ), 0)
            --  INTO :i_s1f,	:i_r1c,	:i_r2c,	:i_r3c,	:i_r4c,	:i_g3f,	:i_g2f,	:i_g1f,	:i_avg, :i_slow,	:i_fast
            from record_s a
            WHERE a.rdate between '20180722' and '""" + rdate + """'
            and a.rdate < '""" + rdate + """'
            AND a.horse  = '""" + horse + """'
            AND a.distance = """ + str(distance) + """
            and r_flag = '0'
            and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 777 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < '""" + rdate + """'  )         
                            and ( select max(rdate) from record_s where horse = a.horse and rdate < '""" + rdate + """' )
            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        common = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        connection.rollback()
        print(
            "Failed selecting 거리별 경주마 평균.최고.최저기록. 코너링 평균 - set_common()", horse
        )

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
                ifnull( avg( (i_s1f * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0) +
                        avg( ifnull( ( select adv_s1f from adv_furlong where rcity = '""" + rcity + """' and grade = a.grade and dist1 = """ + str(distance) + """ and dist2 = a.distance ), 
                      ( select avg( adv_s1f ) from adv_furlong where rcity = '""" + rcity + """' and dist1 = """ + str(distance) + """ and dist2 = a.distance ) ) ),
                ifnull( avg( (i_g1f * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0) +
                        avg( ifnull( ( select adv_g1f from adv_furlong where rcity = '""" + rcity + """' and grade = a.grade and dist1 = """ + str(distance) + """ and dist2 = a.distance ), 
                    ( select avg( adv_g1f ) from adv_furlong where rcity = '""" + rcity + """' and dist1 = """ + str(distance) + """ and dist2 = a.distance ) ) ),
                ifnull( avg( (i_g2f * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0) +
                        avg( ifnull( ( select adv_g2f from adv_furlong where rcity = '""" + rcity + """' and grade = a.grade and dist1 = """ + str(distance) + """ and dist2 = a.distance ), 
                      ( select avg( adv_g2f ) from adv_furlong where rcity = '""" + rcity + """' and dist1 = """ + str(distance) + """ and dist2 = a.distance ) ) ),
                ifnull( avg( (i_g3f * (i_convert - """ + str(i_jockey) + """) )/i_record ), 0) +
                        avg( ifnull( ( select adv_g3f from adv_furlong where rcity = '""" + rcity + """' and grade = a.grade and dist1 = """ + str(distance) + """ and dist2 = a.distance ), 
                    ( select avg( adv_g3f ) from adv_furlong where rcity = '""" + rcity + """' and dist1 = """ + str(distance) + """ and dist2 = a.distance ) ) )
            --  INTO :i_cs1f,	:i_cg1f,	:i_cg2f,	:i_cg3f
            from record_s a
            WHERE a.rdate between '20180722' and '""" + rdate + """'
            and a.rdate < '""" + rdate + """'
            AND a.horse  = '""" + horse + """'
            -- AND a.distance = """ + str(distance) + """
            and r_flag = '0'
            and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 777 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < '""" + rdate + """'  )         
                            and ( select max(rdate) from record_s where horse = a.horse and rdate < '""" + rdate + """' )

              ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        furlong = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        connection.rollback()
        print(
            "Failed selecting 거리별 경주마 평균.최고.최저기록. 코너링 평균 set_common - furlong 환산", horse
        )

    i_cs1f = furlong[0][0]	
    i_cg1f = furlong[0][1]	
    i_cg2f = furlong[0][2]	
    i_cg3f = furlong[0][3]

    # print("furlong", i_cs1f, i_cg1f, i_cg2f, i_cg3f)

    # 경주마 furlong 기록 환산
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey
        strSql = (
            """ 
            UPDATE exp011s1  
            SET rs1f = substr(The1.f_t2s(""" + str(i_s1f) + """), -4),	
                r1c = The1.f_t2s(""" + str(i_r1c) + """),	
                r2c = The1.f_t2s(""" + str(i_r2c) + """),	
                r3c = The1.f_t2s(""" + str(i_r3c) + """),	
                r4c = The1.f_t2s(""" + str(i_r4c) + """),
                rg3f = substr(The1.f_t2s(""" + str(i_g3f) + """), -4),	
                rg2f = substr(The1.f_t2s(""" + str(i_g2f) + """), -4),	
                rg1f = substr(The1.f_t2s(""" + str(i_g1f) + """), -4),
                fast_r = The1.f_t2s(""" + str(i_fast) + """),	
                slow_r = The1.f_t2s(""" + str(i_slow) + """),
                avg_r = The1.f_t2s(""" + str(i_avg) + """),
                cs1f = substr(The1.f_t2s(""" + str(i_cs1f) + """), -4),	
                cg3f = substr(The1.f_t2s(""" + str(i_cg3f) + """), -4),	
                cg2f = substr(The1.f_t2s(""" + str(i_cg2f) + """), -4),	
                cg1f = substr(The1.f_t2s(""" + str(i_cg1f) + """), -4),
                i_s1f = """ + str(i_cs1f) + """,			
                i_g3f = """ + str(i_cg3f) + """,			
                i_g2f = """ + str(i_cg2f) + """,			
                i_g1f = """ + str(i_cg1f) + """,
                i_jockey = """ + str(i_jockey) + """
                
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
        connection.rollback()
        print("Failed uptating 경주마 평균.최고.최저기록. 코너링 평균 set_common update", horse)

    return i_avg, i_fast, i_slow  # 거리별 평균, 최고, 최저기록


# 최고 , 최고, 평균 기록, 코너별 기록 : common, furlong환산
def set_record(rcity, rdate, distance, horse, i_jockey, weight, i_avg, i_fast, i_slow):

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
            SELECT distance, i_s1f + i_g1f + adv_track, rank, i_convert - """ + str(i_jockey) + """, rstate, rdate,
                ( ( i_convert )/a.distance ) * """ + str(distance) + """ - """ + str(i_jockey) + """ + 
                    ifnull( ( select adv_dist from adv_distance where rcity = '""" + rcity + """'
                                                                and grade = a.grade 
                                                                and dist1 = """ + str(distance) + """
                                                                and dist2 = a.distance ), 
            ( select avg( adv_dist ) from adv_distance where dist1 = """ + str(distance) + """
                                                            and dist2 = a.distance ) )		-- 해당경주의 등급별 기록이 없으면, 평균값 치환
            FROM record_s 	a  
            WHERE a.rdate between '20180722' and '""" + rdate + """' and a.rdate < '""" + rdate + """'
            AND a.horse  = '""" + horse + """'
            and r_flag = '0'
            and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 777 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < '""" + rdate + """'  )         
                            and ( select max(rdate) from record_s where horse = a.horse and rdate < '""" + rdate + """' )
            ORDER BY a.rdate DESC 
            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        recent_race = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        connection.rollback()
        print(
            "Failed setting 경주마 최근 7경주 query ", horse, strSql
        )

    # print(recent_race)
    i_cnt = 0
    i_cnt3 = 0
    ls_remark = ''
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

        # print(index, i_100m, horse)

        if i_cnt <= 6:
            ls_remark = ls_remark + str(i_rank) + "-"

        i_cnt = i_cnt + 1

        if i_compare == distance: 		# 해당거리 최근 경주만 합산 
            i_cnt3 = i_cnt3 + 1
            i_recent3 = i_recent3 + i_recent

        # i_100m이 null 이면 거리 환산 기록이 없는 경우 발생 -- 예외처리 필요
        if i_100m:
            i_recent5 = i_recent5 + i_100m
            i_array.append(i_100m)            # 배열 추가
        else:
            i_cnt = i_cnt - 1				#	/* 환산기록이 없는 경주는 스킵하고 진행 ?(로직 고민 필요 )     이 경주 이후에는 기록이 생성됨   adv_distance Table 집계 */

        if i_cnt == 7:
            break

    # print(ls_remark)
    # print(i_array)

    tval = 0
    max = 0
    min = 30000    
    if i_cnt >= 3:

        for i in range(0, i_cnt):

            # print(i)
            tval = i_array[i]
            if max < tval:  #최대값 비교 
                max = tval 

            if min > tval:  #최소값 비교 
                min = tval 

            # print(max, min, tval)

        if max > i_recent5/i_cnt + 60:			                # 제일 느린 기록이 평균기록보다 1초 이상 느리면 제외
            if i_rstate == '불량' and i_rstate == '포화':					# 주로 상태가 불량이면 제외	
                i_recent5 = i_recent5 - max
                i_cnt = i_cnt -1

                # update record_s set flag = '1'  where rdate = :i_rdate and horse = :ls_horse ;
                # commit ;

        if min < i_recent5/i_cnt - 60:			                # 제일 빠른 기록이 평균기록보다 2초이상 빠르면 제외
            if i_rstate == '불량' and i_rstate == '포화':					# 주로 상태가 불량이면 제외	
                i_recent5 == i_recent5 - min
                i_cnt = i_cnt -1

                # update record_s set flag = '1'  where rdate = :i_rdate and horse = :ls_horse ;
                # commit ;

    if i_cnt >= 1: 
        i_recent5 = i_recent5 / i_cnt  
    else:
        i_recent5 = 0

    if i_cnt3 >= 1: 
        i_recent3 = i_recent3 / i_cnt3 
    else:
        i_recent3 = 0

    i_convert = ( i_avg * iw_avg + i_fast * iw_fast + i_slow * iw_slow ) /100

    if i_convert == 0: 
        i_convert = i_recent5
    if i_recent3 == 0:
        i_recent3 = i_recent5

    i_complex = ( i_recent3 * iw_recent3 + i_recent5 * iw_recent5 + i_convert * iw_convert ) / 100

    # 경주마 furlong 기록 환산
    # print(horse, i_convert, i_complex)

    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey
        strSql = (
            """ 
            UPDATE exp011s1  
            SET recent3 = The1.f_t2s(""" + str(i_recent3) + """),
                recent5 = The1.f_t2s(""" + str(i_recent5) + """),
                complex = The1.f_t2s(""" + str(i_complex) + """),
                convert_r = The1.f_t2s(""" + str(i_convert) + """),
                i_complex = """ + str(i_complex) + """
                
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
        connection.rollback()
        print("Failed uptating 경주마 평균.최고.최저기록. 코너링 평균 --- set record", horse, strSql)

    return r_cnt


# 경주 rank set
def set_rank(rcity, rdate, rno):

    # 경주마 기수역량 감안된 평균기록
    try:
        cursor = connection.cursor()

        # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
        strSql = (
            """ 
            SELECT i_complex, gate
            FROM exp011s1
            WHERE rcity = '"""
            + rcity
            + """'
              AND rdate = '"""
            + rdate
            + """'
            AND rno  = """
            + str(rno)
            + """
            AND rank < 90 ORDER BY i_complex    ASC, gate      ASC
            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race = cursor.fetchall()

    except:
        print(
            "Failed setting 경주 rank "
        )
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
                    UPDATE exp011s1  															
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
                rank = cursor.fetchall()

            except:
                print(
                    "Failed setting 경주 rank "
                )
            finally:
                cursor.close()

        else:
            try:
                cursor = connection.cursor()

                # 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
                strSql = (
                    """ 
                    UPDATE exp011s1  															
                    SET rank = """ + str(index) + """
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
                rank = cursor.fetchall()

            except:
                print("Failed setting 경주 rank ")
            finally:
                cursor.close()

    try:
        cursor = connection.cursor()

        # complex5 update
        strSql = (
            """ 
            UPDATE exp011s1  a
            SET complex5 = ( select complex from exp011s1 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank  = 4 ),
                gap = a.i_complex - ( select i_complex from exp011s1 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = a.rank - 1 ),
                gap_back = ( select i_complex from exp011s1 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = a.rank + 1 ) - a.i_complex 
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
        result = cursor.fetchall()

    except:
        print("Failed uptating complex5 update --- set rank")
    finally:
        cursor.close()

    try:
        cursor = connection.cursor()

        # complex5 update
        strSql = (
            """ 
            UPDATE exp011  a
            SET rank = ( select rank from The1.exp011s1 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
                complex = ( select complex from The1.exp011s1 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
                complex5 = ( select complex5 from The1.exp011s1 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
                gap = ( select gap from The1.exp011s1 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
                gap_back = ( select gap_back from The1.exp011s1 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate )
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

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

    except:
        print("Failed uptating exp011 update --- set rank")
    finally:
        cursor.close()

    return 
