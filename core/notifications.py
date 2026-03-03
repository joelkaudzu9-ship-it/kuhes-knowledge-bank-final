from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Notification, User, Resource, ResourceRequest


def create_notification(user, notification_type, title, message, resource=None, request_obj=None):
    """Create in-app notification"""
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        resource=resource,
        request=request_obj
    )
    print(f"✅ In-app notification created for {user.email}: {title}")
    return notification


def send_email_notification(user, subject, message, link=None):
    """Send email notification"""
    try:
        full_message = message
        if link:
            full_message += f"\n\nView: {link}"

        full_message += "\n\n- KUHeS Knowledge Bank Team"

        sent = send_mail(
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


def notify_request_fulfilled(request_obj, resource):
    """Notify requester that their request was fulfilled"""
    user = request_obj.requester
    subject = f"✅ Your request has been fulfilled: {request_obj.title}"

    # Get the site URL from settings
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    # Build the link
    resource_link = f"{site_url}{reverse('resource_detail', args=[resource.id])}"

    message = f"""
Hello {user.username},

Great news! Your request has been fulfilled!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUEST: {request_obj.title}
FULFILLED BY: {resource.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A resource matching your request is now available in the library.

View the resource: {resource_link}

Thank you for using KUHeS Knowledge Bank!
"""

    # Create in-app notification
    create_notification(
        user=user,
        notification_type=Notification.REQUEST_FULFILLED,
        title="✅ Request Fulfilled",
        message=f"Your request '{request_obj.title}' has been fulfilled with '{resource.title}'!",
        resource=resource,
        request_obj=request_obj
    )

    # Send email
    send_email_notification(user, subject, message, link=resource_link)

    print(f"🔔 Request fulfillment notification sent to {user.email}")


def notify_request_upvoted(request_obj, upvoter):
    """Notify requester that someone upvoted their request"""
    if request_obj.requester == upvoter:
        return  # Don't notify yourself

    user = request_obj.requester
    subject = f"👍 Your request received an upvote: {request_obj.title}"

    # Get the site URL from settings
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    # Build the link
    request_link = f"{site_url}{reverse('request_detail', args=[request_obj.id])}"

    message = f"""
Hello {user.username},

Good news! Someone thinks your request is important.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUEST: {request_obj.title}
UPVOTED BY: {upvoter.username}
TOTAL UPVOTES: {request_obj.upvotes + 1}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View your request: {request_link}

The more upvotes, the more likely it will be fulfilled!

- KUHeS Knowledge Bank Team
"""

    # Create in-app notification
    create_notification(
        user=user,
        notification_type=Notification.REQUEST_UPVOTED,
        title="👍 Request Upvoted",
        message=f"{upvoter.username} upvoted your request '{request_obj.title}'",
        request_obj=request_obj
    )

    # Send email (optional - can be enabled/disabled)
    # send_email_notification(user, subject, message, link=request_link)

    print(f"🔔 Upvote notification sent to {user.email} from {upvoter.username}")


def notify_resource_approved(resource):
    """Notify uploader that their resource was approved"""
    user = resource.uploader
    subject = f"✅ Your resource has been approved: {resource.title}"

    # Get the site URL from settings
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    # Build the link
    resource_link = f"{site_url}{reverse('resource_detail', args=[resource.id])}"

    message = f"""
Hello {user.username},

Congratulations! Your resource has been approved!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESOURCE: {resource.title}
TYPE: {resource.get_resource_type_display()}
APPROVED BY: {resource.approved_by.username if resource.approved_by else 'Moderator'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your resource is now live and available to all students.

View your resource: {resource_link}

Thank you for contributing to KUHeS Knowledge Bank!
"""

    # Create in-app notification
    create_notification(
        user=user,
        notification_type=Notification.RESOURCE_APPROVED,
        title="✅ Resource Approved",
        message=f"Your resource '{resource.title}' has been approved and is now live!",
        resource=resource
    )

    # Send email
    send_email_notification(user, subject, message, link=resource_link)

    print(f"🔔 Resource approval notification sent to {user.email}")
    return True


def notify_resource_rejected(resource, reason):
    """Notify uploader that their resource was rejected"""
    user = resource.uploader
    subject = f"❌ Your resource was not approved: {resource.title}"

    message = f"""
Hello {user.username},

Your resource submission was not approved.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESOURCE: {resource.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REASON FOR REJECTION:
{reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You can:
1. Fix the issues mentioned above
2. Upload an improved version
3. Contact a moderator if you have questions

- KUHeS Knowledge Bank Team
"""

    create_notification(
        user=user,
        notification_type=Notification.RESOURCE_REJECTED,
        title="❌ Resource Rejected",
        message=f"Your resource '{resource.title}' was rejected. Reason: {reason[:100]}...",
        resource=resource
    )

    send_email_notification(user, subject, message)

    print(f"🔔 Resource rejection notification sent to {user.email}")


def notify_new_request(request_obj):
    """Notify moderators about new request"""
    moderators = User.objects.filter(role__in=['moderator', 'senior_moderator', 'admin'])

    # Get the site URL from settings
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    # Build the link
    request_link = f"{site_url}{reverse('request_detail', args=[request_obj.id])}"

    count = 0
    for moderator in moderators:
        # Don't notify the requester if they're also a moderator
        if moderator == request_obj.requester:
            continue

        subject = f"📝 New Resource Request: {request_obj.title}"
        message = f"""
Hello {moderator.username},

A new resource request requires attention.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TITLE: {request_obj.title}
REQUESTED BY: {request_obj.requester.username}
URGENCY: {request_obj.get_urgency_display()}
CREATED: {request_obj.created_at.strftime('%B %d, %Y at %I:%M %p')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DESCRIPTION:
{request_obj.description[:200]}{'...' if len(request_obj.description) > 200 else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View request: {request_link}

Please review and help the community!

- KUHeS Knowledge Bank Team
"""

        create_notification(
            user=moderator,
            notification_type=Notification.REQUEST_CREATED,
            title="📝 New Request",
            message=f"New request: {request_obj.title} by {request_obj.requester.username}",
            request_obj=request_obj
        )

        # Send email to moderators (optional - can be enabled)
        # send_email_notification(moderator, subject, message, link=request_link)
        count += 1

    print(f"🔔 New request notification sent to {count} moderators")


def notify_daily_digest(user):
    """Send daily digest of activity"""
    from django.utils import timezone
    from datetime import timedelta

    last_24h = timezone.now() - timedelta(days=1)

    # Get recent activity
    new_resources = Resource.objects.filter(
        status='approved',
        upload_date__gte=last_24h
    ).count()

    new_requests = ResourceRequest.objects.filter(
        created_at__gte=last_24h
    ).count()

    fulfilled_requests = ResourceRequest.objects.filter(
        fulfilled_at__gte=last_24h
    ).count()

    if new_resources == 0 and new_requests == 0 and fulfilled_requests == 0:
        return  # Nothing to report

    # Get the site URL from settings
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    subject = f"📊 KUHeS Daily Digest - {timezone.now().strftime('%B %d, %Y')}"
    message = f"""
Hello {user.username},

Here's what happened in the last 24 hours:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ACTIVITY SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 📄 New resources: {new_resources}
• 📝 New requests: {new_requests}
• ✅ Fulfilled requests: {fulfilled_requests}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quick Links:
• Browse Resources: {site_url}{reverse('browse_resources')}
• View Requests: {site_url}{reverse('request_list')}
• Your Profile: {site_url}{reverse('profile')}

Stay productive!

- KUHeS Knowledge Bank Team
"""

    send_email_notification(user, subject, message)
    print(f"📧 Daily digest sent to {user.email}")


def notify_new_resource(resource):
    """Notify moderators about a new resource pending approval"""
    # Get ALL moderators and admins - NO FILTERING
    moderators = User.objects.filter(role__in=['moderator', 'senior_moderator', 'admin'])

    # Get the site URL from settings
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    # Build the link
    resource_link = f"{site_url}{reverse('moderator_dashboard')}"

    count = 0
    for moderator in moderators:
        # Notify EVERY moderator, including admins
        subject = f"📥 New Resource Pending Approval: {resource.title}"
        message = f"""
Hello {moderator.username},

A new resource has been uploaded and needs your review.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 TITLE: {resource.title}
👤 UPLOADED BY: {resource.uploader.username}
📁 TYPE: {resource.get_resource_type_display()}
📊 LEVEL: {resource.get_level_display()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ Please review this resource as soon as possible.

Go to Moderator Dashboard: {resource_link}

- KUHeS Knowledge Bank Team
"""

        # Create in-app notification
        create_notification(
            user=moderator,
            notification_type=Notification.RESOURCE_UPLOADED,
            title="📥 New Resource Pending",
            message=f"New {resource.get_resource_type_display()} by {resource.uploader.username} needs review",
            resource=resource
        )

        # Send email
        send_email_notification(moderator, subject, message, link=resource_link)
        count += 1
        print(f"📧 Notification sent to moderator: {moderator.email}")

    print(f"🔔 New resource notification sent to {count} moderators for '{resource.title}'")
    return count

def notify_test(user):
    """Test notification function"""
    subject = "🧪 Test Notification from KUHeS"
    message = """
This is a test notification to verify that the email system is working correctly.

If you received this, everything is set up properly!

- KUHeS Knowledge Bank Team
"""

    create_notification(
        user=user,
        notification_type=Notification.SYSTEM_ANNOUNCEMENT,
        title="🧪 Test Notification",
        message="This is a test notification to verify the system."
    )

    send_email_notification(user, subject, message)
    print(f"🧪 Test notification sent to {user.email}")