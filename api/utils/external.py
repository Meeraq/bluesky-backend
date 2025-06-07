# This utils covers the 100ms, Microsoft, Google, Teams

import requests
from datetime import datetime, timedelta
from django.utils import timezone
from ..models import UserToken, CalendarEvent
import jwt
from django.template import Template as RenderTemplate, Context as RenderContext
from django.db.models import (
   
    Q,
    Exists,
    OuterRef
   
)
import uuid

from api.utils.email import send_mail_templates


import environ

env = environ.Env()


def convert_to_24hr_format(time_str):
    time_obj = datetime.strptime(time_str, "%I:%M %p")
    time_24hr = time_obj.strftime("%H:%M")
    return time_24hr


def refresh_microsoft_access_token(user_token):
    if not user_token:
        return None

    refresh_token = user_token.refresh_token
    access_token_expiry = user_token.access_token_expiry
    auth_code = user_token.authorization_code
    if not refresh_token:
        return None

    access_token_expiry = int(access_token_expiry)

    expiration_timestamp = user_token.updated_at + timezone.timedelta(
        seconds=access_token_expiry
    )

    if expiration_timestamp <= timezone.now():
        token_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/token"

        token_data = {
            "client_id": env("MICROSOFT_CLIENT_ID"),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_secret": env("MICROSOFT_CLIENT_SECRET"),
        }

        response = requests.post(token_url, data=token_data)
        token_json = response.json()

        if "access_token" in token_json:
            user_token.access_token = token_json["access_token"]
            user_token.access_token_expiry = token_json.get("expires_in")
            user_token.updated_at = timezone.now()
            user_token.save()

            return user_token.access_token

    return user_token.access_token


