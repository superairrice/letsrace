import datetime
import json
from django.db import connection
import pandas as pd
from requests import session

from django.db.models import Count, Max, Min, Q
from base.models import Exp011


def get_paternal_dist(rcity, rdate, rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT a.gate, a.rank, a.horse, 
                    b.paternal, c.distance,
                    sum(r1) r1,
                    sum(r2) r2,
                    sum(r3) r3,
                    sum(rtot) rtot
                FROM exp011	a,
                    horse		b right outer join paternal c on b.paternal = c.paternal 
                where  a.horse = b.horse
                AND a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
                
                group by a.gate, a.rank, a.horse, b.paternal , c.distance
                order by a.rank, a.gate, c.distance
            ; """

        # print(strSql)
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_paternal(rcity, rdate, rno, distance):

    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT a.gate, a.rank, a.horse, 
                    b.paternal, 
                    sum( if(c.distance = """ + str(distance) + """, r1, 0 )) rd1,
                    sum( if(c.distance = """ + str(distance) + """, r2, 0 )) rd2,
                    sum( if(c.distance = """ + str(distance) + """, r3, 0 )) rd3,
                    sum( if(c.distance = """ + str(distance) + """, rtot, 0)) rdtot,
                    
                    sum(r1) r1,
                    sum(r2) r2,
                    sum(r3) r3,
                    sum(rtot) rtot,
                    b.price/1000, b.tot_prize/1000000
                FROM exp011	a,
                    horse		b right outer join paternal c on b.paternal = c.paternal 
                where  a.horse = b.horse
                AND a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
                
                group by a.gate, a.rank, a.horse, b.paternal 
                order by a.rank, a.gate, a.horse, b.paternal
            ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_judged_jockey(rcity, rdate, rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT distinct a.rank, a.gate, a.horse, b.rdate, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason
                FROM exp011     a,
                      rec015     b
                where a.jockey = b.jockey 
                AND b.t_sort = '기수'
                AND b.rdate between date_format(DATE_ADD('""" + rdate + """', INTERVAL - 100 DAY), '%Y%m%d') and '""" + rdate + """'
                AND a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
                ORDER BY b.rdate desc

            #   union

            #   SELECT distinct a.rank, a.gate, a.horse, b.rdate, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason
            #     FROM exp011     a,
            #           rec015     b
            #     where a.jockey = b.jockey 
            #     AND b.t_sort = '조교사'
            #     AND b.rdate between date_format(DATE_ADD('""" + rdate + """', INTERVAL - 100 DAY), '%Y%m%d') and '""" + rdate + """'
            #     AND a.rcity = '""" + rcity + """'
            #     AND a.rdate = '""" + rdate + """'
            #     AND a.rno = """ + str(rno) + """

            ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_judged_horse(rcity, rdate, rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT distinct a.rank, a.gate, a.horse, b.rdate, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason
                FROM exp011     a,
                      rec015     b
                where a.horse = b.horse 
                AND b.rdate between date_format(DATE_ADD('""" + rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and '""" + rdate + """'
                AND a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
                AND b.rdate < '""" + rdate + """'

              order by a.rank, b.rdate desc
            ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_judged(rcity, rdate, rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT distinct a.rank, a.gate, a.horse, b.horse, b.jockey, b.trainer, b.t_sort, b.t_type, b.t_detail, b.t_reason
                FROM rec011	a right outer join 
                    rec015	b on a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno and a.horse = b.horse
                where a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
              order by a.rank
            ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        rec015 = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in rec015")

    try:
        cursor = connection.cursor()

        strSql = """ 
            SELECT judged
            FROM rec013
                where rcity = '""" + rcity + """'
                AND rdate = '""" + rdate + """'
                AND rno = """ + str(rno) + """
            ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        rec013 = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in rec013")

    return rec015, rec013


def get_pedigree(rcity, rdate, rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT a.gate, a.rank, a.r_rank, a.r_pop, a.horse, a.jockey, a.trainer,	a.host,
                    ( a.year_1st + a.year_2nd + a.year_3rd )*100/a.year_race h_3rd, 
                    a.year_race h_tot, 
                    b.paternal, 
                    b.maternal,
                    (	select sum( year_race ) from horse where paternal = b.paternal ) p_tot,
                    (	select sum( year_1st + year_2nd + year_3rd ) from horse where paternal = b.paternal ) p_3rd,
                    (	select sum( year_race ) from horse where maternal = b.maternal ) m_tot,
                    (	select sum( year_1st + year_2nd + year_3rd ) from horse where maternal = b.maternal ) m_3rd,
                    ifnull(gear1, '') gear1, 
                    ifnull(gear2, '') gear2, 
                    blood1, 
                    blood2, 
                    treat1, 
                    treat2, 
                    price/10000000
                FROM exp011	a,
                    horse		b,
                    exp012 c
                WHERE a.horse = b.horse
                AND a.rcity = c.rcity
                AND a.rdate = c.rdate
                AND a.rno = c.rno
                AND a.gate = c.gate
                AND a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
                order by a.rank, a.gate
            ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_weeks(i_rdate, i_awardee):

    try:
        cursor = connection.cursor()

        strSql = """ 
            select b.rcity, a.rcity rcity_in, b.""" + i_awardee + """, rcnt, r1cnt, r2cnt, r3cnt, r4cnt, r5cnt, rmonth1, rmonth2, rmonth3, rdate1, rdate2, rdate3,
                  ( select year_per from """ + i_awardee + """_w 
                    where wdate = ( select max(wdate) from """ + i_awardee + """_w where wdate <= '""" + i_rdate + """' ) 
                      and """ + i_awardee + """ = b.""" + i_awardee + """ ) year_per
              from
              (
                select """ + i_awardee + """ , sum(r_cnt) rcnt, sum(r1_cnt) r1cnt, sum(r2_cnt) r2cnt, sum(r3_cnt) r3cnt, sum(r4_cnt) r4cnt, sum(r5_cnt) r5cnt,
                              (select max(rcity) from """ + i_awardee + """  where a.""" + i_awardee + """ = """ + i_awardee + """ ) rcity,
                              sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                              sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                              sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                      from award a
                      where rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                        and """ + i_awardee + """ in (  select distinct """ + i_awardee + """ from exp011 a where rdate in ( select distinct rdate from racing ) )
                      group by """ + i_awardee + """
        	    ) a right outer join 
              (
                select rcity,""" + i_awardee + """, 
                        sum(if( rdate = '""" + i_rdate + """', 1, 0 )) rdate1, 
                        sum(if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) + INTERVAL 1 DAY,'%Y%m%d'), 1, 0 )) rdate2, 
                        sum(if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) + INTERVAL 2 DAY,'%Y%m%d'), 1, 0 )) rdate3
                  from exp011
                where rdate in ( select distinct rdate from racing )
                group by rcity, """ + i_awardee + """
              ) b on a.""" + i_awardee + """ = b.""" + i_awardee + """
              order by rcity desc, rmonth1 + rmonth2 + rmonth3 desc
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ 
                select rcity,""" + i_awardee + """ awardee, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey j_name, trainer t_name, host h_name, r_pop, distance, handycap,
                        cs1f, cg3f, cg2f, cg1f, complex, if ( i_prehandy = 0.0, 0, handycap - i_prehandy) i_pre
                  from expect
                where rdate in ( select distinct rdate from racing )
                order by rcity, rdate, rno, rank, gate
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        weeks = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return weeks


