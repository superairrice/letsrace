from django.db import connection


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

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

        print(strSql)

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
                    sum(rtot) rtot
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
                FROM The1.exp011     a,
                      The1.rec015     b
                where a.jockey = b.jockey 
                AND b.t_sort = '기수'
                AND b.rdate between date_format(DATE_ADD('""" + rdate + """', INTERVAL - 100 DAY), '%Y%m%d') and '""" + rdate + """'
                AND a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
              order by jockey, rdate desc
            ; """

        print(strSql)

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
                FROM The1.exp011     a,
                      The1.rec015     b
                where a.horse = b.horse 
         
         
                AND b.rdate between date_format(DATE_ADD('""" + rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and '""" + rdate + """'
                AND a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
              order by a.rank, b.rdate desc
            ; """

        print(strSql)

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
                FROM exp011	a right outer join 
                    rec015	b on a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno and a.horse = b.horse
                where a.rcity = '""" + rcity + """'
                AND a.rdate = '""" + rdate + """'
                AND a.rno = """ + str(rno) + """
              order by a.rank
            ; """

        print(strSql)

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return result


def get_pedigree(rcity, rdate, rno):

    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT a.gate, a.rank, a.horse, a.jockey, a.trainer,	a.host,
                    ( a.year_1st + a.year_2nd + a.year_3rd )*100/a.year_race h_3rd, 
                    a.year_race h_tot, 
                    b.paternal, 
                    b.maternal,
                    (	select sum( year_race ) from horse where paternal = b.paternal ) p_tot,
                    (	select sum( year_1st + year_2nd ) from horse where paternal = b.paternal ) p_3rd,
                    (	select sum( year_race ) from horse where maternal = b.maternal ) m_tot,
                    (	select sum( year_1st + year_2nd ) from horse where maternal = b.maternal ) m_3rd,
                    gear1, gear2, blood1, blood2, treat1, treat2
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

        # print(strSql)

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

    # print(r_cnt)
    # print(type(weeks[0]))

    return weeks


def get_race(i_rdate, i_awardee):

    try:
        cursor = connection.cursor()

        strSql = """ 
                select rcity,""" + i_awardee + """ awardee, rdate, rday, rno, gate, rank, r_rank, horse, remark, jockey j_name, trainer t_name, host h_name, r_pop, distance, handycap
                  from expect
                where rdate in ( select distinct rdate from racing )
                ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        weeks = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    # print(r_cnt)
    # print(type(weeks[0]))

    return weeks


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
                        from training a right outer join  ( select gate, rank, horse, jockey, trainer from The1.exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.horse = b.horse
                        and tdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 14 DAY), '%Y%m%d') and '""" + i_rdate + """'
                      ) a
                      group by gate, rank, horse, jockey, trainer
                      order by rank, gate
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

        print(strSql)

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    # print(training)

    return training


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

    print(awards)

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
                    from award a right outer join  ( select gate, rank, jockey from The1.exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.jockey = b.jockey
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by jockey, gate, rank
                    
                    union all

                    select gate, rank, '', 0, 0, 0, 0,
                            b.trainer, count(0) rcnt, 
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3,
                            '', 0, 0, 0, 0
                    from award a right outer join  ( select gate, rank, trainer from The1.exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.trainer = b.trainer
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by trainer, gate, rank

                    union all

                    select  gate, rank, '', 0, 0, 0, 0, '', 0, 0, 0, 0, b.host, count(0) rcnt, 
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, rank, host from The1.exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.host = b.host
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
                    from award a right outer join  ( select gate, jockey from The1.exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.jockey = b.jockey
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by jockey, gate
                    
                    union all

                    select 2 rflag, gate, b.trainer, count(0) rcnt, (select max(rcity) from trainer  where a.trainer = trainer ) rcity,
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, trainer from The1.exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.trainer = b.trainer
                    and rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    group by trainer, gate

                    union all

                    select 3 rflag,  gate, b.host, count(0) rcnt, (select max(rcity) from host  where a.host = host ) rcity,
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a right outer join  ( select gate, host from The1.exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.host = b.host
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

    print(strSql)

    return awards

# award_status_jockey award_status_trainer


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
                  
                  ( select year_per from """ + i_awardee + """_w 
                    where wdate = ( select max(wdate) from """ + i_awardee + """_w where wdate <= '""" + i_rdate + """' ) 
                      and """ + i_awardee + """ = aa.""" + i_awardee + """ ) year_per
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
                    from The1.record a
                  where rdate between DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 14 DAY,  '%Y%m%d') and  DATE_FORMAT(CAST('""" + i_rdate + """' AS DATE) - INTERVAL 1 DAY,  '%Y%m%d')
                    and grade != '주행검사'
                  group by """ + i_awardee + """
                ) c on aa.""" + i_awardee + """ = c.""" + i_awardee + """
                order by rcity desc, rmonth1 + rmonth2 + rmonth3 desc
                ; """

        print(strSql)

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        weeks = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    return weeks


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
                            from The1.expect 
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

    # print(training)

    return training


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
                        FROM The1.rec011 a
                        where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and '""" + i_rdate + """'
                        and pop_rank = 1
                        group by jockey 

                        union all

                        SELECT jockey, 0, 0, 0, 0,
                                        sum( if( rank = 1, 1, 0 )) r1, sum( if( rank = 2, 1, 0 )) r2, sum( if( rank = 3, 1, 0 )) r3, count(*) rcnt,
                                        0, 0, 0, 0
                        FROM The1.rec011 a
                        where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and '""" + i_rdate + """'
                        and alloc3r <= 1.9 /* 연식 1.9이하 인기마 */
                        
                        group by jockey 

                        union all
    
                        select b.jockey,   0, 0, 0, 0,  0, 0, 0, 0, r1_1,  r1_2,  r1_3,  r1_cnt
                        from
                        (
                          SELECT jockey, gate, sum( if( rank = 1, 1, 0 )) r1_1, sum( if( rank = 2, 1, 0 )) r1_2, sum( if( rank = 3, 1, 0 )) r1_3, count(*) r1_cnt
                          FROM The1.record 
                          where rdate between date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 365 DAY), '%Y%m%d') and '""" + i_rdate + """'
                          and grade != '주행검사'
                          group by jockey , gate	
                          ) a  right outer join  The1.exp011 b  on a.jockey = b.jockey and a.gate = b.gate
                        where b.rcity =  '""" + i_rcity + """'
                          and b.rdate = '""" + i_rdate + """'
                          and b.rno =  """ + str(i_rno) + """


                      ) a  right outer join  The1.exp011 b  on a.jockey = b.jockey
                    where b.rcity =  '""" + i_rcity + """'
                      and b.rdate = '""" + i_rdate + """'
                      and b.rno =  """ + str(i_rno) + """
                    group by b.rank, b.gate, b.jockey
                    order by b.rank, b.gate, b.jockey
                        ;"""

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        training = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in BookListView")

    print(strSql)

    return training


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
                      ( select complex from expect  where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank = 5 ) complex5, 
                      ( select i_complex from expect  where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank = a.rank + 1 ) - i_complex
                  from expect a
                where rcity = '""" + i_rcity + """'
                  and rdate = '""" + i_rdate + """' 
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