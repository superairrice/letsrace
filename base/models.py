from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)
    bio = models.TextField(null=True)

    avatar = models.ImageField(null=True, default="avatar.svg")

    USERNAME_FIELS = 'email'
    REQUIRED_FIELDS = []


class Topic(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(
        User, related_name='participants', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.name


class Message(models.Model):
    # from django.contrib.auth.models import User
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.body[0:50]


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
    r1award = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True)
    r2award = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True)
    r3award = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True)
    r4award = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True)
    r5award = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True)
    sub1award = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True)
    sub2award = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True)
    sub3award = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True)
    cflag = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'exp010'
        unique_together = (('rcity', 'rdate', 'rno'),)


class Exp011(models.Model):
    rcity = models.CharField(primary_key=True, max_length=4)
    rdate = models.CharField(max_length=8)
    rno = models.IntegerField()
    gate = models.IntegerField()
    horse = models.CharField(max_length=20, blank=True, null=True)
    birthplace = models.CharField(max_length=6, blank=True, null=True)
    h_sex = models.CharField(max_length=2, blank=True, null=True)
    h_age = models.IntegerField(blank=True, null=True)
    handycap = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True)
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
    i_s1f = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    i_g3f = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    i_g2f = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    i_g1f = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    i_complex = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    i_jockey = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    i_cycle = models.IntegerField(blank=True, null=True)
    i_prehandy = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True)
    r_rank = models.IntegerField(blank=True, null=True)
    r_record = models.CharField(max_length=10, blank=True, null=True)
    ir_record = models.IntegerField(blank=True, null=True)
    remark = models.CharField(max_length=1000, blank=True, null=True)
    h_weight = models.IntegerField(blank=True, null=True)
    j_per = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True)
    t_per = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True)
    jt_per = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True)
    jt_cnt = models.IntegerField(blank=True, null=True)
    jt_1st = models.IntegerField(blank=True, null=True)
    jt_2nd = models.IntegerField(blank=True, null=True)
    jt_3rd = models.IntegerField(blank=True, null=True)
    r_pop = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'exp011'
        unique_together = (('rcity', 'rdate', 'rno', 'gate'),)

    def count(self):
        if self._result_cache is not None:
            return len(self._result_cache)

        return self.query.get_count(using=self.db)


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


