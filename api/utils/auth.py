from ..models import (
    Pmo,
    HR,
    SuperAdmin,
    Finance,
    Sales,
    Leader,
    UserLoginActivity,
    UserRolePermissions,
    Employee
)
from zohoapi.models import Vendor,ZohoVendor
from zohoapi.serializers import (
    ZohoVendorSerializer,
)
from ..serializers import (
    EmployeeDepthOneSerializer,
    PmoDepthOneSerializer,
    HrDepthOneSerializer,
    SuperAdminDepthOneSerializer,
    FinanceDepthOneSerializer,
    SalesDepthOneSerializer,
    LeaderDepthOneSerializer,
    UserRolePermissionsSerializerDepthOne,
)
from rest_framework import status
from django.utils import timezone
from zohoapi.serializers import VendorDepthOneSerializer
from django.db.models import Q

ROLE_SERIALIZERS = {
    "pmo": PmoDepthOneSerializer,
    "superadmin": SuperAdminDepthOneSerializer,
    "finance": FinanceDepthOneSerializer,
    "hr": HrDepthOneSerializer,
    "sales": SalesDepthOneSerializer,
    "leader": LeaderDepthOneSerializer,
    "employee": EmployeeDepthOneSerializer,
    "vendor": VendorDepthOneSerializer,
}


def get_user_for_active_inactive(role, email):
    try:
        if role == "pmo":
            user = Pmo.objects.get(email=email)
        if role == "vendor":
            user = Vendor.objects.get(email=email)
        if role == "hr":
            user = HR.objects.get(email=email)
        if role == "superadmin":
            user = SuperAdmin.objects.get(email=email)
        if role == "finance":
            user = Finance.objects.get(email=email)
        if role == "sales":
            user = Sales.objects.get(email=email)
        if role == "leader":
            user = Leader.objects.get(email=email)
        if role == "employee":
            user = Employee.objects.get(email=email)
        return user
    except Exception as e:
        print(str(e))
        return None


def get_active_roles(user):
    active_roles = []
    roles = user.profile.roles.filter(~Q(name="ctt_faculty") & ~Q(name="ctt_pmo"))
    for role in roles:
        user_data = get_user_for_active_inactive(role.name, user.profile.user.username)
        if user_data and user_data.active_inactive:
            active_roles.append(role.name)
    return active_roles


def get_role_response(user, user_profile_role, roles):
    try:
        serializer_class = ROLE_SERIALIZERS.get(user_profile_role)
        if not serializer_class:
            return None, "Failed to get user details"
        profile_role_obj = getattr(user.profile, user_profile_role.replace("_", ""))
        if not profile_role_obj.active_inactive:
            return None, "User role is not active"
        serializer = serializer_class(profile_role_obj)
        response_data = {
            **serializer.data,
            "roles": roles,
            "user": {**serializer.data["user"], "type": user_profile_role},
            "last_login": user.last_login,
        }
        additional_data = {}
        if user_profile_role == "vendor":
            print(serializer.data["vendor_id"])
            zoho_vendor = ZohoVendor.objects.get(contact_id=serializer.data["vendor_id"])
            login_timestamp = timezone.now()
            UserLoginActivity.objects.create(
                user=user, timestamp=login_timestamp
            )
            response_data.update(
                {
                    "zoho_vendor": ZohoVendorSerializer(zoho_vendor).data,
                    "message": "Role changed to billing",
                }
            )
        elif user_profile_role == "hr":
            response_data.update(additional_data)
        if response_data["user"] and response_data["user"]["permissions"]:
            permission_ids = response_data["user"]["permissions"]
            if permission_ids:
                user_permissions = UserRolePermissions.objects.filter(id__in=permission_ids)
                response_data["permissions"] = UserRolePermissionsSerializerDepthOne(
                    user_permissions, many=True
                ).data
            else:
                response_data["permissions"] = []
        return response_data, None
    except Exception as e:
        print(str(e))
        return None, "Failed to get user details due to an error"


def get_user_data(user, current_role=None):
    if not user.profile:
        return None, "No Profile found for the user"
    elif user.profile.roles.count() == 0:
        return None, "No Roles found in profile"
    user_roles =  user.profile.roles.all()
    first_user_role_name = user_roles.first().name
    role_names = [role.name for role in user_roles]
    if current_role and current_role in role_names:
        user_profile_role = current_role
    elif user_roles.count() == 1:
        user_profile_role = first_user_role_name
    elif set(role_names) == {"coach", "vendor"}:
        user_profile_role = "coach"
    else:
        other_roles = user_roles.exclude(name__in=["coach", "vendor"])
        if other_roles.exists():
            user_profile_role = other_roles.first().name
        else:
            user_profile_role = first_user_role_name
    roles = get_active_roles(user)
    response_data, error = get_role_response(user, user_profile_role, roles)
    sub_role = ""
    if current_role:
        permission = user.profile.permissions.filter(role__name=current_role).first()
        sub_role = permission.sub_role.name if permission else ""
        response_data["sub_role"] = sub_role
    return response_data, error


def get_user_with_delegation(request, current_role=None, brand="", platform=None):
    """
    Extension of your get_user_data function to handle delegations
    """
    user = request.user
    if hasattr(request, "acting_as") and request.acting_as:
        acting_as = request.acting_as
        delegation_role = request.delegation_role
        delegated_user_data, error = get_user_data(
            acting_as, delegation_role.name
        )
        if error:
            user_data, error = get_user_data(user, current_role)
            return user_data, error
        delegate_data, _ = get_user_data(user, None)
        delegated_user_data["under_delegation"] = True
        delegated_user_data["original_user"] = {
            "id": user.id,
            "username": user.username,
            "name": delegate_data.get("name", user.username),
        }
        delegated_user_data["delegation_info"] = {
            "role": delegation_role.name,
            "start_date": request.delegation.start_date,
            "end_date": request.delegation.end_date,
        }
        return delegated_user_data, None
    else:
        return get_user_data(user, current_role)



def update_user_timezone(user, timezone):
    try:
        user.profile.timezone = timezone
        user.profile.save()
        return True
    except Exception as e:
        print(str(e))
        return False
