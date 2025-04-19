from django.contrib import admin
from .models import User, Restaurant, Availability, Reservation

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine', 'address', 'user')
    list_filter = ('cuisine',)
    search_fields = ('name', 'address')

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'date', 'start_time', 'is_available', 'is_blocked')
    list_filter = ('restaurant', 'date', 'is_available', 'is_blocked')
    search_fields = ('restaurant__name',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'diner', 'availability', 'created_at', 'is_past_display')
    list_filter = ('restaurant', 'availability__date')
    search_fields = ('restaurant__name', 'diner__username')
    
    def is_past_display(self, obj):
        return obj.is_past
    is_past_display.short_description = 'Is Past'
    is_past_display.boolean = True
