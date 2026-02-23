from urllib.parse import unquote

from django.core.management.base import BaseCommand

from base.models import User


class Command(BaseCommand):
    help = "Normalize legacy avatar paths and decode once-encoded file names."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Persist updates. Without this flag, runs in dry-run mode.",
        )

    @staticmethod
    def _normalize(name: str) -> str:
        value = (name or "").strip()
        if not value:
            return value

        if value.startswith("/"):
            value = value.lstrip("/")

        if value.startswith("media/avatars/"):
            value = "avatars/" + value[len("media/avatars/") :]
        elif value.startswith("static/images/avatars/"):
            value = "avatars/" + value[len("static/images/avatars/") :]
        elif value.startswith("images/avatars/"):
            value = "avatars/" + value[len("images/avatars/") :]

        if value.startswith("avatars/"):
            suffix = value[len("avatars/") :]
            decoded_suffix = unquote(suffix)
            value = "avatars/" + decoded_suffix

        return value

    def handle(self, *args, **options):
        commit = options["commit"]
        updated = 0

        queryset = User.objects.exclude(avatar__isnull=True).exclude(avatar="")
        total = queryset.count()

        for user in queryset.iterator():
            original = user.avatar.name
            normalized = self._normalize(original)

            if normalized == original:
                continue

            updated += 1
            self.stdout.write(f"user={user.id}: {original} -> {normalized}")

            if commit:
                user.avatar.name = normalized
                user.save(update_fields=["avatar"])

        mode = "commit" if commit else "dry-run"
        self.stdout.write(self.style.SUCCESS(f"[{mode}] checked={total}, updated={updated}"))
