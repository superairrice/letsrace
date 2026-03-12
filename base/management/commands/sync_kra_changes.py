from django.core.management.base import BaseCommand

from apps.domains.ops.kra_change_sync import sync_latest_kra_change_entries


class Command(BaseCommand):
    help = "Fetch the latest KRA 출전표변경 page and apply horse cancellation/jockey change entries to DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            default="",
            help="Optional custom URL. Defaults to the latest KRA 출전표변경 page.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and parse only. Do not update DB.",
        )

    def handle(self, *args, **options):
        result = sync_latest_kra_change_entries(
            url=options.get("url") or "",
            commit=not bool(options.get("dry_run")),
        )

        self.stdout.write(f"url={result.get('resolved_url') or result.get('url')}")
        self.stdout.write(f"tables={len(result.get('tables', []))}")
        self.stdout.write(f"cancel_lines={result.get('cancel_lines', 0)}")
        self.stdout.write(f"jockey_lines={result.get('jockey_lines', 0)}")

        if options.get("dry_run"):
            self.stdout.write(self.style.WARNING("dry-run: DB update skipped"))
        else:
            self.stdout.write(f"cancel_applied={result.get('cancel_applied', 0)}")
            self.stdout.write(f"jockey_applied={result.get('jockey_applied', 0)}")
            self.stdout.write(self.style.SUCCESS("KRA change sync completed"))
