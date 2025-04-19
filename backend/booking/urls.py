from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, RestaurantViewSet,
    AvailabilityViewSet, ReservationViewSet,
    login_view, logout_view
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'restaurants', RestaurantViewSet)
router.register(r'availabilities', AvailabilityViewSet)
router.register(r'reservations', ReservationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
] 