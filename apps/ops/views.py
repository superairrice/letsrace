from apps.common import *

def updatePopularity(request, rcity, rdate, rno):
    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)
    context = {"rcity": rcity, "exp011s": exp011s}

    # user = request.user
    # form = UserForm(instance=user)

    if request.method == "POST":
        myDict = dict(request.POST)
        print(myDict["pop_1"][0])

        for race in exp011s:
            pop = "pop_" + str(race.gate)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011 set r_pop = """
                    + myDict[pop][0]
                    + """, r_rank = """
                    + myDict[pop][1]
                    + """
                            where rdate = '"""
                    + rdate
                    + """' and rcity = '"""
                    + rcity
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(race.gate)
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
                print("Failed selecting in BookListView")

        # form = Exp011(request.POST, request.FILES, rcity=rcity, rdate=rdate, rno=rno, instance=pop_1)
        # if form.is_valid():
        #     form.save()
        #     redirect('user-profile', pk=rdate)

    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)
    return render(request, "base/update_popularity.html", context)


@login_required(login_url="account_login")

def updateChangedRace(request, rcity, rdate, rno):

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
    elif fdata == "수영조교":
        insert_train_swim(r_content)
    elif fdata == "말진료현황":
        insert_horse_disease(r_content)

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)

    # user = request.user
    # form = UserForm(instance=user)

    if request.method == "POST":
        myDict = dict(request.POST)
        # print(myDict)
        # print(myDict['pop_1'][0])

        for race in exp011s:
            pop = "pop_" + str(race.gate)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011 
                                set r_rank = """
                    + myDict[pop][0]
                    + """,
                                    r_pop = """
                    + myDict[pop][1]
                    + """,
                                    bet = """
                    + myDict[pop][2]
                    + """
                            where rdate = '"""
                    + rdate
                    + """' and rcity = '"""
                    + rcity
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(race.gate)
                    + """
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
                print("Failed updating in exp011")

            exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)

    context = {"rcity": rcity, "exp011s": exp011s, "fdata": fdata}
    return render(request, "base/update_changed_race.html", context)

@login_required(login_url="account_login")

def mockAudit(request, rcity, rdate, rno, hname, awardee):
    """
    mockAudit view (리팩토링)
    - 기본: 초기 로드 -> 조회만 (집계 X)
    - ?calc=1 이면 -> 집계 로직 실행(UPDATE/INSERT 등) 후 HttpResponse 반환
    """
    weight = get_weight2(rcity, rdate, rno)  # 예상: list/tuple 형태
    # print("first weight:", weight)
    wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")

    w_avg = weight[0][0]
    w_fast = weight[0][1]
    w_slow = weight[0][2]
    w_recent3 = weight[0][3]
    w_recent5 = weight[0][4]
    w_convert = weight[0][5]
    w_flag = weight[0][6]

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    # print("r_condition:", r_condition)

    mock_insert2(rcity, rdate, rno)

    # 5) do_calc 체크: ?calc=1 이면 집계 실행 (fetch로 호출되는 경우)
    do_calc = request.GET.get("calc", "0")
    if do_calc == "1":

        # weight = get_weight2(rcity, rdate, rno)  # 예상: list/tuple 형태
        # print("weight:", weight[0][0])
        # wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")

        w_avg = request.GET.get("w_avg") 
        w_fast = request.GET.get("w_fast") 
        w_slow = request.GET.get("w_slow") 
        w_recent3 = request.GET.get("w_recent3") 
        w_recent5 = request.GET.get("w_recent5") 
        w_convert = request.GET.get("w_convert") 
        w_flag = request.GET.get("w_flag") 

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
        # print("1.weight_mock:", weight_mock)

        if (
            int(w_avg) + int(w_fast) + int(w_slow) == 100
            and int(w_recent3) + int(w_recent5) + int(w_convert) == 100  # 가중치 오류 check
        ):
            weight_sum_ok = True
        else:
            weight_sum_ok = False

        if weight_sum_ok:

            messages.warning(request, "weight ok")

            try:
                with connection.cursor() as cursor:
                    update_sql = """
                        UPDATE rec011
                        SET i_mock = NULL
                        WHERE horse IN (
                            SELECT horse FROM exp011 WHERE rcity = %s AND rdate = %s AND rno = %s
                        )
                    """
                    cursor.execute(update_sql, (rcity, rdate, rno))
            except Exception as e:
                print("❌ Failed updating rec011 i_mock:", e)
                # 오류 발생시 롤백 (cursor context manager 사용 시 자동 rollback 아님)
                try:
                    connection.rollback()
                except Exception:
                    pass
                return JsonResponse({"status": "error", "msg": "Broken pipe"})

            # INSERT weight_s2 (파라미터 바인딩으로 안전하게)
            try:
                with connection.cursor() as cursor:
                    insert_sql = """
                        INSERT INTO weight_s2
                        (rcity, rdate, rno, wdate, w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert)
                        VALUES (%s, %s, %s, now(), %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        insert_sql,
                        (
                            rcity,
                            rdate,
                            rno,
                            int(w_avg),
                            int(w_fast),
                            int(w_slow),
                            int(w_recent3),
                            int(w_recent5),
                            int(w_convert),
                        ),
                    )
            except Exception as e:
                print("❌ Failed inserting into weight_s2:", e)
                try:
                    connection.rollback()
                except Exception:
                    pass
                return JsonResponse({"status": "error", "msg": "Broken pipe"})

            try:
                mock_traval2(r_condition, weight_mock)
            except Exception as e:
                print("❌ mock_traval2 에러:", e)
                return JsonResponse({"status": "error", "msg": "Broken pipe"})

            # update_m_rank_score_for_race(
            #     rcity, rdate, rno, model_name="sb_top3_20241129_20251130"
            # )  # 저장해둔 모델 이름

            update_m_rank_score_for_race(
                rcity, rdate, rno, model_name=f"sb_top3_roll12_{rdate[0:6]}"
            )  # 저장해둔 모델 이름

        else:
            messages.error(request, "weight error")

        # print(f"✅ Mock 집계 실행 완료: {rcity}, {rdate}, {rno}")
        # Ajax 호출(프론트)의 경우 간단 텍스트 또는 JSON 반환
        return JsonResponse({"status": "ok", "message": "Mock 집계 완료"})

    # 6) calc != 1 이면 -> 초기 로드(조회) 모드: DB에서 필요한 데이터 조회 후 context 생성
    # exp011s 조회
    exp011s = Exp011s2.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "r_pop", "gate"
    )
    # for r in exp011s:
    #     print(r.s1f_rank, r.g1f_rank, r.g2f_rank, r.g3f_rank)

    if not exp011s.exists():
        return render(request, "base/home.html")

    # horse_records
    try:
        hr_records = recordsByHorse(rcity, rdate, rno, "None")
    except Exception as e:
        print("❌ recordsByHorse 에러:", e)
        hr_records = []

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

    # alloc (Rec010 존재 여부)
    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except Rec010.DoesNotExist:
        alloc = None

    # track, memo, loadin, disease, trainer check 등
    track = get_track_record(rcity, rdate, rno)

    try:
        with connection.cursor() as cursor:
            memo_sql = """
                SELECT REPLACE(REPLACE(horse, '[서]', ''), '[부]', ''), r_etc, r_flag, judge
                FROM rec011
                WHERE rcity = %s AND rdate = %s AND rno = %s
            """
            cursor.execute(memo_sql, (rcity, rdate, rno))
            r_memo = cursor.fetchall()
    except Exception as e:
        print("❌ Failed selecting in 경주 메모:", e)
        r_memo = []

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    # 7) context 구성 및 렌더
    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,
        "disease": disease,
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        "track": track,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
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

    return render(request, "base/mock_audit.html", context)


