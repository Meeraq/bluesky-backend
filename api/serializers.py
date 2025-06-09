from rest_framework import serializers
from django_celery_beat.models import PeriodicTask
from .models import (
    Pmo,
    Profile,
    HR,
    Finance,
    Organisation,
    Notification,
    UserLoginActivity,
    SentEmailActivity,
    UserToken,
    CalendarEvent,
    SuperAdmin,
    APILog,
    Sales,
    Leader,
    Tickets,
    TicketFeedback,
    Role,
    UserRolePermissions,
    SubRole,
    Comment,
    Employee,
    StandardizedField,
    StandardizedFieldRequest,
    DelegationHistory,
    UserHierarchy,
    UserDelegation,
    HierarchyChange,    

)
from django.contrib.auth.models import User
import random
from api.utils.batch import (
    add_contact_in_wati
)
import string
from zohoapi.models import Vendor, InvoiceData,SalesOrder, GmSheet, Offering, Deal,Benchmark
from django.contrib.auth.models import User
import environ
from django.db.models import Prefetch
env = environ.Env()
import requests
import re


def get_exchange_rate(base_currency, target_currency):
    url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"

    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json()

            return data["rates"].get(target_currency)
        except ValueError:
            print("Error parsing JSON response.")
    else:
        print(f"Error: HTTP {response.status_code}")

    return None


def get_value_inside_parentheses(text):
    match = re.search(r"\(([^)]+)\)", text)
    if match:
        return match.group(1)
    return None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "is_staff"]


class PmoDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pmo
        fields = "__all__"
        depth = 1


class EmployeeSerializer(serializers.ModelSerializer):
    is_delete_allowed = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = "__all__"


    def to_representation(self, instance):
        data = super().to_representation(instance)
        permission = (
            instance.user.permissions.filter(role__name="employee").first()
            if instance.user
            else None
        )

        active_roles = []
        active_roles_id = []
        for role in instance.user.roles.all():
            if instance.active_inactive:
                active_roles.append(role.name)
                if role.name in ["pmo","finance","sales"]:
                    active_roles_id.append(role.id)

        data["roles"] = active_roles
        data["add_users"] = active_roles_id
        
        data["sub_role"] = permission.sub_role.name if permission else ""
        data["name"] = instance.first_name + " " + instance.last_name
        data["user_id"] = instance.user.user.id

        return data

class EmployeeDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"
        depth = 1


class SuperAdminDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperAdmin
        fields = "__all__"
        depth = 1


class SalesDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales
        fields = "__all__"
        depth = 1


class FinanceDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finance
        fields = "__all__"
        depth = 1


class HrDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = HR
        fields = "__all__"
        depth = 1

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["name"] = instance.name
        return data


class HrSerializer(serializers.ModelSerializer):
    class Meta:
        model = HR
        fields = "__all__"
        depth = 1


class HrAndOrganisationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        # Handle the conversion based on whether instance is an HR or Organisation object
        if isinstance(instance, HR):
            return {
                "name": instance.organisation.name if instance.organisation else "",
                "image_url": (
                    instance.organisation.image_url.url
                    if instance.organisation and instance.organisation.image_url
                    else ""
                ),
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "email": instance.email,
                "phone": instance.phone,
            }
        elif isinstance(instance, Organisation):
            return {
                "name": instance.name,
                "image_url": (
                    instance.image_url.url if instance and instance.image_url else ""
                ),
            }
        return super().to_representation(instance)


class HrNoDepthSerializer(serializers.ModelSerializer):
    class Meta:
        model = HR
        fields = "__all__"


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = "__all__"




class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"



class UserLoginActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserLoginActivity
        fields = "__all__"



class SentEmailActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = SentEmailActivity
        fields = "__all__"


