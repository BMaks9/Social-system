"""
URL configuration for social_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from drf_yasg import openapi
from web_social_service import views
from django.urls import include, path
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view


router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet, basename="users")

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", include(router.urls)),
    path("admin/", admin.site.urls),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(r"patronages/", views.PatronageList.as_view(), name="patronages-list"),
    path(
        r"patronages/<int:id>/",
        views.PatronageDetail.as_view(),
        name="patronages-detail",
    ),
    path(
        r"patronages/<int:id>/draft/",
        views.PatronageDraft.as_view(),
        name="patronages-draft",
    ),
    path(
        r"patronages/<int:id>/image/",
        views.PatronageImage.as_view(),
        name="patronages-image",
    ),
    path(r"disabilities/", views.DisabilitiesList.as_view(), name="disabilities-list"),
    path(
        r"disabilities/<int:id>/",
        views.DisabilitiesDetail.as_view(),
        name="disabilities-detail",
    ),
    path(
        r"disabilities/<int:id>/submit/",
        views.DisabilitiesSubmit.as_view(),
        name="disabilities-submit",
    ),
    path(
        r"disabilities/<int:id>/complete/",
        views.DisabilitiesComplete.as_view(),
        name="disabilities-complete",
    ),
    path(
        r"disabilities/<int:disabilityId>/patronage/<int:patronageId>/",
        views.Disabilities_Patronage_Edit.as_view(),
        name="disabilities-patronage-edit",
    ),
    # path(r'users/login/', views.login_view(), name='users-login'),
    # # path(r'users/profile/', views.UsersProfile.as_view(), name='users-profile'),
    # path(r'users/logout/', views.logout_view(), name='users-logout'),
    # path(r'login/',  views.login_view, name='login'),
    # path(r'logout/', views.logout_view, name='logout'),
    # path('users/<int:pk>/', views.UserProfileUpdateView.as_view(), name='user_update_profile'),
]
