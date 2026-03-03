from django.contrib import admin
from .models import (
    User, EmailVerification, PasswordReset,
    Resource, ResourceRequest, Bookmark, Rating,
    Notification, ModeratorSeat, TransferRequest
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'role', 'is_verified', 'is_active']
    list_filter = ['role', 'level', 'is_verified']
    search_fields = ['email', 'username']


@admin.register(ModeratorSeat)
class ModeratorSeatAdmin(admin.ModelAdmin):
    list_display = ['seat_code', 'name', 'current_holder', 'seat_type', 'level', 'programme', 'year', 'status']
    list_filter = ['level', 'seat_type', 'status', 'programme_code']
    search_fields = ['seat_code', 'name', 'programme']
    ordering = ['level', 'programme', 'year']

    actions = ['mark_vacant', 'mark_active']

    def mark_vacant(self, request, queryset):
        queryset.update(status='vacant', current_holder=None)
        self.message_user(request, f"{queryset.count()} seats marked as vacant")

    mark_vacant.short_description = "Mark selected as vacant"

    def mark_active(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} seats marked as active")

    mark_active.short_description = "Mark selected as active"


@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    list_display = ['seat', 'from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['seat__seat_code', 'from_user__email', 'to_user__email']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'uploader', 'status', 'upload_date']
    list_filter = ['status', 'resource_type', 'level']
    search_fields = ['title', 'uploader__email']

    actions = ['approve_resources', 'reject_resources']

    def approve_resources(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} resources approved")

    approve_resources.short_description = "Approve selected resources"

    def reject_resources(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} resources rejected")

    reject_resources.short_description = "Reject selected resources"


@admin.register(ResourceRequest)
class ResourceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'requester', 'status', 'upvotes', 'created_at']
    list_filter = ['status', 'level']
    search_fields = ['title', 'requester__email']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']
    search_fields = ['user__email', 'title']


# Register remaining models
admin.site.register(EmailVerification)
admin.site.register(PasswordReset)
admin.site.register(Bookmark)
admin.site.register(Rating)