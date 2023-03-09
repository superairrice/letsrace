from datetime import date, datetime
import os
import pandas as pd

from django.contrib import messages
# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Count, Max, Min, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from base.data_management import get_breakingnews, get_file_contents, get_kradata, get_krafile, krafile_convert

from base.mysqls import (get_award, get_award_race, get_jockey_trend, get_judged, get_judged_horse, get_judged_jockey, get_last2weeks_loadin, get_paternal,
                         get_paternal_dist, get_pedigree, get_popularity_rate, get_prediction, get_print_prediction, get_race, get_race_center_detail_view, get_status_train, get_train, get_train_audit, get_train_horse,
                         get_training, get_status_training, get_weeks, get_last2weeks)
from letsrace.settings import KRAFILE_ROOT

# import base.mysqls

from .forms import MyUserCreationForm, RoomForm, UserForm
# from django.contrib.auth.forms import UserCreationForm
from .models import (Award, Exp010, Exp011, Exp012, JockeyW, JtRate, Message,
                     RaceResult, Racing, Rec010, RecordS, Room, Topic, User)

from django.core.files.storage import FileSystemStorage  # 파일저장

from django.views.decorators.csrf import csrf_exempt


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, messages.warning)

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def registerPage(request):
    # page = 'register'
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.warning(request, form.errors)

            print(form.errors)
            print(form.non_field_errors())

    return render(request, 'base/login_register.html', {'form': form})


def logoutUser(request):
    logout(request)
    return redirect('home')


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    context = {"user": user, "rooms": rooms,
               "room_messages": room_messages, "topics": topics, }
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    # render(request, 'base/room_form.html', context)
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    print(room.host)
    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    # print(user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()

            request_file = request.FILES['filename[]'] if 'filename[]' in request.FILES else None
            if request_file:
                # save attached file
                # create a new instance of FileSystemStorage
                fs = FileSystemStorage()
                file = fs.save(request_file.name, request_file)
                # the fileurl variable now contains the url to the file. This can be used to serve the file when needed.
                fileurl = fs.url(file)

                print(fileurl)

            redirect('user-profile', pk=user.id)

    return render(request, 'base/update-user.html', {'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})


def activityPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    room_messages = Message.objects.all()

    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )

    first_race = racings[0]         # 첫번째 경주 조건

    horse = Exp011.objects.filter(rcity=first_race.rcity,
                                  rdate=first_race.rdate,
                                  rno=first_race.rno,
                                  rank=1).get()
    print(horse.horse)

    print(datetime.today().weekday())

    h_records = RecordS.objects.filter(horse=horse.horse).order_by('-rdate')

    context = {'room_messages': room_messages,
               'horse': horse,
               'h_records': h_records}

    return render(request, 'base/activity.html', context)


def racingPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )
    return render(request, 'base/race.html', {'racings': racings})


def leftPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )
    return render(request, 'base/left_component.html', {'racings': racings})


def rightPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )

    r_results = RaceResult.objects.all().order_by('rdate', 'rcity', 'rno')
    return render(request, 'base/right_component.html', {'r_results': r_results})


def exp011(request, pk):
    room = Exp011.objects.get(rdate=pk)
    print(room.key())
    room_messages = room.message_set.all().order_by('-rank')
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


def home(request):
    q = request.GET.get('q') if request.GET.get(
        'q') != None else ''            # 경마일

    if q == '':
        rdate = Racing.objects.values('rdate').distinct()[
            0]['rdate']          # 초기값은 금요일
        fdate = rdate[0:4] + '-' + rdate[4:6] + '-' + rdate[6:8]

        rdate = Racing.objects.values('rdate').distinct()
        i_rdate = rdate[0]['rdate']

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]
        fdate = q

    jname1 = request.GET.get('j1') if request.GET.get('j1') != None else ''
    jname2 = request.GET.get('j2') if request.GET.get('j2') != None else ''
    jname3 = request.GET.get('j3') if request.GET.get('j3') != None else ''

    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )

    # race = get_race(i_rdate, i_awardee='jockey')
    # race = get_race_center_detail_view(i_rdate, i_awardee='jockey')

    # r_results = RaceResult.objects.all().order_by('rdate', 'rcity', 'rno')
    r_results = RaceResult.objects.filter(
        Q(jockey1__icontains=q) |
        Q(jockey2__icontains=q) |
        Q(jockey3__icontains=q) |
        Q(jockey4__icontains=q) |
        Q(jockey5__icontains=q) |
        Q(jockey6__icontains=q) |
        Q(jockey7__icontains=q)).order_by('rdate', 'rcity', 'rno')

    race, expects = get_prediction(i_rdate)

    print(race)

    context = {'racings': racings, 'expects': expects,
               'jname1': jname1,
               'jname2': jname2,
               'jname3': jname3,
               'r_results': r_results, 'race': race, 'q': q}

    return render(request, 'base/home.html', context)


