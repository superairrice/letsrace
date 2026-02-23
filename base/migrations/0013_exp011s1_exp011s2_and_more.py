from django.db import migrations


class Migration(migrations.Migration):
    """
    NOTE:
    The previous auto-generated 0013 migration attempted to create legacy tables
    (exp011s1/exp011s2) and alter many existing legacy columns/indexes.
    Those schemas already exist in production DBs, which caused
    OperationalError(1050, table already exists).

    Keep this migration as no-op to preserve migration order safely.
    """

    dependencies = [
        ("base", "0012_racecommentarchive"),
    ]

    operations = []
