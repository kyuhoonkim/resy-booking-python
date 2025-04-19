from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('restaurant', 'Restaurant'),
        ('diner', 'Diner'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    cuisine = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant_profile')
    
    def __str__(self):
        return self.name

class Availability(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['restaurant', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.date} {self.start_time}"

class Reservation(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reservations')
    diner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    availability = models.ForeignKey(Availability, on_delete=models.CASCADE, related_name='reservation')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['availability__date', 'availability__start_time']
    
    def __str__(self):
        return f"{self.diner.username} at {self.restaurant.name} on {self.availability.date} {self.availability.start_time}"
    
    @property
    def is_past(self):
        now = timezone.now()
        reservation_datetime = timezone.make_aware(
            timezone.datetime.combine(self.availability.date, self.availability.start_time)
        )
        return now > reservation_datetime
