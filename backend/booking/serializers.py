from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Restaurant, Availability, Reservation

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'first_name', 'last_name']
        read_only_fields = ['id', 'role']

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'cuisine', 'address']
        read_only_fields = ['id']

class AvailabilitySerializer(serializers.ModelSerializer):
    restaurant = RestaurantSerializer(read_only=True)
    restaurant_id = serializers.PrimaryKeyRelatedField(
        queryset=Restaurant.objects.all(),
        source='restaurant',
        write_only=True
    )
    
    class Meta:
        model = Availability
        fields = ['id', 'restaurant', 'restaurant_id', 'date', 'start_time', 'is_available', 'is_blocked']
        read_only_fields = ['id']

class ReservationSerializer(serializers.ModelSerializer):
    restaurant = RestaurantSerializer(read_only=True)
    diner = UserSerializer(read_only=True)
    availability = AvailabilitySerializer(read_only=True)
    
    restaurant_id = serializers.PrimaryKeyRelatedField(
        queryset=Restaurant.objects.all(),
        source='restaurant',
        write_only=True
    )
    availability_id = serializers.PrimaryKeyRelatedField(
        queryset=Availability.objects.all(),
        source='availability',
        write_only=True
    )
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'restaurant', 'restaurant_id', 'diner', 
            'availability', 'availability_id', 'created_at'
        ]
        read_only_fields = ['id', 'diner', 'created_at'] 