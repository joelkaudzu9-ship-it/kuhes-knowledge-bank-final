from django.conf import settings
from django.urls import reverse
from ..models import Notification, ModeratorSeat, User, Resource, ResourceRequest
from ..utils import send_email_notification


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
    return notification


class SmartNotifier:
    """Intelligent notification dispatcher"""

    @staticmethod
    def notify_new_resource(resource):
        """Notify ONLY relevant class reps about new pending resource"""

        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        link = f"{site_url}{reverse('moderator_dashboard')}"

        notified = []

        # Find relevant moderators based on resource level
        if resource.level == 'premed':
            # Pre-Med: Notify class reps + subject lead
            seats = ModeratorSeat.objects.filter(
                level='premed',
                seat_type__in=['class_rep', 'assistant', 'subject_lead'],
                current_holder__isnull=False
            ).select_related('current_holder')

            for seat in seats:
                # If specific subject, prioritize that lead
                if resource.premed_subject and seat.seat_type == 'subject_lead' and seat.subject == resource.premed_subject:
                    SmartNotifier._send_resource_notification(
                        seat.current_holder, resource, link
                    )
                    notified.append(f"Subject Lead: {seat.current_holder.email}")
                elif seat.seat_type in ['class_rep', 'assistant']:
                    SmartNotifier._send_resource_notification(
                        seat.current_holder, resource, link
                    )
                    notified.append(f"Pre-Med Rep: {seat.current_holder.email}")

        elif resource.level == 'undergraduate':
            # Undergraduate: Notify class reps of that program/year
            seats = ModeratorSeat.objects.filter(
                level='undergraduate',
                school=resource.school,
                programme=resource.programme,
                year=resource.year_of_study,
                seat_type__in=['class_rep', 'assistant'],
                current_holder__isnull=False
            ).select_related('current_holder')

            for seat in seats:
                SmartNotifier._send_resource_notification(
                    seat.current_holder, resource, link
                )
                notified.append(f"Class Rep: {seat.current_holder.email}")

        elif resource.level == 'postgraduate':
            # Postgraduate: Notify program rep
            seat = ModeratorSeat.objects.filter(
                level='postgraduate',
                programme=resource.programme,
                year=resource.year_of_study,
                seat_type='class_rep',
                current_holder__isnull=False
            ).select_related('current_holder').first()

            if seat:
                SmartNotifier._send_resource_notification(
                    seat.current_holder, resource, link
                )
                notified.append(f"Program Rep: {seat.current_holder.email}")

        elif resource.level == 'diploma':
            # Diploma: Notify program rep
            seat = ModeratorSeat.objects.filter(
                level='diploma',
                programme=resource.programme,
                year=resource.year_of_study,
                seat_type='class_rep',
                current_holder__isnull=False
            ).select_related('current_holder').first()

            if seat:
                SmartNotifier._send_resource_notification(
                    seat.current_holder, resource, link
                )
                notified.append(f"Diploma Rep: {seat.current_holder.email}")

        # Always notify admins
        admins = User.objects.filter(role='admin')
        for admin in admins:
            SmartNotifier._send_resource_notification(
                admin, resource, link, priority='low'
            )
            notified.append(f"Admin: {admin.email}")

        print(f"📤 New resource notified: {', '.join(notified)}")
        return notified

    @staticmethod
    def notify_new_request(request_obj):
        """Notify ONLY relevant class reps about new request"""

        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        link = f"{site_url}{reverse('request_detail', args=[request_obj.id])}"

        notified = []

        if request_obj.level == 'premed':
            # Pre-Med: Class reps + subject lead
            seats = ModeratorSeat.objects.filter(
                level='premed',
                seat_type__in=['class_rep', 'assistant'],
                current_holder__isnull=False
            ).select_related('current_holder')

            for seat in seats:
                SmartNotifier._send_request_notification(
                    seat.current_holder, request_obj, link
                )
                notified.append(f"Pre-Med Rep: {seat.current_holder.email}")

            # Subject lead if applicable
            if request_obj.premed_subject:
                subject_lead = ModeratorSeat.objects.filter(
                    level='premed',
                    seat_type='subject_lead',
                    subject=request_obj.premed_subject,
                    current_holder__isnull=False
                ).select_related('current_holder').first()

                if subject_lead:
                    SmartNotifier._send_request_notification(
                        subject_lead.current_holder, request_obj, link
                    )
                    notified.append(f"Subject Lead: {subject_lead.current_holder.email}")

        elif request_obj.level == 'undergraduate':
            # Undergraduate: Class reps of that program/year
            seats = ModeratorSeat.objects.filter(
                level='undergraduate',
                school=request_obj.school,
                programme=request_obj.programme,
                year=request_obj.year_of_study,
                seat_type__in=['class_rep', 'assistant'],
                current_holder__isnull=False
            ).select_related('current_holder')

            for seat in seats:
                SmartNotifier._send_request_notification(
                    seat.current_holder, request_obj, link
                )
                notified.append(f"{request_obj.programme} Rep: {seat.current_holder.email}")

        elif request_obj.level == 'postgraduate':
            # Postgraduate: Program rep
            seat = ModeratorSeat.objects.filter(
                level='postgraduate',
                programme=request_obj.programme,
                year=request_obj.year_of_study,
                seat_type='class_rep',
                current_holder__isnull=False
            ).select_related('current_holder').first()

            if seat:
                SmartNotifier._send_request_notification(
                    seat.current_holder, request_obj, link
                )
                notified.append(f"Postgrad Rep: {seat.current_holder.email}")

        elif request_obj.level == 'diploma':
            # Diploma: Program rep
            seat = ModeratorSeat.objects.filter(
                level='diploma',
                programme=request_obj.programme,
                year=request_obj.year_of_study,
                seat_type='class_rep',
                current_holder__isnull=False
            ).select_related('current_holder').first()

            if seat:
                SmartNotifier._send_request_notification(
                    seat.current_holder, request_obj, link
                )
                notified.append(f"Diploma Rep: {seat.current_holder.email}")

        # Notify admins
        admins = User.objects.filter(role='admin')
        for admin in admins:
            SmartNotifier._send_request_notification(
                admin, request_obj, link, priority='low'
            )
            notified.append(f"Admin: {admin.email}")

        print(f"📝 New request notified: {', '.join(notified)}")
        return notified

    @staticmethod
    def notify_resource_approved(resource):
        """Notify ONLY the uploader"""
        user = resource.uploader
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        link = f"{site_url}{reverse('resource_detail', args=[resource.id])}"

        create_notification(
            user=user,
            notification_type=Notification.RESOURCE_APPROVED,
            title="✅ Resource Approved",
            message=f"Your resource '{resource.title}' is now live!",
            resource=resource
        )

        subject = f"✅ Your resource has been approved: {resource.title}"
        message = f"Your resource is now live! View it here: {link}"
        send_email_notification(user, subject, message, link)

        print(f"✅ Approval notified to uploader: {user.email}")

    @staticmethod
    def notify_resource_rejected(resource, reason):
        """Notify ONLY the uploader"""
        user = resource.uploader

        create_notification(
            user=user,
            notification_type=Notification.RESOURCE_REJECTED,
            title="❌ Resource Rejected",
            message=f"Your resource was rejected: {reason[:100]}...",
            resource=resource
        )

        subject = f"❌ Your resource was not approved: {resource.title}"
        message = f"Reason: {reason}"
        send_email_notification(user, subject, message)

        print(f"❌ Rejection notified to uploader: {user.email}")

    @staticmethod
    def notify_request_fulfilled(request_obj, resource):
        """Notify ONLY the requester"""
        user = request_obj.requester
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        link = f"{site_url}{reverse('resource_detail', args=[resource.id])}"

        create_notification(
            user=user,
            notification_type=Notification.REQUEST_FULFILLED,
            title="✅ Request Fulfilled",
            message=f"Your request '{request_obj.title}' has been fulfilled!",
            resource=resource,
            request_obj=request_obj
        )

        subject = f"✅ Your request has been fulfilled: {request_obj.title}"
        message = f"A resource matching your request is now available: {resource.title}"
        send_email_notification(user, subject, message, link)

        print(f"✅ Fulfillment notified to requester: {user.email}")

    @staticmethod
    def notify_request_upvoted(request_obj, upvoter):
        """Notify requester (if not self)"""
        if request_obj.requester == upvoter:
            return

        user = request_obj.requester
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        link = f"{site_url}{reverse('request_detail', args=[request_obj.id])}"

        create_notification(
            user=user,
            notification_type=Notification.REQUEST_UPVOTED,
            title="👍 Request Upvoted",
            message=f"{upvoter.username} upvoted your request",
            request_obj=request_obj
        )

        print(f"👍 Upvote notified to requester: {user.email}")

    @staticmethod
    def _send_resource_notification(user, resource, link, priority='normal'):
        """Helper for resource notifications"""
        create_notification(
            user=user,
            notification_type=Notification.RESOURCE_UPLOADED,
            title="📥 New Pending Resource",
            message=f"New {resource.get_resource_type_display()}: {resource.title[:50]}...",
            resource=resource
        )

        if priority == 'normal':
            subject = f"📥 New Resource Needs Review: {resource.title[:30]}..."
            message = f"""
A new {resource.get_resource_type_display()} needs your review.

Title: {resource.title}
Uploader: {resource.uploader.username}
Level: {resource.get_level_display()}

View in moderator dashboard: {link}
"""
            send_email_notification(user, subject, message, link)

    @staticmethod
    def _send_request_notification(user, request_obj, link, priority='normal'):
        """Helper for request notifications"""
        create_notification(
            user=user,
            notification_type=Notification.REQUEST_CREATED,
            title="📝 New Request",
            message=f"{request_obj.title[:50]}... by {request_obj.requester.username}",
            request_obj=request_obj
        )

        if priority == 'normal':
            subject = f"📝 New Request: {request_obj.title[:30]}..."
            message = f"""
A new request needs attention:

Title: {request_obj.title}
Requester: {request_obj.requester.username}
Urgency: {request_obj.get_urgency_display()}

View request: {link}
"""
            send_email_notification(user, subject, message, link)