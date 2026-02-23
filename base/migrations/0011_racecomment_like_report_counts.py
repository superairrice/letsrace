from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0010_cleanup_noop"),
    ]

    operations = [
        migrations.AddField(
            model_name="racecomment",
            name="like_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="racecomment",
            name="report_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
