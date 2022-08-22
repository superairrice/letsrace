from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from pymysql import ROWID
# from django.contrib.auth.forms import UserCreationForm
from .models import Exp010, Exp011, Racing, RecordS, Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm

from datetime import datetime, date
# Create your views here.

# rooms = [
#     {'id': 1, 'name': 'Lets learn python!'},
#     {'id': 2, 'name': 'Design with me'},
#     {'id': 3, 'name': 'Frontend developers'},
# ]

# def home(request):
#     return HttpResponse('Home page')  # settings.py에 TEMPLATES 경로 설정 후 http 삭제 가능 2022.05.10
# def room(request):
#     return HttpResponse('Room')
# def home(request):
#     # return render(request, 'home.html')
#     # return render(request, 'home.html', {'rooms': rooms})
#     context = {'rooms': rooms}
#     # return render(request, 'home.html', context)
#     # base/templates/base/home.html이 있지만 Django 에서는 이 방법으로 호출함
#     return render(request, 'base/home.html', context)


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


# def home(request):
#     # rooms = Room.objects.all()
#     q = request.GET.get('q') if request.GET.get('q') != None else ''
#     # rooms = Room.objects.filter(topic__name=q)
#     rooms = Room.objects.filter(
#         Q(topic__name__icontains=q) |
#         Q(name__icontains=q) |
#         Q(description__icontains=q)
#     )

#     topics = Exp010.objects.all()[0:5]
#     room_count = rooms.count()
#     room_messages = Message.objects.filter(Q(room__name__icontains=q))

#     context = {'rooms': rooms, 'topics': topics,
#                'room_count': room_count, 'room_messages': room_messages}
#     return render(request, 'base/home.html', context)

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

    # rdates = Racing.objects.distinct().values_list('rdate')
    rdays = Racing.objects.distinct().values('rday')

    first_race = racings[0]         # 첫번째 경주 조건

    exp011s = Exp011.objects.filter(rcity=first_race.rcity,
                                    rdate=first_race.rdate,
                                    rno=first_race.rno).order_by('rank')

    horse = Exp011.objects.filter(rcity=first_race.rcity,
                                  rdate=first_race.rdate,
                                  rno=first_race.rno,
                                  rank=1).get()
    print(horse.horse)

    print(datetime.today().weekday())

    h_records = RecordS.objects.filter(horse=horse.horse).order_by('-rdate')

    context = {'rooms': rooms,
               'racings': racings,
               'room_count': room_count,
               'room_messages': room_messages,
               'rdays': rdays,
               'first_race': first_race,
               'exp011s': exp011s,
               'horse': horse,
               'h_records': h_records}

    return render(request, 'base/home.html', context)


# def room(request, pk):
#     room = None
#     for i in rooms:
#         if i['id'] == int(pk):
#             room = i

#     context = {'room': room}
#     return render(request, 'base/room.html', context)

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

        # if request.method == 'POST':
        #     form = RoomForm(request.POST, instance=room)
        #     if form.is_valid():
        #         form.save()
        #         return redirect('home')

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


# def exp010Page(request):
#     q = request.GET.get('q') if request.GET.get('q') != None else ''
#     exp010s = Exp010.objects.filter(rdate__icontains=q)
#     return render(request, 'base/race.html', {'exp010s': exp010s})


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