class SentEmailActivitySerializerDepthOne(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = SentEmailActivity
        fields = "__all__"



class UserTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserToken
        fields = "__all__"


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = "__all__"


class PmoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pmo
        fields = ["id", "name", "email", "phone", "sub_role", "active_inactive"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        permission = (
            instance.user.permissions.filter(role__name="pmo").first()
            if instance.user
            else None
        )

        data["sub_role"] = permission.sub_role.name if permission else ""
        return data



class LeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leader
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        permission = (
            instance.user.permissions.filter(role__name="leader").first()
            if instance.user
            else None
        )

        data["sub_role"] = permission.sub_role.name if permission else ""
        return data



class LeaderDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leader
        fields = "__all__"
        depth = 1



class APILogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", required=False)

    class Meta:
        model = APILog
        fields = ["path", "username", "created_at", "method"]


class SalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Assuming 'permissions' is a related manager, and you want to filter it
        user_permissions = instance.user.permissions.filter(role__name="sales")

        if user_permissions.exists():
            # Extract the sub_role from the first permission (you can adjust this logic)
            data["sub_role"] = user_permissions.first().sub_role.name
        else:
            data["sub_role"] = ""

        return data



class V2AddHRSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=15)
    organisation = serializers.PrimaryKeyRelatedField(
        queryset=Organisation.objects.all()
    )

    class Meta:
        model = HR
        fields = ["email", "first_name", "last_name", "phone", "organisation"]

    def create(self, validated_data):
        email = validated_data["email"].strip().lower()
        # user = User.objects.filter(email=email).first()
        user = User.objects.get(email=email)

        if not user:
            temp_password = "".join(
                random.choices(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits, k=8
                )
            )
            user = User.objects.create_user(
                username=email,
                password=temp_password,
                email=email,
            )
            profile = Profile.objects.create(user=user)
        else:
            profile = Profile.objects.get(user=user)

        hr_role, created = Role.objects.get_or_create(name="hr")
        profile.roles.add(hr_role)

        hr = HR.objects.create(
            user=profile,
            first_name=validated_data["first_name"].strip().title(),
            last_name=validated_data["last_name"].strip().title(),
            email=email,
            phone=validated_data["phone"],
            organisation=validated_data["organisation"],
        )
        name = hr.first_name + " " + hr.last_name
        add_contact_in_wati("hr", name, hr.phone)

        return hr



class TicketSerializer(serializers.ModelSerializer):
    is_sla_breached = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Tickets
        fields = "__all__"

    def get_is_sla_breached(self, obj):
        # Call the model's method to check SLA breach
        return obj.is_sla_breached

    def get_time_remaining(self, obj):
        # Get time remaining until SLA breach
        time_to_breach = obj.get_time_to_sla_breach()
        if time_to_breach:
            hours, remainder = divmod(time_to_breach.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return {
                "hours": int(hours),
                "minutes": int(minutes),
                "seconds": int(seconds),
                "total_seconds": int(time_to_breach.total_seconds()),
            }
        return None


class TicketSerializerDepthOne(serializers.ModelSerializer):
    is_sla_breached = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Tickets
        fields = "__all__"
        depth = 2

    def get_is_sla_breached(self, obj):
        return obj.is_sla_breached

    def get_time_remaining(self, obj):
        time_to_breach = obj.get_time_to_sla_breach()
        if time_to_breach:
            hours, remainder = divmod(time_to_breach.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return {
                "hours": int(hours),
                "minutes": int(minutes),
                "seconds": int(seconds),
                "total_seconds": int(time_to_breach.total_seconds()),
            }
        return None



class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(
        read_only=True
    )  # Display the username as string
    ticket_id = serializers.PrimaryKeyRelatedField(
        queryset=Tickets.objects.all(), source="ticket", write_only=True
    )

    class Meta:
        model = Comment
        fields = ["id", "user", "message", "created_at", "edited_at", "ticket_id"]
        read_only_fields = ["id", "user", "created_at", "edited_at"]

    def create(self, validated_data):
        ticket = validated_data.pop("ticket")
        comment = Comment.objects.create(**validated_data)
        ticket.comments.add(comment)  # Add the comment to the ticket
        return comment




class SendTestMailSerializer(serializers.Serializer):
    project_event_id = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=True)


class UserRolePermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRolePermissions
        fields = "__all__"


class SubRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubRole
        fields = "__all__"


class UserRolePermissionsSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = UserRolePermissions
        fields = "__all__"
        depth = 1





class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class RoleSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"
        depth = 1




class StandardizedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardizedField
        fields = "__all__"


class StandardizedFieldRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardizedFieldRequest
        fields = "__all__"


class StandardizedFieldRequestDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardizedFieldRequest
        fields = "__all__"
        depth = 1





class UserHierarchySerializer(serializers.ModelSerializer):
    """Serializer for UserHierarchy model with relationship details"""

    subordinate_name = serializers.SerializerMethodField()
    supervisor_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = UserHierarchy
        fields = [
            "id",
            "subordinate",
            "supervisor",
            "role",
            "is_primary",
            "hierarchy_level",
            "created_at",
            "updated_at",
            "subordinate_name",
            "supervisor_name",
            "role_name",
        ]

    def get_subordinate_name(self, obj):
        """Get the name of the subordinate user"""
        if obj.subordinate:
            full_name = (
                f"{obj.subordinate.first_name} {obj.subordinate.last_name}".strip()
            )
            return full_name if full_name else obj.subordinate.username
        return None

    def get_supervisor_name(self, obj):
        """Get the name of the supervisor user"""
        if obj.supervisor:
            full_name = (
                f"{obj.supervisor.first_name} {obj.supervisor.last_name}".strip()
            )
            return full_name if full_name else obj.supervisor.username
        return None

    def get_role_name(self, obj):
        """Get the name of the role"""
        return obj.role.name if obj.role else None

    def validate(self, data):
        """Validate the hierarchy relationship"""
        # Ensure subordinate and supervisor are different
        if data.get("subordinate") == data.get("supervisor"):
            raise serializers.ValidationError("A user cannot be their own supervisor.")

        # Ensure no circular hierarchy is created
        if "subordinate" in data and "supervisor" in data and "role" in data:
            subordinate = data["subordinate"]
            supervisor = data["supervisor"]
            role = data["role"]

            # Check if this would create a circular relationship
            def check_circular_dependency(
                current_supervisor, target_subordinate, current_role
            ):
                """Check recursively if a circular dependency would be created"""
                # Get all supervisors of the current supervisor
                higher_relationships = UserHierarchy.objects.filter(
                    subordinate=current_supervisor, role=current_role
                )

                for rel in higher_relationships:
                    if rel.supervisor == target_subordinate:
                        return True  # Found a circular reference

                    # Check the next level up
                    if check_circular_dependency(
                        rel.supervisor, target_subordinate, current_role
                    ):
                        return True

                return False

            if check_circular_dependency(supervisor, subordinate, role):
                raise serializers.ValidationError(
                    "This would create a circular hierarchy relationship."
                )

        return data


class HierarchyChangeSerializer(serializers.ModelSerializer):
    """Serializer for HierarchyChange model with related names"""

    changed_by_name = serializers.SerializerMethodField()
    subordinate_name = serializers.SerializerMethodField()
    supervisor_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = HierarchyChange
        fields = [
            "id",
            "changed_by",
            "change_type",
            "subordinate",
            "supervisor",
            "role",
            "details",
            "changed_at",
            "changed_by_name",
            "subordinate_name",
            "supervisor_name",
            "role_name",
        ]

    def get_changed_by_name(self, obj):
        """Get the name of the user who made the change"""
        if obj.changed_by:
            full_name = (
                f"{obj.changed_by.first_name} {obj.changed_by.last_name}".strip()
            )
            return full_name if full_name else obj.changed_by.username
        return None

    def get_subordinate_name(self, obj):
        """Get the name of the subordinate user"""
        if obj.subordinate:
            full_name = (
                f"{obj.subordinate.first_name} {obj.subordinate.last_name}".strip()
            )
            return full_name if full_name else obj.subordinate.username
        return None

    def get_supervisor_name(self, obj):
        """Get the name of the supervisor user"""
        if obj.supervisor:
            full_name = (
                f"{obj.supervisor.first_name} {obj.supervisor.last_name}".strip()
            )
            return full_name if full_name else obj.supervisor.username
        return None

    def get_role_name(self, obj):
        """Get the name of the role"""
        return obj.role.name if obj.role else None


class UserDelegationSerializer(serializers.ModelSerializer):
    """Serializer for UserDelegation model with user and role details"""

    delegated_from_name = serializers.SerializerMethodField()
    delegated_to_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = UserDelegation
        fields = [
            "id",
            "delegated_from",
            "delegated_to",
            "role",
            "permissions",
            "status",
            "start_date",
            "end_date",
            "reason",
            "notes",
            "created_at",
            "updated_at",
            "delegated_from_name",
            "delegated_to_name",
            "role_name",
            "is_active",
        ]

    def get_delegated_from_name(self, obj):
        """Get the name of the user delegating permissions"""
        if obj.delegated_from:
            full_name = f"{obj.delegated_from.first_name} {obj.delegated_from.last_name}".strip()
            return full_name if full_name else obj.delegated_from.username
        return None

    def get_delegated_to_name(self, obj):
        """Get the name of the user receiving delegated permissions"""
        if obj.delegated_to:
            full_name = (
                f"{obj.delegated_to.first_name} {obj.delegated_to.last_name}".strip()
            )
            return full_name if full_name else obj.delegated_to.username
        return None

    def get_role_name(self, obj):
        """Get the name of the role"""
        return obj.role.name if obj.role else None

    def get_is_active(self, obj):
        """Check if the delegation is currently active"""
        return obj.is_active

    def validate(self, data):
        """Validate the delegation data"""
        # Ensure start_date is before end_date
        if "start_date" in data and "end_date" in data:
            if data["start_date"] >= data["end_date"]:
                raise serializers.ValidationError(
                    "The end date must be after the start date."
                )

        # Ensure a user is not delegating to themselves
        if data.get("delegated_from") == data.get("delegated_to"):
            raise serializers.ValidationError(
                "A user cannot delegate permissions to themselves."
            )

        return data


class UserDelegationSerializerDepthOne(serializers.ModelSerializer):

    class Meta:
        model = UserDelegation
        fields = "__all__"
        depth = 2


class DelegationHistorySerializer(serializers.ModelSerializer):
    """Serializer for DelegationHistory model with delegation details"""

    delegation_id = serializers.SerializerMethodField()
    delegated_from_name = serializers.SerializerMethodField()
    delegated_to_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    delegation_created_at = serializers.SerializerMethodField()
    delegation_end_date = serializers.SerializerMethodField()

    class Meta:
        model = DelegationHistory
        fields = [
            "id",
            "delegation",
            "action",
            "performed_at",
            "content_type",
            "object_id",
            "delegation_id",
            "delegated_from_name",
            "delegated_to_name",
            "role_name",
            "delegation_created_at",
            "delegation_end_date",
        ]

    def get_delegation_id(self, obj):
        """Get the ID of the delegation"""
        return obj.delegation.id if obj.delegation else None

    def get_delegated_from_name(self, obj):
        """Get the name of the user delegating permissions"""
        if obj.delegation and obj.delegation.delegated_from:
            from_user = obj.delegation.delegated_from
            full_name = f"{from_user.first_name} {from_user.last_name}".strip()
            return full_name if full_name else from_user.username
        return None

    def get_delegated_to_name(self, obj):
        """Get the name of the user receiving delegated permissions"""
        if obj.delegation and obj.delegation.delegated_to:
            to_user = obj.delegation.delegated_to
            full_name = f"{to_user.first_name} {to_user.last_name}".strip()
            return full_name if full_name else to_user.username
        return None

    def get_role_name(self, obj):
        """Get the name of the role"""
        return (
            obj.delegation.role.name if obj.delegation and obj.delegation.role else None
        )

    def get_delegation_created_at(self, obj):
        """Get the creation date of the delegation"""
        return obj.delegation.created_at if obj.delegation else None

    def get_delegation_end_date(self, obj):
        """Get the end date of the delegation"""
        return obj.delegation.end_date if obj.delegation else None
    


class GmSheetDetailedSerializer(serializers.ModelSerializer):
    sales_name = serializers.CharField(source="sales.name", allow_null=True)

    class Meta:
        model = GmSheet
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        deal = Deal.objects.filter(gm_sheet=instance).first()
        if deal:
            data["deal_name"] = deal.deal_name
        else:
            data["deal_name"] = ""
        return data


class OfferingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offering
        fields = "__all__"


class GmSheetDetailedOfferingSerializer(serializers.ModelSerializer):
    sales_name = serializers.CharField(source="sales.name", allow_null=True)

    class Meta:
        model = GmSheet
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        offering = Offering.objects.filter(gm_sheet=instance, is_won=True).first()
        data["offering_data"] = OfferingSerializer(offering).data if offering else None

        return data


class GmSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = GmSheet
        fields = "__all__"


class EmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        permission = (
            instance.user.permissions.filter(role__name="employee").first()
            if instance.user
            else None
        )

        active_roles = []
        active_roles_id = []
        for role in instance.user.roles.all():
            if instance.active_inactive:
                active_roles.append(role.name)
                if role.name in ["curriculum","pmo","finance","sales"]:
                    active_roles_id.append(role.id)

        data["roles"] = active_roles
        data["add_users"] = active_roles_id
        
        data["sub_role"] = permission.sub_role.name if permission else ""
        data["name"] = instance.first_name + " " + instance.last_name
        data["user_id"] = instance.user.user.id

        return data


class GmSheetSalesOrderExistsSerializer(serializers.ModelSerializer):
    sales_order_exists = serializers.SerializerMethodField()
    offering_grossmargin = serializers.SerializerMethodField()

    class Meta:
        model = GmSheet
        fields = "__all__"

    def get_sales_order_exists(self, obj):
        return SalesOrder.objects.filter(gm_sheet_id=obj.id).exists()

    def get_offering_grossmargin(self, obj):
        offerings = Offering.objects.filter(gm_sheet=obj)
        return [
            offering.gross_margin for offering in offerings if offering.gross_margin
        ]


class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        fields = "__all__"
