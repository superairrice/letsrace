from apps.common import *
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from apps.domains.race.race import resultOfRace

# Prediction views

def racePrediction(request, rcity, rdate, rno, hname, awardee):

    view_type = (
        request.GET.get("view_type") if request.GET.get("view_type") != None else ""
    )  # 정렬방식

    if view_type == "1":
        exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
            "rank", "gate"
        )
    else:
        exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
            "r_pop", "gate"
        )
        
    compare_r = exp011s.aggregate(
        Min("i_s1f"),
        Min("i_g1f"),
        Min("i_g2f"),
        Min("i_g3f"),
        Max("handycap"),
        Max("rating"),
        Max("r_pop"),
        Max("j_per"),
        Max("t_per"),
        Max("jt_per"),
        Min("recent5"),
        Min("recent3"),
        Min("convert_r"),
        Min("s1f_rank"),
    )

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    hr_records = recordsByHorse(rcity, rdate, rno, 'None')
    # print(hr_records)

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    # paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
    # paternal_dist = get_paternal_dist(rcity, rdate, rno)  # 부마 거리별 3착 성적

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)
    judged_list, judged = get_judged(rcity, rdate, rno)

    # # # axis = get_axis(rcity, rdate, rno)
    # axis1 = get_axis_rank(rcity, rdate, rno, 1)
    # axis2 = get_axis_rank(rcity, rdate, rno, 2)
    # axis3 = get_axis_rank(rcity, rdate, rno, 3)

    track = get_track_record(
        rcity, rdate, rno
    )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

    # 경주 메모 Query
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT replace( replace( horse, '[서]', ''), '[부]', ''), r_etc, r_flag, judge
                FROM rec011 
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s;
            """
            cursor.execute(query, (rcity, rdate, rno))
            r_memo = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in 경주 메모: {e}")
    finally:
        cursor.close()

    # 경주일 - 출주정보
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT rcity, rdate, rno, rday, rseq, distance, rcount, grade, dividing,
                    rname, rcon1, rcon2, rtime
                FROM exp010 
                WHERE rdate = %s
                ORDER BY rdate, rtime;
            """
            cursor.execute(query, (rdate,))
            weeksrace = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in exp010 : 주별 경주현황 - {e}")

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    check_visit(request)

    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 기수 기승가능 부딤중량
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        "judged_list": judged_list,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        # "axis1": axis1,
        # "axis2": axis2,
        # "axis3": axis3,
        "r_memo": r_memo,
        "track": track,
        "weeksrace": weeksrace,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
        "view_type": view_type,
    }

    return render(request, "base/race_prediction.html", context)

def raceSimulation(request, rcity, rdate, rno, hname, awardee):

    weight = get_weight(rcity, rdate, rno)
    # print(weight[0][7])
    wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")
    mock_insert(rcity, rdate, rno)

    w_avg = (
        request.GET.get("w_avg") if request.GET.get("w_avg") != None else weight[0][0]
    )
    w_fast = (
        request.GET.get("w_fast") if request.GET.get("w_fast") != None else weight[0][1]
    )
    w_slow = (
        request.GET.get("w_slow") if request.GET.get("w_slow") != None else weight[0][2]
    )
    w_recent3 = (
        request.GET.get("w_recent3")
        if request.GET.get("w_recent3") != None
        else weight[0][3]
    )
    w_recent5 = (
        request.GET.get("w_recent5")
        if request.GET.get("w_recent5") != None
        else weight[0][4]
    )
    w_convert = (
        request.GET.get("w_convert")
        if request.GET.get("w_convert") != None
        else weight[0][5]
    )
    w_flag = (
        request.GET.get("w_flag") if request.GET.get("w_flag") != None else weight[0][6]
    )

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    weight_mock = (
        (
            int(w_avg),
            int(w_fast),
            int(w_slow),
            int(w_recent3),
            int(w_recent5),
            int(w_convert),
            w_flag,
        ),
    )  # tuple로 정의

    if weight == weight_mock:  # query 가중치와 입력된 가중치가 동일하면
        # print("같음")
        pass

    if (
        int(w_avg) + int(w_fast) + int(w_slow) == 100
        and int(w_recent3) + int(w_recent5) + int(w_convert) == 100  # 가중치 오류 check
    ):

        if weight != weight_mock:  # 가중치가 뱐경되었으면
            try:
                cursor = connection.cursor()

                strSql = (
                    """ 
                    insert into weight_s1 
                    (
                        rcity,
                        rdate,
                        rno,
                        wdate,
                        w_avg,
                        w_fast,
                        w_slow,
                        w_recent3,
                        w_recent5,
                        w_convert
                    )
                    VALUES
                    (
                        '"""
                    + rcity
                    + """',
                        '"""
                    + rdate
                    + """',
                        """
                    + str(rno)
                    + """,
                        """
                    " now() "
                    """,
                        """
                    + str(w_avg)
                    + """,
                        """
                    + str(w_fast)
                    + """,
                        """
                    + str(w_slow)
                    + """,
                        """
                    + str(w_recent3)
                    + """,
                        """
                    + str(w_recent5)
                    + """,
                        """
                    + str(w_convert)
                    + """
                    )
                ; """
                )

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                weight = cursor.fetchall()

            except:
                print("Failed inserting in weight_s1")
            finally:
                connection.close()

            mock = mock_traval(r_condition, weight_mock)

        if w_flag == 0:
            messages.warning(request, "weight_s1")

        else:
            messages.warning(request, "weight only")

    else:
        messages.warning(request, "오류")
        # weight = get_weight(rcity, rdate, rno)

    # print(
    #     "aaaa",
    #     int(w_avg) + int(w_fast) + int(w_slow),
    #     int(w_recent3) + int(w_recent5) + int(w_convert),
    # )
    # print(weight)

    exp011s = Exp011s1.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "rank", "gate"
    )

    if exp011s:
        pass
    else:
        return render(request, "base/home.html")

    hr_records = recordsByHorse(rcity, rdate, rno, 'None')

    # print(hr_records)
    compare_r = exp011s.aggregate(
        Min("i_s1f"),
        Min("i_g1f"),
        Min("i_g2f"),
        Min("i_g3f"),
        Max("handycap"),
        Max("rating"),
        Max("r_pop"),
        Max("j_per"),
        Max("t_per"),
        Max("jt_per"),
        Min("recent5"),
        Min("recent3"),
        Min("convert_r"),
        Min("s1f_rank"),
    )

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    track = get_track_record(
        rcity, rdate, rno
    )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

    # 경주 메모 Query
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT replace( replace( horse, '[서]', ''), '[부]', ''), r_etc, r_flag
                FROM rec011 
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s;
            """
            cursor.execute(query, (rcity, rdate, rno))
            r_memo = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in 경주 메모: {e}")
    finally:
        cursor.close()

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    trainer_double_check = get_trainer_double_check(rcity, rdate, rno)

    # axis = get_axis(rcity, rdate, rno)
    # axis1 = get_axis_rank(rcity, rdate, rno, 1)
    # axis2 = get_axis_rank(rcity, rdate, rno, 2)
    # axis3 = get_axis_rank(rcity, rdate, rno, 3)

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 기수 기승가능 부딤중량
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        "track": track,
        #    'swim': swim,
        # "h_audit": h_audit,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        # "axis1": axis1,
        # "axis2": axis2,
        # "axis3": axis3,
        "weight": weight,
        "wdate": wdate,
        "w_avg": w_avg,
        "w_fast": w_fast,
        "w_slow": w_slow,
        "w_recent3": w_recent3,
        "w_recent5": w_recent5,
        "w_convert": w_convert,
        "r_memo": r_memo,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
    }
    return render(request, "base/race_simulation.html", context)


# Race views

# 마방 경주마 보유현황

def printPrediction(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""

    if q == "":
        rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]  # 초기값은 금요일
        fdate = rdate[0:4] + "-" + rdate[4:6] + "-" + rdate[6:8]

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]
        fdate = q

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else "부산"
    view_type = request.GET.get("view_type") if request.GET.get("view_type") != None else "2"
    if view_type not in ("1", "2"):
        view_type = "2"

    race, expects = get_print_prediction(rcity, rdate, view_type=view_type)

    check_visit(request)

    if race:
        context = {
            "expects": expects,
            "race": race,
            "fdate": fdate,
            "view_type": view_type,
        }
    else:
        messages.warning(request, fdate + " " + rcity + " 경마 데이터가 없습니다.")
        context = {
            "expects": expects,
            "race": race,
            "fdate": fdate,
            "view_type": view_type,
        }

    # name = get_client_ip(request)
    # if name[0:6] != "15.177":
    #     update_visitor_count(name)

    #     # create a new Visitor instance
    #     new_visitor = Visitor(
    #         ip_address=name,
    #         user_agent=request.META.get("HTTP_USER_AGENT"),
    #         # referrer=request.META.get('HTTP_REFERER'),
    #         referer=rcity + " " + rdate + " " + "Print Prediction",
    #         # timestamp=timezone.now()
    #     )

    #     # insert the new_visitor object into the database
    #     new_visitor.save()

    return render(request, "base/print_prediction.html", context)


# 기수/조교사 주별 출주마 조교현황



def raceResult(request, rcity, rdate, rno, hname, rcity1, rdate1, rno1):
    # records = RecordS.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
    #     "rank", "gate"
    # )
    records = resultOfRace(rcity, rdate, rno)
    if not records:
        return render(request, "base/home.html")

    # r_condition = Rec010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    r_condition = Rec010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).first()
    if r_condition is None:
        return render(request, "base/home.html")

    # rdate_1year = (
    #     str(int(rdate[0:4]) - 1) + rdate[4:8]
    # )  # 최근 1년 경주성적 조회조건 추가

    # hr_records = RecordS.objects.filter(
    #     rdate__lt=rdate, horse__in=records.values("horse")
    # ).order_by("horse", "-rdate")

    hr_records = recordsByHorse(rcity, rdate, rno, "None")

    compare_r = Rec011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).aggregate(
        compare_i_s1f__min=Min("i_s1f"),
        compare_i_g1f__min=Min("i_g1f"),
        compare_i_g2f__min=Min("i_g2f"),
        compare_i_g3f__min=Min("i_g3f"),
        compare_handycap__max=Max("handycap"),
        compare_rating__max=Max("rating"),
    )

    # rec011 모델에 없는 필드(recent3/recent5/convert_r)는 resultOfRace 튜플에서 직접 산출
    def _min_tuple_value(rows, idx):
        vals = []
        for row in rows or []:
            if len(row) <= idx:
                continue
            v = row[idx]
            if v is None:
                continue
            s = str(v).strip()
            if not s:
                continue
            vals.append(s)
        return min(vals) if vals else None

    # race_result.html의 records 튜플 인덱스 기준
    # recent3:74, recent5:75, convert_r:79
    compare_r["compare_recent3__min"] = _min_tuple_value(records, 74)
    compare_r["compare_recent5__min"] = _min_tuple_value(records, 75)
    compare_r["compare_convert_r__min"] = _min_tuple_value(records, 79)

    judged_list, judged = get_judged(rcity, rdate, rno)
    track = get_track_record(rcity, rdate, rno)  # 경주 등급 평균

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    disease = get_disease(rcity, rdate, rno)

    # if len(judged) > 0:
    #     judged = judged[0][0]

    horses = Exp011.objects.values("horse").filter(rcity=rcity1, rdate=rdate1, rno=rno1)

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except Rec010.DoesNotExist:
        alloc = None

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT rcity, rdate, rno, rday, rseq, distance, rcount, grade, dividing, rname, rcon1, rcon2, rtime
                FROM exp010 
                WHERE rdate = %s
                ORDER BY rtime;
            """
            cursor.execute(query, (rdate,))
            weeksrace = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in exp010 : 주별 경주현황 - {e}")

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)
    check_visit(request)

    context = {
        "records": records,
        "r_condition": r_condition,
        "hr_records": hr_records,
        "compare_r": compare_r,
        "hname": hname,
        "judged_list": judged_list,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "horses": horses,
        "alloc": alloc,
        "weeksrace": weeksrace,
        "track": track,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "disease": disease,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
        **compare_r,
    }

    return render(request, "base/race_result.html", context)


