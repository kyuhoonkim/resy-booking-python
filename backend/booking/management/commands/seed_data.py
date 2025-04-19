from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from booking.models import Restaurant, Availability

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # Create admin if not exists
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'is_superuser': True,
                'is_staff': True
            }
        )
        if created:
            admin.set_password('adminpass')
            admin.save()
            self.stdout.write('Created admin user')
        else:
            self.stdout.write('Admin user already exists')

        # Create restaurants
        restaurants = [
            {
                'name': 'Oiji Mi',
                'cuisine': 'Korean',
                'address': '17 W 19th St, New York, NY 10011',
                'username': 'oiji_mi',
                'password': 'restaurantpass'
            },
            {
                'name': 'Rosella',
                'cuisine': 'Japanese',
                'address': '137 Avenue A, New York, NY 10009',
                'username': 'rosella',
                'password': 'restaurantpass'
            },
            {
                'name': 'The Four Horseman',
                'cuisine': 'American',
                'address': '295 Grand St, Brooklyn, NY 11211',
                'username': 'four_horseman',
                'password': 'restaurantpass'
            }
        ]

        for restaurant_data in restaurants:
            # Create or get restaurant user
            user, created = User.objects.get_or_create(
                username=restaurant_data['username'],
                defaults={
                    'email': f"{restaurant_data['username']}@example.com",
                    'role': 'restaurant'
                }
            )
            if created:
                user.set_password(restaurant_data['password'])
                user.save()
            
            # Create or get restaurant profile
            restaurant, created = Restaurant.objects.get_or_create(
                user=user,
                defaults={
                    'name': restaurant_data['name'],
                    'cuisine': restaurant_data['cuisine'],
                    'address': restaurant_data['address']
                }
            )
            
            if created:
                # Pre-fill availability (5-8pm for next 4 weeks)
                today = timezone.now().date()
                for days_ahead in range(28):  # 4 weeks
                    date = today + timedelta(days=days_ahead)
                    for hour in range(17, 20):  # 5pm to 8pm
                        Availability.objects.create(
                            restaurant=restaurant,
                            date=date,
                            start_time=datetime.strptime(f"{hour}:00", "%H:%M").time(),
                            is_available=True,
                            is_blocked=False
                        )
            
            self.stdout.write(f'{"Created" if created else "Updated"} restaurant: {restaurant.name}')

        # Create diners
        diners = [
            {
                'username': 'gyulook',
                'name': 'Kyuhoon',
                'email': 'kyuhoonkim93@gmail.com',
                'password': 'dinerk'
            },
            {
                'username': 'reno',
                'name': 'Irene',
                'email': 'irene@gmail.com',
                'password': 'dineri'
            },
            {
                'username': 'oscar',
                'name': 'Oscar',
                'email': 'oscar@gmail.com',
                'password': 'dinero'
            }
        ]

        for diner_data in diners:
            user, created = User.objects.get_or_create(
                username=diner_data['username'],
                defaults={
                    'email': diner_data['email'],
                    'role': 'diner',
                    'first_name': diner_data['name']
                }
            )
            if created:
                user.set_password(diner_data['password'])
                user.save()
                self.stdout.write(f'Created diner: {diner_data["name"]}')
            else:
                self.stdout.write(f'Diner already exists: {diner_data["name"]}')

        self.stdout.write(self.style.SUCCESS('Successfully seeded data')) 