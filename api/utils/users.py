from django.contrib.auth.models import User
from django.db import models
from api.models import (
    Profile,
    Pmo,
    Role,
)
from rest_framework.response import Response
from api.utils.external import (
    generate_room_id,
  
)
from django.db import transaction
from api.utils.batch import (
    add_contact_in_wati
)
def add_new_pmo(data):
    try:
        name = data.get("name")
        email = data.get("email", "").strip().lower()
        phone = data.get("phone")
        username = email  # username and email are the same
        password = data.get("password")
        sub_role = data.get("sub_role")
        room_id = generate_room_id(email)

        # Check if required data is provided
        if not all([name, email, phone, username, password, room_id]):
            return Response(
                {"error": "All required fields must be provided."}, status=400
            )

        with transaction.atomic():
            # Check if the user already exists
            user = User.objects.filter(email=email).first()

            if not user:
                # If the user does not exist, create a new user
                user = User.objects.create_user(
                    username=username, password=password, email=email
                )
                profile = Profile.objects.create(user=user)

            else:
                profile = Profile.objects.get(user=user)

            # Create or get the "pmo" role
            pmo_role, created = Role.objects.get_or_create(name="pmo")
            profile.roles.add(pmo_role)
            profile.save()

            # Create the PMO User using the Profile
            pmo_user = Pmo.objects.create(
                user=profile,
                name=name,
                email=email,
                phone=phone,
                sub_role=sub_role,
                room_id=room_id,
            )

            name = pmo_user.name
            if pmo_user.phone:
                add_contact_in_wati("pmo", name, pmo_user.phone)
            # Return success response without room_id
            return True

    except Exception as e:
        print(str(e))
        return False