def get_race(i_rdate, i_awardee):

    try:
        cursor = connection.cursor()

        strSql = """ 
                select rcity, rdate, rno, rday, rseq,distance, rcount, grade, dividing, rname, rcon1, rcon2, rtime, r1award/1000, r2award/1000, r3award/1000, r4award/1000, r5award/1000, sub1award/1000, sub2award/1000, sub3award/1000,
                      ( select count(*) from rboard where a.rcity = rcity and a.rdate = rdate and a.rno = rno ) rcnt
                  from exp010 a 
                where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 3 DAY), '%Y%m%d')
                order by rdate, rtime
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        racings = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in exp010 : 주별 경주현황")

    try:
        cursor = connection.cursor()

        strSql = """ 
                select rcity,""" + i_awardee + """ awardee, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey j_name, trainer t_name, host h_name, r_pop, distance, handycap, jt_per
                  from expect
                where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                order by rdate, rcity, rno
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        race_detail = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in expect : 경주별 Detail(약식)) ")

    try:
        cursor = connection.cursor()

        strSql = """ 
                select rcity, rdate, rno, username, memo, board, rcnt, scnt, updated, created
                  from rboard
                where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 3 DAY), '%Y%m%d')
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        race_board = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in expect : 경주별 Detail(약식)) ")

    return racings, race_detail, race_board


def get_training(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = """ select gate, rank, horse, jockey, trainer,
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
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d14
                        from training a right outer join  ( select gate, rank, horse, jockey, trainer from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.horse = b.horse
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d') and '""" + i_rdate + """'
                      ) a
                      group by gate, rank, horse, jockey, trainer
                      order by rank, gate
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ select gate, rank, horse, jockey, trainer,
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
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,

                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,

                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
                        from train a right outer join  ( select gate, rank, horse, jockey, trainer from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.horse = b.horse
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d') and '""" + i_rdate + """'
                      ) a
                      group by gate, rank, horse, jockey, trainer
                      order by rank, gate
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ select gate, rank, r_rank, b.horse, jockey, trainer, s_audit, rider, rider_k, judge, tdate
                                              
                      from
                      (
                          select '출발조교'		s_audit,
                                horse		horse, 
                                rider		rider, 
                                rider_k		rider_k,
                                judge		judge, 
                                tdate		tdate
                            from start_train
                          where tdate between DATE_FORMAT( subdate( str_to_date( '""" + i_rdate + """', '%Y%m%d' ) , 100 ),'%Y%m%d')  and '""" + i_rdate + """' 
                          union all
                          select '발주심사'		s_audit,
                                horse		horse, 
                                rider		rider, 
                                rider_k		rider_k,
                                judge		judge, 
                                rdate		tdate
                            from start_audit
                          where rdate between DATE_FORMAT( subdate( str_to_date( '""" + i_rdate + """', '%Y%m%d' ) , 100 ),'%Y%m%d')  and '""" + i_rdate + """' 
                        ) a right outer join  ( select gate, rank, r_rank, horse, jockey, trainer from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.horse = b.horse
                      order by rank, tdate desc
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight, distance, grade, rating, dividing,
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
                              where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) ) b 
                        where a.horse = b.horse
                        and tdate between date_format(DATE_ADD(rdate, INTERVAL - 12 DAY), '%Y%m%d') and rdate
                      ) a
                      group by rdate, gate, rank, r_rank, r_pop, horse, jockey, trainer
                      order by rdate desc, rank, gate
                        ;"""
        # print(strSql)
        
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()
        
        

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result

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

        strSql = """ select rcity, rdate, rno, gate, rank, r_rank, r_pop, horse, jockey, trainer, j_per, t_per, jt_per, h_weight,
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
                                where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) ) b 
                        where a.horse = b.horse
                        and tdate between date_format(DATE_ADD(rdate, INTERVAL - 14 DAY), '%Y%m%d') and rdate
                        ) a
                        group by rdate, gate, rank, r_rank, r_pop, horse, jockey, trainer
                        order by rdate desc, rank, gate
                        ;"""

        # print(strSql)
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ 
                    select horse, tdate, max(disease) disease, max(laps) laps,  max(t_time) t_time, max(canter) canter,  max(strong) strong, 
                            audit, max(rider) rider, max(judge) judge,
                            weekday(tdate) days
                    from
                    (
                        select distinct  horse, tdate, if( length(disease) > 2, trim(disease), trim(hospital) ) disease, '' laps,  '' t_time, '' canter,  '' strong, '' audit, '' rider, '' judge
                        from treat 
                        where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """ )
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 99 DAY), '%Y%m%d') and '""" + i_rdate + """'
                        union all
                        select horse, tdate, '', laps, '', '', '', '', '', ''
                        from swim 
                        where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """ )
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 99 DAY), '%Y%m%d') and '""" + i_rdate + """'
                        union all
                        select horse, tdate, '', '', t_time, canter, strong, '', '', ''
                        from train 
                        where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """ )
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 99 DAY), '%Y%m%d') and '""" + i_rdate + """'
                        union all
                        select horse, tdate, '', '', '', '', '', '출발', rider, judge
                        from start_train 
                        where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """ )
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 99 DAY), '%Y%m%d') and '""" + i_rdate + """'
                        union all
                        select horse, rdate, '', '', '', '', '', '발주', rider, judge
                        from start_audit 
                        where horse in ( select horse from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """ )
                        and rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 99 DAY), '%Y%m%d') and '""" + i_rdate + """'
                    ) a
                    group by horse, tdate, audit
                    order by tdate desc
                    
            ;"""

        # print(strSql)
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 마필병력 히스토리 ")

    return result


def get_award(i_rdate, i_awardee):
    try:
        cursor = connection.cursor()

        strSql = """ select """ + i_awardee + """, count(0) rcnt, (select max(rcity) from """ + i_awardee + """  where a.""" + i_awardee + """ = """ + i_awardee + """ ) rcity,
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a
                    where rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    and """ + i_awardee + """ in ( select """ + i_awardee + """ from exp011 where rdate = '""" + i_rdate + """')
                    group by """ + i_awardee + """
                    order by sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) +
                             sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) +
                             sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) desc
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ 
              select gate, rank, max(jockey), sum(j_rcnt), sum(j_rmonth1), sum(j_rmonth2), sum(j_rmonth3),
                          max(trainer), sum(t_rcnt), sum(t_rmonth1), sum(t_rmonth2), sum(t_rmonth3), 
                          max(host), sum(h_rcnt), sum(h_rmonth1), sum(h_rmonth2), sum(h_rmonth3)
                from
                  (
                    select gate, rank, b.jockey, count(0) j_rcnt, 
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) j_rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) j_rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) j_rmonth3,
                            '' trainer, 0 t_rcnt, 0 t_rmonth1, 0 t_rmonth2, 0 t_rmonth3,
                            '' host, 0 h_rcnt, 0 h_rmonth1, 0 h_rmonth2, 0 h_rmonth3
                    from award a right outer join  ( select gate, rank, jockey from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.jockey = b.jockey
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by jockey, gate, rank
                    
                    union all

                    select gate, rank, '', 0, 0, 0, 0,
                            b.trainer, count(0) rcnt, 
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3,
                            '', 0, 0, 0, 0
                    from award a right outer join  ( select gate, rank, trainer from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.trainer = b.trainer
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by trainer, gate, rank

                    union all

                    select  gate, rank, '', 0, 0, 0, 0, '', 0, 0, 0, 0, b.host, count(0) rcnt, 
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, rank, host from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.host = b.host
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by host, gate, rank
                  ) a
                  group by gate, rank
                  order by rank, gate
                ; """

        strSql1 = """ 
              select rflag, gate, jockey, rcnt, rcity, rmonth1, rmonth2, rmonth3
                from
                  (
                    select 1 rflag, gate, b.jockey, count(0) rcnt, (select max(rcity) from jockey  where a.jockey = jockey ) rcity,
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, jockey from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.jockey = b.jockey
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by jockey, gate
                    
                    union all

                    select 2 rflag, gate, b.trainer, count(0) rcnt, (select max(rcity) from trainer  where a.trainer = trainer ) rcity,
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, trainer from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.trainer = b.trainer
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by trainer, gate

                    union all

                    select 3 rflag,  gate, b.host, count(0) rcnt, (select max(rcity) from host  where a.host = host ) rcity,
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, host from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.host = b.host
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by host, gate
                  ) a
                  order by gate, rflag
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        awards = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return awards


def get_last2weeks(i_rdate, i_awardee):

    try:
        cursor = connection.cursor()

        strSql = """ 
            select aa.rcity, aa.rcity_in, aa.""" + i_awardee + """, rcnt, r1cnt, r2cnt, r3cnt, r4cnt, r5cnt, rmonth1, rmonth2, rmonth3, rdate1, rdate2, rdate3,

                  lw1_fri1, lw1_fri2, lw1_fri3, lw1_fri,
                  lw1_sat1, lw1_sat2, lw1_sat3, lw1_sat,
                  lw1_sun1, lw1_sun2, lw1_sun3, lw1_sun,
                  lw2_fri1, lw2_fri2, lw2_fri3, lw2_fri,
                  lw2_sat1, lw2_sat2, lw2_sat3, lw2_sat,
                  lw2_sun1, lw2_sun2, lw2_sun3, lw2_sun, award,
                  
                  ( select year_1st from """ + i_awardee + """_w 
                    where wdate = ( select max(wdate) from """ + i_awardee + """_w where wdate < '""" + i_rdate + """' ) 
                      and """ + i_awardee + """ = aa.""" + i_awardee + """ ) year_per,

                  ( select count(*) from rec011
                    where rdate between '""" + i_rdate[0:4] + """0101'  and '""" + i_rdate + """%' 
                    and rank = 1
                    and alloc1r > 0 
                    and """ + i_awardee + """ = aa.""" + i_awardee + """ ) wcnt
              from
              (
                select b.rcity, a.rcity rcity_in, b.""" + i_awardee + """, rcnt, r1cnt, r2cnt, r3cnt, r4cnt, r5cnt, rmonth1, rmonth2, rmonth3, rdate1, rdate2, rdate3
                  from
                    (
                      select """ + i_awardee + """ , sum(r_cnt) rcnt, sum(r1_cnt) r1cnt, sum(r2_cnt) r2cnt, sum(r3_cnt) r3cnt, sum(r4_cnt) r4cnt, sum(r5_cnt) r5cnt,
                                    (select max(rcity) from """ + i_awardee + """  where a.""" + i_awardee + """ = """ + i_awardee + """ ) rcity,
                                    sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                                    sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                                    sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                            from award a
                            where rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                              and """ + i_awardee + """ in (  select distinct """ + i_awardee + """ from exp011 a where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 3 DAY), '%Y%m%d') )
                            group by """ + i_awardee + """
                    ) a right outer join 
                    (
                      select rcity,""" + i_awardee + """, 
                              sum(if( rday = '금', 1, 0 )) rdate1, 
                              sum(if( rday = '토', 1, 0 )) rdate2, 
                              sum(if( rday = '일', 1, 0 )) rdate3
                              
                        from expect
                      where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 3 DAY), '%Y%m%d')
                      group by rcity, """ + i_awardee + """
                    ) b on a.""" + i_awardee + """ = b.""" + i_awardee + """
                ) aa left outer join 
                (
                  select """ + i_awardee + """, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 7 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw1_fri1, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 7 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw1_fri2, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 7 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw1_fri3, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 7 DAY,  '%Y%m%d'), 1, 0)) lw1_fri, 

                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 6 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw1_sat1, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 6 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw1_sat2, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 6 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw1_sat3, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 6 DAY,  '%Y%m%d'), 1, 0)) lw1_sat, 

                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 5 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw1_sun1, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 5 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw1_sun2, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 5 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw1_sun3, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 5 DAY,  '%Y%m%d'), 1, 0)) lw1_sun, 
                      
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw2_fri1, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw2_fri2, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw2_fri3, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d'), 1, 0)) lw2_fri, 

                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 13 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw2_sat1, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 13 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw2_sat2, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 13 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw2_sat3, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 13 DAY,  '%Y%m%d'), 1, 0)) lw2_sat, 

                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 12 DAY,  '%Y%m%d'), if(a.rank = 1, 1, 0), 0)) lw2_sun1, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 12 DAY,  '%Y%m%d'), if(a.rank = 2, 1, 0), 0)) lw2_sun2, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 12 DAY,  '%Y%m%d'), if(a.rank = 3, 1, 0), 0)) lw2_sun3, 
                      sum( if( rdate = DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 12 DAY,  '%Y%m%d'), 1, 0)) lw2_sun, 
                      
                      sum( if(a.rank = 1, r1award + sub1award, 0) +
                      if(a.rank = 2, r2award + sub2award, 0) +
                      if(a.rank = 3, r3award + sub3award, 0) +
                      if(a.rank = 4, r4award, 0) +
                      if(a.rank = 5, r5award, 0) ) award
                    from record a
                  where rdate between DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d') and  DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 1 DAY,  '%Y%m%d')
                    and grade != '주행검사'
                  group by """ + i_awardee + """
                ) c on aa.""" + i_awardee + """ = c.""" + i_awardee + """
                order by rcity desc, wcnt desc, year_per desc
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        weeks = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return weeks


def get_last2weeks_loadin(i_rdate):

    try:
        cursor = connection.cursor()

        strSql = """ 
                    select 'J' flag, jockey, tot_1st, cast(load_in as decimal) 
                    from jockey_w 
                    where wdate = ( select max(wdate) from jockey_w where wdate < '""" + i_rdate + """' ) 
                    union all 
                    select 'T', trainer, tot_1st, team
                    from trainer_w 
                    where wdate = ( select max(wdate) from trainer_w where wdate < '""" + i_rdate + """' ) 
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        results = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기승가능중량")

    return results


def get_status_training(i_rdate):
    try:
        cursor = connection.cursor()

        strSql = """ select rcity, rdate, rno, rday, gate, rank, r_rank, r_pop, horse, trainer, jockey, jt_per, handycap,
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
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), substr(t_time,3,2), 0 ) d14
                        from training a right outer join  
                        ( 
                          select rcity, rdate, rday, rno, trainer, jockey, jt_per, gate, rank, r_rank, r_pop, horse, handycap
                            from expect 
                          where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 3 DAY), '%Y%m%d')
                        ) b on a.horse = b.horse
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d') and '""" + i_rdate + """'
                      ) a
                      group by rcity, rdate, rday, rno, gate, rank, horse
                      order by rcity, rdate, rday, rno, gate
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ select rcity, rdate, rno, rday, gate, rank, r_rank, r_pop, horse, trainer, jockey, jt_per, handycap,
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
                        select b.rcity, b.rdate, b.rday, b.rno, b.gate, b.rank, b.r_rank, b.r_pop, a.horse, b.trainer, b.jockey, b.jt_per, b.handycap,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), rider, '' ) r1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), rider, '' ) r2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), rider, '' ) r3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), rider, '' ) r4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), rider, '' ) r5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), rider, '' ) r6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), rider, '' ) r7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), rider, '' ) r8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), rider, '' ) r9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), rider, '' ) r10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), rider, '' ) r11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), rider, '' ) r12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), rider, '' ) r13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), rider, '' ) r14,
                          
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), t_time, 0 ) d1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), t_time, 0 ) d2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), t_time, 0 ) d3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), t_time, 0 ) d4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), t_time, 0 ) d5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), t_time, 0 ) d6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), t_time, 0 ) d7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), t_time, 0 ) d8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), t_time, 0 ) d9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), t_time, 0 ) d10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), t_time, 0 ) d11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), t_time, 0 ) d12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), t_time, 0 ) d13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), t_time, 0 ) d14,

                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), canter, 0 ) c1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), canter, 0 ) c2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), canter, 0 ) c3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), canter, 0 ) c4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), canter, 0 ) c5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), canter, 0 ) c6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), canter, 0 ) c7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), canter, 0 ) c8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), canter, 0 ) c9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), canter, 0 ) c10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), canter, 0 ) c11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), canter, 0 ) c12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), canter, 0 ) c13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), canter, 0 ) c14,
                          
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 1 DAY), '%Y%m%d'), strong, 0 ) s1,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 DAY), '%Y%m%d'), strong, 0 ) s2,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d'), strong, 0 ) s3,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 4 DAY), '%Y%m%d'), strong, 0 ) s4,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 5 DAY), '%Y%m%d'), strong, 0 ) s5,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 6 DAY), '%Y%m%d'), strong, 0 ) s6,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 7 DAY), '%Y%m%d'), strong, 0 ) s7,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 8 DAY), '%Y%m%d'), strong, 0 ) s8,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 9 DAY), '%Y%m%d'), strong, 0 ) s9,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 10 DAY), '%Y%m%d'), strong, 0 ) s10,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 11 DAY), '%Y%m%d'), strong, 0 ) s11,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 12 DAY), '%Y%m%d'), strong, 0 ) s12,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 13 DAY), '%Y%m%d'), strong, 0 ) s13,
                          if( tdate = date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d'), strong, 0 ) s14
                        from train a right outer join  
                        ( 
                          select rcity, rdate, rday, rno, trainer, jockey, jt_per, gate, rank, r_rank, r_pop, horse, handycap
                            from expect 
                          where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 3 DAY), '%Y%m%d')
                        ) b on a.horse = b.horse
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d') and '""" + i_rdate + """'
                      ) a
                      group by rcity, rdate, rday, rno, gate, rank, horse
                      order by rcity, rdate, rday, rno, gate
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return training

# 기수 인기도 및 게이트 연대율


def get_popularity_rate(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = """select b.rank, b.gate, b.jockey, b.trainer, b.host,
                                  sum(r1_1) r1_1, sum(r1_2) r1_2, sum(r1_3) r1_3, sum(r1_cnt) r1_cnt, 
                                  sum(r3_1) r1_1, sum(r3_2) r2_2, sum(r3_3) r3_3, sum(r3_cnt) r3_cnt,
                                  sum(gt_1) r1_1, sum(gt_2) r2_2, sum(gt_3) gt_3, sum(gt_cnt) gt_cnt
                      from
                      (
                        SELECT jockey, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt,
                                    0 r3_1, 0 r3_2, 0 r3_3, 0 r3_cnt,
                                    0 gt_1, 0 gt_2, 0 gt_3, 0 gt_cnt
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and pop_rank = 1
                        group by jockey 

                        union all

                        SELECT jockey, 0, 0, 0, 0,
                                        sum( if( rank = 1, 1, 0 )) r1, sum( if( rank = 2, 1, 0 )) r2, sum( if( rank = 3, 1, 0 )) r3, count(*) rcnt,
                                        0, 0, 0, 0
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and alloc3r <= 1.9 /* 연식 1.9이하 인기마 */
                        
                        group by jockey 

                        union all
    
                        select b.jockey,   0, 0, 0, 0,  0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt
                        from
                        (
                          SELECT jockey, gate, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM record 
                          where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                          and grade != '주행검사'
                          group by jockey , gate	
                          ) a  right outer join  exp011 b  on a.jockey = b.jockey and a.gate = b.gate
                        where b.rcity =  '""" + i_rcity + """'
                          and b.rdate = '""" + i_rdate + """'
                          and b.rno =  """ + str(i_rno) + """


                      ) a  right outer join  exp011 b  on a.jockey = b.jockey
                    where b.rcity =  '""" + i_rcity + """'
                      and b.rdate = '""" + i_rdate + """'
                      and b.rno =  """ + str(i_rno) + """
                    group by b.rank, b.gate, b.jockey
                    order by b.rank, b.gate, b.jockey
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        popularity = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return popularity

# 조교사 인기도 및 게이트 연대율


def get_popularity_rate_t(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = """select b.rank, b.gate, b.jockey, b.trainer, b.host,
                                  sum(r1_1) r1_1, sum(r1_2) r1_2, sum(r1_3) r1_3, sum(r1_cnt) r1_cnt, 
                                  sum(r3_1) r1_1, sum(r3_2) r2_2, sum(r3_3) r3_3, sum(r3_cnt) r3_cnt,
                                  sum(gt_1) r1_1, sum(gt_2) r2_2, sum(gt_3) gt_3, sum(gt_cnt) gt_cnt
                      from
                      (
                        SELECT trainer, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt,
                                    0 r3_1, 0 r3_2, 0 r3_3, 0 r3_cnt,
                                    0 gt_1, 0 gt_2, 0 gt_3, 0 gt_cnt
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and pop_rank = 1
                        group by trainer 

                        union all

                        SELECT trainer, 0, 0, 0, 0,
                                        sum( if( rank = 1, 1, 0 )) r1, sum( if( rank = 2, 1, 0 )) r2, sum( if( rank = 3, 1, 0 )) r3, count(*) rcnt,
                                        0, 0, 0, 0
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and alloc3r <= 1.9 /* 연식 1.9이하 인기마 */
                        
                        group by trainer 

                        union all
    
                        select b.trainer,   0, 0, 0, 0,  0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt
                        from
                        (
                          SELECT trainer, gate, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM record 
                          where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                          and grade != '주행검사'
                          group by trainer , gate	
                          ) a  right outer join  exp011 b  on a.trainer = b.trainer and a.gate = b.gate
                        where b.rcity =  '""" + i_rcity + """'
                          and b.rdate = '""" + i_rdate + """'
                          and b.rno =  """ + str(i_rno) + """


                      ) a  right outer join  exp011 b  on a.trainer = b.trainer
                    where b.rcity =  '""" + i_rcity + """'
                      and b.rdate = '""" + i_rdate + """'
                      and b.rno =  """ + str(i_rno) + """
                    group by b.rank, b.gate, b.trainer
                    order by b.rank, b.gate, b.trainer
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        popularity = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return popularity

def get_popularity_rate_h(i_rcity, i_rdate, i_rno):
    try:
        cursor = connection.cursor()

        strSql = """select b.rank, b.gate, b.jockey, b.trainer, b.host,
                                  sum(r1_1) r1_1, sum(r1_2) r1_2, sum(r1_3) r1_3, sum(r1_cnt) r1_cnt, 
                                  sum(r3_1) r1_1, sum(r3_2) r2_2, sum(r3_3) r3_3, sum(r3_cnt) r3_cnt,
                                  sum(gt_1) r1_1, sum(gt_2) r2_2, sum(gt_3) gt_3, sum(gt_cnt) gt_cnt
                      from
                      (
                        SELECT host, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt,
                                    0 r3_1, 0 r3_2, 0 r3_3, 0 r3_cnt,
                                    0 gt_1, 0 gt_2, 0 gt_3, 0 gt_cnt
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and pop_rank = 1
                        group by host 

                        union all

                        SELECT host, 0, 0, 0, 0,
                                        sum( if( rank = 1, 1, 0 )) r1, sum( if( rank = 2, 1, 0 )) r2, sum( if( rank = 3, 1, 0 )) r3, count(*) rcnt,
                                        0, 0, 0, 0
                        FROM rec011 a
                        where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                        and alloc3r <= 1.9 /* 연식 1.9이하 인기마 */
                        
                        group by host 

                        union all
    
                        select b.host,   0, 0, 0, 0,  0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt
                        from
                        (
                          SELECT host, gate, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM record 
                          where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d')
                          and grade != '주행검사'
                          group by host , gate	
                          ) a  right outer join  exp011 b  on a.host = b.host and a.gate = b.gate
                        where b.rcity =  '""" + i_rcity + """'
                          and b.rdate = '""" + i_rdate + """'
                          and b.rno =  """ + str(i_rno) + """


                      ) a  right outer join  exp011 b  on a.host = b.host
                    where b.rcity =  '""" + i_rcity + """'
                      and b.rdate = '""" + i_rdate + """'
                      and b.rno =  """ + str(i_rno) + """
                    group by b.rank, b.gate, b.host
                    order by b.rank, b.gate, b.host
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        popularity = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return popularity


def get_print_prediction(i_rcity, i_rdate):

    try:
        cursor = connection.cursor()

        strSql = """ 
                select rcity, rdate, rday, rno, rtime, distance
                  from exp010
                where rcity = '""" + i_rcity + """'
                  and rdate = '""" + i_rdate + """' 
                order by rdate, rcity desc, rno
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        race = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    try:
        cursor = connection.cursor()

        strSql = """
                select rcity, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey, trainer, host, r_pop, distance, handycap, i_prehandy, complex,

                    complex5, gap_back,
                    cast(jt_per as decimal) jt_per
                  from expect a
                where rcity = '""" + i_rcity + """'
                  and rdate = '""" + i_rdate + """' 
                  and rank in ( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 98 )
                order by rcity, rdate, rno, rank, gate
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

    try:
        cursor = connection.cursor()

        strSql = """ 
                select a.rcity, a.rdate, a.rday, a.rno, a.rtime, a.distance, b.r2alloc, b.r333alloc, b.r123alloc
                  from exp010 a left outer join 
                        rec010 b on a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno
                where a.rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 4 DAY), '%Y%m%d')
                order by a.rdate, a.rcity desc, a.rno
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        race = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in exp010 outer join rec010")

    try:
        cursor = connection.cursor()

        strSql = """
                select rcity, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey, trainer, host, r_pop, distance, handycap, i_prehandy, complex,
                    --  ( select complex from expect  where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank = 5 ) complex5, 
                    --  ( select i_complex from expect  where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank = a.rank + 1 ) - i_complex, 
                    complex5, gap_back, 
                    cast(jt_per as decimal) jt_per,
                    rcount
                  from expect a
                where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 4 DAY), '%Y%m%d')
                and rank in ( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 98 )
                order by rcity, rdate, rno, rank, gate
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        expects = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in expect ")

    try:
        cursor = connection.cursor()

        strSql = """
                select rcity, jockey, count(*), 
                        sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) + sum(if(r_rank = 3, 1, 0)) rr123_cnt, 
                        sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0)) + sum(if(rank = 3, 1, 0)) r123_cnt, 
                        sum(if(r_rank = 1, 1, 0)) rr1, sum(if(r_rank = 2, 1, 0)) rr2, sum(if(r_rank = 3, 1, 0)) rr3,
                        sum(if(rank = 1, 1, 0)) r1, sum(if(rank = 2, 1, 0)) r2, sum(if(rank = 3, 1, 0)) r3
                  from expect a
                where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 3 DAY), '%Y%m%d')
                and rno < 80
                group by rcity, jockey
                order by rcity, sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) + sum(if(r_rank = 3, 1, 0)) desc,
                                sum(if(r_rank = 1, 1, 0)) + sum(if(r_rank = 2, 1, 0)) desc,
                                sum(if(r_rank = 1, 1, 0))  desc,
                                sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0)) + sum(if(rank = 3, 1, 0)) desc,
                                sum(if(rank = 1, 1, 0)) + sum(if(rank = 2, 1, 0))  desc,
                                sum(if(rank = 1, 1, 0)) desc
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        award_j = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")
    # print(r_cnt)
    # print(type(weeks[0]))
    
    try:
        cursor = connection.cursor()

        strSql = """ 
                select a.rdate, a.rday, date_format( curdate(), '%Y%m%d' ), rcity
                from exp010 a
                where a.rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and date_format(DATE_ADD('""" + i_rdate + """', INTERVAL + 4 DAY), '%Y%m%d')
                group by a.rdate, a.rday, a.rcity
                order by a.rdate, a.rday, a.rcity desc 
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        rdays = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting rdays")

    return race, expects, award_j, rdays


