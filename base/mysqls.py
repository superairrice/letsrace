import datetime
import json
from django.db import connection
import pandas as pd
import numpy as np
from requests import session

from django.db.models import Count, Max, Min, Q
from base.models import Exp011


def get_paternal_dist(rcity, rdate, rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                SELECT a.gate, a.rank, a.horse, 
                    b.paternal, c.distance,
                    sum(r1) r1,
                    sum(r2) r2,
                    sum(r3) r3,
                    sum(rtot) rtot
                FROM exp011	a,
                    horse		b right outer join paternal c on b.paternal = c.paternal 
                where  a.horse = b.horse
                AND a.rcity = '"""
            + rcity
            + """'
                AND a.rdate = '"""
            + rdate
            + """'
                AND a.rno = """
            + str(rno)
            + """
                
                group by a.gate, a.rank, a.horse, b.paternal , c.distance
                order by a.rank, a.gate, c.distance
            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_paternal(rcity, rdate, rno, distance):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
              SELECT a.gate, a.rank, a.horse, 
                    b.paternal, 
                    sum( if(c.distance = """
            + str(distance)
            + """, r1, 0 )) rd1,
                    sum( if(c.distance = """
            + str(distance)
            + """, r2, 0 )) rd2,
                    sum( if(c.distance = """
            + str(distance)
            + """, r3, 0 )) rd3,
                    sum( if(c.distance = """
            + str(distance)
            + """, rtot, 0)) rdtot,
                    
                    sum(r1) r1,
                    sum(r2) r2,
                    sum(r3) r3,
                    sum(rtot) rtot,
                    b.price/1000,
                    -- b.tot_prize/1000000
                    ( select price/1000 from horse_w where horse = a.horse and wdate = ( select min(wdate) from horse_w where horse = a.horse and price > 0)  )
                FROM exp011	a,
                    ( select horse, paternal, price, tot_prize 
                        from horse_w where wdate = ( select max(wdate) from horse_w where wdate <= '"""
            + rdate
            + """' )) b left outer join paternal c on b.paternal = c.paternal 
                where  a.horse = b.horse
                AND a.rcity = '"""
            + rcity
            + """'
                AND a.rdate = '"""
            + rdate
            + """'
                AND a.rno = """
            + str(rno)
            + """
                
                group by a.gate, a.rank, a.horse, b.paternal 
                order by a.rank, a.gate, a.horse, b.paternal
            ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_judged_jockey(rcity, rdate, rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                SELECT distinct rank, gate, a_horse, b_rdate, b_horse, jockey, trainer, t_sort, t_type, t_detail, t_reason, b_rcity, b_rno
                FROM (
                SELECT a.rank, a.gate, a.horse a_horse, b.rdate b_rdate, b.horse b_horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason, b.rcity b_rcity, b.rno b_rno
                FROM exp011     a,
                    rec015     b
                where a.jockey = b.jockey 
                AND b.t_sort = '기수'
                AND b.rdate between date_format(DATE_ADD('"""
            + rdate
            + """', INTERVAL - 100 DAY), '%Y%m%d') and '"""
            + rdate
            + """'
                AND a.rcity = '"""
            + rcity
            + """'
                AND a.rdate = '"""
            + rdate
            + """'
                AND a.rno = """
            + str(rno)
            + """

            union all

                SELECT  a.rank, a.gate, a.horse, b.rdate b_rdate, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason, b.rcity b_rcity, b.rno b_rno
                FROM exp011     a,
                    rec015     b
                where a.trainer = b.trainer 
                AND b.t_sort = '조교사'
                AND b.rdate between date_format(DATE_ADD('"""
            + rdate
            + """', INTERVAL - 100 DAY), '%Y%m%d') and '"""
            + rdate
            + """'
                AND a.rcity = '"""
            + rcity
            + """'
                AND a.rdate = '"""
            + rdate
            + """'
                AND a.rno = """
            + str(rno)
            + """ 
            ) a
            order by b_rdate desc
            ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_judged_horse(rcity, rdate, rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
              SELECT distinct a.rank, a.gate, a.horse, b.rdate, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason, a.rcity, a.rno
                FROM exp011     a,
                      rec015     b
                where a.horse = b.horse 
                AND b.rdate between date_format(DATE_ADD('"""
            + rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and '"""
            + rdate
            + """'
                AND a.rcity = '"""
            + rcity
            + """'
                AND a.rdate = '"""
            + rdate
            + """'
                AND a.rno = """
            + str(rno)
            + """
                AND b.rdate < '"""
            + rdate
            + """'

              order by a.rank, b.rdate desc
            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_judged(rcity, rdate, rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
              SELECT distinct a.rank, a.gate, a.horse, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason
                FROM rec011	a right outer join 
                    rec015	b on a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno and a.horse = b.horse
                where a.rcity = '"""
            + rcity
            + """'
                AND a.rdate = '"""
            + rdate
            + """'
                AND a.rno = """
            + str(rno)
            + """
              order by a.rank
            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        rec015 = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in rec015")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            SELECT judged
            FROM rec013
                where rcity = '"""
            + rcity
            + """'
                AND rdate = '"""
            + rdate
            + """'
                AND rno = """
            + str(rno)
            + """
            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        rec013 = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in rec013")

    return rec015, rec013


def get_pedigree(rcity, rdate, rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                SELECT a.gate, a.rank, a.r_rank, a.r_pop, a.horse, a.jockey, a.trainer, a.host,
                    tot_race,
                    tot_1st, 
                    tot_2nd, 
                    tot_3rd,
                    year_race,
                    year_1st,
                    year_2nd,
                    year_3rd,
                    ifnull(gear1, '') gear1, 
                    ifnull(gear2, '') gear2, 
                    blood1, 
                    blood2, 
                    treat1, 
                    treat2, 
                    a.prize_tot/1000, a.prize_year/1000, a.rating, a.i_cycle, reason, jockey_old, birthplace, h_sex, h_age, complex, complex5,
                    ( select concat( gear1, gear2) from The1.exp012   where horse = a.horse and rdate = ( select max(rdate) from The1.exp012 where rdate < a.rdate and horse = a.horse) )
                FROM exp011	a,
                    exp012 c
                WHERE a.rcity = c.rcity
                AND a.rdate = c.rdate
                AND a.rno = c.rno
                AND a.gate = c.gate
                AND a.rcity = '"""
            + rcity
            + """'
                AND a.rdate = '"""
            + rdate
            + """'
                AND a.rno = """
            + str(rno)
            + """
                order by a.rank, a.gate
            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_weeks(i_rdate, i_awardee):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select b.rcity, a.rcity rcity_in, b."""
            + i_awardee
            + """, rcnt, r1cnt, r2cnt, r3cnt, r4cnt, r5cnt, rmonth1, rmonth2, rmonth3, rdate1, rdate2, rdate3,
                  ( select year_per from """
            + i_awardee
            + """_w 
                    where wdate = ( select max(wdate) from """
            + i_awardee
            + """_w where wdate <= '"""
            + i_rdate
            + """' ) 
                      and """
            + i_awardee
            + """ = b."""
            + i_awardee
            + """ ) year_per
              from
              (
                select """
            + i_awardee
            + """ , sum(r_cnt) rcnt, sum(r1_cnt) r1cnt, sum(r2_cnt) r2cnt, sum(r3_cnt) r3cnt, sum(r4_cnt) r4cnt, sum(r5_cnt) r5cnt,
                              (select max(rcity) from """
            + i_awardee
            + """  where a."""
            + i_awardee
            + """ = """
            + i_awardee
            + """ ) rcity,
                              sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) rmonth1,
                              sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                              sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                      from award a
                      where rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                        and """
            + i_awardee
            + """ in (  select distinct """
            + i_awardee
            + """ from exp011 a where rdate in ( select distinct rdate from racing ) )
                      group by """
            + i_awardee
            + """
        	    ) a right outer join 
              (
                select rcity,"""
            + i_awardee
            + """, 
                        sum(if( rdate = '"""
            + i_rdate
            + """', 1, 0 )) rdate1, 
                        sum(if( rdate = DATE_FORMAT(CAST('"""
            + i_rdate
            + """' AS DATE) + INTERVAL 1 DAY,'%Y%m%d'), 1, 0 )) rdate2, 
                        sum(if( rdate = DATE_FORMAT(CAST('"""
            + i_rdate
            + """' AS DATE) + INTERVAL 2 DAY,'%Y%m%d'), 1, 0 )) rdate3
                  from exp011
                where rdate in ( select distinct rdate from racing )
                group by rcity, """
            + i_awardee
            + """
              ) b on a."""
            + i_awardee
            + """ = b."""
            + i_awardee
            + """
              order by rcity desc, rmonth1 + rmonth2 + rmonth3 desc
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        weeks = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return weeks


def get_race_center_detail_view(i_rdate, i_awardee):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity,"""
            + i_awardee
            + """ awardee, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey j_name, trainer t_name, host h_name, r_pop, distance, handycap,
                        cs1f, cg3f, cg2f, cg1f, complex, if ( i_prehandy = 0.0, 0, handycap - i_prehandy) i_pre
                from expect
                where rdate in ( select distinct rdate from racing )
                order by rcity, rdate, rno, rank, gate
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        weeks = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return weeks


def get_race(i_rdate, i_awardee):

    # exp010 Query
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity, rdate, rno, rday, rseq,distance, rcount, grade, dividing, rname, rcon1, rcon2, rtime, r1award/1000, r2award/1000, r3award/1000, r4award/1000, r5award/1000, sub1award/1000, sub2award/1000, sub3award/1000,
                ( select count(*) from rboard where a.rcity = rcity and a.rdate = rdate and a.rno = rno ) rcnt
                   -- 0
                from exp010 a 
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                order by rdate, rtime
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        racings = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in exp010 : 주별 경주현황")

    # race detail Query
    # try:
    #     cursor = connection.cursor()

    #     strSql = (
    #         """
    #             select rcity,"""
    #         + i_awardee
    #         + """ awardee, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey j_name, trainer t_name, host h_name, r_pop, distance, handycap, jt_per, s1f_rank, corners, g3f_rank, g1f_rank, alloc3r, jockey_old, reason
    #             from expect
    #             where rdate between date_format(DATE_ADD('"""
    #         + i_rdate
    #         + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
    #         + i_rdate
    #         + """', INTERVAL + 3 DAY), '%Y%m%d')
    #             and rno < 80
    #             and 1 <> 1
    #             order by rdate, rtime, gate
    #             ; """
    #     )

    #     r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
    #     race_detail = cursor.fetchall()

    #     connection.commit()
    #     connection.close()

    # except:
    #     connection.rollback()
    #     print("Failed selecting in expect : 경주별 Detail(약식)) ")

    return racings


def get_board_list(i_rdate, i_awardee):

    # 게시판 rboard Query
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity, rdate, rno, username, memo, board, rcnt, scnt, updated, created
                from rboard
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        board_list = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in expect : 경주별 게시판 리스트 ")

    return board_list


def get_training(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select gate, rank, horse, jockey, trainer,
                                              max(r1), CAST( max(d1) AS INTEGER ), 
                                              max(r2), CAST( max(d2) AS INTEGER ), 
                                              max(r3), CAST( max(d3) AS INTEGER ), 
                                              max(r4), CAST( max(d4) AS INTEGER ), 
                                              max(r5), CAST( max(d5) AS INTEGER ), 
                                              max(r6), CAST( max(d6) AS INTEGER ), 
                                              max(r7), CAST( max(d7) AS INTEGER ), 
                                              max(r8), CAST( max(d8) AS INTEGER ), 
                                              max(r9), CAST( max(d9) AS INTEGER ), 
                                              max(r10), CAST( max(d10) AS INTEGER ), 
                                              max(r11), CAST( max(d11) AS INTEGER ), 
                                              max(r12), CAST( max(d12) AS INTEGER ), 
                                              max(r13), CAST( max(d13) AS INTEGER ), 
                                              max(r14), CAST( max(d14) AS INTEGER )
                      from
                      (
                        select gate, b.rank, a.horse, b.jockey, b.trainer,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d1,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d2,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d3,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d4,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d5,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d6,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d7,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d8,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d9,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d10,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d11,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d12,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d13,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d14
                        from training a right outer join  ( select gate, rank, horse, jockey, trainer from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.horse = b.horse
                        and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                      ) a
                      group by gate, rank, horse, jockey, trainer
                      order by rank, gate
                        ;"""
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return training


def get_train(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select gate, rank, horse, jockey, trainer,
                                              max(r1), max(d1), max(c1), max(s1) , 
                                              max(r2), max(d2), max(c2), max(s2) , 
                                              max(r3), max(d3), max(c3), max(s3) , 
                                              max(r4), max(d4), max(c4), max(s4) , 
                                              max(r5), max(d5), max(c5), max(s5) , 
                                              max(r6), max(d6), max(c6), max(s6) , 
                                              max(r7), max(d7), max(c7), max(s7) , 
                                              max(r8), max(d8), max(c8), max(s8) , 
                                              max(r9), max(d9), max(c9), max(s9) , 
                                              max(r10), max(d10), max(c10), max(s10) , 
                                              max(r11), max(d11), max(c11), max(s11) , 
                                              max(r12), max(d12), max(c12), max(s12) , 
                                              max(r13), max(d13), max(c13), max(s13) , 
                                              max(r14), max(d14), max(c14), max(s14) 
                      from
                      (
                        select gate, b.rank, a.horse, b.jockey, b.trainer,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,

                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,

                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
                        from train a right outer join  ( select gate, rank, horse, jockey, trainer from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.horse = b.horse
                        and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                      ) a
                      group by gate, rank, horse, jockey, trainer
                      order by rank, gate
                        ;"""
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return training


def get_train_audit(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select gate, rank, r_rank, b.horse, jockey, trainer, s_audit, rider, rider_k, judge, tdate
                                              
                      from
                      (
                          select '출발조교'		s_audit,
                                horse		horse, 
                                rider		rider, 
                                rider_k		rider_k,
                                judge		judge, 
                                tdate		tdate
                            from start_train
                          where tdate between DATE_FORMAT( subdate( str_to_date( '"""
            + i_rdate
            + """', '%Y%m%d' ) , 100 ),'%Y%m%d')  and '"""
            + i_rdate
            + """' 
                          union all
                          select '발주심사'		s_audit,
                                horse		horse, 
                                rider		rider, 
                                rider_k		rider_k,
                                judge		judge, 
                                rdate		tdate
                            from start_audit
                          where rdate between DATE_FORMAT( subdate( str_to_date( '"""
            + i_rdate
            + """', '%Y%m%d' ) , 100 ),'%Y%m%d')  and '"""
            + i_rdate
            + """' 
                        ) a right outer join  ( select gate, rank, r_rank, horse, jockey, trainer from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.horse = b.horse
                      order by rank, tdate desc
                        ;"""
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Train audit")

    return training


def get_train_horse(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight, distance, grade, rating, dividing, i_cycle,
                        reason, jockey_old, birthplace, h_sex, h_age, complex, complex5,
                                            max(r1), max(d1), max(c1), max(s1) , 
                                            max(r2), max(d2), max(c2), max(s2) , 
                                            max(r3), max(d3), max(c3), max(s3) , 
                                            max(r4), max(d4), max(c4), max(s4) , 
                                            max(r5), max(d5), max(c5), max(s5) , 
                                            max(r6), max(d6), max(c6), max(s6) , 
                                            max(r7), max(d7), max(c7), max(s7) , 
                                            max(r8), max(d8), max(c8), max(s8) , 
                                            max(r9), max(d9), max(c9), max(s9) , 
                                            max(r10), max(d10), max(c10), max(s10) , 
                                            max(r11), max(d11), max(c11), max(s11) , 
                                            max(r12), max(d12), max(c12), max(s12) , 
                                            max(r13), max(d13), max(c13), max(s13) , 
                                            max(r14), max(d14), max(c14), max(s14) ,
                    -- ( select count(*) from train aa where aa.horse = a.horse and aa.tdate between date_format(DATE_ADD(a.rdate, INTERVAL - 14 DAY), '%Y%m%d') and a.rdate and aa.rider = jockey ) laps
                    ( select sum(laps) from swim aa where aa.horse = a.horse and aa.tdate between date_format(DATE_ADD(a.rdate, INTERVAL - 14 DAY), '%Y%m%d') and a.rdate ) swims
                    from
                    (
                        select rdate, gate, b.rank, r_rank, r_pop, a.horse, b.jockey, b.trainer, b.rcity, rno, j_per, t_per, jt_per,h_weight, distance, b.grade, rating, dividing, i_cycle,
                        reason, jockey_old, birthplace, h_sex, h_age, complex, complex5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,

                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,

                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
                        from train a ,
                            ( select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, 
                                    j_per, t_per, jt_per, h_weight, distance, grade, rating, dividing, i_cycle, reason, jockey_old, birthplace, h_sex, h_age, complex, complex5
                                from expect  
                              where rdate = '"""
            + i_rdate
            + """' 
                              and horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) ) b 
                        where a.horse = b.horse
                        and tdate between date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d') and rdate
                        -- and 1<>1
                      ) a
                      group by rdate, gate, rank, r_rank, r_pop, horse, jockey, trainer
                      order by rdate desc, rank, gate
                        ;"""
        )
        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in Train Horse")

    return result

def get_train_horse1(i_rdate, i_hname):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight, distance, grade, rating, dividing, i_cycle,
                        reason, jockey_old, birthplace, h_sex, h_age, complex, complex5,
                                            max(r1), max(d1), max(c1), max(s1) , 
                                            max(r2), max(d2), max(c2), max(s2) , 
                                            max(r3), max(d3), max(c3), max(s3) , 
                                            max(r4), max(d4), max(c4), max(s4) , 
                                            max(r5), max(d5), max(c5), max(s5) , 
                                            max(r6), max(d6), max(c6), max(s6) , 
                                            max(r7), max(d7), max(c7), max(s7) , 
                                            max(r8), max(d8), max(c8), max(s8) , 
                                            max(r9), max(d9), max(c9), max(s9) , 
                                            max(r10), max(d10), max(c10), max(s10) , 
                                            max(r11), max(d11), max(c11), max(s11) , 
                                            max(r12), max(d12), max(c12), max(s12) , 
                                            max(r13), max(d13), max(c13), max(s13) , 
                                            max(r14), max(d14), max(c14), max(s14) ,
                    -- ( select count(*) from train aa where aa.horse = a.horse and aa.tdate between date_format(DATE_ADD(a.rdate, INTERVAL - 14 DAY), '%Y%m%d') and a.rdate and aa.rider = jockey ) laps
                    ( select sum(laps) from swim aa where aa.horse = a.horse and aa.tdate between date_format(DATE_ADD(a.rdate, INTERVAL - 14 DAY), '%Y%m%d') and a.rdate ) swims
                    from
                    (
                        select rdate, gate, b.rank, r_rank, r_pop, a.horse, b.jockey, b.trainer, b.rcity, rno, j_per, t_per, jt_per,h_weight, distance, b.grade, rating, dividing, i_cycle,
                        reason, jockey_old, birthplace, h_sex, h_age, complex, complex5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,

                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,

                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
                        from train a ,
                            ( select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, 
                                    j_per, t_per, jt_per, h_weight, distance, grade, rating, dividing, i_cycle, reason, jockey_old, birthplace, h_sex, h_age, complex, complex5
                                from expect  
                              where horse = '""" + i_hname + """' ) b 
                        where a.horse = b.horse
                        and tdate between date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d') and rdate
                        -- and 1<>1
                      ) a
                      group by rdate, gate, rank, r_rank, r_pop, horse, jockey, trainer
                      order by rdate desc, rank, gate
                        ;"""
        )
        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in Train Horse")

    return result


def get_train_horse_care(
    i_rcity, i_rdate, i_rno
):  # 기수가 4주간 조교 회수가 많은 경주마 check
    try:
        cursor = connection.cursor()

        strSql = (
            """ select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight, distance, grade, rating, dividing,
                                            max(r1), max(d1), max(c1), max(s1) , 
                                            max(r2), max(d2), max(c2), max(s2) , 
                                            max(r3), max(d3), max(c3), max(s3) , 
                                            max(r4), max(d4), max(c4), max(s4) , 
                                            max(r5), max(d5), max(c5), max(s5) , 
                                            max(r6), max(d6), max(c6), max(s6) , 
                                            max(r7), max(d7), max(c7), max(s7) , 
                                            max(r8), max(d8), max(c8), max(s8) , 
                                            max(r9), max(d9), max(c9), max(s9) , 
                                            max(r10), max(d10), max(c10), max(s10) , 
                                            max(r11), max(d11), max(c11), max(s11) , 
                                            max(r12), max(d12), max(c12), max(s12) , 
                                            max(r13), max(d13), max(c13), max(s13) , 
                                            max(r14), max(d14), max(c14), max(s14) ,
                                            ( select sum(laps) from swim aa where aa.horse = a.horse and aa.tdate between date_format(DATE_ADD(a.rdate, INTERVAL - 14 DAY), '%Y%m%d') and a.rdate ) laps
                    from
                    (
                        select rdate, gate, b.rank, r_rank, r_pop, a.horse, b.jockey, b.trainer, b.rcity, rno, j_per, t_per, jt_per,h_weight, distance, b.grade, rating, dividing,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,

                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,

                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
                          if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
                        from train a ,
                            ( select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight, distance, grade, rating, dividing
                                from expect  
                              where horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) ) b 
                        where a.horse = b.horse
                        and tdate between date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d') and rdate
                      ) a
                      group by rdate, gate, rank, r_rank, r_pop, horse, jockey, trainer
                      order by rdate desc, rank, gate
                        ;"""
        )
        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result


def trend_title(i_rdate):

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            SELECT date_format(DATE_ADD(rdate, INTERVAL - 1 DAY),'%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%m.%d'),
                date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%m.%d')
                FROM exp010 
                where rdate = '"""
            + i_rdate
            + """' and rno = 1
            ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        trend_title = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in train Trend Title")
    # result = dict[result]
    # print(trend_title)

    return trend_title


# def get_train_horse(i_rcity, i_rdate, i_rno):
#     try:
#         cursor = connection.cursor()

#         strSql = """ select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight,
#                                             max(r1), max(d1), max(c1), max(s1) ,
#                                             max(r2), max(d2), max(c2), max(s2) ,
#                                             max(r3), max(d3), max(c3), max(s3) ,
#                                             max(r4), max(d4), max(c4), max(s4) ,
#                                             max(r5), max(d5), max(c5), max(s5) ,
#                                             max(r6), max(d6), max(c6), max(s6) ,
#                                             max(r7), max(d7), max(c7), max(s7) ,
#                                             max(r8), max(d8), max(c8), max(s8) ,
#                                             max(r9), max(d9), max(c9), max(s9) ,
#                                             max(r10), max(d10), max(c10), max(s10) ,
#                                             max(r11), max(d11), max(c11), max(s11) ,
#                                             max(r12), max(d12), max(c12), max(s12) ,
#                                             max(r13), max(d13), max(c13), max(s13) ,
#                                             max(r14), max(d14), max(c14), max(s14)
#                     from
#                     (
#                         select rdate, gate, b.rank, r_rank, r_pop, a.horse, b.jockey, b.trainer, b.rcity, rno, j_per, t_per, jt_per,h_weight,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,

#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,

#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,

#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
#                           if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
#                         from train a ,
#                             ( select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight
#                                 from exp011
#                               where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) ) b
#                         where a.horse = b.horse
#                         and tdate between date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d') and rdate
#                       ) a
#                       group by rdate, gate, rank, r_rank, r_pop, horse, jockey, trainer
#                       order by rdate desc, rank, gate
#                         ;"""

#         r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
#         result = cursor.fetchall()

#         connection.commit()
#         connection.close()

#     except:
#         connection.rollback()
#         print("Failed selecting in BookListView")

#     return result


def get_swim_horse(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight,
                                            max(s1) , 
                                            max(s2) , 
                                            max(s3) , 
                                            max(s4) , 
                                            max(s5) , 
                                            max(s6) , 
                                            max(s7) , 
                                            max(s8) , 
                                            max(s9) , 
                                            max(s10) , 
                                            max(s11) , 
                                            max(s12) , 
                                            max(s13) , 
                                            max(s14) 
                    from
                    (
                        select rdate, gate, b.rank, r_rank, r_pop, a.horse, b.jockey, b.trainer, b.rcity, rno, j_per, t_per, jt_per,h_weight,

                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 1 DAY), '%Y%m%d'), laps, 0 ) s1,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 2 DAY), '%Y%m%d'), laps, 0 ) s2,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 3 DAY), '%Y%m%d'), laps, 0 ) s3,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 4 DAY), '%Y%m%d'), laps, 0 ) s4,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 5 DAY), '%Y%m%d'), laps, 0 ) s5,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 6 DAY), '%Y%m%d'), laps, 0 ) s6,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 7 DAY), '%Y%m%d'), laps, 0 ) s7,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 8 DAY), '%Y%m%d'), laps, 0 ) s8,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 9 DAY), '%Y%m%d'), laps, 0 ) s9,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 10 DAY), '%Y%m%d'), laps, 0 ) s10,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 11 DAY), '%Y%m%d'), laps, 0 ) s11,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d'), laps, 0 ) s12,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 13 DAY), '%Y%m%d'), laps, 0 ) s13,
                            if( tdate = date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d'), laps, 0 ) s14
                        from swim a ,
                            ( select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight
                                from exp011 
                                where horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) ) b 
                        where a.horse = b.horse
                        and tdate between date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d') and rdate
                        ) a
                        group by rdate, gate, rank, r_rank, r_pop, horse, jockey, trainer
                        order by rdate desc, rank, gate
                        ;"""
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result


# def get_treat_horse(i_rcity, i_rdate, i_rno):
#     try:
#         cursor = connection.cursor()

#         strSql = """
#                     select distinct horse, tdate, team, hospital, disease
#                     from treat a
#                     where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """ )
#                     and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 60 DAY), '%Y%m%d') and '""" + i_rdate + """'
#                     order by  a.horse, a.tdate desc
#             ;"""

