import os
import binascii
from django.contrib.auth.models import AbstractUser
from .choices import RoleChoices, LocationTypeChoices, PriorityChoices, StatusChoices, NotificationChoices
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
# from essentials.utils import CipherUtils, DateTimeUtils
# from essentials.exceptions import DetailErrorException
# from .tasks import send_2factor_otp

class AuthToken(models.Model):
    key = models.CharField(_("Key"), max_length=40, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="auth_token",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    device_id = models.UUIDField(_("Device ID"))
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
        return f"Token({self.user}, {self.device_id}, {self.key})"

    class Meta:
        unique_together = ["user", "device_id"]
        verbose_name = _("Auth Token")
        verbose_name_plural = _("Auth Tokens")




class User(AbstractUser):
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True)
    is_verified = models.BooleanField(default=False)
    designation = models.CharField(max_length=25, null=True)
    office_location = models.CharField(max_length=100, blank=True)
    
    
    # JWT = {
    #     'fields': {
    #         'email': {
    #             'field': serializers.EmailField,
    #             'kwargs': {
    #                 'label': _('Email'),
    #                 'write_only': True,
    #                 'required': True,
    #                 'allow_blank': True
    #             }
    #         },
    #         'password': {
    #             'field': serializers.CharField,
    #             'kwargs': {
    #                 'label': _("Password"),
    #                 'style': {'input_type': 'password'},
    #                 'trim_whitespace': False,
    #                 'write_only': True
    #             }
    #         },
    #         'device_id': {
    #             'field': serializers.UUIDField,
    #             'kwargs': {
    #                 'format': 'hex_verbose',
    #                 'error_messages': {
    #                     'device_id': 'A valid UUID is required'
    #                 },
    #                 'write_only': True
    #             }
    #         }
    #     },
    #     'payload_fields': ['device_id'],
        # 'validators': [
        #     (lambda x: 'email' in x or 'phone' in x, _('Either email or phone must be set'))
        # ]
    # } 

    password = models.CharField(_('password'), max_length=128, null=True)

    email = models.EmailField(
        _('email address'),
        null=True,
        unique=True,
        error_messages={
            'unique': _('A user with that email already exists!')
        }
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
        help_text=_("Designates whether ths user should be treated as active")
    )

    is_staff = models.BooleanField(
        _('staff Status'),
        default=False,
        help_text=_("Designates whether the user can log into the admin site.")
    )

    # objects = CustomUserManager()
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'

    # For superuser creation
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    # @classmethod
    # def get_user_by_email(cls, email):
    #     try:
    #         return User.objects.get(email=email)
    #     except ObjectDoesNotExist:
    #         return None

    @property
    def full_name(self):
        return ' '.join(
            [str(name) for name in [self.first_name, self.middle_name, self.last_name] if name and name != '']
        )

    # def get_temporary_token(self):
    #     return CipherUtils.encrypt({'user': self.pk, 'timestamp': DateTimeUtils.current_timestamp()})

    def mail_email_verification(self):
        otp, created = self.otps.get_or_create(user=self, type=settings.OTP_VERIFY_EMAIL)
        otp.send_mail(
            subject=_('Verify your email address'),
            token_dict={'token': self.get_temporary_token()},
            show_verification_link=True
        )
    
    # @classmethod
    # def send_phone_auth_otp(cls, phone, ts):
    #     otp = cls.generate_phone_auth_otp(str(phone), ts)
    #     send_2factor_otp.delay(phone.national_number, otp)

    # @staticmethod
    # def generate_phone_auth_otp(phone, ts):
    #     msg = phone + str(ts)
    #     digest = hmac.new(settings.OTP_SECRET, msg.encode('utf-8'), hashlib.sha1).digest()
    #     o = digest[19] & 15            
    #     h = (struct.unpack(">I", digest[o:o+4])[0] & 0x7fffffff) % 10000
    #     return str(h).rjust(4, "0")
    
    # @staticmethod
    # def verify_phone_auth_otp(token, otp):
    #     data = CipherUtils.decrypt(token)
    #     if data is None:
    #         return False, None
    #     expire_time = datetime.datetime.fromtimestamp(data['gts']) + \
    #         datetime.timedelta(minutes=settings.OTP_SMS_EXPIRING_TIME)
    #     if datetime.datetime.now() > expire_time:
    #         return False, None
    #     generated_otp = User.generate_phone_auth_otp(data['phone'], data['ts'])
    #     if generated_otp != otp:
    #         return False, None
    #     return True, data
    
    # @staticmethod
    # def generate_phone_auth_token(
    #     phone, 
    #     ts, 
    #     action: PhoneAuth, 
    #     device_id: str,
    #     gts=None
    # ):
    #     return CipherUtils.encrypt({
    #         'phone': phone,
    #         'ts': ts, 
    #         'action': action.value,
    #         'device_id': device_id,
    #         'gts': gts or DateTimeUtils.current_timestamp()
    #     })

    # def get_jwt_token(self, **kwargs):
    #     token = RefreshToken.for_user(self)
    #     for key, value in kwargs.items():
    #         token[key] = str(value)
    #     return {
    #         'refresh': str(token),
    #         'access': str(token.access_token)
    #     }

    # def revoke_refresh_token(self, refresh_token):
    #     try:
    #         token = RefreshToken(refresh_token)
    #         token.blacklist()
    #     except TokenError:
    #         raise DetailErrorException('Token is invalid or expired')

    @classmethod
    def exists(cls, **kwargs):
        return cls.objects.filter(**kwargs).exists()

    @classmethod
    def get_or_create_anon_user(cls):
        return cls.objects.get_or_create(
            email=settings.ANON_USER_EMAIL,
            defaults={
                'first_name': settings.ANON_USER_FIRST_NAME,
                'last_name': settings.ANON_USER_LAST_NAME,
            })[0]
    
    def is_anonymous_user(self):
        return True if self.email == settings.ANON_USER_EMAIL else False

    def __str__(self):
        return f'{self.pk}'
    
    @property
    def is_staff_member(self):
        return self.role in ['teaching_staff', 'non_teaching_staff', 'admin', 'maintenance', 'security']
    
    @property
    def manage_issues(self):
        return self.role in ['admin', 'maintenance', 'staff']
    
    @property
    def report_issues(self):
        return True
    
    class Meta:
        managed = True
        abstract = False
    
    
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