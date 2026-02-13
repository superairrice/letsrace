from apps.common import *

def home(request):

    q = request.GET.get("q") if request.GET.get("q") != None else ""  # 경마일

    view_type = request.GET.get("view_type") if request.GET.get("view_type") != None else ""  # 정렬방식

    if q == "":
        # rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]  # 초기값은 금요일

        # rdate = Racing.objects.values("rdate").distinct().order_by("rdate")[:1]

        try:
            cursor = connection.cursor()

            strSql = """ 
                    SELECT min(rdate)
                    FROM The1.exp010
                    WHERE rdate >= ( SELECT MAX(DATE_FORMAT(CAST(rdate AS DATE) - INTERVAL 4 DAY, '%Y%m%d')) FROM The1.exp010 WHERE rno < 80)
                ; """

            cursor.execute(strSql)
            rdate = cursor.fetchall()

        except:
            print("Failed selecting in rdate")
        finally:
            cursor.close()

        # print(rdate[0][0], type(rdate))
        i_rdate = rdate[0][0]

        fdate = i_rdate[0:4] + "-" + i_rdate[4:6] + "-" + i_rdate[6:8]

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]

        i_rdate = rdate
        fdate = q

    # topics = Topic.objects.exclude(name__icontains=q)

    racings = get_race(i_rdate, i_awardee="jockey")
    # race_board = get_board_list(i_rdate, i_awardee="jockey")

    race, expects, rdays, judged_jockey, changed_race, award_j = get_prediction(i_rdate)
    # print(racings)

    if view_type == "1":
        # expects는 raw SQL fetchall 결과(튜플)일 수 있음. 안전하게 정렬 키를 구성.
        def _exp_key(row):
            # 객체(Attr) 또는 튜플(Idx) 모두 지원
            if hasattr(row, "rcity"):
                return (row.rcity, row.rdate, row.rno, row.rank, row.gate)
            # 튜플 인덱스: a.rcity(0), a.rdate(1), a.rno(3), b.gate(4), b.rank(5)
            try:
                return (row[0], row[1], row[3], row[5], row[4])
            except Exception:
                return row
        expects = sorted(expects, key=_exp_key)

    # expects Query
    try:
        cursor = connection.cursor()

        strSql = (
            """
            select a.rcity, a.rdate, a.rday, a.rno, b.gate, b.rank, b.r_rank, b.horse, b.remark, b.jockey, b.trainer, b.host, b.r_pop, a.distance, b.handycap, b.i_prehandy, b.complex,
                b.complex5, b.gap_back, 
                b.jt_per, b.jt_cnt, b.jt_3rd,
                b.s1f_rank, b.i_cycle, a.rcount, recent3, recent5, convert_r, jockey_old, reason, b.alloc3r*1
            
            from exp010 a, exp011 b
            where a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno
            and a.rdate between date_format(DATE_ADD(%s, INTERVAL - 3 DAY), '%%Y%%m%%d') and date_format(DATE_ADD(%s, INTERVAL + 4 DAY), '%%Y%%m%%d')
            and b.rank in ( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 98, 99 ) 
            order by b.rcity, b.rdate, b.rno, b.rank, b.gate 
            ; """
        )
        cursor.execute(strSql, (i_rdate, i_rdate))
        results = cursor.fetchall()

    except:
        # connection.rollback()
        print("Failed selecting in expect ")
    finally:
        cursor.close()

    # loadin = get_last2weeks_loadin(i_rdate)

    rflag = False  # 경마일, 비경마일 구분
    for r in rdays:
        # print(r[0], r[2])
        if r[0] == r[2]:
            rflag = True
            break

    check_visit(request)

    base_dt = datetime.strptime(i_rdate, "%Y%m%d")
    from_date = (base_dt - timedelta(days=3)).strftime("%Y%m%d")
    to_date = (base_dt + timedelta(days=4)).strftime("%Y%m%d")

    race_df, summary = calc_rpop_anchor_26_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,
    )
    
    
    
    try:
        summary_keys = list(summary.keys()) if isinstance(summary, dict) else []
        race_rows = len(race_df) if race_df is not None else 0
        day_summary_len = (
            len(summary.get("day_summary", {})) if isinstance(summary, dict) else 0
        )
        print(
            "[rpop2] from_date=%s to_date=%s summary_type=%s summary_keys=%s "
            "race_rows=%s day_summary_len=%s"
            % (
                from_date,
                to_date,
                type(summary).__name__,
                summary_keys,
                race_rows,
                day_summary_len,
            )
        )
    except Exception as exc:
        print(f"[rpop2] debug failed: {exc}")

    summary_display = []
    summary_total = None
    method_bet_totals = []
    method_bet_total_sum = 0.0
    method_refund_total_sum = 0.0
    method_profit_total_sum = 0.0

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        method_columns = [
            ("1축 2~4 5~7", "1축_2~4_5~7_베팅액", "1축_2~4_5~7_환수액"),
            ("1축 2~4", "1축_2~4_베팅액", "1축_2~4_환수액"),
            ("1축 2~6 삼복", "1축_2~6_삼복_베팅액", "1축_2~6_삼복_환수액"),
            ("1~2복조 3~8 삼복", "1~2복조_3~8_삼복_베팅액", "1~2복조_3~8_삼복_환수액"),
            ("BOX4 삼복", "BOX4_삼복_베팅액", "BOX4_삼복_환수액"),
        ]
        for label, bet_col, refund_col in method_columns:
            if bet_col in race_df.columns and refund_col in race_df.columns:
                bet_amount = float(race_df[bet_col].fillna(0).sum())
                refund_amount = float(race_df[refund_col].fillna(0).sum())
                profit_amount = refund_amount - bet_amount
                method_bet_totals.append(
                    {
                        "label": label,
                        "amount": bet_amount,
                        "refund": refund_amount,
                        "profit": profit_amount,
                    }
                )
                method_bet_total_sum += bet_amount
                method_refund_total_sum += refund_amount
                method_profit_total_sum += profit_amount

    if isinstance(summary, dict):
        day_summary = summary.get("day_summary", {})
        track_summary = summary.get("track_summary", {})
        day_hit_summary = summary.get("day_hit_summary", {})
        track_hit_summary = summary.get("track_hit_summary", {})
        use_track = bool(track_summary)
        summary_source = track_summary if use_track else day_summary
        hit_source = track_hit_summary if use_track else day_hit_summary
        total_races = 0
        total_bet = 0.0
        total_refund = 0.0
        total_hits = 0
        total_r_pop1_top3_hits = 0
        for key in sorted(summary_source.keys()):
            d = summary_source[key]
            hits_detail = hit_source.get(key, [])
            refund_rate = (
                d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
            )
            hit_rate = d["hits"] / d["races"] if d["races"] > 0 else 0.0
            profit = d["total_refund"] - d["total_bet"]
            avg_bet = d["total_bet"] / d["races"] if d["races"] > 0 else 0.0
            summary_display.append(
                {
                    "label": key,
                    "races": d["races"],
                    "refund_rate": refund_rate,
                    "total_bet": d["total_bet"],
                    "total_refund": d["total_refund"],
                    "profit": profit,
                    "hits": d["hits"],
                    "hit_rate": hit_rate,
                    "avg_bet": avg_bet,
                    "hit_details": hits_detail,
                }
            )
            total_races += d["races"]
            total_bet += d["total_bet"]
            total_refund += d["total_refund"]
            total_hits += d["hits"]
            total_r_pop1_top3_hits += d.get("r_pop1_top3_hits", 0)
        if total_races > 0:
            total_profit = total_refund - total_bet
            total_refund_rate = total_refund / total_bet if total_bet > 0 else 0.0
            total_hit_rate = total_hits / total_races if total_races > 0 else 0.0
            total_avg_bet = total_bet / total_races if total_races > 0 else 0.0
            total_r_pop1_top3_rate = (
                total_r_pop1_top3_hits / total_races if total_races > 0 else 0.0
            )
            summary_total = {
                "races": total_races,
                "total_bet": total_bet,
                "total_refund": total_refund,
                "profit": total_profit,
                "hits": total_hits,
                "hit_rate": total_hit_rate,
                "r_pop1_top3_hits": total_r_pop1_top3_hits,
                "r_pop1_top3_rate": total_r_pop1_top3_rate,
                "refund_rate": total_refund_rate,
                "avg_bet": total_avg_bet,
            }
        else:
            summary_total = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "profit": 0.0,
                "hits": 0,
                "hit_rate": 0.0,
                "r_pop1_top3_hits": 0,
                "r_pop1_top3_rate": 0.0,
                "refund_rate": 0.0,
                "avg_bet": 0.0,
            }

    # print(summary_display)

    context = {
        "racings": racings,
        "expects": expects,
        "results": results,
        "fdate": fdate,
        # "loadin": loadin,
        # "race_detail": race_detail,
        # "race_board": race_board,
        # "jname1": jname1,
        # "jname2": jname2,
        # "jname3": jname3,
        "award_j": award_j,
        "race": race,
        # "t_count": t_count,
        "rdays": rdays,
        "judged_jockey": judged_jockey,
        "changed_race": changed_race,               #출마표 젼경
        "rflag": rflag,  # 경마일, 비경마일 구분
        "view_type": view_type,
        "summary": summary,
        "summary_display": summary_display,
        "summary_total": summary_total,
        "method_bet_totals": method_bet_totals,
        "method_bet_total_sum": method_bet_total_sum,
        "method_refund_total_sum": method_refund_total_sum,
        "method_profit_total_sum": method_profit_total_sum,

    }

    return render(request, "base/home.html", context)

# @login_required(login_url="home")

def racingPage(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )
    return render(request, "base/race.html", {"racings": racings})

def leftPage(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )
    return render(request, "base/left_component.html", {"racings": racings})

def rightPage(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )

    r_results = RaceResult.objects.all().order_by("rdate", "rcity", "rno")
    return render(request, "base/right_component.html", {"r_results": r_results})

def exp011(request, pk):
    room = Exp011.objects.get(rdate=pk)
    print(room.key())
    room_messages = room.message_set.all().order_by("-rank")
    participants = room.participants.all()

    if request.method == "POST":
        message = Message.objects.create(
            user=request.user, room=room, body=request.POST.get("body")
        )
        room.participants.add(request.user)
        return redirect("room", pk=room.id)

    context = {
        "room": room,
        "room_messages": room_messages,
        "participants": participants,
    }
    return render(request, "base/room.html", context)

def pyscriptTest(request):
    pass

    return render(request, "base/pyscript_test.html")

def send_email():
    subject = "message"
    to = ["keombit@gmail.com"]
    from_email = "id@gmail.com"
    message = "메지시 테스트"
    EmailMessage(subject=subject, body=message, to=to, from_email=from_email).send()
# 주별 입상마 경주전개 현황