def homePage_a(request, rcity, rdate):

    racings = Racing.objects.filter(rcity=rcity, rdate=rdate)
    print(racings.query)
    context = {'rcity': rcity, 'racings': racings}

    return render(request, 'base/home_a.html', context)


def activityPage_a(request, hname):
    # q = request.GET.get('q') if request.GET.get('q') != None else ''

    h_records = RecordS.objects.filter(horse=hname).order_by('-rdate')

    horse = h_records[0]

    context = {'horse': horse,
               'h_records': h_records}

    return render(request, 'base/activity_a.html', context)


def activityComponentPage_a(request, hname):
    # q = request.GET.get('q') if request.GET.get('q') != None else ''

    h_records = RecordS.objects.filter(horse=hname).order_by('-rdate')

    horse = h_records[0]

    context = {'horse': horse,
               'h_records': h_records}

    return render(request, 'base/activity_component_a.html', context)


def predictionRace(request, rcity, rdate, rno, hname, awardee):

    exp011s = Exp011.objects.filter(rcity=rcity,
                                    rdate=rdate,
                                    rno=rno).order_by('rank', 'gate')
    if exp011s:
        pass
    else:
        return render(request, 'base/home.html')

    if (exp011s.values("rank")[4].get('rank') > 90):  # 신마일경우 skip
        complex5 = '0:00.0'
    else:
        complex5 = exp011s.values("complex")[4]

        if complex5:
            pass
        else:
            return render(request, 'base/home.html')

    r_condition = Exp010.objects.filter(
        rcity=rcity, rdate=rdate, rno=rno).get()

    # h_records = RecordS.objects.filter(
    #     rdate__lt=rdate, horse=horse.horse).order_by('-rdate')

    hr_records = RecordS.objects.filter(
        rdate__lt=rdate, horse__in=exp011s.values("horse")).order_by('horse', '-rdate')

    # hr_pedigree = Exp012.objects.filter(
    #     rdate__lt=rdate, horse__in=exp011s.values("horse")).order_by('-rdate')

    # print(hr_records.query)

    # training_team = get_training_team(rcity, rdate, rno)

    race = get_race(rdate, i_awardee='jockey')

    compare_r = exp011s.aggregate(Min('i_s1f'), Min('i_g1f'), Min('i_g2f'), Min('i_g3f'), Max(
        'handycap'), Max('rating'), Max('r_pop'), Max('j_per'), Max('t_per'), Max('jt_per'))

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    paternal = get_paternal(
        rcity, rdate, rno, r_condition.distance)    # 부마 3착 성적
    paternal_dist = get_paternal_dist(
        rcity, rdate, rno)                # 부마 거리별 3착 성적

    pedigree = get_pedigree(rcity, rdate, rno)                          # 병력
    # training = get_training(rcity, rdate, rno)
    # train = get_train(rcity, rdate, rno)
    train = get_train_horse(rcity, rdate, rno)

    h_audit = get_train_audit(rcity, rdate, rno)

    popularity_rate = get_popularity_rate(
        rcity, rdate, rno)            # 인기순위별 승률

    judged = get_judged(rcity, rdate, rno)
    judged_horse = get_judged_horse(rcity, rdate, rno)
    judged_jockey = get_judged_jockey(rcity, rdate, rno)

    trend_j = get_jockey_trend(rcity, rdate, rno)

    # print(trend_j)

    context = {'exp011s': exp011s,
               'r_condition': r_condition,
               'complex5': complex5,
               'hr_records': hr_records,
               'compare_r': compare_r,
               'alloc': alloc,
               'judged': judged,
               'judged_horse': judged_horse,
               'judged_jockey': judged_jockey,
               'race': race,
               'pedigree': pedigree,
               'paternal': paternal,
               'paternal_dist': paternal_dist,
               # 'hr_pedigree': hr_pedigree,

               'popularity_rate': popularity_rate,
               #    'training': training,
               'train': train,
               'h_audit': h_audit,
               'trend_j': trend_j.to_html(index=False, header=True, justify="right", classes="rwd-table", table_id="rwd-table"),
               #  'pdf1': pdf1,
               }

    return render(request, 'base/prediction_race.html', context)


