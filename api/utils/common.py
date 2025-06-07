from django.db import transaction
from ..models import (
    User,
    Profile,
    Role,
    Notification,
    SubRole,
    UserRolePermissions,
)
import string
import random
from datetime import datetime
import requests
from django.utils import timezone

import environ
from api.utils.constants import ROLE_PERMISSIONS, DEFAULT_PERMISSIONS

env = environ.Env()


def create_user_permission_for_role(role, sub_role, profile):
    role = Role.objects.get(name=role)
    sub_role = SubRole.objects.get(name=sub_role)
    user_permission, created = UserRolePermissions.objects.get_or_create(
        role=role, sub_role=sub_role
    )
    # Add permissions as a list of dictionaries (JSONField expects this)
    if created:
        user_permission.permission = (
            ROLE_PERMISSIONS[role.name]
            if role.name in ROLE_PERMISSIONS
            else DEFAULT_PERMISSIONS
        )
        # Save the changes to the database
        user_permission.save()
    profile.permissions.add(user_permission)
    profile.save()
    return profile


def create_notification(user, path, message):
    notification = Notification.objects.create(user=user, path=path, message=message)
    return notification



def get_purchase_order(purchase_orders, purchase_order_id):
    for po in purchase_orders:
        if po.get("purchaseorder_id") == purchase_order_id:
            return po
    return None

