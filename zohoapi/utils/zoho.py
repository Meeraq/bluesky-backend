import requests
from zohoapi.models import AccessToken
from django.utils import timezone
from rest_framework.response import Response


import environ

env = environ.Env()


def generate_access_token_from_refresh_token(refresh_token, bigin=False):
    token_url = env("ZOHO_API_BIGIN_TOKEN_URL") if bigin else env("ZOHO_TOKEN_URL")
    client_id = env("ZOHO_API_BIGIN_CLIENT_ID") if bigin else env("ZOHO_CLIENT_ID")
    client_secret = (
        env("ZOHO_API_BIGIN_CLIENT_SECRET") if bigin else env("ZOHO_CLIENT_SECRET")
    )

    # Payload for requesting access token
    token_payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": env("REDIRECT_URI"),
        "grant_type": "refresh_token",
    }
    token_response = requests.post(token_url, params=token_payload)

    token_data = token_response.json()
    if "access_token" in token_data:
        return token_data["access_token"]
    else:
        return None
