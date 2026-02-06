from django.urls import include, path


urlpatterns = [
    path("", include("apps.core.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.community.urls")),
    path("", include("apps.prediction.urls")),
    path("", include("apps.ops.urls")),
]
