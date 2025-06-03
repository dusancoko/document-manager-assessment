from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from propylon_document_manager.file_versions.api.views import (
    CustomObtainAuthToken, 
    FileDownloadByNameView, 
    FileUploadView, 
    FileCompareView,
    FileShareView
)


# API URLS
urlpatterns = [
    # API base url
    path("admin/", admin.site.urls),
    path("api/", include("propylon_document_manager.site.api_router")),
    # DRF auth token
    path("api-auth/", include("rest_framework.urls")),
    path("api/token/", CustomObtainAuthToken.as_view(), name="custom_token_auth"),
    path("api/upload/", FileUploadView.as_view(), name="file_upload"),
    path("api/download/<path:path>/", FileDownloadByNameView.as_view(), name="file_download"),
    path("api/compare/", FileCompareView.as_view(), name="file_compare"),
    path("api/share/", FileShareView.as_view(), name="file_share"),
]

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns