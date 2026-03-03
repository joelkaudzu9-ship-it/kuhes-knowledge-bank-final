from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models import EmailVerification, PasswordReset


def send_verification_email(user, request):
    """Send email verification link"""
    # Create verification token
    verification = EmailVerification.objects.create(user=user)

    # Build verification link
    verification_link = request.build_absolute_uri(
        reverse('verify_email', args=[str(verification.token)])
    )

    # Email content
    subject = '🔐 Verify your KUHeS Knowledge Bank account'
    message = f"""
Hello {user.username},

Welcome to KUHeS Knowledge Bank! Please verify your email address to activate your account.

VERIFICATION LINK:
{verification_link}

This link expires in 24 hours.

If you didn't create this account, please ignore this email.

- KUHeS Knowledge Bank Team
"""

    # HTML version (optional but nicer)
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066CC; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #0066CC;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>KUHeS Knowledge Bank</h1>
        </div>
        <div class="content">
            <h2>Hello {user.username}!</h2>
            <p>Welcome to KUHeS Knowledge Bank! Please verify your email address to activate your account.</p>

            <p style="text-align: center;">
                <a href="{verification_link}" class="button">Verify Email Address</a>
            </p>

            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{verification_link}</p>

            <p><strong>This link expires in 24 hours.</strong></p>

            <p>If you didn't create this account, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; {timezone.now().year} KUHeS Knowledge Bank. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

    # Send email
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

    return verification




def send_email_notification(user, subject, message, link=None):
    """Send email notification"""
    try:
        full_message = message
        if link:
            full_message += f"\n\nView: {link}"

        full_message += "\n\n- KUHeS Knowledge Bank Team"

        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        print(f"📧 Email sent to {user.email}: {subject}")
        return True
    except Exception as e:
        print(f"❌ Email failed to {user.email}: {e}")
        return False


def send_password_reset_email(user, request):
    """Send password reset link"""
    # Create reset token
    reset = PasswordReset.objects.create(user=user)

    # Build reset link
    reset_link = request.build_absolute_uri(
        reverse('reset_password', args=[str(reset.token)])
    )

    # Email content
    subject = '🔑 Reset your KUHeS Knowledge Bank password'
    message = f"""
Hello {user.username},

We received a request to reset your password for KUHeS Knowledge Bank.

RESET LINK:
{reset_link}

This link expires in 1 hour for security reasons.

If you didn't request this, please ignore this email and ensure your account is secure.

- KUHeS Knowledge Bank Team
"""

    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066CC; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #0066CC;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeeba; padding: 10px; border-radius: 5px; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>KUHeS Knowledge Bank</h1>
        </div>
        <div class="content">
            <h2>Hello {user.username}!</h2>
            <p>We received a request to reset your password.</p>

            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </p>

            <p>Or copy and paste this link:</p>
            <p style="word-break: break-all;">{reset_link}</p>

            <div class="warning">
                <p><strong>⚠️ Security Notice:</strong> This link expires in 1 hour. 
                If you didn't request this, please ignore this email and ensure your account is secure.</p>
            </div>
        </div>
        <div class="footer">
            <p>&copy; {timezone.now().year} KUHeS Knowledge Bank. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

    # Send email
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

    return reset