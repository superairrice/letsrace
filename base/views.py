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

from base.mysqls import get_award, get_award_race, get_paternal, get_paternal_dist, get_pedigree, get_race, get_training, get_weeks
# from django.contrib.auth.forms import UserCreationForm
from .models import Award, Exp010, Exp011, Exp012, JockeyW, JtRate, RaceResult, Racing, Rec010, RecordS, Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm


from datetime import datetime, date

from django_pivot import pivot

from django.db import connection

from django.shortcuts import get_object_or_404

# from django_pivot.histogram import histogram

from django.http.request import QueryDict


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


def leftPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )
    return render(request, 'base/left.html', {'racings': racings})


def rightPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) |
        Q(rdate__icontains=q) |
        Q(rday__icontains=q)
    )

    r_results = RaceResult.objects.all().order_by('rdate', 'rcity', 'rno')
    return render(request, 'base/right.html', {'r_results': r_results})


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
                                    rno=first_race.rno).order_by('rank')[0:2]

    horse = Exp011.objects.filter(rcity=first_race.rcity,
                                  rdate=first_race.rdate,
                                  rno=first_race.rno,
                                  rank=1).get()

    # print(datetime.today().weekday())
    # print(exp011s.count)

    h_records = RecordS.objects.filter(horse=horse.horse).order_by('-rdate')

    # 금주 경주예상 종합

    rdate = Racing.objects.values('rdate').distinct()

    i_rdate = rdate[0]['rdate']
    # awards = get_award_race('서울', i_rdate, 3, i_awardee='jockey')
    weeks = get_weeks(i_rdate, i_awardee='jockey')
    race = get_race(i_rdate, i_awardee='jockey')

    r_results = RaceResult.objects.all().order_by('rdate', 'rcity', 'rno')
    # .filter( rdate__in=rdate.values_list('rdate', flat=True))
    # print(r_results)

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
               'weeks': weeks,
               'race': race,
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

    hr_pedigree = Exp012.objects.filter(
        rdate__lt=rdate, horse__in=exp011s.values("horse")).order_by('-rdate')

    print(hr_records.query)

    training = get_training(rcity, rdate, rno)
    race = get_race(rdate, i_awardee='jockey')

    compare_r = exp011s.aggregate(Min('i_s1f'), Min('i_g1f'), Min('i_g2f'), Min('i_g3f'), Max(
        'handycap'), Max('rating'), Max('r_pop'), Max('j_per'), Max('t_per'), Max('jt_per'))

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    pedigree = get_pedigree(rcity, rdate, rno)
    paternal = get_paternal(rcity, rdate, rno, r_condition.distance)
    paternal_dist = get_paternal_dist(rcity, rdate, rno)

    print(paternal_dist)

    awards_j = get_award_race(rcity, rdate, rno, i_awardee='jockey')

    context = {'exp011s': exp011s, 'r_condition': r_condition,
               'complex5': complex5,
               'hr_records': hr_records, 'compare_r': compare_r, 'alloc': alloc,
               'awards_j': awards_j,
               'race': race,
               'pedigree': pedigree,
               'paternal': paternal,
               'paternal_dist': paternal_dist,
               'hr_pedigree': hr_pedigree,

               #    'horse': horse,
               'training': training,

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


def update_popularity(request, rcity, rdate, rno):

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

    compare_r = records.aggregate(Min('i_s1f'), Min('i_g1f'), Min('i_g2f'), Min('i_g3f'), Max(
        'handycap'), Max('rating'))


    context = {'records': records, 'r_condition': r_condition,
               'hr_records': hr_records, 'compare_r': compare_r, 'hname': hname

							}

    return render(request, 'base/race_result.html', context)
