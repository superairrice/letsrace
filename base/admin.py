from django.contrib import admin


# Register your models here.

from .models import Exp010, Exp011, Exp012, JockeyW, RaceResult, Rec010, RecordS, Room, Topic, Message, User, Racing, JtRate

admin.site.register(User)
admin.site.register(Room)
admin.site.register(Topic)
admin.site.register(Message)

admin.site.register(Rec010)

admin.site.register(Exp010)
admin.site.register(Exp011)
admin.site.register(Exp012)
admin.site.register(Racing)

admin.site.register(RecordS)
admin.site.register(JockeyW)
admin.site.register(JtRate)
admin.site.register(RaceResult)