# def mockAudit(request, rcity, rdate, rno, hname, awardee):

#     weight = get_weight2(rcity, rdate, rno)
#     # print(weight[0][7])
#     wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")

#     # i_mock clear
#     try:
#         with connection.cursor() as cursor:

#             strSql = """
#                 UPDATE rec011
#                 SET i_mock = null
#                 WHERE horse in (select horse from exp011 where rcity = %s and rdate = %s and rno = %s)
#             """
#             r_cnt = cursor.execute(strSql, (rcity, rdate, rno))
#             # connection.commit()

#     except Exception as e:
#         print("❌ Failed updating rec011 i_mock:", rcity, rdate, rno, "| Error:", e)
#         connection.rollback()

#     mock_insert2(rcity, rdate, rno)

#     w_avg = (
#         request.GET.get("w_avg") if request.GET.get("w_avg") != None else weight[0][0]
#     )
#     w_fast = (
#         request.GET.get("w_fast") if request.GET.get("w_fast") != None else weight[0][1]
#     )
#     w_slow = (
#         request.GET.get("w_slow") if request.GET.get("w_slow") != None else weight[0][2]
#     )
#     w_recent3 = (
#         request.GET.get("w_recent3")
#         if request.GET.get("w_recent3") != None
#         else weight[0][3]
#     )
#     w_recent5 = (
#         request.GET.get("w_recent5")
#         if request.GET.get("w_recent5") != None
#         else weight[0][4]
#     )
#     w_convert = (
#         request.GET.get("w_convert")
#         if request.GET.get("w_convert") != None
#         else weight[0][5]
#     )
#     w_flag = (
#         request.GET.get("w_flag") if request.GET.get("w_flag") != None else weight[0][6]
#     )

