import os
import binascii
from django.contrib.auth.models import AbstractUser
from .choices import RoleChoices, LocationTypeChoices, PriorityChoices, StatusChoices, NotificationChoices
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AuthToken(models.Model):
    key = models.CharField(_("Key"), max_length=40, unique=True, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="custom_auth_tokens",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    device_id = models.UUIDField(_("Device ID"))
    device_name = models.CharField(_("Device Name"), max_length=100, blank=True, null=True)
    last_login = models.DateTimeField(_("Last Login"), auto_now=True)
    status = models.BooleanField(_("token status"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    objects = models.Manager()

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()

    def save(self, *args, **kwargs):
        if not self.device_id:
            raise ValueError("Device ID is required for AuthToken.")
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Token({self.user.username}, {self.device_id})"

    class Meta:
        unique_together = ["user", "device_id"]
        verbose_name = _("Auth Token")
        verbose_name_plural = _("Auth Tokens")
        ordering = ['-last_login']


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    designation = models.CharField(max_length=25, null=True, blank=True)
    office_location = models.CharField(max_length=100, blank=True)

    password = models.CharField(_('password'), max_length=128, null=True)

    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _('A user with that email already exists!')
        },
        null=True
    )

    email_verified = models.BooleanField(
        _('email verified'),
        default=False
    )

    first_name = models.CharField(_('first name'), max_length=128)
    middle_name = models.CharField(
        _('middle name'),
        max_length=128,
        blank=True,
        null=True
    )
    last_name = models.CharField(_('last name'), max_length=128)

    created_at = models.DateTimeField(_('date joined'), default=timezone.now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_("Designates whether this user should be treated as active")
    )

    is_staff = models.BooleanField(
        _('staff Status'),
        default=False,
        help_text=_("Designates whether the user can log into the admin site.")
    )

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    @property
    def full_name(self):
        return ' '.join(
            [str(name) for name in [self.first_name, self.middle_name, self.last_name] 
             if name and name != '']
        )

    @property
    def is_staff_member(self):
        return self.role in ['teaching_staff', 'non_teaching_staff', 'admin', 'maintenance', 'security']
    
    @property
    def can_manage_issues(self):
        return self.role in ['admin', 'maintenance', 'teaching_staff', 'non_teaching_staff']
    
    @property
    def can_report_issues(self):
        return True

    @classmethod
    def exists(cls, **kwargs):
        return cls.objects.filter(**kwargs).exists()

    def __str__(self):
        return f'{self.username} ({self.full_name})'
    
    class Meta:
        managed = True
        abstract = False
        ordering = ['-created_at']
        
class Category(models.Model):
    name = models.CharField(max_length=25, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, null=True)
    color = models.CharField(max_length=10, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
class Location(models.Model):
    name = models.CharField(max_length=100)
    location_type = models.CharField(choices=LocationTypeChoices, max_length=20)
    building = models.CharField(max_length=100, null=True)
    floor = models.CharField(max_length=20, null=True)
    room_no = models.CharField(max_length=20, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.location_type})"
    
    
    
class Issue(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_issues')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='issues')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='issues')
    priority = models.CharField(max_length=20, choices=PriorityChoices.choices, default='medium')
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default='reported')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    upvotes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)
    estimated_resolution_time = models.DurationField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.status}"
    
class IssueImage(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='issue_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.issue.title}"
    

class Upvote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='upvotes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'issue')
    
    def __str__(self):
        return f"{self.user.username} upvoted {self.issue.title}"
    

class Comment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.issue.title}"
    
    
class IssueStatusHistory(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='status_history')
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Issue Status Histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.issue.title}: {self.old_status} → {self.new_status}"
    

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NotificationChoices.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient.username}"