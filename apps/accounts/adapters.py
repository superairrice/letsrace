import logging

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


logger = logging.getLogger(__name__)


class LoggingSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        provider = getattr(getattr(sociallogin, "account", None), "provider", "unknown")
        uid = getattr(getattr(sociallogin, "account", None), "uid", "")
        logger.warning(
            "[social_login] pre_social_login provider=%s uid=%s path=%s",
            provider,
            uid,
            getattr(request, "path", ""),
        )
        return super().pre_social_login(request, sociallogin)

    def on_authentication_error(
        self,
        request,
        provider_id,
        error=None,
        exception=None,
        extra_context=None,
    ):
        logger.error(
            "[social_login] auth_error provider=%s error=%s exception=%s path=%s query=%s",
            provider_id,
            error,
            exception,
            getattr(request, "path", ""),
            getattr(request, "META", {}).get("QUERY_STRING", ""),
        )
        return super().on_authentication_error(
            request,
            provider_id,
            error=error,
            exception=exception,
            extra_context=extra_context,
        )