#     r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

#     weight_mock = (
#         (
#             int(w_avg),
#             int(w_fast),
#             int(w_slow),
#             int(w_recent3),
#             int(w_recent5),
#             int(w_convert),
#             w_flag,
#         ),
#     )  # tuple로 정의

#     if weight == weight_mock:  # query 가중치와 입력된 가중치가 동일하면
#         # print("같음")
#         pass

#     if (
#         int(w_avg) + int(w_fast) + int(w_slow) == 100
#         and int(w_recent3) + int(w_recent5) + int(w_convert) == 100  # 가중치 오류 check
#     ):

#         if weight != weight_mock:  # 가중치가 뱐경되었으면
#             try:
#                 cursor = connection.cursor()

#                 strSql = (
#                     """
#                     insert into weight_s2
#                     (
#                         rcity,
#                         rdate,
#                         rno,
#                         wdate,
#                         w_avg,
#                         w_fast,
#                         w_slow,
#                         w_recent3,
#                         w_recent5,
#                         w_convert
#                     )
#                     VALUES
#                     (
#                         '"""
#                     + rcity
#                     + """',
#                         '"""
#                     + rdate
#                     + """',
#                         """
#                     + str(rno)
#                     + """,
#                         """
#                     " now() "
#                     """,
#                         """
#                     + str(w_avg)
#                     + """,
#                         """
#                     + str(w_fast)
#                     + """,
#                         """
#                     + str(w_slow)
#                     + """,
#                         """
#                     + str(w_recent3)
#                     + """,
#                         """
#                     + str(w_recent5)
#                     + """,
#                         """
#                     + str(w_convert)
#                     + """
#                     )
#                 ; """
#                 )

#                 r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
#                 weight = cursor.fetchall()

#             except:
#                 print("Failed inserting in weight_s1")
#             finally:
#                 connection.close()

#             mock = mock_traval2(r_condition, weight_mock)

#         if w_flag == 0:
#             messages.warning(request, "weight_s1")

#         else:
#             messages.warning(request, "weight only")

#     else:
#         messages.warning(request, "오류")
#         # weight = get_weight(rcity, rdate, rno)

#     # print(
#     #     "aaaa",
#     #     int(w_avg) + int(w_fast) + int(w_slow),
#     #     int(w_recent3) + int(w_recent5) + int(w_convert),
#     # )
#     # print(weight)

#     exp011s = Exp011s2.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
#         "rank", "gate"
#     )

#     if exp011s:
#         pass
#     else:
#         return render(request, "base/home.html")

#     hr_records = recordsByHorse(rcity, rdate, rno, 'None')

#     # print(hr_records)
#     compare_r = exp011s.aggregate(
#         Min("i_s1f"),
#         Min("i_g1f"),
#         Min("i_g2f"),
#         Min("i_g3f"),
#         Max("handycap"),
#         Max("rating"),
#         Max("r_pop"),
#         Max("j_per"),
#         Max("t_per"),
#         Max("jt_per"),
#         Min("recent5"),
#         Min("recent3"),
#         Min("convert_r"),
#         Min("s1f_rank"),
#     )

#     try:
#         alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
#     except:
#         alloc = None

#     track = get_track_record(
#         rcity, rdate, rno
#     )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

#     # 경주 메모 Query
#     try:
#         with connection.cursor() as cursor:
#             query = """
#                 SELECT replace( replace( horse, '[서]', ''), '[부]', ''), r_etc, r_flag, judge
#                 FROM rec011
#                 WHERE rcity = %s
#                 AND rdate = %s
#                 AND rno = %s;
#             """
#             cursor.execute(query, (rcity, rdate, rno))
#             r_memo = cursor.fetchall()

