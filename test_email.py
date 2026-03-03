import os
import django
from django.core.mail import send_mail

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuhes_kb.settings')
django.setup()

from django.conf import settings

print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")

try:
    sent = send_mail(
        'Test Email from KUHeS',
        'This is a test email to verify SMTP settings.',
        settings.DEFAULT_FROM_EMAIL,
        ['your_personal_email@gmail.com'],  # Change this to your email
        fail_silently=False,
    )
    print(f"✅ Email sent! Count: {sent}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()