def get_report_code(i_rcity, i_rdate, i_rno):

    try:
        cursor = connection.cursor()
        strSql = """ select rcity, rdate, rno, rank, gate, horse, r_start, r_corners, r_finish, r_wrapup, r_etc
                    from rec011 
                    where rcity =  '""" + i_rcity + """'
                      and rdate = '""" + i_rdate + """'
                      and rno =  """ + str(i_rno) + """
                      order by rank, gate
                    """
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        rec011 = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting start")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R1' order by r_code; """
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        r_start = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting r_start")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R2' order by r_code; """
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        r_corners = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting r_corners")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R3' order by r_code; """
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        r_finish = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting r_finish")
    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R4' order by r_code; """
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ 
                select a.trainer
                  from exp011 a
                where a.rcity =  '""" + i_rcity + """'
                and a.rdate = '""" + i_rdate + """'
                and a.rno =  """ + str(i_rno) + """
                group by a.rcity, a.rdate, a.rno, a.trainer
                having count(*) >= 2

                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        trainer_double_check = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in exp010 outer join rec010")

    return trainer_double_check


def get_jockey_trend(i_rcity, i_rdate, i_rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
              select b.rank, b.gate, b.r_rank, b.r_pop, b.horse, CONCAT( RPAD(b.jockey, 5),RPAD( b.trainer, 5), b.host), a.wdate, a.year_per, CONCAT(debut, ' ', age, '_', wcnt) debut, weeks
              from
              (
                SELECT wdate, jockey, cast( year_3per as DECIMAL(4,1))*10 year_per, tot_1st, debut, CONCAT(wrace, '`', w1st, '`', w2nd, '`', w3rd) weeks, 
                        ( select concat( max(age) , ' ', max(tot_1st) ) from jockey_w c where c.jockey = d.jockey and c.wdate < '""" + i_rdate + """' ) age,
                        ( select concat( sum(if( r_rank = 1, 1, 0)),'_', sum(if( r_rank = 2, 1, 0)), '_', sum(if( r_rank = 3, 1, 0))) from exp011 
                            where jockey = d.jockey -- and r_rank <= 3 
                            and rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and '""" + i_rdate + """' ) wcnt
                FROM jockey_w d
                where wdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 88 DAY), '%Y%m%d') and '""" + i_rdate + """'
                and wdate < '""" + i_rdate + """'
              ) a  right outer join  expect b  on a.jockey = b.jockey 
              where b.rdate = '""" + i_rdate + """' and b.rcity = '""" + i_rcity + """' and b.rno = """ + str(i_rno) + """
              order by b.rank, a.wdate desc
              ; """

        # print(strSql)

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Jockey Trend")

    col = ['예상', '마번', '실순', '인기',
           'horse', '기수', 'wdate', 'year_per', '데뷔', 'Weeks']
    data = list(result)
    # print(data)

    df = pd.DataFrame(data=data, columns=col)
    # print(df)

    pdf1 = pd.pivot_table(df,                # 피벗할 데이터프레임
                          index=('예상', '마번', '실순', '인기',
                                 'horse', '기수', '데뷔'),    # 행 위치에 들어갈 열
                          columns='wdate',    # 열 위치에 들어갈 열
                          values=('year_per', 'Weeks'), aggfunc='max')     # 데이터로 사용할 열

    # pdf1.columns = ['/'.join(col) for col in pdf1.columns]
    pdf1.columns = [''.join(col)[4:6] + '.' + ''.join(col)[6:8]
                    for col in pdf1.columns]

    # print(((pdf1)))

    pdf1 = pdf1.reset_index()

    # print(pdf1)
    
    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT distinct distinct CONCAT( substr(wdate,5,2), '.', substr(wdate,7,2) )
                FROM jockey_w d
                where wdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 88 DAY), '%Y%m%d') and '""" + i_rdate + """'
                and wdate < '""" + i_rdate + """'
                order by wdate
              ; """

        # print(strSql)

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        trend_title = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Jockey Trend Title")
    # result = dict[result]
    

    return pdf1, trend_title