#     except Exception as e:
#         print(f"❌ Failed selecting in 경주 메모: {e}")
#     finally:
#         cursor.close()

#     loadin = get_loadin(rcity, rdate, rno)
#     disease = get_disease(rcity, rdate, rno)

#     trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

#     trainer_double_check = get_trainer_double_check(rcity, rdate, rno)

#     # axis = get_axis(rcity, rdate, rno)
#     # axis1 = get_axis_rank(rcity, rdate, rno, 1)
#     # axis2 = get_axis_rank(rcity, rdate, rno, 2)
#     # axis3 = get_axis_rank(rcity, rdate, rno, 3)

#     recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

#     context = {
#         "exp011s": exp011s,
#         "r_condition": r_condition,
#         "loadin": loadin,  # 기수 기승가능 부딤중량
#         "disease": disease,  # 기수 기승가능 부딤중량
#         "hr_records": hr_records,
#         "compare_r": compare_r,
#         "alloc": alloc,
#         "track": track,
#         #    'swim': swim,
#         # "h_audit": h_audit,
#         "trainer_double_check": str(trainer_double_check),
#         "training_cnt": training_cnt,
#         # "axis1": axis1,
#         # "axis2": axis2,
#         # "axis3": axis3,
#         "weight": weight,
#         "wdate": wdate,
#         "w_avg": w_avg,
#         "w_fast": w_fast,
#         "w_slow": w_slow,
#         "w_recent3": w_recent3,
#         "w_recent5": w_recent5,
#         "w_convert": w_convert,
#         "r_memo": r_memo,
#         "recovery_cnt": recovery_cnt,
#         "start_cnt": start_cnt,
#         "audit_cnt": audit_cnt,
#     }
#     return render(request, "base/mock_audit.html", context)


# @login_required(login_url="account_login")
# def mockAudit(request, rcity, rdate, rno, hname, awardee):
#     """
#     특정 경주에 대한 Mock Audit
#     - 처음 화면 진입(GET): 조회만
#     - 버튼 클릭 또는 요청 파라미터 있을 때: 집계 실행
#     """

#     # 1️⃣ 기본 가중치 조회
#     weight = get_weight2(rcity, rdate, rno)
#     wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")

#     # 2️⃣ 가중치 파라미터 (GET 요청이면 weight값 그대로)
#     w_avg = request.GET.get("w_avg") or weight[0][0]
#     w_fast = request.GET.get("w_fast") or weight[0][1]
#     w_slow = request.GET.get("w_slow") or weight[0][2]
#     w_recent3 = request.GET.get("w_recent3") or weight[0][3]
#     w_recent5 = request.GET.get("w_recent5") or weight[0][4]
#     w_convert = request.GET.get("w_convert") or weight[0][5]
#     w_flag = request.GET.get("w_flag") or weight[0][6]

#     # 3️⃣ 기본 조건
#     r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

#     # 4️⃣ mock 집계 여부 체크 (예: "calc" 파라미터가 있을 때만 집계)
#     do_calc = request.GET.get("calc", "0")  # 기본값 0 → 조회만
#     if do_calc == "1":
#         print("✅ Mock 집계 실행 중:", rcity, rdate, rno)

#         # i_mock clear
#         try:
#             with connection.cursor() as cursor:
#                 strSql = """
#                     UPDATE rec011
#                     SET i_mock = null
#                     WHERE horse in (
#                         SELECT horse FROM exp011
#                         WHERE rcity = %s AND rdate = %s AND rno = %s
#                     )
#                 """
#                 cursor.execute(strSql, (rcity, rdate, rno))
#         except Exception as e:
#             print("❌ Failed updating rec011 i_mock:", e)
#             connection.rollback()

#         # mock 집계
#         mock_insert2(rcity, rdate, rno)
#         mock_traval2(
#             r_condition,
#             (
#                 (
#                     int(w_avg),
#                     int(w_fast),
#                     int(w_slow),
#                     int(w_recent3),
#                     int(w_recent5),
#                     int(w_convert),
#                     w_flag,
#                 ),
#             ),
#         )

#         messages.success(request, "Mock 집계가 완료되었습니다.")
#     else:
#         print("🔹 초기 로드: 집계 생략 (조회만 수행)")

