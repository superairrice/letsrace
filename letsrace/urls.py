"""letsrace URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static


def healthz(request):
    return HttpResponse("ok")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('base.api.urls')),

    path('__debug__/', include('debug_toolbar.urls')),

    # path('', include('base.urls')),

    path('accounts/', include('allauth.urls')),
    # path('accounts/', include('base.api.urls')),

    path('', include('base.urls')),

    # Backward-compatible redirects for previous root-level allauth URLs.
    path('login/', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    path('logout/', RedirectView.as_view(url='/accounts/logout/', permanent=False)),
    path('signup/', RedirectView.as_view(url='/accounts/signup/', permanent=False)),
    path('google/login/', RedirectView.as_view(url='/accounts/google/login/', permanent=False)),
    path('google/login/callback/', RedirectView.as_view(url='/accounts/google/login/callback/', permanent=False)),
    path('naver/login/', RedirectView.as_view(url='/accounts/naver/login/', permanent=False)),
    path('naver/login/callback/', RedirectView.as_view(url='/accounts/naver/login/callback/', permanent=False)),

    # url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),



]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler400 = "apps.core.views.error_400"
handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