def get_trainer_trend(i_rcity, i_rdate, i_rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
              select b.rank, b.gate, b.r_rank, b.r_pop, b.horse, CONCAT( RPAD(b.trainer, 5),RPAD( b.jockey, 5), b.host), a.wdate, a.year_per, CONCAT(debut, ' ', age, '_', wcnt) debut, weeks
              from
              (
                SELECT wdate, trainer, cast( year_3per as DECIMAL(4,1))*10 year_per, tot_1st, debut, CONCAT(wrace, '`', w1st, '`', w2nd, '`', w3rd) weeks,
                        ( select concat( max(age) , ' ', max(tot_1st) ) from trainer_w c where c.trainer = d.trainer and c.wdate < '""" + i_rdate + """' ) age,
                        ( select concat( sum(if( r_rank = 1, 1, 0)),'_', sum(if( r_rank = 2, 1, 0)), '_', sum(if( r_rank = 3, 1, 0))) from exp011 
                            where trainer = d.trainer -- and r_rank <= 3 
                            and rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 3 DAY), '%Y%m%d') and '""" + i_rdate + """' ) wcnt
                FROM trainer_w d
                where wdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 88 DAY), '%Y%m%d') and '""" + i_rdate + """'
                and wdate < '""" + i_rdate + """'
              ) a  right outer join  expect b  on a.trainer = b.trainer 
              where b.rdate = '""" + i_rdate + """' and b.rcity = '""" + i_rcity + """' and b.rno = """ + str(i_rno) + """
              order by b.rank, a.wdate desc
              ; """

        # print(strSql)

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in Trainer Trend")

    # result = dict[result]

    col = ['예상', '마번', '실순', '인기',
           'horse', '기수', 'wdate', 'year_per', '데뷔', 'Weeks']
    data = list(result)
    # print(data)

    df = pd.DataFrame(data=data, columns=col)
    # print(df)

    pdf1 = pd.pivot_table(df,                # 피벗할 데이터프레임
                          index=('예상', '마번', '실순', '인기',
                                 'horse', '기수', '데뷔'),    # 행 위치에 들어갈 열
                          columns='wdate',    # 열 위치에 들어갈 열
                          values=('year_per', 'Weeks'), aggfunc='max')     # 데이터로 사용할 열

    # pdf1.columns = ['/'.join(col) for col in pdf1.columns]
    pdf1.columns = [''.join(col)[4:6] + '.' + ''.join(col)[6:8]
                    for col in pdf1.columns]

    # print(((pdf1)))
    
    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT distinct CONCAT( substr(wdate,5,2), '.', substr(wdate,7,2) )
                FROM jockey_w d
                where wdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 88 DAY), '%Y%m%d') and '""" + i_rdate + """'
                and wdate < '""" + i_rdate + """'
                order by wdate
              ; """

        # print(strSql)

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