def create_microsoft_calendar_event(
    access_token, event_details, attendee_email_name, session
):
    event_create_url = "https://graph.microsoft.com/v1.0/me/events"

    formatted_date = datetime.strptime(event_details["startDate"], "%d-%m-%Y").strftime(
        "%Y-%m-%d"
    )

    start_datetime = (
        f"{formatted_date}T{convert_to_24hr_format(event_details['startTime'])}:00"
    )
    end_datetime = (
        f"{formatted_date}T{convert_to_24hr_format(event_details['endTime'])}:00"
    )

    event_details_title = event_details["title"]
    if event_details["title"] == "Coaching Session Session":
        event_details_title = "Coaching Session"

    event_payload = {
        "subject": event_details_title,
        "body": {"contentType": "HTML", "content": event_details["description"]},
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        "attendees": [{"emailAddress": attendee_email_name, "type": "required"}],
    }

    user_token = UserToken.objects.get(access_token=access_token)
    new_access_token = refresh_microsoft_access_token(user_token)
    if not new_access_token:
        new_access_token = access_token

    headers = {
        "Authorization": f"Bearer {new_access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(event_create_url, json=event_payload, headers=headers)

    if response.status_code == 201:
        microsoft_response_data = response.json()

        calendar_event = CalendarEvent(
            event_id=microsoft_response_data.get("id"),
            title=event_details_title,
            description=event_details.get("description"),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            attendee=attendee_email_name.get("address"),
            creator=microsoft_response_data.get("organizer", {})
            .get("emailAddress", {})
            .get("address", ""),
            session=session,
            account_type="microsoft",
        )
        calendar_event.save()

        print("Event created successfully.")
        return True
    else:
        print(f"Event creation failed. Status code: {response.status_code}")
        print(response.text)
        return False


def delete_google_calendar_event(access_token, event_id):
    try:
        response = requests.delete(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 204:
            return {"message": "Event deleted successfully"}
        elif response.status_code == 404:
            return {"error": "Event not found"}
        else:
            return {
                "error": "Failed to delete event",
                "status_code": response.status_code,
            }

    except Exception as e:
        return {"error": "An error occurred", "details": str(e)}


def delete_microsoft_calendar_event(access_token, event_id):
    try:
        event_delete_url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.delete(event_delete_url, headers=headers)

        if response.status_code == 204:
            return {"message": "Event deleted successfully"}
        elif response.status_code == 404:
            return {"error": "Event not found"}
        else:
            return {
                "error": "Failed to delete event",
                "status_code": response.status_code,
            }

    except Exception as e:
        return {"error": "An error occurred", "details": str(e)}


def create_teams_meeting(user_email, live_session_id, topic, start_time, end_time):
    try:
        event_create_url = "https://graph.microsoft.com/v1.0/me/onlineMeetings"
        user_token = UserToken.objects.get(user_profile__user__username=user_email)
        new_access_token = refresh_microsoft_access_token(user_token)
        if not new_access_token:
            new_access_token = user_token.access_token
        headers = {
            "Authorization": f"Bearer {new_access_token}",
            "Content-Type": "application/json",
        }
        event_payload = {
            "startDateTime": start_time,
            "endDateTime": end_time,
            "subject": topic,
        }
        response = requests.post(event_create_url, json=event_payload, headers=headers)
        print(response.json())
        if response.status_code == 201:
            meeting_info = response.json()
            meeting_link = meeting_info.get("joinWebUrl")
            live_session = LiveSession.objects.get(id=live_session_id)
            live_session.meeting_link = meeting_link
            live_session.teams_meeting_id = meeting_info.get("id")
            live_session.save()
            print("Meeting Link Generated")
            return True
        else:
            return False
    except Exception as e:
        print(str(e))
        return False


def delete_teams_meeting(user_email, live_session):
    user_token = UserToken.objects.get(user_profile__user__username=user_email)
    new_access_token = refresh_microsoft_access_token(user_token)
    if not new_access_token:
        new_access_token = user_token.access_token
    meeting_delete_url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{live_session.teams_meeting_id}"
    headers = {
        "Authorization": f"Bearer {new_access_token}",
    }
    response = requests.delete(meeting_delete_url, headers=headers)
    if response.status_code == 204:
        # live_session.meeting_link = ""
        # live_session.save()
        return {"message": "Event deleted successfully"}
    elif response.status_code == 404:
        return {"error": "Event not found"}
    else:
        return {
            "error": "Failed to delete event",
            "status_code": response.status_code,
        }


def get_access_token(user_email):
    try:
        user_token = UserToken.objects.get(user_profile__user__username=user_email)
        new_access_token = refresh_microsoft_access_token(user_token)
        return new_access_token if new_access_token else user_token.access_token
    except UserToken.DoesNotExist:
        print(f"User token not found for email: {user_email}")
        return None


def format_datetime(timestamp):
    datetime_obj = datetime.fromtimestamp(int(timestamp) / 1000) + timedelta(
        hours=5, minutes=30
    )
    return datetime_obj.strftime("%Y-%m-%dT%H:%M:00")

def update_or_create_outlook_calendar_invite(
    calendar_invite=None,
    subject=None,
    description=None,
    start_time_stamp=None,
    end_time_stamp=None,
    attendees=None,
    user_email=None,
    caas_session=None,
    schedular_session=None,
    live_session=None,
    meeting_location=None,
    task=None,
    free=False,
    action="create",
):
    access_token = get_access_token(user_email)
    if not access_token:
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    start_datetime = format_datetime(start_time_stamp)
    end_datetime = format_datetime(end_time_stamp)

    event_payload = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": description},
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        "attendees": attendees,
        "location": {
            "displayName": meeting_location if meeting_location else "",
        },
        "showAs": "free" if free else "busy",
    }

    if action == "update":
        if not calendar_invite or not calendar_invite.event_id:
            print("Invalid calendar invite for update.")
            return False
        event_update_url = (
            f"https://graph.microsoft.com/v1.0/me/events/{calendar_invite.event_id}"
        )
        success = send_outlook_request(
            event_update_url, "PATCH", event_payload, headers
        )
        if success:
            calendar_invite.title = subject
            calendar_invite.description = description
            calendar_invite.start_datetime = start_datetime
            calendar_invite.end_datetime = end_datetime
            calendar_invite.attendees = attendees
            calendar_invite.caas_session = caas_session
            calendar_invite.schedular_session = schedular_session
            calendar_invite.live_session = live_session
            calendar_invite.management_task = task
            calendar_invite.save()
        return success

    elif action == "create":
        event_create_url = "https://graph.microsoft.com/v1.0/me/events"
        microsoft_response_data = send_outlook_request(
            event_create_url, "POST", event_payload, headers
        )
        if microsoft_response_data:
            calendar_invite = CalendarInvites(
                event_id=microsoft_response_data.get("id"),
                title=subject,
                description=description,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                attendees=attendees,
                creator=user_email,
                caas_session=caas_session,
                schedular_session=schedular_session,
                live_session=live_session,
                management_task=task,
            )
            calendar_invite.save()
            print("Calendar invite sent successfully.")
            return True

    return False


def update_outlook_calendar_invite(*args, **kwargs):
    return update_or_create_outlook_calendar_invite(*args, **kwargs, action="update")


def create_outlook_calendar_invite(*args, **kwargs):
    return update_or_create_outlook_calendar_invite(*args, **kwargs, action="create")


def get_all_calendar_events(user_email):
    events_url = "https://graph.microsoft.com/v1.0/me/events"
    try:
        user_token = UserToken.objects.get(user_profile__user__username=user_email)
        new_access_token = refresh_microsoft_access_token(user_token)
        if not new_access_token:
            new_access_token = user_token.access_token

        headers = {
            "Authorization": f"Bearer {new_access_token}",
            "Content-Type": "application/json",
        }

        response = requests.get(events_url, headers=headers)

        if response.status_code == 200:
            events_data = response.json()
            return events_data["value"]  # Return the list of events
        else:
            print(f"Failed to fetch events. Status code: {response.status_code}")
            print(response.text)
            return None

    except UserToken.DoesNotExist:
        print(f"User token not found for email: {user_email}")
        return None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def delete_outlook_calendar_invite(calendar_invite):
    try:
        user_token = UserToken.objects.get(
            user_profile__user__username=calendar_invite.creator
        )
        new_access_token = refresh_microsoft_access_token(user_token)
        if not new_access_token:
            new_access_token = user_token.access_token
        event_delete_url = (
            f"https://graph.microsoft.com/v1.0/me/events/{calendar_invite.event_id}"
        )
        headers = {
            "Authorization": f"Bearer {new_access_token}",
        }
        response = requests.delete(event_delete_url, headers=headers)
        if response.status_code == 204:
            calendar_invite.delete()
            return {"message": "Event deleted successfully"}
        elif response.status_code == 404:
            return {"error": "Event not found"}
        else:
            return {
                "error": "Failed to delete event",
                "status_code": response.status_code,
            }

    except Exception as e:
        return {"error": "An error occurred", "details": str(e)}


def update_outlook_attendees(calendar_invite, new_attendees):
    try:
        user_token = UserToken.objects.get(
            user_profile__user__username=calendar_invite.creator
        )
        new_access_token = refresh_microsoft_access_token(user_token)
        if not new_access_token:
            new_access_token = user_token.access_token

        graph_api_url = (
            f"https://graph.microsoft.com/v1.0/me/events/{calendar_invite.event_id}"
        )

        headers = {
            "Authorization": f"Bearer {new_access_token}",
            "Content-Type": "application/json",
        }

        response = requests.patch(
            graph_api_url, json={"attendees": new_attendees}, headers=headers
        )

        if response.status_code == 200:
            print("Attendees updated successfully.")

        else:
            print(f"Failed to update attendees: {response.text}")

    except Exception as e:
        print(str(e))


def generateManagementToken():
    expires = 24 * 3600
    now = datetime.utcnow()
    exp = now + timedelta(seconds=expires)
    return jwt.encode(
        payload={
            "access_key": env("100MS_APP_ACCESS_KEY"),
            "type": "management",
            "version": 2,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": exp,
            "nbf": now,
        },
        key=env("100MS_APP_SECRET"),
    )


def generate_room_id(email):
    management_token = generateManagementToken()

    try:
        payload = {
            "name": email.replace(".", "-").replace("@", ""),
            "description": "This is a sample description for the room",
            "region": "in",
        }

        response_from_100ms = requests.post(
            "https://api.100ms.live/v2/rooms",
            headers={
                "Authorization": f"Bearer {management_token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if response_from_100ms.status_code == 200:
            room_id = response_from_100ms.json().get("id")
            return room_id
        else:
            return None
    except Exception as e:
        print(f"Error while generating meeting link: {str(e)}")
        return None


def send_customized_mail(project, event_name, email, variable_data, bcc=[]):
    project_event = ProjectEvent.objects.filter(
        project=project, event_name=event_name
    ).first()
    if project_event:
        subject = project_event.subject
        content = project_event.content
        template = RenderTemplate(content)
        context = RenderContext(variable_data)
        email_message = template.render(context)
        combined_bcc = project_event.bcc_email if project_event.bcc_email else []
        if bcc:
            combined_bcc += bcc
        combined_bcc = list(set(combined_bcc))

        send_mail_templates(
            "customized_mail_template.html",
            [email],
            subject,
            {
                "content": email_message,
            },
            combined_bcc,
        )



TWILIO_BASE_URL = "https://content.twilio.com/v1/"

def twilio_auth():
    return (env("TWILIO_ACCOUNT_SID"), env("TWILIO_AUTH_TOKEN"))


def send_twilio_message(
    to, from_whatsapp, content_sid, messaging_service_sid, content_variables
):
    """
    Utility function to send a Twilio message.
    :param to: Recipient's phone number (WhatsApp format).
    :param from_whatsapp: Sender's WhatsApp number.
    :param content_sid: Twilio ContentSid for the template.
    :param messaging_service_sid: Twilio MessagingServiceSid.
    :param content_variables: JSON formatted string for template variables.
    :return: Response object containing either message SID and status or an error.
    """
    url = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json".format(
        env("TWILIO_ACCOUNT_SID")
    )
    payload = {
        "To": to,
        "From": from_whatsapp,
        "ContentSid": content_sid,
        "MessagingServiceSid": messaging_service_sid,
        "ContentVariables": content_variables,
    }
    response = requests.post(url, data=payload, auth=twilio_auth())
    if response.status_code == 201:
        return {
            "recipient": to,
            "message_sid": response.json().get("sid"),
            "status": response.json().get("status"),
        }
    else:
        return {"recipient": to, "error": response.json()}