def awards(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )

    room_count = Exp011.objects.all().count()
    room_messages = Message.objects.filter(Q(room__name__icontains=q))

    # rdates = Racing.objects.distinct().values_list('rdate')
    rdays = Racing.objects.distinct().values('rcity', 'rdate', 'rday', 'rno', 'distance', 'rcount', 'grade',
                                             'dividing', 'rname', 'rcon1', 'rcon2',  'rtime').order_by('rdate', '-rcity', 'rno')

    seoul = Racing.objects.filter(rcity='서울').values(
        'rdate', 'rday').annotate(rcount=Count('rdate'))
    busan = Racing.objects.filter(rcity='부산').values(
        'rdate', 'rday').annotate(rcount=Count('rdate'))

    seoul_fri = Racing.objects.filter(rcity='서울', rday='금').distinct().values('rcity', 'rdate', 'rday', 'rno', 'distance', 'rcount', 'grade',
                                                                              'dividing', 'rname', 'rcon1', 'rcon2',  'rtime').order_by('rno')
    seoul_sat = Racing.objects.filter(rcity='서울', rday='토').distinct().values('rcity', 'rdate', 'rday', 'rno', 'distance', 'rcount', 'grade',
                                                                              'dividing', 'rname', 'rcon1', 'rcon2',  'rtime').order_by('rno')
    seoul_sun = Racing.objects.filter(rcity='서울', rday='일').distinct().values('rcity', 'rdate', 'rday', 'rno', 'distance', 'rcount', 'grade',
                                                                              'dividing', 'rname', 'rcon1', 'rcon2',  'rtime').order_by('rno')
    busan_fri = Racing.objects.filter(rcity='부산', rday='금').distinct().values('rcity', 'rdate', 'rday', 'rno', 'distance', 'rcount', 'grade',
                                                                              'dividing', 'rname', 'rcon1', 'rcon2',  'rtime').order_by('rno')
    busan_sat = Racing.objects.filter(rcity='부산', rday='토').distinct().values('rcity', 'rdate', 'rday', 'rno', 'distance', 'rcount', 'grade',
                                                                              'dividing', 'rname', 'rcon1', 'rcon2',  'rtime').order_by('rno')
    busan_sun = Racing.objects.filter(rcity='부산', rday='일').distinct().values('rcity', 'rdate', 'rday', 'rno', 'distance', 'rcount', 'grade',
                                                                              'dividing', 'rname', 'rcon1', 'rcon2',  'rtime').order_by('rno')

    # print(seoul_sat)

    first_race = racings[0]         # 첫번째 경주 조건

    exp011s = Exp011.objects.filter(rcity=first_race.rcity,
                                    rdate=first_race.rdate,
                                    rno=first_race.rno).order_by('rank')

    horse = Exp011.objects.filter(rcity=first_race.rcity,
                                  rdate=first_race.rdate,
                                  rno=first_race.rno,
                                  rank=1).get()

    # print(datetime.today().weekday())
    # print(seoul)

    h_records = RecordS.objects.filter(horse=horse.horse).order_by('-rdate')

    # 금주 경주예상 종합

    rdate = Racing.objects.values('rdate').distinct()
    # print(rdate[0]['rdate'])

    i_rdate = rdate[0]['rdate']
    awards = get_award(i_rdate, i_awardee='jockey')

    r_results = RaceResult.objects.all().order_by('rdate', 'rcity', 'rno')
    # .filter( rdate__in=rdate.values_list('rdate', flat=True))

    allocs = Rec010.objects.filter(rdate__in=rdate.values_list(
        'rdate', flat=True)).order_by('rdate', 'rcity', 'rno')

    print(awards)

    context = {'rooms': rooms,
               'racings': racings,
               'room_count': room_count,
               'room_messages': room_messages,
               'rdays': rdays,
               'first_race': first_race,
               'exp011s': exp011s,
               'horse': horse,
               'seoul': seoul,
               'seoul_fri': seoul_fri,
               'seoul_sat': seoul_sat,
               'seoul_sun': seoul_sun,
               'busan_fri': busan_fri,
               'busan_sat': busan_sat,
               'busan_sun': busan_sun,
               'rdate': rdate,
               'r_results': r_results,
               'allocs': allocs,
               'awards': awards,
               'busan': busan,
               'h_records': h_records}

    return render(request, 'base/awards.html', context)