#         print(strSql)
#         r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
#         result = cursor.fetchall()

#         connection.commit()
#         connection.close()

#     except:
#         connection.rollback()
#         print("Failed selecting in 마필병력 히스토리 ")

#     return result


def get_treat_horse(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                    select horse, tdate, max(disease) disease, max(laps) laps,  max(t_time) t_time, max(canter) canter,  max(strong) strong, 
                            audit, max(rider) rider, max(judge) judge,
                            weekday(tdate) days
                    from
                    (
                        select distinct  horse, tdate, if( length(disease) > 2, trim(disease), trim(hospital) ) disease, '' laps,  '' t_time, '' canter,  '' strong, '' audit, '' rider, '' judge
                        from treat 
                        where horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """ )
                        and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 99 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                        union all
                        select horse, tdate, '', laps, '', '', '', '', '', ''
                        from swim 
                        where horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """ )
                        and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 99 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                        union all
                        select horse, tdate, '', '', t_time, canter, strong, '', rider, ''
                        from train 
                        where horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """ )
                        and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 99 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                        union all
                        select horse, tdate, '', '', '', '', '', '출발', rider, judge
                        from start_train 
                        where horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """ )
                        and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 99 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                        union all
                        select horse, rdate, '', '', '', '', '', '발주', rider, judge
                        from start_audit 
                        where horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """ )
                        and rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 99 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                        union all
                        select horse, rdate, concat( mid(grade,1,2), ' ', 'Race: ', convert(rcount, char),'두, 인기도:', convert(r_pop, char)), '', '', '', '', '경주', jockey, 
                                                concat( convert(r_rank, char), '  ﹆  ', convert(rank, char))
                        from expect
                        where horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """ )
                        and rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 99 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    ) a
                    group by horse, tdate, audit
                    order by tdate desc
                    
            ;"""
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 마필병력 히스토리 ")

    return result


def get_track_record(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select f_t2s(avg(con_avg))
            from rec010_track
            where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
            and ( rcity, distance, grade ) in ( select rcity, distance, grade from exp010 
                                                    where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """ )
            ;"""
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 등급별 거리별 평균기록 ")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select f_t2s(avg(con_avg))
            from rec010_track
            where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
            and ( rcity, distance, grade ) in ( select rcity, distance, grade from exp010 
                                                    where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """ )
            ;"""
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # print(result)

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 등급별 거리별 평균기록 ")

    return result


def get_award(i_rdate, i_awardee):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select """
            + i_awardee
            + """, count(0) rcnt, (select max(rcity) from """
            + i_awardee
            + """  where a."""
            + i_awardee
            + """ = """
            + i_awardee
            + """ ) rcity,
                            sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a
                    where rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                    and """
            + i_awardee
            + """ in ( select """
            + i_awardee
            + """ from exp011 where rdate = '"""
            + i_rdate
            + """')
                    group by """
            + i_awardee
            + """
                    order by sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) +
                             sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) +
                             sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) desc
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        awards = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return awards


def get_award_race(i_rcity, i_rdate, i_rno, i_awardee):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
              select gate, rank, max(jockey), sum(j_rcnt), sum(j_rmonth1), sum(j_rmonth2), sum(j_rmonth3),
                          max(trainer), sum(t_rcnt), sum(t_rmonth1), sum(t_rmonth2), sum(t_rmonth3), 
                          max(host), sum(h_rcnt), sum(h_rmonth1), sum(h_rmonth2), sum(h_rmonth3)
                from
                  (
                    select gate, rank, b.jockey, count(0) j_rcnt, 
                            sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) j_rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) j_rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) j_rmonth3,
                            '' trainer, 0 t_rcnt, 0 t_rmonth1, 0 t_rmonth2, 0 t_rmonth3,
                            '' host, 0 h_rcnt, 0 h_rmonth1, 0 h_rmonth2, 0 h_rmonth3
                    from award a right outer join  ( select gate, rank, jockey from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.jockey = b.jockey
                    and rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                    group by jockey, gate, rank
                    
                    union all

                    select gate, rank, '', 0, 0, 0, 0,
                            b.trainer, count(0) rcnt, 
                            sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3,
                            '', 0, 0, 0, 0
                    from award a right outer join  ( select gate, rank, trainer from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.trainer = b.trainer
                    and rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                    group by trainer, gate, rank

                    union all

                    select  gate, rank, '', 0, 0, 0, 0, '', 0, 0, 0, 0, b.host, count(0) rcnt, 
                            sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, rank, host from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.host = b.host
                    and rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                    group by host, gate, rank
                  ) a
                  group by gate, rank
                  order by rank, gate
                ; """
        )

        strSql1 = (
            """ 
              select rflag, gate, jockey, rcnt, rcity, rmonth1, rmonth2, rmonth3
                from
                  (
                    select 1 rflag, gate, b.jockey, count(0) rcnt, (select max(rcity) from jockey  where a.jockey = jockey ) rcity,
                            sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, jockey from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.jockey = b.jockey
                    and rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                    group by jockey, gate
                    
                    union all

                    select 2 rflag, gate, b.trainer, count(0) rcnt, (select max(rcity) from trainer  where a.trainer = trainer ) rcity,
                            sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, trainer from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.trainer = b.trainer
                    and rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                    group by trainer, gate

                    union all

                    select 3 rflag,  gate, b.host, count(0) rcnt, (select max(rcity) from host  where a.host = host ) rcity,
                            sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, host from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """) b on a.host = b.host
                    and rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                    group by host, gate
                  ) a
                  order by gate, rflag
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        awards = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return awards


