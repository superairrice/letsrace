# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AccountEmailaddress(models.Model):
    email = models.CharField(unique=True, max_length=254)
    verified = models.IntegerField()
    primary = models.IntegerField()
    user = models.ForeignKey('BaseUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailaddress'


class AccountEmailconfirmation(models.Model):
    created = models.DateTimeField()
    sent = models.DateTimeField(blank=True, null=True)
    key = models.CharField(unique=True, max_length=64)
    email_address = models.ForeignKey(AccountEmailaddress, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailconfirmation'


class AdvDistance(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    grade = models.CharField(max_length=10)
    dist1 = models.IntegerField()
    dist2 = models.IntegerField()
    i_100m1 = models.DecimalField(max_digits=16, decimal_places=8, blank=True, null=True)
    i_100m2 = models.DecimalField(max_digits=16, decimal_places=8, blank=True, null=True)
    adv_dist = models.DecimalField(max_digits=16, decimal_places=8, blank=True, null=True)
    rcnt1 = models.IntegerField(blank=True, null=True)
    rcnt2 = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'adv_distance'
        unique_together = (('rcity', 'grade', 'dist1', 'dist2'),)


class AdvFurlong(models.Model):
    rcity = models.CharField(max_length=4)
    grade = models.CharField(max_length=10)
    dist1 = models.IntegerField()
    dist2 = models.IntegerField()
    i_s1f1 = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    i_s1f2 = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    adv_s1f = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    i_g1f1 = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    i_g1f2 = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    adv_g1f = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    i_g2f1 = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    i_g2f2 = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    adv_g2f = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    i_g3f1 = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    i_g3f2 = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    adv_g3f = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    rcnt1 = models.IntegerField(blank=True, null=True)
    rcnt2 = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'adv_furlong'


class AdvJockey(models.Model):
    jockey = models.CharField(primary_key=True, max_length=10)
    distance = models.IntegerField()
    gate = models.IntegerField()
    avg = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_record = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_gate = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    rcnt = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    joc_rate = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_jockey = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'adv_jockey'
        unique_together = (('jockey', 'distance', 'gate'),)


class AdvTrack(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    grade = models.CharField(max_length=10)
    distance = models.IntegerField()
    record = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    avg_rec = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_flag = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_track = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'adv_track'
        unique_together = (('rcity', 'rdate', 'rno', 'grade', 'distance'),)


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class Award(models.Model):
    rmonth = models.CharField(primary_key=True, max_length=6, db_collation='euckr_korean_ci')
    jockey = models.CharField(max_length=10, db_collation='euckr_korean_ci')
    trainer = models.CharField(max_length=10, db_collation='euckr_korean_ci')
    host = models.CharField(max_length=20, db_collation='euckr_korean_ci')
    r1_cnt = models.IntegerField(blank=True, null=True)
    r2_cnt = models.IntegerField(blank=True, null=True)
    r3_cnt = models.IntegerField(blank=True, null=True)
    r4_cnt = models.IntegerField(blank=True, null=True)
    r5_cnt = models.IntegerField(blank=True, null=True)
    r_cnt = models.IntegerField(blank=True, null=True)
    award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'award'
        unique_together = (('rmonth', 'jockey', 'trainer', 'host'),)


class BaseMessage(models.Model):
    id = models.BigAutoField(primary_key=True)
    body = models.TextField()
    updated = models.DateTimeField()
    created = models.DateTimeField()
    room = models.ForeignKey('BaseRoom', models.DO_NOTHING)
    user = models.ForeignKey('BaseUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_message'


class BaseRoom(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    updated = models.DateTimeField()
    created = models.DateTimeField()
    host = models.ForeignKey('BaseUser', models.DO_NOTHING, blank=True, null=True)
    topic = models.ForeignKey('BaseTopic', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'base_room'


class BaseRoomParticipants(models.Model):
    id = models.BigAutoField(primary_key=True)
    room = models.ForeignKey(BaseRoom, models.DO_NOTHING)
    user = models.ForeignKey('BaseUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_room_participants'
        unique_together = (('room', 'user'),)


class BaseTopic(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'base_topic'


class BaseUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(unique=True, max_length=254, blank=True, null=True)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()
    bio = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    avatar = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'base_user'


class BaseUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(BaseUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_user_groups'
        unique_together = (('user', 'group'),)


class BaseUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(BaseUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BaseVisitor(models.Model):
    id = models.BigAutoField(primary_key=True)
    ip_address = models.CharField(max_length=50)
    user_agent = models.CharField(max_length=500)
    referer = models.CharField(max_length=500)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'base_visitor'


class BaseVisitorcount(models.Model):
    id = models.BigAutoField(primary_key=True)
    date = models.DateField()
    count = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'base_visitorcount'


class BaseVisitorlog(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    date = models.DateField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'base_visitorlog'


class Breakingnews(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    title = models.CharField(max_length=12)
    news = models.CharField(max_length=2000, blank=True, null=True)
    in_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'breakingnews'
        unique_together = (('rcity', 'rdate', 'title'), ('rcity', 'rdate', 'title'),)


class CancelH(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=10)
    rno = models.IntegerField()
    gate = models.IntegerField()
    horse = models.CharField(max_length=18)
    reason = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cancel_h'
        unique_together = (('rcity', 'rdate', 'rno', 'gate', 'horse'),)


class CancelJ(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=10)
    rno = models.IntegerField()
    gate = models.IntegerField()
    horse = models.CharField(max_length=18)
    jockey_o = models.CharField(max_length=10, blank=True, null=True)
    jockey_n = models.CharField(max_length=10, blank=True, null=True)
    handycap = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    reason = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cancel_j'
        unique_together = (('rcity', 'rdate', 'rno', 'gate', 'horse'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(BaseUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class Exp010(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    rday = models.CharField(max_length=2, blank=True, null=True)
    rseq = models.IntegerField(blank=True, null=True)
    distance = models.IntegerField(blank=True, null=True)
    rcount = models.CharField(max_length=2, blank=True, null=True)
    grade = models.CharField(max_length=10, blank=True, null=True)
    dividing = models.CharField(max_length=20, blank=True, null=True)
    rname = models.CharField(max_length=40, blank=True, null=True)
    rcon1 = models.CharField(max_length=20, blank=True, null=True)
    rcon2 = models.CharField(max_length=20, blank=True, null=True)
    rtime = models.CharField(max_length=5, blank=True, null=True)
    r1award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    r2award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    r3award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    r4award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    r5award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    sub1award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    sub2award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    sub3award = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    cflag = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exp010'
        unique_together = (('rcity', 'rdate', 'rno'), ('rcity', 'rdate', 'rno'),)


class Exp011(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    gate = models.IntegerField()
    horse = models.CharField(max_length=20, blank=True, null=True)
    birthplace = models.CharField(max_length=6, blank=True, null=True)
    h_sex = models.CharField(max_length=2, blank=True, null=True)
    h_age = models.IntegerField(blank=True, null=True)
    handycap = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    joc_adv = models.CharField(max_length=4, blank=True, null=True)
    jockey = models.CharField(max_length=10, blank=True, null=True)
    trainer = models.CharField(max_length=10, blank=True, null=True)
    host = models.CharField(max_length=20, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    prize_tot = models.FloatField(blank=True, null=True)
    prize_year = models.FloatField(blank=True, null=True)
    prize_half = models.FloatField(blank=True, null=True)
    tot_1st = models.IntegerField(blank=True, null=True)
    tot_2nd = models.IntegerField(blank=True, null=True)
    tot_3rd = models.IntegerField(blank=True, null=True)
    tot_race = models.IntegerField(blank=True, null=True)
    year_1st = models.IntegerField(blank=True, null=True)
    year_2nd = models.IntegerField(blank=True, null=True)
    year_3rd = models.IntegerField(blank=True, null=True)
    year_race = models.IntegerField(blank=True, null=True)
    recent3 = models.CharField(max_length=6, blank=True, null=True)
    recent5 = models.CharField(max_length=6, blank=True, null=True)
    fast_r = models.CharField(max_length=6, blank=True, null=True)
    slow_r = models.CharField(max_length=6, blank=True, null=True)
    avg_r = models.CharField(max_length=6, blank=True, null=True)
    convert_r = models.CharField(max_length=6, blank=True, null=True)
    rs1f = models.CharField(max_length=4, blank=True, null=True)
    r1c = models.CharField(max_length=6, blank=True, null=True)
    r2c = models.CharField(max_length=6, blank=True, null=True)
    r3c = models.CharField(max_length=6, blank=True, null=True)
    r4c = models.CharField(max_length=6, blank=True, null=True)
    rg3f = models.CharField(max_length=4, blank=True, null=True)
    rg2f = models.CharField(max_length=4, blank=True, null=True)
    rg1f = models.CharField(max_length=4, blank=True, null=True)
    complex = models.CharField(max_length=6, blank=True, null=True)
    cs1f = models.CharField(max_length=4, blank=True, null=True)
    cg3f = models.CharField(max_length=4, blank=True, null=True)
    cg2f = models.CharField(max_length=4, blank=True, null=True)
    cg1f = models.CharField(max_length=4, blank=True, null=True)
    rank = models.IntegerField(blank=True, null=True)
    i_g3f = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_s1f = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_g2f = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_g1f = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_complex = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_jockey = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_cycle = models.IntegerField(blank=True, null=True)
    i_prehandy = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    r_rank = models.IntegerField(blank=True, null=True)
    r_record = models.CharField(max_length=10, blank=True, null=True)
    ir_record = models.IntegerField(blank=True, null=True)
    remark = models.CharField(max_length=1000, blank=True, null=True)
    h_weight = models.CharField(max_length=10, blank=True, null=True)
    j_per = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    t_per = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    jt_per = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    jt_cnt = models.IntegerField(blank=True, null=True)
    jt_1st = models.IntegerField(blank=True, null=True)
    jt_2nd = models.IntegerField(blank=True, null=True)
    jt_3rd = models.IntegerField(blank=True, null=True)
    r_pop = models.IntegerField(blank=True, null=True)
    jockey_old = models.CharField(max_length=10, blank=True, null=True)
    handycap_old = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    reason = models.CharField(max_length=45, blank=True, null=True)
    complex5 = models.CharField(max_length=6, blank=True, null=True)
    gap = models.IntegerField(blank=True, null=True)
    gap_back = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exp011'
        unique_together = (('rcity', 'rdate', 'rno', 'gate'), ('rcity', 'rdate', 'rno', 'gate'),)


class Exp012(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    gate = models.IntegerField()
    horse = models.CharField(max_length=20, blank=True, null=True)
    gear1 = models.CharField(max_length=20, blank=True, null=True)
    gear2 = models.CharField(max_length=20, blank=True, null=True)
    blood1 = models.CharField(max_length=20, blank=True, null=True)
    blood2 = models.CharField(max_length=20, blank=True, null=True)
    treat1 = models.CharField(max_length=100, blank=True, null=True)
    treat2 = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exp012'
        unique_together = (('rcity', 'rdate', 'rno', 'gate'),)


class Exp013(models.Model):
    rcity = models.CharField(max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    gate = models.IntegerField()
    horse = models.CharField(max_length=20, blank=True, null=True)
    v_rank = models.IntegerField(blank=True, null=True)
    r_rank = models.IntegerField(blank=True, null=True)
    v_record = models.CharField(max_length=10, blank=True, null=True)
    r_record = models.CharField(max_length=10, blank=True, null=True)
    distance = models.IntegerField(blank=True, null=True)
    iv_record = models.IntegerField(blank=True, null=True)
    ir_record = models.IntegerField(blank=True, null=True)
    remark = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exp013'


class Hname(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    h_before = models.CharField(max_length=18)
    h_after = models.CharField(max_length=18)
    host = models.CharField(max_length=20, blank=True, null=True)
    cdate = models.CharField(max_length=10, blank=True, null=True)
    reason = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'hname'
        unique_together = (('rcity', 'h_before', 'h_after'),)


class Horse(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    horse = models.CharField(max_length=16)
    birth = models.CharField(max_length=10)
    birthplace = models.CharField(max_length=4, blank=True, null=True)
    sex = models.CharField(max_length=2, blank=True, null=True)
    age = models.CharField(max_length=2, blank=True, null=True)
    grade = models.CharField(max_length=4, blank=True, null=True)
    team = models.CharField(max_length=3, blank=True, null=True)
    trainer = models.CharField(max_length=6, blank=True, null=True)
    host = models.CharField(max_length=20, blank=True, null=True)
    paternal = models.CharField(max_length=45, blank=True, null=True)
    maternal = models.CharField(max_length=45, blank=True, null=True)
    tot_race = models.IntegerField(blank=True, null=True)
    tot_1st = models.IntegerField(blank=True, null=True)
    tot_2nd = models.IntegerField(blank=True, null=True)
    tot_3rd = models.IntegerField(blank=True, null=True)
    year_race = models.IntegerField(blank=True, null=True)
    year_1st = models.IntegerField(blank=True, null=True)
    year_2nd = models.IntegerField()
    year_3rd = models.IntegerField(blank=True, null=True)
    tot_prize = models.FloatField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'horse'
        unique_together = (('rcity', 'horse', 'birth'),)


class Host(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    host = models.CharField(max_length=40)
    h_total = models.IntegerField()
    h_cancel = models.IntegerField(blank=True, null=True)
    h_current = models.IntegerField(blank=True, null=True)
    debut = models.CharField(max_length=10, blank=True, null=True)
    year_race = models.CharField(max_length=20, blank=True, null=True)
    year_prize = models.FloatField(blank=True, null=True)
    tot_race = models.CharField(max_length=20, blank=True, null=True)
    tot_prize = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'host'
        unique_together = (('rcity', 'host', 'h_total'),)


class Jockey(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    jockey = models.CharField(max_length=6)
    birth = models.CharField(max_length=10)
    team = models.CharField(max_length=3, blank=True, null=True)
    age = models.CharField(max_length=2, blank=True, null=True)
    debut = models.CharField(max_length=10, blank=True, null=True)
    load_in = models.CharField(max_length=2, blank=True, null=True)
    load_out = models.CharField(max_length=2, blank=True, null=True)
    tot_race = models.IntegerField(blank=True, null=True)
    tot_1st = models.IntegerField(blank=True, null=True)
    tot_2nd = models.IntegerField(blank=True, null=True)
    tot_3rd = models.IntegerField(blank=True, null=True)
    year_race = models.IntegerField(blank=True, null=True)
    year_1st = models.IntegerField(blank=True, null=True)
    year_2nd = models.IntegerField(blank=True, null=True)
    year_3rd = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'jockey'
        unique_together = (('rcity', 'jockey', 'birth'),)


class JockeyW(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    wdate = models.CharField(max_length=8)
    jockey = models.CharField(max_length=6)
    birth = models.CharField(max_length=10)
    team = models.CharField(max_length=3, blank=True, null=True)
    age = models.CharField(max_length=2, blank=True, null=True)
    debut = models.CharField(max_length=10, blank=True, null=True)
    load_in = models.CharField(max_length=2, blank=True, null=True)
    load_out = models.CharField(max_length=2, blank=True, null=True)
    tot_race = models.IntegerField(blank=True, null=True)
    tot_1st = models.IntegerField(blank=True, null=True)
    tot_2nd = models.IntegerField(blank=True, null=True)
    tot_3rd = models.IntegerField(blank=True, null=True)
    year_race = models.IntegerField(blank=True, null=True)
    year_1st = models.IntegerField(blank=True, null=True)
    year_2nd = models.IntegerField(blank=True, null=True)
    year_3rd = models.IntegerField(blank=True, null=True)
    year_per = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    year_3per = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'jockey_w'
        unique_together = (('rcity', 'wdate', 'jockey', 'birth'),)


class Kradata(models.Model):
    fname = models.CharField(primary_key=True, max_length=40)
    fcontents = models.TextField(blank=True, null=True)
    rdate = models.CharField(max_length=8, blank=True, null=True)
    fcode = models.CharField(max_length=2, blank=True, null=True)
    fstatus = models.CharField(max_length=1, blank=True, null=True)
    in_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kradata'


class Krafile(models.Model):
    fname = models.CharField(primary_key=True, max_length=40)
    fpath = models.CharField(max_length=200, blank=True, null=True)
    rdate = models.CharField(max_length=8, blank=True, null=True)
    fcode = models.CharField(max_length=2, blank=True, null=True)
    fstatus = models.CharField(max_length=1, blank=True, null=True)
    in_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'krafile'


class Maternal(models.Model):
    maternal = models.CharField(primary_key=True, max_length=45, db_collation='euckr_korean_ci')
    distance = models.IntegerField()
    r1 = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    r2 = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    r3 = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    rtot = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'maternal'
        unique_together = (('maternal', 'distance'),)


class PRecord(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4, db_collation='euckr_korean_ci')
    rdate = models.CharField(max_length=8, db_collation='euckr_korean_ci')
    rno = models.IntegerField()
    rday = models.CharField(max_length=2, db_collation='euckr_korean_ci', blank=True, null=True)
    rseq = models.IntegerField(blank=True, null=True)
    distance = models.IntegerField(blank=True, null=True)
    grade = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    dividing = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rname = models.CharField(max_length=40, db_collation='euckr_korean_ci', blank=True, null=True)
    rcon1 = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rcon2 = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    weather = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rstate = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rmoisture = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rtime = models.CharField(max_length=5, db_collation='euckr_korean_ci', blank=True, null=True)
    race_speed = models.CharField(max_length=2, db_collation='euckr_korean_ci', blank=True, null=True)
    gate = models.IntegerField()
    rank = models.IntegerField(blank=True, null=True)
    horse = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    birthplace = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    h_sex = models.CharField(max_length=2, db_collation='euckr_korean_ci', blank=True, null=True)
    h_age = models.IntegerField(blank=True, null=True)
    handycap = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    jockey = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    joc_adv = models.CharField(max_length=4, db_collation='euckr_korean_ci', blank=True, null=True)
    trainer = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    host = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    h_weight = models.IntegerField(blank=True, null=True)
    w_change = models.CharField(max_length=4, db_collation='euckr_korean_ci', blank=True, null=True)
    record = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    gap = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    corners = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    rs1f = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r1c = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r2c = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r3c = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r4c = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg3f = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg2f = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg1f = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    alloc1r = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    alloc3r = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    judge = models.CharField(max_length=4, db_collation='euckr_korean_ci', blank=True, null=True)
    judge_reason = models.CharField(max_length=30, db_collation='euckr_korean_ci', blank=True, null=True)
    audit_reason = models.CharField(max_length=30, db_collation='euckr_korean_ci', blank=True, null=True)
    i_s1f = models.IntegerField(blank=True, null=True)
    i_r1c = models.IntegerField(blank=True, null=True)
    i_r2c = models.IntegerField(blank=True, null=True)
    i_r3c = models.IntegerField(blank=True, null=True)
    i_r4c = models.IntegerField(blank=True, null=True)
    i_g3f = models.IntegerField(blank=True, null=True)
    i_g2f = models.IntegerField(blank=True, null=True)
    i_g1f = models.IntegerField(blank=True, null=True)
    i_record = models.IntegerField(blank=True, null=True)
    jockey_w = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    burden_w = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_jockey = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_track = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_convert = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    r_start = models.CharField(max_length=5, db_collation='euckr_korean_ci', blank=True, null=True)
    r_corners = models.CharField(max_length=5, db_collation='euckr_korean_ci', blank=True, null=True)
    r_finish = models.CharField(max_length=5, db_collation='euckr_korean_ci', blank=True, null=True)
    r_wrapup = models.CharField(max_length=5, db_collation='euckr_korean_ci', blank=True, null=True)
    r_etc = models.CharField(max_length=400, db_collation='euckr_korean_ci', blank=True, null=True)
    r_flag = models.CharField(max_length=1, db_collation='euckr_korean_ci', blank=True, null=True)
    p_rank = models.IntegerField(blank=True, null=True)
    p_record = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    pop_rank = models.IntegerField(blank=True, null=True)
    gap_b = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    gear1 = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    gear2 = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    treat1 = models.CharField(max_length=100, db_collation='euckr_korean_ci', blank=True, null=True)
    treat2 = models.CharField(max_length=100, db_collation='euckr_korean_ci', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_record'
        unique_together = (('rcity', 'rdate', 'rno', 'gate'),)


class Paternal(models.Model):
    paternal = models.CharField(primary_key=True, max_length=45, db_collation='euckr_korean_ci')
    distance = models.IntegerField()
    r1 = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    r2 = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    r3 = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    rtot = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'paternal'
        unique_together = (('paternal', 'distance'),)


class Pbcatcol(models.Model):
    pbc_tnam = models.CharField(max_length=193)
    pbc_tid = models.IntegerField(blank=True, null=True)
    pbc_ownr = models.CharField(max_length=193)
    pbc_cnam = models.CharField(max_length=193)
    pbc_cid = models.SmallIntegerField(blank=True, null=True)
    pbc_labl = models.CharField(max_length=254, blank=True, null=True)
    pbc_lpos = models.SmallIntegerField(blank=True, null=True)
    pbc_hdr = models.CharField(max_length=254, blank=True, null=True)
    pbc_hpos = models.SmallIntegerField(blank=True, null=True)
    pbc_jtfy = models.SmallIntegerField(blank=True, null=True)
    pbc_mask = models.CharField(max_length=31, blank=True, null=True)
    pbc_case = models.SmallIntegerField(blank=True, null=True)
    pbc_hght = models.SmallIntegerField(blank=True, null=True)
    pbc_wdth = models.SmallIntegerField(blank=True, null=True)
    pbc_ptrn = models.CharField(max_length=31, blank=True, null=True)
    pbc_bmap = models.CharField(max_length=1, blank=True, null=True)
    pbc_init = models.CharField(max_length=254, blank=True, null=True)
    pbc_cmnt = models.CharField(max_length=254, blank=True, null=True)
    pbc_edit = models.CharField(max_length=31, blank=True, null=True)
    pbc_tag = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pbcatcol'


class Pbcatedt(models.Model):
    pbe_name = models.CharField(max_length=30)
    pbe_edit = models.CharField(max_length=254, blank=True, null=True)
    pbe_type = models.SmallIntegerField(blank=True, null=True)
    pbe_cntr = models.IntegerField(blank=True, null=True)
    pbe_seqn = models.SmallIntegerField()
    pbe_flag = models.IntegerField(blank=True, null=True)
    pbe_work = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pbcatedt'


class Pbcatfmt(models.Model):
    pbf_name = models.CharField(max_length=30)
    pbf_frmt = models.CharField(max_length=254, blank=True, null=True)
    pbf_type = models.SmallIntegerField(blank=True, null=True)
    pbf_cntr = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pbcatfmt'


class Pbcattbl(models.Model):
    pbt_tnam = models.CharField(max_length=193)
    pbt_tid = models.IntegerField(blank=True, null=True)
    pbt_ownr = models.CharField(max_length=193)
    pbd_fhgt = models.SmallIntegerField(blank=True, null=True)
    pbd_fwgt = models.SmallIntegerField(blank=True, null=True)
    pbd_fitl = models.CharField(max_length=1, blank=True, null=True)
    pbd_funl = models.CharField(max_length=1, blank=True, null=True)
    pbd_fchr = models.SmallIntegerField(blank=True, null=True)
    pbd_fptc = models.SmallIntegerField(blank=True, null=True)
    pbd_ffce = models.CharField(max_length=18, blank=True, null=True)
    pbh_fhgt = models.SmallIntegerField(blank=True, null=True)
    pbh_fwgt = models.SmallIntegerField(blank=True, null=True)
    pbh_fitl = models.CharField(max_length=1, blank=True, null=True)
    pbh_funl = models.CharField(max_length=1, blank=True, null=True)
    pbh_fchr = models.SmallIntegerField(blank=True, null=True)
    pbh_fptc = models.SmallIntegerField(blank=True, null=True)
    pbh_ffce = models.CharField(max_length=18, blank=True, null=True)
    pbl_fhgt = models.SmallIntegerField(blank=True, null=True)
    pbl_fwgt = models.SmallIntegerField(blank=True, null=True)
    pbl_fitl = models.CharField(max_length=1, blank=True, null=True)
    pbl_funl = models.CharField(max_length=1, blank=True, null=True)
    pbl_fchr = models.SmallIntegerField(blank=True, null=True)
    pbl_fptc = models.SmallIntegerField(blank=True, null=True)
    pbl_ffce = models.CharField(max_length=18, blank=True, null=True)
    pbt_cmnt = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pbcattbl'


class Pbcatvld(models.Model):
    pbv_name = models.CharField(max_length=30)
    pbv_vald = models.CharField(max_length=254, blank=True, null=True)
    pbv_type = models.SmallIntegerField(blank=True, null=True)
    pbv_cntr = models.IntegerField(blank=True, null=True)
    pbv_msg = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pbcatvld'


class RaceCd(models.Model):
    cd_type = models.CharField(primary_key=True, max_length=2)
    nm_type = models.CharField(max_length=45, blank=True, null=True)
    r_code = models.CharField(max_length=5)
    r_name = models.CharField(max_length=450, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'race_cd'
        unique_together = (('cd_type', 'r_code'),)


class Rboard(models.Model):
    username = models.CharField(primary_key=True, max_length=150)
    board = models.CharField(max_length=20)
    rcity = models.CharField(max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    memo = models.CharField(max_length=2000, blank=True, null=True)
    rcnt = models.IntegerField(blank=True, null=True)
    scnt = models.IntegerField(blank=True, null=True)
    updated = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rboard'
        unique_together = (('username', 'board', 'rcity', 'rdate', 'rno'),)


class Rec010(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    rday = models.CharField(max_length=2, blank=True, null=True)
    rseq = models.IntegerField(blank=True, null=True)
    distance = models.IntegerField(blank=True, null=True)
    grade = models.CharField(max_length=10, blank=True, null=True)
    dividing = models.CharField(max_length=10, blank=True, null=True)
    rname = models.CharField(max_length=40, blank=True, null=True)
    rcon1 = models.CharField(max_length=10, blank=True, null=True)
    rcon2 = models.CharField(max_length=20, blank=True, null=True)
    weather = models.CharField(max_length=10, blank=True, null=True)
    rstate = models.CharField(max_length=10, blank=True, null=True)
    rmoisture = models.CharField(max_length=10, blank=True, null=True)
    rtime = models.CharField(max_length=5, blank=True, null=True)
    r1award = models.CharField(max_length=8, blank=True, null=True)
    r2award = models.CharField(max_length=8, blank=True, null=True)
    r3award = models.CharField(max_length=8, blank=True, null=True)
    r4award = models.CharField(max_length=8, blank=True, null=True)
    r5award = models.CharField(max_length=8, blank=True, null=True)
    sub1award = models.CharField(max_length=8, blank=True, null=True)
    sub2award = models.CharField(max_length=8, blank=True, null=True)
    sub3award = models.CharField(max_length=8, blank=True, null=True)
    sale1 = models.CharField(max_length=15, blank=True, null=True)
    sale2 = models.CharField(max_length=15, blank=True, null=True)
    sale3 = models.CharField(max_length=15, blank=True, null=True)
    sale4 = models.CharField(max_length=15, blank=True, null=True)
    sale5 = models.CharField(max_length=15, blank=True, null=True)
    sale6 = models.CharField(max_length=15, blank=True, null=True)
    sale7 = models.CharField(max_length=15, blank=True, null=True)
    sales = models.CharField(max_length=15, blank=True, null=True)
    r1alloc = models.CharField(max_length=40, blank=True, null=True)
    r3alloc = models.CharField(max_length=40, blank=True, null=True)
    r2alloc = models.CharField(max_length=40, blank=True, null=True)
    r12alloc = models.CharField(max_length=40, blank=True, null=True)
    r23alloc = models.CharField(max_length=40, blank=True, null=True)
    r333alloc = models.CharField(max_length=40, blank=True, null=True)
    r123alloc = models.CharField(max_length=40, blank=True, null=True)
    passage_s1f = models.CharField(max_length=100, blank=True, null=True)
    passage_g8f = models.CharField(max_length=100, blank=True, null=True)
    passage_1c = models.CharField(max_length=100, blank=True, null=True)
    passage_2c = models.CharField(max_length=100, blank=True, null=True)
    passage_3c = models.CharField(max_length=100, blank=True, null=True)
    passage_4c = models.CharField(max_length=100, blank=True, null=True)
    passage_g1f = models.CharField(max_length=100, blank=True, null=True)
    r3f = models.CharField(max_length=6, blank=True, null=True)
    r4f = models.CharField(max_length=6, blank=True, null=True)
    furlong = models.CharField(max_length=100, blank=True, null=True)
    passage = models.CharField(max_length=100, blank=True, null=True)
    passage_t = models.CharField(max_length=100, blank=True, null=True)
    race_speed = models.CharField(max_length=2, blank=True, null=True)
    r_judge = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rec010'
        unique_together = (('rcity', 'rdate', 'rno'),)


class Rec011(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    gate = models.IntegerField()
    rank = models.IntegerField(blank=True, null=True)
    horse = models.CharField(max_length=20, blank=True, null=True)
    birthplace = models.CharField(max_length=6, blank=True, null=True)
    h_sex = models.CharField(max_length=2, blank=True, null=True)
    h_age = models.IntegerField(blank=True, null=True)
    handycap = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    jockey = models.CharField(max_length=10, blank=True, null=True)
    joc_adv = models.CharField(max_length=4, blank=True, null=True)
    trainer = models.CharField(max_length=10, blank=True, null=True)
    host = models.CharField(max_length=20, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    h_weight = models.IntegerField(blank=True, null=True)
    w_change = models.CharField(max_length=4, blank=True, null=True)
    record = models.CharField(max_length=6, blank=True, null=True)
    gap = models.CharField(max_length=10, blank=True, null=True)
    corners = models.CharField(max_length=20, blank=True, null=True)
    rs1f = models.CharField(max_length=6, blank=True, null=True)
    r1c = models.CharField(max_length=6, blank=True, null=True)
    r2c = models.CharField(max_length=6, blank=True, null=True)
    r3c = models.CharField(max_length=6, blank=True, null=True)
    r4c = models.CharField(max_length=6, blank=True, null=True)
    rg3f = models.CharField(max_length=6, blank=True, null=True)
    rg2f = models.CharField(max_length=6, blank=True, null=True)
    rg1f = models.CharField(max_length=6, blank=True, null=True)
    alloc1r = models.CharField(max_length=10, blank=True, null=True)
    alloc3r = models.CharField(max_length=10, blank=True, null=True)
    judge = models.CharField(max_length=4, blank=True, null=True)
    judge_reason = models.CharField(max_length=30, blank=True, null=True)
    audit_reason = models.CharField(max_length=30, blank=True, null=True)
    i_s1f = models.IntegerField(blank=True, null=True)
    i_r1c = models.IntegerField(blank=True, null=True)
    i_r2c = models.IntegerField(blank=True, null=True)
    i_r3c = models.IntegerField(blank=True, null=True)
    i_r4c = models.IntegerField(blank=True, null=True)
    i_g3f = models.IntegerField(blank=True, null=True)
    i_g2f = models.IntegerField(blank=True, null=True)
    i_g1f = models.IntegerField(blank=True, null=True)
    i_record = models.IntegerField(blank=True, null=True)
    jockey_w = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    distance_w = models.IntegerField(blank=True, null=True)
    burden_w = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_jockey = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_track = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_convert = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    r_start = models.CharField(max_length=5, blank=True, null=True)
    r_corners = models.CharField(max_length=5, blank=True, null=True)
    r_finish = models.CharField(max_length=5, blank=True, null=True)
    r_wrapup = models.CharField(max_length=5, blank=True, null=True)
    r_etc = models.CharField(max_length=400, blank=True, null=True)
    r_flag = models.CharField(max_length=1, blank=True, null=True)
    p_rank = models.IntegerField(blank=True, null=True)
    p_record = models.CharField(max_length=6, blank=True, null=True)
    pop_rank = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rec011'
        unique_together = (('rcity', 'rdate', 'rno', 'gate'),)


class Rec012(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    pair1 = models.IntegerField()
    pair2 = models.IntegerField()
    pair = models.CharField(max_length=5, blank=True, null=True)
    alloc = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rec012'
        unique_together = (('rcity', 'rdate', 'rno', 'pair1', 'pair2'),)


class Rec013(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    judged = models.CharField(max_length=2000, blank=True, null=True)
    judged_add = models.CharField(max_length=1000, blank=True, null=True)
    committee = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rec013'
        unique_together = (('rcity', 'rdate', 'rno'),)


class Rec014(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    distance = models.CharField(max_length=4, blank=True, null=True)
    furlong01 = models.CharField(max_length=6, blank=True, null=True)
    furlong02 = models.CharField(max_length=6, blank=True, null=True)
    furlong03 = models.CharField(max_length=6, blank=True, null=True)
    furlong04 = models.CharField(max_length=6, blank=True, null=True)
    furlong05 = models.CharField(max_length=6, blank=True, null=True)
    furlong06 = models.CharField(max_length=6, blank=True, null=True)
    furlong07 = models.CharField(max_length=6, blank=True, null=True)
    furlong08 = models.CharField(max_length=6, blank=True, null=True)
    furlong09 = models.CharField(max_length=6, blank=True, null=True)
    furlong10 = models.CharField(max_length=6, blank=True, null=True)
    furlong11 = models.CharField(max_length=6, blank=True, null=True)
    furlong12 = models.CharField(max_length=6, blank=True, null=True)
    passage01 = models.CharField(max_length=4, blank=True, null=True)
    passage02 = models.CharField(max_length=4, blank=True, null=True)
    passage03 = models.CharField(max_length=4, blank=True, null=True)
    passage04 = models.CharField(max_length=4, blank=True, null=True)
    passage05 = models.CharField(max_length=4, blank=True, null=True)
    passage06 = models.CharField(max_length=4, blank=True, null=True)
    passage07 = models.CharField(max_length=4, blank=True, null=True)
    passage08 = models.CharField(max_length=4, blank=True, null=True)
    passage09 = models.CharField(max_length=4, blank=True, null=True)
    passage10 = models.CharField(max_length=4, blank=True, null=True)
    passage11 = models.CharField(max_length=4, blank=True, null=True)
    passage12 = models.CharField(max_length=4, blank=True, null=True)
    passage01t = models.CharField(max_length=6, blank=True, null=True)
    passage02t = models.CharField(max_length=6, blank=True, null=True)
    passage03t = models.CharField(max_length=6, blank=True, null=True)
    passage04t = models.CharField(max_length=6, blank=True, null=True)
    passage05t = models.CharField(max_length=6, blank=True, null=True)
    passage06t = models.CharField(max_length=6, blank=True, null=True)
    passage07t = models.CharField(max_length=6, blank=True, null=True)
    passage08t = models.CharField(max_length=6, blank=True, null=True)
    passage09t = models.CharField(max_length=6, blank=True, null=True)
    passage10t = models.CharField(max_length=6, blank=True, null=True)
    passage11t = models.CharField(max_length=6, blank=True, null=True)
    passage12t = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rec014'
        unique_together = (('rcity', 'rdate', 'rno'),)


class Rec015(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    gate = models.IntegerField()
    t_sort = models.CharField(max_length=10)
    horse = models.CharField(max_length=20)
    t_type = models.CharField(max_length=18)
    t_detail = models.CharField(max_length=50)
    t_reason = models.CharField(max_length=200, blank=True, null=True)
    jockey = models.CharField(max_length=10, blank=True, null=True)
    trainer = models.CharField(max_length=10, blank=True, null=True)
    t_text = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rec015'
        unique_together = (('rcity', 'rdate', 'rno', 'gate', 't_sort', 'horse', 't_type', 't_detail'),)


class RecordS(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4, db_collation='euckr_korean_ci')
    rdate = models.CharField(max_length=8, db_collation='euckr_korean_ci')
    rno = models.IntegerField()
    rday = models.CharField(max_length=2, db_collation='euckr_korean_ci', blank=True, null=True)
    rseq = models.IntegerField(blank=True, null=True)
    distance = models.IntegerField(blank=True, null=True)
    grade = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    dividing = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rname = models.CharField(max_length=40, db_collation='euckr_korean_ci', blank=True, null=True)
    rcon1 = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rcon2 = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    weather = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rstate = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rmoisture = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rtime = models.CharField(max_length=5, db_collation='euckr_korean_ci', blank=True, null=True)
    gate = models.IntegerField()
    rank = models.IntegerField(blank=True, null=True)
    horse = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    birthplace = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    h_sex = models.CharField(max_length=2, db_collation='euckr_korean_ci', blank=True, null=True)
    h_age = models.IntegerField(blank=True, null=True)
    handycap = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    jockey = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    joc_adv = models.CharField(max_length=4, db_collation='euckr_korean_ci', blank=True, null=True)
    trainer = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    host = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    h_weight = models.IntegerField(blank=True, null=True)
    w_change = models.CharField(max_length=4, db_collation='euckr_korean_ci', blank=True, null=True)
    record = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    gap = models.CharField(max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    corners = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    rs1f = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r1c = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r2c = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r3c = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r4c = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg3f = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg2f = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg1f = models.CharField(max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    i_s1f = models.IntegerField(blank=True, null=True)
    i_r1c = models.IntegerField(blank=True, null=True)
    i_r2c = models.IntegerField(blank=True, null=True)
    i_r3c = models.IntegerField(blank=True, null=True)
    i_r4c = models.IntegerField(blank=True, null=True)
    i_g3f = models.IntegerField(blank=True, null=True)
    i_g2f = models.IntegerField(blank=True, null=True)
    i_g1f = models.IntegerField(blank=True, null=True)
    i_record = models.IntegerField(blank=True, null=True)
    jockey_w = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    burden_w = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_jockey = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    adv_track = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    i_convert = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    flag = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'record_s'
        unique_together = (('rcity', 'rdate', 'rno', 'gate'), ('horse', 'rdate', 'distance'),)


class SocialaccountSocialaccount(models.Model):
    provider = models.CharField(max_length=30)
    uid = models.CharField(max_length=191)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    extra_data = models.TextField()
    user = models.ForeignKey(BaseUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialaccount'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialapp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=191)
    secret = models.CharField(max_length=191)
    key = models.CharField(max_length=191)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp'


class SocialaccountSocialappSites(models.Model):
    id = models.BigAutoField(primary_key=True)
    socialapp = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp_sites'
        unique_together = (('socialapp', 'site'),)


class SocialaccountSocialtoken(models.Model):
    token = models.TextField()
    token_secret = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)
    account = models.ForeignKey(SocialaccountSocialaccount, models.DO_NOTHING)
    app = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialtoken'
        unique_together = (('app', 'account'),)


class StartAudit(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=10)
    rno = models.IntegerField()
    gate = models.IntegerField()
    horse = models.CharField(max_length=18)
    rider = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    rider_k = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    audit_reason = models.CharField(max_length=20, db_collation='utf8_general_ci', blank=True, null=True)
    judge = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    judge_reason = models.CharField(max_length=20, db_collation='utf8_general_ci', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'start_audit'
        unique_together = (('rcity', 'rdate', 'rno', 'gate', 'horse'),)


class StartTrain(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4, db_collation='euckr_korean_ci')
    horse = models.CharField(max_length=18, db_collation='euckr_korean_ci')
    tdate = models.CharField(max_length=10)
    team = models.CharField(max_length=2, blank=True, null=True)
    team_num = models.CharField(max_length=3, blank=True, null=True)
    rider = models.CharField(max_length=20, blank=True, null=True)
    rider_k = models.CharField(max_length=10, blank=True, null=True)
    judge = models.CharField(max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'start_train'
        unique_together = (('rcity', 'horse', 'tdate'),)


class Swim(models.Model):
    horse = models.CharField(primary_key=True, max_length=16)
    tdate = models.CharField(max_length=8)
    team = models.CharField(max_length=2, blank=True, null=True)
    trainer = models.CharField(max_length=6, blank=True, null=True)
    laps = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'swim'
        unique_together = (('horse', 'tdate'),)


class Train(models.Model):
    rcity = models.CharField(max_length=5, db_collation='utf8_general_ci')
    tdate = models.CharField(primary_key=True, max_length=8, db_collation='utf8_general_ci')
    horse = models.CharField(max_length=18, db_collation='utf8_general_ci')
    team = models.CharField(max_length=3, db_collation='utf8_general_ci', blank=True, null=True)
    team_num = models.CharField(max_length=3, db_collation='utf8_general_ci', blank=True, null=True)
    grade = models.CharField(max_length=6, db_collation='utf8_general_ci', blank=True, null=True)
    rider = models.CharField(max_length=12, db_collation='utf8_general_ci')
    in_time = models.CharField(max_length=5, db_collation='utf8_general_ci', blank=True, null=True)
    out_time = models.CharField(max_length=5, db_collation='utf8_general_ci', blank=True, null=True)
    t_time = models.IntegerField(blank=True, null=True)
    canter = models.IntegerField(blank=True, null=True)
    strong = models.IntegerField(blank=True, null=True)
    remark = models.CharField(max_length=4, db_collation='utf8_general_ci', blank=True, null=True)
    swim = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'train'
        unique_together = (('tdate', 'horse', 'rcity'),)


class Trainer(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    trainer = models.CharField(max_length=6, db_collation='utf8_general_ci')
    birth = models.CharField(max_length=10, db_collation='utf8_general_ci')
    team = models.CharField(max_length=3, db_collation='utf8_general_ci', blank=True, null=True)
    age = models.CharField(max_length=2, db_collation='utf8_general_ci', blank=True, null=True)
    debut = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    tot_race = models.IntegerField(blank=True, null=True)
    tot_1st = models.IntegerField(blank=True, null=True)
    tot_2nd = models.IntegerField(blank=True, null=True)
    tot_3rd = models.IntegerField(blank=True, null=True)
    year_race = models.IntegerField(blank=True, null=True)
    year_1st = models.IntegerField(blank=True, null=True)
    year_2nd = models.IntegerField(blank=True, null=True)
    year_3rd = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trainer'
        unique_together = (('rcity', 'trainer', 'birth'),)


class TrainerW(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    wdate = models.CharField(max_length=8)
    trainer = models.CharField(max_length=6, db_collation='utf8_general_ci')
    birth = models.CharField(max_length=10, db_collation='utf8_general_ci')
    team = models.CharField(max_length=3, db_collation='utf8_general_ci', blank=True, null=True)
    age = models.CharField(max_length=2, db_collation='utf8_general_ci', blank=True, null=True)
    debut = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    tot_race = models.IntegerField(blank=True, null=True)
    tot_1st = models.IntegerField(blank=True, null=True)
    tot_2nd = models.IntegerField(blank=True, null=True)
    tot_3rd = models.IntegerField(blank=True, null=True)
    year_race = models.IntegerField(blank=True, null=True)
    year_1st = models.IntegerField(blank=True, null=True)
    year_2nd = models.IntegerField(blank=True, null=True)
    year_3rd = models.IntegerField(blank=True, null=True)
    year_per = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    year_3per = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trainer_w'
        unique_together = (('rcity', 'trainer', 'birth', 'wdate'),)


class Training(models.Model):
    rcity = models.CharField(max_length=4)
    tdate = models.CharField(primary_key=True, max_length=8, db_collation='utf8_general_ci')
    horse = models.CharField(max_length=18)
    team = models.CharField(max_length=3, db_collation='utf8_general_ci', blank=True, null=True)
    trainer = models.CharField(max_length=6, db_collation='utf8_general_ci', blank=True, null=True)
    team_num = models.CharField(max_length=2, db_collation='utf8_general_ci', blank=True, null=True)
    rider = models.CharField(max_length=2, db_collation='utf8_general_ci', blank=True, null=True)
    in_time = models.CharField(max_length=5, db_collation='utf8_general_ci', blank=True, null=True)
    out_time = models.CharField(max_length=5, db_collation='utf8_general_ci', blank=True, null=True)
    t_time = models.CharField(max_length=5, db_collation='utf8_general_ci', blank=True, null=True)
    remark = models.CharField(max_length=100, db_collation='utf8_general_ci', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'training'
        unique_together = (('tdate', 'horse', 'rcity'),)


class Treat(models.Model):
    rcity = models.CharField(max_length=4)
    horse = models.CharField(primary_key=True, max_length=18)
    tdate = models.CharField(max_length=10, db_collation='utf8_general_ci')
    team = models.CharField(max_length=2, db_collation='utf8_general_ci')
    hospital = models.CharField(max_length=30, db_collation='utf8_general_ci')
    disease = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'treat'
        unique_together = (('horse', 'tdate', 'rcity', 'team', 'hospital', 'disease'),)


class VarRace(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    distance = models.IntegerField()
    grade = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    weather = models.CharField(max_length=10, db_collation='utf8_general_ci')
    rstate = models.CharField(max_length=10, db_collation='utf8_general_ci')
    rmoisture = models.CharField(max_length=10, db_collation='utf8_general_ci')
    gate = models.IntegerField()
    s1f = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    r1c = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    r2c = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    r3c = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    r4c = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    g3f = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    g2f = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    g1f = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    record = models.CharField(max_length=10, db_collation='utf8_general_ci', blank=True, null=True)
    i_s1f = models.IntegerField(blank=True, null=True)
    i_r1c = models.IntegerField(blank=True, null=True)
    i_r2c = models.IntegerField(blank=True, null=True)
    i_r3c = models.IntegerField(blank=True, null=True)
    i_r4c = models.IntegerField(blank=True, null=True)
    i_g3f = models.IntegerField(blank=True, null=True)
    i_g2f = models.IntegerField(blank=True, null=True)
    i_g1f = models.IntegerField(blank=True, null=True)
    i_record = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'var_race'
        unique_together = (('rcity', 'distance', 'weather', 'rstate', 'rmoisture', 'gate'),)


class Weight(models.Model):
    wdate = models.DateTimeField(primary_key=True)
    w_avg = models.IntegerField(blank=True, null=True)
    w_fast = models.IntegerField(blank=True, null=True)
    w_slow = models.IntegerField(blank=True, null=True)
    w_recent3 = models.IntegerField(blank=True, null=True)
    w_recent5 = models.IntegerField(blank=True, null=True)
    w_convert = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'weight'