#     # 5️⃣ 이하 조회용 쿼리 그대로 유지
#     exp011s = Exp011s2.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
#         "rank", "gate"
#     )
#     if not exp011s:
#         return render(request, "base/home.html")

#     hr_records = recordsByHorse(rcity, rdate, rno, "None")

#     compare_r = exp011s.aggregate(
#         Min("i_s1f"),
#         Min("i_g1f"),
#         Min("i_g2f"),
#         Min("i_g3f"),
#         Max("handycap"),
#         Max("rating"),
#         Max("r_pop"),
#         Max("j_per"),
#         Max("t_per"),
#         Max("jt_per"),
#         Min("recent5"),
#         Min("recent3"),
#         Min("convert_r"),
#         Min("s1f_rank"),
#     )

#     try:
#         alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
#     except:
#         alloc = None

#     track = get_track_record(rcity, rdate, rno)

#     # 경주 메모
#     try:
#         with connection.cursor() as cursor:
#             query = """
#                 SELECT REPLACE(REPLACE(horse, '[서]', ''), '[부]', ''), r_etc, r_flag, judge
#                 FROM rec011
#                 WHERE rcity = %s AND rdate = %s AND rno = %s;
#             """
#             cursor.execute(query, (rcity, rdate, rno))
#             r_memo = cursor.fetchall()
#     except Exception as e:
#         print(f"❌ Failed selecting in 경주 메모: {e}")
#         r_memo = []

#     loadin = get_loadin(rcity, rdate, rno)
#     disease = get_disease(rcity, rdate, rno)
#     trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)
#     recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

#     context = {
#         "exp011s": exp011s,
#         "r_condition": r_condition,
#         "loadin": loadin,
#         "disease": disease,
#         "hr_records": hr_records,
#         "compare_r": compare_r,
#         "alloc": alloc,
#         "track": track,
#         "trainer_double_check": str(trainer_double_check),
#         "training_cnt": training_cnt,
#         "weight": weight,
#         "wdate": wdate,
#         "w_avg": w_avg,
#         "w_fast": w_fast,
#         "w_slow": w_slow,
#         "w_recent3": w_recent3,
#         "w_recent5": w_recent5,
#         "w_convert": w_convert,
#         "r_memo": r_memo,
#         "recovery_cnt": recovery_cnt,
#         "start_cnt": start_cnt,
#         "audit_cnt": audit_cnt,
#     }
#     return render(request, "base/mock_audit.html", context)


from django.http import JsonResponse

def mockAccept(request, rcity, rdate, rno):
    """
    특정 경주에 대한 Mock Accept 처리를 수행하는 함수
    """
    if request.method == "GET":
        # 예시: 로그 출력
        print(f"Mock Accept 실행: {rcity}, {rdate}, {rno}")

        # 예시: DB 처리 로직
        try:
            cursor = connection.cursor()

            # complex5 update
            strSql = (
                """
                UPDATE exp011 a
                JOIN The1.exp011s2 b
                ON a.rcity = b.rcity
                AND a.rdate = b.rdate
                AND a.rno   = b.rno
                AND a.gate  = b.gate
                SET 
                    a.rank      = b.rank,
                    a.complex   = b.complex,
                    a.recent3   = b.recent3,
                    a.recent5   = b.recent5,
                    a.convert_r = b.convert_r,
                    a.rs1f      = b.rs1f,
                    a.rg3f      = b.rg3f,
                    a.rg2f      = b.rg2f,
                    a.rg1f      = b.rg1f,
                    a.cs1f      = b.cs1f,
                    a.cg3f      = b.cg3f,
                    a.cg2f      = b.cg2f,
                    a.cg1f      = b.cg1f,
                    a.i_s1f     = b.i_s1f,
                    a.i_g3f     = b.i_g3f,
                    a.i_g2f     = b.i_g2f,
                    a.i_g1f     = b.i_g1f,
                    a.s1f_rank  = b.s1f_rank,
                    a.g3f_rank  = b.g3f_rank,
                    a.g2f_rank  = b.g2f_rank,
                    a.g1f_rank  = b.g1f_rank,
                    a.remark    = b.remark,
                    a.bet       = b.bet,
                    a.complex5  = b.complex5,
                    a.gap       = b.gap,
                    a.gap_back  = b.gap_back
                WHERE a.rcity = '"""
                + rcity
                + """'
                AND a.rdate = '"""
                + rdate
                + """'
                AND a.rno  = """
                + str(rno)
                + """
                ; """
            )

            # print(strSql)

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            # connection.commit()

        except Exception as e:
            connection.rollback()
            print("Failed Update exp011 all :", e, strSql)
        finally:
            if cursor:
                cursor.close()

        # ✅ 반드시 HTTP 응답 객체를 반환해야 함
        return JsonResponse(
            {
                "status": "success",
                "message": f"Mock Accept 실행 완료 ({rcity}, {rdate}, {rno})",
            }
        )

    # 잘못된 요청일 경우
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