# 출주마 경주결과

def raceResultHorse(request, rcity, rdate, rno, hname):

    hname = (
        request.GET.get("hname") if request.GET.get("hname") != None else hname.strip()
    )

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    exp011s = Exp011.objects.filter(
        rcity=rcity, rdate=rdate, rno=rno, horse=hname
    ).get()

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select gate, horse
            from exp011 
            where rcity = '"""
            + rcity
            + """'
            and rdate = '"""
            + rdate
            + """' 
            and rno = """
            + str(rno)
            + """
            order by rank, gate
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        h_names = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 게이트별 출주마")

    # 경주 메모 Query
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT replace( replace( horse, '[서]', ''), '[부]', ''), r_etc, r_flag
                FROM rec011 
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s;
            """
            cursor.execute(query, (rcity, rdate, rno))
            r_memo = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in 경주 메모: {e}")

    # train = get_train_horse1(rdate, hname)
    hr_records = recordsByHorse(rcity, rdate, rno, hname)

    check_visit(request)

    # print(hr_records)
    # print(hname in h_names)

    context = {
        "r_condition": r_condition,
        "hr_records": hr_records,
        "rdate": rdate,
        "exp011s": exp011s,
        "hname": hname,
        "h_names": h_names,
        "r_memo": r_memo,
    }

    return render(request, "base/race_result_horse.html", context)

# 축마 선정

def raceAxis(request, rcity, rdate, rno, jockey):

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno, jockey=jockey).get()
    if exp011s:
        pass
    else:
        return render(request, "base/home.html")

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    # axis = get_axis(rcity, rdate, rno)
    axis = get_axis_rank(rdate, jockey, r_condition.distance, exp011s.s1f_rank)

    # print(axis)
    # print(hname in h_names)

    context = {
        "axis": axis,
        "exp011s": exp011s,
        "r_condition": r_condition,
    }

    return render(request, "base/race_axis.html", context)

def raceTraining(request, rcity, rdate, rno):

    train = get_train_horse(rcity, rdate, rno)
    train_title = trend_title(rdate)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    check_visit(request)

    context = {
        "train": train,
        "train_title": train_title,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "r_condition": r_condition,
    }

    return render(request, "base/race_training.html", context)

