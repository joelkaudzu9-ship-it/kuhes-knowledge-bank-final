from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta


class User(AbstractUser):
    """Custom User Model for KUHeS Knowledge Bank"""

    # User Levels
    PREMED = 'premed'
    UNDERGRADUATE = 'undergraduate'
    POSTGRADUATE = 'postgraduate'
    DIPLOMA = 'diploma'

    LEVEL_CHOICES = [
        (PREMED, 'Pre-Med Foundation'),
        (UNDERGRADUATE, 'Undergraduate'),
        (POSTGRADUATE, 'Postgraduate'),
        (DIPLOMA, 'Diploma'),
    ]

    # Schools
    MEDICINE = 'medicine'
    NURSING = 'nursing'
    MATERNAL = 'maternal'
    LIFE_SCIENCES = 'life_sciences'
    PUBLIC_HEALTH = 'public_health'

    SCHOOL_CHOICES = [
        (MEDICINE, 'Medicine and Oral Health'),
        (NURSING, 'Nursing'),
        (MATERNAL, 'Maternal, Neonatal and Reproductive Health'),
        (LIFE_SCIENCES, 'Life Sciences and Allied Health Professions'),
        (PUBLIC_HEALTH, 'Global and Public Health'),
    ]

    # User Roles
    STUDENT = 'student'
    MODERATOR = 'moderator'
    SENIOR_MODERATOR = 'senior_moderator'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (MODERATOR, 'Moderator'),
        (SENIOR_MODERATOR, 'Senior Moderator'),
        (ADMIN, 'Administrator'),
    ]

    # Basic Info
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    # Academic Profile
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=STUDENT)

    # Undergraduate Fields
    school = models.CharField(max_length=20, choices=SCHOOL_CHOICES, blank=True, null=True)
    programme = models.CharField(max_length=100, blank=True)
    year_of_study = models.IntegerField(blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)

    # Pre-Med Fields
    premed_cohort = models.CharField(max_length=20, blank=True)
    intended_programme = models.CharField(max_length=100, blank=True)

    # Statistics
    upload_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)

    # Moderator Fields
    moderator_seat_id = models.CharField(max_length=50, blank=True, null=True)

    # Account Status
    last_active = models.DateTimeField(default=timezone.now)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def get_available_seats(self):
        """Get seats available for this user based on their programme and year"""
        if self.level == 'premed':
            # Pre-Med students can only get Pre-Med seats
            return ModeratorSeat.objects.filter(
                level='premed',
                status='vacant'
            )
        elif self.level == 'undergraduate':
            # Undergraduate students can get seats in their programme/year
            return ModeratorSeat.objects.filter(
                level='undergraduate',
                school=self.school,
                programme=self.programme,
                year=self.year_of_study,
                status='vacant'
            )
        elif self.level == 'postgraduate':
            return ModeratorSeat.objects.filter(
                level='postgraduate',
                programme=self.programme,
                year=self.year_of_study,
                status='vacant'
            )
        return ModeratorSeat.objects.none()

    def __str__(self):
        return f"{self.email} - {self.get_role_display()}"


class EmailVerification(models.Model):
    """Email verification tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Verification for {self.user.email}"


class PasswordReset(models.Model):
    """Password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Password reset for {self.user.email}"


