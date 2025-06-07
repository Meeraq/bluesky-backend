from zohoapi.models import Vendor
import json
import random
import string
from rest_framework.response import Response
from django.db.models import Q, Subquery, OuterRef, Value, BooleanField, Max
from django.db import transaction, IntegrityError
from rest_framework import status
import json
import uuid
import logging
from openai import OpenAI
from datetime import datetime
from api.utils.constants import (
    ROLE_PERMISSIONS,
    DEFAULT_PERMISSIONS,
)
from api.models import (
    User,
    Role,
    Pmo,
    HR,
    Profile,
    SubRole,
    UserRolePermissions,
    UserHierarchy,
    UserDelegation,
)
from rest_framework import serializers
import os
from twilio.rest import Client
from typing import Optional
import environ
import re
from zohoapi.models import Offering
from api.serializers import OfferingSerializer
env = environ.Env()



def create_user_with_profile(email, username):
    temp_password = "".join(
        random.choices(
            string.ascii_uppercase + string.ascii_lowercase + string.digits, k=8
        )
    )
    user = User.objects.create_user(
        username=username, password=temp_password, email=email
    )
    profile = Profile.objects.create(user=user)
    return user, profile


def add_role_to_profile(profile, role_name):
    role, created = Role.objects.get_or_create(name=role_name)
    profile.roles.add(role)
    profile.save()


def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        raise RuntimeError(f"Set the {name} environment variable")


def generate_temp_password():
    return "".join(
        random.choices(
            string.ascii_uppercase + string.ascii_lowercase + string.digits, k=8
        )
    )


def create_user_profile(email):
    user = User.objects.create_user(
        username=email, password=generate_temp_password(), email=email
    )
    profile = Profile.objects.create(user=user)
    return user, profile


def get_or_create_user_profile(email):
    user = User.objects.filter(email=email).first()
    if not user:
        user, profile = create_user_profile(email)
    else:
        profile = Profile.objects.get(user=user)
    return user, profile


def create_user_profile_and_role(data, role_name, serializer_class):
    name = data.get("name")
    email = data.get("email", "").strip().lower()
    phone = data.get("phone")
    # need to be check done also
    # if not (name and phone and email):
    #     return {
    #         "error": "Name, phone, and email are mandatory fields."
    #     }, status.HTTP_400_BAD_REQUEST

    user = User.objects.filter(email=email).first()
    if not user:
        user = User.objects.create_user(
            username=email,
            email=email,
            password=User.objects.make_random_password(),
        )
    profile, _ = Profile.objects.get_or_create(user=user)
    role, _ = Role.objects.get_or_create(name=role_name)
    profile.roles.add(role)
    profile.save()

    serializer = serializer_class(data=data)
    if serializer.is_valid():
        serializer.save(user=profile)
        return serializer.data, status.HTTP_201_CREATED
    else:
        return serializer.errors, status.HTTP_400_BAD_REQUEST


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




user_hierarchy_modal_mapping = {
    "SalesOrder": "added_by__in",
    "ClientInvoice": "sales_order__added_by__in",
    "GmSheet": "added_by__in",
    "HandoverDetails": "added_by__in",
    "Deal": "added_by__in",
    "Company": "added_by__in",
    "Contact": "added_by__in",
}


def get_subordinates_of_a_user_in_role(modal, user, role):
    try:
        subordinates = list(
            UserHierarchy.objects.filter(
                supervisor__user__user=user, role=role
            ).values_list("supervisor__user__user", flat=True)
        )
        filter_key = user_hierarchy_modal_mapping.get(modal, "")
        if filter_key and subordinates:
            # Return a Q object instead of a dictionary
            return Q(**{filter_key: subordinates})
        
        # Return an empty Q object instead of empty dictionary
        return Q()

    except Exception as e:
        print(str(e))
        return Q()



def get_user_deligation_functionlity_permission(user, functionality, role):
    try:
        user_deligation = UserDelegation.objects.filter(
            delegated_to__user__user=user, status="active", role=role
        ).first()
        if user_deligation:
            for permission in user_deligation.permissions:
                if permission["functionality"] == functionality:

                    return permission, user_deligation.delegated_from
            return [], None
    except Exception as e:
        print(str(e))
        return [], None
    
def parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str)
    except (TypeError, ValueError):
        return None



def handle_offerings_update(gm_sheet, offerings_data):
    existing_offerings = Offering.objects.filter(gm_sheet=gm_sheet)
    existing_ids = {offering.id for offering in existing_offerings}
    incoming_ids = {
        offering.get("id") for offering in offerings_data if offering.get("id")
    }

    # Delete offerings that are in the database but not in the incoming data
    to_delete_ids = existing_ids - incoming_ids
    if to_delete_ids:
        Offering.objects.filter(id__in=to_delete_ids).delete()

    for offering_data in offerings_data:
        offering_id = offering_data.get("id")
        if offering_id:
            try:
                offering_instance = Offering.objects.get(
                    id=offering_id, gm_sheet=gm_sheet
                )
                offering_serializer = OfferingSerializer(
                    offering_instance, data=offering_data, partial=True
                )
                if offering_serializer.is_valid():
                    offering_serializer.save()
                else:
                    return offering_serializer.errors, status.HTTP_400_BAD_REQUEST
            except Offering.DoesNotExist:
                return {"error": "Offering not found"}, status.HTTP_404_NOT_FOUND
        else:
            offering_data["gm_sheet"] = gm_sheet.id
            offering_serializer = OfferingSerializer(data=offering_data)
            if offering_serializer.is_valid():
                offering_serializer.save()
            else:
                return offering_serializer.errors, status.HTTP_400_BAD_REQUEST
    return None, None

