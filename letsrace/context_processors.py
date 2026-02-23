from django.conf import settings


def analytics_ids(request):
    return {
        "GA_MEASUREMENT_ID": getattr(settings, "GA_MEASUREMENT_ID", ""),
        "GTM_CONTAINER_ID": getattr(settings, "GTM_CONTAINER_ID", ""),
    }