class Racing(models.Model):
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
    r1award = models.CharField(max_length=8, blank=True, null=True)
    r2award = models.CharField(max_length=8, blank=True, null=True)
    r3award = models.CharField(max_length=8, blank=True, null=True)
    r4award = models.CharField(max_length=8, blank=True, null=True)
    r5award = models.CharField(max_length=8, blank=True, null=True)
    sub1award = models.CharField(max_length=8, blank=True, null=True)
    sub2award = models.CharField(max_length=8, blank=True, null=True)
    sub3award = models.CharField(max_length=8, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'racing'


class RecordS(models.Model):
    rcity = models.CharField(
        primary_key=True, max_length=4, db_collation='euckr_korean_ci')
    rdate = models.CharField(max_length=8, db_collation='euckr_korean_ci')
    rno = models.IntegerField()
    rday = models.CharField(
        max_length=2, db_collation='euckr_korean_ci', blank=True, null=True)
    rseq = models.IntegerField(blank=True, null=True)
    distance = models.IntegerField(blank=True, null=True)
    grade = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    dividing = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rname = models.CharField(
        max_length=40, db_collation='euckr_korean_ci', blank=True, null=True)
    rcon1 = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rcon2 = models.CharField(
        max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    weather = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rstate = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rmoisture = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    rtime = models.CharField(
        max_length=5, db_collation='euckr_korean_ci', blank=True, null=True)
    gate = models.IntegerField()
    rank = models.IntegerField(blank=True, null=True)
    horse = models.CharField(
        max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    birthplace = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    h_sex = models.CharField(
        max_length=2, db_collation='euckr_korean_ci', blank=True, null=True)
    h_age = models.IntegerField(blank=True, null=True)
    handycap = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True)
    jockey = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    joc_adv = models.CharField(
        max_length=4, db_collation='euckr_korean_ci', blank=True, null=True)
    trainer = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    host = models.CharField(
        max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    h_weight = models.IntegerField(blank=True, null=True)
    w_change = models.CharField(
        max_length=4, db_collation='euckr_korean_ci', blank=True, null=True)
    record = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    gap = models.CharField(
        max_length=10, db_collation='euckr_korean_ci', blank=True, null=True)
    corners = models.CharField(
        max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    rs1f = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r1c = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r2c = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r3c = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    r4c = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg3f = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg2f = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    rg1f = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    i_s1f = models.IntegerField(blank=True, null=True)
    i_r1c = models.IntegerField(blank=True, null=True)
    i_r2c = models.IntegerField(blank=True, null=True)
    i_r3c = models.IntegerField(blank=True, null=True)
    i_r4c = models.IntegerField(blank=True, null=True)
    i_g3f = models.IntegerField(blank=True, null=True)
    i_g2f = models.IntegerField(blank=True, null=True)
    i_g1f = models.IntegerField(blank=True, null=True)
    i_record = models.IntegerField(blank=True, null=True)
    jockey_w = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    burden_w = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    adv_jockey = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    adv_track = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    i_convert = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    alloc1r = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    alloc3r = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True)
    p_rank = models.IntegerField(blank=True, null=True)
    p_record = models.CharField(
        max_length=6, db_collation='euckr_korean_ci', blank=True, null=True)
    pop_rank = models.IntegerField(blank=True, null=True)
    gear1 = models.CharField(
        max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    gear2 = models.CharField(
        max_length=20, db_collation='euckr_korean_ci', blank=True, null=True)
    treat1 = models.CharField(
        max_length=40, db_collation='euckr_korean_ci', blank=True, null=True)
    treat2 = models.CharField(
        max_length=40, db_collation='euckr_korean_ci', blank=True, null=True)

    # flag = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'record'
        unique_together = (('rcity', 'rdate', 'rno', 'gate'),
                           ('horse', 'rdate', 'distance'),)


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
    year_per = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'jockey_w'
        unique_together = (('rcity', 'wdate', 'jockey', 'birth'),)


class JtRate(models.Model):
    jockey = models.CharField(primary_key=True, max_length=6)
    trainer = models.CharField(max_length=6)
    r_cnt = models.IntegerField(blank=True, null=True)
    r_1st = models.IntegerField(blank=True, null=True)
    r_2nd = models.IntegerField(blank=True, null=True)
    r_3rd = models.IntegerField(blank=True, null=True)
    r_per = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'jt_rate'


class RaceResult(models.Model):
    rcity = models.CharField(
        primary_key=True, max_length=4, db_collation='euckr_korean_ci')
    rdate = models.CharField(max_length=8, db_collation='euckr_korean_ci')
    rno = models.IntegerField()
    r01 = models.IntegerField(blank=True, null=True)
    r02 = models.IntegerField(blank=True, null=True)
    r03 = models.IntegerField(blank=True, null=True)
    r04 = models.IntegerField(blank=True, null=True)
    r05 = models.IntegerField(blank=True, null=True)
    r06 = models.IntegerField(blank=True, null=True)
    r07 = models.IntegerField(blank=True, null=True)
    r08 = models.IntegerField(blank=True, null=True)
    r09 = models.IntegerField(blank=True, null=True)
    r10 = models.IntegerField(blank=True, null=True)
    r_r01 = models.IntegerField(blank=True, null=True)
    r_r02 = models.IntegerField(blank=True, null=True)
    r_r03 = models.IntegerField(blank=True, null=True)
    r_r04 = models.IntegerField(blank=True, null=True)
    r_r05 = models.IntegerField(blank=True, null=True)
    r_r06 = models.IntegerField(blank=True, null=True)
    r_r07 = models.IntegerField(blank=True, null=True)
    r_r08 = models.IntegerField(blank=True, null=True)
    r_r09 = models.IntegerField(blank=True, null=True)
    r_r10 = models.IntegerField(blank=True, null=True)
    r_cnt = models.IntegerField(blank=True, null=True)
    rday = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'race_result'


class Award(models.Model):
    rmonth = models.CharField(primary_key=True, max_length=6)
    jockey = models.CharField(max_length=6)
    trainer = models.CharField(max_length=8)
    host = models.CharField(max_length=10)
    award = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'award'


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
