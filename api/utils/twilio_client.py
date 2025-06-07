# utils/twilio_client.py

from twilio.rest import Client
from django.conf import settings
import environ

env = environ.Env()

def get_twilio_client():
    return Client(env("TWILIO_ACCOUNT_SID"), env("TWILIO_AUTH_TOKEN"))
