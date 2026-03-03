from .models import Notification

def notification_count(request):
    """Add notification count to all templates"""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return {
            'unread_notifications': unread_count
        }
    return {'unread_notifications': 0}