import calendar
from datetime import date, datetime, time
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from django.urls import reverse
import requests
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
import calendar
from os import name
import time
import django_filters
from api.utils.pagination import CustomPageNumberPagination
from django.apps import apps
from django.db import DatabaseError
from django.utils.timezone import make_aware
from datetime import datetime, time
from django.db.models import (
    ForeignKey,
    ManyToManyField,
    F,
    ExpressionWrapper,
    DateTimeField,
    Avg,
)

from django.core.mail import send_mail, get_connection
from django.utils.decorators import method_decorator
import re
import pytz
from typing import Tuple, Dict, Optional
import logging
from openpyxl import Workbook
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.db import transaction, IntegrityError
from django.core.mail import EmailMessage, get_connection
from rest_framework.exceptions import AuthenticationFailed, ValidationError, NotFound
from django.core.exceptions import ObjectDoesNotExist
from operationsBackend import settings
from api.utils.users import add_new_pmo
from .serializers import (
    UserSerializer,
    LeaderDepthOneSerializer,
    LeaderSerializer,
    TicketSerializer,
    HrSerializer,
    OrganisationSerializer,
    NotificationSerializer,
    UserLoginActivitySerializer,
    SentEmailActivitySerializer,
    SentEmailActivitySerializerDepthOne,
    PmoSerializer,
    APILogSerializer,
    SalesSerializer,
    TicketSerializerDepthOne,
    CommentSerializer,
    SendTestMailSerializer,
    UserRolePermissionsSerializer,
    SubRoleSerializer,
    RoleSerializer,
    RoleSerializerDepthOne,
    EmployeeSerializer,
    StandardizedFieldRequestDepthOneSerializer,
    StandardizedFieldSerializer,
    UserHierarchySerializer,
    UserDelegationSerializer,
    UserDelegationSerializerDepthOne,
    GmSheetSalesOrderExistsSerializer,
    OfferingSerializer,
    GmSheetDetailedOfferingSerializer,
    GmSheetDetailedSerializer,
    BenchmarkSerializer,
    DelegationHistorySerializer,
    HierarchyChangeSerializer,
    HierarchyChange,
    HrAndOrganisationSerializer,
    GmSheetSerializer,
)
from django.template import Template as RenderTemplate, Context as RenderContext

from zohoapi.serializers import (
    PurchaseOrderGetSerializer,
    ZohoVendorSerializer,
)
from .filters import TicketFilter, GmSheetListFilter
from zohoapi.models import (
    Vendor,
    Benchmark,
    SalesOrder,
    ClientInvoice,
    GmSheet,
    Offering,
)
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ObjectDoesNotExist, FieldDoesNotExist
from django.db.models.functions import Concat, TruncDate
from .permissions import IsInRoles
from rest_framework import generics, filters
from django.utils.crypto import get_random_string
import math
import uuid
from rest_framework import generics
from datetime import datetime, timedelta
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from api.utils.email import (
    send_mail_templates,
)
from api.utils.datetime import (
    format_timestamp,
    get_date,
    get_time,
    get_weeks_for_current_month,
    get_formatted_time_with_timezone_name,
    get_formatted_date_with_timezone_name,
)
from api.utils.constants import ROLE_PERMISSIONS, FIELD_NAME_VALUES, MODELS_TO_UPDATE
from api.utils.external import (
    refresh_microsoft_access_token,
    generateManagementToken,
)
from api.utils.batch import add_contact_in_wati
from api.utils.auth import update_user_timezone
from api.utils.profiles import update_profiles_active_inactive
from .models import (
    Profile,
    Leader,
    Pmo,
    OTP,
    HR,
    Organisation,
    Tickets,
    Notification,
    UserLoginActivity,
    SentEmailActivity,
    Role,
    UserToken,
    APILog,
    Finance,
    Sales,
    TableHiddenColumn,
    get_user_name,
    CalendarEvent,
    Comment,
    UserRolePermissions,
    SubRole,
    SuperAdmin,
    TicketFeedback,
    Employee,
    StandardizedField,
    StandardizedFieldRequest,
    UserHierarchy,
    UserDelegation,
    DelegationHistory,
)
import jwt
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import string
import random
from django.db.models import (
    Q,
    Min,
    Exists,
    OuterRef,
    Case,
    When,
    Subquery,
    OuterRef,
    BooleanField,
    F,
    Prefetch,
    QuerySet,
    Value,
    Sum,
)
from django.db.models.functions import Cast, Now
from django.db import models
from collections import defaultdict
from rest_framework import status
from rest_framework.views import APIView
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.tokens import get_token_generator
from urllib.parse import urlencode
from django.http import HttpResponseRedirect
import pdfkit
import os
from django.utils.dateparse import parse_datetime
import openai
from openai import OpenAI

# Create your views here.
from collections import defaultdict
from django.http import HttpResponse
from time import sleep
from django.db.models import Max, Count, IntegerField, DurationField
from openai import OpenAI
import environ
from api.utils.methods import (
    create_user_permission_for_role,
    parse_date,
    get_subordinates_of_a_user_in_role,
    handle_offerings_update,
)
from django.views.decorators.csrf import csrf_exempt
from api.utils.auth import (
    get_user_data,
    get_active_roles,
    get_role_response,
    get_user_for_active_inactive,
)
import neverbounce_sdk
from twilio.rest import Client

from typing import List


env = environ.Env()

wkhtmltopdf_path = os.environ.get("WKHTMLTOPDF_PATH", r"/usr/local/bin/wkhtmltopdf")

pdfkit_config = pdfkit.configuration(wkhtmltopdf=f"{wkhtmltopdf_path}")
logger = logging.getLogger(__name__)


@receiver(reset_password_token_created)
def password_reset_token_created(
    sender, instance, reset_password_token, *args, **kwargs
):
    app_name = instance.request.data.get("app_name", "")
    user = reset_password_token.user
    email_plaintext_message = "{}?token={}".format(
        reverse("password_reset:reset-password-request"), reset_password_token.key
    )
    subject = "Meeraq - Forgot Password"
    if (
        user.profile.roles.all().count() == 1
        and user.profile.roles.all().first().name == "coach"
        and user.profile.coach.is_approved == False
    ):
        # link = f'{env("APP_URL")}/create-password/{reset_password_token.key}'
        if app_name == "assessment":
            link = f"{env('ASSESSMENT_APP_URL')}/create-password/{reset_password_token.key}"
        else:
            link = f"{env('APP_URL')}/create-password/{reset_password_token.key}"
        name = user.profile.coach.first_name

        send_mail_templates(
            "coach_templates/create_new_password.html",
            [reset_password_token.user.email],
            "Meeraq Platform | Create New Password",
            {"name": name, "createPassword": link},
            [],  # no bcc
        )

        return None
    else:
        name = get_user_name(user)
        if app_name == "assessment":
            link = f"{env('ASSESSMENT_APP_URL')}/create-password/{reset_password_token.key}"
        elif app_name == "zoho":
            link = f"{env('ZOHO_APP_URL')}/reset-password/{reset_password_token.key}"
            # not sending when requested from vendor portal but user is not vendor in our system
            if not user.profile.roles.filter(name="vendor").exists():
                return None
        else:
            link = f"{env('APP_URL')}/create-password/{reset_password_token.key}"

        send_mail_templates(
            "forgot_password.html",
            [reset_password_token.user.email],
            "Meeraq Platform | Password Reset",
            {"name": name, "resetPassword": link},
            [],  # no bcc
        )