# 기수 or 조교사 최근 99일 경주결과
def get_solidarity(i_rcity, i_rdate, i_rno, i_awardee, i_filter):
    
    try:
        cursor = connection.cursor()

        strSql = """ 
                    select rcity, rdate, rno, distance, grade, dividing, weather, rstate, rmoisture, r1award, r2alloc, race_speed,
                        gate, rank, horse, h_weight, w_change, jockey, trainer, if( host = '', ' ', host), rating, handycap, record, corners, gap, gap_b, p_record, p_rank, pop_rank, alloc1r, alloc3r,
                        rs1f, rg3f, rg2f, rg1f, race_speed
                    from record 
                    where ( '""" + i_awardee + """' ) in ( select '""" + i_awardee + """' from exp011 where rcity = '""" + i_rcity + """' and rdate = '""" + i_rdate + """' and rno =  """ + str(i_rno) + """ ) 
                    and rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 99 DAY), '%Y%m%d') and '""" + i_rdate + """'
                    and rank <= """ + i_filter + """
                    -- and r1award > 0  
                    order by rdate desc, rno desc, rcity
                ; """

        # print(strSql)
        
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기수, 조교사, 마주 최근 1년 연대현황")

    return result

# 기수 or 조교사 or 마주 최근 99일 경주결과
def get_race_awardee1( i_rdate, i_awardee, i_name):
    
    try:
        cursor = connection.cursor()

        strSql = """ 
                    select rcity, rdate, rno, distance, grade, dividing, weather, rstate, rmoisture, r1award, r2alloc, race_speed,
                        gate, rank, horse, h_weight, w_change, jockey, trainer, host, rating, handycap, record, corners, gap, gap_b, p_record, p_rank, pop_rank, alloc1r, alloc3r,
                        rs1f, rg3f, rg2f, rg1f, race_speed
                    from record 
                    where """ + i_awardee + """ = '""" + i_name + """'
                    and rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 30 DAY), '%Y%m%d') and '""" + i_rdate + """'
                    order by rdate desc, rno desc, rcity
                ; """

        # print(strSql)
        
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

        strSql = """ 
                    select gate, count(*), sum( if ( a.r_rank <= 3, 1, 0)), sum( if ( a.r_rank <= 3	, 1, 0))/count(*)*100,        
                    -- sum( if(a.alloc3r <= 1.9, 1, 0)),  sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0)), sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0))/ sum( if(a.alloc3r <= 1.9, 1, 0))*100
                    sum( if(a.jt_per >= a.j_per, 1, 0)),  sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0)), sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0))/ sum( if(a.jt_per >= a.j_per, 1, 0))*100,
                    sum( if(a.jt_per < a.j_per, 1, 0)),  sum( if ( a.r_rank <= 3 and a.jt_per < a.j_per, 1, 0)), sum( if ( a.r_rank <= 3 and a.jt_per < a.j_per, 1, 0))/ sum( if(a.jt_per < a.j_per, 1, 0))*100
                    from The1.expect a
                    where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and '""" + i_rdate + """'
                    and ( rcity, rdate, rno ) not in ( select rcity, rdate, rno from The1.expect where rank = 98  group by rcity, rdate, rno having count(*) >= 2 ) 
                    and rank = 1
                    and jockey = ( select jockey from exp011 where rcity = '""" + i_rcity + """' and rdate = '""" + i_rdate + """' and rno =  """ + str(i_rno) + """ and rank = 1) 
                    -- and gate = ( select gate from exp011 where rcity = '""" + i_rcity + """' and rdate = '""" + i_rdate + """' and rno =  """ + str(i_rno) + """ and rank = 1) 
                    group by gate
                    
                    union all
                    
                    select 'TOT', count(*), sum( if ( a.r_rank <= 3, 1, 0)), sum( if ( a.r_rank <= 3	, 1, 0))/count(*)*100,
                    -- sum( if(a.alloc3r <= 1.9, 1, 0)),  sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0)), sum( if ( a.r_rank <= 3 and a.alloc3r <= 1.9, 1, 0))/ sum( if(a.alloc3r <= 1.9, 1, 0))*100
                    sum( if(a.jt_per >= a.j_per, 1, 0)),  sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0)), sum( if ( a.r_rank <= 3 and a.jt_per >= a.j_per, 1, 0))/ sum( if(a.jt_per >= a.j_per, 1, 0))*100,
                    sum( if(a.jt_per < a.j_per, 1, 0)),  sum( if ( a.r_rank <= 3 and a.jt_per < a.j_per, 1, 0)), sum( if ( a.r_rank <= 3 and a.jt_per < a.j_per, 1, 0))/ sum( if(a.jt_per < a.j_per, 1, 0))*100
                    from The1.expect a
                    where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and '""" + i_rdate + """'
                    and ( rcity, rdate, rno ) not in ( select rcity, rdate, rno from The1.expect where rank = 98  group by rcity, rdate, rno having count(*) >= 2 ) 
                    and rank = 1
                    and jockey = ( select jockey from exp011 where rcity = '""" + i_rcity + """' and rdate = '""" + i_rdate + """' and rno =  """ + str(i_rno) + """ and rank = 1) 
                ; """

        # print(strSql)
        
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')
        # print(index, items)

        if items[0]:
            rdate = items[0][0:4] + items[0][5:7] + items[0][8:10]
            rno = items[1]

            horse = items[3]
            if horse[0:1] == '[':
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

                strSql = """ update exp011
                            set jockey = '""" + jockey_new + """',
                                handycap = """ + handy_new + """,
                                jockey_old =  '""" + jockey_old + """',
                                handycap_old = """ + handy_old + """,
                                reason = '""" + reason + """'
                        where rdate = '""" + rdate + """' and rno = """ + str(rno) + """ and horse = '""" + horse + """'
                    ; """

                # print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed updating in exp011 : 기수변경")

    return len(lines)

