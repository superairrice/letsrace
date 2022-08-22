from ast import Pass
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Min, Max
# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from pymysql import ROWID
# from django.contrib.auth.forms import UserCreationForm
from .models import Award, Exp010, Exp011, JockeyW, JtRate, RaceResult, Racing, Rec010, RecordS, Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm

from datetime import datetime, date

from django_pivot import pivot

from django.db import connection

from django.shortcuts import get_object_or_404

# from django_pivot.histogram import histogram


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
            messages.error(request, 'Username or password does not exist')

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
            messages.error(request, 'An error occurred during registration')

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

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
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

    # print(room_count)

    first_race = racings[0]         # 첫번째 경주 조건

    exp011s = Exp011.objects.filter(rcity=first_race.rcity,
                                    rdate=first_race.rdate,
                                    rno=first_race.rno).order_by('rank')

    horse = Exp011.objects.filter(rcity=first_race.rcity,
                                  rdate=first_race.rdate,
                                  rno=first_race.rno,
                                  rank=1).get()

    print(datetime.today().weekday())
    # print(seoul)

    h_records = RecordS.objects.filter(horse=horse.horse).order_by('-rdate')

    # 금주 경주예상 종합

    rdate = Racing.objects.values('rdate').distinct()

    i_rdate = rdate[0]['rdate']
    awards = get_award_race('서울', i_rdate, 3, i_awardee='jockey')

    r_results = RaceResult.objects.all().order_by('rdate', 'rcity', 'rno')
    # .filter( rdate__in=rdate.values_list('rdate', flat=True))

    allocs = Rec010.objects.filter(rdate__in=rdate.values_list(
        'rdate', flat=True)).order_by('rdate', 'rcity', 'rno')

    context = {'rooms': rooms,
            'racings': racings,
            'room_count': room_count,
            'room_messages': room_messages,
            'first_race': first_race,
            'exp011s': exp011s,
            'horse': horse,
            'rdate': rdate,
            'r_results': r_results,
            'allocs': allocs,
            'awards': awards,
            'h_records': h_records}

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


def leftPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )
    return render(request, 'base/left_component.html', {'racings': racings})


def prediction_race(request, rcity, rdate, rno, hname, awardee):

    exp011s = Exp011.objects.filter(rcity=rcity,
                                    rdate=rdate,
                                    rno=rno).order_by('rank', 'gate')
    print(exp011s.count())

    if exp011s:
        pass
    else:
        return render(request, 'base/home.html')

    if hname == '0':
        horse = Exp011.objects.filter(rcity=rcity,
                                      rdate=rdate,
                                      rno=rno,
                                      rank=1).get()
    else:
        horse = Exp011.objects.filter(rcity=rcity,
                                      rdate=rdate,
                                      rno=rno,
                                      horse=hname).get()

    r_condition = Exp010.objects.filter(
        rcity=rcity, rdate=rdate, rno=rno).get()

    h_records = RecordS.objects.filter(
        rdate__lt=rdate, horse=horse.horse).order_by('-rdate')

    compare_r = exp011s.aggregate(Min('i_s1f'), Min(
        'i_g1f'), Min('i_g2f'), Min('i_g3f'), Max('handycap'), Max('rating'))

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None


    # # awards = get_award_race(i_rcity=rcity, i_rdate=rdate, i_rno=rno, i_awardee=awardee)
    # print(alloc.query)

    if awardee == '0':
        awards_j = None
        awards_t = None
        awards_h = None
    else:
        awards_j = get_award_race(rcity, rdate, rno, i_awardee='jockey')
        awards_t = get_award_race(rcity, rdate, rno, i_awardee='trainer')
        awards_h = get_award_race(rcity, rdate, rno, i_awardee='host')

    context = {'exp011s': exp011s, 'r_condition': r_condition, 'h_records': h_records, 'compare_r': compare_r, 'alloc': alloc,
               'awards_j': awards_j,
               'awards_t': awards_t,
               'awards_h': awards_h,
               'horse': horse}

    return render(request, 'base/prediction_race.html', context)


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

    print(strSql)

    return awards


def get_award_race(i_rcity, i_rdate, i_rno, i_awardee):

    try:
        cursor = connection.cursor()

        strSql = """ select ( select min(gate) from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """ and """ + i_awardee + """ = a.""" + i_awardee + """) gate,
                            """ + i_awardee + """, count(0) rcnt, (select max(rcity) from """ + i_awardee + """  where a.""" + i_awardee + """ = """ + i_awardee + """ ) rcity,
                            sum( if( rmonth = substr( '""" + i_rdate + """', 1, 6), award, 0 )) rmonth1,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -1 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth2,
                            sum( if( rmonth = substr( date_format( DATE_ADD( '""" + i_rdate + """', INTERVAL -2 MONTH) , '%Y%m%d'), 1, 6), award, 0)) rmonth3
                    from award a
                    where rmonth between substr(date_format(DATE_ADD('""" + i_rdate + """', INTERVAL - 2 MONTH), '%Y%m%d'), 1, 6) and substr('""" + i_rdate + """', 1, 6)
                    and """ + i_awardee + """ in ( select """ + i_awardee + """ from exp011 where rdate = '""" + i_rdate + """' and rcity = '""" + i_rcity + """' and rno = """ + str(i_rno) + """)
                    group by """ + i_awardee + """
                    order by gate
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