class Resource(models.Model):
    """Resource model for handouts, past papers, etc."""

    # Resource Types
    HANDOUT = 'handout'
    PAST_PAPER = 'past_paper'
    LECTURE_NOTE = 'lecture_note'
    RESEARCH = 'research'
    CLINICAL_GUIDE = 'clinical_guide'
    VIDEO = 'video'
    STUDY_SET = 'study_set'
    SUMMARY = 'summary'
    LAB_MANUAL = 'lab_manual'
    CASE_STUDY = 'case_study'
    FORMULA_SHEET = 'formula_sheet'
    DIAGRAM = 'diagram'

    RESOURCE_TYPES = [
        (HANDOUT, '📄 Handout'),
        (PAST_PAPER, '📝 Past Paper'),
        (LECTURE_NOTE, '📚 Lecture Note'),
        (RESEARCH, '🔬 Research Article'),
        (CLINICAL_GUIDE, '🩺 Clinical Guide'),
        (VIDEO, '🎥 Video'),
        (STUDY_SET, '📋 Study Set'),
        (SUMMARY, '📊 Summary Sheet'),
        (LAB_MANUAL, '🧪 Lab Manual'),
        (CASE_STUDY, '🏥 Case Study'),
        (FORMULA_SHEET, '📐 Formula Sheet'),
        (DIAGRAM, '📊 Diagram'),
    ]

    # Academic Levels
    PREMED = 'premed'
    UNDERGRADUATE = 'undergraduate'
    POSTGRADUATE = 'postgraduate'
    DIPLOMA = 'diploma'

    LEVEL_CHOICES = [
        (PREMED, 'Pre-Med'),
        (UNDERGRADUATE, 'Undergraduate'),
        (POSTGRADUATE, 'Postgraduate'),
        (DIPLOMA, 'Diploma'),
    ]

    # Pre-Med Subjects
    BIOLOGY = 'biology'
    CHEMISTRY = 'chemistry'
    PHYSICS = 'physics'
    MATHEMATICS = 'mathematics'
    ICT = 'ict'
    COMMUNICATION = 'communication'

    SUBJECT_CHOICES = [
        (BIOLOGY, '🧬 Biology'),
        (CHEMISTRY, '🧪 Chemistry'),
        (PHYSICS, '⚡ Physics'),
        (MATHEMATICS, '📐 Mathematics'),
        (ICT, '💻 ICT'),
        (COMMUNICATION, '🗣️ Communication'),
    ]

    # Basic Info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)

    # Classification
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)

    # Pre-Med specific
    premed_subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, blank=True, null=True)

    # Undergraduate specific
    school = models.CharField(max_length=20, choices=User.SCHOOL_CHOICES, blank=True, null=True)
    programme = models.CharField(max_length=100, blank=True)
    year_of_study = models.IntegerField(blank=True, null=True)
    semester = models.IntegerField(blank=True, null=True)

    # Common fields
    lecturer = models.CharField(max_length=100, blank=True)
    course_code = models.CharField(max_length=20, blank=True)
    academic_year = models.CharField(max_length=20, blank=True)

    # Tags
    tags = models.CharField(max_length=500, blank=True, help_text="Comma separated tags")

    # File or Video Link
    file = models.FileField(upload_to='resources/%Y/%m/', blank=True, null=True)
    video_link = models.URLField(blank=True, null=True, help_text="YouTube/Vimeo link for video resources")
    file_size = models.IntegerField(default=0)  # In bytes
    file_type = models.CharField(max_length=50, blank=True)

    # Metadata
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_resources')
    upload_date = models.DateTimeField(auto_now_add=True)

    # Status
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    FLAGGED = 'flagged'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (FLAGGED, 'Flagged'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_resources')
    approval_date = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True)

    # Statistics
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)

    # Versioning
    version = models.CharField(max_length=10, blank=True)
    is_latest = models.BooleanField(default=True)

    # Relations
    is_duplicate_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['status', 'upload_date']),
            models.Index(fields=['level', 'premed_subject']),
            models.Index(fields=['school', 'programme', 'year_of_study']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_resource_type_display()}"

    def save(self, *args, **kwargs):
        # Set file size and type if file exists
        if self.file and not self.file_size:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)

    def clean(self):
        """Validate that either file or video_link is provided based on type"""
        from django.core.exceptions import ValidationError

        if self.resource_type == 'video' and not self.video_link:
            raise ValidationError('Video link is required for video resources')
        elif self.resource_type != 'video' and not self.file:
            raise ValidationError('File is required for non-video resources')


class ResourceRequest(models.Model):
    """Model for students to request resources"""

    title = models.CharField(max_length=200)
    description = models.TextField()

    # Classification
    level = models.CharField(max_length=20, choices=Resource.LEVEL_CHOICES)
    premed_subject = models.CharField(max_length=20, choices=Resource.SUBJECT_CHOICES, blank=True, null=True)
    school = models.CharField(max_length=20, choices=User.SCHOOL_CHOICES, blank=True, null=True)
    programme = models.CharField(max_length=100, blank=True)
    year_of_study = models.IntegerField(blank=True, null=True)

    # Requester
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_requests')

    # Status
    OPEN = 'open'
    FULFILLED = 'fulfilled'
    CLOSED = 'closed'

    STATUS_CHOICES = [
        (OPEN, 'Open'),
        (FULFILLED, 'Fulfilled'),
        (CLOSED, 'Closed'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)
    fulfilled_by = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.requester.username}"


class Bookmark(models.Model):
    """User bookmarks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'resource']

    def __str__(self):
        return f"{self.user.username} - {self.resource.title}"


class Rating(models.Model):
    """User ratings for resources"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'resource']

    def __str__(self):
        return f"{self.user.username} - {self.resource.title}: {self.rating}⭐"