# 경주 변경 내용 update - 기수변경
def set_changed_race_jockey(i_rcity, i_rdate, i_rno, r_content):
    # print(r_content)

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')
        # print(index, items)

        if items[0]:
            rdate = items[0][0:4] + items[0][5:7] + items[0][8:10]
            rno = items[1]

            horse = items[3]
            if horse[0:1] == '[':
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

                strSql = """ update exp011
                            set jockey = '""" + jockey_new + """',
                                handycap = """ + handy_new + """,
                                jockey_old =  '""" + jockey_old + """',
                                handycap_old = """ + handy_old + """,
                                reason = '""" + reason + """'
                        where rdate = '""" + rdate + """' and rno = """ + str(rno) + """ and horse = '""" + horse + """'
                    ; """

                # print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed updating in exp011 : 기수변경")

    return len(lines)

# 경주 변경 내용 update - 경주마 취소


def set_changed_race_horse(i_rcity, i_rdate, i_rno, r_content):
    # print(r_content)

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')

        print(index, items)

        if items[0]:
            rdate = items[1][0:4] + items[1][5:7] + items[1][8:10]
            rno = items[2]
            horse = items[4]
            if horse[0:1] == '[':
                horse = horse[3:]
            reason = items[7]

            # print(rdate, rno, horse, reason)

            try:
                cursor = connection.cursor()

                strSql = """ update exp011
                              set reason = '""" + reason + """',
                                  r_rank = 99
                          where rdate = '""" + rdate + """' and rno = """ + str(rno) + """ and horse = '""" + horse + """'
                      ; """

                # print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed updating in exp011 : 경주마 취소")

    return len(lines)