def raceJudged(request, rcity, rdate, rno):

    pedigree = get_pedigree(rcity, rdate, rno)  # 병력
    treat = get_treat_horse(rcity, rdate, rno)
    judged_horse = get_judged_horse(rcity, rdate, rno)
    judged_jockey = get_judged_jockey(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    check_visit(request)

    context = {
        "pedigree": pedigree,
        "treat": treat,
        "judged_horse": judged_horse,
        "judged_jockey": judged_jockey,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "r_condition": r_condition,
    }

    return render(request, "base/race_judged.html", context)

def raceRelated(request, rcity, rdate, rno):

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    award_j, award_t, award_h, race_detail = get_race_related(rcity, rdate, rno)
    
    loadin = get_loadin(rcity, rdate, rno)

    judged_jockey = get_judged_jockey(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    check_visit(request)

    context = {
        "r_condition": r_condition,  # 기수 기승가능 부딤중량
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "judged_jockey": judged_jockey,
        "race_detail": race_detail,
        "award_j": award_j,
        "award_t": award_t,
        "award_h": award_h,
        "training_cnt": training_cnt,
        "trainer_double_check": str(trainer_double_check),
    }

    return render(request, "base/race_related.html", context)

def raceRelatedInfo(request, rcity, rdate, rno):

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    train = get_train_horse(rcity, rdate, rno)

    train_title = trend_title(rdate)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    pedigree = get_pedigree(rcity, rdate, rno)  # 병력
    treat = get_treat_horse(rcity, rdate, rno)
    judged_horse = get_judged_horse(rcity, rdate, rno)
    judged_jockey = get_judged_jockey(rcity, rdate, rno)

    # award_j, award_t, award_h, race_detail = get_race_related(rcity, rdate, rno)

    paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
    paternal_dist = get_paternal_dist(rcity, rdate, rno)  # 부마 거리별 3착 성적

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    try:
        cursor = connection.cursor()
        strSql = """ 
            select host, horse, trainer, birthplace, sex, age, grade, tot_race, tot_1st, tot_2nd, tot_3rd, year_race, year_1st, year_2nd, year_3rd, tot_prize/1000, rating, price/1000
            from horse_w
            where wdate = ( select max(wdate) from The1.horse_w where wdate < %s )  
            and host in  ( select host from exp011 where rcity =  %s and rdate = %s and rno =  %s )
            order by host, trainer, horse
        """
        # 안전한 SQL 파라미터 바인딩
        params = (
            rdate,
            rcity,
            rdate,
            rno,
        )

        cursor.execute(strSql, params)
        horses = cursor.fetchall()

    except:
        print(f"❌ Failed selecting in horses:")  # 오류 메시지 출력
    finally:
        cursor.close()

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    view_type = (
        request.GET.get("view_type") if request.GET.get("view_type") != None else ""
    )  # 정렬방식
    if view_type == "1":
        # train는 raw SQL fetchall 결과(튜플)일 수 있음. 안전하게 정렬 키를 구성.
        def _exp_key(row):
            # 객체(Attr) 또는 튜플(Idx) 모두 지원
            if hasattr(row, "rcity"):
                return (row.rcity, row.rdate, row.rno, row.rank, row.gate)
            # 튜플 인덱스: a.rcity(0), a.rdate(1), a.rno(3), b.gate(4), b.rank(5)
            try:
                return (row[0], row[1], row[3], row[5], row[4])
            except Exception:
                return row

        train = sorted(train, key=_exp_key)

    # print(start_cnt)

    context = {
        "r_condition": r_condition,  # 기수 기승가능 부딤중량
        "train": train,  # 기수 기승가능 부딤중량
        "train_title": train_title,  # 기수 기승가능 부딤중량
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "pedigree": pedigree,  # 기수 기승가능 부딤중량
        "treat": treat,  # 기수 기승가능 부딤중량
        "judged_horse": judged_horse,  # 기수 기승가능 부딤중량
        "judged_jockey": judged_jockey,
        "start_cnt": start_cnt,
        "recovery_cnt": recovery_cnt,
        "audit_cnt": audit_cnt,
        # "award_h": award_h,
        # "race_detail": race_detail,
        "paternal": paternal,  
        "paternal_dist": paternal_dist,  
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 경주마 중대 질병 진료 회수
        "horses": horses,  
    }

    return render(request, "base/race_related_info.html", context)

def statusStable(request, rcity, rdate, rno):

    # r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    # print(r_condition)

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).first()
    if not r_condition:
        # 1) 가장 무난: 404
        from django.http import Http404

        raise Http404("Exp010 not found")

        # 2) 또는: 빈 화면/기본값으로 처리하고 싶으면
        # return render(request, "some_template.html", {"warning": "데이터 없음"})

    stable, stable_g, stable_h = get_status_stable(rcity, rdate, rno)
    stable_list = stable.values.tolist()
    stable_list_g = stable_g.values.tolist()
    stable_title = stable.columns.tolist() 

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select a.trainer
                from exp011 a
                where a.rcity =  '"""
            + rcity
            + """'
                and a.rdate = '"""
            + rdate
            + """'
                and a.rno =  """
            + str(rno)
            + """
                group by a.rcity, a.rdate, a.rno, a.trainer
                having count(*) >= 2

                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        trainer_double_check = cursor.fetchall()

    except:
        print("Failed selecting in trainer double cheeck")
    finally:
        connection.close()

    context = {
        "r_condition": r_condition,
        "stable_list": stable_list,
        "stable_list_g": stable_list_g,
        "stable_title": stable_title,
        "stable_h": stable_h,
        "trainer_double_check": str(trainer_double_check),
    }

    return render(request, "base/status_stable.html", context)


# 기수 or 조교사 최근 12주 성적 / 99일 경주결과

def raceTrain(request, rcity, rdate, rno):
    train = get_train_horse(rcity, rdate, rno)

    context = {
        "train": train,
    }

    return render(request, "base/race_train.html", context)

def trainingAwardee(request, rdate, awardee, name, hname):

    status = get_training_awardee(rdate, awardee, name)
    train_title = trend_title(rdate)

    # print(status)

    context = {
        "status": status,
        "train_title": train_title,
        "awardee": awardee,
        "name": name,
        "hname": hname,
    }

    return render(request, "base/training_awardee.html", context)

# 출주마 이전 조교현황

def trainingHorse(request, rcity, rdate, rno, hname):

    hname = request.GET.get("hname") if request.GET.get("hname") != None else hname.strip()

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno, horse=hname).get()

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select gate, horse
            from exp011 
            where rcity = '"""
            + rcity
            + """'
            and rdate = '"""
            + rdate
            + """' 
            and rno = """
            + str(rno)
            + """
            order by gate
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        h_names = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 게이트별 출주마")

    train = get_train_horse1(rdate, hname)
    check_visit(request)

    # print(exp011s.rdate)
    # print(hname in h_names)

    context = {
        "r_condition": r_condition,
        "train": train,
        "rdate": rdate,
        "exp011s": exp011s,
        "hname": hname,
        "h_names": h_names,
    }

    return render(request, "base/training_horse.html", context)


# 기수 마방 연대 현황

def jtCollaboration(request, rcity, rdate, rno, jockey, trainer):

    collaboration = get_jt_collaboration(rcity, rdate, rno, jockey, trainer)
    check_visit(request)

    context = {
        "collaboration": collaboration,
        "rdate": rdate,
    }

    return render(request, "base/jt_collaboration.html", context)


# 기수 최근 2주간 훈련현황

def jockey2weekTrain(request, rcity, rdate, rno):

    j2week = get_jockeys_train(rcity, rdate, rno)

    context = {
        "j2week": j2week,
        "rdate": rdate,
    }

    return render(request, "base/jockey_2week_train.html", context)

def weeksStatus(request, rcity, rdate):
    status = get_weeks_status(rcity, rdate)

    rank1 = [item for item in status if item[15] == 1]  # item[15] : 예상착순(rank)
    rank2 = [item for item in status if item[15] == 2]  # item[15] : 예상착순(rank)
    rank3 = [item for item in status if item[15] == 3]  # item[15] : 예상착순(rank)
    r_rank1 = [item for item in status if item[16] == 1]  # item[16] : 실제착순(r_rank)
    r_rank2 = [item for item in status if item[16] == 2]  # item[16] : 실제착순(r_rank)
    r_rank3 = [item for item in status if item[16] == 3]  # item[16] : 실제착순(r_rank)

    try:
        cursor = connection.cursor()

        strSql = """
            SELECT jockey, CAST(load_in AS DECIMAL)
            FROM jockey_w
            WHERE wdate = (SELECT MAX(wdate) FROM jockey_w WHERE wdate < %s);
        """
        cursor.execute(strSql, (rdate,))
        loadin = cursor.fetchall()

    except:
        print("Failed selecting in 기승가능중량")
    finally:
        cursor.close()

    # print(status)

    context = {
        "status": status,
        "loadin": loadin,
        "rank1": len(rank1),
        "rank2": len(rank2),
        "rank3": len(rank3),
        "r_rank1": len(r_rank1),
        "r_rank2": len(r_rank2),
        "r_rank3": len(r_rank3),
        "rcount": len(status),
        "winname": "weeksStatus",
    }

    return render(request, "base/weeks_status.html", context)

def trendWinningRate(request, rcity, rdate, rno, awardee, i_filter):
    if awardee == "jockey":
        trend_data, trend_title = get_jockey_trend(rcity, rdate, rno)
        # solidarity = get_solidarity(
        #     rcity, rdate, rno, "jockey", i_filter
        # )  # 기수, 조교사, 마주 연대현황 최근1년

    else:
        trend_data, trend_title = get_trainer_trend(rcity, rdate, rno)
        # solidarity = get_solidarity(
        #     rcity, rdate, rno, "trainer", i_filter
        # )  # 기수, 조교사, 마주 연대현황 최근1년

    # print(solidarity)
    # print(trend_title)

    trend_j = trend_data.values.tolist()
    trend_j_title = trend_data.columns.tolist()

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    
    try:
        cursor = connection.cursor()

        strSql = """  
            select b.rcity,
                b.jockey awardee,
                b.rdate,
                a.rday,
                b.rno,
                a.grade,
                dividing,
                b.gate,
                b.rank,
                b.r_rank,
                b.horse,
                b.remark,
                b.jockey j_name,
                b.trainer t_name, b.host h_name,
                r_pop,
                a.distance,
                handycap,
                jt_per,
                jt_cnt,
                remark,
                s1f_rank,
                replace( corners, ' ', '') corners,
                g3f_rank,
                g1f_rank,
                alloc3r,
                jockey_old,
                reason
            from The1.exp010 a, The1.exp011 b 
            where a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno
            and a.rdate between date_format(DATE_ADD(%s, INTERVAL - 4 DAY), '%%Y%%m%%d') and date_format(DATE_ADD(%s, INTERVAL + 3 DAY), '%%Y%%m%%d')
            and a.rno < 80
            order by a.rdate, a.rtime, gate
            ; """
        cursor.execute(strSql, (rdate, rdate))
        race_detail = cursor.fetchall()

    except:
        print("Failed selecting in expect : 경주별 Detail(약식)) ")
    finally:
        cursor.close()

    context = {
        "trend_j": trend_j,
        "trend_j_title": trend_j_title,
        "trend_title": trend_title,
        "r_condition": r_condition,
        "awardee": awardee,
        "race_detail": race_detail,
        # "solidarity": solidarity,
    }

    return render(request, "base/trend_winning_rate.html", context)


# 출주주기별 마방 승률 - 최근 1년

def cycleWinningRate(request, rcity, rdate, rno, awardee, i_filter):
    if awardee == "jockey":
        trend_data, trend_title = get_jockey_trend(rcity, rdate, rno)
        # solidarity = get_solidarity(
        #     rcity, rdate, rno, "jockey", i_filter
        # )  # 기수, 조교사, 마주 연대현황 최근1년

    else:
        trend_data = get_cycle_winning_rate(rcity, rdate, rno)
        # solidarity = get_solidarity(
        #     rcity, rdate, rno, "trainer", i_filter
        # )  # 기수, 조교사, 마주 연대현황 최근1년

    # print(solidarity)
    # print(trend_title)

    trend_j = trend_data.values.tolist()

    trend_j_title = trend_data.columns.tolist()

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    trainer_double_check = get_trainer_double_check(rcity, rdate, rno)
    # print(trainer_double_check)

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    context = {
        "trend_j": trend_j,
        "trend_j_title": trend_j_title,
        "r_condition": r_condition,
        "awardee": awardee,
        # "solidarity": solidarity,
        "trainer_double_check": str(trainer_double_check),
        "alloc": alloc,
    }

    return render(request, "base/cycle_winning_rate.html", context)


# thethe9 rank1 실경주 입상현황

def jtAnalysis(
    request,
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

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else rcity
    fdate = (
        request.GET.get("fdate")
        if request.GET.get("fdate") != None
        else fdate[0:4] + "-" + fdate[4:6] + "-" + fdate[6:8]
    )
    tdate = (
        request.GET.get("tdate")
        if request.GET.get("tdate") != None
        else tdate[0:4] + "-" + tdate[4:6] + "-" + tdate[6:8]
    )
    jockey = request.GET.get("jockey") if request.GET.get("jockey") != None else jockey
    trainer = (
        request.GET.get("trainer") if request.GET.get("trainer") != None else trainer
    )
    host = request.GET.get("host") if request.GET.get("host") != None else host
    horse = request.GET.get("horse") if request.GET.get("horse") != None else horse
    r1 = request.GET.get("r1") if request.GET.get("r1") != None else r1
    r2 = request.GET.get("r2") if request.GET.get("r2") != None else r2
    rr1 = request.GET.get("rr1") if request.GET.get("rr1") != None else rr1
    rr2 = request.GET.get("rr2") if request.GET.get("rr2") != None else rr2
    gate = request.GET.get("gate") if request.GET.get("gate") != None else gate
    distance = (
        request.GET.get("distance") if request.GET.get("distance") != None else distance
    )
    handycap = (
        request.GET.get("handycap") if request.GET.get("handycap") != None else handycap
    )

    # print('2', fdate, tdate, jockey, trainer, host, horse, r1, r2, rr1, rr2)

    # if fdate == "":
    #     # fdate =
    #     pass
    # else:
    #     fdate = fdate[0:4] + fdate[5:7] + fdate[8:10]
    #     tdate = tdate[0:4] + tdate[5:7] + tdate[8:10]

    status = get_thethe9_ranks(
        rcity,
        fdate[0:4] + fdate[5:7] + fdate[8:10],
        tdate[0:4] + tdate[5:7] + tdate[8:10],
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
    )

    rank1 = [item for item in status if item[15] == 1]  # item[15] : 예상착순(rank)
    rank2 = [item for item in status if item[15] == 2]  # item[15] : 예상착순(rank)
    rank3 = [item for item in status if item[15] == 3]  # item[15] : 예상착순(rank)
    r_rank1 = [item for item in status if item[16] == 1]  # item[16] : 실제착순(r_rank)
    r_rank2 = [item for item in status if item[16] == 2]  # item[16] : 실제착순(r_rank)
    r_rank3 = [item for item in status if item[16] == 3]  # item[16] : 실제착순(r_rank)

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT jockey, CAST(load_in AS DECIMAL)
                FROM jockey_w
                WHERE wdate = (SELECT MAX(wdate) FROM jockey_w WHERE wdate < %s);
            """
            cursor.execute(query, (tdate[0:4] + tdate[5:7] + tdate[8:10],))
            loadin = cursor.fetchall()

    except Exception as e:
        print(f"Failed selecting in 기승가능중량: {e}")

    
    # check_visit(request)

    context = {
        "status": status,
        "loadin": loadin,
        "rcity": rcity,
        "fdate": fdate,
        "tdate": tdate,
        "today": tdate[0:4] + tdate[5:7] + tdate[8:10],
        "jockey": jockey,
        "trainer": trainer,
        "host": host,
        "horse": horse,
        "r1": r1,
        "r2": r2,
        "rr1": rr1,
        "rr2": rr2,
        "gate": gate,
        "distance": distance,
        "handycap": handycap[0:2],
        "rank1": len(rank1),
        "rank2": len(rank2),
        "rank3": len(rank3),
        "r_rank1": len(r_rank1),
        "r_rank2": len(r_rank2),
        "r_rank3": len(r_rank3),
        "rcount": len(status),
    }

    return render(request, "base/jt_analysis.html", context)


# thethe9 rank1 실경주 입상현황

def jtAnalysisJockey(
    request,
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
    rno,
):

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else rcity
    fdate = (
        request.GET.get("fdate")
        if request.GET.get("fdate") != None
        else fdate[0:4] + "-" + fdate[4:6] + "-" + fdate[6:8]
    )
    tdate = (
        request.GET.get("tdate")
        if request.GET.get("tdate") != None
        else tdate[0:4] + "-" + tdate[4:6] + "-" + tdate[6:8]
    )
    jockey = request.GET.get("jockey") if request.GET.get("jockey") != None else jockey
    trainer = (
        request.GET.get("trainer") if request.GET.get("trainer") != None else trainer
    )
    host = request.GET.get("host") if request.GET.get("host") != None else host
    jockey_b = (
        request.GET.get("jockey_b") if request.GET.get("jockey_b") != None else jockey_b
    )
    r1 = request.GET.get("r1") if request.GET.get("r1") != None else r1
    r2 = request.GET.get("r2") if request.GET.get("r2") != None else r2
    rr1 = request.GET.get("rr1") if request.GET.get("rr1") != None else rr1
    rr2 = request.GET.get("rr2") if request.GET.get("rr2") != None else rr2
    gate = request.GET.get("gate") if request.GET.get("gate") != None else gate
    distance = (
        request.GET.get("distance") if request.GET.get("distance") != None else distance
    )
    handycap = (
        request.GET.get("handycap") if request.GET.get("handycap") != None else handycap
    )
    rno = request.GET.get("rno") if request.GET.get("rno") != None else rno

    # print('2', fdate, tdate, jockey, trainer, host, horse, r1, r2, rr1, rr2)

    # if fdate == "":
    #     # fdate =
    #     pass
    # else:
    #     fdate = fdate[0:4] + fdate[5:7] + fdate[8:10]
    #     tdate = tdate[0:4] + tdate[5:7] + tdate[8:10]

    status = get_thethe9_ranks_jockey(
        rcity,
        fdate[0:4] + fdate[5:7] + fdate[8:10],
        tdate[0:4] + tdate[5:7] + tdate[8:10],
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
    )

    rank1 = [item for item in status if item[15] == 1]  # item[15] : 예상착순(rank)
    rank2 = [item for item in status if item[15] == 2]  # item[15] : 예상착순(rank)
    rank3 = [item for item in status if item[15] == 3]  # item[15] : 예상착순(rank)
    r_rank1 = [item for item in status if item[16] == 1]  # item[16] : 실제착순(r_rank)
    r_rank2 = [item for item in status if item[16] == 2]  # item[16] : 실제착순(r_rank)
    r_rank3 = [item for item in status if item[16] == 3]  # item[16] : 실제착순(r_rank)

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT jockey, CAST(load_in AS DECIMAL)
                FROM jockey_w
                WHERE wdate = (SELECT MAX(wdate) FROM jockey_w WHERE wdate < %s);
            """
            cursor.execute(query, (tdate[0:4] + tdate[5:7] + tdate[8:10],))
            loadin = cursor.fetchall()

    except Exception as e:
        print(f"Failed selecting in 기승가능중량: {e}")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select gate, jockey
            from exp011 
            where rcity = '"""
            + rcity
            + """'
            and rdate = '"""
            + tdate[0:4]
            + tdate[5:7]
            + tdate[8:10]
            + """' 
            and rno = """
            + str(rno)
            + """
            order by gate, jockey
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        jockeys = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기승가능중량")

    # print(jockeys)
    check_visit(request)

    context = {
        "status": status,
        "loadin": loadin,
        "rcity": rcity,
        "fdate": fdate,
        "tdate": tdate,
        "today": tdate[0:4] + tdate[5:7] + tdate[8:10],
        "jockey": jockey,
        "trainer": trainer,
        "host": host,
        "jockey_b": jockey_b,
        "r1": r1,
        "r2": r2,
        "rr1": rr1,
        "rr2": rr2,
        "gate": gate,
        "distance": distance,
        "handycap": handycap[0:2],
        "rank1": len(rank1),
        "rank2": len(rank2),
        "rank3": len(rank3),
        "r_rank1": len(r_rank1),
        "r_rank2": len(r_rank2),
        "r_rank3": len(r_rank3),
        "rcount": len(status),
        "rno": rno,
        "jockeys": jockeys,
    }

    return render(request, "base/jt_analysis_jockey.html", context)

def jtAnalysisMulti(
    request,
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
    rno,
    start,
):

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else rcity
    fdate = (
        request.GET.get("fdate")
        if request.GET.get("fdate") != None
        else fdate[0:4] + "-" + fdate[4:6] + "-" + fdate[6:8]
    )
    tdate = (
        request.GET.get("tdate")
        if request.GET.get("tdate") != None
        else tdate[0:4] + "-" + tdate[4:6] + "-" + tdate[6:8]
    )
    jockey = request.GET.get("jockey") if request.GET.get("jockey") != None else jockey.strip()
    trainer = (
        request.GET.get("trainer") if request.GET.get("trainer") != None else trainer.strip()
    )
    host = request.GET.get("host") if request.GET.get("host") != None else host.strip()
    jockey_b = (
        request.GET.get("jockey_b")
        if request.GET.get("jockey_b") != None
        else jockey_b.strip()
    )
    r1 = request.GET.get("r1") if request.GET.get("r1") != None else r1
    r2 = request.GET.get("r2") if request.GET.get("r2") != None else r2
    rr1 = request.GET.get("rr1") if request.GET.get("rr1") != None else rr1
    rr2 = request.GET.get("rr2") if request.GET.get("rr2") != None else rr2
    gate = request.GET.get("gate") if request.GET.get("gate") != None else gate
    distance = (
        request.GET.get("distance") if request.GET.get("distance") != None else distance
    )
    handycap = (
        request.GET.get("handycap") if request.GET.get("handycap") != None else handycap
    )
    rno = request.GET.get("rno") if request.GET.get("rno") != None else rno
    start = request.GET.get("start") if request.GET.get("start") != None else start

    # print('2', fdate, tdate, jockey, trainer, host, jockey_b, r1, r2, rr1, rr2)
    # print(tdate)

    # if fdate == "":
    #     # fdate =
    #     pass
    # else:
    #     fdate = fdate[0:4] + fdate[5:7] + fdate[8:10]
    #     tdate = tdate[0:4] + tdate[5:7] + tdate[8:10]

    status = get_thethe9_ranks_multi(
        rcity,
        fdate[0:4] + fdate[5:7] + fdate[8:10],
        tdate[0:4] + tdate[5:7] + tdate[8:10],
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
        start,
    )

    rank1 = [item for item in status if item[29] == 1]  # item[29] : 예상착순(rank)
    rank2 = [item for item in status if item[29] == 2]  # item[29] : 예상착순(rank)
    rank3 = [item for item in status if item[29] == 3]  # item[29] : 예상착순(rank)
    r_rank1 = [item for item in status if item[16] == 1]  # item[16] : 실제착순(r_rank)
    r_rank2 = [item for item in status if item[16] == 2]  # item[16] : 실제착순(r_rank)
    r_rank3 = [item for item in status if item[16] == 3]  # item[16] : 실제착순(r_rank)

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT jockey, CAST(load_in AS DECIMAL)
                FROM jockey_w
                WHERE wdate = (SELECT MAX(wdate) FROM jockey_w WHERE wdate < %s);
            """
            cursor.execute(query, (tdate[0:4] + tdate[5:7] + tdate[8:10],))
            loadin = cursor.fetchall()

    except Exception as e:
        print(f"Failed selecting in 기승가능중량: {e}")

    # 경주별 출주 기수, 조교사, 마주 
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT gate, jockey, trainer, host, horse
                FROM exp011 
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s
                ORDER BY gate, jockey;
            """
            cursor.execute(query, (rcity, tdate[0:4] + tdate[5:7] + tdate[8:10], rno))
            jockeys = cursor.fetchall()

    except Exception as e:
        print(f"Failed selecting in 기승가능중량: {e}")

    # print(jockeys)
    j_string=""
    t_string=""
    h_string=""
    for i, j in enumerate(jockeys):
        # print(i, j[1], j[2], j[3])
        j_string = j_string + j[1]
        t_string = t_string + j[2]
        h_string = h_string + j[3]

    check_visit(request)

    context = {
        "status": status,
        "loadin": loadin,
        "rcity": rcity,
        "fdate": fdate,
        "tdate": tdate,
        "today": tdate[0:4] + tdate[5:7] + tdate[8:10],
        "jockey": jockey,
        "trainer": trainer,
        "host": host,
        "jockey_b": jockey_b,
        "r1": r1,
        "r2": r2,
        "rr1": rr1,
        "rr2": rr2,
        "gate": gate,
        "distance": distance,
        "handycap": handycap[0:2],
        "rank1": len(rank1),
        "rank2": len(rank2),
        "rank3": len(rank3),
        "r_rank1": len(r_rank1),
        "r_rank2": len(r_rank2),
        "r_rank3": len(r_rank3),
        "rcount": len(status),
        "rno": rno,
        "start": start,
        "jockeys": jockeys,
        "j_string": j_string,
        "t_string": t_string,
        "h_string": h_string,
    }

    return render(request, "base/jt_analysis_multi.html", context)


# Reports views


def awards(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q)
    )

    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )

    room_count = Exp011.objects.all().count()
    room_messages = Message.objects.filter(Q(room__name__icontains=q))

    # rdates = Racing.objects.distinct().values_list('rdate')
    rdays = (
        Racing.objects.distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rdate", "-rcity", "rno")
    )

    seoul = (
        Racing.objects.filter(rcity="서울")
        .values("rdate", "rday")
        .annotate(rcount=Count("rdate"))
    )
    busan = (
        Racing.objects.filter(rcity="부산")
        .values("rdate", "rday")
        .annotate(rcount=Count("rdate"))
    )

    seoul_fri = (
        Racing.objects.filter(rcity="서울", rday="금")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    seoul_sat = (
        Racing.objects.filter(rcity="서울", rday="토")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    seoul_sun = (
        Racing.objects.filter(rcity="서울", rday="일")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    busan_fri = (
        Racing.objects.filter(rcity="부산", rday="금")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    busan_sat = (
        Racing.objects.filter(rcity="부산", rday="토")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    busan_sun = (
        Racing.objects.filter(rcity="부산", rday="일")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )

    # print(seoul_sat)

    first_race = racings[0]  # 첫번째 경주 조건

    exp011s = Exp011.objects.filter(
        rcity=first_race.rcity, rdate=first_race.rdate, rno=first_race.rno
    ).order_by("rank")

    horse = Exp011.objects.filter(
        rcity=first_race.rcity, rdate=first_race.rdate, rno=first_race.rno, rank=1
    ).get()

    # print(datetime.today().weekday())
    # print(seoul)

    h_records = RecordS.objects.filter(horse=horse.horse).order_by("-rdate")

    # 금주 경주예상 종합

    rdate = Racing.objects.values("rdate").distinct()
    # print(rdate[0]['rdate'])

    i_rdate = rdate[0]["rdate"]
    awards = get_award(i_rdate, i_awardee="jockey")

    r_results = RaceResult.objects.all().order_by("rdate", "rcity", "rno")
    # .filter( rdate__in=rdate.values_list('rdate', flat=True))

    allocs = Rec010.objects.filter(
        rdate__in=rdate.values_list("rdate", flat=True)
    ).order_by("rdate", "rcity", "rno")

    print(awards)

    context = {
        "rooms": rooms,
        "racings": racings,
        "room_count": room_count,
        "room_messages": room_messages,
        "rdays": rdays,
        "first_race": first_race,
        "exp011s": exp011s,
        "horse": horse,
        "seoul": seoul,
        "seoul_fri": seoul_fri,
        "seoul_sat": seoul_sat,
        "seoul_sun": seoul_sun,
        "busan_fri": busan_fri,
        "busan_sat": busan_sat,
        "busan_sun": busan_sun,
        "rdate": rdate,
        "r_results": r_results,
        "allocs": allocs,
        "awards": awards,
        "busan": busan,
        "h_records": h_records,
    }

    return render(request, "base/awards.html", context)


@login_required(login_url="account_login")

def raceReport(request, rcity, rdate, rno):
    r_content = (
        request.GET.get("r_content") if request.GET.get("r_content") != None else ""
    )
    fdata = request.GET.get("fdata") if request.GET.get("fdata") != None else ""

    if fdata == "-":
        print(fdata)
    elif fdata == "마체중":
        set_changed_race_weight(rcity, rdate, rno, r_content)
    elif fdata == "경주순위":
        set_changed_race_rank(rcity, rdate, rno, r_content)
    elif fdata == "경주마취소":
        set_changed_race_horse(rcity, rdate, rno, r_content)
    elif fdata == "기수변경":
        set_changed_race_jockey(rcity, rdate, rno, r_content)

    rec011s, r_start, r_corners, r_finish, r_wrapup = get_report_code(rcity, rdate, rno)

    context = {
        "rcity": rcity,
        "rec011s": rec011s,
        "r_start": r_start,
        "r_corners": r_corners,
        "r_finish": r_finish,
        "r_wrapup": r_wrapup,
    }

    if request.method == "POST":
        myDict = dict(request.POST)
        print(myDict)

        for (
            rcity,
            rdate,
            rno,
            rank,
            gate,
            horse,
            r_start,
            r_corners,
            r_finish,
            r_wrapup,
            r_etc,
        ) in rec011s:
            pop = "pop_" + str(gate)
            # print(myDict[pop][0])

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update rec011 
                                set r_start = '"""
                    + myDict[pop][0]
                    + """',
                                    r_corners = '"""
                    + myDict[pop][1]
                    + """'
                            where rdate = '"""
                    + rdate
                    + """' and rcity = '"""
                    + rcity
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(gate)
                    + """
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
                print("Failed updating in rec011")

        # form = Exp011(request.POST, request.FILES, rcity=rcity, rdate=rdate, rno=rno, instance=pop_1)
        # if form.is_valid():
        #     form.save()
        #     redirect('user-profile', pk=rdate)

    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)
    return render(request, "base/race_report.html", context)


@login_required(login_url="account_login")

def raceReview(request, rcity, rdate, rno):

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    # print(r_condition.rcount)

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    judged_list, judged = get_judged(rcity, rdate, rno)

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    # exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)

    # user = request.user
    # form = UserForm(instance=user)

    if request.method == "POST":

        myDict = dict(request.POST)
        # print(myDict)
        # print(myDict['judge'][0])
        # print(exp011_cnt)

        for i in range(1, int(r_condition.rcount) +1 ):

            # print(i, myDict["r_etc"][i - 1])
            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011
                                set r_rank = """
                    + myDict['r_rank'][i - 1]
                    + """
                            where rcity = '"""
                    + rcity
                    + """' and rdate = '"""
                    + rdate
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(i)
                    + """
                        ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

            except:
                # connection.rollback()
                print("Failed updating in exp011")

            try:

                cursor = connection.cursor()

                strSql = (
                    """ update rec011
                                set judge = '""" + myDict['judge'][0] + """' 
                                , r_start = '""" + myDict['start'][i - 1] + """'
                                , r_flag = '""" + myDict['flag'][i - 1] + """'
                                , r_etc = '""" + myDict['r_etc'][i - 1] + """' 
                                
                            where rcity = '"""
                    + rcity
                    + """' and rdate = '"""
                    + rdate
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(i)
                    + """
                        ; """
                )

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

            except:
                # connection.rollback()
                print("Failed updating in rec011")

    try:
        cursor = connection.cursor()
        strSql = """ select cd_type, r_code, r_name from race_cd order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race_cd = cursor.fetchall()

    except:
        print("Failed selecting r_start")
    finally:
        cursor.close()

    try:
        cursor = connection.cursor()
        strSql = (
            """ select a.rcity, a.rdate, a.rno, a.gate, a.horse, a.jockey, a.trainer, a.rank, a.r_rank, a.h_sex, a.h_age, a.birthplace, a.i_cycle, a.h_weight, a.handycap, a.i_prehandy, a.reason, a.alloc1r, a.alloc3r,
                    b.r_start, b.r_flag, b.r_etc, TRIM(b.judge)
            from exp011 a, rec011 b
            where a.rcity = b.rcity
            and a.rdate = b.rdate
            and a.rno = b.rno
            and a.gate = b.gate
            and a.rcity = '"""
            + rcity
            + """'
            and a.rdate = '"""
            + rdate
            + """' 
            and a.rno = """
            + str(rno)
            + """
            order by a.gate 
            ; """
        )

        # print(strSql)

        exp011_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        exp011s = cursor.fetchall()

        # print(r_cnt)

    except:
        print("Failed selecting expext record")
    finally:
        cursor.close()

    context = {
        "rcity": rcity,
        "exp011s": exp011s,
        "r_condition": r_condition,
        "race_cd": race_cd,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 기수 기승가능 부딤중량
        "judged_list": judged_list,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
    }
    return render(request, "base/race_review.html", context)

