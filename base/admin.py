from django.contrib import admin


# Register your models here.

from .models import (
    Exp010,
    Exp011,
    Exp012,
    JockeyW,
    JtRate,
    Message,
    RaceComment,
    RaceCommentArchive,
    RaceResult,
    Racing,
    Rec010,
    RecordS,
    Room,
    Topic,
    User,
)

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


@admin.register(RaceComment)
class RaceCommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "rcity",
        "rdate",
        "rno",
        "nickname",
        "like_count",
        "report_count",
        "created",
    )
    list_filter = ("rcity", "rdate", "created")
    search_fields = ("nickname", "content")
    ordering = ("-created",)


@admin.register(RaceCommentArchive)
class RaceCommentArchiveAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_comment_id",
        "rcity",
        "rdate",
        "rno",
        "nickname",
        "archived_reason",
        "archived_by_authenticated",
        "archived_at",
    )
    list_filter = ("rcity", "rdate", "archived_reason", "archived_by_authenticated", "archived_at")
    search_fields = ("nickname", "content", "original_comment_id")
    ordering = ("-archived_at",)
