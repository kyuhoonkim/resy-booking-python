from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model, login, logout
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import PermissionDenied
from .models import Restaurant, Availability, Reservation
from .serializers import (
    UserSerializer, RestaurantSerializer,
    AvailabilitySerializer, ReservationSerializer
)

User = get_user_model()

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ensure_csrf_cookie
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            login(request, user)
            return Response({
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name
            })
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
@ensure_csrf_cookie
def logout_view(request):
    logout(request)
    return Response({'message': 'Successfully logged out'})

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
    permission_classes = [permissions.AllowAny]
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdmin() | IsRestaurant()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return Restaurant.objects.all()

    def perform_update(self, serializer):
        if self.request.user.role == 'restaurant' and self.get_object().user != self.request.user:
            raise PermissionDenied('You can only update your own restaurant profile')
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role == 'restaurant' and instance.user != self.request.user:
            raise PermissionDenied('You can only delete your own restaurant profile')
        instance.delete()

class AvailabilityViewSet(viewsets.ModelViewSet):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'block', 'unblock']:
            return [IsAdmin() | IsRestaurant()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Availability.objects.all()
        elif self.request.user.role == 'restaurant':
            restaurant = Restaurant.objects.get(user=self.request.user)
            return Availability.objects.filter(restaurant=restaurant)
        return Availability.objects.all()

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
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsDiner()]
        elif self.action in ['update', 'partial_update']:
            return [IsAdmin() | IsRestaurant() | IsDiner()]
        return [permissions.IsAuthenticated()]

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
                raise PermissionDenied('This time slot is not available')
            
            # Check for optimistic locking
            if Reservation.objects.filter(availability=availability).exists():
                raise PermissionDenied('This time slot has already been booked')
            
            availability.is_available = False
            availability.save()
            serializer.save(diner=self.request.user)
        else:
            raise PermissionDenied('Only diners can create reservations')

    def perform_destroy(self, instance):
        if self.request.user.role == 'diner' and instance.diner != self.request.user:
            raise PermissionDenied('You can only cancel your own reservations')
        elif self.request.user.role == 'restaurant' and instance.restaurant.user != self.request.user:
            raise PermissionDenied('You can only cancel reservations for your restaurant')
        
        availability = instance.availability
        availability.is_available = True
        availability.save()
        instance.delete()
