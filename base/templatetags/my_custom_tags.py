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