def get_last2weeks(i_rdate, i_awardee, i_friday):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select aa.rcity, aa.rcity_in, aa."""
            + i_awardee
            + """, rcnt, r1cnt, r2cnt, r3cnt, r4cnt, r5cnt, rmonth1, rmonth2, rmonth3, rdate1, rdate2, rdate3,
                lw1_fri1, lw1_fri2, lw1_fri3, lw1_fri,
                lw1_sat1, lw1_sat2, lw1_sat3, lw1_sat,
                lw1_sun1, lw1_sun2, lw1_sun3, lw1_sun,
                lw2_fri1, lw2_fri2, lw2_fri3, lw2_fri,
                lw2_sat1, lw2_sat2, lw2_sat3, lw2_sat,
                lw2_sun1, lw2_sun2, lw2_sun3, lw2_sun, award,
                
                ( select year_1st from """
            + i_awardee
            + """_w 
                    where wdate = ( select max(wdate) from """
            + i_awardee
            + """_w where wdate < '"""
            + i_rdate
            + """' ) 
                      and """
            + i_awardee
            + """ = aa."""
            + i_awardee
            + """ ) year_per,

                  ( select count(*) from rec011
                    where rdate between '"""
            + i_rdate[0:4]
            + """0101'  and '"""
            + i_rdate
            + """%' 
                    and rank = 1
                    and alloc1r > 0 
                    and """
            + i_awardee
            + """ = aa."""
            + i_awardee
            + """ ) wcnt
              from
              (
                select b.rcity, a.rcity rcity_in, b."""
            + i_awardee
            + """, rcnt, r1cnt, r2cnt, r3cnt, r4cnt, r5cnt, rmonth1, rmonth2, rmonth3, rdate1, rdate2, rdate3
                  from
                    (
                      select """
            + i_awardee
            + """ , sum(r_cnt) rcnt, sum(r1_cnt) r1cnt, sum(r2_cnt) r2cnt, sum(r3_cnt) r3cnt, sum(r4_cnt) r4cnt, sum(r5_cnt) r5cnt,
                                    (select max(rcity) from """
            + i_awardee
            + """  where a."""
            + i_awardee
            + """ = """
            + i_awardee
            + """ ) rcity,
                                    sum( if( rmonth = substr( '"""
            + i_rdate
            + """', 1, 6), award, 0 )) rmonth1,
                                    sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                                    sum( if( rmonth = substr( date_format( DATE_ADD( '"""
            + i_rdate
            + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                            from award a
                            where rmonth between substr(date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('"""
            + i_rdate
            + """', 1, 6)
                              and """
            + i_awardee
            + """ in (  select distinct """
            + i_awardee
            + """ from exp011 a where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d') )
                            group by """
            + i_awardee
            + """
                    ) a right outer join 
                    (
                      select rcity,"""
            + i_awardee
            + """, 
                              sum(if( rday = '금', 1, 0 )) rdate1, 
                              sum(if( rday = '토', 1, 0 )) rdate2, 
                              sum(if( rday = '일', 1, 0 )) rdate3
                              
                        from expect
                      where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                      group by rcity, """
            + i_awardee
            + """
                    ) b on a."""
            + i_awardee
            + """ = b."""
            + i_awardee
            + """
                ) aa left outer join 
                (
                select """
            + i_awardee
            + """, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 7 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw1_fri1, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 7 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw1_fri2, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 7 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw1_fri3, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 7 DAY,  '%Y%m%d'), 1, 0)) lw1_fri, 

                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 6 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw1_sat1, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 6 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw1_sat2, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 6 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw1_sat3, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 6 DAY,  '%Y%m%d'), 1, 0)) lw1_sat, 

                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 5 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw1_sun1, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 5 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw1_sun2, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 5 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw1_sun3, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 5 DAY,  '%Y%m%d'), 1, 0)) lw1_sun, 

                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw2_fri1, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw2_fri2, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw2_fri3, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d'), 1, 0)) lw2_fri, 

                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 13 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw2_sat1, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 13 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw2_sat2, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 13 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw2_sat3, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 13 DAY,  '%Y%m%d'), 1, 0)) lw2_sat, 

                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 12 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw2_sun1, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 12 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw2_sun2, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 12 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw2_sun3, 
                sum( if( rdate = DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 12 DAY,  '%Y%m%d'), 1, 0)) lw2_sun, 
                    
                    sum( if(a.rank = 1, r1award + sub1award, 0) +
                    if(a.rank = 2, r2award + sub2award, 0) +
                    if(a.rank = 3, r3award + sub3award, 0) +
                    if(a.rank = 4, r4award, 0) +
                    if(a.rank = 5, r5award, 0) ) award
                    from record a
                where rdate between DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d') and  DATE_FORMAT(CAST('"""
            + i_friday
            + """' AS DATE) - INTERVAL 1 DAY,  '%Y%m%d')
                    and grade != '주행검사'
                group by """
            + i_awardee
            + """
                ) c on aa."""
            + i_awardee
            + """ = c."""
            + i_awardee
            + """
                order by rcity desc, wcnt desc, year_per desc
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        weeks = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 상금 수득 현황")

    return weeks


# 기승가능중량 or 마방 팀번호 ==> AwardStatusJockey
def get_last2weeks_loadin(i_rdate):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                    select 'J' flag, jockey, tot_1st, cast(load_in as decimal) 
                    from jockey_w 
                    where wdate = ( select max(wdate) from jockey_w where wdate < '"""
            + i_rdate
            + """' ) 
                    union all 
                    select 'T', trainer, tot_1st, team
                    from trainer_w 
                    where wdate = ( select max(wdate) from trainer_w where wdate < '"""
            + i_rdate
            + """' ) 
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        results = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 기승가능중량")

    return results


# 기승가능중량 => PredictionRace
def get_loadin(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select jockey, cast(load_in as decimal) 
            from jockey_w 
            where wdate = ( select max(wdate) from jockey_w where wdate < '"""
            + i_rdate
            + """' ) 

            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        loadin = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 기승가능중량")

    return loadin


def get_disease(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = """ 
            select horse, max(tdate), count(*)
            from
            (
            select horse, tdate, max(disease) 
            from treat
            where horse in (
                select horse
                from exp011
                where rdate = '""" + i_rdate + """'
                and rcity = '""" + i_rcity + """'
                and rno = """ + str(i_rno) + """
            )
            and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 99 DAY), '%Y%m%d') and '""" + i_rdate + """'
            and ( disease like '%절염%' or disease like '%골막염%' or disease like '%대염%' )
            -- and ( disease like '%회복%'  )
            group by horse, tdate
            ) a
            group by horse
            
        ; """

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        disease = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 기승가능중량")

    return disease


def get_status_training(i_rdate):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select rcity, rdate, rno, rday, gate, rank, r_rank, r_pop, horse, trainer, jockey, jt_per, handycap,
                                        max(r1), CAST( max(d1) AS INTEGER ), 
                                        max(r2), CAST( max(d2) AS INTEGER ), 
                                        max(r3), CAST( max(d3) AS INTEGER ), 
                                        max(r4), CAST( max(d4) AS INTEGER ), 
                                        max(r5), CAST( max(d5) AS INTEGER ), 
                                        max(r6), CAST( max(d6) AS INTEGER ), 
                                        max(r7), CAST( max(d7) AS INTEGER ), 
                                        max(r8), CAST( max(d8) AS INTEGER ), 
                                        max(r9), CAST( max(d9) AS INTEGER ), 
                                        max(r10), CAST( max(d10) AS INTEGER ), 
                                        max(r11), CAST( max(d11) AS INTEGER ), 
                                        max(r12), CAST( max(d12) AS INTEGER ), 
                                        max(r13), CAST( max(d13) AS INTEGER ), 
                                        max(r14), CAST( max(d14) AS INTEGER )
                from
                (
                        select b.rcity, b.rdate, b.rday, b.rno, b.gate, b.rank, b.r_rank, b.r_pop, a.horse, b.trainer, b.jockey, b.jt_per, b.handycap,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d1,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d2,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d3,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d4,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d5,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d6,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d7,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d8,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d9,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d10,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d11,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d12,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d13,
                          if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d14
                        from training a right outer join  
                        ( 
                          select rcity, rdate, rday, rno, trainer, jockey, jt_per, gate, rank, r_rank, r_pop, horse, handycap
                            from expect 
                          where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                        ) b on a.horse = b.horse
                        and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                      ) a
                      group by rcity, rdate, rday, rno, gate, rank, horse
                      order by rcity, rdate, rday, rno, gate
                        ;"""
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return training


def get_status_train(i_rdate):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select rcity, rdate, rno, rday, gate, rank, r_rank, r_pop, horse, trainer, jockey, jt_per, handycap, j_per, t_per, h_weight, distance, grade, rating, dividing, host, i_prehandy, jockey_old, reason,
                                            max(r1), max(d1), max(c1), max(s1), 
                                            max(r2), max(d2), max(c2), max(s2), 
                                            max(r3), max(d3), max(c3), max(s3), 
                                            max(r4), max(d4), max(c4), max(s4), 
                                            max(r5), max(d5), max(c5), max(s5), 
                                            max(r6), max(d6), max(c6), max(s6), 
                                            max(r7), max(d7), max(c7), max(s7), 
                                            max(r8), max(d8), max(c8), max(s8), 
                                            max(r9), max(d9), max(c9), max(s9), 
                                            max(r10), max(d10), max(c10), max(s10), 
                                            max(r11), max(d11), max(c11), max(s11), 
                                            max(r12), max(d12), max(c12), max(s12), 
                                            max(r13), max(d13), max(c13), max(s13), 
                                            max(r14), max(d14), max(c14), max(s14),
                                            ( select sum(laps) from swim aa where aa.horse = a.horse and aa.tdate between date_format(DATE_ADD(a.rdate, INTERVAL - 14 DAY), '%Y%m%d') and a.rdate ) laps
                from
                (
                    select b.rcity, b.rdate, b.rday, b.rno, b.gate, b.rank, b.r_rank, b.r_pop, a.horse, b.trainer, b.jockey, b.jt_per, b.handycap, b.j_per, b.t_per, b.h_weight,
                        b.distance, b.grade, b.rating, b.dividing, b.host, b.i_prehandy, jockey_old, reason,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
                    from train a right outer join  
                    ( 
                        select rcity, rdate, rday, rno, trainer, jockey, jt_per, gate, rank, r_rank, r_pop, horse, handycap, j_per, t_per, h_weight, distance, grade, rating, dividing, host, i_prehandy,
                            jockey_old, reason
                        from expect 
                        where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                    ) b on a.horse = b.horse
                    and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                ) a
                group by rcity, rdate, rday, rno, gate, rank, horse
                order by rcity, rdate, rday, rno, gate
            ;"""
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return training


# 기수, 조교사 주별 출주마 조교현황
def get_training_awardee(i_rdate, i_awardee, i_name):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select rcity, rdate, rno, rday, gate, rank, r_rank, r_pop, horse, trainer, jockey, jt_per, handycap, j_per, t_per, h_weight, distance, grade, rating, dividing, host, i_prehandy, jockey_old, reason,
                        birthplace, h_sex, h_age, i_cycle,
                                            max(r1), max(d1), max(c1), max(s1), 
                                            max(r2), max(d2), max(c2), max(s2), 
                                            max(r3), max(d3), max(c3), max(s3), 
                                            max(r4), max(d4), max(c4), max(s4), 
                                            max(r5), max(d5), max(c5), max(s5), 
                                            max(r6), max(d6), max(c6), max(s6), 
                                            max(r7), max(d7), max(c7), max(s7), 
                                            max(r8), max(d8), max(c8), max(s8), 
                                            max(r9), max(d9), max(c9), max(s9), 
                                            max(r10), max(d10), max(c10), max(s10), 
                                            max(r11), max(d11), max(c11), max(s11), 
                                            max(r12), max(d12), max(c12), max(s12), 
                                            max(r13), max(d13), max(c13), max(s13), 
                                            max(r14), max(d14), max(c14), max(s14),
                                        ( select sum(laps) from swim aa where aa.horse = a.horse and aa.tdate between date_format(DATE_ADD(a.rdate, INTERVAL - 14 DAY), '%Y%m%d') and a.rdate ) laps
                from
                (
                    select b.rcity, b.rdate, b.rday, b.rno, b.gate, b.rank, b.r_rank, b.r_pop, a.horse, b.trainer, b.jockey, b.jt_per, b.handycap, b.j_per, b.t_per, b.h_weight,
                        b.distance, b.grade, b.rating, b.dividing, b.host, b.i_prehandy, jockey_old, reason, birthplace, h_sex, h_age, i_cycle,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
                        if( tdate = date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
                    from train a right outer join  
                    ( 
                        select rcity, rdate, rday, rno, trainer, jockey, jt_per, gate, rank, r_rank, r_pop, horse, handycap, j_per, t_per, h_weight, distance, grade, rating, dividing, host, i_prehandy,
                            jockey_old, reason, birthplace, h_sex, h_age, i_cycle
                        from expect 
                        where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                        and """
            + i_awardee
            + """ = '"""
            + i_name
            + """'
                    ) b on a.horse = b.horse
                    and tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 14 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                ) a
                group by rcity, rdate, rday, rno, gate, rank, horse
                order by rcity, rdate, rday, rno, gate
            ;"""
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in training")

    return training


# race related Query
def get_race_related(i_rcity, i_rdate, i_rno):

    try:
        cursor = connection.cursor()

        strSql = (
            """
            select b.rank, b.gate, b.r_rank, b.jockey, b.trainer, b.host, b.horse, b.rating, b.r_pop, b.complex, b.complex5, rcnt, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, rrcnt, rr1, rr2, rr3, rr4, rr5, rr6, rr7, rr8, rr9, rr10, rr11, rr12
            from
            (
                select jockey, count(*) rcnt, 
                        sum(if(rank = 1, 1, 0)) r1, 
                        sum(if(rank = 2, 1, 0)) r2, 
                        sum(if(rank = 3, 1, 0)) r3,
                        sum(if(rank = 4, 1, 0)) r4,
                        sum(if(rank = 5, 1, 0)) r5,
                        sum(if(rank = 6, 1, 0)) r6,
                        sum(if(rank = 7, 1, 0)) r7,
                        sum(if(rank = 8, 1, 0)) r8,
                        sum(if(rank = 9, 1, 0)) r9,
                        sum(if(rank = 10, 1, 0)) r10,
                        sum(if(rank = 11, 1, 0)) r11,
                        sum(if(rank >= 12, 1, 0)) r12,
                        
                        sum(if(r_rank > 0, 1, 0 )) rrcnt,
                        sum(if(r_rank = 1, 1, 0)) rr1, 
                        sum(if(r_rank = 2, 1, 0)) rr2, 
                        sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(r_rank = 4, 1, 0)) rr4,
                        sum(if(r_rank = 5, 1, 0)) rr5,
                        sum(if(r_rank = 6, 1, 0)) rr6,
                        sum(if(r_rank = 7, 1, 0)) rr7,
                        sum(if(r_rank = 8, 1, 0)) rr8,
                        sum(if(r_rank = 9, 1, 0)) rr9,
                        sum(if(r_rank = 10, 1, 0)) rr10,
                        sum(if(r_rank = 11, 1, 0)) rr11,
                        sum(if(r_rank >= 12, 1, 0)) rr12
                from expect a
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                group by jockey
                
            ) a right outer join  exp011 b  on a.jockey = b.jockey
            where b.rcity =  '"""
            + i_rcity
            + """'
                    and b.rdate = '"""
            + i_rdate
            + """'
                    and b.rno =  """
            + str(i_rno)
            + """
                    order by b.rank, b.gate
                ; """
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        award_j = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in Award_j")

    try:
        cursor = connection.cursor()

        strSql = (
            """
            select b.rank, b.gate, b.r_rank, b.jockey, b.trainer, b.host, b.horse, b.rating, b.r_pop, b.complex, b.complex5, rcnt, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, rrcnt, rr1, rr2, rr3, rr4, rr5, rr6, rr7, rr8, rr9, rr10, rr11, rr12
            from
            (
                select trainer, count(*) rcnt, 
                        sum(if(rank = 1, 1, 0)) r1, 
                        sum(if(rank = 2, 1, 0)) r2, 
                        sum(if(rank = 3, 1, 0)) r3,
                        sum(if(rank = 4, 1, 0)) r4,
                        sum(if(rank = 5, 1, 0)) r5,
                        sum(if(rank = 6, 1, 0)) r6,
                        sum(if(rank = 7, 1, 0)) r7,
                        sum(if(rank = 8, 1, 0)) r8,
                        sum(if(rank = 9, 1, 0)) r9,
                        sum(if(rank = 10, 1, 0)) r10,
                        sum(if(rank = 11, 1, 0)) r11,
                        sum(if(rank >= 12, 1, 0)) r12,
                        
                        sum(if(r_rank > 0, 1, 0 )) rrcnt,
                        sum(if(r_rank = 1, 1, 0)) rr1, 
                        sum(if(r_rank = 2, 1, 0)) rr2, 
                        sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(r_rank = 4, 1, 0)) rr4,
                        sum(if(r_rank = 5, 1, 0)) rr5,
                        sum(if(r_rank = 6, 1, 0)) rr6,
                        sum(if(r_rank = 7, 1, 0)) rr7,
                        sum(if(r_rank = 8, 1, 0)) rr8,
                        sum(if(r_rank = 9, 1, 0)) rr9,
                        sum(if(r_rank = 10, 1, 0)) rr10,
                        sum(if(r_rank = 11, 1, 0)) rr11,
                        sum(if(r_rank >= 12, 1, 0)) rr12
                from expect a
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                group by trainer
                
            ) a right outer join  exp011 b  on a.trainer = b.trainer
            where b.rcity =  '"""
            + i_rcity
            + """'
                    and b.rdate = '"""
            + i_rdate
            + """'
                    and b.rno =  """
            + str(i_rno)
            + """
                    order by b.rank, b.gate
                ; """
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        award_t = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in Award_t")

    try:
        cursor = connection.cursor()

        strSql = (
            """
            select b.rank, b.gate, b.r_rank, b.jockey, b.trainer, b.host, b.horse, b.rating, b.r_pop, b.complex, b.complex5, rcnt, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, rrcnt, rr1, rr2, rr3, rr4, rr5, rr6, rr7, rr8, rr9, rr10, rr11, rr12
            from
            (
                select host, count(*) rcnt, 
                        sum(if(rank = 1, 1, 0)) r1, 
                        sum(if(rank = 2, 1, 0)) r2, 
                        sum(if(rank = 3, 1, 0)) r3,
                        sum(if(rank = 4, 1, 0)) r4,
                        sum(if(rank = 5, 1, 0)) r5,
                        sum(if(rank = 6, 1, 0)) r6,
                        sum(if(rank = 7, 1, 0)) r7,
                        sum(if(rank = 8, 1, 0)) r8,
                        sum(if(rank = 9, 1, 0)) r9,
                        sum(if(rank = 10, 1, 0)) r10,
                        sum(if(rank = 11, 1, 0)) r11,
                        sum(if(rank >= 12, 1, 0)) r12,
                        
                        sum(if(r_rank > 0, 1, 0 )) rrcnt,
                        sum(if(r_rank = 1, 1, 0)) rr1, 
                        sum(if(r_rank = 2, 1, 0)) rr2, 
                        sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(r_rank = 4, 1, 0)) rr4,
                        sum(if(r_rank = 5, 1, 0)) rr5,
                        sum(if(r_rank = 6, 1, 0)) rr6,
                        sum(if(r_rank = 7, 1, 0)) rr7,
                        sum(if(r_rank = 8, 1, 0)) rr8,
                        sum(if(r_rank = 9, 1, 0)) rr9,
                        sum(if(r_rank = 10, 1, 0)) rr10,
                        sum(if(r_rank = 11, 1, 0)) rr11,
                        sum(if(r_rank >= 12, 1, 0)) rr12
                from expect a
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                group by host
                
            ) a right outer join  exp011 b  on a.host = b.host
            where b.rcity =  '"""
            + i_rcity
            + """'
                    and b.rdate = '"""
            + i_rdate
            + """'
                    and b.rno =  """
            + str(i_rno)
            + """
                    order by b.rank, b.gate
                ; """
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        award_h = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in Award_h")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity, jockey awardee, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey j_name, trainer t_name, host h_name, r_pop, distance, handycap, jt_per, s1f_rank, corners, g3f_rank, g1f_rank, alloc3r, jockey_old, reason
                from expect
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                order by rdate, rtime, gate
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race_detail = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in expect : 경주별 Detail(약식)) ")

    return award_j, award_t, award_h, race_detail


# 기수 인기도 및 게이트 연대율
def get_popularity_rate_j(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """select b.rank, b.gate, b.jockey, b.trainer, b.host,
                    sum(r1_1) r1_1, sum(r1_2) r1_2, sum(r1_3) r1_3, sum(r1_cnt) r1_cnt, 
                    sum(r3_1) r1_1, sum(r3_2) r2_2, sum(r3_3) r3_3, sum(r3_cnt) r3_cnt,
                    sum(gt_1) r1_1, sum(gt_2) r2_2, sum(gt_3) gt_3, sum(gt_cnt) gt_cnt
                from
                (
                        SELECT jockey, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt,
                                    0 r3_1, 0 r3_2, 0 r3_3, 0 r3_cnt,
                                    0 gt_1, 0 gt_2, 0 gt_3, 0 gt_cnt
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and pop_rank between 1 and 3
                        group by jockey 

                        union all

                        select b.jockey,   0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt,  0, 0, 0, 0
                        from
                        (
                          SELECT jockey, distance, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM record 
                          where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                          and grade != '주행검사'
                          group by jockey , distance	
                          ) a  right outer join  expect b  on a.jockey = b.jockey and a.distance = b.distance
                        where b.rcity =  '"""
            + i_rcity
            + """'
                          and b.rdate = '"""
            + i_rdate
            + """'
                          and b.rno =  """
            + str(i_rno)
            + """

                        union all
    
                        select b.jockey,   0, 0, 0, 0,  0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt
                        from
                        (
                          SELECT jockey, gate, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM record 
                          where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                          and grade != '주행검사'
                          group by jockey , gate	
                          ) a  right outer join  exp011 b  on a.jockey = b.jockey and a.gate = b.gate
                        where b.rcity =  '"""
            + i_rcity
            + """'
                          and b.rdate = '"""
            + i_rdate
            + """'
                          and b.rno =  """
            + str(i_rno)
            + """


                      ) a  right outer join  exp011 b  on a.jockey = b.jockey
                    where b.rcity =  '"""
            + i_rcity
            + """'
                      and b.rdate = '"""
            + i_rdate
            + """'
                      and b.rno =  """
            + str(i_rno)
            + """
                    group by b.rank, b.gate, b.jockey
                    order by b.rank, b.gate, b.jockey
                        ;"""
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        popularity = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    try:
        cursor = connection.cursor()

        strSql = (
            """
            select b.rank, b.gate, b.jockey, b.trainer, b.host, rcnt, r1, r2, r3, r4, r5, r6, r7, r8, rrcnt, rr1, rr2, rr3, rr4, rr5, rr6, rr7, rr8
            from
            (
                select jockey, count(*) rcnt, 
                        sum(if(rank = 1, 1, 0)) r1, 
                        sum(if(rank = 2, 1, 0)) r2, 
                        sum(if(rank = 3, 1, 0)) r3,
                        sum(if(rank = 4, 1, 0)) r4,
                        sum(if(rank = 5, 1, 0)) r5,
                        sum(if(rank = 6, 1, 0)) r6,
                        sum(if(rank = 7, 1, 0)) r7,
                        sum(if(rank >= 8, 1, 0)) r8,
                        
                        sum(if(r_rank > 0, 1, 0 )) rrcnt,
                        sum(if(r_rank = 1, 1, 0)) rr1, 
                        sum(if(r_rank = 2, 1, 0)) rr2, 
                        sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(r_rank = 4, 1, 0)) rr4,
                        sum(if(r_rank = 5, 1, 0)) rr5,
                        sum(if(r_rank = 6, 1, 0)) rr6,
                        sum(if(r_rank = 7, 1, 0)) rr7,
                        sum(if(r_rank >= 8, 1, 0)) rr8
                from expect a
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                group by jockey
                
            ) a right outer join  exp011 b  on a.jockey = b.jockey
            where b.rcity =  '"""
            + i_rcity
            + """'
                    and b.rdate = '"""
            + i_rdate
            + """'
                    and b.rno =  """
            + str(i_rno)
            + """
                    order by b.rank, b.gate
                ; """
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        award_j = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Award_j")

    return popularity, award_j


# 조교사 인기도 및 게이트 연대율


def get_popularity_rate_t(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """select b.rank, b.gate, b.jockey, b.trainer, b.host,
                                  sum(r1_1) r1_1, sum(r1_2) r1_2, sum(r1_3) r1_3, sum(r1_cnt) r1_cnt, 
                                  sum(r3_1) r1_1, sum(r3_2) r2_2, sum(r3_3) r3_3, sum(r3_cnt) r3_cnt,
                                  sum(gt_1) r1_1, sum(gt_2) r2_2, sum(gt_3) gt_3, sum(gt_cnt) gt_cnt
                      from
                      (
                        SELECT trainer, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt,
                                    0 r3_1, 0 r3_2, 0 r3_3, 0 r3_cnt,
                                    0 gt_1, 0 gt_2, 0 gt_3, 0 gt_cnt
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and pop_rank between 1 and 3
                        group by trainer 

                        union all

                        select b.trainer,   0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt,  0, 0, 0, 0
                        from
                        (
                          SELECT trainer, distance, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM record 
                          where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                          and grade != '주행검사'
                          group by trainer , distance	
                          ) a  right outer join  expect b  on a.trainer = b.trainer and a.distance = b.distance
                        where b.rcity =  '"""
            + i_rcity
            + """'
                          and b.rdate = '"""
            + i_rdate
            + """'
                          and b.rno =  """
            + str(i_rno)
            + """

                        union all
    
                        select b.trainer,   0, 0, 0, 0,  0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt
                        from
                        (
                          SELECT trainer, gate, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM record 
                          where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                          and grade != '주행검사'
                          group by trainer , gate	
                          ) a  right outer join  exp011 b  on a.trainer = b.trainer and a.gate = b.gate
                        where b.rcity =  '"""
            + i_rcity
            + """'
                          and b.rdate = '"""
            + i_rdate
            + """'
                          and b.rno =  """
            + str(i_rno)
            + """


                      ) a  right outer join  exp011 b  on a.trainer = b.trainer
                    where b.rcity =  '"""
            + i_rcity
            + """'
                      and b.rdate = '"""
            + i_rdate
            + """'
                      and b.rno =  """
            + str(i_rno)
            + """
                    group by b.rank, b.gate, b.trainer
                    order by b.rank, b.gate, b.trainer
                        ;"""
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        popularity = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    try:
        cursor = connection.cursor()

        strSql = (
            """
            select b.rank, b.gate, b.jockey, b.trainer, b.host, rcnt, r1, r2, r3, r4, r5, r6, r7, r8, rrcnt, rr1, rr2, rr3, rr4, rr5, rr6, rr7, rr8
            from
            (
                select trainer, count(*) rcnt, 
                        sum(if(rank = 1, 1, 0)) r1, 
                        sum(if(rank = 2, 1, 0)) r2, 
                        sum(if(rank = 3, 1, 0)) r3,
                        sum(if(rank = 4, 1, 0)) r4,
                        sum(if(rank = 5, 1, 0)) r5,
                        sum(if(rank = 6, 1, 0)) r6,
                        sum(if(rank = 7, 1, 0)) r7,
                        sum(if(rank >= 8, 1, 0)) r8,
                        
                        sum(if(r_rank > 0, 1, 0 )) rrcnt,
                        sum(if(r_rank = 1, 1, 0)) rr1, 
                        sum(if(r_rank = 2, 1, 0)) rr2, 
                        sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(r_rank = 4, 1, 0)) rr4,
                        sum(if(r_rank = 5, 1, 0)) rr5,
                        sum(if(r_rank = 6, 1, 0)) rr6,
                        sum(if(r_rank = 7, 1, 0)) rr7,
                        sum(if(r_rank >= 8, 1, 0)) rr8
                from expect a
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                group by trainer
                
            ) a right outer join  exp011 b  on a.trainer = b.trainer
            where b.rcity =  '"""
            + i_rcity
            + """'
                    and b.rdate = '"""
            + i_rdate
            + """'
                    and b.rno =  """
            + str(i_rno)
            + """
                    order by b.rank, b.gate
                ; """
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        award_t = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Award_t")

    return popularity, award_t


def get_popularity_rate_h(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """select b.rank, b.gate, b.jockey, b.trainer, b.host,
                                  sum(r1_1) r1_1, sum(r1_2) r1_2, sum(r1_3) r1_3, sum(r1_cnt) r1_cnt, 
                                  sum(r3_1) r1_1, sum(r3_2) r2_2, sum(r3_3) r3_3, sum(r3_cnt) r3_cnt,
                                  sum(gt_1) r1_1, sum(gt_2) r2_2, sum(gt_3) gt_3, sum(gt_cnt) gt_cnt
                      from
                      (
                        SELECT host, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt,
                                    0 r3_1, 0 r3_2, 0 r3_3, 0 r3_cnt,
                                    0 gt_1, 0 gt_2, 0 gt_3, 0 gt_cnt
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and pop_rank between 1 and 3
                        group by host 

                        union all

                        SELECT host, 0, 0, 0, 0,
                                        sum( if( rank = 1, 1, 0 )) r1, sum( if( rank = 2, 1, 0 )) r2, sum( if( rank = 3, 1, 0 )) r3, count(*) rcnt,
                                        0, 0, 0, 0
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and alloc3r <= 1.9 /* 연식 1.9이하 인기마 */
                        
                        group by host 

                        union all
    
                        select b.host,   0, 0, 0, 0,  0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt
                        from
                        (
                          SELECT host, gate, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM record 
                          where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d')
                          and grade != '주행검사'
                          group by host , gate	
                          ) a  right outer join  exp011 b  on a.host = b.host and a.gate = b.gate
                        where b.rcity =  '"""
            + i_rcity
            + """'
                          and b.rdate = '"""
            + i_rdate
            + """'
                          and b.rno =  """
            + str(i_rno)
            + """


                      ) a  right outer join  exp011 b  on a.host = b.host
                    where b.rcity =  '"""
            + i_rcity
            + """'
                      and b.rdate = '"""
            + i_rdate
            + """'
                      and b.rno =  """
            + str(i_rno)
            + """
                    group by b.rank, b.gate, b.host
                    order by b.rank, b.gate, b.host
                        ;"""
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        popularity = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    try:
        cursor = connection.cursor()

        strSql = (
            """
            select b.rank, b.gate, b.jockey, b.trainer, b.host, rcnt, r1, r2, r3, r4, r5, r6, r7, r8, rrcnt, rr1, rr2, rr3, rr4, rr5, rr6, rr7, rr8
            from
            (
                select host, count(*) rcnt, 
                        sum(if(rank = 1, 1, 0)) r1, 
                        sum(if(rank = 2, 1, 0)) r2, 
                        sum(if(rank = 3, 1, 0)) r3,
                        sum(if(rank = 4, 1, 0)) r4,
                        sum(if(rank = 5, 1, 0)) r5,
                        sum(if(rank = 6, 1, 0)) r6,
                        sum(if(rank = 7, 1, 0)) r7,
                        sum(if(rank >= 8, 1, 0)) r8,
                        
                        sum(if(r_rank > 0, 1, 0 )) rrcnt,
                        sum(if(r_rank = 1, 1, 0)) rr1, 
                        sum(if(r_rank = 2, 1, 0)) rr2, 
                        sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(r_rank = 4, 1, 0)) rr4,
                        sum(if(r_rank = 5, 1, 0)) rr5,
                        sum(if(r_rank = 6, 1, 0)) rr6,
                        sum(if(r_rank = 7, 1, 0)) rr7,
                        sum(if(r_rank >= 8, 1, 0)) rr8
                from expect a
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                group by host
                
            ) a right outer join  exp011 b  on a.host = b.host
            where b.rcity =  '"""
            + i_rcity
            + """'
                    and b.rdate = '"""
            + i_rdate
            + """'
                    and b.rno =  """
            + str(i_rno)
            + """
                    order by b.rank, b.gate
                ; """
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        award_h = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Award_j")

    return popularity, award_h


def get_print_prediction(i_rcity, i_rdate):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity, rdate, rday, rno, rtime, distance,  substr(grade,1,2) grade, substr(dividing,1,2) dividing
                from exp010
                where rcity = '"""
            + i_rcity
            + """'
                and rdate = '"""
            + i_rdate
            + """' 
                order by rdate, rcity desc, rno
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    try:
        cursor = connection.cursor()

        strSql = (
            """
                select a.rcity, a.rdate, a.rday, a.rno, b.gate, b.rank, b.r_rank, b.horse, b.remark, b.jockey, b.trainer, b.host, b.r_pop, a.distance, b.handycap, b.i_prehandy, b.complex,
                    b.complex5, b.gap_back, 
                    b.jt_per, b.jt_cnt, b.jt_3rd,
                    b.s1f_rank, b.i_cycle, a.rcount, recent3, recent5, convert_r, 
                    ( 
                        select count(disease) 
                        from treat
                        where horse = b.horse
                        and tdate between date_format(DATE_ADD('"""
                        + i_rdate
                        + """', INTERVAL - 99 DAY), '%Y%m%d') and '"""
                        + i_rdate
                        + """'
                        and ( disease like '%절염%' or disease like '%골막염%' or disease like '%대염%' )
                        -- group by horse, tdate
                    ),
            
                    ( select count(*) from The1.train 
                        where tdate between date_format(DATE_ADD('"""
                        + i_rdate
                        + """' , INTERVAL - 21 DAY), '%Y%m%d') and '"""
                        + i_rdate
                        + """' 
                        and horse = b.horse
                        and rider = b.jockey
                    --    group by horse, rider 
                    -- having count(*) >= 7
                    )
                from exp010 a, exp011 b
                where a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno
                and a.rcity = '"""
            + i_rcity
            + """'
                and a.rdate = '"""
            + i_rdate
            + """' 
                and b.rank in ( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 98 )
                order by a.rcity, a.rdate, a.rno, b.rank, b.gate
                ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        expects = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")
    # print(r_cnt)
    # print(type(weeks[0]))

    return race, expects


def get_prediction(i_rdate):

    # race Query
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select a.rcity, a.rdate, a.rday, a.rno, a.rtime, a.distance, b.r2alloc, b.r333alloc, b.r123alloc, a.grade, a.dividing,
                ( select judged from rec013 where a.rcity = rcity and a.rdate = rdate and a.rno = rno ) judged
                from exp010 a left outer join 
                    rec010 b on a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno
                where a.rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 4 DAY), '%Y%m%d')
                order by a.rdate, a.rtime
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in exp010 outer join rec010")

    # expects Query
    try:
        cursor = connection.cursor()

        strSql = (
            """
                select a.rcity, a.rdate, a.rday, a.rno, b.gate, b.rank, b.r_rank, b.horse, b.remark, b.jockey, b.trainer, b.host, b.r_pop, a.distance, b.handycap, b.i_prehandy, b.complex,
                    b.complex5, b.gap_back, 
                    b.jt_per, b.jt_cnt, b.jt_3rd,
                    b.s1f_rank, b.i_cycle, a.rcount, recent3, recent5, convert_r, 0, 0
                
                from exp010 a, exp011 b
                where a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno
                and b.rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 4 DAY), '%Y%m%d')
                and b.rank in ( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 98 )
                order by b.rcity, b.rdate, b.rno, b.rank, b.gate
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        expects = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in expect ")

    # awqard_j Query
    try:
        cursor = connection.cursor()

        strSql = (
            """
                select rcity, jockey, count(*),
                        sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) + sum(if(r_rank = 3, 1, 0)) rr123_cnt,
                        sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0)) + sum(if(rank = 3, 1, 0)) r123_cnt,
                        sum(if(r_rank = 1, 1, 0)) rr1, sum(if(r_rank = 2, 1, 0)) rr2, sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(rank = 1, 1, 0)) r1, sum(if(rank = 2, 1, 0)) r2, sum(if(rank = 3, 1, 0)) r3, 
                        date_format(DATE_ADD( min(rdate) , INTERVAL - 7 DAY), '%Y%m%d'),
                        -- min(rdate), 
                        max(rdate)
                from expect a
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                -- and 1 <> 1
                group by rcity, jockey
                order by rcity, sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) + sum(if(r_rank = 3, 1, 0)) desc,
                                sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) desc,
                                sum(if(r_rank = 1, 1, 0))  desc,
                                sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0)) + sum(if(rank = 3, 1, 0)) desc,
                                sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0))  desc,
                                sum(if(rank = 1, 1, 0)) desc,
                                count(*) desc
                ; """
        )
        # print(strSql) 

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        award_j = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in BookListView")
    # print(r_cnt)
    # print(type(weeks[0]))

    # rdays Query
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select a.rdate, a.rday, date_format( curdate(), '%Y%m%d' ) -- , rcity
                from exp010 a
                where a.rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 4 DAY), '%Y%m%d')
                group by a.rdate, a.rday
                order by a.rdate, a.rday 
                ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        rdays = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting rdays")

    # judged_jockey Query
    # try:
    #     cursor = connection.cursor()

    #     strSql = (
    #         """
    #         SELECT distinct b.rcity, b.rdate, b.rno, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason
    #             FROM exp011     a,
    #                 rec015     b
    #             where a.jockey = b.jockey and 1 <> 1
    #             AND b.t_sort = '기수'
    #             AND b.rdate between date_format(DATE_ADD('"""
    #         + i_rdate
    #         + """', INTERVAL - 100 DAY), '%Y%m%d') and '"""
    #         + i_rdate
    #         + """'
    #             AND a.rdate between '"""
    #         + i_rdate
    #         + """' and date_format(DATE_ADD('"""
    #         + i_rdate
    #         + """', INTERVAL + 3 DAY), '%Y%m%d')
    #         ORDER BY b.rdate desc

    #         ; """
    #     )

    #     # print(strSql)
    #     r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
    #     judged_jockey = cursor.fetchall()

    #     connection.commit()
    #     connection.close()

    # except:
    #     connection.rollback()
    #     print("Failed selecting in judged jockey")

    return race, expects, rdays, award_j


def get_expects(i_rdate):

    try:
        cursor = connection.cursor()

        strSql = (
            """
                select rcity, jockey, count(*), 
                        sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) + sum(if(r_rank = 3, 1, 0)) rr123_cnt, 
                        sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0)) + sum(if(rank = 3, 1, 0)) r123_cnt, 
                        sum(if(r_rank = 1, 1, 0)) rr1, 
                        sum(if(r_rank = 2, 1, 0)) rr2, 
                        sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(rank = 1, 1, 0)) r1, 
                        sum(if(rank = 2, 1, 0)) r2, 
                        sum(if(rank = 3, 1, 0)) r3
                from expect a
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                group by rcity, jockey
                order by rcity, sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) + sum(if(r_rank = 3, 1, 0)) desc,
                                sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) desc,
                                sum(if(r_rank = 1, 1, 0))  desc,
                                sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0)) + sum(if(rank = 3, 1, 0)) desc,
                                sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0))  desc,
                                sum(if(rank = 1, 1, 0)) desc
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        award_j = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in award_j")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            SELECT distinct b.rcity, b.rdate, b.rno, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason
                FROM exp011     a,
                    rec015     b
                where a.jockey = b.jockey 
                AND b.t_sort = '기수'
                AND b.rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 100 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                AND a.rdate between '"""
            + i_rdate
            + """' and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
            ORDER BY b.rdate desc

            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        judged_jockey = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in judged jockey")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity, jockey, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey j_name, trainer t_name, host h_name, r_pop, distance, handycap, jt_per, s1f_rank, jockey_old, reason
                from expect
                where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                order by rdate, rcity, rno
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race_detail = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in expect : 경주별 Detail(약식)) ")

    return award_j, race_detail, judged_jockey


def get_report_code(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()
        strSql = (
            """ select rcity, rdate, rno, rank, gate, horse, r_start, r_corners, r_finish, r_wrapup, r_etc
                    from rec011 
                    where rcity =  '"""
            + i_rcity
            + """'
                      and rdate = '"""
            + i_rdate
            + """'
                      and rno =  """
            + str(i_rno)
            + """
                      order by rank, gate
                    """
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        rec011 = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting start")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R1' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_start = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting r_start")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R2' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_corners = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting r_corners")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R3' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_finish = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting r_finish")
    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R4' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_wrapup = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting r_wrapup")

    return rec011, r_start, r_corners, r_finish, r_wrapup


def get_trainer_double_check(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select a.trainer
                from exp011 a
                where a.rcity =  '"""
            + i_rcity
            + """'
                and a.rdate = '"""
            + i_rdate
            + """'
                and a.rno =  """
            + str(i_rno)
            + """
                group by a.rcity, a.rdate, a.rno, a.trainer
                having count(*) >= 2

                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        trainer_double_check = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in exp010 outer join rec010")

    try:
        cursor = connection.cursor()

        strSql = (
            """ select rider, lpad( cast( count(*) as char), 2, ' ') from train 
                where tdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 21 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                and horse in ( select horse from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """)
                and rider in ( select jockey from exp011 where rdate = '"""
            + i_rdate
            + """' and rcity = '"""
            + i_rcity
            + """' and rno = """
            + str(i_rno)
            + """)
                group by rider 
            having count(*) >= 7
            ;"""
        )
        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        training_cnt = cursor.fetchall()

        # connection.commit()
        # connection.close()

        # print(training_cnt)
    except:
        # connection.rollback()
        print("Failed selecting in training_cnt")

    return trainer_double_check, training_cnt


# 마방 등급별 경주마 보유현황
def stable_status(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = """ 
                SELECT wdate, trainer, grade, count(*)
                FROM horse_w a
                where wdate  between '20240103' and  '20240303'
                and trainer in ( select trainer from exp011 where rcity = '서울' and rdate = '20240303' ) 
                group by wdate desc, trainer, grade
            ; """

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Jockey Trend")

    col = ["예상", "마번", "실순", "인기", "기수", "마주", "마방", "등급", "두수"]
    data = list(result)
    # print(data)

    df = pd.DataFrame(data=data, columns=col)

    pdf1 = pd.pivot_table(
        df,  # 피벗할 데이터프레임
        index=(
            "예상",
            "마번",
            "실순",
            "인기",
            "기수",
            "마주",
            "마방",
        ),  # 행 위치에 들어갈 열
        columns="등급",  # 열 위치에 들어갈 열
        values=("두수"),
        aggfunc="max",
        fill_value=0,  # null 치환
    )  # 데이터로 사용할 열

    # pdf1.columns = ['/'.join(col) for col in pdf1.columns]
    pdf1.columns = ["".join(col) for col in pdf1.columns]

    pdf1 = pdf1.reset_index()
    # print(pdf1)

    return pdf1


# 경주별 마방 등급별 경주마 보유현황
def get_status_stable(i_rcity, i_rdate, i_rno):

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            SELECT max(wdate) FROM trainer_w where wdate like '"""
            + i_rdate[0:6]
            + """%' and wdate <= '"""
            + i_rdate
            + """' 
        ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()
        
        # print(r_cnt, result[0][0])

    except:
        # connection.rollback()
        print("Failed selecting wdate ")
        
    if result[0][0] != None:
        
        try:
            cursor = connection.cursor()

            strSql = (
                """ 
                    SELECT b.rank, b.gate, b.r_rank, b.r_pop, b.jockey, b.host, b.horse, b.rating, a.trainer, a.grade, a.wdate, count(*) cnt, 
                    -- sum(a.year_1st ) r1cnt
                    sum( if( a.host = b.host, 1, 0)) r1cnt 
                    FROM horse_w a,
                        expect b
                    where a.trainer = b.trainer 
                    -- and a.host = b.host
                    and a.wdate in (
                        SELECT max(wdate) FROM trainer_w where wdate like '"""
                + i_rdate[0:6]
                + """%' and wdate <= '"""
                + i_rdate
                + """' 
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 1 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 2 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 3 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 4 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 5 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 6 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 7 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 8 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 9 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 10 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 11 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 12 MONTH), '%Y%m%')
                    )
                    and b.rcity = '"""
                + i_rcity
                + """' and b.rdate = '"""
                + i_rdate
                + """' and b.rno = """
                + str(i_rno)
                + """
                    group by b.rank, b.gate, b.r_rank, b.r_pop, b.jockey, b.host, b.horse, b.rating, a.trainer, a.grade, a.wdate
                ; """
            )

            # print(strSql)
            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            result = cursor.fetchall()

            # print(result)
            # print(r_cnt)

            # connection.commit()
            # connection.close()

        except:
            # connection.rollback()
            print("Failed selecting in status_stable")
    else:
        try:
            cursor = connection.cursor()

            strSql = (
                """ 
                    SELECT b.rank, b.gate, b.r_rank, b.r_pop, b.jockey, b.host, b.horse, b.rating, a.trainer, a.grade, a.wdate, count(*) cnt, sum(a.year_1st) r1cnt
                    FROM horse_w a,
                        expect b
                    where a.trainer = b.trainer 
                    -- and a.host = b.host
                    and a.wdate in (
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 1 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 2 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 3 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 4 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 5 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 6 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 7 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 8 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 9 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 10 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 11 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 12 MONTH), '%Y%m%')
                        union all
                        SELECT max(wdate) FROM trainer_w where wdate like date_format(DATE_ADD('"""
                + i_rdate
                + """', INTERVAL - 13 MONTH), '%Y%m%')
                    )
                    and b.rcity = '"""
                + i_rcity
                + """' and b.rdate = '"""
                + i_rdate
                + """' and b.rno = """
                + str(i_rno)
                + """
                    group by b.rank, b.gate, b.r_rank, b.r_pop, b.jockey, b.host, b.horse, b.rating, a.trainer, a.grade, a.wdate
                ; """
            )

            # print(strSql)
            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            result = cursor.fetchall()

            # print(result)
            # print(r_cnt)

            # connection.commit()
            # connection.close()

        except:
            # connection.rollback()
            print("Failed selecting in status_stable")

    col = [
        "예상",
        "마번",
        "실순",
        "인기",
        "기수",
        "마주",
        "경주마",
        "레이팅",
        "마방",
        "등급",
        "wdate",
        "cnt",
        "r1cnt",
    ]
    data = list(result)
    df = pd.DataFrame(data=data, columns=col)

    # print(data[0:100])

    #### 월별 마방 경주마 보유 추이
    pdf1 = pd.pivot_table(
        df,  # 피벗할 데이터프레임
        index=(
            "예상",
            "마번",
            "실순",
            "인기",
            "기수",
            "마주",
            "경주마",
            "레이팅",
            "마방",
        ),  # 행 위치에 들어갈 열
        values=(
            "cnt",
            "r1cnt",
        ),
        columns="wdate",  # 열 위치에 들어갈 열
        aggfunc={"cnt": np.sum, "r1cnt": np.sum},
        fill_value=0,  # null 치환
    )  # 데이터로 사용할 열

    pdf1.columns = [
        "'" + "".join(col[1])[2:4] + "." + "".join(col[1])[4:6] for col in pdf1.columns
    ]
    pdf1 = pdf1.reset_index()

    #### 월별 등급별 마방 경주마 보유 추이
    pdf2 = pd.pivot_table(
        df,  # 피벗할 데이터프레임
        index=[
            "예상",
            "마번",
            "실순",
            "인기",
            "기수",
            "마주",
            "경주마",
            "레이팅",
            "마방",
            "등급",
        ],  # 행 위치에 들어갈 열
        values=(
            "cnt",
            "r1cnt",
        ),
        columns="wdate",  # 열 위치에 들어갈 열
        aggfunc={"cnt": np.sum, "r1cnt": np.sum},
        fill_value=0,  # null 치환
    )  # 데이터로 사용할 열

    pdf2.columns = [
        "'" + "".join(col[1])[2:4] + "." + "".join(col[1])[4:6] for col in pdf2.columns
    ]
    pdf2 = pdf2.reset_index()

    #### 마주 경주마 보유
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            SELECT a.trainer, a.host, a.grade, if(a.horse = b.horse, 0, 1), count(*) cnt, sum(a.year_1st) year_1st, sum(a.year_2nd) year_2nd, sum(a.year_3rd) year_3rd, sum(a.year_race) year_cnt
            FROM horse_w a,
            expect b 
            where a.trainer = b.trainer
            and a.host = b.host
            and a.wdate in (
                SELECT max(wdate) FROM trainer_w where wdate like '"""
            + i_rdate[0:6]
            + """%' and wdate <= '"""
            + i_rdate
            + """' 
                )
                and b.rcity = '"""
            + i_rcity
            + """' and b.rdate = '"""
            + i_rdate
            + """' and b.rno = """
            + str(i_rno)
            + """
                group by a.trainer, a.host, a.grade, if(a.horse = b.horse, 0, 1)
            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result_h = cursor.fetchall()
        # print(strSql)

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in host stable")

    return pdf1, pdf2, result_h


def get_jockey_trend(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select b.rank, b.gate, b.r_rank, b.r_pop, b.horse, CONCAT( RPAD(b.jockey, 5),RPAD( b.trainer, 5), b.host), a.wdate, a.year_per, CONCAT(debut, ' ', age, '_', wcnt) debut, weeks
            from
            (
                SELECT wdate, jockey, cast( year_3per as DECIMAL(4,1))*10 year_per, tot_1st, debut, CONCAT(wrace, '`', w1st, '`', w2nd, '`', w3rd) weeks, 
                        ( select concat( max(age) , ' ', max(tot_1st) ) from jockey_w c where c.jockey = d.jockey and c.wdate < '"""
            + i_rdate
            + """' ) age,
                        ( select concat( sum(if( r_rank = 1, 1, 0)),'`', sum(if( r_rank = 2, 1, 0)), '`', sum(if( r_rank = 3, 1, 0))) from exp011 
                            where jockey = d.jockey -- and r_rank <= 3 
                            and rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """' ) wcnt
                FROM jockey_w d
                where wdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 85 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                and wdate < '"""
            + i_rdate
            + """'
            ) a  right outer join  expect b  on a.jockey = b.jockey 
            where b.rdate = '"""
            + i_rdate
            + """' and b.rcity = '"""
            + i_rcity
            + """' and b.rno = """
            + str(i_rno)
            + """
            order by b.rank, a.wdate desc
            ; """
        )

        # print(strSql)
        
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in Jockey Trend")

    col = [
        "예상",
        "마번",
        "실순",
        "인기",
        "horse",
        "기수",
        "wdate",
        "year_per",
        "데뷔",
        "Weeks",
    ]
    data = list(result)
    # print(data)

    df = pd.DataFrame(data=data, columns=col)
    # print(df)

    pdf1 = pd.pivot_table(
        df,  # 피벗할 데이터프레임
        index=(
            "예상",
            "마번",
            "실순",
            "인기",
            "horse",
            "기수",
            "데뷔",
        ),  # 행 위치에 들어갈 열
        columns="wdate",  # 열 위치에 들어갈 열
        values=("year_per", "Weeks"),
        aggfunc="max",
        fill_value=0,
    )  # 데이터로 사용할 열

    # pdf1.columns = ['/'.join(col) for col in pdf1.columns]
    pdf1.columns = ["".join(col)[4:6] + "." + "".join(col)[6:8] for col in pdf1.columns]

    # print(((pdf1)))

    pdf1 = pdf1.reset_index()

    # print(pdf1)

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
              SELECT distinct distinct CONCAT( substr(wdate,5,2), '.', substr(wdate,7,2) )
                FROM jockey_w d
                where wdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 85 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                and wdate < '"""
            + i_rdate
            + """'
                order by wdate
              ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        trend_title = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in Jockey Trend Title")
    # result = dict[result]

    return pdf1, trend_title


def get_trainer_trend(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
              select b.rank, b.gate, b.r_rank, b.r_pop, b.horse, CONCAT( RPAD(b.trainer, 5),RPAD( b.jockey, 5), b.host), a.wdate, a.year_per, CONCAT(debut, ' ', age, '_', wcnt) debut, weeks
              from
              (
                SELECT wdate, trainer, cast( year_3per as DECIMAL(4,1))*10 year_per, tot_1st, debut, CONCAT(wrace, '`', w1st, '`', w2nd, '`', w3rd) weeks,
                        ( select concat( max(age) , ' ', max(tot_1st) ) from trainer_w c where c.trainer = d.trainer and c.wdate < '"""
            + i_rdate
            + """' ) age,
                        ( select concat( sum(if( r_rank = 1, 1, 0)),'`', sum(if( r_rank = 2, 1, 0)), '`', sum(if( r_rank = 3, 1, 0))) from exp011 
                            where trainer = d.trainer -- and r_rank <= 3 
                            and rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 3 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """' ) wcnt
                FROM trainer_w d
                where wdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 85 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                and wdate < '"""
            + i_rdate
            + """'
              ) a  right outer join  expect b  on a.trainer = b.trainer 
              where b.rdate = '"""
            + i_rdate
            + """' and b.rcity = '"""
            + i_rcity
            + """' and b.rno = """
            + str(i_rno)
            + """
              order by b.rank, a.wdate desc
              ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Trainer Trend")

    # result = dict[result]

    col = [
        "예상",
        "마번",
        "실순",
        "인기",
        "horse",
        "기수",
        "wdate",
        "year_per",
        "데뷔",
        "Weeks",
    ]
    data = list(result)
    # print(data)

    df = pd.DataFrame(data=data, columns=col)
    # print(df)

    pdf1 = pd.pivot_table(
        df,  # 피벗할 데이터프레임
        index=(
            "예상",
            "마번",
            "실순",
            "인기",
            "horse",
            "기수",
            "데뷔",
        ),  # 행 위치에 들어갈 열
        columns="wdate",  # 열 위치에 들어갈 열
        values=("year_per", "Weeks"),
        aggfunc="max",
        fill_value=0,
    )  # 데이터로 사용할 열

    # pdf1.columns = ['/'.join(col) for col in pdf1.columns]
    pdf1.columns = ["".join(col)[4:6] + "." + "".join(col)[6:8] for col in pdf1.columns]

    # print(((pdf1)))

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
              SELECT distinct CONCAT( substr(wdate,5,2), '.', substr(wdate,7,2) )
                FROM jockey_w d
                where wdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 85 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                and wdate < '"""
            + i_rdate
            + """'
                order by wdate
              ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        trend_title = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Jockey Trend Title")
    # result = dict[result]

    pdf1 = pdf1.reset_index()

    # print(pdf1)

    return pdf1, trend_title


# 마방별 경주마 출주주기에 따른 연승율
def get_cycle_winning_rate(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select b.rank, b.gate, b.r_rank, b.r_pop, b.horse, b.trainer, title, r3per, CONCAT(r1cnt, '`', r2cnt, '`', r3cnt) r3total, round( ifnull(b.i_cycle,0)/7, 0) weeks,
                (
                    SELECT ifnull( CONCAT( b.h_age, b.h_sex, '  ', b.h_weight, space(10), convert( count(*), CHAR), ' ﹅ ', sum( if( rank = 1, 1, 0 )), '﹆', sum( if( rank = 2, 1, 0 )), '﹆', sum( if( rank = 3, 1, 0 )), space(3), round( sum( if( rank <= 3, 1, 0 ))/count(*)*100, 1)), '-')
                    FROM record
                    where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 999 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    and judge is null
                    and mid(w_change,1,3)*1 between if( length( mid(h_weight, 5,3)) = 0, '0', mid(h_weight, 5,3) )*1 - 2 and if( length( mid(h_weight, 5,3)) = 0, '0', mid(h_weight, 5,3) )*1 + 2   -- 체중변동 +- 2
                    and mid(w_change,1,1) = if ( length(b.h_weight) = 3 ,'+', mid(b.h_weight, 5,1))             -- 경주취소마 처리
                    and h_sex = b.h_sex
                    -- and distance = b.distance 
                    and h_age = if( length(h_age) = 1, mid(b.h_age, 1,1), mid(b.h_age, 1,2) )
                    -- and handycap*1 between b.handycap*1 - 1 and b.handycap*1 + 1
                    -- and grade = b.grade
                    and h_weight*1 between mid(b.h_weight,1,3)*1 - mid(b.h_weight, 5,3)*1 - 10 and mid(b.h_weight,1,3)*1 - mid(b.h_weight, 5,3)*1 + 10            -- 기준 직전경주 마체중 +- 10
                ),
                (
                    SELECT ifnull( CONCAT( b.h_age, b.h_sex, '  ', b.h_weight, space(10), convert( count(*), CHAR), ' ﹅ ', sum( if( rank = 1, 1, 0 )), '﹆', sum( if( rank = 2, 1, 0 )), '﹆', sum( if( rank = 3, 1, 0 )), space(3), round( sum( if( rank <= 3, 1, 0 ))/count(*)*100, 1)), '-')
                    FROM record
                    where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 999 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    and judge is null
                    and mid(w_change,1,3)*1 between if( length( mid(h_weight, 5,3)) = 0, '0', mid(h_weight, 5,3) )*1 - 2 and if( length( mid(h_weight, 5,3)) = 0, '0', mid(h_weight, 5,3) )*1 + 2   -- 체중변동 +- 2
                    and mid(w_change,1,1) = if ( length(b.h_weight) = 3 ,'+', mid(b.h_weight, 5,1))             -- 경주취소마 처리
                    and h_sex = b.h_sex
                    and distance = b.distance 
                    and h_age = if( length(h_age) = 1, mid(b.h_age, 1,1), mid(b.h_age, 1,2) )
                    -- and handycap*1 between b.handycap*1 - 1 and b.handycap*1 + 1
                    -- and grade = b.grade
                    and h_weight*1 between mid(b.h_weight,1,3)*1 - mid(b.h_weight, 5,3)*1 - 10 and mid(b.h_weight,1,3)*1 - mid(b.h_weight, 5,3)*1 + 10            -- 기준 직전경주 마체중 +- 10
                )
            from
            (
                SELECT trainer, 
                case
					when ifnull(i_cycle, 0) = 0 then '0.신마'
					when round( i_cycle/7, 0)  >=  1 and round( i_cycle/7, 0)  <= 2 then '1.2주'
					when round( i_cycle/7, 0)  =  3 then '2.3주'
					when round( i_cycle/7, 0)  =  4 then '3.4주'
					when round( i_cycle/7, 0)  =  5 then '4.5주'
					when round( i_cycle/7, 0)  =  6 then '5.6주'
					when round( i_cycle/7, 0)  =  7 then '6.7주'
					when round( i_cycle/7, 0)  =  8 then '7.8주'
					when round( i_cycle/7, 0)  =  9 then '8.9주'
					when round( i_cycle/7, 0)  =  10 then '9.10주'
					when round( i_cycle/7, 0)  >=  11 and round( i_cycle/7, 0)  <= 56 then 'A.1년'
					when round( i_cycle/7, 0)  >=  57 then 'B.휴양'
				end title,
                count(*) cnt, sum(if( rank = 1, 1, 0 )) r1cnt, sum(if( rank = 2, 1, 0 )) r2cnt, sum(if( rank = 3, 1, 0 )) r3cnt, round( sum(if( rank <= 3, 1, 0 ))/ count(*)*100, 1) r3per
				FROM rec011 a
				where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 999 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
				and judge is null
				and p_rank is not null -- 경주 취소마 or 주행중지마 제외 
				-- and p_rank <= 20
				and trainer is not null
				-- and round( i_cycle/7, 0)  = 2 
				group by trainer,
                case
					when ifnull(i_cycle, 0) = 0 then '0.신마'
					when round( i_cycle/7, 0)  >=  1 and round( i_cycle/7, 0)  <= 2 then '1.2주'
					when round( i_cycle/7, 0)  =  3 then '2.3주'
					when round( i_cycle/7, 0)  =  4 then '3.4주'
					when round( i_cycle/7, 0)  =  5 then '4.5주'
					when round( i_cycle/7, 0)  =  6 then '5.6주'
					when round( i_cycle/7, 0)  =  7 then '6.7주'
					when round( i_cycle/7, 0)  =  8 then '7.8주'
					when round( i_cycle/7, 0)  =  9 then '8.9주'
					when round( i_cycle/7, 0)  =  10 then '9.10주'
					when round( i_cycle/7, 0)  >=  11 and round( i_cycle/7, 0)  <= 52 then 'A.1년'
					when round( i_cycle/7, 0)  >=  53 then 'B.휴양'
					end
			) a right outer join  expect b  on a.trainer = b.trainer 
            where b.rdate = '"""
            + i_rdate
            + """' and b.rcity = '"""
            + i_rcity
            + """' and b.rno = """
            + str(i_rno)
            + """
            order by b.rank
            ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in cycle winning rate")

    # result = dict[result]

    col = [
        "예상",
        "마번",
        "실순",
        "인기",
        "horse",
        "마방",
        "title",
        "r3per",
        "r3total",
        "weeks",
        "weight_per",
        "dist_per",
    ]
    data = list(result)

    # print(data)

    df = pd.DataFrame(data=data, columns=col)

    pdf1 = pd.pivot_table(
        df,  # 피벗할 데이터프레임
        index=(
            "예상",
            "마번",
            "실순",
            "인기",
            "horse",
            "마방",
            "weeks",
            "weight_per",
            "dist_per",
        ),  # 행 위치에 들어갈 열
        columns="title",  # 열 위치에 들어갈 열
        values=("r3per", "r3total"),
        aggfunc=("max"),
        fill_value=0,
    )  # 데이터로 사용할 열

    # pdf1.columns = ['/'.join(col) for col in pdf1.columns]
    pdf1.columns = ["".join(col)[7:] for col in pdf1.columns]

    pdf1 = pdf1.reset_index()

    return pdf1


# 기수 or 조교사 최근 99일 경주결과
def get_solidarity(i_rcity, i_rdate, i_rno, i_awardee, i_filter):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                    select a.rcity, a.rdate, a.rno, a.distance, a.grade, a.dividing, a.weather, a.rstate, a.rmoisture, a.r1award, a.r2alloc, a.race_speed,
                        a.gate, a.rank, a.horse, a.h_weight, a.w_change, a.jockey, a.trainer, if( a.grade = '주행검사', ' ', a.host), a.rating, a.handycap, a.handycap - b.i_prehandy, a.record, 
                        replace( a.corners, ' ', '') corners, 
                        a.gap, a.gap_b, a.p_record, a.p_rank, a.pop_rank, a.alloc1r, a.alloc3r,
                        a.rs1f, a.rg3f, a.rg2f, a.rg1f, a.i_cycle,
                        a.jt_per, a.adv_track
                    from record a
                        LEFT JOIN exp011 b ON a.rcity = b.rcity AND a.rdate = b.rdate AND a.rno = b.rno  AND a.gate = b.gate
                    where ( a."""
            + i_awardee
            + """ ) in ( select """
            + i_awardee
            + """ from exp011 where rcity = '"""
            + i_rcity
            + """' and rdate = '"""
            + i_rdate
            + """' and rno =  """
            + str(i_rno)
            + """ ) 
                    and a.rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 30 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    and a.rank <= """
            + i_filter
            + """
                and a.r1award > 0  
                    order by a.rdate desc, a.rno desc, a.rcity
                ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기수, 조교사, 마주 최근 1년 연대현황")

    return result


# 기수 or 조교사 or 마주 최근 365일 경주결과
def get_recent_awardee(i_rdate, i_awardee, i_name):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                    select rcity, rdate, rno, distance, grade, dividing, weather, rstate, rmoisture, r1award, r2alloc, race_speed,
                        gate, rank, horse, h_weight, w_change, jockey, trainer, if( grade = '주행검사', '주행', host) host, rating, handycap, record, 
                        replace( corners,' ', '' ) corners,
                        gap, gap_b, p_record, p_rank, pop_rank, alloc1r, alloc3r,
                        rs1f, rg3f, rg2f, rg1f, i_cycle,
                        jt_per
                    from record a
                    where """
            + i_awardee
            + """ = '"""
            + i_name
            + """'
                    and rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    order by rdate desc, rno desc, rcity
                ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기수, 조교사, 마주 최근 1년 연대현황")

    return result


# 기수 or 조교사 or 마주 최근 44일 경주결과
def get_recent_horse(i_rdate, i_awardee, i_name):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                    select rcity, rdate, rno, distance, grade, dividing, weather, rstate, rmoisture, r1award, r2alloc, race_speed,
                        gate, rank, horse, h_weight, w_change, jockey, trainer, if( grade = '주행검사', ' ', host) host, rating, handycap, record, 
                        replace( corners,' ', '' ) corners,
                        gap, gap_b, p_record, p_rank, pop_rank, alloc1r, alloc3r,
                        rs1f, rg3f, rg2f, rg1f, i_cycle,
                        jt_per
                    from record a
                    where """
            + i_awardee
            + """ = '"""
            + i_name
            + """'
                    -- and rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 1000 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    and rdate < '"""
            + i_rdate
            + """'
                    order by rdate desc, rno desc, rcity
                ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기수, 조교사, 마주 최근 1년 연대현황")

    return result


# 기수 기준 축마선정
def get_axis(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                    select gate, count(*), sum( if ( a.r_rank <= 3, 1, 0)), sum( if ( a.r_rank <= 3	, 1, 0))/count(*)*100,        
                    -- sum( if(a.alloc3r <= 1.9, 1, 0)),  sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0)), sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0))/ sum( if(a.alloc3r <= 1.9, 1, 0))*100
                    sum( if(a.jt_per >= a.j_per, 1, 0)),  sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0)), sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0))/ sum( if(a.jt_per >= a.j_per, 1, 0))*100,
                    sum( if(a.jt_per < a.j_per, 1, 0)),  sum( if ( a.r_rank <= 3 and a.jt_per < a.j_per, 1, 0)), sum( if ( a.r_rank <= 3 and a.jt_per < a.j_per, 1, 0))/ sum( if(a.jt_per < a.j_per, 1, 0))*100
                    from expect a
                    where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    and ( rcity, rdate, rno ) not in ( select rcity, rdate, rno from expect where rank = 98  group by rcity, rdate, rno having count(*) >= 2 ) 
                    and rank = 1
                    and jockey = ( select jockey from exp011 where rcity = '"""
            + i_rcity
            + """' and rdate = '"""
            + i_rdate
            + """' and rno =  """
            + str(i_rno)
            + """ and rank = 1) 
                    -- and gate = ( select gate from exp011 where rcity = '"""
            + i_rcity
            + """' and rdate = '"""
            + i_rdate
            + """' and rno =  """
            + str(i_rno)
            + """ and rank = 1) 
                    group by gate
                    
                    union all
                    
                    select 'TOT', count(*), sum( if ( a.r_rank <= 3, 1, 0)), sum( if ( a.r_rank <= 3	, 1, 0))/count(*)*100,
                    -- sum( if(a.alloc3r <= 1.9, 1, 0)),  sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0)), sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0))/ sum( if(a.alloc3r <= 1.9, 1, 0))*100
                    sum( if(a.jt_per >= a.j_per, 1, 0)),  sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0)), sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0))/ sum( if(a.jt_per >= a.j_per, 1, 0))*100,
                    sum( if(a.jt_per < a.j_per, 1, 0)),  sum( if ( a.r_rank <= 3 and a.jt_per < a.j_per, 1, 0)), sum( if ( a.r_rank <= 3 and a.jt_per < a.j_per, 1, 0))/ sum( if(a.jt_per < a.j_per, 1, 0))*100
                    from expect a
                    where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    and ( rcity, rdate, rno ) not in ( select rcity, rdate, rno from expect where rank = 98  group by rcity, rdate, rno having count(*) >= 2 ) 
                    and rank = 1
                    and jockey = ( select jockey from exp011 where rcity = '"""
            + i_rcity
            + """' and rdate = '"""
            + i_rdate
            + """' and rno =  """
            + str(i_rno)
            + """ and rank = 1) 
                ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 축마 가능성 check ")

    # print(result)

    return result


# thethe9 rank 기준 축마 가능성 Query
def get_axis_rank(i_rcity, i_rdate, i_rno, i_rank):
    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                    select gate, count(*), 
					sum( if ( a.r_rank <= 3, 1, 0)), 
                    sum( if ( a.r_rank <= 3     , 1, 0))/count(*)*100,        
                    sum( if ( a.alloc1r <= 4.4, 1, 0)),  
                    sum( if ( a.r_rank <= 3 and a.alloc1r <= 4.4, 1, 0)), 
                    sum( if ( a.r_rank <= 3 and a.alloc1r <= 4.4, 1, 0)) / sum( if(a.alloc1r <= 4.4, 1, 0))*100,
                    
                    sum( if ( a.jt_per >= a.j_per, 1, 0)),  
                    sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0)), 
                    sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0)) / sum( if(a.jt_per >= a.j_per, 1, 0))*100
                    from expect a
                    where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    and ( rcity, rdate, rno ) not in ( select rcity, rdate, rno from expect where rank = 98  group by rcity, rdate, rno having count(*) >= 2 ) 
                    and rank <= """
            + str(i_rank)
            + """
                    and jockey = ( select jockey from exp011 where rcity = '"""
            + i_rcity
            + """' and rdate = '"""
            + i_rdate
            + """' and rno =  """
            + str(i_rno)
            + """ and rank = """
            + str(i_rank)
            + """ ) 

                    group by gate
                    
                    union all
                    
                    select 'TOT', count(*), 
					sum( if ( a.r_rank <= 3, 1, 0)), 
                    sum( if ( a.r_rank <= 3     , 1, 0))/count(*)*100,        
                    -- sum( if(a.alloc3r <= 1.9, 1, 0)),  sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0)), sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0))/ sum( if(a.alloc3r <= 1.9, 1, 0))*100
                    sum( if ( a.alloc1r <= 4.4, 1, 0)),  
                    sum( if ( a.r_rank <= 3 and a.alloc1r <= 4.4, 1, 0)), 
                    sum( if ( a.r_rank <= 3 and a.alloc1r <= 4.4, 1, 0)) / sum( if(a.alloc1r <= 4.4, 1, 0))*100,
                    
                    sum( if ( a.jt_per >= a.j_per, 1, 0)),  
                    sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0)), 
                    sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0)) / sum( if(a.jt_per >= a.j_per, 1, 0))*100
                    from expect a
                    where rdate between date_format(DATE_ADD('"""
            + i_rdate
            + """', INTERVAL - 365 DAY), '%Y%m%d') and '"""
            + i_rdate
            + """'
                    and ( rcity, rdate, rno ) not in ( select rcity, rdate, rno from expect where rank = 98  group by rcity, rdate, rno having count(*) >= 2 ) 
                    and rank <= """
            + str(i_rank)
            + """
                    and jockey = ( select jockey from exp011 where rcity = '"""
            + i_rcity
            + """' and rdate = '"""
            + i_rdate
            + """' and rno =  """
            + str(i_rno)
            + """ and rank = """
            + str(i_rank)
            + """) 
                ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 축마 가능성 check ")

    # print(result)

    return result


# 경주 변경 내용 update - 금주의경마 출전표변경
def set_changed_race(i_rcity, i_rdate, i_rno, r_content):
    # print(r_content)

    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")
        # print(index, items[0], len(items))

        if len(items) == 8:  # 말취소 아이템수 == 8
            if items[0] == "서울" or items[0] == "부경":
                # print(index, items)

                rdate = items[1][0:4] + items[1][5:7] + items[1][8:10]
                rno = items[2]
                horse = items[4]
                if horse[0:1] == "[":
                    horse = horse[3:]
                reason = items[7]

                # print(rdate, rno, horse, reason)

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """ update exp011
                                set reason = '"""
                        + reason
                        + """',
                                    r_rank = 99
                            where rdate = '"""
                        + rdate
                        + """' and rno = """
                        + str(rno)
                        + """ and horse = '"""
                        + horse
                        + """'
                        ; """
                    )

                    # print(strSql)
                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    awards = cursor.fetchall()

                    # connection.commit()
                    # connection.close()

                    # return render(request, 'base/update_popularity.html', context)
                    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

                except:
                    # connection.rollback()
                    print("Failed updating in exp011 : 경주마 취소")

        elif len(items) == 9:  # 기수변경 아이템수 == 9
            if items[0] == "서울" or items[0] == "부경":
                # print(index, items)

                rdate = items[1][0:4] + items[1][5:7] + items[1][8:10]
                rno = items[2]

                horse = items[4]
                if horse[0:1] == "[":
                    horse = horse[3:]

                jockey_old = items[5]
                jockey_new = items[6]

                # handy_old = items[]

                handy_new = items[7]
                reason = items[8]

                # print(rdate, rno, horse, jockey_old,
                #   handy_old, jockey_new, handy_new, reason)

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """ update exp011
                                set jockey = '"""
                        + jockey_new
                        + """',
                                    handycap = """
                        + handy_new
                        + """,
                                    jockey_old =  '"""
                        + jockey_old
                        + """',
                                    handycap_old = handycap,
                                    reason = '"""
                        + reason
                        + """'
                            where rdate = '"""
                        + rdate
                        + """' and rno = """
                        + str(rno)
                        + """ and horse = '"""
                        + horse
                        + """'
                        ; """
                    )

                    # print(strSql)
                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    awards = cursor.fetchall()

                    # connection.commit()
                    # connection.close()

                    # return render(request, 'base/update_popularity.html', context)
                    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

                except:
                    # connection.rollback()
                    print("Failed updating in exp011 : 기수변경")

    return len(lines)


# 경주 변경 내용 update - 기수변경
def set_changed_race_jockey(i_rcity, i_rdate, i_rno, r_content):
    # print(r_content)

    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")
        # print(index, items)

        if items[0]:
            rdate = items[0][0:4] + items[0][5:7] + items[0][8:10]
            rno = items[1]

            horse = items[3]
            if horse[0:1] == "[":
                horse = horse[3:]

            jockey_old = items[4]
            handy_old = items[5]
            jockey_new = items[6]
            handy_new = items[7]
            reason = items[8]

            # print(rdate, rno, horse, jockey_old,
            #   handy_old, jockey_new, handy_new, reason)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011
                            set jockey = '"""
                    + jockey_new
                    + """',
                                handycap = """
                    + handy_new
                    + """,
                                jockey_old =  '"""
                    + jockey_old
                    + """',
                                handycap_old = """
                    + handy_old
                    + """,
                                reason = '"""
                    + reason
                    + """'
                        where rdate = '"""
                    + rdate
                    + """' and rno = """
                    + str(rno)
                    + """ and horse = '"""
                    + horse
                    + """'
                    ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                # connection.commit()
                # connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                # connection.rollback()
                print("Failed updating in exp011 : 기수변경")

    return len(lines)


# 경주 변경 내용 update - 경주마 취소


def set_changed_race_horse(i_rcity, i_rdate, i_rno, r_content):
    # print(r_content)

    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")

        # print(index, items)

        if items[0]:
            rdate = items[1][0:4] + items[1][5:7] + items[1][8:10]
            rno = items[2]
            horse = items[4]
            if horse[0:1] == "[":
                horse = horse[3:]
            reason = items[7]

            # print(rdate, rno, horse, reason)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011
                              set reason = '"""
                    + reason
                    + """',
                                  r_rank = 99
                          where rdate = '"""
                    + rdate
                    + """' and rno = """
                    + str(rno)
                    + """ and horse = '"""
                    + horse
                    + """'
                      ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                # connection.commit()
                # connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed updating in exp011 : 경주마 취소")

    return len(lines)


# 경주 변경 내용 update - 경주마 체중


def set_changed_race_weight(i_rcity, i_rdate, i_rno, r_content):
    # print(r_content)

    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")

        # print(index, items, len(items))

        if items[0] and index == 0:
            rdate = items[0][0:4] + items[0][5:7] + items[0][8:10]
        elif items[0] and len(items) == 10:
            horse = items[1]
            if horse[0:1] == "[":
                horse = horse[3:]

            if int(items[3]) >= 0:
                items[3] = "+" + items[3]

            weight = items[2] + " " + items[3]

            # print(rdate, horse, weight)

            if items[2]:

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """ 
                                update exp011
                                set h_weight = '"""
                        + weight
                        + """'
                                where rdate = '"""
                        + rdate
                        + """' and horse = '"""
                        + horse
                        + """'
                            ; """
                    )

                    # print(strSql)
                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    awards = cursor.fetchall()

                    # connection.commit()
                    # connection.close()

                    # return render(request, 'base/update_popularity.html', context)
                    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

                except:
                    # connection.rollback()
                    print("Failed updating in exp011 : 경주마 체중")

    return len(lines)


# 경주 변경 내용 update - 경주순위


def set_changed_race_rank(i_rcity, i_rdate, i_rno, r_content):
    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")

        # print(index, items, len(items))

        if items[0] and index == 0:
            rdate = items[0][0:4] + items[0][6:8] + items[0][10:12]
            rno = items[0][19:21]
            if rno[1:2] == "경":
                rno = rno[0:1]
                rcity = items[0][23:25]
            else:
                rcity = items[0][24:26]

            if rcity == "부경":
                rcity = "부산"

        elif items[0] != "순위" and len(items) == 16:
            r_rank = items[0]
            horse = items[2]
            if horse[0:1] == "[":
                horse = horse[3:]

            alloc1r = items[13]
            alloc3r = items[14]

            # print(horse,  alloc1r, alloc3r)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011
                        set r_rank = """
                    + r_rank
                    + """,
                            alloc1r = '"""
                    + alloc1r
                    + """',
                            alloc3r = '"""
                    + alloc3r
                    + """'
                        where rdate = '"""
                    + rdate
                    + """' and horse = '"""
                    + horse
                    + """'
                ; """
                )

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                # connection.commit()
                # connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                # connection.rollback()
                print("Failed updating in exp011 : 경주마 순위")

        elif len(items) == 13:  # 서울 경주기록
            gate = items[1]
            corners = items[2]
            s1f = items[3][2:]
            g3f = items[10][2:]
            g1f = items[11][2:]
            record = items[12][0:6]

            # print(rno, rcity, gate,  remark, record)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011
                        set corners = '"""
                    + corners
                    + """',
                        r_record = '"""
                    + record
                    + """',
                        r_s1f = '"""
                    + s1f
                    + """',
                        r_g3f = '"""
                    + g3f
                    + """',
                        r_g1f = '"""
                    + g1f
                    + """'
                        where rcity = '"""
                    + rcity
                    + """' 
                    and rdate = '"""
                    + rdate
                    + """' 
                    and rno = """
                    + rno
                    + """
                    and gate = """
                    + gate
                    + """
                ; """
                )

                print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                # connection.commit()
                # connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                # connection.rollback()
                print("Failed updating in exp011 : 경주마 순위")

        elif len(items) == 12:  # 부산 경주기록
            gate = items[1]
            corners = items[2]
            s1f = items[3][2:]
            g3f = items[9][2:]
            g1f = items[10][2:]
            record = items[11][0:6]

            # print(rno, rcity, gate,  remark, record)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011
                        set corners = '"""
                    + corners
                    + """',
                        r_record = '"""
                    + record
                    + """',
                        r_s1f = '"""
                    + s1f
                    + """',
                        r_g3f = '"""
                    + g3f
                    + """',
                        r_g1f = '"""
                    + g1f
                    + """'
                        where rcity = '"""
                    + rcity
                    + """' 
                    and rdate = '"""
                    + rdate
                    + """' 
                    and rno = """
                    + rno
                    + """
                    and gate = """
                    + gate
                    + """
                ; """
                )

                print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                # connection.commit()
                # connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                # connection.rollback()
                print("Failed updating in exp011 : 경주마 순위")

    return len(lines)


# 수영조교 데이터 입력


def insert_train_swim(r_content):
    # print(r_content)

    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")

        # print(index, items)

        if items[0] and index == 0:
            tdate = items[0][0:4] + items[0][5:7] + items[0][8:10]
            print(tdate)
        elif items[0] and index >= 2:  # 제목(title) 라인 스킵
            team = items[1][0:2]
            trainer = items[1][3:-1]

            if team[1:] == "조":
                team = team[0:1]
            else:
                trainer = trainer[1:]

            horse = items[3]
            laps = items[4][0:1]
            print(trainer, horse, laps)

            # print(tdate, horse, team)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ insert swim 
                                ( horse, tdate, team, trainer, laps ) 
                                values ( '"""
                    + horse
                    + """', '"""
                    + tdate
                    + """', '"""
                    + team
                    + """', '"""
                    + trainer
                    + """', """
                    + laps
                    + """ )
                      ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                # connection.commit()
                # connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                # connection.rollback()
                print("Failed inserting in swim : 수영조교")

    return len(lines)


# 말진료현황 데이터 입력


def insert_horse_disease(r_content):
    # print(r_content)

    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")

        # print(index, items)

        if items[0]:
            num = items[0]
            tdate = items[1][0:4] + items[1][5:7] + items[1][8:10]
            horse = items[2]

            team = items[3][0:-1].zfill(2)
            hospital = items[4]
            disease = items[5]

            # print(tdate, horse, team, hospital, disease)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ delete from treat
                                where horse = '"""
                    + horse
                    + """'
                                and tdate = '"""
                    + tdate
                    + """'
                                and hospital = '"""
                    + hospital
                    + """'
                        ; """
                )

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                # connection.commit()
                # connection.close()

            except:
                # connection.rollback()
                print("Failed deleting in swim : 말 진료현황")

            try:
                cursor = connection.cursor()

                strSql = (
                    """ insert treat
                                ( rcity, horse, tdate, team, hospital, disease )
                                values ( '"""
                    + num
                    + """', '"""
                    + horse
                    + """', '"""
                    + tdate
                    + """', '"""
                    + team
                    + """', '"""
                    + hospital
                    + """', '"""
                    + disease
                    + """' )
                        ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

            except:
                connection.rollback()
                print("Failed inserting in swim : 말 진료현황")

    return len(lines)


# 경주 변경 내용 update - 경주순위


def set_race_review(i_rcity, i_rdate, i_rno, r_content):
    print(r_content)

    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")

        print(index, items)

        if items[0] and index == 0:
            rdate = items[0][0:4] + items[0][6:8] + items[0][10:12]
        elif items[0] and index >= 9:
            r_rank = items[0]
            horse = items[2]
            if horse[0:1] == "[":
                horse = horse[3:]

            print(rdate, horse, r_rank)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011
                              set r_rank = """
                    + r_rank
                    + """
                          where rdate = '"""
                    + rdate
                    + """' and horse = '"""
                    + horse
                    + """'
                      ; """
                )

                print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed updating in exp011 : 경주마 체중")


# 출전등록 시뮬레이션
def insert_race_simulation(rcity, rcount, r_content):
    # print(r_content)
    # print(rcount)

    lines = r_content.split("\n")

    for index, line in enumerate(lines):
        items = line.split("\t")

        if items[0]:
            if index == 0:
                rdate = items[0][0:4] + items[0][6:8] + items[0][10:12]
                rno = items[0][-5:]

                if rno[0:1] == "제":
                    rno = rno[1:2]
                else:
                    rno = rno[0:2]

                i_rno = int(rno) + 80

            elif index == 1:
                pos = items[0].find(" ")
                # print(pos)
                grade = items[0][0:pos]
                # print(grade)

                pos = items[0].find("M")
                # print(pos)
                distance = items[0][pos - 4 : pos]

                # print(distance)

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """ delete from exp010
                                    where rcity = '"""
                        + rcity
                        + """'
                                    and rdate = '"""
                        + rdate
                        + """'
                                    and rno = """
                        + str(i_rno)
                        + """
                            ; """
                    )

                    # print(strSql)

                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    awards = cursor.fetchall()

                    # connection.commit()
                    # connection.close()

                except:
                    # connection.rollback()
                    print("Failed deleting in exp010")

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """ insert into exp010
                                    ( rcity, rdate, rno, grade, distance, rcount )
                                values ( '"""
                        + rcity
                        + """', '"""
                        + rdate
                        + """', """
                        + str(i_rno)
                        + """, 
                                        '"""
                        + grade
                        + """', """
                        + distance
                        + """, '"""
                        + str(rcount)
                        + """' )
                            ; """
                    )

                    # print(strSql)

                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    awards = cursor.fetchall()

                    # connection.commit()
                    # connection.close()

                except:
                    # connection.rollback()
                    print("Failed inserting in exp010")

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """ delete from exp011
                                    where rcity = '"""
                        + rcity
                        + """'
                                    and rdate = '"""
                        + rdate
                        + """'
                                    and rno = """
                        + str(i_rno)
                        + """
                            ; """
                    )

                    # print(strSql)
                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    awards = cursor.fetchall()

                    # connection.commit()
                    # connection.close()

                except:
                    # connection.rollback()
                    print("Failed deleting in exp011")

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """ delete from exp012
                                    where rcity = '"""
                        + rcity
                        + """'
                                    and rdate = '"""
                        + rdate
                        + """'
                                    and rno = """
                        + str(i_rno)
                        + """
                            ; """
                    )

                    # print(strSql)
                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    awards = cursor.fetchall()

                    # connection.commit()
                    # connection.close()

                except:
                    # connection.rollback()
                    print("Failed deleting in exp012")

            else:
                # print( items[0], (items[0]))
                if index > 5 and items[0] >= "1" and items[0] <= "99":
                    print(items)
                    gate = items[0]
                    horse = items[1]
                    if horse[0:1] == "[":
                        horse = horse[3:]

                    # sql 튜플값 가져올때 [0][0]
                    jockey = get_jockey(horse)[0][0]

                    rating = items[2]
                    birthplace = items[4]
                    sex = items[5]
                    age = items[6]
                    trainer = items[7]
                    host = items[8]
                    # print(gate, horse, trainer, host)

                    try:
                        cursor = connection.cursor()

                        strSql = (
                            """ insert into exp011
                                        ( rcity, rdate, rno, gate, horse, rating, birthplace, h_sex, h_age, trainer, host, handycap, jockey  )
                                        values ( '"""
                            + rcity
                            + """', '"""
                            + rdate
                            + """', """
                            + str(i_rno)
                            + """, """
                            + gate
                            + """, '"""
                            + horse
                            + """', 
                                            """
                            + rating
                            + """ , '"""
                            + birthplace
                            + """' , '"""
                            + sex
                            + """' , """
                            + age
                            + """ , 
                                            '"""
                            + trainer
                            + """' , '"""
                            + host
                            + """', 57,  '"""
                            + jockey
                            + """'   )
                                        ; """
                        )

                        # print(strSql)

                        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                        awards = cursor.fetchall()

                        # connection.commit()
                        # connection.close()

                    except:
                        # connection.rollback()
                        print("Failed inserting in exp011")

                    try:
                        cursor = connection.cursor()

                        strSql = (
                            """ insert into exp012
                                        ( rcity, rdate, rno, gate, horse  )
                                        values ( '"""
                            + rcity
                            + """', '"""
                            + rdate
                            + """', """
                            + str(i_rno)
                            + """, """
                            + gate
                            + """, '"""
                            + horse
                            + """' )
                                        ; """
                        )

                        # print(strSql)

                        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                        awards = cursor.fetchall()

                        # connection.commit()
                        # connection.close()

                    except:
                        # connection.rollback()
                        print("Failed inserting in exp012")

                else:
                    pass

    return len(lines)


# 심판위원 Report
def insert_race_judged(rcity, r_content):
    # print(r_content)
    # print(rcount)

    lines = r_content.split("\n")

    rno = 0
    judged = ""
    committee = ""
    for index, line in enumerate(lines):
        items = line.split("\t")

        # print(items[0])

        if items[0]:
            if index == 0:
                # print(items[0][14:16])
                if items[0][14:16] == "서울":
                    rcity = "서울"
                else:
                    rcity = "부산"
                # print(items[1])

            elif index == 3:
                rdate = items[1][0:4] + items[1][6:8] + items[1][10:12]
            elif index > 5:
                # print(items[0][-4:])
                if items[0][-2:] == "경주":
                    rno = items[0][-4:][0:2]
                    judged = ""  # 경주별로 재경사항 초기화
                elif items[0][0:2] == "심판":
                    committee = items[1]
                elif items[0][0:1] == "●":
                    judged = judged + "\n" + items[0]
                else:
                    # if items[0][0:8] == '경주번호, 등급' or items[0][0:7] == '기수변경 내역' or items[0][0:5] == '제재 내역' :
                    if (
                        items[0][0:8] == "경주번호, 등급"
                        or items[0][0:7] == "기수변경 내역"
                        or items[0][0:5] == "제재 내역"
                        or items[0][0:4] == "약물검사"
                    ):
                        if rno == 0:  # 추가 재결사항 update
                            # print(rcity, rdate, rno, judged)
                            # print( judged)
                            # lst = judged.split('●')

                            # for i in range(1,len(lst)):             # 첫번째 라인 스킵
                            #     str = lst[i].replace(' ', '')
                            #     # print(str)

                            #     rdate_add = lst[i][0:5].replace(' ', '') + lst[i][6:8].replace(' ', '0') + lst[i][9:11].replace(' ', '0')
                            #     rno_add = lst[i][18:19]
                            #     judged_add = lst[i][22:]
                            #     ret = insert_race_judged_sql(rcity, rdate_add, int(rno_add), '', judged_add, committee)
                            pass

                        else:
                            # print(rdate)
                            ret = insert_race_judged_sql(
                                rcity, rdate, rno, judged, "", committee
                            )

    return len(lines)


def insert_race_judged_sql(rcity, rdate, rno, judged, judged_add, committee):
    # print(committee)
    try:
        cursor = connection.cursor()

        strSql = (
            """    select count(*) from rec013
                        where rcity = '"""
            + rcity
            + """'
                        and rdate = '"""
            + rdate
            + """'
                        and rno = """
            + str(rno)
            + """
                        ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        ret = cursor.fetchall()

        # print((ret[0][0]))      # 재결사항 입력 여부

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed select error in rec013")

    if ret[0][0] == 0:
        try:
            cursor = connection.cursor()

            strSql = (
                """ insert into rec013
                            ( rcity, rdate, rno, judged )
                            values ( '"""
                + rcity
                + """', '"""
                + rdate
                + """', """
                + str(rno)
                + """, '"""
                + judged
                + """' )
                            ; """
            )
            # print(strSql)

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            ret = cursor.fetchall()

            # connection.commit()
            # connection.close()

        except:
            # connection.rollback()
            print("Failed inserting in rec013 ")
    else:
        try:
            cursor = connection.cursor()

            strSql = (
                """ update rec013
                            set judged = '"""
                + judged
                + """'
                        where rcity = '"""
                + rcity
                + """' and rdate = '"""
                + rdate
                + """' and rno = """
                + str(rno)
                + """
                            ; """
            )
            # print(strSql)
            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            ret = cursor.fetchall()

            # connection.commit()
            # connection.close()

        except:
            # connection.rollback()
            print("Failed updating in rec013")

    return ret


def get_jockey(horse):  # 출전등록 시뮬레이션 - 기수 select
    try:
        cursor = connection.cursor()

        strSql = (
            """ select jockey from rec011
                        where horse = '"""
            + horse
            + """'
                        and rdate = ( select max(rdate) from rec011 where horse = '"""
            + horse
            + """')
                        ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        jockey = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed inserting in exp010")

    return jockey


# 주별 입상마 경주전개 현황
def get_weeks_status(rcity, rdate):
    try:
        cursor = connection.cursor()

        strSql = (
            """ select 
                    a.rcity, a.rdate, a.rno, b.rday, b.distance, b.grade, 
                    concat(b.dividing, ' ', b.rname, ' ', b.rcon1, ' ', b.rcon2), 
                    a.horse, a.jockey, a.trainer, a.host, a.h_weight, a.handycap, a.handycap - a.i_prehandy,
                    a.gate, a.rank, a.r_rank, 
                    replace( a.corners, ' ', '') corners,
                    a.r_s1f, a.r_g3f, a.r_g1f, 
                    a.s1f_rank, a.g3f_rank, a.g2f_rank, a.g1f_rank, 
                    a.cs1f, a.cg3f, a.cg1f, a.i_cycle, a.r_pop, a.alloc1r, a.alloc3r, a.complex, a.r_record, c.race_speed,
                    a.jt_per, a.jt_cnt, a.jt_1st, a.jt_2nd, a.jt_3rd, a.jockey_old, a.reason, a.h_sex, a.h_age, a.birthplace, 
                    a.j_per, a.t_per, a.rating, c.r2alloc, c.r333alloc, d.r_etc, d.gap, d.gap_b, c.weather, c.rstate, c.rmoisture, 
                    d.adv_track, c.r_judge, a.rating, d.h_cnt, d.h_mare, d.pop_rank, d.r_flag, passage_s1f
                FROM 
                    The1.exp011 a
                LEFT JOIN 
                    The1.exp010 b ON a.rcity = b.rcity AND a.rdate = b.rdate AND a.rno = b.rno
                LEFT OUTER JOIN 
                    The1.rec010 c ON a.rcity = c.rcity AND a.rdate = c.rdate AND a.rno = c.rno 
                LEFT OUTER JOIN 
                    The1.rec011 d ON a.rcity = d.rcity AND a.rdate = d.rdate AND a.rno = d.rno and a.gate = d.gate
                where a.rcity = '"""
            + rcity
            + """'
                and a.rdate between date_format(DATE_ADD('"""
            + rdate
            + """', INTERVAL - 10 DAY), '%Y%m%d') 
                and date_format(DATE_ADD('"""
            + rdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
            and ( a.r_rank between 1 and 1 )
            -- and ( a.r_rank between 1 and 3 or ( a.r_rank = 0 and a.rank <= 3 ) )
            order by a.rcity, a.rdate, a.rno, a.r_rank, a.rank
        ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed inserting in weeksStatus")

    return result


# thethe9 rank 1 입상현황
def get_thethe9_ranks(
    rcity,
    fdate,
    tdate,
    jockey,
    trainer,
    host,
    horse,
    r1,
    r2,
    rr1,
    rr2,
    gate,
    distance,
    handycap,
):
    try:
        cursor = connection.cursor()

        if r2 == 99 or r2 == "99":
            and_rank = ""
        else:
            and_rank = " and a.rank between " + str(r1) + " and " + str(r2)

        if rr2 == 99 or r2 == "99":
            and_r_rank = ""
        else:
            and_r_rank = " and a.r_rank between " + str(rr1) + " and " + str(rr2)

        if gate == 0 or gate == "0":
            and_gate = ""
        else:
            and_gate = " and a.gate = " + str(gate)

        if distance == 0 or distance == "0":
            and_distance = ""
        else:
            and_distance = " and b.distance = " + str(distance)

        if handycap == 0 or handycap == "0":
            and_handycap = ""
        else:
            and_handycap = (
                " and a.handycap between "
                + handycap[0:2]
                + ".0"
                + " and "
                + handycap[0:2]
                + ".5"
            )

        strSql = (
            """ SELECT 
                    a.rcity, a.rdate, a.rno, b.rday, b.distance, b.grade, 
                    concat(b.dividing, ' ', b.rname, ' ', b.rcon1, ' ', b.rcon2), 
                    a.horse, a.jockey, a.trainer, a.host, a.h_weight, a.handycap, a.handycap - a.i_prehandy,
                    a.gate, a.rank, a.r_rank, 
                    replace( a.corners, ' ', '') corners,
                    a.r_s1f, a.r_g3f, a.r_g1f, 
                    a.s1f_rank, a.g3f_rank, a.g2f_rank, a.g1f_rank, 
                    a.cs1f, a.cg3f, a.cg1f, a.i_cycle, a.r_pop, a.alloc1r, a.alloc3r, a.complex, a.r_record, c.race_speed,
                    a.jt_per, a.jt_cnt, a.jt_1st, a.jt_2nd, a.jt_3rd, a.jockey_old, a.reason, a.h_sex, a.h_age, a.birthplace, 
                    a.j_per, a.t_per, a.rating, c.r2alloc, c.r333alloc, d.r_etc, d.gap, d.gap_b, c.weather, c.rstate, c.rmoisture, 
                    d.adv_track, c.r_judge, a.rating, d.h_cnt, d.h_mare, d.pop_rank, d.r_flag, passage_s1f
                FROM 
                    The1.exp011 a
                LEFT JOIN 
                    The1.exp010 b ON a.rcity = b.rcity AND a.rdate = b.rdate AND a.rno = b.rno
                LEFT OUTER JOIN 
                    The1.rec010 c ON a.rcity = c.rcity AND a.rdate = c.rdate AND a.rno = c.rno 
                LEFT OUTER JOIN 
                    The1.rec011 d ON a.rcity = d.rcity AND a.rdate = d.rdate AND a.rno = d.rno and a.gate = d.gate
                WHERE a.rcity like '%"""
            + rcity
            + """%'
                and a.rdate between '"""
            + fdate
            + """' and '"""
            + tdate
            + """'
                """
            + and_rank
            + """
                """
            + and_r_rank
            + """
                """
            + and_gate
            + """
                """
            + and_distance
            + """
                """
            + and_handycap
            + """
                -- and a.rank between """
            + str(r1)
            + """ and """
            + str(r2)
            + """
                -- and a.r_rank between """
            + str(rr1)
            + """ and """
            + str(rr2)
            + """
                and a.jockey like '%"""
            + jockey
            + """%'
                and a.trainer like '%"""
            + trainer
            + """%'
                and a.host like '%"""
            + host
            + """%'
                and a.horse like '%"""
            + horse
            + """%'
            order by a.rdate desc, b.rtime desc, a.r_rank, a.rank
        ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in thethe9_ranks")

    return result


# thethe9 rank 1 입상현황
def get_thethe9_ranks_jockey(
    rcity,
    fdate,
    tdate,
    jockey,
    trainer,
    host,
    jockey_b,
    r1,
    r2,
    rr1,
    rr2,
    gate,
    distance,
    handycap,
):
    try:
        cursor = connection.cursor()

        if r2 == 99 or r2 == "99":
            and_rank = ""
        else:
            and_rank = " and a.rank between " + str(r1) + " and " + str(r2)

        if rr2 == 99 or rr2 == "99":
            and_r_rank = ""
        else:
            and_r_rank = " and a.r_rank between " + str(rr1) + " and " + str(rr2)

        # print(rr1, rr2, and_r_rank) 
        
        if gate == 0 or gate == "0":
            and_gate = ""
        else:
            and_gate = " and a.gate = " + str(gate)

        if distance == 0 or distance == "0":
            and_distance = ""
        else:
            and_distance = " and b.distance = " + str(distance)

        if handycap == 0 or handycap == "0":
            and_handycap = ""
        else:
            and_handycap = (
                " and a.handycap between "
                + handycap[0:2]
                + ".0"
                + " and "
                + handycap[0:2]
                + ".5"
            )
            
        if jockey_b == 0 or jockey_b == "" or jockey_b == "%":
            and_jockey_b = ""
        else:
            and_jockey_b = (
                " and ( a.rcity, a.rdate, a.rno ) in ( select rcity, rdate, rno from rec010 where rcity like '%' and rdate between '" + fdate + "' and '"
                + tdate
                + "' and jockeys like '%"
                + jockey_b
                + "%')"
            )

        # print(jockey_b)
        # print(and_jockey_b)
        strSql = (
            """ SELECT 
                    a.rcity, a.rdate, a.rno, b.rday, b.distance, b.grade, 
                    concat(b.dividing, ' ', b.rname, ' ', b.rcon1, ' ', b.rcon2), 
                    a.horse, a.jockey, a.trainer, a.host, a.h_weight, a.handycap, a.handycap - a.i_prehandy,
                    a.gate, a.rank, a.r_rank, 
                    replace( a.corners, ' ', '') corners,
                    a.r_s1f, a.r_g3f, a.r_g1f, 
                    a.s1f_rank, a.g3f_rank, a.g2f_rank, a.g1f_rank, 
                    a.cs1f, a.cg3f, a.cg1f, a.i_cycle, a.r_pop, a.alloc1r, a.alloc3r, a.complex, a.r_record, c.race_speed,
                    a.jt_per, a.jt_cnt, a.jt_1st, a.jt_2nd, a.jt_3rd, a.jockey_old, a.reason, a.h_sex, a.h_age, a.birthplace, 
                    a.j_per, a.t_per, a.rating, c.r2alloc, c.r333alloc, d.r_etc, d.gap, d.gap_b, c.weather, c.rstate, c.rmoisture, d.adv_track, 
                    c.r_judge, a.rating, d.h_cnt, d.h_mare, d.pop_rank, d.r_flag, passage_s1f
                FROM 
                    The1.exp011 a
                LEFT JOIN 
                    The1.exp010 b ON a.rcity = b.rcity AND a.rdate = b.rdate AND a.rno = b.rno
                LEFT OUTER JOIN 
                    The1.rec010 c ON a.rcity = c.rcity AND a.rdate = c.rdate AND a.rno = c.rno 
                LEFT OUTER JOIN 
                    The1.rec011 d ON a.rcity = d.rcity AND a.rdate = d.rdate AND a.rno = d.rno and a.gate = d.gate
                WHERE a.rcity like '%'
                and a.rdate between '"""
            + fdate
            + """' and date_format(DATE_ADD('"""
            + tdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                """
            + and_rank
            + """
                """
            + and_r_rank
            + """
                """
            + and_gate
            + """
                """
            + and_distance
            + """
                """
            + and_handycap
            + """
                """
            + and_jockey_b
            + """
                and a.jockey like '%"""
            + jockey
            + """%'
                and a.trainer like '%"""
            + trainer
            + """%'
                and a.host like '%"""
            + host
            + """%'
                
            order by a.rdate desc, b.rtime, a.r_rank, a.rank
        ; """
        )

        print(strSql) 
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in thethe9_ranks_jockey")

    return result

# thethe9 rank 1 입상현황
def get_thethe9_ranks_multi(
    rcity,
    fdate,
    tdate,
    jockey,
    trainer,
    host,
    jockey_b,
    r1,
    r2,
    rr1,
    rr2,
    gate,
    distance,
    handycap,
    start
):
    try:
        cursor = connection.cursor()

        if r2 == 99 or r2 == "99":
            and_rank = ""
        else:
            and_rank = " and d.pop_rank between " + str(r1) + " and " + str(r2)

        if rr2 == 99 or rr2 == "99":
            and_r_rank = ""
        else:
            and_r_rank = " and a.r_rank between " + str(rr1) + " and " + str(rr2)

        # print(rr1, rr2, and_r_rank)

        if gate == 0 or gate == "0":
            and_gate = ""
        else:
            and_gate = " and a.gate = " + str(gate)

        if distance == 0 or distance == "0":
            and_distance = ""
        else:
            and_distance = " and b.distance = " + str(distance)

        if start == 0 or start == "" or start == "%":
            and_corners = ""
        else:
            and_corners = " and a.corners like '" + start + "-%'"

        if handycap == 0 or handycap == "0":
            and_handycap = ""
        else:
            and_handycap = (
                " and a.handycap between "
                + handycap[0:2]
                + ".0"
                + " and "
                + handycap[0:2]
                + ".5"
            )

        if jockey_b == 0 or jockey_b == "" or jockey_b == "%":
            and_jockey_b = ""
        else:
            and_jockey_b = (
                " and ( a.rcity, a.rdate, a.rno ) in ( select rcity, rdate, rno from rec010 where rcity like '%' and rdate between '" + fdate + "' and '"
                + tdate
                + "' and jockeys like '%"
                + jockey_b
                + "%')"
            )

        # print(jockey_b)
        # print(and_jockey_b)
        strSql = (
            """ SELECT 
                    a.rcity, a.rdate, a.rno, b.rday, b.distance, b.grade, 
                    concat(b.dividing, ' ', b.rname, ' ', b.rcon1, ' ', b.rcon2), 
                    a.horse, a.jockey, a.trainer, a.host, a.h_weight, a.handycap, a.handycap - a.i_prehandy,
                    a.gate, a.rank, a.r_rank, 
                    replace( a.corners, ' ', '') corners,
                    a.r_s1f, a.r_g3f, a.r_g1f, 
                    a.s1f_rank, a.g3f_rank, a.g2f_rank, a.g1f_rank, 
                    a.cs1f, a.cg3f, a.cg1f, a.i_cycle, a.r_pop, a.alloc1r, a.alloc3r, a.complex, a.r_record, c.race_speed,
                    a.jt_per, a.jt_cnt, a.jt_1st, a.jt_2nd, a.jt_3rd, a.jockey_old, a.reason, a.h_sex, a.h_age, a.birthplace, 
                    a.j_per, a.t_per, a.rating, c.r2alloc, c.r333alloc, d.r_etc, d.gap, d.gap_b, c.weather, c.rstate, c.rmoisture, d.adv_track, 
                    c.r_judge, a.rating, d.h_cnt, d.h_mare, d.pop_rank, d.r_flag, passage_s1f
                FROM 
                    The1.exp011 a
                LEFT JOIN 
                    The1.exp010 b ON a.rcity = b.rcity AND a.rdate = b.rdate AND a.rno = b.rno
                LEFT OUTER JOIN 
                    The1.rec010 c ON a.rcity = c.rcity AND a.rdate = c.rdate AND a.rno = c.rno 
                LEFT OUTER JOIN 
                    The1.rec011 d ON a.rcity = d.rcity AND a.rdate = d.rdate AND a.rno = d.rno and a.gate = d.gate
                WHERE a.rcity like '%'
                and a.rdate between '"""
            + fdate
            + """' and date_format(DATE_ADD('"""
            + tdate
            + """', INTERVAL + 3 DAY), '%Y%m%d')
                """
            + and_rank
            + """
                """
            + and_r_rank
            + """
                """
            + and_gate
            + """
                """
            + and_distance
            + """
                """
            + and_handycap
            + """
                """
            + and_jockey_b
            + """
                """
            + and_corners
            + """
                and a.jockey like '%"""
            + jockey
            + """%'
                and a.trainer like '%"""
            + trainer
            + """%'
                and a.host like '%"""
            + host
            + """%'

            order by a.rdate desc, b.rtime desc, a.r_rank, a.rank
        ; """
        )

        # print(strSql) 
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in thethe9_ranks_jockey")

    return result
