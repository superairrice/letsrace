from django.db import connection
from base.models import Krafile

def get_krafile(rcity, rdate1, rdate2, fcode, fstatus):

  try:
    cursor = connection.cursor()

    strSql = """ 
              SELECT a.fname,   
                      @row:=@row+1 as No,
                  " " as rcheck,
                      a.fpath,
                      a.rdate,   
                      a.fcode,   
                      a.fstatus,   
                      a.in_date  
              FROM krafile a,(select @row :=0 from dual) b
              WHERE Left( Right( fname , 6), 2) like '""" + rcity + """%'
              AND rdate between '""" + rdate1 + """' and '""" + rdate2 + """'
              AND fcode like  '""" + fcode + """%'
              AND fstatus like  '""" + fstatus + """%'
            ; """

    r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
    result = cursor.fetchall()

    connection.commit()
    connection.close()

    # print(strSql)
    # print(result[0:5])

  except:
    connection.rollback()
    print("Failed selecting in krafile")

  return result

def get_kradata(rcity, rdate1, rdate2, fcode, fstatus):

  try:
    cursor = connection.cursor()

    strSql = """ 
              SELECT a.fname,   
                      @row:=@row+1 as No,
                  " " as rcheck,
                      a.rdate,   
                      a.fcode,   
                      a.fstatus,   
                      a.in_date  
              FROM kradata a,(select @row :=0 from dual) b
              WHERE Left( Right( fname , 6), 2) like '""" + rcity + """%'
              AND rdate between '""" + rdate1 + """' and '""" + rdate2 + """'
              AND fcode like  '""" + fcode + """%'
              AND fstatus like  '""" + fstatus + """%'
            ; """

    r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
    result = cursor.fetchall()

    connection.commit()
    connection.close()

    # print(strSql)
    # print(result[0:5])

  except:
    connection.rollback()
    print("Failed selecting in krafile")

  return result

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

    # print(strSql)
    # print(result[0:5])

  except:
    connection.rollback()
    print("Failed selecting in krafile")

  return str(result[0], 'cp949')


# def get_file_contents(fname):

#   result = Krafile.objects.values('fcontents').filter(fname=fname)
  

#   return (result)
