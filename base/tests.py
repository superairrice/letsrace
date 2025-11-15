def mockAudit(request, rcity, rdate, rno, hname, awardee):
    """
    mockAudit view (리팩토링)
    - 기본: 초기 로드 -> 조회만 (집계 X)
    - ?calc=1 이면 -> 집계 로직 실행(UPDATE/INSERT 등) 후 HttpResponse 반환
    """

    # 1) 기본 가중치 조회 (외부 유틸 함수)
    try:
        weight = get_weight2(rcity, rdate, rno)  # 예상: list/tuple 형태
        # weight[0] 에 (w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert, w_flag, wdate) 등 있다고 가정
    except Exception as e:
        print("❌ get_weight2 에러:", e)
        weight = None

    if not weight:
        messages.error(request, "가중치 조회 실패")
        # 조회용 빈 컨텍스트로 렌더하거나 적절히 처리
        return render(request, "base/mock_audit.html", {})

    # wdate는 weight[0][7]이 datetime이라고 가정
    try:
        wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        wdate = None

    # 2) 사용자 입력 가중치 (GET으로도 받음; 없으면 기본 weight 사용)
    # request.GET.get(...) 의 반환은 str 이므로 int 변환은 집계시 수행
    w_avg = request.GET.get("w_avg") or weight[0][0]
    w_fast = request.GET.get("w_fast") or weight[0][1]
    w_slow = request.GET.get("w_slow") or weight[0][2]
    w_recent3 = request.GET.get("w_recent3") or weight[0][3]
    w_recent5 = request.GET.get("w_recent5") or weight[0][4]
    w_convert = request.GET.get("w_convert") or weight[0][5]
    w_flag = request.GET.get("w_flag") or weight[0][6]

    # DB에서의 r_condition (Exp010)
    try:
        r_condition = Exp010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except Exp010.DoesNotExist:
        messages.error(request, "경주 조건을 찾을 수 없습니다.")
        return render(request, "base/home.html")

    # weight_mock: 비교를 위해 동일한 형태로 만듦 (원래 코드의 형태 유지)
    try:
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
        )
    except Exception:
        # 만약 GET 파라미터가 문자열 등으로 들어와 int 변환 실패하면,
        # 원래 weight 값과 비교하지 않고 넘어감
        weight_mock = None

    # 3) 가중치 합 검증 (숫자형으로 변환 필요)
    try:
        total1 = int(w_avg) + int(w_fast) + int(w_slow)
        total2 = int(w_recent3) + int(w_recent5) + int(w_convert)
        weight_sum_ok = total1 == 100 and total2 == 100
    except Exception:
        weight_sum_ok = False

        # 4) 만약 가중치가 변경되었고 합이 올바르면 weight_s2에 INSERT 및 mock_traval2 실행
        #    (그러나 실제 집계는 do_calc 체크에서만 수행하므로 여기서는 조회 전용)
        #    => 이 블록은 calc==1 일 때도 중복 수행되지 않도록 do_calc 분기로 옮김

        # 5-2) mock_insert2 실행 (외부 함수, DB 변경이 있을 수 있으므로 예외처리)
    try:
        mock_insert2(rcity, rdate, rno)
    except Exception as e:
        print("❌ mock_insert2 에러:", e)
        return HttpResponse("Error: mock_insert2 failed", status=500)

    # 5) do_calc 체크: ?calc=1 이면 집계 실행 (fetch로 호출되는 경우)
    do_calc = request.GET.get("calc", "0")
    if do_calc == "1":
        # print("✅ Mock 집계 실행 시작:", rcity, rdate, rno)

        # 5-1) rec011.i_mock 초기화 (UPDATE)
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

        # 5-3) 만약 가중치가 변경되었으면 weight_s2에 기록 및 mock_traval2 실행
        #      기존 코드와 동일한 로직을 안전하게 수행
        if weight_mock is not None and weight != weight_mock and weight_sum_ok:
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

            # DB에 반영된 새 weight는 필요하면 get_weight2로 다시 가져오거나,
            # 바로 weight_mock을 사용하여 mock_traval2 호출
            try:
                mock_traval2(r_condition, weight_mock)
            except Exception as e:
                print("❌ mock_traval2 에러:", e)
                return JsonResponse({"status": "error", "msg": "Broken pipe"})

        # 5-4) w_flag에 따른 메시지 (원래 로직 유지)
        if str(w_flag) == "0" or w_flag == 0:
            messages.warning(request, "weight_s1")
        else:
            messages.warning(request, "weight only")

        # print(f"✅ Mock 집계 실행 완료: {rcity}, {rdate}, {rno}")
        # Ajax 호출(프론트)의 경우 간단 텍스트 또는 JSON 반환
        return JsonResponse({"status": "ok", "message": "Mock 집계 완료"})

    # 6) calc != 1 이면 -> 초기 로드(조회) 모드: DB에서 필요한 데이터 조회 후 context 생성
    # exp011s 조회
    exp011s = Exp011s2.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "rank", "gate"
    )
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