from django.http import JsonResponse
from django.db import connection

# from compute_gpt import process_race  # 우리가 만든 모듈

def execChatGPT(request, rcity, rdate, rno):
    """
    ChatGPT 기반 예측을 수행하는 함수
    - exp011에서 해당 경주마들 조회
    - compute_gpt.process_race 로 예측
    - 결과를 JSON으로 반환
    """

    cursor = None
    try:
        cursor = connection.cursor()

        # ✅ 안전한 파라미터 바인딩 사용
        strSql = """
            SELECT
                rcity,
                rdate,
                rno,
                gate,
                horse,
                birthplace,
                h_sex,
                h_age,
                handycap,
                joc_adv,
                jockey,
                trainer,
                host,
                rating,
                prize_tot,
                prize_year,
                prize_half,
                tot_1st,
                tot_2nd,
                tot_3rd,
                tot_race,
                year_1st,
                year_2nd,
                year_3rd,
                year_race,
                
                if(f_s2t(recent3) = 0,f_s2t(recent5),f_s2t(recent3)) AS recent3,
                f_s2t(recent5) AS recent5,
                if(f_s2t(fast_r) = 0,f_s2t(recent5),f_s2t(fast_r)) AS fast_r,
                if(f_s2t(slow_r) = 0,f_s2t(recent5),f_s2t(slow_r)) AS slow_r,
                if(f_s2t(avg_r) = 0,f_s2t(recent5),f_s2t(avg_r)) AS avg_r,

                rs1f,
                r1c,
                r2c,
                r3c,
                r4c,
                rg3f,
                rg2f,
                rg1f,

                cs1f,
                cg3f,
                cg2f,
                cg1f,
                rank,
                i_s1f,
                i_g3f,
                i_g2f,
                i_g1f,

                i_jockey,
                i_cycle,
                i_prehandy,

                remark,
                s1f_rank,
                g2f_rank,

                h_weight,
                j_per,
                t_per,
                jt_per,
                jt_cnt,
                jt_1st,
                jt_2nd,
                jt_3rd,
                ( select distance from exp010 where rcity = The1.exp011.rcity and rdate = The1.exp011.rdate and rno = The1.exp011.rno ) as distance
            FROM The1.exp011
            WHERE rcity = %s
            AND rdate = %s
            AND rno   = %s
            AND rank < 98
        ORDER BY gate ASC
        """
        
        # print(strSql % (rcity, rdate, rno))  # 디버깅용 출력

        cursor.execute(strSql, [rcity, rdate, rno])
        exp011s = cursor.fetchall()   # 튜플 리스트
        
        
        """       # ✅ g2f_update 함수 호출"""
        # for e in exp011s:
        #     rcity = e[0]
        #     rdate = e[1]
        #     horse = e[4]
        #     distance = e[52]
        #     print("g2f_update 호출:", rcity, rdate, horse, distance)
        #     try:
        #         g2f_update(rcity, rdate, horse, distance, connection,)
        #     except Exception as e:
        #         print("g2f_update 실패:", rcity, rdate, horse, distance, e)
            
            

        # ✅ compute_gpt.py 에서 만든 메인 함수 호출
        predictions = process_race(exp011s)

        print("✅ ChatGPT 예측 완료:")
        # 도표 형태로 출력 (콘솔)
        # print(
        #     f"{'순위':^3} | {'마번':^3} | {'종합':^3} | "
        #     f"{'s1f':^5} | {'g3f':^5} | {'g1f':^5} | {'기록':^5} | {'최근8r':^5} | {'연대':^3} | {'선행%':^3} | {'마명':^10} | {'트렌드':^6} | {'코멘트':^6}"
        # )
        # print("-" * 100)

        if predictions:
            for p in predictions:

                r_pop = p["expected_rank"]
                tot_score = p["score"]
                s1f_per = p["early_score"]
                g3f_per = p["late_score"]
                g1f_per = p["late200_score"]
                rec_per = p["speed_score"]    
                rec8_trend = p["form_score"]
                jt_score = p["conn_score"]
                start_score = p["front_run_place_prob"]
                comment_one = p["one_line_comment"]
                comment_all = p["reason"]

                try:
                    cursor = connection.cursor()
                    update_sql = """
                        UPDATE exp011
                        SET r_pop = %s,
                            tot_score = %s,
                            s1f_per = %s,
                            g3f_per = %s,
                            g1f_per = %s,
                            rec_per = %s,
                            rec8_trend = %s,
                            jt_score = %s,
                            start_score = %s,
                            comment_one = %s,
                            comment_all = %s
                        WHERE rcity = %s AND rdate = %s AND rno = %s AND gate = %s
                    """
                    cursor.execute(
                        update_sql,
                        (
                            r_pop,
                            tot_score,
                            s1f_per,
                            g3f_per,
                            g1f_per,
                            rec_per,
                            rec8_trend,
                            jt_score,
                            start_score,
                            comment_one,
                            comment_all,
                            rcity,
                            rdate,
                            rno,
                            p["gate"],
                        ),
                    )
                    connection.commit()
                except Exception as e:
                    print(f"Failed to update exp011: {e}")
                finally:
                    if cursor:
                        cursor.close()

                score_display = p["score"] if p["score"] is not None else 0.0
                early_display = p["early_score"] if p["early_score"] is not None else 0.0
                late_display = p["late_score"] if p["late_score"] is not None else 0.0
                late200_display = (
                    p["late200_score"] if p["late200_score"] is not None else 0.0
                )
                speed_display = (
                    p["speed_score"] if p["speed_score"] is not None else 0.0
                )
                form_display = p["form_score"] if p["form_score"] is not None else 0.0
                conn_display = p["conn_score"] if p["conn_score"] is not None else 0.0
                front_display = (
                    p["front_run_place_prob"]
                    if p["front_run_place_prob"] is not None
                    else 0.0
                )

                one_line_display = (
                    p["one_line_comment"] if p["one_line_comment"] is not None else ""
                )
                reason_display = p["reason"] if p["reason"] is not None else ""

                # print(
                #     f"{p['expected_rank']:^4} | {p['gate']:^6} | "
                #     f"{score_display:^6.2f} | {early_display:^5.1f} | {late_display:^5.1f} | {late200_display:^5.1f} | "
                #     f"{speed_display:^6.1f} | {form_display:^6.1f} | {conn_display:^6.1f} | {front_display:^6.1f} | {p['horse']:10} | {one_line_display:^60} | {reason_display:^1000}"
                # )

    except Exception as e:
        # 에러 내용도 같이 내려주면 디버깅 편함

        return JsonResponse(
            {
                "status": "error",
                "message": f"Failed Select exp011 / process_race: {e}",
            },
            status=500,
        )
    finally:
        if cursor:
            cursor.close()

    try:
        cursor = connection.cursor()
        update_sql = """
            UPDATE exp011
            SET r_pop = rank
            WHERE rcity = %s AND rdate = %s AND rno = %s AND rank >= 98
        """
        cursor.execute(
            update_sql,
            (
                rcity,
                rdate,
                rno
            ),
        )
        
        connection.commit()
    except Exception as e:
        print(f"Failed to update exp011: {e}")
    finally:
        if cursor:
            cursor.close()

    print("✅ ChatGPT 예측 exp011 tot_race = 0 update 완료")

    # update_m_rank_score_for_race(
    #             rcity, rdate, rno, model_name="sb_top3_20241129_20251130"
    #         )  # 저장해둔 모델 이름

    try:
        update_m_rank_score_for_race(
            rcity, rdate, rno, model_name=f"sb_top3_roll12_{rdate[0:6]}"
        )  # 저장해둔 모델 이름
    except Exception as e:
        print(f"⚠️ update_m_rank_score_for_race skipped: {e}")

    # exp011 점수/순위 반영 (단일 경주)
    try:
        update_exp011_for_race(rcity, rdate, int(rno))
    except Exception as e:
        print(f"⚠️ update_exp011_for_race skipped: {e}")

    # exp010 r_guide 업데이트 (단일 경주)
    try:
        info = run_rguide_update(
            rcity=rcity,
            rdate=rdate,
            rno=int(rno),
            dry_run=False,
        )
        updated = (info or {}).get("updated_rows")
        total = (info or {}).get("total_races")
        if updated is not None and total is not None:
            print(f"[done] {rcity} {rdate} R{rno} -> exp010={total} races, updated={updated} rows")
        else:
            print("✅ r_guide updated successfully.")
    except Exception as e:
        print(f"⚠️ r_guide update skipped: {e}")
    finally:
        print("---")

    # ✅ 예측 결과를 그대로 반환
    return JsonResponse(
        {
            "status": "success",
            "message": f"Exec chatGPT 실행 완료 ({rcity}, {rdate}, {rno})",
            "predictions": predictions,   # gate, horse, expected_rank, reason 등
        }
    )

