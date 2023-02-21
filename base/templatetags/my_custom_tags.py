from django import template
from django.db import connection

import os

from letsrace.settings import KRAFILE_ROOT


register = template.Library()


def read_file(filename):
    with open(filename, 'rb') as f:
        photo = f.read()
    return photo


@register.simple_tag
def my_tag(a):
    return a


@register.simple_tag
def get_file_contents(fname):

    try:
        cursor = connection.cursor()

        strSql = """ 
              SELECT fcontents
              FROM kradata  
              WHERE fname = '""" + fname + """'
            ; """

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchone()
        # result = cursor.fetchall()

        connection.commit()
        connection.close()

        # print(result[0].decode('euc-kr', errors='strict'))
        # print(result[0:5])
        f = result[0].decode('euc-kr', errors='strict')

        # if fname[0:4] < '2022':
        #   os.makedirs(KRAFILE_ROOT / '2022이전', exist_ok=True)
        #   os.chdir(KRAFILE_ROOT / '2022이전')
        # elif fname[0:4] == '2022':
        #   os.makedirs(KRAFILE_ROOT / '2022', exist_ok=True)
        #   os.chdir(KRAFILE_ROOT / '2022')
        # elif fname[0:4] == '2023':
        #   os.makedirs(KRAFILE_ROOT / '2023', exist_ok=True)
        #   os.chdir(KRAFILE_ROOT / '2023')
        # else:
        #   os.chdir(KRAFILE_ROOT)

        if fname[0:4] < '2018':
            os.makedirs(KRAFILE_ROOT / '2022이전', exist_ok=True)
            os.chdir(KRAFILE_ROOT / '2022이전')
        else:
            os.makedirs(KRAFILE_ROOT / fname[0:4], exist_ok=True)
            os.chdir(KRAFILE_ROOT / fname[0:4])

        letter = open(fname, 'w')                         # 새 파일 열기
        letter.write(f)
        letter.close()                                    # 닫기

    except:
        connection.rollback()
        print("Failed selecting in krafile")

    return letter
    # return str(result[0], 'euc-kr')


@register.simple_tag
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
                        from train a right outer join  ( select gate, rank, horse, jockey, trainer from The1.exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """) b on a.horse = b.horse
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


@register.simple_tag
def get_train_horse(i_rdate, i_horse):
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
                        from train a right outer join  ( select gate, rank, horse, jockey, trainer from The1.exp011 where rdate = '""" + i_rdate + """' and horse = '""" + i_horse + """' ) b on a.horse = b.horse
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
