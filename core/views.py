from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
import logging

from .models import (
    User, EmailVerification, PasswordReset, Resource,
    ResourceRequest, RequestUpvote, Bookmark, Rating,
    Notification, ModeratorSeat, TransferRequest
)
from .forms import ResourceUploadForm, ResourceRequestForm
from .utils import send_verification_email, send_password_reset_email
from .notifications.smart_notify import SmartNotifier

logger = logging.getLogger(__name__)


# Add this debug view temporarily
def debug_view(request):
    """Debug endpoint to test if Django is working"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_count = User.objects.count()
        return HttpResponse(f"✅ Django is working! Users: {user_count}")
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}", status=500)


def index(request):
    """Home page"""
    return render(request, 'core/index.html')


def register(request):
    """User registration with email verification"""
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Basic validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')

        if not email.endswith('@kuhes.ac.mw'):
            messages.error(request, 'Only @kuhes.ac.mw email addresses are allowed!')
            return redirect('register')

        # Check if user exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken!')
            return redirect('register')

        # Create user (inactive until email verified)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        user.is_active = False
        user.save()

        # Send verification email
        try:
            send_verification_email(user, request)
            messages.success(request, 'Account created! Please check your email to verify your account.')
        except Exception as e:
            # If email fails, create token and show link for development
            verification = EmailVerification.objects.create(user=user)
            verification_link = request.build_absolute_uri(
                reverse('verify_email', args=[str(verification.token)])
            )
            messages.warning(
                request,
                f'⚠️ Email could not be sent. Use this link to verify: {verification_link}'
            )
            logger.error(f"Email sending failed: {e}")

        return redirect('login')

    return render(request, 'core/register.html')


def verify_email(request, token):
    """Verify user email with token"""
    verification = get_object_or_404(EmailVerification, token=token)

    if verification.is_valid():
        user = verification.user
        user.is_active = True
        user.is_verified = True
        user.save()

        # Delete used token
        verification.delete()

        messages.success(request, 'Email verified! You can now log in.')
    else:
        messages.error(request, 'Verification link has expired. Please register again.')
        verification.delete()

    return redirect('login')


def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, is_verified=False)
            send_verification_email(user, request)
            messages.success(request, 'Verification email sent! Please check your inbox.')
        except User.DoesNotExist:
            messages.error(request, 'No unverified account found with that email.')

    return render(request, 'core/resend_verification.html')


def forgot_password(request):
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        logger.info(f"Password reset requested for email: {email}")

        try:
            # Check if user exists
            user = User.objects.get(email=email, is_active=True)
            logger.info(f"User found: {user.username} (ID: {user.id})")

            # Try to send email
            try:
                reset = send_password_reset_email(user, request)
                logger.info(f"Password reset email sent. Token: {reset.token}")
                messages.success(request, 'Password reset link sent to your email!')
            except Exception as email_error:
                logger.error(f"Email sending failed: {email_error}")

                # For development, show the link anyway
                if settings.DEBUG:
                    reset = PasswordReset.objects.create(user=user)
                    reset_link = request.build_absolute_uri(
                        reverse('reset_password', args=[str(reset.token)])
                    )
                    messages.warning(
                        request,
                        f'⚠️ DEVELOPMENT MODE: Use this link: {reset_link}'
                    )
                else:
                    messages.error(request, 'Could not send email. Please try again later.')

        except User.DoesNotExist:
            logger.warning(f"User not found with email: {email}")
            # Don't reveal that email doesn't exist for security
            messages.success(request, 'If an account exists with that email, a reset link has been sent.')
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            messages.error(request, 'An error occurred. Please try again.')

        return redirect('login')

    return render(request, 'core/forgot_password.html')


def reset_password(request, token):
    """Reset password using token"""
    reset = get_object_or_404(PasswordReset, token=token)

    if not reset.is_valid():
        messages.error(request, 'Password reset link has expired. Please request a new one.')
        reset.delete()
        return redirect('forgot_password')

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('reset_password', token=token)

        # Set new password
        user = reset.user
        user.set_password(password1)
        user.save()

        # Delete used token
        reset.delete()

        messages.success(request, 'Password reset successfully! You can now log in with your new password.')
        return redirect('login')

    return render(request, 'core/reset_password.html', {'token': token})


def custom_logout(request):
    """Custom logout view - prevents back button from showing logged-in pages"""
    logout(request)

    # Clear session data
    request.session.flush()

    messages.success(request, 'You have been successfully logged out.')

    # Create response with cache-control headers
    response = redirect('index')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def form_valid(self, form):
        try:
            messages.success(self.request, f'Welcome back, {form.get_user().username}!')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            messages.error(self.request, 'An error occurred during login.')
            return redirect('login')

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid email or password. Please try again.')
        return super().form_invalid(form)


@login_required
def dashboard(request):
    """User dashboard"""
    return render(request, 'core/dashboard.html', {'user': request.user})


@login_required
def profile(request):
    """Profile page - View and Edit"""
    if request.method == 'POST':
        # Update user fields
        user = request.user
        user.level = request.POST.get('level')
        user.school = request.POST.get('school')
        user.programme = request.POST.get('programme')
        user.year_of_study = request.POST.get('year_of_study')
        user.graduation_year = request.POST.get('graduation_year')
        user.premed_cohort = request.POST.get('premed_cohort')
        user.intended_programme = request.POST.get('intended_programme')
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'core/profile.html', {'user': request.user})


@login_required
def upload_resource(request):
    """Upload a resource"""
    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploader = request.user
            resource.status = 'pending'

            # Handle video vs file
            if resource.resource_type == 'video':
                resource.file = None  # No file for videos
            else:
                resource.video_link = None  # No link for files

            resource.save()

            # Increment upload count for user
            user = request.user
            user.upload_count += 1
            user.save()

            # Notify relevant reps
            SmartNotifier.notify_new_resource(resource)

            if resource.resource_type == 'video':
                messages.success(request, 'Video link uploaded successfully! It will be reviewed by your class reps.')
            else:
                messages.success(request, 'File uploaded successfully! It will be reviewed by your class reps.')

            return redirect('my_uploads')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ResourceUploadForm()

    return render(request, 'core/upload.html', {'form': form})


@login_required
def moderator_dashboard(request):
    """Moderator dashboard - shows ONLY resources from moderator's class"""

    # Check if user is moderator
    if request.user.role not in ['moderator', 'senior_moderator', 'admin']:
        messages.error(request, 'You do not have moderator access.')
        return redirect('dashboard')

    user = request.user

    # Get user's moderator seat
    user_seat = ModeratorSeat.objects.filter(current_holder=user).first()

    # Build query filter based on user's role and seat
    resource_filter = Q()

    if user.role == 'admin':
        # Admins see everything
        resource_filter = Q()
        scope = "ALL RESOURCES"
    elif user.role == 'senior_moderator':
        # Senior moderators see their school
        if user.school:
            resource_filter &= Q(school=user.school)
            scope = f"SCHOOL: {user.get_school_display()}"
        else:
            resource_filter = Q()
            scope = "ALL RESOURCES"
    elif user_seat:
        # Class reps see ONLY their specific class
        if user_seat.level == 'premed':
            if user_seat.seat_type == 'subject_lead':
                # Subject lead sees their subject only
                resource_filter &= Q(level='premed', premed_subject=user_seat.subject)
                scope = f"PRE-MED {user_seat.get_subject_display()}"
            else:
                # Pre-Med class rep sees all Pre-Med
                resource_filter &= Q(level='premed')
                scope = "PRE-MED"

        elif user_seat.level == 'undergraduate':
            # Undergraduate rep sees their specific program/year
            resource_filter &= Q(
                level='undergraduate',
                school=user_seat.school,
                programme=user_seat.programme,
                year_of_study=user_seat.year
            )
            scope = f"{user_seat.programme} YEAR {user_seat.year}"

        elif user_seat.level in ['postgraduate', 'diploma']:
            # Postgrad/Diploma rep sees their program
            resource_filter &= Q(
                level=user_seat.level,
                programme=user_seat.programme,
                year_of_study=user_seat.year
            )
            scope = f"{user_seat.programme} YEAR {user_seat.year}"
        else:
            scope = "NO CLASS ASSIGNED"
    else:
        # Moderators without seats see nothing (shouldn't happen)
        resource_filter = Q(id__in=[])  # Empty queryset
        scope = "NO CLASS ASSIGNED"

    # Get pending resources for their class ONLY
    pending_resources = Resource.objects.filter(
        resource_filter,
        status='pending'
    ).order_by('upload_date')

    # Get statistics (scoped)
    total_pending = pending_resources.count()
    total_approved = Resource.objects.filter(resource_filter, status='approved').count()
    total_rejected = Resource.objects.filter(resource_filter, status='rejected').count()

    # Get recent activity (scoped)
    recent_approvals = Resource.objects.filter(
        resource_filter,
        status='approved',
        approval_date__isnull=False
    ).order_by('-approval_date')[:10]

    # Get flagged resources (scoped)
    flagged_resources = Resource.objects.filter(
        resource_filter,
        status='flagged'
    ).order_by('-updated_at')[:5]

    context = {
        'pending_resources': pending_resources,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'recent_approvals': recent_approvals,
        'flagged_resources': flagged_resources,
        'scope': scope,
        'user_seat': user_seat,
    }

    return render(request, 'core/moderator/dashboard.html', context)