def updatePopularity(request, rcity, rdate, rno):

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)
    context = {'rcity': rcity, 'exp011s': exp011s}

    # user = request.user
    # form = UserForm(instance=user)

    if request.method == 'POST':

        myDict = dict(request.POST)
        print(myDict['pop_1'][0])

        for race in exp011s:
            pop = 'pop_' + str(race.gate)

            try:
                cursor = connection.cursor()

                strSql = """ update exp011 set r_pop = """ + myDict[pop][0] + """, r_rank = """ + myDict[pop][1] + """
														where rdate = '""" + rdate + """' and rcity = '""" + rcity + """' and rno = """ + str(rno) + """ and gate = """ + str(race.gate) + """
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
                print("Failed selecting in BookListView")

        # form = Exp011(request.POST, request.FILES, rcity=rcity, rdate=rdate, rno=rno, instance=pop_1)
        # if form.is_valid():
        #     form.save()
        #     redirect('user-profile', pk=rdate)

    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)
    return render(request, 'base/update_popularity.html', context)


def raceResult(request, rcity, rdate, rno, hname, awardee):

    records = RecordS.objects.filter(rcity=rcity,
                                     rdate=rdate,
                                     rno=rno).order_by('rank', 'gate')
    if records:
        pass
    else:
        return render(request, 'base/home.html')

    r_condition = Rec010.objects.filter(
        rcity=rcity, rdate=rdate, rno=rno).get()

    hr_records = RecordS.objects.filter(
        rdate__lt=rdate, horse__in=records.values("horse")).order_by('horse', '-rdate')

    compare_r = records.aggregate(Min('i_s1f'), Min('i_g1f'), Min(
        'i_g2f'), Min('i_g3f'), Max('handycap'), Max('rating'))

    # judged = get_judged(rcity, rdate, rno)
    judged_horse = get_judged_horse(rcity, rdate, rno)
    # judged_jockey = get_judged_jockey(rcity, rdate, rno)

    pedigree = get_pedigree(rcity, rdate, rno)
    # training = get_training(rcity, rdate, rno)
    train = get_train_horse(rcity, rdate, rno)
    h_audit = get_train_audit(rcity, rdate, rno)

    train = sorted(train, key=lambda x: x[5] or 99)
    pedigree = sorted(pedigree, key=lambda x: x[2] or 99)
    # print(h_audit)

    context = {'records': records,
               'r_condition': r_condition,
               #    'training': training,
               'train': train,
               'hr_records': hr_records,
               'compare_r': compare_r, 'hname': hname,
               'pedigree': pedigree,
               'h_audit': h_audit,
               'judged_horse': judged_horse,
               }

    return render(request, 'base/race_result.html', context)


def raceTrain(request, rcity, rdate, rno):

    train = get_train_horse(rcity, rdate, rno)

    context = {
        'train': train,

    }

    return render(request, 'base/race_train.html', context)


def printPrediction(request):

    q = request.GET.get('q') if request.GET.get('q') != None else ''

    if q == '':
        rdate = Racing.objects.values('rdate').distinct()[
            0]['rdate']          # 초기값은 금요일
        fdate = rdate[0:4] + '-' + rdate[4:6] + '-' + rdate[6:8]

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]
        fdate = q

    rcity = request.GET.get('rcity') if request.GET.get(
        'rcity') != None else '부산'

    jname1 = request.GET.get('j1') if request.GET.get('j1') != None else ''
    jname2 = request.GET.get('j2') if request.GET.get('j2') != None else ''
    jname3 = request.GET.get('j3') if request.GET.get('j3') != None else ''

    race, expects = get_print_prediction(rcity, rdate)

    if race:
        context = {'expects': expects, 'race': race, 'fdate': fdate,
                   'jname1': jname1, 'jname2': jname2, 'jname3': jname3}
    else:
        messages.warning(request, fdate + " " + rcity + " 경마 데이터가 없습니다.")
        context = {'expects': expects, 'race': race, 'fdate': fdate,
                   'jname1': jname1, 'jname2': jname2, 'jname3': jname3}

    return render(request, 'base/print_prediction.html', context)


def awardStatusTrainer(request):

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    jname1 = request.GET.get('j1') if request.GET.get('j1') != None else ''
    jname2 = request.GET.get('j2') if request.GET.get('j2') != None else ''
    jname3 = request.GET.get('j3') if request.GET.get('j3') != None else ''

    if q == '':

        today = datetime.today()
        if today.weekday() == 5:  # {0:월, 1:화, 2:수, 3:목, 4:금, 5:토, 6:일}
            rdate = Racing.objects.values('rdate').distinct()[1]['rdate']
        elif today.weekday() == 6:
            rdate = Racing.objects.values('rdate').distinct()[2]['rdate']
        else:
            rdate = Racing.objects.values('rdate').distinct()[0]['rdate']

        friday = Racing.objects.values('rdate').distinct()[
            0]['rdate']          # weeks 기준일
        fdate = friday[0:4] + '-' + friday[4:6] + '-' + friday[6:8]

    else:

        print(q[5:7] + '-' + q[8:10] + '-' + q[0:4])
        today = datetime.strptime(
            q[5:7] + '-' + q[8:10] + '-' + q[0:4], '%m-%d-%Y')
        # friday =
        print(today)

        if today.weekday() == 4:
            rdate = q[0:4] + q[5:7] + q[8:10]
            friday = rdate
            fdate = friday[0:4] + '-' + friday[4:6] + '-' + friday[6:8]

        else:

            rdate = q[0:4] + q[5:7] + q[8:10]

            friday = rdate
            fdate = q

            messages.warning(request, "선택된 날짜가 금요일이 아닙니다.")

    weeks = get_last2weeks(friday, i_awardee='trainer')
    loadin = get_last2weeks_loadin(friday)
    # status = get_status_training(rdate)
    status = get_status_train(rdate)

    context = {'weeks': weeks, 'loadin': loadin, 'status': status, 'fdate': fdate,
               'jname1': jname1, 'jname2': jname2, 'jname3': jname3}

    return render(request, 'base/award_status_trainer.html', context)


def awardStatusJockey(request):

    q = request.GET.get('q') if request.GET.get('q') != None else ''
    jname1 = request.GET.get('j1') if request.GET.get('j1') != None else ''
    jname2 = request.GET.get('j2') if request.GET.get('j2') != None else ''
    jname3 = request.GET.get('j3') if request.GET.get('j3') != None else ''

    if q == '':

        today = datetime.today()
        if today.weekday() == 5:  # {0:월, 1:화, 2:수, 3:목, 4:금, 5:토, 6:일}
            rdate = Racing.objects.values('rdate').distinct()[1]['rdate']
        elif today.weekday() == 6:
            rdate = Racing.objects.values('rdate').distinct()[2]['rdate']
        else:
            rdate = Racing.objects.values('rdate').distinct()[0]['rdate']

        friday = Racing.objects.values('rdate').distinct()[
            0]['rdate']          # weeks 기준일
        fdate = friday[0:4] + '-' + friday[4:6] + '-' + friday[6:8]

    else:

        print(q[5:7] + '-' + q[8:10] + '-' + q[0:4])
        today = datetime.strptime(
            q[5:7] + '-' + q[8:10] + '-' + q[0:4], '%m-%d-%Y')
        # friday =
        print(today)

        if today.weekday() == 4:
            rdate = q[0:4] + q[5:7] + q[8:10]
            friday = rdate
            fdate = friday[0:4] + '-' + friday[4:6] + '-' + friday[6:8]

        else:

            rdate = q[0:4] + q[5:7] + q[8:10]

            friday = rdate
            fdate = q

            messages.warning(request, "선택된 날짜가 금요일이 아닙니다.")

    weeks = get_last2weeks(friday, i_awardee='jockey')
    loadin = get_last2weeks_loadin(friday)
    # status = get_status_training(rdate)
    status = get_status_train(rdate)

    context = {'weeks': weeks, 'loadin': loadin, 'status': status, 'fdate': fdate,
               'jname1': jname1, 'jname2': jname2, 'jname3': jname3}

    return render(request, 'base/award_status_jockey.html', context)


def dataManagement(request):

    rcity = request.GET.get('rcity') if request.GET.get(
        'rcity') != None else ''
    q1 = request.GET.get('q1') if request.GET.get('q1') != None else ''
    q2 = request.GET.get('q2') if request.GET.get('q2') != None else ''
    fcode = request.GET.get('fcode') if request.GET.get(
        'fcode') != None else ''
    fstatus = request.GET.get('fstatus') if request.GET.get(
        'fstatus') != None else ''

    if q1 == '':

        friday = Racing.objects.values('rdate').distinct()[
            0]['rdate']          # weeks 기준일
        sunday = Racing.objects.values('rdate').distinct()[
            2]['rdate']          # weeks 기준일

        rdate1 = friday[0:4] + friday[4:6] + friday[6:8]
        rdate2 = sunday[0:4] + sunday[4:6] + sunday[6:8]

        fdate1 = friday[0:4] + '-' + friday[4:6] + '-' + friday[6:8]
        fdate2 = sunday[0:4] + '-' + sunday[4:6] + '-' + sunday[6:8]

    else:

        rdate1 = q1[0:4] + q1[5:7] + q1[8:10]
        rdate2 = q2[0:4] + q2[5:7] + q2[8:10]

        fdate1 = q1[0:4] + '-' + q1[5:7] + '-' + q1[8:10]
        fdate2 = q2[0:4] + '-' + q2[5:7] + '-' + q2[8:10]

    krafile = get_krafile(rcity, rdate1, rdate2, fcode, fstatus)
    if krafile:
        messages.warning(request, '총 ' + str(len(krafile)) + '건이 검색되었습니다.')
    else:
        messages.warning(request, "검색된 결과가 없습니다.")
    # kradata = get_kradata(rcity, rdate1, rdate2, fcode, fstatus)

    # print(krafile)
    # print(kradata)

    if request.method == 'POST':
        myDict = dict(request.POST)

        krafile_convert(myDict['rcheck'])

        # for fname in myDict['rcheck']:
        #     print(fname)

        #     if fname[-12:-10] == '11':
        #         print(fname[-12:-10])

        #     file = open(fname, "r")
        #     while True:
        #         line = file.readline()
        #         if not line:
        #             break
        #         print(line.strip())
        #     file.close()

    context = {'q1': q1, 'q2': q2, 'fcode': fcode, 'fstatus': fstatus,
               'krafile': krafile,
               #    'kradata': kradata,
               'fdate1': fdate1, 'fdate2': fdate2}

    return render(request, 'base/data_management.html', context)


def dataBreakingNews(request):

    rcity = request.GET.get('rcity') if request.GET.get(
        'rcity') != None else ''
    q1 = request.GET.get('q1') if request.GET.get('q1') != None else ''
    q2 = request.GET.get('q2') if request.GET.get('q2') != None else ''
    title = request.GET.get('title') if request.GET.get(
        'title') != None else ''

    if q1 == '':

        friday = Racing.objects.values('rdate').distinct()[
            0]['rdate']          # weeks 기준일
        sunday = Racing.objects.values('rdate').distinct()[
            2]['rdate']          # weeks 기준일

        rdate1 = friday[0:4] + friday[4:6] + friday[6:8]
        rdate2 = sunday[0:4] + sunday[4:6] + sunday[6:8]

        fdate1 = friday[0:4] + '-' + friday[4:6] + '-' + friday[6:8]
        fdate2 = sunday[0:4] + '-' + sunday[4:6] + '-' + sunday[6:8]

    else:

        rdate1 = q1[0:4] + q1[5:7] + q1[8:10]
        rdate2 = q2[0:4] + q2[5:7] + q2[8:10]

        fdate1 = q1[0:4] + '-' + q1[5:7] + '-' + q1[8:10]
        fdate2 = q2[0:4] + '-' + q2[5:7] + '-' + q2[8:10]

    breakingnews = get_breakingnews(rcity, rdate1, rdate2, title)
    print(breakingnews)
    if breakingnews:
        messages.warning(
            request, '총 ' + str(len(breakingnews)) + '건이 검색되었습니다.')
    else:
        messages.warning(request, "검색된 결과가 없습니다.")
    # kradata = get_kradata(rcity, rdate1, rdate2, title, fstatus)

    # print(breakingnews)
    # print(kradata)

    if request.method == 'POST':
        myDict = dict(request.POST)

        # breakingnews_convert(myDict['rcheck'])

        # for fname in myDict['rcheck']:
        #     print(fname)

        #     if fname[-12:-10] == '11':
        #         print(fname[-12:-10])

        #     file = open(fname, "r")
        #     while True:
        #         line = file.readline()
        #         if not line:
        #             break
        #         print(line.strip())
        #     file.close()

    context = {'q1': q1, 'q2': q2, 'title': title,
               'breakingnews': breakingnews,
               'fdate1': fdate1, 'fdate2': fdate2}

    return render(request, 'base/data_breakingnews.html', context)


@csrf_exempt
def krafileInput(request):
    request_files = request.FILES.getlist(
        'image_uploads') if 'image_uploads' in request.FILES else None

    if request_files:
        # save attached file
        for request_file in request_files:
            # create a new instance of FileSystemStorage
            fs = FileSystemStorage()

            fname = request_file.name

            if fname[-4:] == 'xlsx':
                os.makedirs(KRAFILE_ROOT / 'xlsx', exist_ok=True)
                fs.location = KRAFILE_ROOT / 'xlsx'
            else:
                if fname[0:4] < '2018':
                    os.makedirs(KRAFILE_ROOT / '2022이전', exist_ok=True)
                    fs.location = KRAFILE_ROOT / '2022이전'
                else:
                    os.makedirs(KRAFILE_ROOT /
                                fname[0:4], exist_ok=True)
                    fs.location = KRAFILE_ROOT / fname[0:4]

            if fs.exists(fname):
                fs.delete(fname)

                try:
                    cursor = connection.cursor()

                    strSql = """
														DELETE FROM krafile
														WHERE fname = '""" + fname + """'
														; """

                    # print(strSql)

                    r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
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

            if fname[-4:] == 'xlsx':
                print(fname[-4:])

                fdate = fname[-19:-11]
                fcode = 'c1'

                file = fs.save(request_file.name, request_file)
                # shutil.copy(request_file, str(fs.location) + '/')
            else:

                fdate = fname[0:8]
                fcode = fname[-12:-10]
                fcontent = request_file.read().decode(
                    'euc-kr', errors='strict')       # 한글 decode

                letter = open(str(fs.location) + '/' +
                              fname, 'w')           # 새 파일 열기
                letter.write(fcontent)
                letter.close()                                    # 닫기

            try:
                cursor = connection.cursor()

                strSql = """
												INSERT INTO krafile
												( fname, fpath, rdate, fcode, fstatus, in_date )
												VALUES
												( '""" + fname + """',
												'""" + str(fs.location) + '/' + fname + """',
												'""" + fdate + """',
												'""" + fcode + """',
												'I',
												""" + 'NOW()' + """
												) ; """

                # print(strSql)
                r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
                result = cursor.fetchone()
                # result = cursor.fetchall()

                connection.commit()
                connection.close()

            except:
                connection.rollback()
                print("Failed inserting in krafile")

    context = {'request_files': request_files}

    return render(request, 'base/krafile_input.html', context)


@csrf_exempt
def BreakingNewsInput(request):

    rcity = request.GET.get('rcity') if request.GET.get(
        'rcity') != None else ''
    rdate = request.GET.get('rdate') if request.GET.get(
        'rdate') != None else ''
    title = request.GET.get('title') if request.GET.get(
        'title') != None else ''
    news = request.GET.get('news') if request.GET.get(
        'news') != None else ''

    try:
        cursor = connection.cursor()

        strSql = """
								DELETE FROM breakingnews
								WHERE rcity = '""" + rcity + """' and rdate = '""" + rdate + """' and title = '""" + title + """'
								; """

        # print(strSql)

        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchone()
        # result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed deleting in Breaking News")

    try:
        cursor = connection.cursor()

        strSql = """
								INSERT INTO breakingnews
								( rcity, rdate, title, news, in_date )
								VALUES
								( '""" + rcity + """',
								'""" + rdate + """',
								'""" + title + """',
								'""" + news + """',
								""" + 'NOW()' + """
								) ; """

        # print(strSql)
        r_cnt = cursor.execute(strSql)         # 결과값 개수 반환
        result = cursor.fetchone()
        # result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed inserting in Breaking News")

    context = {'rdate': rdate}

    return render(request, 'base/breakingnews_input.html', context)


def pyscriptTest(request):
    pass

    return render(request, 'base/pyscript_test.html')