def writeSignificant(request, rdate, horse):
    if request.method == "POST":
        start = request.POST.get("start")
        corners = request.POST.get("corners")
        finish = request.POST.get("finish")
        wrapup = request.POST.get("wrapup")
        r_etc = request.POST.get("r_etc")
        r_flag = request.POST.get("r_flag")
        
        h_memo = request.POST.get("h_memo")
        print('---', h_memo)

        try:
            cursor = connection.cursor()

            strSql = (
                """ update rec011 
                    set r_start = '"""
                + start
                + """',
                        r_corners = '"""
                + corners
                + """',
                        r_finish = '"""
                + finish
                + """',
                        r_wrapup = '"""
                + wrapup
                + """',
                        r_flag = '"""
                + r_flag
                + """',
                        r_etc = '"""
                + r_etc.strip()
                + """'
                    where rdate =  '"""
                + rdate
                + """'
                    and horse = '"""
                + horse
                + """'
                    ; """
            )

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            awards = cursor.fetchall()

        except:
            # connection.rollback()
            print("Failed updating in rec011")
        finally:
            cursor.close()

        try:
            
            with connection.cursor() as cur:
                sql = """
                INSERT INTO horse_memo
                    ( horse, rdate, memo )
                VALUES
                    (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    memo      = VALUES(memo) 
                    
                """

                values = ( horse, rdate, h_memo.strip() )
                cur.execute(sql, values)
                # connection.commit()
                print("성공적으로 INSERT 또는 UPDATE 완료")

        except Exception as e:
            print("DB 처리 중 오류 발생:", e)
            # connection.rollback()

        finally:
            connection.close()
            
        try:
            cursor = connection.cursor()
            strSql = (
                """ update record_s set r_flag = '"""
                + r_flag
                + """'
                        where rdate = '"""
                + rdate
                + """'
                        and horse = '"""
                + horse
                + """'
                        ;"""
            )
            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            r_significant = cursor.fetchall()

        except:
            connection.rollback()
            print("Failed updating r_flag")
        finally:
            cursor.close()

    try:
        cursor = connection.cursor()
        strSql = (
            """ select r_start, r_corners, r_finish, r_wrapup, r_etc, r_flag
                    from rec011 
                    where rdate = '"""
            + rdate
            + """'
                    and horse = '"""
            + horse
            + """'
                    ;"""
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_significant = cursor.fetchall()

    except:
        print("Failed selecting start")
    finally:
        cursor.close()

    try:
        cursor = connection.cursor()
        strSql = (
            """ select memo
                    from horse_memo 
                    where rdate = '"""
            + rdate
            + """'
                    and horse = '"""
            + horse
            + """'
                    ;"""
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        h_memo = cursor.fetchall()

    except:
        print("Failed selecting Horse Memo")
    finally:
        cursor.close()

    try:
        cursor = connection.cursor()
        strSql = """ select cd_type, r_code, r_name from race_cd order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race_cd = cursor.fetchall()

    except:
        print("Failed selecting r_start")
    finally:
        cursor.close()
        
    # print(r_significant, a)

    context = {
        "rdate": rdate,
        "horse": horse,
        "r_significant": r_significant,
        "race_cd": race_cd,
        # "r_start": r_start,
        # "r_corners": r_corners,
        # "r_finish": r_finish,
        # "r_wrapup": r_wrapup,
        "h_memo": h_memo,
    }
    return render(request, "base/write_significant.html", context)