def raceBreakingNews(request):
    def _decode_kra_bytes(body):
        if not body:
            return ""
        # 1) BOM/UTF-8 우선
        for enc in ("utf-8-sig", "utf-8"):
            try:
                return body.decode(enc)
            except Exception:
                pass

        # 2) KRA 페이지에서 흔한 한글 인코딩 fallback
        decoded_candidates = []
        for enc in ("cp949", "euc-kr"):
            try:
                txt = body.decode(enc)
                decoded_candidates.append(txt)
            except Exception:
                pass

        if not decoded_candidates:
            # 마지막 fallback (깨짐 방지 최소화)
            return body.decode("latin-1", errors="ignore")

        def _score(text):
            # 한글/핵심 키워드가 많이 포함된 디코딩 결과를 우선
            hangul_cnt = len(re.findall(r"[가-힣]", text))
            keyword_cnt = sum(
                text.count(k)
                for k in (
                    "출전표",
                    "변경",
                    "경주",
                    "서울",
                    "부산",
                    "부경",
                    "기수",
                    "마필",
                )
            )
            return hangul_cnt + (keyword_cnt * 20)

        return max(decoded_candidates, key=_score)

    def _strip_html(value):
        if value is None:
            return ""
        text = str(value)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", unescape(text)).strip()

    def _normalize_changed_race_text(raw_text):
        if not raw_text:
            return ""

        def _norm_city(city):
            city = (city or "").strip()
            if city in ("부산경남", "부산", "부경"):
                return "부경"
            if city == "서울":
                return "서울"
            if city == "제주":
                return "제주"
            return city

        def _norm_date(date_text):
            m = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", date_text or "")
            if not m:
                return ""
            return f"{m.group(1)}.{int(m.group(2)):02d}.{int(m.group(3)):02d}"

        lines = [re.sub(r"\s+", " ", (ln or "")).strip() for ln in str(raw_text).splitlines()]
        lines = [ln for ln in lines if ln]

        section = ""
        normalized_rows = []

        for ln in lines:
            if "말취소" in ln:
                section = "cancel"
                continue
            if "기수변경" in ln:
                section = "jockey"
                continue
            if any(k in ln for k in ("출발시각변경", "경주취소", "출전표변경", "홈 >", "Copyright")):
                section = ""
                continue

            # 불필요 헤더/메뉴 행 스킵
            if any(
                key in ln
                for key in (
                    "경마사이트링크",
                    "금주의경마",
                    "출전정보",
                    "말취소내용",
                    "기수변경내용",
                    "지역 경주일자",
                    "지역\t경주일자",
                    "경주번호",
                    "출전번호",
                    "변경전",
                    "변경후",
                )
            ):
                continue

            if section not in ("cancel", "jockey"):
                continue

            # 첫 토큰이 지역(서울/부경/제주)이어야 실제 데이터 행으로 간주
            if not re.match(r"^(서울|부경|부산경남|제주)\b", ln):
                continue

            # 공백 기준 토큰화(사유는 나머지 전체로 보존)
            parts = ln.split(" ")
            if len(parts) < 6:
                continue

            city = _norm_city(parts[0])
            date_txt = _norm_date(parts[1])
            if not date_txt:
                continue

            # 말취소: 지역 일자 rno gate horse trainer jockey reason
            if section == "cancel":
                if len(parts) < 8:
                    continue
                rno = re.sub(r"[^0-9]", "", parts[2]) or "0"
                gate = re.sub(r"[^0-9]", "", parts[3]) or "0"
                horse = parts[4]
                trainer = parts[5]
                jockey = parts[6]
                reason = " ".join(parts[7:]).strip()
                row = "\t".join([city, date_txt, rno, gate, horse, trainer, jockey, reason])
                normalized_rows.append(row)
                continue

            # 기수변경: 지역 일자 rno gate horse old new weight reason
            if section == "jockey":
                if len(parts) < 9:
                    continue
                rno = re.sub(r"[^0-9]", "", parts[2]) or "0"
                gate = re.sub(r"[^0-9]", "", parts[3]) or "0"
                horse = parts[4]
                jockey_old = parts[5]
                jockey_new = parts[6]
                weight = parts[7]
                reason = " ".join(parts[8:]).strip()
                row = "\t".join([city, date_txt, rno, gate, horse, jockey_old, jockey_new, weight, reason])
                normalized_rows.append(row)

        # 중복 제거
        unique_rows = list(dict.fromkeys([r for r in normalized_rows if r.strip()]))
        return "\n".join(unique_rows)

    def _normalize_rdate_text(yyyymmdd):
        if not yyyymmdd or len(yyyymmdd) != 8:
            return yyyymmdd
        return f"{yyyymmdd[0:4]}.{yyyymmdd[4:6]}.{yyyymmdd[6:8]}"

    def _crawl_kra_changed_entries(rcity=None, rdate=None):
        # KRA 출전표변경 페이지 후보 URL
        # 요구사항: 조건 없이(전체) 최신 노출 데이터를 수집

        url_candidates = [
            "https://race.kra.co.kr/thisweekrace/ThisWeekChulmapyoChange.do",
            "https://park.kra.co.kr/thisweekrace/ThisWeekChulmapyoChange.do",
            "https://race.kra.co.kr/thisweekrace/ThisWeekChulmapyoChange.do?" + urlencode({"meet": "1"}),
            "https://race.kra.co.kr/thisweekrace/ThisWeekChulmapyoChange.do?" + urlencode({"meet": "3"}),
            "https://race.kra.co.kr/chulmainfo/chulmapyoChange.do?"
            + urlencode({"Act": "02", "Sub": "1"}),
            "https://park.kra.co.kr/chulmainfo/chulmapyoChange.do?"
            + urlencode({"Act": "02", "Sub": "1"}),
            "https://race.kra.co.kr/chulmainfo/chulmapyoChangeList.do?"
            + urlencode({}),
            "https://park.kra.co.kr/chulmainfo/chulmapyoChangeList.do?"
            + urlencode({}),
        ]

        rows = []
        source_url = ""
        raw_html = ""
        for url in url_candidates:
            try:
                req = Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; thethe9-bot/1.0)",
                        "Referer": "https://race.kra.co.kr/",
                        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                    },
                )
                with urlopen(req, timeout=6) as resp:
                    body = resp.read()
                decoded = _decode_kra_bytes(body)
                if not decoded:
                    continue
                if "출전표" not in decoded and "기수" not in decoded and "취소" not in decoded:
                    continue
                raw_html = decoded
                source_url = url
                break
            except Exception:
                continue

        # 로컬 저장 HTML 테스트 폴백 (개발/점검용)
        if not raw_html:
            local_candidates = [
                Path("/Users/Super007/Documents/전체_출전표변경_금주의경마.htm"),
            ]
            for local_path in local_candidates:
                try:
                    if not local_path.exists() or not local_path.is_file():
                        continue
                    body = local_path.read_bytes()
                    decoded = _decode_kra_bytes(body)
                    if not decoded:
                        continue
                    if "출전표" not in decoded and "기수" not in decoded and "취소" not in decoded:
                        continue
                    raw_html = decoded
                    source_url = str(local_path)
                    break
                except Exception:
                    continue

        if not raw_html:
            return "", [], ""

        tr_matches = re.findall(r"<tr[^>]*>(.*?)</tr>", raw_html, flags=re.IGNORECASE | re.DOTALL)
        formatted_lines = []
        preview_rows = []

        def _norm_date(s):
            x = (s or "").strip()
            x = x.replace("-", ".").replace("/", ".")
            m = re.search(r"(20\d{2})\.(\d{1,2})\.(\d{1,2})", x)
            if m:
                return f"{m.group(1)}.{int(m.group(2)):02d}.{int(m.group(3)):02d}"
            return ""

        def _norm_city(s):
            x = (s or "").strip()
            if "서울" in x:
                return "서울"
            if "부산" in x or "부경" in x:
                return "부경"
            if "제주" in x:
                return "제주"
            return x

        for tr_html in tr_matches:
            tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr_html, flags=re.IGNORECASE | re.DOTALL)
            cols = [_strip_html(td) for td in tds]
            cols = [c for c in cols if c]
            if len(cols) < 6:
                continue

            row_text = " ".join(cols).strip()
            # 헤더/설명 행 제외
            if any(k in row_text for k in ("경마장", "경주일", "출전표", "변경내역", "자료", "제목")):
                continue

            city = _norm_city(cols[0] if len(cols) > 0 else "")
            date_txt = _norm_date(cols[1] if len(cols) > 1 else "")
            if not date_txt:
                continue

            # KRA 표준 8/9 컬럼 우선 처리
            if len(cols) >= 9:
                rno = re.sub(r"[^0-9]", "", cols[2]) or "0"
                gate = re.sub(r"[^0-9]", "", cols[3]) or "0"
                horse = cols[4]
                jockey_old = cols[5]
                jockey_new = cols[6]
                handycap = cols[7] if re.search(r"[0-9]", cols[7]) else "0"
                reason = cols[8]
                line = "\\t".join([city, date_txt, rno, gate, horse, jockey_old, jockey_new, handycap, reason])
                formatted_lines.append(line)
                preview_rows.append(
                    {
                        "type": "기수변경",
                        "rno": rno,
                        "gate": gate,
                        "horse": horse,
                        "jockey_old": jockey_old,
                        "jockey_new": jockey_new,
                        "handycap": handycap,
                        "reason": reason,
                    }
                )
                continue

            if len(cols) == 8:
                rno = re.sub(r"[^0-9]", "", cols[2]) or "0"
                gate = re.sub(r"[^0-9]", "", cols[3]) or "0"
                horse = cols[4]
                reason = cols[7]
                line = "\\t".join([city, date_txt, rno, gate, horse, "-", "-", reason])
                formatted_lines.append(line)
                preview_rows.append(
                    {
                        "type": "출전표변경",
                        "rno": rno,
                        "gate": gate,
                        "horse": horse,
                        "jockey_old": "",
                        "jockey_new": "",
                        "handycap": "",
                        "reason": reason,
                    }
                )
                continue

            # 비정형 행 fallback: 핵심 정보만 채움
            if len(cols) >= 6:
                rno = "0"
                gate = "0"
                for c in cols:
                    if rno == "0":
                        m_r = re.search(r"(\d{1,2})\s*R", c, flags=re.IGNORECASE)
                        if m_r:
                            rno = str(int(m_r.group(1)))
                    if gate == "0":
                        m_g = re.search(r"^\d{1,2}$", c)
                        if m_g:
                            gate = m_g.group(0)
                horse = cols[4] if len(cols) > 4 else ""
                reason = cols[-1]
                line = "\\t".join([city, date_txt, rno, gate, horse, "-", "-", reason])
                formatted_lines.append(line)
                preview_rows.append(
                    {
                        "type": "출전표변경",
                        "rno": rno,
                        "gate": gate,
                        "horse": horse,
                        "jockey_old": "",
                        "jockey_new": "",
                        "handycap": "",
                        "reason": reason,
                    }
                )

        # 중복 제거(문자열 기준)
        unique_lines = list(dict.fromkeys([x for x in formatted_lines if x.strip()]))
        if unique_lines and len(preview_rows) != len(unique_lines):
            preview_rows = preview_rows[: len(unique_lines)]
        if unique_lines:
            return "\\n".join(unique_lines), preview_rows, source_url

        # 폴백: HTML 전체 텍스트에서 한국어 포맷(말취소/기수변경) 재추출
        text_like = raw_html
        text_like = re.sub(r"<br\s*/?>", "\n", text_like, flags=re.IGNORECASE)
        text_like = re.sub(r"</tr\s*>", "\n", text_like, flags=re.IGNORECASE)
        text_like = re.sub(r"</t[dh]\s*>", " ", text_like, flags=re.IGNORECASE)
        text_like = re.sub(r"<[^>]+>", " ", text_like)
        text_like = unescape(text_like)
        text_like = re.sub(r"[ \t]+", " ", text_like)
        text_like = re.sub(r"\n{2,}", "\n", text_like)

        fallback_text = _normalize_changed_race_text(text_like)
        if not fallback_text:
            # 파싱이 0건이어도 원문 텍스트를 화면에 보여서 즉시 확인 가능하게 반환
            plain_preview = re.sub(r"\s+", " ", text_like).strip()
            if len(plain_preview) > 12000:
                plain_preview = plain_preview[:12000] + "\n...[truncated]"
            return plain_preview, [], source_url

        fallback_rows = []
        for ln in fallback_text.splitlines():
            parts = ln.split("\t")
            if len(parts) == 9:
                fallback_rows.append(
                    {
                        "type": "기수변경",
                        "rno": parts[2],
                        "gate": parts[3],
                        "horse": parts[4],
                        "jockey_old": parts[5],
                        "jockey_new": parts[6],
                        "handycap": parts[7],
                        "reason": parts[8],
                    }
                )
            elif len(parts) == 8:
                fallback_rows.append(
                    {
                        "type": "출전표변경",
                        "rno": parts[2],
                        "gate": parts[3],
                        "horse": parts[4],
                        "jockey_old": "",
                        "jockey_new": "",
                        "handycap": "",
                        "reason": parts[7],
                    }
                )

        return fallback_text, fallback_rows, source_url

    r_content = (
        request.POST.get("r_content") if request.POST.get("r_content") != None else ""
    )

    rcity = request.POST.get("rcity") if request.POST.get("rcity") != None else "서울"

    fdate = request.POST.get("fdate") if request.POST.get("fdate") != None else ""

    rno = request.POST.get("rno") if request.POST.get("rno") != None else 99

    rcount = request.POST.get("rcount") if request.POST.get("rcount") != None else 30

    fdata = request.POST.get("fdata") if request.POST.get("fdata") != None else "-"
    action = request.POST.get("action") if request.POST.get("action") != None else "convert"

    # 경마일 기본값 보정: 빈 값이면 최신 경마일 자동 설정
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(fdate or "")):
        try:
            latest = (
                Racing.objects.values("rdate")
                .exclude(rdate__isnull=True)
                .exclude(rdate__exact="")
                .order_by("-rdate")
                .first()
            )
            if latest and latest.get("rdate"):
                rr = str(latest["rdate"])
                if len(rr) == 8 and rr.isdigit():
                    fdate = f"{rr[0:4]}-{rr[4:6]}-{rr[6:8]}"
                else:
                    fdate = datetime.now().strftime("%Y-%m-%d")
            else:
                fdate = datetime.now().strftime("%Y-%m-%d")
        except Exception:
            fdate = datetime.now().strftime("%Y-%m-%d")

    rdate = fdate[0:4] + fdate[5:7] + fdate[8:10]

    result_cnt = 0
    crawl_rows = []
    crawl_source = ""

    if request.method == "POST" and action == "crawl_kra":
        fdata = "출전표변경"
        r_content, crawl_rows, crawl_source = _crawl_kra_changed_entries()
        result_cnt = len(crawl_rows)
        if result_cnt == 0:
            if crawl_source:
                messages.info(request, "출전표변경 내역이 없습니다. (0건)")
            else:
                messages.warning(request, "마사회 출전표변경 데이터를 가져오지 못했습니다.")
        else:
            messages.success(request, f"출전표변경 {result_cnt}건을 크롤링했습니다. Convert를 눌러 반영하세요.")
    else:
        if fdata == "-":
            result_cnt = 0
        elif fdata == "출전표변경":
            normalized_text = _normalize_changed_race_text(r_content)
            apply_text = normalized_text if normalized_text else r_content
            if normalized_text:
                r_content = normalized_text
            result_cnt = set_changed_race(rcity, rdate, rno, apply_text)
        elif fdata == "마체중":
            result_cnt = set_changed_race_weight(rcity, rdate, rno, r_content)
        elif fdata == "경주순위":
            result_cnt = set_changed_race_rank(rcity, rdate, rno, r_content)
        elif fdata == "경주마취소":
            result_cnt = set_changed_race_horse(rcity, rdate, rno, r_content)
        elif fdata == "기수변경":
            result_cnt = set_changed_race_jockey(rcity, rdate, rno, r_content)
        elif fdata == "수영조교":
            result_cnt = insert_train_swim(r_content)
        elif fdata == "말진료현황":
            result_cnt = insert_horse_disease(r_content)
        elif fdata == "출전등록 시뮬레이션":
            result_cnt = insert_race_simulation(rcity, rcount, r_content)
        elif fdata == "심판위원 Report":
            result_cnt = insert_race_judged(rcity, r_content)
        elif fdata == "출발심사(b4)":
            result_cnt = insert_start_audit(r_content)
        elif fdata == "출발조교(b5)":
            result_cnt = insert_start_train(r_content)

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=86)

    context = {
        "rcity": rcity,
        "rdate": rdate,
        "rno": rno,
        "rcount": rcount,
        "exp011s": exp011s,
        "r_content": r_content,
        "fdata": fdata,
        "fdate": fdate,
        "result_cnt": result_cnt,
        "crawl_rows": crawl_rows,
        "crawl_source": crawl_source,
    }

    # user = request.user
    # form = UserForm(instance=user)

    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)
    return render(request, "base/race_breakingnews.html", context)


