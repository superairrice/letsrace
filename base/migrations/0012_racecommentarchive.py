from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0011_racecomment_like_report_counts"),
    ]

    operations = [
        migrations.CreateModel(
            name="RaceCommentArchive",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rcity", models.CharField(db_index=True, max_length=4)),
                ("rdate", models.CharField(db_index=True, max_length=8)),
                ("rno", models.IntegerField(db_index=True)),
                ("original_comment_id", models.BigIntegerField(db_index=True)),
                ("nickname", models.CharField(max_length=50)),
                ("content", models.TextField(max_length=1000)),
                ("like_count", models.PositiveIntegerField(default=0)),
                ("report_count", models.PositiveIntegerField(default=0)),
                ("original_created", models.DateTimeField(blank=True, null=True)),
                ("original_updated", models.DateTimeField(blank=True, null=True)),
                ("archived_at", models.DateTimeField(auto_now_add=True)),
                ("archived_reason", models.CharField(default="self_delete", max_length=40)),
                ("archived_by_authenticated", models.BooleanField(default=False)),
                (
                    "archived_by_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="race_comment_archives",
                        to="base.user",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="base.user"
                    ),
                ),
            ],
            options={
                "ordering": ["-archived_at"],
            },
        ),
        migrations.AddIndex(
            model_name="racecommentarchive",
            index=models.Index(fields=["rcity", "rdate", "rno"], name="base_raceco_rcity_5bd444_idx"),
        ),
        migrations.AddIndex(
            model_name="racecommentarchive",
            index=models.Index(fields=["original_comment_id"], name="base_raceco_origina_46072c_idx"),
        ),
        migrations.AddIndex(
            model_name="racecommentarchive",
            index=models.Index(fields=["archived_at"], name="base_raceco_archive_7f6fcb_idx"),
        ),
    ]
