from django.db import models
import os
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.core.mail import EmailMessage
from django_celery_beat.models import PeriodicTask
import uuid
from datetime import datetime, timedelta
import environ

env = environ.Env()


def generate_uuid():
    return str(uuid.uuid4())


def send_mail_templates(file_name, user_email, email_subject, content, bcc_emails):
    try:
        email_message = render_to_string(file_name, content)
        email = EmailMessage(
            f"{env('EMAIL_SUBJECT_INITIAL',default='')} {email_subject}",
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            user_email,
            bcc_emails,
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")


def get_user_name(user):
    try:
        roles = user.profile.roles.all()
        if not roles.exists():
            return "User"
        role = roles.first().name
        if role == "pmo":
            return user.profile.pmo.name
        elif role == "employee":
            return (
                user.profile.employee.first_name + " " + user.profile.employee.last_name
            )
        elif role == "vendor":
            return user.profile.vendor.name
        elif role == "superadmin":
            return user.profile.superadmin.name
        elif role == "finance":
            return user.profile.finance.name
        elif role == "sales":
            return user.profile.sales.name
        else:
            return "User"
    except Exception as e:
        print(str(e))
        return "User"


class SubRole(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sub_roles = models.ManyToManyField(SubRole)

    def __str__(self):
        return self.name


class UserRolePermissions(models.Model):
    role = models.ForeignKey(Role, null=True, on_delete=models.SET_NULL)
    sub_role = models.ForeignKey(SubRole, null=True, on_delete=models.SET_NULL)
    permission = models.JSONField(default=list, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Role:{self.role.name} -> SubRole:{self.sub_role.name}"


class Profile(models.Model):
    user_types = [
        ("pmo", "pmo"),
        ("leader", "leader"),
        ("superadmin", "superadmin"),
        ("finance", "finance"),
        ("employee", "employee"),
        ("sales", "sales"),
    ]
    timezone = models.CharField(max_length=100, default="Asia/Kolkata")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roles = models.ManyToManyField(Role)
    permissions = models.ManyToManyField(UserRolePermissions)

    def __str__(self):
        return self.user.username


class SuperAdmin(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Finance(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    active_inactive = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Sales(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    active_inactive = models.BooleanField(default=True)
    sales_person_id = models.CharField(max_length=255, blank=True, default="")
    business = models.CharField(max_length=255, blank=True, default="meeraq")
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Leader(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    active_inactive = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Pmo(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    room_id = models.CharField(max_length=50, blank=True)
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.name




def validate_pdf_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if not ext == ".pdf":
        raise ValidationError("Only PDF files are allowed.")
    

class Organisation(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.ImageField(upload_to="post_images", blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name


class HR(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    active_inactive = models.BooleanField(default=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.first_name + " " + self.last_name

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.CharField(max_length=225, null=True, blank=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    path = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True)
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class UserLoginActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"User Login Activity for {self.user.username}"


class SentEmailActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_subject = models.CharField(max_length=500)
    content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"Sent Email - {self.user.username}"


class UserToken(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ("google", "Google"),
        ("microsoft", "Microsoft"),
    ]

    user_profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    access_token_expiry = models.TextField(blank=True)
    authorization_code = models.TextField(blank=True)
    account_type = models.CharField(
        max_length=50, choices=ACCOUNT_TYPE_CHOICES, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_profile.user.username

class CalendarEvent(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ("google", "Google"),
        ("microsoft", "Microsoft"),
    ]

    event_id = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    start_datetime = models.CharField(max_length=255, blank=True, null=True)
    end_datetime = models.CharField(max_length=255, blank=True, null=True)
    attendee = models.CharField(max_length=255, blank=True, null=True)
    creator = models.CharField(max_length=255, blank=True, null=True)
    account_type = models.CharField(
        max_length=50, choices=ACCOUNT_TYPE_CHOICES, blank=True
    )
    
class APILog(models.Model):
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.path}"


class TableHiddenColumn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    table_name = models.CharField(max_length=225, blank=True)
    hidden_columns = models.JSONField(default=list, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"


class TicketFeedback(models.Model):
    # Question 1: Overall Satisfaction
    satisfaction_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Satisfaction Rating",
        help_text="How satisfied are you with the way your issue was handled? (1-5)",
    )
    # Question 2: Response Timeliness
    response_timeliness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Response Timeliness",
        help_text="How timely was the response to your ticket? (1-5)",
    )
    # Question 3: Resolution Helpfulness
    resolution_helpfulness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Resolution Helpfulness",
        help_text="How helpful was the resolution to you? (1-5)",
    )
    # Question 4: Experience Smoothness (Text field)
    experience_smoothness = models.TextField(
        verbose_name="Experience Smoothness",
        help_text="How smooth was your overall experience with the ticket process?",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Employee(models.Model):
    ROLE_CHOICES = [
        ("head", "Head"),
        ("team_member", "Team Member"),
    ]

    ORGANISATION_CHOICES = [
        ("ctt", "CTT"),
        ("meeraq", "Meeraq"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    user = models.OneToOneField(
        Profile, on_delete=models.CASCADE, blank=True, null=True
    )
    function = models.CharField(max_length=255, null=True)
    active_inactive = models.BooleanField(default=True)
    role = models.CharField(max_length=11, choices=ROLE_CHOICES, default="team_member")
    organisation = models.CharField(
        max_length=6, choices=ORGANISATION_CHOICES, default="meeraq"
    )
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default="active")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



# Registration Model: Stores user registration details and their session selections.
class Tickets(models.Model):
    PRIORITY_CHOICES = (
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    )
    # Status Choices
    STATUS_CHOICES = (
        ("open", "Open"),
        ("in_review", "In Review"),
        ("closed", "Closed"),
        ("cancelled", "Cancelled"),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    user_type = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="tickets", blank=True)
    raise_to = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=255, choices=STATUS_CHOICES, blank=True, null=True, default="open"
    )
    comments = models.ManyToManyField(Comment, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ticket_number = models.CharField(max_length=20, blank=True, null=True)
    # New SLA related fields
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    sla_due_date = models.DateTimeField(blank=True, null=True)
    resolution_date = models.DateTimeField(blank=True, null=True)
    is_sla_breached = models.BooleanField(default=False)
    feedback = models.OneToOneField(
        TicketFeedback,
        on_delete=models.SET_NULL,
        related_name="ticket",
        blank=True,
        null=True,
    )
    unique_id = models.CharField(
        max_length=225, default=generate_uuid, blank=True, null=True
    )
    assignee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store original values to track changes
        if self.id:
            self._original_priority = self.priority

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        # Check if this is a new ticket or an existing one
        is_new = not self.id

        # If new ticket or priority has changed, update the SLA due date
        if is_new or (
            not is_new
            and self._state.adding is False
            and hasattr(self, "_original_priority")
            and self._original_priority != self.priority
        ):
            self.set_sla_due_date()

        # If status changes to 'closed', set resolution date
        if self.status == "closed" and not self.resolution_date:
            self.resolution_date = timezone.now()

        # If status changed from 'closed' to something else, clear resolution date
        elif self.status != "closed" and self.resolution_date:
            self.resolution_date = None

        # Check if SLA is breached
        self.check_sla_breach()
        super().save(*args, **kwargs)

        # Store original values after save for future comparison
        if not is_new:
            self._original_priority = self.priority

    def set_sla_due_date(self):
        now = timezone.now()
        
        # Function to add business days
        def add_business_days(start_date, business_days):
            business_days_added = 0
            current_date = start_date
            
            while business_days_added < business_days:
                current_date += timedelta(days=1)
                # Skip weekends (5=Saturday, 6=Sunday in Python's weekday())
                if current_date.weekday() < 5:  # 0-4 are Monday to Friday
                    business_days_added += 1
                    
            # Set to end of day (11:59:59 PM)
            return current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Set SLA due date based on priority
        if self.priority == "critical":
            # Critical: 1 hour (not affected by weekends)
            self.sla_due_date = now + timedelta(hours=1)
        
        elif self.priority == "high":
            # High: 4 hours (not affected by weekends)
            self.sla_due_date = now + timedelta(hours=4)
        
        elif self.priority == "medium":
            # Medium: 2 business days
            # Start counting from today
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.sla_due_date = add_business_days(today, 2)
        
        elif self.priority == "low":
            # Low: 4 business days
            # Start counting from today
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.sla_due_date = add_business_days(today, 4)

    def check_sla_breach(self):
        # Only check for breach if ticket is not closed or cancelled yet
        if self.status not in ["closed", "cancelled"] and self.sla_due_date:
            if timezone.now() > self.sla_due_date:
                self.is_sla_breached = True
            else:
                self.is_sla_breached = False

    def get_time_to_sla_breach(self):
        """Returns time remaining until SLA breach or None if already breached/closed/cancelled"""
        if self.status in ["closed", "cancelled"] or self.is_sla_breached:
            return None

        if self.sla_due_date:
            now = timezone.now()
            if now < self.sla_due_date:
                return self.sla_due_date - now
        return None

    def get_resolution_time(self):
        """Returns the total resolution time if ticket is resolved"""
        if self.resolution_date:
            return self.resolution_date - self.created_at
        return None


class UserHierarchy(models.Model):
    """
    Defines direct reporting relationships between users within specific roles
    This allows for user-to-user hierarchies within your organizational structure
    """

    subordinate = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="supervisor_relationships"
    )
    supervisor = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="subordinate_relationships"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        help_text="The role context in which this hierarchy relationship exists",
    )
    is_primary = models.BooleanField(
        default=True, help_text="Whether this is the primary supervisor for this role"
    )
    hierarchy_level = models.IntegerField(
        default=1, help_text="1=direct supervisor, 2+=higher level supervisor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("subordinate", "supervisor", "role")
        verbose_name_plural = "User Hierarchies"

    def __str__(self):
        return f"{self.subordinate} reports to {self.supervisor} in {self.role.name}"

    def save(self, *args, **kwargs):
        # Check for circular references before saving
        if self.subordinate == self.supervisor:
            raise ValidationError("A user cannot be their own supervisor.")

        # Ensure no circular hierarchy chain exists
        user_chain = self._get_supervisor_chain(self.supervisor, self.role)
        if self.subordinate.id in user_chain:
            raise ValidationError(
                "This would create a circular hierarchy relationship."
            )

        # If setting as primary, clear other primary relationships for this subordinate in this role
        if self.is_primary:
            UserHierarchy.objects.filter(
                subordinate=self.subordinate, role=self.role, is_primary=True
            ).update(is_primary=False)

        super().save(*args, **kwargs)

    def _get_supervisor_chain(self, user, role, chain=None):
        """Helper method to get all supervisors in a chain to check for circular references"""
        if chain is None:
            chain = set()

        chain.add(user.id)
        supervisors = UserHierarchy.objects.filter(subordinate=user, role=role)

        for hierarchy in supervisors:
            if hierarchy.supervisor.id not in chain:
                chain.update(
                    self._get_supervisor_chain(hierarchy.supervisor, role, chain)
                )

        return chain


class UserDelegation(models.Model):
    """
    Tracks temporary delegation of permissions from one user to another
    when someone is temporarily unavailable or on leave
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("scheduled", "Scheduled"),
        ("expired", "Expired"),
    ]


    delegated_from = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="outgoing_delegations",
        help_text="User delegating their permissions",
    )
    delegated_to = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="incoming_delegations",
        help_text="User receiving delegated permissions",
    )

    # The role context for this delegation
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, help_text="The role context for this delegation"
    )

    # Store the specific permissions being delegated
    permissions = models.JSONField(default=list)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="scheduled"
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Notes about the delegation
    reason = models.TextField(blank=True, help_text="Reason for the delegation")
    notes = models.TextField(blank=True, help_text="Additional instructions or notes")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delegation from {self.delegated_from} to {self.delegated_to} ({self.role.name})"

    @property
    def is_active(self):
        """Check if the delegation is currently active"""
        now = timezone.now()
        return self.status == "active" and self.start_date <= now <= self.end_date

    def activate(self):
        """Manually activate this delegation"""
        self.status = "active"
        self.save()

    def deactivate(self):
        """Manually deactivate this delegation"""
        self.status = "inactive"
        self.save()


class DelegationHistory(models.Model):
    """
    Tracks actions performed by users with delegated permissions
    Provides an audit trail of what was done under delegation
    """

    delegation = models.ForeignKey(
        UserDelegation, on_delete=models.CASCADE, related_name="history"
    )
    action = models.TextField(help_text="Description of what action was performed")
    performed_at = models.DateTimeField(auto_now_add=True)

    # Optional: reference to specific object modified
    content_type = models.CharField(max_length=100, blank=True)
    object_id = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Delegation Histories"

    def __str__(self):
        return f"Action by {self.delegation.delegated_to} on behalf of {self.delegation.delegated_from}"


class HierarchyChange(models.Model):
    """
    Tracks changes to the user hierarchy for audit purposes
    """

    CHANGE_TYPES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("deleted", "Deleted"),
    ]

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hierarchy_changes_made",
    )
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    subordinate = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hierarchy_changes_as_subordinate",
    )
    supervisor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hierarchy_changes_as_supervisor",
    )
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    details = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" hierarchy: {self.subordinate} -> {self.supervisor} in {self.role}"


class CalendarInvites(models.Model):
    event_id = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start_datetime = models.CharField(max_length=255, blank=True, null=True)
    end_datetime = models.CharField(max_length=255, blank=True, null=True)
    attendees = models.JSONField(blank=True, null=True)
    creator = models.CharField(max_length=255, blank=True, null=True)



class StandardizedField(models.Model):
    FIELD_CHOICES = (
        ("location", "Work Location"),
        ("other_certification", "Assessment Certification"),
        ("area_of_expertise", "Industry"),
        ("job_roles", "Job roles"),
        ("companies_worked_in", "Companies worked in"),
        ("language", "Language Proficiency"),
        ("education", "Education Institutions"),
        ("domain", "Functional Domain"),
        ("client_companies", "Client companies"),
        ("educational_qualification", "Educational Qualification"),
        ("city", "City"),
        ("country", "Country"),
        ("topic", "Topic"),
        ("product_type", "Product Type"),
        ("category", "Category"),
        ("asset_location", "Location"),
        ("project_type", "Project Type"),
        ("credentials_feels_like", "Credential Feels like"),
        ("competency", "Competency"),
        ("coaching_type", "Coaching Type"),
        ("function", "Function"),
        ("client_experience_level", "Client Experience Level"),
    )
    field = models.CharField(max_length=225, choices=FIELD_CHOICES, blank=True)
    values = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.field}"


class StandardizedFieldRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )
    standardized_field_name = models.ForeignKey(
        StandardizedField, on_delete=models.CASCADE, blank=True
    )
    value = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" {self.standardized_field_name} - {self.status}"