# record calculation 기준정보 Setup

def raceCalculation(request):

    if request.method == "GET":
        q1 = request.GET.get("q1") if request.GET.get("q1") != None else ""
        q2 = request.GET.get("q2") if request.GET.get("q2") != None else ""

        if q1 == "":
            rday1 = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일

            rday3 = Racing.objects.values("rdate").distinct()[2]["rdate"]  # weeks 기준일

            rdate1 = rday1[0:4] + rday1[4:6] + rday1[6:8]
            rdate2 = rday3[0:4] + rday3[4:6] + rday3[6:8]

            fdate1 = rday1[0:4] + "-" + rday1[4:6] + "-" + rday1[6:8]
            fdate2 = rday3[0:4] + "-" + rday3[4:6] + "-" + rday3[6:8]

        else:
            rdate1 = q1[0:4] + q1[5:7] + q1[8:10]
            rdate2 = q2[0:4] + q2[5:7] + q2[8:10]

            fdate1 = q1[0:4] + "-" + q1[5:7] + "-" + q1[8:10]
            fdate2 = q2[0:4] + "-" + q2[5:7] + "-" + q2[8:10]

        # print(rdate1, rdate2)
        exp010s = []

        # exp011 조회
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT rcity, rdate, rno, grade, rname, distance, dividing, rcount
                    FROM exp010
                    WHERE rdate between %s and %s
                    ORDER BY rcity, rdate, rno;
                """
                cursor.execute(query, (rdate1, rdate2))
                exp010s = cursor.fetchall()

        except Exception as e:
            print(f"❌ Failed selecting in 경주 메모: {e}")
        finally:
            cursor.close()

    if request.method == "POST":
        from apps.ops.views import execChatGPT

        rdate1 = request.POST.get("rdate1") 
        rdate2 = request.POST.get("rdate2")

        q1 = request.POST.get("q1")
        q2 = request.POST.get("q2")

        fdate1 = q1[0:4] + "-" + q1[5:7] + "-" + q1[8:10]
        fdate2 = q2[0:4] + "-" + q2[5:7] + "-" + q2[8:10]

        rcheck1 = request.POST.get("rcheck1")

        # print(rdate1, rdate2, q1, q2, rcheck1)

        if rcheck1:

            # print("POST", rdate1, rdate2)
            # print("경주 기준정보 계산 시작", rdate1)

            ret = baseline_compute(connection, rdate1)
            if ret == 1:
                messages.success(request, "경주 기준정보 계산 완료.")
            else:
                messages.error(request, "경주 기준정보 계산 오류 발생.")

            renewal_record_s(connection, rdate1)

        else:

            print("집계안함", rdate1, rdate2)

        # exp011 조회
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT rcity, rdate, rno, grade, rname, distance, dividing, rcount
                    FROM exp010
                    WHERE rdate between %s and %s
                    ORDER BY rcity, rdate, rno;
                """
                cursor.execute(query, (rdate1, rdate2))
                exp010s = cursor.fetchall()

        except Exception as e:
            print(f"❌ Failed selecting in 경주 메모: {e}")
        finally:
            cursor.close()

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
            # connection.rollback()
            print("Failed inserting in weight")

        # print(weight)

        for index, exp010 in enumerate(exp010s):

            print(exp010[0], exp010[1], exp010[2], "경주 Mock Audit 시작")

            r_condition = Exp010.objects.filter(rcity=exp010[0], rdate=exp010[1], rno=exp010[2]).get()

            create_record(connection, r_condition, weight)

            execChatGPT(request, rcity=exp010[0], rdate=exp010[1], rno=exp010[2])

            print(exp010, "경주 집계 완료")

            # if exp010[2] == 1:
            #     break

        # m_rank m_score 갱신
        update_m_rank_score_for_period(
            rdate1,
            rdate2,
            # model_name="sb_top3_20241129_20251130",
            model_name=f"sb_top3_roll12_{rdate1[0:6]}"
        )

        update_exp011_for_period(rdate1, rdate2)         #f_score, f_rank 점수 갱신  
        # exp010 r_guide 업데이트 (기간)
        run_rguide_update(from_date=rdate1, to_date=rdate2, dry_run=False)

    context = {
        "q1": q1,
        "q2": q2,
        "rdate1": rdate1,
        "rdate2": rdate2,
        "fdate1": fdate1,
        "fdate2": fdate2,
        "exp010s": exp010s,
    }

    return render(request, "base/race_calculation.html", context)

