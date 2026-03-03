import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuhes_kb.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import ModeratorSeat

User = get_user_model()

print("🚀 Running database setup...")

# Run migrations
from django.core.management import call_command
call_command('migrate')
print("✅ Migrations complete")

# Create admin if not exists
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        email='admin@kuhes.ac.mw',
        username='admin',
        password='Admin@2024'
    )
    print("✅ Admin user created")
else:
    print("✅ Admin already exists")

# Create moderator seats if not exist
if ModeratorSeat.objects.count() == 0:
    # Add your seat creation code here or run separately
    print("⚠️ No moderator seats found - run seat creation script separately")
else:
    print(f"✅ {ModeratorSeat.objects.count()} moderator seats exist")

print("🎉 Database setup complete!")