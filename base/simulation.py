import datetime
import json
from django.db import connection
import pandas as pd
import numpy as np
from requests import session

from django.db.models import Count, Max, Min, Q
from base.models import Exp011


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

            connection.commit()
            connection.close()

        except:
            connection.rollback()
            print(
                "Failed selecting in 게이트별 조건 Query, 등급, 거리, 경주마, 부담중량, 기수, 마방, 기수복승률, 조교사 복승률 등"
            )

        # 기수 역량 가중치 쿼리 : 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jockey Query
        i_jockey = get_jockey_ability(
            r_condition.rdate,            # 경주일
            str(gate_con[0][3]),          # 부담중량
            str(gate_con[0][1]),          # 경주거리
            gate_con[0][4],               # 기수
            i,                            # 게이트
        )

        print(gate_con[0][4], i_jockey) 
        common, furlong = get_furlong(r_condition.rcity, r_condition.rdate, gate_con[0][1], gate_con[0][2], i_jockey[0][0])   # 경마장, 경주일, 경주거리, 경주마

        print(common)
        print(furlong)

    return i_jockey

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

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print(
            "Failed selecting 거리별 게이트별 기수 역량 Query : adv_jockey + f_burden_w"
        )

    if i_jockey:
        pass
    else:
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

            print(r_cnt)

            connection.commit()
            connection.close()

        except:
            connection.rollback()
            print("Failed selecting 게이트별 기수 역량 Query : adv_jockey + f_burden_w")

        # print((i_jockey[0]))

        if i_jockey[0] == None:       # select avg 는 1건 반환 (None)
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

                connection.commit()
                connection.close()

            except:
                connection.rollback()
                print("Failed selecting 기수 역량 Query : f_burden_w only")

    return i_jockey


# 최고 , 최고, 평균 기록, 코너별 기록 : common, furlong환산
def get_furlong(rcity, rdate, distance, horse, i_jockey):

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

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print(
            "Failed selecting 거리별 경주마 평균.최고.최저기록. 코너링 평균"
        )

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

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print(
            "Failed selecting 거리별 경주마 평균.최고.최저기록. 코너링 평균"
        )
        
    # print(furlong)

    return common, furlong