def awardStatusTrainer(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    jname1 = request.GET.get("j1") if request.GET.get("j1") != None else ""
    jname2 = request.GET.get("j2") if request.GET.get("j2") != None else ""
    jname3 = request.GET.get("j3") if request.GET.get("j3") != None else ""

    if q == "":
        today = datetime.today()
        if today.weekday() == 4:  # {0:월, 1:화, 2:수, 3:목, 4:금, 5:토, 6:일}
            rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]
        elif today.weekday() == 5:
            rdate = Racing.objects.values("rdate").distinct()[1]["rdate"]
        else:
            rdate = Racing.objects.values("rdate").distinct()[2]["rdate"]

        friday = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일
        fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

    else:
        # print(q[5:7] + "-" + q[8:10] + "-" + q[0:4])
        today = datetime.strptime(q[5:7] + "-" + q[8:10] + "-" + q[0:4], "%m-%d-%Y")

        if today.weekday() == 4:
            rdate = q[0:4] + q[5:7] + q[8:10]
            friday = rdate
            fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

        else:
            rdate = q[0:4] + q[5:7] + q[8:10]

            friday = rdate
            fdate = q

            # messages.warning(request, "선택된 날짜가 금요일이 아닙니다.")

    weeks = get_last2weeks(
        friday,
        i_awardee="trainer",
        i_friday=Racing.objects.values("rdate").distinct()[0]["rdate"],
    )
    loadin = get_last2weeks_loadin(friday)

    check_visit(request)
    
    context = {
        "weeks": weeks,
        "loadin": loadin,
        "fdate": fdate,
        "rdate": rdate,
        "jname1": jname1,
        "jname2": jname2,
        "jname3": jname3,
    }

    return render(request, "base/award_status_trainer.html", context)

