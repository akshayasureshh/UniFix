from django.db import models

class RoleChoices(models.TextChoices):
    STUDENT = 'student', 'Student'
    TEACHING_STAFF = 'teaching_staff', 'Teaching Staff'
    NON_TEACHING_STAFF = 'non_teaching_staff', 'Non-Teaching Staff'
    ADMIN = 'admin', 'Administrator'
    MAINTENANCE = 'maintenance', 'Maintenance Team'
    SECURITY = 'security', 'Security Staff'


class LocationTypeChoices(models.TextChoices):
    CLASSROOM = 'classroom', 'Classroom'
    BUILDING = 'building', 'Building'
    ROOM = 'room', 'Room'
    OUTDOOR = 'outdoor', 'Outdoor Area'
    LAB = 'lab', 'Laboratory'
    LIBRARY = 'library', 'Library'
    CANTEEN = 'canteen', 'Canteen'
    HOSTEL = 'hostel', 'Hostel'
    SPORTS = 'sports', 'Sports Facility'
    OTHERS = 'others', 'Others'


class PriorityChoices(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class StatusChoices(models.TextChoices):
    REPORTED = 'reported', 'Reported'
    ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
    IN_PROGRESS = 'in_progress', 'In Progress'
    RESOLVED = 'resolved', 'Resolved'
    CLOSED = 'closed', 'Closed'
    REJECTED = 'rejected', 'Rejected'


class NotificationChoices(models.TextChoices):
    ISSUE_CREATED = 'issue_created', 'Issue Created'
    ISSUE_UPDATED = 'issue_updated', 'Issue Updated'
    COMMENT_ADDED = 'comment_added', 'Comment Added'
    UPVOTE_RECEIVED = 'upvote_received', 'Upvote Received'
    ASSIGNMENT_CHANGED = 'assignment_changed', 'Assignment Changed'