# 경주 변경 내용 update - 경주마 체중


def set_changed_race_weight(i_rcity, i_rdate, i_rno, r_content):
    # print(r_content)

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')

        # print(index, items)

        if items[0] and index == 0:
            rdate = items[0][0:4] + items[0][5:7] + items[0][8:10]
        elif items[0] and index >= 8:
            horse = items[1]
            if horse[0:1] == '[':
                horse = horse[3:]

            if int(items[3]) > 0:
                items[3] = '+' + items[3]

            weight = items[2] + ' ' + items[3]

            # print(rdate, horse, weight)

            try:
                cursor = connection.cursor()

                strSql = """ 
                            update exp011
                            set h_weight = '""" + weight + """'
                            where rdate = '""" + rdate + """' and horse = '""" + horse + """'
                        ; """

                # print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed updating in exp011 : 경주마 체중")
    return len(lines)

# 경주 변경 내용 update - 경주순위


def set_changed_race_rank(i_rcity, i_rdate, i_rno, r_content):
    # print(r_content)

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')

        # print(index, items)

        if items[0] and index == 0:
            rdate = items[0][0:4] + items[0][6:8] + items[0][10:12]
        elif items[0] and index >= 9:

            r_rank = items[0]
            print(r_rank)
            horse = items[2]
            if horse[0:1] == '[':
                horse = horse[3:]

            # print(rdate, horse, r_rank)

            try:
                cursor = connection.cursor()

                strSql = """ update exp011
                              set r_rank = """ + r_rank + """
                          where rdate = '""" + rdate + """' and horse = '""" + horse + """'
                      ; """

                # print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed updating in exp011 : 경주마 체중")

    return len(lines)

# 수영조교 데이터 입력


def insert_train_swim(r_content):
    # print(r_content)

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')

        # print(index, items)

        if items[0] and index == 0:
            tdate = items[0][0:4] + items[0][5:7] + items[0][8:10]
            print(tdate)
        elif items[0] and index >= 2:               # 제목(title) 라인 스킵

            team = items[1][0:2]
            trainer = items[1][3:-1]

            if team[1:] == '조':
                team = team[0:1]
            else:
                trainer = trainer[1:]

            horse = items[3]
            laps = items[4][0:1]
            print(trainer, horse, laps)

            # print(tdate, horse, team)

            try:
                cursor = connection.cursor()

                strSql = """ insert swim 
                                ( horse, tdate, team, trainer, laps ) 
                                values ( '""" + horse + """', '""" + tdate + """', '""" + team + """', '""" + trainer + """', """ + laps + """ )
                      ; """

                print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed inserting in swim : 수영조교")

    return len(lines)

# 말진료현황 데이터 입력


