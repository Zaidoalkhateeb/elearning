from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import TokenObtainSingleSessionView

urlpatterns = [
    path('token/', TokenObtainSingleSessionView.as_view(), name='token_obtain_single_session'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