def awardStatusJockey(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    jname1 = request.GET.get("j1") if request.GET.get("j1") != None else ""
    jname2 = request.GET.get("j2") if request.GET.get("j2") != None else ""
    jname3 = request.GET.get("j3") if request.GET.get("j3") != None else ""

    if q == "":
        today = datetime.today()
        if today.weekday() == 4:  # {0:월, 1:화, 2:수, 3:목, 4:금, 5:토, 6:일}
            rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]
        elif today.weekday() == 5:
            rdate = Racing.objects.values("rdate").distinct()[1]["rdate"]
        else:
            rdate = Racing.objects.values("rdate").distinct()[2]["rdate"]

        friday = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일
        fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

    else:
        # print(q[5:7] + "-" + q[8:10] + "-" + q[0:4])
        today = datetime.strptime(q[5:7] + "-" + q[8:10] + "-" + q[0:4], "%m-%d-%Y")
        # print(today)

        if today.weekday() == 4:
            rdate = q[0:4] + q[5:7] + q[8:10]
            friday = rdate
            fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

        else:
            rdate = q[0:4] + q[5:7] + q[8:10]

            friday = rdate
            fdate = q

            # messages.warning(request, "선택된 날짜가 금요일이 아닙니다.")

    weeks = get_last2weeks(
        friday,
        i_awardee="jockey",
        i_friday=Racing.objects.values("rdate").distinct()[0]["rdate"],
    )

    loadin = get_last2weeks_loadin(friday)

    check_visit(request)

    context = {
        "weeks": weeks,
        "loadin": loadin,
        "fdate": fdate,
        "rdate": rdate,
        "jname1": jname1,
        "jname2": jname2,
        "jname3": jname3,
    }

    return render(request, "base/award_status_jockey.html", context)

def awardStatusWeek(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    jname1 = request.GET.get("j1") if request.GET.get("j1") != None else ""
    jname2 = request.GET.get("j2") if request.GET.get("j2") != None else ""
    jname3 = request.GET.get("j3") if request.GET.get("j3") != None else ""

    if q == "":
        today = datetime.today()
        if today.weekday() == 4:  # {0:월, 1:화, 2:수, 3:목, 4:금, 5:토, 6:일}
            rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]
        elif today.weekday() == 5:
            rdate = Racing.objects.values("rdate").distinct()[1]["rdate"]
        else:
            rdate = Racing.objects.values("rdate").distinct()[2]["rdate"]

        friday = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일
        fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

    else:
        # print(q[5:7] + "-" + q[8:10] + "-" + q[0:4])
        today = datetime.strptime(q[5:7] + "-" + q[8:10] + "-" + q[0:4], "%m-%d-%Y")
        # print(today)

        if today.weekday() == 4:
            rdate = q[0:4] + q[5:7] + q[8:10]
            friday = rdate
            fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

        else:
            rdate = q[0:4] + q[5:7] + q[8:10]

            friday = rdate
            fdate = q

            # messages.warning(request, "선택된 날짜가 금요일이 아닙니다.")

    week = get_status_week(
        friday
    )

    loadin = get_last2weeks_loadin(friday)

    check_visit(request)

    context = {
        "week": week,
        "loadin": loadin,
        "fdate": fdate,
        "rdate": rdate,
        "jname1": jname1,
        "jname2": jname2,
        "jname3": jname3,
    }

    return render(request, "base/award_status_week.html", context)

def dataManagement(request):
    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else ""
    q1 = request.GET.get("q1") if request.GET.get("q1") != None else ""
    q2 = request.GET.get("q2") if request.GET.get("q2") != None else ""
    fcode = request.GET.get("fcode") if request.GET.get("fcode") != None else ""
    fstatus = request.GET.get("fstatus") if request.GET.get("fstatus") != None else ""

    if q1 == "":
        friday = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일

        sunday = Racing.objects.values("rdate").distinct()[1]["rdate"]  # weeks 기준일

        rdate1 = friday[0:4] + friday[4:6] + friday[6:8]
        rdate2 = sunday[0:4] + sunday[4:6] + sunday[6:8]

        fdate1 = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]
        fdate2 = sunday[0:4] + "-" + sunday[4:6] + "-" + sunday[6:8]

    else:
        rdate1 = q1[0:4] + q1[5:7] + q1[8:10]
        rdate2 = q2[0:4] + q2[5:7] + q2[8:10]

        fdate1 = q1[0:4] + "-" + q1[5:7] + "-" + q1[8:10]
        fdate2 = q2[0:4] + "-" + q2[5:7] + "-" + q2[8:10]

    krafile = get_krafile(rcity, rdate1, rdate2, fcode, fstatus)
    if krafile:
        messages.warning(request, "총 " + str(len(krafile)) + "건.")
    else:
        messages.warning(request, "결과 0.")

    # print(krafile)
    # print(kradata)

    if request.method == "POST":

        # print(krafile, "POST")
        myDict = dict(request.POST) 
        # print(myDict['fpath'])

        for index, rcheck in enumerate(myDict["rcheck"]):
            # print(rcheck)

            fpath = myDict['fpath'][index].strip()

            if rcheck == "0":
                krafile_convert(fpath)

        #     if fname[-12:-10] == '11':
        #         print(fname[-12:-10])

        #     file = open(fname, "r")
        #     while True:
        #         line = file.readline()
        #         if not line:
        #             break
        #         print(line.strip())
        #     file.close()

    context = {
        "q1": q1,
        "q2": q2,
        "rcity": rcity,
        "fcode": fcode,
        "fstatus": fstatus,
        "krafile": krafile,
        # 'kradata': kradata,
        "fdate1": fdate1,
        "fdate2": fdate2,
    }

    return render(request, "base/data_management.html", context)


@csrf_exempt

def krafileInput(request):
    request_files = (
        request.FILES.getlist("image_uploads")
        if "image_uploads" in request.FILES
        else None
    )

    if request_files:
        # save attached file
        for request_file in request_files:
            # create a new instance of FileSystemStorage
            fs = FileSystemStorage()

            fname = request_file.name

            if fname[-4:] == "xlsx":
                os.makedirs(KRAFILE_ROOT / "xlsx", exist_ok=True)
                fs.location = KRAFILE_ROOT / "xlsx"
            else:
                if fname[0:4] < "2018":
                    os.makedirs(KRAFILE_ROOT / "2022이전", exist_ok=True)
                    fs.location = KRAFILE_ROOT / "2022이전"
                else:
                    os.makedirs(KRAFILE_ROOT / fname[0:4], exist_ok=True)
                    fs.location = KRAFILE_ROOT / fname[0:4]

            if fs.exists(fname):
                fs.delete(fname)

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """
                            DELETE FROM krafile
                            WHERE fname = '"""
                        + fname
                        + """'
                            ; """
                    )

                    # print(strSql)

                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    result = cursor.fetchone()
                    # result = cursor.fetchall()

                    connection.commit()
                    connection.close()

                except:
                    connection.rollback()
                    print("Failed deleting in krafile")

            # file = fs.save(request_file.name, request_file)
            # # the fileurl variable now contains the url to the file. This can be used to serve the file when needed.
            # fileurl = fs.url(file)

            if fname[-4:] == "xlsx":
                print(fname[-4:])

                fdate = fname[-19:-11]
                fcode = "c1"

                file = fs.save(request_file.name, request_file)
                # shutil.copy(request_file, str(fs.location) + '/')
            else:
                fdate = fname[0:8]
                fcode = fname[-12:-10]
                fcontent = request_file.read().decode(
                    "euc-kr", errors="strict"
                )  # 한글 decode

                letter = open(str(fs.location) + "/" + fname, "w")  # 새 파일 열기
                letter.write(fcontent)
                letter.close()  # 닫기

            try:
                cursor = connection.cursor()

                strSql = (
                    """
                        INSERT INTO krafile
                        ( fname, fpath, rdate, fcode, fstatus, in_date )
                        VALUES
                        ( '"""
                    + fname
                    + """',
                        '"""
                    + str(fs.location)
                    + "/"
                    + fname
                    + """',
                        '"""
                    + fdate
                    + """',
                        '"""
                    + fcode
                    + """',
                        'I',
                        """
                    + "NOW()"
                    + """
                        ) ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                result = cursor.fetchone()
                # result = cursor.fetchall()

                connection.commit()
                connection.close()

            except:
                connection.rollback()
                print("Failed inserting in krafile")

    context = {"request_files": request_files}

    return render(request, "base/krafile_input.html", context)


@csrf_exempt

def BreakingNewsInput(request):
    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else ""
    rdate = request.GET.get("rdate") if request.GET.get("rdate") != None else ""
    title = request.GET.get("title") if request.GET.get("title") != None else ""
    news = request.GET.get("news") if request.GET.get("news") != None else ""

    try:
        cursor = connection.cursor()

        strSql = (
            """
                DELETE FROM breakingnews
                WHERE rcity = '"""
            + rcity
            + """' and rdate = '"""
            + rdate
            + """' and title = '"""
            + title
            + """'
                ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchone()
        # result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed deleting in Breaking News")

    try:
        cursor = connection.cursor()

        strSql = (
            """
                INSERT INTO breakingnews
                ( rcity, rdate, title, news, in_date )
                VALUES
                ( '"""
            + rcity
            + """',
                '"""
            + rdate
            + """',
                '"""
            + title
            + """',
                '"""
            + news
            + """',
                """
            + "NOW()"
            + """
                ) ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchone()
        # result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed inserting in Breaking News")

    context = {"rdate": rdate}

    return render(request, "base/breakingnews_input.html", context)