@login_required
def approve_resource(request, resource_id):
    """Approve a pending resource"""
    # Check if user is moderator
    if request.user.role not in ['moderator', 'senior_moderator', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    # Get the resource
    try:
        resource = Resource.objects.get(id=resource_id, status='pending')
    except Resource.DoesNotExist:
        messages.error(request, 'Resource not found or already processed.')
        return redirect('moderator_dashboard')

    # Approve the resource
    resource.status = 'approved'
    resource.approved_by = request.user
    resource.approval_date = timezone.now()
    resource.save()

    # Notify uploader
    SmartNotifier.notify_resource_approved(resource)

    messages.success(request, f'✅ Resource "{resource.title}" has been approved and is now public!')

    return redirect('moderator_dashboard')


@login_required
def reject_resource(request, resource_id):
    """Reject a pending resource with reason"""
    # Check if user is moderator
    if request.user.role not in ['moderator', 'senior_moderator', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    # Get the resource
    try:
        resource = Resource.objects.get(id=resource_id, status='pending')
    except Resource.DoesNotExist:
        messages.error(request, 'Resource not found or already processed.')
        return redirect('moderator_dashboard')

    if request.method == 'POST':
        reason = request.POST.get('reason', '')

        if not reason:
            messages.error(request, 'Please provide a reason for rejection.')
            return render(request, 'core/moderator/reject.html', {'resource': resource})

        # Reject the resource
        resource.status = 'rejected'
        resource.rejection_reason = reason
        resource.approved_by = request.user
        resource.approval_date = timezone.now()
        resource.save()

        # Notify uploader
        SmartNotifier.notify_resource_rejected(resource, reason)

        messages.success(request, f'❌ Resource "{resource.title}" has been rejected.')

        return redirect('moderator_dashboard')

    return render(request, 'core/moderator/reject.html', {'resource': resource})


@login_required
def request_list(request):
    """View all resource requests - UNIVERSAL (everyone sees all)"""

    # Get filter parameters
    status = request.GET.get('status', 'open')
    level = request.GET.get('level', '')
    sort = request.GET.get('sort', '-upvotes')

    # Base queryset - NO FILTERS! Everyone sees all requests
    requests_queryset = ResourceRequest.objects.all()

    # Apply filters (user-selected)
    if status:
        requests_queryset = requests_queryset.filter(status=status)
    if level:
        requests_queryset = requests_queryset.filter(level=level)

    # Apply sorting
    if sort == 'newest':
        requests_queryset = requests_queryset.order_by('-created_at')
    elif sort == 'oldest':
        requests_queryset = requests_queryset.order_by('created_at')
    elif sort == 'urgent':
        requests_queryset = requests_queryset.order_by('-urgency', '-upvotes')
    else:
        requests_queryset = requests_queryset.order_by('-upvotes', '-created_at')

    # Check if current user has upvoted each request
    for req in requests_queryset:
        req.user_upvoted = RequestUpvote.objects.filter(
            user=request.user,
            request=req
        ).exists()

    # Get counts
    counts = {
        'open': ResourceRequest.objects.filter(status='open').count(),
        'in_progress': ResourceRequest.objects.filter(status='in_progress').count(),
        'fulfilled': ResourceRequest.objects.filter(status='fulfilled').count(),
    }

    context = {
        'requests': requests_queryset,
        'counts': counts,
        'current_status': status,
        'current_level': level,
        'current_sort': sort,
    }

    return render(request, 'core/requests/list.html', context)


@login_required
def create_request(request):
    """Create a new resource request - only for user's own class"""

    if request.method == 'POST':
        form = ResourceRequestForm(request.POST)
        if form.is_valid():
            resource_request = form.save(commit=False)
            resource_request.requester = request.user

            # Auto-fill based on user's profile
            user = request.user

            # Pre-Med students can only create Pre-Med requests
            if user.level == 'premed':
                resource_request.level = 'premed'
                # They can choose subject, but that's it

            # Undergraduate students can only create requests for their program/year
            elif user.level == 'undergraduate':
                resource_request.level = 'undergraduate'
                resource_request.school = user.school
                resource_request.programme = user.programme
                resource_request.year_of_study = user.year_of_study

            # Postgraduate students
            elif user.level == 'postgraduate':
                resource_request.level = 'postgraduate'
                resource_request.programme = user.programme
                resource_request.year_of_study = user.year_of_study

            # Diploma students
            elif user.level == 'diploma':
                resource_request.level = 'diploma'
                resource_request.programme = user.programme
                resource_request.year_of_study = user.year_of_study

            resource_request.save()

            # Notify relevant reps
            SmartNotifier.notify_new_request(resource_request)

            messages.success(request, 'Your request has been posted!')
            return redirect('request_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Pre-fill form with user's class info
        initial_data = {}
        if request.user.level == 'premed':
            initial_data['level'] = 'premed'
        elif request.user.level == 'undergraduate':
            initial_data['level'] = 'undergraduate'
            initial_data['school'] = request.user.school
            initial_data['programme'] = request.user.programme
            initial_data['year_of_study'] = request.user.year_of_study
        # ... etc for other levels

        form = ResourceRequestForm(initial=initial_data)

    return render(request, 'core/requests/create.html', {'form': form})


@login_required
def request_detail(request, request_id):
    """View request details"""
    resource_request = get_object_or_404(ResourceRequest, id=request_id)

    # Check if user has upvoted
    user_upvoted = RequestUpvote.objects.filter(
        user=request.user,
        request=resource_request
    ).exists()

    # Get similar requests
    similar_requests = ResourceRequest.objects.filter(
        level=resource_request.level,
        status='open'
    ).exclude(id=resource_request.id)[:5]

    # Check if user can moderate
    can_moderate = request.user.role in ['moderator', 'senior_moderator', 'admin']

    context = {
        'request': resource_request,
        'user_upvoted': user_upvoted,
        'similar_requests': similar_requests,
        'can_moderate': can_moderate,
    }

    return render(request, 'core/requests/detail.html', context)


@login_required
def upvote_request(request, request_id):
    """Upvote ANY request - universal support"""
    resource_request = get_object_or_404(ResourceRequest, id=request_id)

    upvote, created = RequestUpvote.objects.get_or_create(
        user=request.user,
        request=resource_request
    )

    if created:
        resource_request.upvotes += 1
        resource_request.save()

        # Notify requester
        if resource_request.requester != request.user:
            SmartNotifier.notify_request_upvoted(resource_request, request.user)

        messages.success(request, 'Request upvoted!')
    else:
        upvote.delete()
        resource_request.upvotes -= 1
        resource_request.save()
        messages.success(request, 'Upvote removed.')

    return redirect('request_detail', request_id=request_id)


@login_required
def mark_fulfilled(request, request_id):
    """Mark a request as fulfilled (only for requester or moderator)"""
    resource_request = get_object_or_404(ResourceRequest, id=request_id)

    # Check permission
    if request.user != resource_request.requester and request.user.role not in ['moderator', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('request_detail', request_id=request_id)

    if request.method == 'POST':
        resource_id = request.POST.get('resource_id')
        if resource_id:
            try:
                resource = Resource.objects.get(id=resource_id)

                # Update request
                resource_request.status = 'fulfilled'
                resource_request.fulfilled_by = resource
                resource_request.fulfilled_at = timezone.now()
                resource_request.save()

                # Notify requester
                SmartNotifier.notify_request_fulfilled(resource_request, resource)

                messages.success(request, 'Request marked as fulfilled! The requester has been notified.')

            except Resource.DoesNotExist:
                messages.error(request, 'Resource not found.')
        else:
            messages.error(request, 'Please provide the resource ID.')

    return redirect('request_detail', request_id=request_id)


@login_required
def my_requests(request):
    """View user's own requests"""
    user_requests = ResourceRequest.objects.filter(requester=request.user).order_by('-created_at')
    return render(request, 'core/requests/my_requests.html', {'requests': user_requests})


@login_required
def analytics_dashboard(request):
    """Analytics dashboard - shows data based on user's role and class"""

    # Base permission check
    if request.user.role not in ['moderator', 'senior_moderator', 'admin']:
        messages.error(request, 'Access denied. Moderator privileges required.')
        return redirect('dashboard')

    today = timezone.now()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)

    # ===========================================
    # DETERMINE USER'S SCOPE
    # ===========================================
    user = request.user
    is_admin = user.role == 'admin'
    is_senior = user.role == 'senior_moderator'

    # Get user's moderator seat (if any)
    user_seat = ModeratorSeat.objects.filter(current_holder=user).first()

    # ===========================================
    # BUILD FILTERS BASED ON USER ROLE
    # ===========================================
    resource_filters = Q()
    request_filters = Q()
    user_filters = Q()

    if is_admin:
        # Admins see everything
        scope = "ALL UNIVERSITY"

    elif is_senior:
        # Senior moderators see their school/program
        scope = f"SENIOR MODERATOR - {user.get_school_display() if user.school else 'All'}"
        if user.school:
            resource_filters &= Q(school=user.school)
            request_filters &= Q(school=user.school)
            user_filters &= Q(school=user.school)

    elif user_seat:
        # Class reps see only their specific class
        if user_seat.level == 'premed':
            if user_seat.seat_type == 'subject_lead':
                # Subject lead sees only their subject
                scope = f"PRE-MED {user_seat.get_subject_display()} LEAD"
                resource_filters &= Q(level='premed', premed_subject=user_seat.subject)
                request_filters &= Q(level='premed', premed_subject=user_seat.subject)
                user_filters &= Q(level='premed')
            else:
                # Pre-Med class rep sees all Pre-Med
                scope = "PRE-MED CLASS REP"
                resource_filters &= Q(level='premed')
                request_filters &= Q(level='premed')
                user_filters &= Q(level='premed')

        elif user_seat.level == 'undergraduate':
            # Undergraduate rep sees their specific program/year
            scope = f"{user_seat.programme} YEAR {user_seat.year} REP"
            resource_filters &= Q(
                level='undergraduate',
                school=user_seat.school,
                programme=user_seat.programme,
                year_of_study=user_seat.year
            )
            request_filters &= Q(
                level='undergraduate',
                school=user_seat.school,
                programme=user_seat.programme,
                year_of_study=user_seat.year
            )
            user_filters &= Q(
                level='undergraduate',
                school=user_seat.school,
                programme=user_seat.programme,
                year_of_study=user_seat.year
            )

        elif user_seat.level in ['postgraduate', 'diploma']:
            # Postgrad/Diploma rep sees their program
            scope = f"{user_seat.programme} YEAR {user_seat.year} REP"
            resource_filters &= Q(
                level=user_seat.level,
                programme=user_seat.programme,
                year_of_study=user_seat.year
            )
            request_filters &= Q(
                level=user_seat.level,
                programme=user_seat.programme,
                year_of_study=user_seat.year
            )
            user_filters &= Q(
                level=user_seat.level,
                programme=user_seat.programme,
                year_of_study=user_seat.year
            )
        else:
            scope = "GENERAL MODERATOR (no specific class)"
    else:
        # Fallback for moderators without seats
        scope = "GENERAL MODERATOR (no specific class)"

    # ===========================================
    # APPLY FILTERS TO ALL QUERIES
    # ===========================================

    # User stats (filtered)
    if is_admin:
        total_users = User.objects.count()
        active_users = User.objects.filter(last_active__gte=last_30_days).count()
        new_users_7d = User.objects.filter(date_joined__gte=last_7_days).count()
    else:
        total_users = User.objects.filter(user_filters).count()
        active_users = User.objects.filter(user_filters, last_active__gte=last_30_days).count()
        new_users_7d = User.objects.filter(user_filters, date_joined__gte=last_7_days).count()

    # Resource stats (filtered)
    resources = Resource.objects.filter(resource_filters)
    total_resources = resources.count()
    approved_resources = resources.filter(status='approved').count()
    pending_resources = resources.filter(status='pending').count()

    download_sum = resources.aggregate(total=Sum('download_count'))['total']
    total_downloads = download_sum if download_sum is not None else 0

    view_sum = resources.aggregate(total=Sum('view_count'))['total']
    total_views = view_sum if view_sum is not None else 0

    # Request stats (filtered)
    requests_queryset = ResourceRequest.objects.filter(request_filters)
    total_requests = requests_queryset.count()
    open_requests = requests_queryset.filter(status='open').count()
    fulfilled_requests = requests_queryset.filter(status='fulfilled').count()

    # Top Resources (within scope)
    top_resources = resources.filter(status='approved').order_by('-download_count')[:10]

    # Top Uploaders (within scope)
    top_uploaders = User.objects.filter(
        user_filters,
        uploaded_resources__in=resources.filter(status='approved')
    ).annotate(
        resource_count=Count('uploaded_resources')
    ).filter(resource_count__gt=0).order_by('-resource_count')[:10]

    # Resources by Type (within scope)
    resource_types = []
    for type_code, type_name in Resource.RESOURCE_TYPES:
        count = resources.filter(resource_type=type_code, status='approved').count()
        if count > 0:
            resource_types.append({
                'code': type_code,
                'name': type_name,
                'count': count
            })

    # Recent Activity (within scope)
    recent_uploads = resources.filter(status='approved').order_by('-upload_date')[:10]
    recent_requests = requests_queryset.order_by('-created_at')[:10]

    # Daily Activity (last 7 days) - within scope
    daily_downloads = []
    daily_uploads = []
    dates = []

    for i in range(6, -1, -1):
        date = today.date() - timedelta(days=i)
        dates.append(date.strftime('%a'))

        day_start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(date, datetime.max.time()))

        # Downloads on this day (simplified)
        day_resources = resources.filter(upload_date__lte=day_end)
        downloads = sum(r.download_count for r in day_resources)
        daily_downloads.append(downloads)

        # Uploads on this day
        uploads = resources.filter(upload_date__range=[day_start, day_end]).count()
        daily_uploads.append(uploads)

    # ===========================================
    # PREPARE CONTEXT
    # ===========================================
    context = {
        # Scope info
        'scope': scope,
        'is_admin': is_admin,
        'is_senior': is_senior,
        'user_seat': user_seat,

        # Overview stats
        'total_users': total_users,
        'active_users': active_users,
        'new_users_7d': new_users_7d,
        'total_resources': total_resources,
        'approved_resources': approved_resources,
        'pending_resources': pending_resources,
        'total_downloads': total_downloads,
        'total_views': total_views,
        'total_requests': total_requests,
        'open_requests': open_requests,
        'fulfilled_requests': fulfilled_requests,

        # Lists
        'top_resources': top_resources,
        'top_uploaders': top_uploaders,
        'recent_uploads': recent_uploads,
        'recent_requests': recent_requests,

        # Charts
        'resource_types': resource_types,
        'dates': dates,
        'daily_downloads': daily_downloads,
        'daily_uploads': daily_uploads,
    }

    return render(request, 'core/analytics/dashboard.html', context)


@login_required
def moderate_request(request, request_id):
    """Moderator actions on requests"""
    if request.user.role not in ['moderator', 'senior_moderator', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('request_detail', request_id=request_id)

    resource_request = get_object_or_404(ResourceRequest, id=request_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'pin':
            resource_request.is_pinned = not resource_request.is_pinned
            messages.success(request, f'Request {"pinned" if resource_request.is_pinned else "unpinned"}!')

        elif action == 'priority':
            try:
                priority = int(request.POST.get('priority', 0))
                resource_request.priority = priority
                messages.success(request, f'Priority set to {priority}!')
            except ValueError:
                messages.error(request, 'Invalid priority value')

        elif action == 'notes':
            notes = request.POST.get('notes', '')
            resource_request.moderator_notes = notes
            messages.success(request, 'Moderator notes updated!')

        elif action == 'merge':
            duplicate_id = request.POST.get('duplicate_id')
            try:
                duplicate = ResourceRequest.objects.get(id=duplicate_id)
                # Transfer upvotes from duplicate to main
                resource_request.upvotes += duplicate.upvotes
                # Mark duplicate as closed
                duplicate.status = 'closed'
                duplicate.save()
                resource_request.save()
                messages.success(request, f'Merged with request #{duplicate_id}')
            except ResourceRequest.DoesNotExist:
                messages.error(request, 'Duplicate request not found')

        elif action == 'delete':
            if request.user.role == 'admin':  # Only admin can delete
                title = resource_request.title
                resource_request.delete()
                messages.success(request, f'Request "{title}" deleted')
                return redirect('request_list')
            else:
                messages.error(request, 'Only admins can delete requests')

        resource_request.save()

    return redirect('request_detail', request_id=request_id)


@login_required
def bulk_approve(request):
    """Approve multiple resources at once"""
    if request.user.role not in ['moderator', 'senior_moderator', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        resource_ids = request.POST.getlist('resource_ids')
        if resource_ids:
            resources = Resource.objects.filter(id__in=resource_ids, status='pending')
            count = resources.count()
            resources.update(
                status='approved',
                approved_by=request.user,
                approval_date=timezone.now()
            )
            messages.success(request, f'✅ {count} resources approved successfully!')

    return redirect('moderator_dashboard')


@login_required
def notifications(request):
    """View user notifications"""
    notifications_list = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Mark all as read
    if request.GET.get('mark_read'):
        notifications_list.update(is_read=True)
        messages.success(request, 'All notifications marked as read')
        return redirect('notifications')

    # Get counts
    unread_count = notifications_list.filter(is_read=False).count()

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(notifications_list, 20)
    page = request.GET.get('page')
    notifications_page = paginator.get_page(page)

    context = {
        'notifications': notifications_page,
        'unread_count': unread_count,
    }

    return render(request, 'core/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    # Handle different notification types appropriately
    if notification.resource:
        # Only redirect to resource detail if it's approved
        if notification.resource.status == 'approved':
            return redirect('resource_detail', resource_id=notification.resource.id)
        else:
            # If resource is pending/rejected, go to my_uploads instead
            messages.info(request, 'This resource is still pending approval or was rejected.')
            return redirect('my_uploads')
    elif notification.request:
        return redirect('request_detail', request_id=notification.request.id)
    else:
        return redirect('notifications')


@login_required
def my_uploads(request):
    """View user's uploads"""
    uploads = Resource.objects.filter(uploader=request.user).order_by('-upload_date')
    return render(request, 'core/my_uploads.html', {'uploads': uploads})


@login_required
def browse_resources(request):
    """Browse all approved resources with advanced search"""
    resources = Resource.objects.filter(status='approved')

    # Get search parameters
    query = request.GET.get('q', '')
    resource_type = request.GET.get('type', '')
    level = request.GET.get('level', '')
    subject = request.GET.get('subject', '')
    school = request.GET.get('school', '')
    year = request.GET.get('year', '')
    sort = request.GET.get('sort', '-upload_date')  # Default: newest first

    # Build search filters
    filters = Q()

    if query:
        filters &= Q(title__icontains=query) | \
                   Q(description__icontains=query) | \
                   Q(tags__icontains=query) | \
                   Q(lecturer__icontains=query) | \
                   Q(course_code__icontains=query)

    if resource_type:
        filters &= Q(resource_type=resource_type)

    if level:
        filters &= Q(level=level)

        # Level-specific filters
        if level == 'premed' and subject:
            filters &= Q(premed_subject=subject)
        elif level == 'undergraduate':
            if school:
                filters &= Q(school=school)
            if year:
                filters &= Q(year_of_study=year)

    # Apply filters
    resources = resources.filter(filters)

    # Apply sorting
    if sort == 'downloads':
        resources = resources.order_by('-download_count')
    elif sort == 'title':
        resources = resources.order_by('title')
    else:  # default: newest
        resources = resources.order_by('-upload_date')

    # Get unique values for filters
    subjects = Resource.SUBJECT_CHOICES
    schools = User.SCHOOL_CHOICES
    years = range(1, 7)

    context = {
        'resources': resources,
        'query': query,
        'selected_type': resource_type,
        'selected_level': level,
        'selected_subject': subject,
        'selected_school': school,
        'selected_year': year,
        'selected_sort': sort,
        'subjects': subjects,
        'schools': schools,
        'years': years,
    }

    return render(request, 'core/browse.html', context)


@login_required
def download_resource(request, resource_id):
    """Download resource with proper permission checks"""

    logger.info(f"Download requested for resource ID: {resource_id}")

    # First, try to get the resource without status filter
    try:
        resource = Resource.objects.get(id=resource_id)
        logger.info(f"Resource found: {resource.title} (Status: {resource.status})")
    except Resource.DoesNotExist:
        logger.error(f"Resource {resource_id} not found in database")
        messages.error(request, 'Resource not found.')
        return redirect('browse_resources')
    except Exception as e:
        logger.error(f"Error fetching resource: {e}")
        messages.error(request, 'Error accessing resource.')
        return redirect('browse_resources')

    user = request.user

    # ===========================================
    # CHECK IF FILE EXISTS
    # ===========================================
    if not resource.file:
        messages.error(request, 'This resource has no file attached.')
        return redirect('resource_detail', resource_id=resource_id)

    # ===========================================
    # DOWNLOAD PERMISSION CHECKS
    # ===========================================
    can_download = False
    reason = ""

    # Case 1: Approved resource - anyone can download
    if resource.status == 'approved':
        can_download = True
        reason = "approved resource"

    # Case 2: Admin - can download anything
    elif user.role == 'admin':
        can_download = True
        reason = "admin access"

    # Case 3: Uploader - can download their own files
    elif user == resource.uploader:
        can_download = True
        reason = "uploader access"

    # Case 4: Moderator - check class access
    elif user.role in ['moderator', 'senior_moderator']:
        # Get user's moderator seat
        try:
            user_seat = ModeratorSeat.objects.filter(current_holder=user).first()

            if user_seat:
                # Check if this resource belongs to their class
                if user_seat.level == 'premed':
                    if user_seat.seat_type == 'subject_lead':
                        # Subject lead sees their subject
                        has_access = (
                                resource.level == 'premed' and
                                resource.premed_subject == user_seat.subject
                        )
                        if has_access:
                            can_download = True
                            reason = f"subject lead access ({user_seat.get_subject_display()})"
                    else:
                        # Pre-Med class rep sees all Pre-Med
                        has_access = (resource.level == 'premed')
                        if has_access:
                            can_download = True
                            reason = "pre-med class rep access"

                elif user_seat.level == 'undergraduate':
                    # Undergraduate rep sees their specific program/year
                    has_access = (
                            resource.level == 'undergraduate' and
                            resource.school == user_seat.school and
                            resource.programme == user_seat.programme and
                            resource.year_of_study == user_seat.year
                    )
                    if has_access:
                        can_download = True
                        reason = f"{user_seat.programme} year {user_seat.year} rep access"

                elif user_seat.level in ['postgraduate', 'diploma']:
                    # Postgrad/Diploma rep sees their program
                    has_access = (
                            resource.level == user_seat.level and
                            resource.programme == user_seat.programme and
                            resource.year_of_study == user_seat.year
                    )
                    if has_access:
                        can_download = True
                        reason = f"{user_seat.programme} rep access"
        except Exception as e:
            logger.error(f"Error checking moderator seat: {e}")

    # ===========================================
    # DENY ACCESS IF NOT PERMITTED
    # ===========================================
    if not can_download:
        logger.warning(f"Download denied for user {user.email} - no permission")
        messages.error(request, 'You do not have permission to download this resource.')
        return redirect('resource_detail', resource_id=resource_id)

    logger.info(f"Download permitted: {reason}")

    # ===========================================
    # INCREMENT DOWNLOAD COUNTS (only for approved)
    # ===========================================
    try:
        if resource.status == 'approved':
            resource.download_count += 1
            resource.save()

            if resource.uploader:
                resource.uploader.download_count += 1
                resource.uploader.save()
            logger.info(f"Download count incremented")
    except Exception as e:
        logger.warning(f"Could not increment download count: {e}")
        # Continue anyway - don't block download for counting error

    # ===========================================
    # SERVE THE FILE
    # ===========================================
    try:
        logger.info(f"Serving file: {resource.file.url}")
        return redirect(resource.file.url)
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        messages.error(request, 'Error accessing file.')
        return redirect('resource_detail', resource_id=resource_id)


@login_required
def resource_detail(request, resource_id):
    """View resource details with proper permission checks"""

    try:
        resource = Resource.objects.get(id=resource_id)
    except Resource.DoesNotExist:
        messages.error(request, 'Resource not found.')
        return redirect('browse_resources')

    user = request.user

    # ===========================================
    # PERMISSION CHECKS
    # ===========================================
    can_view = False
    can_download = False
    can_interact = False  # bookmark, rate, etc.

    # Case 1: Resource is APPROVED - anyone can view/download/interact
    if resource.status == 'approved':
        can_view = True
        can_download = True
        can_interact = True

    # Case 2: User is ADMIN - can do everything
    elif user.role == 'admin':
        can_view = True
        can_download = True
        can_interact = True  # Admins can do everything

    # Case 3: User is the UPLOADER - can view their own pending/rejected
    elif user == resource.uploader:
        can_view = True
        can_download = True  # Uploader can download their own files
        can_interact = False  # But cannot bookmark/rate own pending resources

    # Case 4: User is a MODERATOR - check if they have permission for this class
    elif user.role in ['moderator', 'senior_moderator']:
        # Get user's moderator seat
        user_seat = ModeratorSeat.objects.filter(current_holder=user).first()

        if user_seat:
            # Check if this resource belongs to their class
            has_class_access = False

            if user_seat.level == 'premed':
                if user_seat.seat_type == 'subject_lead':
                    # Subject lead sees their subject
                    has_class_access = (
                            resource.level == 'premed' and
                            resource.premed_subject == user_seat.subject
                    )
                else:
                    # Pre-Med class rep sees all Pre-Med
                    has_class_access = (resource.level == 'premed')

            elif user_seat.level == 'undergraduate':
                # Undergraduate rep sees their specific program/year
                has_class_access = (
                        resource.level == 'undergraduate' and
                        resource.school == user_seat.school and
                        resource.programme == user_seat.programme and
                        resource.year_of_study == user_seat.year
                )

            elif user_seat.level in ['postgraduate', 'diploma']:
                # Postgrad/Diploma rep sees their program
                has_class_access = (
                        resource.level == user_seat.level and
                        resource.programme == user_seat.programme and
                        resource.year_of_study == user_seat.year
                )

            if has_class_access:
                can_view = True
                can_download = True  # Moderators can download to review
                can_interact = False  # But cannot bookmark/rate pending resources

    # ===========================================
    # DENY ACCESS IF NOT PERMITTED
    # ===========================================
    if not can_view:
        messages.error(request, 'You do not have permission to view this resource.')
        return redirect('browse_resources')

    # Increment view count only for approved resources
    if resource.status == 'approved':
        resource.view_count += 1
        resource.save()

    user_seat = ModeratorSeat.objects.filter(current_holder=user).first() if user.role in ['moderator',
                                                                                           'senior_moderator'] else None

    context = {
        'resource': resource,
        'can_download': can_download,
        'can_interact': can_interact,
        'is_moderator_view': (
                    user.role in ['moderator', 'senior_moderator', 'admin'] and resource.status != 'approved'),
        'user_seat': user_seat,
    }

    return render(request, 'core/resource_detail.html', context)


@login_required
def change_password(request):
    """Change password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'core/change_password.html', {'form': form})


@login_required
def delete_resource(request, resource_id):
    """Delete a resource (uploader can delete if pending, moderators anytime)"""
    resource = get_object_or_404(Resource, id=resource_id)

    # Check permissions
    can_delete = False
    reason = ""

    if request.user.role in ['moderator', 'senior_moderator', 'admin']:
        # Moderators can delete anytime
        can_delete = True
        reason = "moderator"
    elif request.user == resource.uploader and resource.status == 'pending':
        # Uploader can only delete pending resources
        can_delete = True
        reason = "uploader (pending)"

    if not can_delete:
        messages.error(request, 'You do not have permission to delete this resource.')
        return redirect('resource_detail', resource_id=resource_id)

    if request.method == 'POST':
        title = resource.title
        resource.delete()

        # Log the deletion
        logger.info(f"Resource '{title}' (ID: {resource_id}) deleted by {request.user.email} ({reason})")

        messages.success(request, f'Resource "{title}" has been deleted.')

        # Redirect based on who deleted
        if request.user.role in ['moderator', 'senior_moderator', 'admin']:
            return redirect('moderator_dashboard')
        else:
            return redirect('my_uploads')

    # GET request - show confirmation page
    return render(request, 'core/delete_confirm.html', {'resource': resource})


@login_required
def toggle_bookmark(request, resource_id):
    """Add or remove a bookmark - only for approved resources"""
    resource = get_object_or_404(Resource, id=resource_id)

    # Only allow bookmarking approved resources
    if resource.status != 'approved':
        messages.error(request, 'You can only bookmark approved resources.')
        return redirect('resource_detail', resource_id=resource_id)

    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        resource=resource
    )

    if created:
        messages.success(request, '📌 Resource bookmarked!')
    else:
        bookmark.delete()
        messages.success(request, '🔓 Bookmark removed')

    return redirect('resource_detail', resource_id=resource_id)


@login_required
def my_bookmarks(request):
    """View user's bookmarked resources"""
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('resource').order_by('-created_at')

    context = {
        'bookmarks': bookmarks,
    }
    return render(request, 'core/bookmarks.html', context)


@login_required
def rate_resource(request, resource_id):
    """Rate a resource - only for approved resources"""
    if request.method == 'POST':
        resource = get_object_or_404(Resource, id=resource_id)

        # Only allow rating approved resources
        if resource.status != 'approved':
            messages.error(request, 'You can only rate approved resources.')
            return redirect('resource_detail', resource_id=resource_id)

        rating_value = request.POST.get('rating')

        if rating_value and rating_value.isdigit():
            rating_value = int(rating_value)
            if 1 <= rating_value <= 5:
                rating, created = Rating.objects.update_or_create(
                    user=request.user,
                    resource=resource,
                    defaults={'rating': rating_value}
                )

                if created:
                    messages.success(request, f'⭐ Rated {rating_value} stars!')
                else:
                    messages.success(request, f'⭐ Rating updated to {rating_value} stars!')

        return redirect('resource_detail', resource_id=resource_id)

    return redirect('resource_detail', resource_id=resource_id)


@login_required
def delete_request(request, request_id):
    """Delete a request (uploader can delete, moderators anytime)"""
    resource_request = get_object_or_404(ResourceRequest, id=request_id)

    # Check permissions
    can_delete = False
    reason = ""

    if request.user.role in ['moderator', 'senior_moderator', 'admin']:
        # Moderators can delete anytime
        can_delete = True
        reason = "moderator"
    elif request.user == resource_request.requester:
        # Requester can delete their own requests
        can_delete = True
        reason = "requester"

    if not can_delete:
        messages.error(request, 'You do not have permission to delete this request.')
        return redirect('request_detail', request_id=request_id)

    if request.method == 'POST':
        title = resource_request.title
        resource_request.delete()

        logger.info(f"Request '{title}' (ID: {request_id}) deleted by {request.user.email} ({reason})")

        messages.success(request, f'Request "{title}" has been deleted.')
        return redirect('request_list')

    # GET request - show confirmation page
    return render(request, 'core/delete_confirm_request.html', {'request': resource_request})


@login_required
def class_rep_dashboard(request):
    """Dashboard for managing class rep seats"""
    # Only senior moderators and admins can access
    if request.user.role not in ['senior_moderator', 'admin']:
        messages.error(request, 'Access denied. Senior moderator privileges required.')
        return redirect('dashboard')

    # Get all seats
    seats = ModeratorSeat.objects.all().order_by('level', 'programme', 'year')

    # Get pending transfers
    pending_transfers = TransferRequest.objects.filter(status='pending').order_by('-created_at')

    # Statistics
    total_seats = seats.count()
    filled_seats = seats.filter(current_holder__isnull=False).count()
    vacant_seats = total_seats - filled_seats

    context = {
        'seats': seats,
        'pending_transfers': pending_transfers,
        'total_seats': total_seats,
        'filled_seats': filled_seats,
        'vacant_seats': vacant_seats,
    }

    return render(request, 'core/moderator/seats.html', context)


@login_required
def create_seat(request):
    """Create a new moderator seat"""
    if request.user.role not in ['senior_moderator', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        seat = ModeratorSeat.objects.create(
            name=request.POST.get('name'),
            seat_type=request.POST.get('seat_type'),
            level=request.POST.get('level'),
            school=request.POST.get('school') or None,
            programme=request.POST.get('programme') or None,
            year=request.POST.get('year') or None,
            subject=request.POST.get('subject') or None,
        )
        messages.success(request, f'Seat "{seat.name}" created successfully!')
        return redirect('class_rep_dashboard')

    return render(request, 'core/moderator/create_seat.html')


@login_required
def initiate_transfer(request, seat_id):
    """Initiate transfer of a moderator seat"""
    seat = get_object_or_404(ModeratorSeat, id=seat_id)

    # Check permission
    if request.user != seat.current_holder and request.user.role not in ['senior_moderator', 'admin']:
        messages.error(request, 'Only the current holder or senior moderators can initiate transfers.')
        return redirect('class_rep_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            new_holder = User.objects.get(email=email)

            # Check if user already has a seat
            if new_holder.moderator_seats.exists():
                messages.error(request, 'This user already holds a moderator seat.')
                return redirect('initiate_transfer', seat_id=seat_id)

            # Create transfer request
            transfer = TransferRequest.objects.create(
                seat=seat,
                from_user=request.user,
                to_user=new_holder
            )

            # Notify the new user
            create_notification(
                user=new_holder,
                notification_type='transfer_request',
                title="📨 Class Rep Invitation",
                message=f"You've been nominated to become {seat.name}. Click to accept."
            )

            messages.success(request, f'Transfer request sent to {email}. They have 7 days to accept.')
            return redirect('class_rep_dashboard')

        except User.DoesNotExist:
            messages.error(request, 'User not found with that email.')

    return render(request, 'core/moderator/initiate_transfer.html', {'seat': seat})


@login_required
def my_transfers(request):
    """View transfer requests for current user"""
    received = TransferRequest.objects.filter(to_user=request.user, status='pending')
    sent = TransferRequest.objects.filter(from_user=request.user)

    context = {
        'received': received,
        'sent': sent,
    }

    return render(request, 'core/moderator/transfers.html', context)


@login_required
def respond_transfer(request, transfer_id):
    """Accept or reject a transfer request"""
    transfer = get_object_or_404(TransferRequest, id=transfer_id, to_user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            # Need senior moderator approval
            transfer.status = 'pending_approval'
            transfer.save()

            # Notify senior moderators
            seniors = User.objects.filter(role='senior_moderator')
            for senior in seniors:
                create_notification(
                    user=senior,
                    notification_type='transfer_approval',
                    title="🔐 Transfer Requires Approval",
                    message=f"{request.user.username} accepted the {transfer.seat.name} transfer. Please verify."
                )

            messages.success(request, 'You have accepted. Waiting for senior moderator approval.')

        elif action == 'reject':
            transfer.status = 'rejected'
            transfer.responded_at = timezone.now()
            transfer.save()

            messages.success(request, 'Transfer request rejected.')

        return redirect('my_transfers')

    return render(request, 'core/moderator/respond_transfer.html', {'transfer': transfer})


@login_required
def approve_transfer(request, transfer_id):
    """Senior moderator approves a transfer"""
    if request.user.role not in ['senior_moderator', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    transfer = get_object_or_404(TransferRequest, id=transfer_id, status='pending_approval')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            transfer.approve(request.user)
            messages.success(request, f'Transfer approved! {transfer.to_user.username} is now the class rep.')

        elif action == 'reject':
            reason = request.POST.get('reason', '')
            transfer.reject(request.user, reason)
            messages.success(request, 'Transfer rejected.')

    return redirect('class_rep_dashboard')


def toast_demo(request):
    """Test all toast types"""
    messages.success(request, '✅ Resource uploaded successfully!')
    messages.error(request, '❌ Something went wrong!')
    messages.warning(request, '⚠️ Please check your input!')
    messages.info(request, 'ℹ️ New features available!')
    return redirect('dashboard')


def ajax_toast(request):
    """Test AJAX toast"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'toast': {
                'type': 'success',
                'message': 'Action completed!',
                'duration': 3000
            }
        })
    return JsonResponse({'error': 'Not AJAX'}, status=400)


def test_email_direct(request):
    """Direct test of email functionality"""
    result = []
    result.append("🔍 TESTING EMAIL DIRECTLY\n")

    try:
        # Test 1: Check settings
        result.append(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        result.append(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        result.append(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        result.append(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

        # Test 2: Try to send
        send_mail(
            'Direct Test from KUHeS',
            'This email was sent directly from the test view.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        result.append("\n✅ Email sent successfully!")
    except Exception as e:
        result.append(f"\n❌ Error: {str(e)}")
        import traceback
        result.append(traceback.format_exc())

    return HttpResponse('<br>'.join(result).replace('\n', '<br>'))