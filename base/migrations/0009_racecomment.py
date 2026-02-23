from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0008_exp010_r_guide_exp010_r_overview_exp011_alloc1r_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RaceComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rcity", models.CharField(db_index=True, max_length=4)),
                ("rdate", models.CharField(db_index=True, max_length=8)),
                ("rno", models.IntegerField(db_index=True)),
                ("nickname", models.CharField(max_length=50)),
                ("content", models.TextField(max_length=1000)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="base.user")),
            ],
            options={
                "ordering": ["-created"],
            },
        ),
        migrations.AddIndex(
            model_name="racecomment",
            index=models.Index(fields=["rcity", "rdate", "rno"], name="base_raceco_rcity_8f44e1_idx"),
        ),
        migrations.AddIndex(
            model_name="racecomment",
            index=models.Index(fields=["created"], name="base_raceco_created_73bb0e_idx"),
        ),
    ]