class ResourceRequest(models.Model):
    """Model for students to request resources"""

    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Describe exactly what you're looking for")

    # Classification
    level = models.CharField(max_length=20, choices=Resource.LEVEL_CHOICES)
    premed_subject = models.CharField(max_length=20, choices=Resource.SUBJECT_CHOICES, blank=True, null=True)
    school = models.CharField(max_length=20, choices=User.SCHOOL_CHOICES, blank=True, null=True)
    programme = models.CharField(max_length=100, blank=True)
    year_of_study = models.IntegerField(blank=True, null=True)
    course_code = models.CharField(max_length=20, blank=True)

    # Requester
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_requests')

    # Status
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    FULFILLED = 'fulfilled'
    CLOSED = 'closed'

    STATUS_CHOICES = [
        (OPEN, '🟢 Open'),
        (IN_PROGRESS, '🟡 In Progress'),
        (FULFILLED, '✅ Fulfilled'),
        (CLOSED, '🔴 Closed'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)

    # Fulfillment
    fulfilled_by = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='fulfilled_requests')
    fulfilled_at = models.DateTimeField(blank=True, null=True)

    # Votes
    upvotes = models.IntegerField(default=0)
    # Add to existing ResourceRequest class
    priority = models.IntegerField(default=0, help_text="Higher number = higher priority (moderator only)")
    is_pinned = models.BooleanField(default=False, help_text="Pin important requests")
    moderator_notes = models.TextField(blank=True, help_text="Internal moderator notes")

    # Urgency
    URGENT = 'urgent'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

    URGENCY_CHOICES = [
        (URGENT, '🔴 Urgent'),
        (HIGH, '🟠 High'),
        (MEDIUM, '🟡 Medium'),
        (LOW, '🟢 Low'),
    ]

    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default=MEDIUM)

    # Deadline (optional)
    deadline = models.DateField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-upvotes', '-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['level', 'premed_subject']),
        ]

    def __str__(self):
        return f"{self.title} - {self.requester.username}"


