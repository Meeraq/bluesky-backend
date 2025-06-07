from ..serializers import VendorDepthOneSerializer
import environ
import os
import pdfkit


env = environ.Env()

wkhtmltopdf_path = os.environ.get(
    "WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

pdfkit_config = pdfkit.configuration(wkhtmltopdf=f"{wkhtmltopdf_path}")


def get_user_data(user):
    if not user.profile:
        return None
    elif user.profile.roles.count() == 0:
        return None
    user_profile_role = user.profile.roles.filter(name="vendor")
    if not user.profile.vendor.active_inactive:
        return None
    if user_profile_role.exists() and user.profile.vendor:
        serializer = VendorDepthOneSerializer(user.profile.vendor)
    else:
        return None
    return {
        **serializer.data,
        "user": {**serializer.data["user"], "type": "vendor"},
    }