@api_view(["GET"])
@permission_classes(
    [IsAuthenticated, IsInRoles("coach", "pmo", "learner", "hr", "sales")]
)
def get_hr(request):
    try:
        # Get all the Coach objects
        hr = HR.objects.all()

        # Serialize the Coach objects
        serializer = HrSerializer(hr, many=True)

        # Return the serialized Coach objects as the response
        return Response(serializer.data, status=200)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_organisation(request):
    orgs = Organisation.objects.all()
    serializer = OrganisationSerializer(orgs, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def add_organisation(request):
    print(request.data.get("image_url", ""))
    org = Organisation.objects.create(
        name=request.data.get("name", ""), image_url=request.data.get("image_url", "")
    )
    orgs = Organisation.objects.all()
    serializer = OrganisationSerializer(orgs, many=True)
    return Response(
        {"message": "Organisation added successfully.", "details": serializer.data},
        status=200,
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def update_organisation(request, org_id):
    try:
        org = Organisation.objects.get(id=org_id)
    except Organisation.DoesNotExist:
        return Response({"error": "Organization not found"}, status=404)

    serializer = OrganisationSerializer(org, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Organization updated successfully", "data": serializer.data}
        )
    return Response(serializer.errors, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def add_hr(request):
    try:
        email = request.data.get("email", "").strip().lower()
        with transaction.atomic():
            user = User.objects.filter(email=email).first()
            if not user:
                temp_password = "".join(
                    random.choices(
                        string.ascii_uppercase + string.ascii_lowercase + string.digits,
                        k=8,
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

            organisation = Organisation.objects.filter(
                id=request.data.get("organisation")
            ).first()

            hr = HR.objects.create(
                user=profile,
                first_name=request.data.get("first_name").strip().title(),
                last_name=request.data.get("last_name").strip().title(),
                email=email,
                phone=request.data.get("phone"),
                organisation=organisation,
            )
            create_user_permission_for_role("Hr", "Manager", profile)
            name = hr.first_name + " " + hr.last_name
            add_contact_in_wati("hr", name, hr.phone)

            hrs = HR.objects.all()
            serializer = HrSerializer(hrs, many=True)
            return Response(
                {"message": "HR added successfully", "details": serializer.data},
                status=200,
            )

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to add HR"}, status=400)


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def update_hr(request, hr_id):
    try:
        hr = HR.objects.get(id=hr_id)
    except HR.DoesNotExist:
        return Response({"error": "HR not found"}, status=status.HTTP_404_NOT_FOUND)
    # Get the associated user profile
    with transaction.atomic():
        # Update HR instance
        serializer = HrSerializer(hr, data=request.data, partial=True)
        if serializer.is_valid():
            new_email = (
                request.data.get("email", "").strip().lower()
            )  # Get the new email from the request
            existing_user = (
                User.objects.filter(email=new_email).exclude(username=hr.email).first()
            )
            if existing_user:
                return Response(
                    {"error": "User with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # saving hr
            updated_hr = serializer.save()
            user = updated_hr.user.user
            name = hr.first_name + " " + hr.last_name
            add_contact_in_wati("hr", name, hr.phone)
            # if email if getting updated -> updating email in all other user present
            if not updated_hr.email.strip().lower() == user.email.strip().lower():
                user.email = new_email
                user.username = new_email
                user.save()
                for role in user.profile.roles.all():
                    if role.name == "pmo":
                        pmo = Pmo.objects.get(user=user.profile)
                        pmo.email = new_email
                        pmo.save()
                    if role.name == "vendor":
                        vendor = Vendor.objects.get(user=user.profile)
                        vendor.email = new_email
                        vendor.save()
            return Response(
                {"message": "HR updated successfully", "data": serializer.data}
            )
        # Handle serializer errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("superadmin")])
def create_pmo(request):
    try:
        data = request.data
        added = add_new_pmo(data=data)
        if added:
            return Response({"message": "PMO added successfully."}, status=201)
        else:
            return Response({"error": "Failed to add pmo"}, status=500)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to add pmo"}, status=500)


@api_view(["PUT"])
@permission_classes([AllowAny, IsInRoles("superadmin")])
def edit_pmo(request):
    # Get data from request
    name = request.data.get("name")
    email = request.data.get("email", "").strip().lower()
    phone = request.data.get("phone")
    sub_role = request.data.get("sub_role")
    pmo_email = request.data.get("pmo_email", "").strip().lower()
    try:
        with transaction.atomic():
            existing_user = (
                User.objects.filter(username=email).exclude(username=pmo_email).first()
            )
            if existing_user:
                return Response(
                    {"error": "User with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            pmo = Pmo.objects.get(email=pmo_email)
            pmo.user.user.username = email
            pmo.user.user.email = email
            pmo.user.user.save()
            pmo.email = email
            pmo.name = name
            pmo.phone = phone
            pmo.sub_role = sub_role
            pmo.save()
            if pmo.phone:
                add_contact_in_wati("pmo", pmo.name, pmo.phone)

            return Response({"message": "PMO updated successfully."}, status=201)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to update pmo."}, status=500)


def updateLastLogin(email):
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = User.objects.get(username=email)
    user.last_login = today
    user.save()


@api_view(["GET"])
@permission_classes([AllowAny])
def get_management_token(request):
    management_token = generateManagementToken()
    return Response(
        {"message": "Success", "management_token": management_token}, status=200
    )


@csrf_exempt
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def get_csrf(request):
    response = Response({"detail": "CSRF cookie set", "csrf_token": get_token(request)})
    response["X-CSRFToken"] = get_token(request)

    return response


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")
    current_role = data.get("current_role")
    if username is None or password is None:
        raise ValidationError({"detail": "Please provide username and password."})
    print("password", password)
    user = authenticate(request, username=username, password=password)

    if user is None:
        raise AuthenticationFailed({"detail": "Invalid credentials."})
    last_login = user.last_login

    login(request, user)
    user_data, error = get_user_data(user, current_role)
    if error:
        return Response({"error": error}, status=400)
    if user_data:
        login_timestamp = timezone.now()
        UserLoginActivity.objects.create(user=user, timestamp=login_timestamp)
        request_timezone = request.data.get("timezone")
        if request_timezone:
            update_user_timezone(user, request_timezone)

        response = Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
            }
        )
        response["X-CSRFToken"] = get_token(request)
        return response
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    if not request.user.is_authenticated:
        raise AuthenticationFailed({"detail": "You're not logged in."})

    logout(request)
    return Response({"detail": "Successfully logged out."})


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def session_view(request):
    current_role = request.query_params.get("current_role")
    user = request.user
    last_login = user.last_login
    user_data, error = get_user_data(user, current_role)
    if error:
        return Response({"error": error}, status=400)
    if user_data:
        request_timezone = request.data.get("timezone")
        if request_timezone:
            update_user_timezone(user, request_timezone)
        response = Response(
            {
                "isAuthenticated": True,
                "user": {**user_data, "last_login": last_login},
            }
        )
        response["X-CSRFToken"] = get_token(request)
        return response
    else:
        return Response({"error": "Invalid user type"}, status=400)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def generate_otp(request):
    try:
        user = User.objects.get(username=request.data["email"])
        platform = request.data.get("platform", "unknown")
        if platform == "mobile" and not any(
            role.name == "learner" for role in user.profile.roles.all()
        ):
            return Response({"error": "User does not exist"}, status=400)

        try:
            # Check if OTP already exists for the user
            otp_obj = OTP.objects.get(user=user)
            otp_obj.delete()
        except OTP.DoesNotExist:
            pass
        # Generate OTP and save it to the database
        otp = get_random_string(length=6, allowed_chars="0123456789")

        created_otp = OTP.objects.create(user=user, otp=otp)
        print("created_otp", created_otp)
        user_data, error = get_user_data(user, None)
        if error:
            return Response({"error": "User does not exist"}, status=400)
        name = user_data.get("name") or user_data.get("first_name") or "User"
        # Send OTP on email to learner
        subject = "MyMentor Login OTP" if platform == "mobile" else f"Meeraq Login OTP"
        message = (
            f"Dear {name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}"
        )
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.username])
        microsoft_auth_url = (
            f'{env("BACKEND_URL")}/api/microsoft/oauth/{request.data["email"]}/'
        )
        user_token_present = False
        try:
            user_token = UserToken.objects.get(
                user_profile__user__username=request.data["email"]
            )
            if user_token:
                user_token_present = True
        except Exception as e:
            pass

        send_mail_templates(
            "login_with_otp.html",
            [user],
            subject,
            {
                "name": name,
                "otp": created_otp.otp,
                "email": request.data["email"],
                "microsoft_auth_url": microsoft_auth_url,
                "user_token_present": user_token_present,
            },
            [],  # no bcc
        )
        return Response({"message": f"OTP has been sent to {user.username}!"})

    except Exception as e:
        # Handle the case where the user with the given email does not exist
        print(str(e))

        return Response({"error": "Failed to send otp."}, status=400)

    except Exception as e:
        print("hello", str(e))
        # Handle any other exceptions
        return Response({"error": str(e)}, status=500)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def validate_otp(request):
    otp_obj = (
        OTP.objects.filter(
            user__username=request.data["email"], otp=request.data["otp"]
        )
        .order_by("-created_at")
        .first()
    )
    data = request.data
    platform = data.get("platform", "unknown")
    current_role = data.get("current_role")

    if otp_obj is None:
        raise AuthenticationFailed("Invalid OTP")

    user = otp_obj.user
    user_email = request.data["email"]
    otp_obj.delete()
    last_login = user.last_login
    login(request, user)
    user_data, error = get_user_data(user, current_role)
    if error:
        return Response({"error": error}, status=400)
    if user_data:
        login_timestamp = timezone.now()
        UserLoginActivity.objects.create(
            user=user, timestamp=login_timestamp, platform=platform
        )
        request_timezone = request.data.get("timezone")
        if request_timezone:
            update_user_timezone(user, request_timezone)
        response = Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
            }
        )
        response["X-CSRFToken"] = get_token(request)
        return response
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("coach", "pmo", "learner", "hr")])
def get_notifications(request, user_id):
    notifications = Notification.objects.filter(user__id=user_id).order_by(
        "-created_at"
    )
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsInRoles("coach", "pmo", "learner", "hr")])
def mark_all_notifications_as_read(request):
    notifications = Notification.objects.filter(
        read_status=False, user__id=request.data["user_id"]
    )
    notifications.update(read_status=True)
    return Response("Notifications marked as read.")


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsInRoles("coach", "pmo", "learner", "hr")])
def mark_notifications_as_read(request):
    user_id = request.data.get("user_id")
    notification_ids = request.data.get("notification_ids")

    if user_id is None or notification_ids is None:
        return Response("Both user_id and notification_ids are required.", status=400)

    print("abcd")

    notifications = Notification.objects.filter(
        id=notification_ids, user__id=user_id, read_status=False
    )

    notifications.update(read_status=True)
    return Response("Notifications marked as read.")


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("coach", "pmo", "learner", "hr")])
def unread_notification_count(request, user_id):
    count = Notification.objects.filter(user__id=user_id, read_status=False).count()
    return Response({"count": count})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_user_role(request, user_id):
    user_role = request.data.get("user_role", "")
    user = User.objects.get(id=user_id)
    if not user.profile:
        return Response(
            {"error": "No user profile."}, status=status.HTTP_400_BAD_REQUEST
        )
    elif user.profile.roles.count() == 0:
        return Response({"error": "No user role."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_profile_role = user.profile.roles.get(name=user_role).name
    except Exception as e:
        return Response(
            {"error": "User role not found."}, status=status.HTTP_400_BAD_REQUEST
        )

    roles = get_active_roles(user)
    response_data, response_status = get_role_response(user, user_profile_role, roles)
    sub_role = ""
    if user_role:
        permission = user.profile.permissions.filter(role__name=user_role).first()
        sub_role = permission.sub_role.name if permission else ""
        response_data["sub_role"] = sub_role

    if response_data is None:
        return Response(
            {"error": f"Role change to {user_profile_role} not allowed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(response_data, status=response_status)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "superadmin")])
def get_users(request):
    user_profiles = Profile.objects.all()
    res = []
    for profile in user_profiles:
        active_roles = []
        inactive_roles = []
        # existing_roles = [item.name for item in profile.roles.all()]
        for role in profile.roles.all():
            user = get_user_for_active_inactive(role.name, profile.user.username)
            if user:
                if user.active_inactive:
                    active_roles.append(role.name)
                else:
                    inactive_roles.append(role.name)
        email = profile.user.email
        res.append(
            {
                "id": profile.id,
                "email": email,
                "roles": active_roles,
                "inactive_roles": inactive_roles,
            }
        )
    return Response(res)


@api_view(["GET"])
@permission_classes([AllowAny])
def microsoft_auth(request, user_mail_address):
    oauth2_endpoint = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"

    auth_params = {
        "client_id": env("MICROSOFT_CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": env("MICROSOFT_REDIRECT_URI"),
        "response_mode": "query",
        "scope": "openid offline_access User.Read Calendars.ReadWrite profile email  OnlineMeetings.Read OnlineMeetings.ReadWrite",
        "state": "shashankmeeraq",
        "login_hint": user_mail_address,
    }

    auth_url = f"{oauth2_endpoint}?{urlencode(auth_params)}"

    return HttpResponseRedirect(auth_url)


@api_view(["POST", "GET"])
@permission_classes([AllowAny])
def microsoft_callback(request):
    try:
        authorization_code = request.GET.get("code")

        token_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            "client_id": env("MICROSOFT_CLIENT_ID"),
            "scope": "User.Read",
            "code": authorization_code,
            "redirect_uri": env("MICROSOFT_REDIRECT_URI"),
            "grant_type": "authorization_code",
            "client_secret": env("MICROSOFT_CLIENT_SECRET"),
        }

        response = requests.post(token_url, data=token_data)

        token_json = response.json()

        if "access_token" in token_json and "refresh_token" in token_json:
            access_token = token_json["access_token"]
            refresh_token = token_json["refresh_token"]
            expires_in = token_json["expires_in"]
            auth_code = authorization_code
            user_email_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {access_token}"}

            user_email_response = requests.get(user_email_url, headers=headers)

            if user_email_response.status_code == 200:
                user_info_data = user_email_response.json()
                user_email = user_info_data.get("mail", "")
                user = User.objects.get(username=user_email)
                user_profile = Profile.objects.get(user=user)
                user_token, created = UserToken.objects.get_or_create(
                    user_profile=user_profile
                )
                user_token.access_token = access_token
                user_token.refresh_token = refresh_token
                user_token.access_token_expiry = expires_in
                user_token.authorization_code = auth_code
                user_token.account_type = "microsoft"
                user_token.save()
            return HttpResponseRedirect(env("APP_URL"))
        else:
            error_json = response.json()
            return JsonResponse(error_json, status=response.status_code)

    except Exception as e:
        # Handle exceptions here, you can log the exception for debugging
        print(f"An exception occurred: {str(e)}")
        # You might want to return an error response or redirect to an error page.
        return JsonResponse({"error": "An error occurred"}, status=500)


class UserTokenAvaliableCheck(APIView):
    permission_classes = [
        IsAuthenticated,
        IsInRoles("pmo", "coach", "facilitator", "hr", "learner"),
    ]

    def get(self, request, user_mail, format=None):
        user_token_present = False
        try:
            user_token = UserToken.objects.get(user_profile__user__username=user_mail)
            if user_token:
                user_token_present = True
        except Exception as e:
            pass
        return Response({"user_token_present": user_token_present})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("superadmin", "pmo")])
def get_api_logs(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if not start_date or not end_date:
        logs = APILog.objects.all()
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            logs = APILog.objects.filter(created_at__date__range=(start_date, end_date))
        except ValueError:
            return JsonResponse(
                {"error": "Invalid date format. Please use YYYY-MM-DD."}, status=400
            )

    result_dict = {}

    for log in logs:
        matching_key = next((key for key in log.path.split("/") if key), None)
        if matching_key:
            activity = matching_key
            user_type = (
                log.user.profile.roles.all().first().name.lower()
                if log.user
                and log.user.profile
                and log.user.profile.roles.all().first()
                else None
            )

            key = (user_type, activity)
            result_dict[key] = result_dict.get(key, 0) + 1

    # Create a nested dictionary with user types and activities as keys and counts as values
    user_activity_count_dict = {
        user_type: {
            activity: sum(
                value
                for key, value in result_dict.items()
                if key[0] == user_type and key[1] == activity
            )
        }
        for user_type in set(key[0] for key in result_dict)
    }
    output_list = []
    for user_type, activities in user_activity_count_dict.items():
        for activity, count in activities.items():
            output_list.append(
                {"user_type": user_type, "activity": activity, "count": count}
            )
    return Response(output_list)


class UpdateUserRoles(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            with transaction.atomic():
                user_id = request.data.get("user_id")
                removed_roles = request.data.get("removed_roles")
                added_roles = request.data.get("added_roles")

                profile = Profile.objects.get(id=user_id)

                for role in removed_roles:
                    user = get_user_for_active_inactive(role, profile.user.username)

                    user.active_inactive = False
                    user.save()

                for role in added_roles:
                    user = get_user_for_active_inactive(role, profile.user.username)

                    user.active_inactive = True
                    user.save()

                return Response({"message": "Roles updated successfully!"})
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to update."},
                status=500,
            )


class UniqueValuesView(APIView):
    def get(self, request, *args, **kwargs):
        # Get model names, app names, and fields from query parameters
        model_names = request.GET.getlist("model")
        app_names = request.GET.getlist("app_name")
        fields = request.GET.getlist("fields")

        if not model_names or not fields or len(model_names) != len(app_names):
            return JsonResponse(
                {
                    "error": "Model names, app names, and fields must be specified and match in length."
                },
                status=400,
            )

        unique_values = {}

        for model_name, app_name in zip(model_names, app_names):
            try:
                # Dynamically get the model
                model = apps.get_model(app_name, model_name)
            except LookupError:
                return JsonResponse(
                    {
                        "error": f"Model '{model_name}' in app '{app_name}' does not exist."
                    },
                    status=400,
                )

            for column in fields:
                # Handle nested

                parts = column.split("__")
                if len(parts) == 1:
                    # Simple field
                    column = parts[0]
                    try:
                        field = model._meta.get_field(column)
                        field_type = field.get_internal_type()

                        if field_type in [
                            "JSONField",
                            "CharField",
                            "BooleanField",
                            "DateField",
                            "TextField",
                        ]:
                            # Retrieve distinct values
                            values = model.objects.values_list(
                                column, flat=True
                            ).distinct()

                            if field_type == "JSONField":
                                # Flatten the JSONField values and exclude None, empty strings, and "undefined"
                                flattened_values = self.flatten_json_values(values)
                                if column not in unique_values:
                                    unique_values[column] = set()
                                unique_values[column].update(
                                    v
                                    for v in flattened_values
                                    if v not in [None, "", " ", "undefined"]
                                )
                            else:
                                # Exclude None, empty strings, and "undefined"
                                if column not in unique_values:
                                    unique_values[column] = set()
                                unique_values[column].update(
                                    v
                                    for v in values
                                    if v not in [None, "", " ", "undefined"]
                                )
                        else:
                            return JsonResponse(
                                {
                                    "error": f"Field '{column}' is not supported for unique value retrieval."
                                },
                                status=400,
                            )
                    except FieldDoesNotExist:
                        return JsonResponse(
                            {
                                "error": f"Field '{column}' does not exist in model '{model_name}'."
                            },
                            status=400,
                        )
                else:
                    # Nested field
                    base_field = parts[0]
                    nested_field = "__".join(parts[1:])
                    print("nested", nested_field)
                    try:
                        base_field_obj = model._meta.get_field(base_field)
                        if isinstance(base_field_obj, (ForeignKey, ManyToManyField)):
                            # Handling foreign keys or many-to-many relationships
                            related_model = base_field_obj.related_model
                            related_values = related_model.objects.values_list(
                                nested_field, flat=True
                            ).distinct()

                            if column not in unique_values:
                                unique_values[column] = set()

                            unique_values[column].update(
                                v
                                for v in related_values
                                if v not in [None, "", " ", "undefined"]
                            )
                        else:
                            return JsonResponse(
                                {
                                    "error": f"Field '{base_field}' is not a ForeignKey or ManyToManyField in model '{model_name}'."
                                },
                                status=400,
                            )
                    except (FieldDoesNotExist, ValueError) as e:
                        return JsonResponse(
                            {"error": f"Error with nested field '{column}': {str(e)}"},
                            status=400,
                        )

        # Convert sets to lists for JSON serialization
        for key in unique_values:
            unique_values[key] = list(unique_values[key])

        return JsonResponse(unique_values, safe=False)

    def flatten_json_values(self, json_values):
        """Recursively flatten JSON values into a single list."""
        flattened = []
        for value in json_values:
            if isinstance(value, list):
                flattened.extend(self.flatten_json_values(value))
            elif isinstance(value, dict):
                flattened.extend(self.flatten_json_values(value.values()))
            else:
                if value not in [
                    None,
                    "",
                    "undefined",
                    " ",
                ]:  # Exclude None, empty strings, and "undefined"
                    flattened.append(value)
        return flattened


class GetModelOptionsView(APIView):
    """
    A generic API view to fetch id and name fields from any model dynamically,
    with support for additional fields, proper handling of relationship fields,
    and concatenating multiple field values.
    """

    def get_field_value(self, instance, field_name, model_field):
        """Helper method to get the appropriate value based on field type"""
        value = getattr(instance, field_name)

        # Handle Many-to-Many fields
        if isinstance(model_field, models.ManyToManyField):
            return [item.id for item in value.all()]

        # Handle Foreign Key fields
        if isinstance(model_field, models.ForeignKey):
            return value.id if value else None

        return value

    def get_label_value(self, instance, field_names):
        """Helper method to concatenate multiple field values for the label"""
        if not field_names or not isinstance(field_names, list):
            return getattr(instance, "name", "")

        field_values = []
        for field_name in field_names:
            value = getattr(instance, field_name, "")
            if value:
                field_values.append(str(value))

        return " ".join(field_values) if field_values else ""

    def get(self, request, *args, **kwargs):
        app_label = request.query_params.get("app")
        model_name = request.query_params.get("model")
        fields = request.query_params.get("field_name")
        same = request.query_params.get("same")
        current_id = request.query_params.get("current_id")
        additional_fields = (
            request.query_params.get("additional_fields", "").split(",")
            if request.query_params.get("additional_fields")
            else []
        )

        # Remove empty strings from additional_fields
        additional_fields = [f for f in additional_fields if f]

        # Parse field_name parameter - handle multiple fields
        field_names = fields.split(",") if fields else ["name"]
        field_names = [f.strip() for f in field_names if f.strip()]

        # For single field compatibility
        name_of_field = field_names[0] if field_names else "name"

        # Extract filters
        filters = {}
        exclude_conditions = []
        excluded_params = {
            "app",
            "model",
            "field_name",
            "same",
            "current_id",
            "additional_fields",
        }

        for key, value in request.query_params.items():
            if key not in excluded_params:
                if "isnull" in key and value in ["True", "False"]:
                    filters[key] = value == "True"
                elif key.endswith("__ne"):
                    exclude_conditions.append({key.replace("__ne", ""): value})
                else:
                    filters[key] = value

        if not app_label or not model_name:
            return Response(
                {"error": "Both 'app' and 'model' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            Model = apps.get_model(app_label, model_name)
        except LookupError:
            return Response(
                {"error": f"Model '{model_name}' in app '{app_label}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            queryset = Model.objects.filter(**filters)

            # Apply exclude conditions
            for exclude_filter in exclude_conditions:
                queryset = queryset.exclude(**exclude_filter)

            # Handle current_id case
            if current_id:
                try:
                    current_item = Model.objects.filter(id=current_id).first()
                    if current_item:
                        # Get model fields
                        model_fields = {f.name: f for f in Model._meta.get_fields()}

                        # Build current item result
                        current_result = {
                            "value": (
                                getattr(current_item, name_of_field)
                                if same
                                else current_item.id
                            ),
                            "label": self.get_label_value(current_item, field_names),
                        }

                        # Add additional fields
                        for field in additional_fields:
                            if field in model_fields:
                                current_result[field] = self.get_field_value(
                                    current_item, field, model_fields[field]
                                )

                        # Get filtered queryset excluding current item
                        filtered_queryset = queryset.exclude(id=current_id).distinct()

                        # Build results for other items
                        other_results = []
                        for item in filtered_queryset:
                            result = {
                                "value": (
                                    getattr(item, name_of_field) if same else item.id
                                ),
                                "label": self.get_label_value(item, field_names),
                            }

                            for field in additional_fields:
                                if field in model_fields:
                                    result[field] = self.get_field_value(
                                        item, field, model_fields[field]
                                    )
                            other_results.append(result)

                        return Response(
                            {"results": [current_result] + other_results},
                            status=status.HTTP_200_OK,
                        )

                except Exception as e:
                    pass

            # Normal filtering without current_id
            results = []
            model_fields = {f.name: f for f in Model._meta.get_fields()}

            for item in queryset.distinct():
                result = {
                    "value": getattr(item, name_of_field) if same else item.id,
                    "label": self.get_label_value(item, field_names),
                }

                for field in additional_fields:
                    if field in model_fields:
                        result[field] = self.get_field_value(
                            item, field, model_fields[field]
                        )

                results.append(result)

            return Response({"results": results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error applying filters: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TicketListCreateView(generics.ListCreateAPIView):
    queryset = Tickets.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    pagination_class = CustomPageNumberPagination
    filterset_class = TicketFilter

    search_fields = ["name", "user__username", "user_type", "status"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TicketSerializer
        return TicketSerializerDepthOne

    def perform_create(self, serializer):
        ticket = serializer.save()
        requested_user_name = ticket.user.username if ticket.user else "Unknown"
        description = ticket.description
        ticket_number = ticket.ticket_number
        created_date = ticket.created_at.strftime("%d-%m-%Y")
        ticket_raise_to = ticket.raise_to
        email_subject = f"New Ticket Raised: {ticket.name}"
        heading = "Tech Team" if ticket_raise_to == "tech_team" else "Ekansh Tech Team"
        username = get_user_name(ticket.user)
        content = {
            "heading": heading,
            "ticket": ticket,
            "requested_user_name": requested_user_name,
            "description": description,
            "date": created_date,
            "username": username,
            "ticket_number": ticket_number,
        }
        file_name = "ticket_raising_email.html"
        if ticket_raise_to == "tech_team":
            bcc_emails = json.loads(env("BCC_EMAILS_TICKET_FOR_TECH"))
            bcc_emails.append(requested_user_name)
            user_email = json.loads(env("TECH_SUPPORT"))
        elif ticket_raise_to == "ekansh_tech":
            bcc_emails = json.loads(env("BCC_EMAILS_FOR_EKANSH_TECH"))
            bcc_emails.append(requested_user_name)
            user_email = json.loads(env("EKANSH_TECH_SUPPORT"))

        else:
            return
        send_mail_templates(file_name, user_email, email_subject, content, bcc_emails)


class TicketNumberGenerateView(APIView):
    """
    API view to generate and return the next ticket number.
    """

    def get(self, request, *args, **kwargs):
        # Get the latest ticket based on created_at and check for ticket_number
        latest_ticket = Tickets.objects.order_by("-created_at").first()
        if latest_ticket and latest_ticket.ticket_number:
            # Extract the number part and increment it by 1
            last_ticket_number = int(
                latest_ticket.ticket_number[1:]
            )  # Assuming format 'T100', skip 'T'
            new_ticket_number = f"T{last_ticket_number + 1}"
        else:
            # Start from 'T100' if no ticket or no ticket number found
            new_ticket_number = "T100"

        # Return the new ticket number as a JSON response
        return Response({"ticket_number": new_ticket_number}, status=status.HTTP_200_OK)


class AllTicketListView(generics.ListCreateAPIView):
    queryset = Tickets.objects.all()
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    pagination_class = None
    filterset_class = TicketFilter


class TicketStatisticsAPIView(APIView):
    """
    API endpoint to get ticket statistics for the SLA dashboard
    """

    def get(self, request, *args, **kwargs):
        # Get date range parameters
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        # Parse dates
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
        except (ValueError, TypeError):
            # Default to last 7 days if dates not provided or invalid
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=7)

        # Filter tickets by date range
        tickets = Tickets.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        )

        # Total tickets in the period
        total_tickets = tickets.count()

        # Completed tickets
        completed_tickets = tickets.filter(status="closed").count()

        # Helper function to categorize tickets
        def categorize_tickets(resolved_tickets):
            """
            Categorize tickets into before time, on time, and breached
            """
            before_time_count = 0
            on_time_count = 0
            breached_count = 0

            for ticket in resolved_tickets:
                if not ticket.sla_due_date or not ticket.resolution_date:
                    continue

                # Calculate time difference
                time_to_resolve = ticket.resolution_date - ticket.created_at
                sla_time_allowed = ticket.sla_due_date - ticket.created_at

                # Convert to seconds for comparison
                resolve_seconds = time_to_resolve.total_seconds()
                allowed_seconds = sla_time_allowed.total_seconds()

                if (
                    ticket.is_sla_breached
                    or ticket.resolution_date > ticket.sla_due_date
                ):
                    breached_count += 1
                elif resolve_seconds <= (allowed_seconds * 0.75):
                    before_time_count += 1
                else:
                    on_time_count += 1

            return before_time_count, on_time_count, breached_count

        # Get resolved tickets (all data needed for categorization)
        resolved_tickets = tickets.filter(
            status="closed", resolution_date__isnull=False
        )

        # Open tickets with breached SLA
        open_breached = tickets.filter(
            ~Q(status__in=["closed", "cancelled"]), is_sla_breached=True
        ).count()

        # Categorize tickets
        before_time_count, on_time_count, breached_count = categorize_tickets(
            resolved_tickets
        )

        # Total breached (resolved breached + open breached)
        total_breached = breached_count + open_breached

        # Calculate completion and breach rates
        completion_rate = (
            round((completed_tickets / total_tickets * 100), 1)
            if total_tickets > 0
            else 0
        )
        sla_breach_rate = (
            round((total_breached / total_tickets * 100), 1) if total_tickets > 0 else 0
        )

        # Calculate average resolution time in hours
        avg_resolution_time = 0
        if resolved_tickets.exists():
            # Calculate resolution time as duration
            resolution_time = resolved_tickets.annotate(
                resolution_duration=ExpressionWrapper(
                    F("resolution_date") - F("created_at"), output_field=DurationField()
                )
            ).aggregate(avg=Avg("resolution_duration"))

            # Convert average duration to hours
            if resolution_time["avg"]:
                avg_resolution_time = resolution_time["avg"].total_seconds() / 3600

        # Get priority breakdown
        priority_counts = {
            "critical": tickets.filter(priority="critical").count(),
            "high": tickets.filter(priority="high").count(),
            "medium": tickets.filter(priority="medium").count(),
            "low": tickets.filter(priority="low").count(),
        }

        # Prepare response data
        response_data = {
            "total_tickets": total_tickets,
            "completed_tickets": completed_tickets,
            "breached_tickets": total_breached,
            "on_time_tickets": on_time_count,
            "before_time_tickets": before_time_count,
            "completion_rate": completion_rate,
            "sla_breach_rate": sla_breach_rate,
            "avg_resolution_time": round(avg_resolution_time, 1),
            "priority_counts": priority_counts,
        }

        return Response(response_data, status=status.HTTP_200_OK)


# Retrieve, update, and delete view
class TicketRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tickets.objects.all()
    serializer_class = TicketSerializer

    def perform_update(self, serializer):
        instance = self.get_object()
        brand = get_brand(self.request)
        old_status = instance.status
        ticket = serializer.save()
        # If status changed to closed, send closure notification
        if old_status != "closed" and ticket.status == "closed":
            requested_user_name = ticket.user.username if ticket.user else "Unknown"
            username = get_user_name(ticket.user)
            description = ticket.description
            created_date = ticket.created_at.strftime("%d-%m-%Y")
            ticket_raise_to = ticket.raise_to
            ticket_number = ticket.ticket_number
            if brand == "ctt":
                feedback_url = (
                    f"{env('LXP_APP_URL')}/ticket-feedback/{ticket.unique_id}"
                )
            else:
                feedback_url = (
                    f"{env('CAAS_APP_URL')}/ticket-feedback/{ticket.unique_id}"
                )
            email_subject = "Your Ticket Has Been Resolved - Share Your Feedback!"
            heading = (
                "Tech Team" if ticket_raise_to == "tech_team" else "Ekansh Tech Team"
            )
            content = {
                "heading": heading,
                "ticket": ticket,
                "ticket_number": ticket_number,
                "requested_user_name": requested_user_name,
                "description": description,
                "date": created_date,
                "username": username,
                "feedback_url": feedback_url,
            }
            bcc_emails = (
                json.loads(env("TICKET_CLOSURE_BCC_MAILS_FOR_TECH"))
                if ticket_raise_to == "tech_team"
                else json.loads(env("TICKET_CLOSURE_BCC_MAILS_FOR_EKANSH_TECH"))
            )
            file_name = "ticket_closing_mail_to_rajat.html"
            send_mail_templates(
                file_name, [requested_user_name], email_subject, content, bcc_emails
            )


class TicketFeedbackAPIView(APIView):
    """
    API endpoint for fetching ticket details and submitting feedback using the unique ID.
    """

    def get(self, request, unique_id):
        """
        Fetch ticket details by unique_id for the feedback form
        """
        try:
            # Use filter().first() instead of get() to avoid MultipleObjectsReturned error
            ticket = Tickets.objects.filter(unique_id=unique_id).first()

            if not ticket:
                return Response(
                    {"error": "Invalid ticket ID or link expired"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # For security and performance, only return necessary information
            ticket_data = {
                "id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "name": ticket.name,
                "status": ticket.status,
                "user": {
                    "username": ticket.user.username if ticket.user else "Unknown"
                },
            }

            return Response(ticket_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request, unique_id):
        try:
            ticket = Tickets.objects.filter(unique_id=unique_id).first()

            if not ticket:
                return Response(
                    {"error": "Invalid ticket ID or link expired"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if ticket.feedback:
                return Response(
                    {"error": "Feedback already submitted for this ticket"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            satisfaction_rating = request.data.get("satisfactionRating")
            response_timeliness = request.data.get("responseTimeliness")
            resolution_helpfulness = request.data.get("resolutionHelpfulness")
            experience_smoothness = request.data.get("experienceSmoothness")
            if not all(
                [
                    satisfaction_rating,
                    response_timeliness,
                    resolution_helpfulness,
                    experience_smoothness,
                ]
            ):
                return Response(
                    {"error": "All feedback ratings are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                feedback = TicketFeedback.objects.create(
                    satisfaction_rating=satisfaction_rating,
                    response_timeliness=response_timeliness,
                    resolution_helpfulness=resolution_helpfulness,
                    experience_smoothness=experience_smoothness,
                )
                ticket.feedback = feedback
                ticket.save()
            return Response(
                {
                    "message": "Feedback submitted successfully",
                    "ticket_number": ticket.ticket_number,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AddCommentView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# List and Create
class UserRolePermissionsListCreateView(generics.ListCreateAPIView):
    queryset = UserRolePermissions.objects.all()
    serializer_class = UserRolePermissionsSerializer
    permission_classes = [IsAuthenticated]


# Retrieve, Update, and Delete
class UserRolePermissionsRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = UserRolePermissions.objects.all()
    serializer_class = UserRolePermissionsSerializer
    permission_classes = [IsAuthenticated]


class SubRoleListCreateView(generics.ListCreateAPIView):
    queryset = SubRole.objects.all()
    serializer_class = SubRoleSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        role_name = request.data.get("role_name")
        sub_role_name = request.data.get("sub_role_name")
        permissions = request.data.get("permissions")

        try:
            # Check if role exists, return 404 if not

            role = get_object_or_404(Role, name=role_name)

            # Check if sub-role with this name already exists
            if SubRole.objects.filter(name=sub_role_name).exists():
                return Response(
                    {"error": "SubRole with this name already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create the sub-role and assign it to the role
            sub_role = SubRole.objects.create(name=sub_role_name)
            role.sub_roles.add(sub_role)  # Assigning the sub-role to the role

            user_permission, created = UserRolePermissions.objects.get_or_create(
                role=role, sub_role=sub_role
            )
            # Add permissions as a list of dictionaries (JSONField expects this)
            user_permission.permission = permissions[role.name]
            # Save the changes to the database
            user_permission.save()

            return Response(
                {"message": "SubRole created and assigned to Role successfully."},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            print("Error:", str(e))  # Print the error for debugging
            return Response(
                {"error": "An error occurred while creating the SubRole."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubRoleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubRole.objects.all()
    serializer_class = SubRoleSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access


# List and Create view
class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializerDepthOne
    permission_classes = [IsAuthenticated]
    pagination_class = None


# Retrieve, Update, and Delete view
class RoleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class UserRolePermissionsRetrieveView(generics.RetrieveAPIView):
    serializer_class = UserRolePermissionsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        role_id = self.kwargs.get("role")
        sub_role_id = self.kwargs.get("sub_role")

        return get_object_or_404(
            UserRolePermissions, role_id=role_id, sub_role_id=sub_role_id
        )


class RoleListCreateViewPagination(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializerDepthOne
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "sub_roles__name"]


class GetSubRolesForRole(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        try:
            # Get the role_name from URL parameters
            role_name = kwargs.get("role_name")

            # Get the role object or return 404 if not found
            role = get_object_or_404(Role, name=role_name)

            # Get all sub-roles associated with this role
            sub_roles = role.sub_roles.all()

            # Serialize the sub-roles
            serializer = SubRoleSerializer(sub_roles, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetRoleForName(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        try:
            # Get the role_name from URL parameters
            role_name = kwargs.get("role_name")

            # Get the role object or return 404 if not found
            role = get_object_or_404(Role, name=role_name)

            # Get all sub-roles associated with this role

            serializer = RoleSerializerDepthOne(role)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


MODELS_MAPPING = {
    "pmo": Pmo,
    "sales": Sales,
    "leader": Leader,
    "employee": Employee,
}

SERIALIZER_MAPPING = {
    "pmo": PmoSerializer,
    "sales": SalesSerializer,
    "leader": LeaderSerializer,
    "employee": EmployeeSerializer,
}


class GetTeamOfManager(generics.ListAPIView):
    """
    API View to retrieve team members excluding the manager with custom pagination.

    URL Parameters:
    - user_id: ID of the manager
    - user_type: Type of user (pmo, sales, curriculum, leader)
    """

    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user_type = self.request.query_params.get("user_type")
        user_id = self.request.query_params.get("user_id")
        search = self.request.query_params.get("search")

        if user_type not in MODELS_MAPPING:
            return MODELS_MAPPING[
                "employee"
            ].objects.none()  # Return an empty queryset with a valid model

        subordinates = (
            UserHierarchy.objects.filter(supervisor__user__user__id=user_id)
            .values_list("subordinate__user__user__id", flat=True)
            .distinct()
        )
        print(subordinates)
        user_model = MODELS_MAPPING[user_type]
        queryset = user_model.objects.filter(
            user__user__id__in=subordinates,
        )

        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("id")

    def get_serializer_class(self):
        user_type = self.request.query_params.get("user_type")
        return SERIALIZER_MAPPING.get(user_type, SERIALIZER_MAPPING["pmo"])

    def list(self, request, *args, **kwargs):
        user_type = request.query_params.get("user_type")
        user_id = request.query_params.get("user_id")

        # Validate user_type
        if user_type not in MODELS_MAPPING:
            return Response(
                {
                    "error": f"Invalid user_type. Must be one of: {', '.join(MODELS_MAPPING.keys())}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Verify if user exists
            # user_model = MODELS_MAPPING[user_type]
            # if not user_model.objects.filter(id=user_id).exists():
            #     return Response(
            #         {"error": f"User with id {user_id} does not exist"},
            #         status=status.HTTP_404_NOT_FOUND
            #     )

            # Get queryset and paginate
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({"count": queryset.count(), "results": serializer.data})

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetPermissionForUserRole(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        try:
            # Get the role_name from URL parameters
            user_type = kwargs.get("user_type")
            user_id = kwargs.get("user_id")

            user_model = MODELS_MAPPING[user_type]

            # Get the role object or return 404 if not found
            user_data = user_model.objects.get(id=user_id)

            permission = user_data.user.permissions.filter(role__name=user_type).first()
            # Get all sub-roles associated with this role

            # Serialize the sub-roles
            serializer = UserRolePermissionsSerializer(permission)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateSubRoleOfUser(APIView):
    def put(self, request, *args, **kwargs):
        try:
            # Get data from request
            user_type = request.data.get("role")
            user_id = request.data.get("user_id")
            new_sub_role = request.data.get("sub_role")

            if not all([user_type, user_id, new_sub_role]):
                return Response(
                    {"error": "Missing required fields"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate user type
            if user_type not in MODELS_MAPPING:
                return Response(
                    {"error": f"Invalid user type: {user_type}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get user instance
            user_model = MODELS_MAPPING[user_type]
            user_instance = get_object_or_404(user_model, id=user_id)
            profile = user_instance.user

            # Get new role permission
            new_role_permission = UserRolePermissions.objects.get(
                role__name=user_type, sub_role__name=new_sub_role
            )

            # Remove old permission for this role
            old_permission = profile.permissions.get(role__name=user_type)
            profile.permissions.remove(old_permission)

            # Add new permission
            profile.permissions.add(new_role_permission)

            # Update sub_role field if the model has it
            if hasattr(user_instance, "sub_role"):
                user_instance.sub_role = new_sub_role
                user_instance.save()

            return Response(
                {
                    "message": "Sub role and permissions updated successfully",
                    "user_id": user_id,
                    "new_sub_role": new_sub_role,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": f"Failed to update sub role: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StandardizedFieldAPI(APIView):
    permission_classes = [
        IsAuthenticated,
        IsInRoles(
            "coach", "facilitator", "pmo", "hr", "learner", "leader", "curriculum"
        ),
    ]

    def get(self, request):
        standardized_fields = StandardizedField.objects.all()

        standardized_fields_serializer = StandardizedFieldSerializer(
            standardized_fields, many=True
        )

        field_data = {
            field_data["field"]: field_data["values"]
            for field_data in standardized_fields_serializer.data
        }

        return Response(field_data)


class StandardizedFieldRequestAPI(APIView):
    permission_classes = [
        IsAuthenticated,
        IsInRoles("coach", "facilitator", "pmo", "curriculum"),
    ]

    def get(self, request):
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        today_requests = StandardizedFieldRequest.objects.filter(
            requested_at__gte=today_start, status="pending"
        ).order_by("-requested_at")

        other_requests = StandardizedFieldRequest.objects.filter(
            Q(status="pending") & Q(requested_at__lt=today_start)
        ).order_by("-requested_at")

        today_requests_serializer = StandardizedFieldRequestDepthOneSerializer(
            today_requests, many=True
        )
        other_requests_serializer = StandardizedFieldRequestDepthOneSerializer(
            other_requests, many=True
        )

        return Response(
            {
                "today_requests": today_requests_serializer.data,
                "other_requests": other_requests_serializer.data,
            }
        )


class StandardFieldAddValue(APIView):
    permission_classes = [
        IsAuthenticated,
        IsInRoles("pmo", "finance", "leader", "curriculum"),
    ]

    def post(self, request):
        try:
            with transaction.atomic():
                # Extracting data from request body
                field_name = request.data.get("field_name")
                option_value = request.data.get("optionValue").strip()

                # Validate the input data
                if not field_name or not option_value:
                    return Response(
                        {"error": "Field name and option value are required."},
                        status=400,
                    )

                # Get or create the StandardizedField instance for the given field_name
                standardized_field, created = StandardizedField.objects.get_or_create(
                    field=field_name
                )

                # Check if the option_value already exists in the values list of the standardized_field
                if option_value not in standardized_field.values:
                    # Add the option_value to the values list and save the instance
                    standardized_field.values.append(option_value)
                    standardized_field.save()

                    # Check if the field_name is 'project_type'
                    if field_name == "project_type":
                        # Check if there are Benchmark instances
                        if not Benchmark.objects.exists():
                            # Create a Benchmark instance with the project_type key
                            Benchmark.objects.create(project_type={option_value: ""})
                            return Response(
                                {
                                    "message": f"Benchmark created with {option_value} in project_type."
                                },
                                status=200,
                            )

                        # Filter Benchmark instances by the current year
                        current_year = datetime.now().year
                        benchmarks = Benchmark.objects.all()

                        if benchmarks.exists():
                            # Update the project_type field of existing Benchmark instances
                            for benchmark in benchmarks:
                                if not benchmark.project_type:
                                    benchmark.project_type = (
                                        {}
                                    )  # Ensure project_type is a dictionary
                                benchmark.project_type[option_value] = ""
                                benchmark.save()

                            return Response(
                                {
                                    "message": f"Value Added to {FIELD_NAME_VALUES[field_name]} field for the current year."
                                },
                                status=200,
                            )
                        else:
                            # No Benchmark instances for the current year, create one and update project_type
                            Benchmark.objects.create(
                                year=current_year, project_type={option_value: ""}
                            )
                            return Response(
                                {
                                    "message": f"Benchmark created with {option_value} in project_type for the current year."
                                },
                                status=200,
                            )

                    # Return success response for other field names
                    return Response(
                        {
                            "message": f"Value Added to {FIELD_NAME_VALUES[field_name]} field."
                        },
                        status=200,
                    )

                else:
                    # Return error response if the option_value already exists
                    return Response({"error": "Value already present."}, status=400)

        except Exception as e:
            # Return error response if any exception occurs
            return Response(
                {"error": "Failed to add value."},
                status=500,
            )


class StandardFieldEditValue(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "curriculum")]

    def put(self, request):
        try:
            with transaction.atomic():
                # Extracting data from request body
                field_name = request.data.get("field_name")
                previous_value = request.data.get("previous_value")
                new_value = request.data.get("new_value").strip()

                # Retrieve the StandardizedField instance corresponding to the provided field_name
                standardized_field = StandardizedField.objects.filter(
                    field=field_name
                ).first()

                # Check if the field exists
                if standardized_field:
                    # Check if the previous_value exists in the values list of the standardized_field
                    if previous_value in standardized_field.values:
                        # Update the value if it exists
                        index = standardized_field.values.index(previous_value)
                        standardized_field.values[index] = new_value
                        standardized_field.save()

                        # If the field_name is 'project_type', update the corresponding key in the project_type field of Benchmark instances
                        if field_name == "project_type":
                            benchmarks = Benchmark.objects.all()
                            for benchmark in benchmarks:
                                if previous_value in benchmark.project_type:
                                    benchmark.project_type[new_value] = (
                                        benchmark.project_type.pop(previous_value)
                                    )
                                    benchmark.save()

                        # Return success response
                        return Response(
                            {
                                "message": f"Value Updated in {FIELD_NAME_VALUES[field_name]} field."
                            },
                            status=200,
                        )
                    else:
                        # Return error response if the previous_value does not exist
                        return Response(
                            {
                                "message": f"{previous_value} not found in {FIELD_NAME_VALUES[field_name]} field."
                            },
                            status=404,
                        )
                else:
                    # Return error response if the field does not exist
                    return Response(
                        {"message": f"{FIELD_NAME_VALUES[field_name]} not found."},
                        status=404,
                    )

        except Exception as e:
            # Log the exception
            print(str(e))
            # Return error response if any exception occurs
            return Response(
                {"error": "Failed to update."},
                status=500,
            )


class StandardizedFieldRequestAcceptReject(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "curriculum")]

    def put(self, request):
        status = request.data.get("status")
        request_ids = request.data.get("request_id")

        if not isinstance(request_ids, list):
            request_ids = [request_ids]

        try:
            with transaction.atomic():
                for request_id in request_ids:
                    request_instance = StandardizedFieldRequest.objects.get(
                        id=request_id
                    )
                    field_name = request_instance.standardized_field_name.field
                    value = request_instance.value

                    standardized_field, created = (
                        StandardizedField.objects.get_or_create(field=field_name)
                    )
                    if status == "accepted":
                        request_instance.status = status
                        request_instance.save()
                    else:
                        request_instance.status = status
                        request_instance.save()

                        if value in standardized_field.values:
                            standardized_field.values.remove(value)
                            standardized_field.save()

                        for model_name, fields in MODELS_TO_UPDATE.items():
                            model_class = globals()[model_name]
                            instances = model_class.objects.all()

                            for instance in instances:
                                for field in fields:
                                    field_value = getattr(instance, field, None)
                                    if field_value is not None:
                                        if (
                                            isinstance(field_value, list)
                                            and value in field_value
                                        ):
                                            field_value.remove(value)
                                            instance.save()
                        if request_instance.coach:
                            send_mail_templates(
                                "coach_templates/reject_feild_item_request.html",
                                [request_instance.coach.email],
                                "Meeraq | Field Rejected",
                                {
                                    "name": f"{request_instance.coach.first_name} {request_instance.coach.last_name}",
                                    "value": value,
                                    "feild": field_name.replace(" ", "_").title(),
                                },
                                [],
                            )
                return Response({"message": f"Requests {status}"}, status=200)
        except Exception as e:
            print(str(e))
            return Response({"error": "Failed to perform operation."}, status=500)


class StandardFieldDeleteValue(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "curriculum")]

    def delete(self, request):
        try:
            with transaction.atomic():
                # Extracting data from request body
                field_name = request.data.get("field_name")
                option_value = request.data.get("optionValue")

                # Retrieve the StandardizedField instance for the given field_name
                standardized_field = StandardizedField.objects.get(field=field_name)

                # Check if the field_name is 'project_type'
                if field_name == "project_type":
                    # Retrieve all Benchmark instances
                    benchmarks = Benchmark.objects.all()
                    for benchmark in benchmarks:
                        # Check if the option_value exists in the project_type field of the Benchmark instance
                        if option_value in benchmark.project_type:
                            # Remove the option_value from the project_type field and save the Benchmark instance
                            del benchmark.project_type[option_value]
                            benchmark.save()

                # Check if the option_value exists in the values list of the standardized_field
                if option_value in standardized_field.values:
                    # Remove the option_value from the values list and save the instance
                    standardized_field.values.remove(option_value)
                    standardized_field.save()
                else:
                    # Return error response if the option_value does not exist
                    return Response({"error": "Value not present."}, status=404)

                # Return success response
                return Response(
                    {
                        "message": f"Value deleted from {FIELD_NAME_VALUES[field_name]} field."
                    },
                    status=200,
                )

        except StandardizedField.DoesNotExist:
            # Return error response if the StandardizedField instance does not exist
            return Response({"error": "Field not found."}, status=404)

        except Exception as e:
            # Log the exception
            print(str(e))
            # Return error response if any other exception occurs
            return Response(
                {"error": "Failed to delete value."},
                status=500,
            )


@api_view(["POST"])
@permission_classes(
    [IsAuthenticated, IsInRoles("pmo", "coach", "facilitator", "learner")]
)
def standard_field_request(request, user_id):
    try:
        with transaction.atomic():
            value = request.data.get("value").strip()
            userType = request.data.get("userType")

            field_name = request.data.get(
                "field_name"
            )  # Adjust this based on your field name
            standardized_field, created = StandardizedField.objects.get_or_create(
                field=field_name
            )

            if value not in standardized_field.values:
                standardized_field.values.append(value)
                standardized_field.save()
            else:
                return Response({"error": "Value already present."}, status=404)

            return Response({"message": "Request sent."}, status=200)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to create request."}, status=500)


class ActiveDeligationOfUser(APIView):
    def get(self, request, user_id, user_type, status):
        try:

            deligation = UserDelegation.objects.get(
                delegated_to__user__user__id=user_id,
                role__name=user_type,
                status=status,
            )
            serializer = UserDelegationSerializer(deligation)
            return Response(serializer.data)
        except Exception as e:
            print(str(e))
            return Response({"error": str(e)}, status=500)


class ActiveDeligationOfUserDepth(APIView):
    def get(self, request, user_id, user_type, status):
        try:

            deligation = UserDelegation.objects.filter(
                delegated_to__user__user__id=user_id,
                role__name=user_type,
                status=status,
            )
            serializer = UserDelegationSerializerDepthOne(deligation, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(str(e))
            return Response({"error": str(e)}, status=500)


class DeligatedToRolePermission(APIView):
    def get(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id)

            data = {}  # Change list to dictionary
            for permission in employee.user.permissions.all():
                data[permission.role.name] = (
                    permission.permission
                )  # Ensure correct data structure

            return Response(
                {
                    "permission": data,
                    "roles": RoleSerializerDepthOne(
                        employee.user.roles.all(), many=True
                    ).data,
                }
            )

        except Exception as e:
            print(str(e))  # Consider using logging instead of print
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserHierarchyOfUserRetrieveAPIView(APIView):
    """API to get the complete hierarchy for a specific user"""

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):

        # Get supervisors (users who supervise the given user)
        supervisors = UserHierarchy.objects.filter(
            subordinate__user__user__id=user_id
        ).order_by("hierarchy_level")

        # Get subordinates (users who report to the given user)
        subordinates = UserHierarchy.objects.filter(
            supervisor__user__user__id=user_id
        ).order_by("hierarchy_level")

        # Serialize the data
        supervisor_data = UserHierarchySerializer(supervisors, many=True).data
        subordinate_data = UserHierarchySerializer(subordinates, many=True).data

        return Response(
            {
                "supervisors": supervisor_data,
                "subordinates": subordinate_data,
            }
        )


class GetEmployeeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()


class CreateEmployeeView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsInRoles("superadmin", "finance", "leader")]
    serializer_class = EmployeeSerializer

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                data = request.data
                employee_serializer = self.get_serializer(data=data)
                if employee_serializer.is_valid():
                    first_name = data.get("first_name")
                    last_name = data.get("last_name")
                    email = data.get("email", "").strip().lower()
                    phone_number = data.get("phone_number")
                    sales_id = data.get("sales_id")

                    if not (first_name and last_name and phone_number and email):
                        return Response(
                            {"error": "Name and phone are mandatory fields."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    user = User.objects.filter(email=email).first()
                    if not user:
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            password=User.objects.make_random_password(),
                        )
                        profile = Profile.objects.create(user=user)
                    else:
                        profile = Profile.objects.get(user=user)

                    employee_role, created = Role.objects.get_or_create(name="employee")
                    profile.roles.add(employee_role)
                    profile.save()

                    employee_serializer.save(user=profile)
                    return Response(
                        employee_serializer.data, status=status.HTTP_201_CREATED
                    )

                return Response(
                    employee_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GmSheetListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = GmSheet.objects.all().order_by("-created_at")
    serializer_class = GmSheetSalesOrderExistsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["project", "project_type"]


class GMSheetBySalesView(generics.ListAPIView):
    serializer_class = GmSheetSalesOrderExistsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        sales_person_id = self.kwargs.get("sales_person_id")
        gmsheet = GmSheet.objects.filter(sales__id=sales_person_id).order_by(
            "-created_at"
        )
        return gmsheet


class EmployeeUpdateView(generics.UpdateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        employee_id = request.data.get("id")
        if not employee_id:
            return Response(
                {"error": "Employee ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(employee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteEmployeeView(generics.DestroyAPIView):
    queryset = Employee.objects.all()
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        employee_id = request.data.get("id")
        if not employee_id:
            return Response(
                {"error": "Employee ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND
            )

        employee.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteGmSheetView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = GmSheet.objects.all()
    lookup_field = "id"

    def delete(self, request, *args, **kwargs):
        gmsheet_id = request.data.get("gmSheetId")
        try:
            gmsheet = self.get_queryset().get(id=gmsheet_id)
            gmsheet.delete()
            return Response(
                {"success": "GM Sheet deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except GmSheet.DoesNotExist:
            return Response(
                {"error": "GM Sheet does not exist."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to delete GM Sheet."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OfferingsByGMSheetView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OfferingSerializer

    def get_queryset(self):
        gmsheet_id = self.kwargs.get("gmsheet_id")
        offerings = Offering.objects.filter(gm_sheet=gmsheet_id)
        return offerings


class AllGmSheetView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GmSheetDetailedSerializer
    queryset = GmSheet.objects.all().order_by("-created_at")
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = GmSheetListFilter
    search_fields = [
        "deal_status",
        "project_type",
        "gmsheet_number",
        "client_name",
        "project_name",
        "product_type",
        "participant_level",
    ]

    def get_queryset(self):
        query_params = self.request.query_params
        leader = query_params.get("leader", None)
        sales_id = query_params.get("sales_id", None)
        product_type = query_params.get("product_type", None)
        caas_project_id = query_params.get("caas_project_id", None)
        schedular_project_id = query_params.get("schedular_project_id", None)
        start_date = query_params.get("start_date", None)
        end_date = query_params.get("end_date", None)
        user_type = self.request.query_params.get("user_type")
        user_id = self.request.query_params.get("user_id")
        user_filter = Q(added_by__id=user_id)
        if user_id == "all":
            user_filter = Q()
        elif user_id and user_type and self.request.user.id == int(user_id):
            role = Role.objects.get(name=user_type)
            filter_subordinates = get_subordinates_of_a_user_in_role(
                "GmSheet", self.request.user, role
            )
            if filter_subordinates:
                user_filter |= filter_subordinates
        queryset = GmSheet.objects.filter(user_filter)
        # queryset = GmSheet.objects.all()
        # Apply date range filter if provided
        if start_date and end_date:
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            if start_date and end_date:
                end_datetime = datetime.combine(end_date, time.max)
                start_datetime = make_aware(datetime.combine(start_date, time.min))
                end_datetime = make_aware(end_datetime)
                queryset = queryset.filter(
                    created_at__range=(start_datetime, end_datetime)
                )
        if leader:
            queryset = (
                queryset.filter(offering__isnull=False)
                .order_by("-created_at")
                .distinct()
            )

        if product_type:
            gmsheet_ids = SalesOrder.objects.filter(
                Q(caas_project__project_type=product_type)
                | Q(schedular_project__project_type=product_type)
            ).values_list("gm_sheet_id", flat=True)
            queryset = queryset.filter(id__in=gmsheet_ids).order_by("-created_at")
        if caas_project_id:
            gmsheet_ids = SalesOrder.objects.filter(
                caas_project__id=caas_project_id
            ).values_list("gm_sheet_id", flat=True)
            queryset = queryset.filter(id__in=gmsheet_ids).order_by("-created_at")
        if schedular_project_id:
            gmsheet_ids = SalesOrder.objects.filter(
                schedular_project__id=schedular_project_id
            ).values_list("gm_sheet_id", flat=True)
            queryset = queryset.filter(id__in=gmsheet_ids).order_by("-created_at")

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        query_params = self.request.query_params
        leader = query_params.get("leader", None)
        sales_id = query_params.get("sales_id", None)
        product_type = query_params.get("product_type", None)
        caas_project_id = query_params.get("caas_project_id", None)
        schedular_project_id = query_params.get("schedular_project_id", None)
        if leader:
            return GmSheetDetailedOfferingSerializer
        elif sales_id:
            return GmSheetSalesOrderExistsSerializer
        elif product_type or caas_project_id or schedular_project_id:
            return GmSheetDetailedSerializer
        return super().get_serializer_class()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_gmsheet(request):
    try:
        gmsheet = (
            GmSheet.objects.filter(offering__isnull=False)
            .order_by("-created_at")
            .distinct()
        )
        serializer = GmSheetDetailedSerializer(gmsheet, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get GM Sheet."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class LeaderCumulativeDataView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GmSheetDetailedSerializer
    queryset = (
        GmSheet.objects.all()
        .filter(offering__isnull=False, deal_status__in=["won", "lost"])
        .order_by("-created_at")
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = GmSheetListFilter
    search_fields = [
        "deal_status",
        "project_type",
        "gmsheet_number",
        "client_name",
        "project_name",
        "product_type",
        "participant_level",
    ]

    def fetch_exchange_rate(self, currency):
        print("fetch_exchange_rate")
        try:
            response = requests.get(
                f"https://api.exchangerate-api.com/v4/latest/{currency}"
            )
            response.raise_for_status()
            return response.json().get("rates")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching exchange rate: {str(e)}")
            return None

    def list(self, request, *args, **kwargs):
        cumulative_data = {
            "total_gross_margin": 0,
            "total_won": 0,
            "total_cost": 0,
            "total_revenue": 0,
            "total_profit": 0,
            "total_lost": 0,
        }
        queryset = self.get_queryset()
        gm_sheets = GmSheetListFilter(
            self.request.query_params, queryset=queryset
        ).qs  # Filtering relevant data
        serializer = GmSheetDetailedOfferingSerializer(gm_sheets, many=True)
        filterAppliedData = serializer.data

        # Fetch exchange rates
        exchange_rates = self.fetch_exchange_rate("INR")
        if exchange_rates:
            for item in filterAppliedData:
                won_offering = item.get("offering_data")
                if won_offering:
                    # Gross margin
                    gross_margin = won_offering.get("gross_margin")
                    if gross_margin:
                        cumulative_data["total_gross_margin"] += float(gross_margin)

                    cumulative_data["total_won"] += 1

                    currency = item.get("currency")
                    if currency in exchange_rates:
                        # Total revenue
                        revenue_structure = won_offering.get("revenue_structure")
                        if revenue_structure:
                            cumulative_data["total_revenue"] += (
                                self.total_revenue(revenue_structure)
                                / exchange_rates[currency]
                            )

                        # Total cost
                        cost_structure = won_offering.get("cost_structure")
                        if cost_structure:
                            cumulative_data["total_cost"] += (
                                self.total_cost(cost_structure)
                                / exchange_rates[currency]
                            )

                        # Total profit
                        total_profit = won_offering.get("total_profit")
                        if total_profit:
                            cumulative_data["total_profit"] += (
                                float(total_profit) / exchange_rates[currency]
                            )
                    else:
                        print(f"Currency {currency} not found in exchange rates.")

                # Total lost
                if item.get("deal_status") == "lost":
                    cumulative_data["total_lost"] += 1

            # Round all floating point values to 2 decimal places
            cumulative_data["total_gross_margin"] = round(
                cumulative_data["total_gross_margin"], 2
            )
            cumulative_data["total_cost"] = round(cumulative_data["total_cost"], 2)
            cumulative_data["total_revenue"] = round(
                cumulative_data["total_revenue"], 2
            )
            cumulative_data["total_profit"] = round(cumulative_data["total_profit"], 2)
            return Response({"results": cumulative_data}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to fetch exchange rates"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def total_revenue(self, items):
        return sum(
            item.get("hours", 0) * item.get("units", 0) * item.get("fees", 0)
            for item in items
        )

    def total_cost(self, items):
        return sum(
            item.get("hours", 0) * item.get("coach", 0) * item.get("price", 0)
            for item in items
        )


@api_view(["GET"])
@permission_classes(
    [IsAuthenticated]
)  # Assuming authenticated users can access all benchmarks
def get_all_benchmarks(request):
    if request.method == "GET":
        try:
            benchmarks = Benchmark.objects.all()
            serializer = BenchmarkSerializer(benchmarks, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class UserHierarchyListCreateView(generics.ListCreateAPIView):
    """API view for listing and creating UserHierarchy records"""

    serializer_class = UserHierarchySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = UserHierarchy.objects.all().order_by("-created_at")

        # Filter by subordinate or supervisor if specified
        subordinate_id = self.request.query_params.get("subordinate", None)
        if subordinate_id:
            queryset = queryset.filter(subordinate_id=subordinate_id)

        supervisor_id = self.request.query_params.get("supervisor", None)
        if supervisor_id:
            queryset = queryset.filter(supervisor_id=supervisor_id)

        role_id = self.request.query_params.get("role", None)
        if role_id:
            queryset = queryset.filter(role_id=role_id)

        is_primary = self.request.query_params.get("is_primary", None)
        if is_primary and is_primary.lower() in ("true", "false"):
            queryset = queryset.filter(is_primary=is_primary.lower() == "true")

        return queryset

    def perform_create(self, serializer):
        # Transaction to ensure both the hierarchy record and change history are created
        with transaction.atomic():
            hierarchy = serializer.save()

            # Create a hierarchy change record for auditing
            HierarchyChange.objects.create(
                changed_by=self.request.user,
                change_type="created",
                subordinate=hierarchy.subordinate,
                supervisor=hierarchy.supervisor,
                role=hierarchy.role,
                details=f"Created hierarchy relationship: {hierarchy.subordinate.first_name} {hierarchy.subordinate.last_name} reports to {hierarchy.supervisor.first_name} {hierarchy.supervisor.last_name}",
            )


class UserHierarchyRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating and deleting UserHierarchy records"""

    serializer_class = UserHierarchySerializer
    permission_classes = [IsAuthenticated]
    queryset = UserHierarchy.objects.all()

    def perform_update(self, serializer):
        # Transaction to ensure both updates happen
        with transaction.atomic():
            # Get the original data before update
            instance = self.get_object()

            # Update the record
            updated_instance = serializer.save()

            # Create a change record
            HierarchyChange.objects.create(
                changed_by=self.request.user,
                change_type="updated",
                subordinate=updated_instance.subordinate,
                supervisor=updated_instance.supervisor,
                role=updated_instance.role,
                details=f"Updated hierarchy relationship: {updated_instance.subordinate.first_name} reports to {updated_instance.supervisor.first_name}",
            )

    def perform_destroy(self, instance):
        # Transaction to ensure both deletions happen atomically
        with transaction.atomic():
            # Create a change record before deleting
            HierarchyChange.objects.create(
                changed_by=self.request.user,
                change_type="deleted",
                subordinate=instance.subordinate,
                supervisor=instance.supervisor,
                role=instance.role,
                details=f"Deleted hierarchy relationship: {instance.subordinate.first_name} reported to {instance.supervisor.first_name}",
            )

            # Delete the instance
            instance.delete()


class UserHierarchyRetrieveAPIView(APIView):
    """API to get the complete hierarchy for a specific user"""

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        employee = get_object_or_404(Employee, id=user_id)

        # Get supervisors (users who supervise the given user)
        supervisors = UserHierarchy.objects.filter(subordinate=employee).order_by(
            "hierarchy_level"
        )

        # Get subordinates (users who report to the given user)
        subordinates = UserHierarchy.objects.filter(supervisor=employee).order_by(
            "hierarchy_level"
        )

        # Serialize the data
        supervisor_data = UserHierarchySerializer(supervisors, many=True).data
        subordinate_data = UserHierarchySerializer(subordinates, many=True).data
        user_data = EmployeeSerializer(employee).data

        return Response(
            {
                "user": user_data,
                "supervisors": supervisor_data,
                "subordinates": subordinate_data,
            }
        )


class HierarchyChangeListAPIView(generics.ListAPIView):
    """API to list hierarchy changes with filtering options"""

    serializer_class = HierarchyChangeSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HierarchyChange.objects.all().order_by("-changed_at")

        # Filter by user if specified
        user_id = self.kwargs.get("user_id", None)
        if user_id:
            queryset = queryset.filter(
                Q(subordinate_id=user_id) | Q(supervisor_id=user_id)
            )

        # Additional filtering options
        change_type = self.request.query_params.get("change_type", None)
        if change_type:
            queryset = queryset.filter(change_type=change_type)

        changed_by = self.request.query_params.get("changed_by", None)
        if changed_by:
            queryset = queryset.filter(changed_by_id=changed_by)

        role = self.request.query_params.get("role", None)
        if role:
            queryset = queryset.filter(role_id=role)

        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)
        if start_date and end_date:
            queryset = queryset.filter(changed_at__range=[start_date, end_date])

        return queryset


class PotentialSupervisorsAPIView(APIView):
    """API to get potential supervisors for hierarchy management"""

    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        # Get all users who are not the current user
        # In a real app, you might want to filter this further based on roles or permissions
        potential_supervisors = Employee.objects.filter(active_inactive=True)
        serializer = EmployeeSerializer(potential_supervisors, many=True)
        return Response(serializer.data)


# User Delegation API Views
class UserDelegationListCreateView(generics.ListCreateAPIView):
    """API view for listing and creating UserDelegation records"""

    serializer_class = UserDelegationSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        superadmin = SuperAdmin.objects.filter(user__user=self.request.user)
        leader = Leader.objects.filter(user__user=self.request.user)
        queryset = UserDelegation.objects.all().order_by("-created_at")
        if not (superadmin or leader):
            queryset = queryset.filter(created_by=self.request.user)

        # Filter by delegated_from or delegated_to if specified
        delegated_from = self.request.query_params.get("delegated_from", None)
        if delegated_from:
            queryset = queryset.filter(delegated_from_id=delegated_from)

        delegated_to = self.request.query_params.get("delegated_to", None)
        if delegated_to:
            queryset = queryset.filter(delegated_to_id=delegated_to)

        status_param = self.request.query_params.get("status", None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by active delegations (current date is between start_date and end_date)
        active_only = self.request.query_params.get("active_only", None)
        if active_only and active_only.lower() == "true":
            now = timezone.now()
            queryset = queryset.filter(
                status="active", start_date__lte=now, end_date__gte=now
            )

        return queryset

    def perform_create(self, serializer):
        """Additional operations when creating a delegation"""
        # Set status based on dates

        now = timezone.now()
        start_date = serializer.validated_data.get("start_date")

        # If start date is in the future, set status to scheduled
        # Otherwise, set to active
        initial_status = "scheduled" if start_date > now else "active"
        # Save with the determined status
        serializer.save(created_by=self.request.user, status=initial_status)


class UserDelegationRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating and deleting UserDelegation records"""

    serializer_class = UserDelegationSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserDelegation.objects.all()

    def update(self, request, *args, **kwargs):
        """Handle updates with additional validations"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # If only updating status, handle it differently
        data = serializer.validated_data
        if "status" in data and len(data) == 1:
            new_status = data["status"]

            # If activating, ensure it's within date range
            if new_status == "active":
                now = timezone.now()
                if not (instance.start_date <= now <= instance.end_date):
                    return Response(
                        {"detail": "Cannot activate delegation outside its date range"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        self.perform_update(serializer)
        return Response(serializer.data)


# Delegation History API Views
class DelegationHistoryListView(generics.ListAPIView):
    """API view for listing DelegationHistory records"""

    serializer_class = DelegationHistorySerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DelegationHistory.objects.all().order_by("-performed_at")

        # Apply filters based on query parameters
        delegation_id = self.request.query_params.get("delegation", None)
        if delegation_id:
            queryset = queryset.filter(delegation_id=delegation_id)

        user_id = self.request.query_params.get("user", None)
        if user_id:
            # Get delegations where this user is either delegating or receiving
            delegations = UserDelegation.objects.filter(
                Q(delegated_from_id=user_id) | Q(delegated_to_id=user_id)
            ).values_list("id", flat=True)
            queryset = queryset.filter(delegation_id__in=delegations)

        action_type = self.request.query_params.get("action_type", None)
        if action_type:
            queryset = queryset.filter(action__icontains=action_type)

        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)
        if start_date and end_date:
            queryset = queryset.filter(performed_at__range=[start_date, end_date])

        content_type = self.request.query_params.get("content_type", None)
        if content_type:
            queryset = queryset.filter(content_type=content_type)

        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(action__icontains=search)

        return queryset


class DelegationHistoryDetailView(generics.RetrieveAPIView):
    """API view for retrieving a single DelegationHistory record"""

    serializer_class = DelegationHistorySerializer
    permission_classes = [IsAuthenticated]
    queryset = DelegationHistory.objects.all()


class RecordDelegationAction(APIView):
    """API to record an action performed under delegation"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        delegation_id = request.data.get("delegation_id")
        action = request.data.get("action")
        content_type = request.data.get("content_type", "")
        object_id = request.data.get("object_id", None)

        if not delegation_id or not action:
            return Response(
                {"detail": "delegation_id and action are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the delegation
        try:
            delegation = UserDelegation.objects.get(id=delegation_id)
        except UserDelegation.DoesNotExist:
            return Response(
                {"detail": "Delegation not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Ensure the delegation is active
        now = timezone.now()
        if not (
            delegation.status == "active"
            and delegation.start_date <= now <= delegation.end_date
        ):
            return Response(
                {"detail": "Delegation is not active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure the current user is the delegated_to user
        if request.user.id != delegation.delegated_to_id:
            return Response(
                {
                    "detail": "You are not authorized to perform actions under this delegation"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Record the delegation action
        history = DelegationHistory.objects.create(
            delegation=delegation,
            action=action,
            content_type=content_type,
            object_id=object_id,
        )

        serializer = DelegationHistorySerializer(history)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrganizationStructureAPIView(APIView):
    """API to get the organizational structure for visualization"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the top-level supervisors (users who don't report to anyone)
        top_level_users = User.objects.filter(is_active=True).exclude(
            id__in=UserHierarchy.objects.values_list("subordinate_id", flat=True)
        )

        # Build the organization structure recursively
        org_structure = self._build_org_structure(top_level_users)

        return Response(org_structure)

    def _build_org_structure(self, users):
        """Recursively build the organization structure"""
        structure = []

        for user in users:
            # Get all direct reports for this user
            subordinates = UserHierarchy.objects.filter(
                supervisor=user, is_primary=True  # Only consider primary relationships
            ).values_list("subordinate_id", flat=True)
            subordinate_users = User.objects.filter(id__in=subordinates)

            # Get user roles
            roles = []
            try:
                if hasattr(user, "profile") and user.profile:
                    roles = list(user.profile.roles.values_list("name", flat=True))
            except:
                pass

            # Create user node
            user_node = {
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}".strip() or user.username,
                "email": user.email,
                "roles": roles,
                "children": (
                    self._build_org_structure(subordinate_users)
                    if subordinate_users
                    else []
                ),
            }

            structure.append(user_node)

        return structure


@api_view(["GET"])
def get_employees(request):
    try:
        # Check for the 'active' query parameter
        active = request.query_params.get("active")  # Default to 'true' if not provided

        # Filter employees based on 'status' field using the 'active' parameter
        if active == "false":
            employees = Employee.objects.filter(status="active")
        else:
            employees = Employee.objects.all()

        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("superadmin", "finance", "leader")])
def create_employee(request):
    try:
        with transaction.atomic():
            sales_id = request.query_params.get("sales_id")
            data = request.data
            first_name = data.get("first_name", "").title()
            last_name = data.get("last_name", "").title()
            email = data.get("email", "").strip().lower()
            add_users = data.get("add_users", [])
            phone_number = data.get("phone_number")
            full_name = first_name + " " + last_name
            if not (first_name and last_name and phone_number and email):
                return Response(
                    {"error": "Please fill all the mandatory fields."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Employee.objects.filter(email=email).exists():
                return Response(
                    {"error": "Employee with this mail already exisit."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.filter(username=email).first()

            if not user:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=User.objects.make_random_password(),
                )
                profile = Profile.objects.create(user=user)
            else:
                profile = Profile.objects.get(user=user)

            employee_role, created = Role.objects.get_or_create(name="employee")
            profile.roles.add(employee_role)
            profile.save()
            employee = Employee.objects.create(user=profile)

            employee_serializer = EmployeeSerializer(
                employee, data=request.data, partial=True
            )
            if employee_serializer.is_valid():
                employee_serializer.save()
                create_user_permission_for_role("employee", "Manager", profile)

            for role_id in add_users:

                role = Role.objects.get(id=role_id)
                if role in profile.roles.all():
                    continue

                profile.roles.add(role)
                profile.save()
                instance = None
                if "pmo" == role.name:

                    instance = Pmo.objects.create(
                        user=profile, name=full_name, email=email, phone=phone_number
                    )

                if "sales" == role.name:

                    instance = Sales.objects.create(
                        user=profile, name=full_name, email=email, phone=phone_number
                    )

                if "finance" == role.name:

                    instance = Finance.objects.create(
                        user=profile,
                        name=full_name,
                        email=email,
                    )

                if instance:
                    create_user_permission_for_role(role.name, "Manager", profile)

            return Response(
                {"message": "Employee created successfully."},
                status=status.HTTP_201_CREATED,
            )

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to create employee."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class HrAndOrganisationView(generics.ListAPIView):
    permission_classes = [
        IsAuthenticated,
        IsInRoles("coach", "pmo", "learner", "hr", "sales"),
    ]
    serializer_class = HrAndOrganisationSerializer

    def get_queryset(self):
        # Fetch HR data with organization information
        search = self.request.query_params.get("search", "")

        hr_with_org = HR.objects.filter(organisation__isnull=False).select_related(
            "organisation"
        )
        # Fetch organizations that have no associated HR data
        organisations_with_hr_ids = hr_with_org.values_list(
            "organisation_id", flat=True
        )
        organisations_without_hr = Organisation.objects.exclude(
            id__in=organisations_with_hr_ids
        )

        if search:
            hr_with_org = hr_with_org.filter(
                Q(first_name__icontains=search)
                | Q(email__icontains=search)
                | Q(last_name__icontains=search)
                | Q(organisation__name__icontains=search)
            )
            organisations_without_hr = organisations_without_hr.filter(
                Q(name__icontains=search)
            )
        # Create a list to hold the combined data
        data_source = list(hr_with_org) + list(organisations_without_hr)

        return data_source


@api_view(["POST"])
@transaction.atomic
def create_gmsheet(request):
    try:
        if request.method == "POST":
            gmsheet_data = request.data.get("gmsheet")
            gm_sheet_serializer = GmSheetSerializer(data=gmsheet_data)
            if gm_sheet_serializer.is_valid():
                gm_sheet = gm_sheet_serializer.save()
                if gm_sheet.sales:
                    gm_sheet.added_by = gm_sheet.sales.user.user
                    gm_sheet.save()
                offerings_data = request.data.get("offerings")
                if offerings_data:
                    for offering_data in offerings_data:
                        offering_data["gm_sheet"] = gm_sheet.id
                        offering_serializer = OfferingSerializer(data=offering_data)
                        if offering_serializer.is_valid():
                            offering_serializer.save()
                        else:
                            return Response(
                                offering_serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                return Response(
                    gm_sheet_serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                gm_sheet_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        # Handle any exceptions here
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_offerings_by_gmsheet_id(request, gmsheet_id):
    offerings = Offering.objects.filter(gm_sheet=gmsheet_id)
    serializer = OfferingSerializer(offerings, many=True)
    return Response(serializer.data)


@api_view(["PUT"])
@transaction.atomic
def add_offerings(request, id):
    try:
        gm_sheet = GmSheet.objects.get(id=id)
        existing_offerings = Offering.objects.filter(gm_sheet=gm_sheet)
        is_add_offering = existing_offerings.count() == 0

        offerings_data = request.data.get("offerings", [])
        errors, status_code = handle_offerings_update(gm_sheet, offerings_data)
        if errors:
            return Response(errors, status=status_code)

        if is_add_offering:
            recipient_email = (
                ["sujata@meeraq.com"]
                if env("ENVIRONMENT") == "PRODUCTION"
                else ["naveen@meeraq.com"]
            )
            send_mail_templates(
                "leader_emails/gm_sheet_created.html",
                recipient_email,
                "New GM Sheet created",
                {
                    "projectName": gm_sheet.project_name,
                    "clientName": gm_sheet.client_name,
                    "startdate": gm_sheet.start_date,
                    "projectType": gm_sheet.project_type,
                    "salesName": gm_sheet.sales.name,
                },
                [],
            )

        return Response({"message": "Update Successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to update data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@transaction.atomic
def update_gmsheet(request, id):
    try:
        gm_sheet = GmSheet.objects.get(id=id)
        gmsheet_data = request.data.get("gmsheet")
        gm_sheet_serializer = GmSheetSerializer(
            gm_sheet, data=gmsheet_data, partial=True
        )

        if gm_sheet_serializer.is_valid():
            gm_sheet = gm_sheet_serializer.save()

            return Response(gm_sheet_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                gm_sheet_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to update data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
def update_is_accepted_status(request, pk):
    try:
        gm_sheet = GmSheet.objects.get(pk=pk)
    except GmSheet.DoesNotExist:
        return Response(
            {"error": "GmSheet not found"}, status=status.HTTP_404_NOT_FOUND
        )
    data = {}
    # Check if is_accepted is present in request data
    if "is_accepted" in request.data:
        data["is_accepted"] = request.data.get("is_accepted")
        # Call send_mail_templates if is_accepted is True
        if data["is_accepted"]:
            template_name = "gm_sheet_approved.html"
            subject = "GM Sheet approved"
            context_data = {
                "projectName": gm_sheet.project_name,
                "clientName": gm_sheet.client_name,
                "startdate": gm_sheet.start_date,
                "projectType": gm_sheet.project_type,
                "salesName": gm_sheet.sales.name,
            }
            bcc_list = []  # No BCC
            send_mail_templates(
                template_name,
                (
                    [gm_sheet.sales.email]
                    if env("ENVIRONMENT") == "PRODUCTION"
                    else ["naveen@meeraq.com"]
                ),
                subject,
                context_data,
                bcc_list,
            )

    # Check if deal_status is present in request data
    if "deal_status" in request.data:
        data["deal_status"] = request.data.get("deal_status")
        all_offerings = Offering.objects.filter(gm_sheet=gm_sheet)
        all_offerings.update(is_won=False)
        if data["deal_status"].lower() == "won":
            offering_id = request.data.get("offering_id")
            if not offering_id:
                return Response(
                    {"error": "Offering ID not provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                offering = Offering.objects.get(pk=offering_id)
                offering.is_won = True
                offering.save()
            except Offering.DoesNotExist:
                return Response(
                    {"error": "Offering not found"}, status=status.HTTP_404_NOT_FOUND
                )

    gm_sheet_serializer = GmSheetSerializer(gm_sheet, data=data, partial=True)
    if gm_sheet_serializer.is_valid():
        gm_sheet_serializer.save()
        return Response(gm_sheet_serializer.data, status=status.HTTP_200_OK)
    return Response(gm_sheet_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def create_benchmark(request):
    year = request.data.get("year")
    if not year:
        return Response(
            {"error": "Year is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Fetch all existing benchmarks
    existing_benchmarks = Benchmark.objects.all()

    # Gather project_type keys from existing benchmarks
    project_type_keys = set()
    for benchmark in existing_benchmarks:
        project_type_keys.update(benchmark.project_type.keys())

    # Create new project_type with keys and empty string values
    project_type = {key: "" for key in project_type_keys}

    data = {
        "year": year,
        "project_type": project_type,
    }

    serializer = BenchmarkSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def update_benchmark(request):
    year = request.data.get("year", None)  # Extract year from request data
    benchmark_data = request.data.get(
        "benchmark", None
    )  # Extract benchmark data from request data

    if year is None:
        return Response(
            {"error": "Year is required in the payload"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        benchmark = Benchmark.objects.get(year=year)
    except Benchmark.DoesNotExist:
        return Response(
            {"error": f"Benchmark for year {year} does not exist"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "PUT":
        serializer = BenchmarkSerializer(
            benchmark, data={"project_type": benchmark_data}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_employee(request):
    try:
        with transaction.atomic():
            employee_id = request.data.get("id")
            if not employee_id:
                return Response(
                    {"error": "Employee ID is required."}, status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                employee = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                return Response(
                    {"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND
                )
            
            # Process input data
            first_name = request.data.get("first_name", "").title()
            last_name = request.data.get("last_name", "").title()
            email = request.data.get("email", "").strip().lower()
            phone_number = request.data.get("phone_number")
            add_users = request.data.get("add_users", [])
            full_name = f"{first_name} {last_name}"
            
            # Update the employee record
            serializer = EmployeeSerializer(employee, data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            instance = serializer.save()
            profile = employee.user
            
            # Process role assignments
            for role_id in add_users:
                try:
                    role = Role.objects.get(id=role_id)
               
                    # Skip if user already has this role
                    if role in profile.roles.all():
                        continue
                        
                    profile.roles.add(role)
                    profile.save()
                    
                    # Create role-specific profile based on role name
                    role_instance = None
                    role_name = role.name.lower()
                    
                    if role_name == "pmo":
                        role_instance = Pmo.objects.create(
                            user=profile, 
                            name=full_name, 
                            email=email, 
                            phone=phone_number
                        )
                    elif role_name == "sales":
                        role_instance = Sales.objects.create(
                            user=profile, 
                            name=full_name, 
                            email=email, 
                            phone=phone_number
                        )
                    elif role_name == "finance":
                        role_instance = Finance.objects.create(
                            user=profile,
                            name=full_name,
                            email=email
                        )
                    
                    if role_instance:
                        create_user_permission_for_role(role_name, "Manager", profile)
                except Role.DoesNotExist:
                    # Log the error but continue processing other roles
                    print(f"Role with ID {role_id} not found")
            
            # Update active/inactive status
            if instance.status == "active":
                update_profiles_active_inactive(instance.user, True)
            else:
                update_profiles_active_inactive(instance.user, False)
            
            return Response(serializer.data)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to updated employee"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_employee(request):
    employee_id = request.data.get("id")
    if not employee_id:
        return Response(
            {"error": "Employee ID is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND
        )

    employee.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