class RequestUpvote(models.Model):
    """Track who upvoted which request"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request = models.ForeignKey(ResourceRequest, on_delete=models.CASCADE, related_name='upvoted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'request']

    def __str__(self):
        return f"{self.user.username} upvoted {self.request.title}"


class Notification(models.Model):
    """User notifications"""

    # Types
    REQUEST_CREATED = 'request_created'
    REQUEST_UPDATED = 'request_updated'
    REQUEST_FULFILLED = 'request_fulfilled'
    REQUEST_UPVOTED = 'request_upvoted'
    RESOURCE_APPROVED = 'resource_approved'
    RESOURCE_REJECTED = 'resource_rejected'
    RESOURCE_UPLOADED = 'resource_uploaded'
    RESOURCE_DOWNLOADED = 'resource_downloaded'
    COMMENT_ADDED = 'comment_added'
    MODERATOR_ACTION = 'moderator_action'
    SYSTEM_ANNOUNCEMENT = 'system_announcement'

    TYPE_CHOICES = [
        (REQUEST_CREATED, '📝 Request Created'),
        (REQUEST_UPDATED, '🔄 Request Updated'),
        (REQUEST_FULFILLED, '✅ Request Fulfilled'),
        (REQUEST_UPVOTED, '👍 Request Upvoted'),
        (RESOURCE_APPROVED, '✅ Resource Approved'),
        (RESOURCE_REJECTED, '❌ Resource Rejected'),
        (RESOURCE_UPLOADED, '📤 Resource Uploaded'),
        (RESOURCE_DOWNLOADED, '📥 Resource Downloaded'),
        (COMMENT_ADDED, '💬 Comment Added'),
        (MODERATOR_ACTION, '🛡️ Moderator Action'),
        (SYSTEM_ANNOUNCEMENT, '📢 Announcement'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Related objects (optional)
    resource = models.ForeignKey('Resource', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='notifications')
    request = models.ForeignKey('ResourceRequest', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='notifications')

    # Status
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.type}"


class ModeratorSeat(models.Model):
    """Represents a moderator seat for a specific class"""

    # Seat Types
    CLASS_REP = 'class_rep'
    ASSISTANT = 'assistant'
    SUBJECT_LEAD = 'subject_lead'

    SEAT_TYPE_CHOICES = [
        (CLASS_REP, '👑 Class Representative'),
        (ASSISTANT, '🤝 Assistant Representative'),
        (SUBJECT_LEAD, '📚 Subject Lead'),
    ]

    # Pre-Med Subjects (for subject leads)
    BIOLOGY = 'biology'
    CHEMISTRY = 'chemistry'
    PHYSICS = 'physics'
    MATHEMATICS = 'mathematics'
    ICT = 'ict'
    COMMUNICATION = 'communication'

    SUBJECT_CHOICES = [
        (BIOLOGY, '🧬 Biology'),
        (CHEMISTRY, '🧪 Chemistry'),
        (PHYSICS, '⚡ Physics'),
        (MATHEMATICS, '📐 Mathematics'),
        (ICT, '💻 ICT'),
        (COMMUNICATION, '🗣️ Communication'),
    ]

    # Basic Info
    seat_code = models.CharField(max_length=20, unique=True, help_text="Unique code for this seat (e.g., MBBS-3-REP-1)")
    name = models.CharField(max_length=100, help_text="e.g., MBBS Year 3 Rep")
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE_CHOICES, default=CLASS_REP)

    # Class Identification
    level = models.CharField(max_length=20, choices=Resource.LEVEL_CHOICES)
    school = models.CharField(max_length=20, choices=User.SCHOOL_CHOICES, blank=True, null=True)
    programme = models.CharField(max_length=100, blank=True)
    programme_code = models.CharField(max_length=20, blank=True, help_text="e.g., MBBS, BNS, BPHARM")
    year = models.IntegerField(blank=True, null=True)

    # For Pre-Med subject leads
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, blank=True, null=True)

    # Current holder
    current_holder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderator_seats'
    )

    # Seat history (JSON field to store previous holders)
    holder_history = models.JSONField(default=list, blank=True)

    # Status
    ACTIVE = 'active'
    VACANT = 'vacant'
    SUSPENDED = 'suspended'

    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (VACANT, 'Vacant'),
        (SUSPENDED, 'Suspended'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=VACANT)

    # Term dates
    term_start = models.DateField(auto_now_add=True)
    term_end = models.DateField(blank=True, null=True)

    # Transfer settings
    last_transferred = models.DateTimeField(blank=True, null=True)
    transfer_count = models.IntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'programme', 'year', 'seat_type']
        unique_together = [
            ['level', 'school', 'programme', 'year', 'seat_type', 'subject']
        ]

    def __str__(self):
        if self.current_holder:
            return f"{self.seat_code} - {self.current_holder.username}"
        return f"{self.seat_code} - VACANT"

    def get_display_name(self):
        """Get human-readable seat name"""
        if self.seat_type == 'subject_lead' and self.subject:
            return f"Pre-Med {self.get_subject_display()} Lead"
        elif self.seat_type == 'class_rep':
            return f"{self.programme} Year {self.year} Representative 1"
        elif self.seat_type == 'assistant':
            return f"{self.programme} Year {self.year} Representative 2"
        return self.name

    def is_active(self):
        return self.status == 'active' and self.current_holder is not None

    def transfer_to(self, new_holder, transferred_by):
        """Transfer seat to new holder"""
        if self.current_holder:
            # Add current holder to history
            history_entry = {
                'user_id': self.current_holder.id,
                'username': self.current_holder.username,
                'email': self.current_holder.email,
                'transferred_at': timezone.now().isoformat(),
                'transferred_by': transferred_by.username if transferred_by else 'system'
            }
            self.holder_history.append(history_entry)

            # Remove moderator role from old holder if they have no other seats
            if self.current_holder.moderator_seats.count() <= 1:
                self.current_holder.role = 'student'
                self.current_holder.save()

        # Assign new holder
        self.current_holder = new_holder
        self.last_transferred = timezone.now()
        self.transfer_count += 1
        self.status = 'active'
        self.save()

        # Give new holder moderator role
        new_holder.role = 'moderator'
        new_holder.save()

        return True


class TransferRequest(models.Model):
    """Request to transfer a moderator seat"""

    seat = models.ForeignKey(ModeratorSeat, on_delete=models.CASCADE, related_name='transfer_requests')

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transfer_requests_sent'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transfer_requests_received'
    )

    # Status
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    EXPIRED = 'expired'

    STATUS_CHOICES = [
        (PENDING, '⏳ Pending'),
        (APPROVED, '✅ Approved'),
        (REJECTED, '❌ Rejected'),
        (EXPIRED, '⌛ Expired'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    # Verification
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_transfers'
    )
    verified_at = models.DateTimeField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def approve(self, verifier):
        self.status = 'approved'
        self.verified_by = verifier
        self.verified_at = timezone.now()
        self.responded_at = timezone.now()
        self.save()

        # Transfer the seat
        self.seat.transfer_to(self.to_user, verifier)

        # Create notification
        from .notifications import create_notification
        create_notification(
            user=self.to_user,
            notification_type='moderator_transfer',
            title="🎉 You're now a Class Rep!",
            message=f"You have been approved as {self.seat.name}."
        )

    def reject(self, verifier, reason=""):
        self.status = 'rejected'
        self.verified_by = verifier
        self.verified_at = timezone.now()
        self.responded_at = timezone.now()
        self.save()