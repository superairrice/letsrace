from django.db import migrations, models
from django.db.models import Count, Sum
import django.utils.timezone


def dedupe_visitorcount_rows(apps, schema_editor):
    VisitorCount = apps.get_model("base", "VisitorCount")
    duplicate_dates = (
        VisitorCount.objects.values("date")
        .annotate(row_count=Count("id"), total_count=Sum("count"))
        .filter(row_count__gt=1)
    )

    for row in duplicate_dates:
        date_value = row["date"]
        total_count = row["total_count"] or 0
        rows = VisitorCount.objects.filter(date=date_value).order_by("id")
        keeper = rows.first()
        if keeper is None:
            continue
        keeper.count = total_count
        keeper.save(update_fields=["count"])
        rows.exclude(id=keeper.id).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0014_alter_user_avatar_upload_to"),
    ]

    operations = [
        migrations.RunPython(dedupe_visitorcount_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="visitorcount",
            name="date",
            field=models.DateField(default=django.utils.timezone.now, unique=True),
        ),
    ]
