from django.db import migrations


class Migration(migrations.Migration):
    """
    NOTE:
    The previous auto-generated 0010 migration attempted to create legacy tables
    (exp011s1/exp011s2) that already exist in production databases.
    This no-op migration keeps migration order stable without touching schema.
    """

    dependencies = [
        ("base", "0009_racecomment"),
    ]

    operations = []
