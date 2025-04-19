from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Restaurant, Availability, Reservation
from .serializers import (
    UserSerializer, RestaurantSerializer,
    AvailabilitySerializer, ReservationSerializer
)

User = get_user_model()

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsRestaurant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'restaurant'

class IsDiner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'diner'

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all()
        return User.objects.none()

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [IsAdmin | IsRestaurant]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Restaurant.objects.all()
        elif self.request.user.role == 'restaurant':
            return Restaurant.objects.filter(user=self.request.user)
        return Restaurant.objects.none()

class AvailabilityViewSet(viewsets.ModelViewSet):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAdmin | IsRestaurant]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Availability.objects.all()
        elif self.request.user.role == 'restaurant':
            restaurant = Restaurant.objects.get(user=self.request.user)
            return Availability.objects.filter(restaurant=restaurant)
        return Availability.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role == 'restaurant':
            restaurant = Restaurant.objects.get(user=self.request.user)
            serializer.save(restaurant=restaurant)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        availability = self.get_object()
        if availability.is_available and not availability.is_blocked:
            availability.is_blocked = True
            availability.save()
            return Response({'status': 'slot blocked'})
        return Response(
            {'error': 'Slot is not available or already blocked'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        availability = self.get_object()
        if availability.is_blocked:
            availability.is_blocked = False
            availability.save()
            return Response({'status': 'slot unblocked'})
        return Response(
            {'error': 'Slot is not blocked'},
            status=status.HTTP_400_BAD_REQUEST
        )

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAdmin | IsRestaurant | IsDiner]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Reservation.objects.all()
        elif self.request.user.role == 'restaurant':
            restaurant = Restaurant.objects.get(user=self.request.user)
            return Reservation.objects.filter(restaurant=restaurant)
        elif self.request.user.role == 'diner':
            return Reservation.objects.filter(diner=self.request.user)
        return Reservation.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role == 'diner':
            availability = serializer.validated_data['availability']
            if not availability.is_available or availability.is_blocked:
                raise serializers.ValidationError('This time slot is not available')
            
            # Check for optimistic locking
            if Reservation.objects.filter(availability=availability).exists():
                raise serializers.ValidationError('This time slot has already been booked')
            
            availability.is_available = False
            availability.save()
            serializer.save(diner=self.request.user)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role == 'diner' and instance.diner != self.request.user:
            raise PermissionDenied('You can only cancel your own reservations')
        
        availability = instance.availability
        availability.is_available = True
        availability.save()
        instance.delete()
