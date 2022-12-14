# Generated by Django 4.0.5 on 2022-10-12 02:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_award_jockeyw_jtrate_raceresult_rec010_records_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Exp012',
            fields=[
                ('rcity', models.CharField(max_length=4, primary_key=True, serialize=False)),
                ('rdate', models.CharField(max_length=8)),
                ('rno', models.IntegerField()),
                ('gate', models.IntegerField()),
                ('horse', models.CharField(blank=True, max_length=20, null=True)),
                ('gear1', models.CharField(blank=True, max_length=20, null=True)),
                ('gear2', models.CharField(blank=True, max_length=20, null=True)),
                ('blood1', models.CharField(blank=True, max_length=20, null=True)),
                ('blood2', models.CharField(blank=True, max_length=20, null=True)),
                ('treat1', models.CharField(blank=True, max_length=100, null=True)),
                ('treat2', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'db_table': 'exp012',
                'managed': False,
            },
        ),
        migrations.AddField(
            model_name='exp011',
            name='j_per',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='exp011',
            name='jt_1st',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exp011',
            name='jt_2nd',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exp011',
            name='jt_3rd',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exp011',
            name='jt_cnt',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exp011',
            name='jt_per',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='exp011',
            name='r_pop',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exp011',
            name='t_per',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='racing',
            name='r1award',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='racing',
            name='r2award',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='racing',
            name='r3award',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='racing',
            name='r4award',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='racing',
            name='r5award',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='racing',
            name='sub1award',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='racing',
            name='sub2award',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='racing',
            name='sub3award',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='exp010',
            unique_together={('rcity', 'rdate', 'rno')},
        ),
        migrations.AlterUniqueTogether(
            name='exp011',
            unique_together={('rcity', 'rdate', 'rno', 'gate')},
        ),
        migrations.AlterModelTable(
            name='records',
            table='record',
        ),
    ]