def insert_horse_disease(r_content):
    # print(r_content)

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')

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

                strSql = """ delete from treat
                                where horse = '""" + horse + """'
                                and tdate = '""" + tdate + """'
                                and hospital = '""" + hospital + """'
                        ; """

                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

            except:
                connection.rollback()
                print("Failed deleting in swim : 말 진료현황")

            try:
                cursor = connection.cursor()

                strSql = """ insert treat
                                ( rcity, horse, tdate, team, hospital, disease )
                                values ( '""" + num + """', '""" + horse + """', '""" + tdate + """', '""" + team + """', '""" + hospital + """', '""" + disease + """' )
                        ; """

                # print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')

        print(index, items)

        if items[0] and index == 0:
            rdate = items[0][0:4] + items[0][6:8] + items[0][10:12]
        elif items[0] and index >= 9:

            r_rank = items[0]
            horse = items[2]
            if horse[0:1] == '[':
                horse = horse[3:]

            print(rdate, horse, r_rank)

            try:
                cursor = connection.cursor()

                strSql = """ update exp011
                              set r_rank = """ + r_rank + """
                          where rdate = '""" + rdate + """' and horse = '""" + horse + """'
                      ; """

                print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

    lines = r_content.split('\n')

    for index, line in enumerate(lines):
        items = line.split('\t')

        if items[0]:

            if index == 0:

                rdate = items[0][0:4] + items[0][6:8] + items[0][10:12]
                rno = items[0][-5:]

                if rno[0:1] == '제':
                    rno = rno[1:2]
                else:
                    rno = rno[0:2]

                i_rno = int(rno) + 80

            elif index == 1:

                pos = items[0].find(' ')
                # print(pos)
                grade = items[0][0:pos]
                # print(grade)

                pos = items[0].find('M')
                # print(pos)
                distance = items[0][pos - 4:pos]

                # print(distance)

                try:
                    cursor = connection.cursor()

                    strSql = """ delete from exp010
                                    where rcity = '""" + rcity + """'
                                    and rdate = '""" + rdate + """'
                                    and rno = """ + str(i_rno) + """
                            ; """

                    # print(strSql)

                    r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                    awards = cursor.fetchall()

                    connection.commit()
                    connection.close()

                except:
                    connection.rollback()
                    print("Failed deleting in exp010")

                try:
                    cursor = connection.cursor()

                    strSql = """ insert into exp010
                                    ( rcity, rdate, rno, grade, distance, rcount )
                                values ( '""" + rcity + """', '""" + rdate + """', """ + str(i_rno) + """, 
                                        '""" + grade + """', """ + distance + """, '""" + str(rcount) + """' )
                            ; """

                    # print(strSql)

                    r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                    awards = cursor.fetchall()

                    connection.commit()
                    connection.close()

                except:
                    connection.rollback()
                    print("Failed inserting in exp010")

                try:
                    cursor = connection.cursor()

                    strSql = """ delete from exp011
                                    where rcity = '""" + rcity + """'
                                    and rdate = '""" + rdate + """'
                                    and rno = """ + str(i_rno) + """
                            ; """

                    # print(strSql)
                    r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                    awards = cursor.fetchall()

                    connection.commit()
                    connection.close()

                except:
                    connection.rollback()
                    print("Failed deleting in exp011")

                try:
                    cursor = connection.cursor()

                    strSql = """ delete from exp012
                                    where rcity = '""" + rcity + """'
                                    and rdate = '""" + rdate + """'
                                    and rno = """ + str(i_rno) + """
                            ; """

                    # print(strSql)
                    r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                    awards = cursor.fetchall()

                    connection.commit()
                    connection.close()

                except:
                    connection.rollback()
                    print("Failed deleting in exp012")

            else:

                if index > 5 and int(items[0]) >= 1:
                    gate = items[0]
                    horse = items[1]
                    if horse[0:1] == '[':
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

                        strSql = """ insert into exp011
                                        ( rcity, rdate, rno, gate, horse, rating, birthplace, h_sex, h_age, trainer, host, handycap, jockey  )
                                        values ( '""" + rcity + """', '""" + rdate + """', """ + str(i_rno) + """, """ + gate + """, '""" + horse + """', 
                                            """ + rating + """ , '""" + birthplace + """' , '""" + sex + """' , """ + age + """ , 
                                            '""" + trainer + """' , '""" + host + """', 57,  '""" + jockey + """'   )
                                        ; """

                        # print(strSql)

                        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                        awards = cursor.fetchall()

                        connection.commit()
                        connection.close()

                    except:
                        connection.rollback()
                        print("Failed inserting in exp011")

                    try:
                        cursor = connection.cursor()

                        strSql = """ insert into exp012
                                        ( rcity, rdate, rno, gate, horse  )
                                        values ( '""" + rcity + """', '""" + rdate + """', """ + str(i_rno) + """, """ + gate + """, '""" + horse + """' )
                                        ; """

                        # print(strSql)

                        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                        awards = cursor.fetchall()

                        connection.commit()
                        connection.close()

                    except:
                        connection.rollback()
                        print("Failed inserting in exp012")

                else:
                    pass

    return len(lines)

# 심판위원 Report
def insert_race_judged(rcity, r_content):
    # print(r_content)
    # print(rcount)

    lines = r_content.split('\n')

    rno = 0
    judged = ''
    committee = ''
    for index, line in enumerate(lines):
        items = line.split('\t')

        # print(items[0])

        if items[0]:

            if index == 0:
                # print(items[0][14:16])
                if items[0][14:16] == '서울':
                    rcity = '서울'
                else:
                    rcity = '부산'
                # print(items[1])

            elif index == 3:
                rdate = items[1][0:4] + items[1][6:8] + items[1][10:12]
            elif index > 5:

                # print(items[0][-4:])
                if items[0][-2:] == '경주':
                    rno = items[0][-4:][0:2]
                    judged = ''     # 경주별로 재경사항 초기화 
                elif items[0][0:2] == '심판':
                    committee = items[1]
                elif items[0][0:1] == '●':
                    judged =  judged + '\n' + items[0]
                else:
                    # if items[0][0:8] == '경주번호, 등급' or items[0][0:7] == '기수변경 내역' or items[0][0:5] == '제재 내역' :
                    if items[0][0:8] == '경주번호, 등급' or items[0][0:7] == '기수변경 내역' or items[0][0:5] == '제재 내역' or items[0][0:4] == '약물검사' :

                        if rno == 0:                                # 추가 재결사항 update
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
                            ret = insert_race_judged_sql(rcity, rdate, rno, judged, '', committee)

    return len(lines)

def insert_race_judged_sql(rcity, rdate, rno, judged, judged_add, committee):
    # print(committee)
    try:
        cursor = connection.cursor()

        strSql = """    select count(*) from rec013
                        where rcity = '""" + rcity + """'
                        and rdate = '""" + rdate + """'
                        and rno = """ + str(rno) + """
                        ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        ret = cursor.fetchall()

        # print((ret[0][0]))      # 재결사항 입력 여부


        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed select error in rec013")

    if ret[0][0] == 0:
        try:
            cursor = connection.cursor()

            strSql = """ insert into rec013
                            ( rcity, rdate, rno, judged )
                            values ( '""" + rcity + """', '""" + rdate + """', """ + str(rno) + """, '""" + judged + """' )
                            ; """
            # print(strSql)

            r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
            ret = cursor.fetchall()

            connection.commit()
            connection.close()

        except:
            connection.rollback()
            print("Failed inserting in rec013 ")
    else:
        try:
            cursor = connection.cursor()

            strSql = """ update rec013
                            set judged = '""" + judged + """'
                        where rcity = '""" + rcity + """' and rdate = '""" + rdate + """' and rno = """ + str(rno) + """
                            ; """
            # print(strSql)
            r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
            ret = cursor.fetchall()

            connection.commit()
            connection.close()

        except:
            connection.rollback()
            print("Failed updating in rec013")

    return ret

def get_jockey(horse):      # 출전등록 시뮬레이션 - 기수 select 
    try:
        cursor = connection.cursor()

        strSql = """ select jockey from rec011
                        where horse = '""" + horse + """'
                        and rdate = ( select max(rdate) from rec011 where horse = '""" + horse + """')
                        ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        jockey = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed inserting in exp010")

    return jockey
