from django.contrib.auth.models import User
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from operationsBackend import settings
import environ
from api.models import SentEmailActivity
from django.template import Template as RenderTemplate, Context as RenderContext
import requests
from datetime import datetime
import base64
import pdfkit
from io import BytesIO
from api.utils.constants import pdfkit_config
env = environ.Env()






def create_send_email(user_email, file_name,email_message):
    try:
        user = User.objects.get(username=user_email)
        sent_email = SentEmailActivity.objects.create(
            user=user,
            email_subject=file_name,
            content=email_message,
            timestamp=timezone.now(),
        )
        sent_email.save()
    except Exception as e:
        pass


def send_mail_templates(file_name, user_email, email_subject, content, bcc_emails):
    try:
        email_message = render_to_string(file_name, content)

        email = EmailMessage(
            f"{env('EMAIL_SUBJECT_INITIAL',default='')} {email_subject}",
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            user_email,
            bcc_emails,
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
        for email in user_email:
            create_send_email(email, file_name,email_message)
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")


def send_mail_templates_with_attachment(
    file_name,
    user_email,
    email_subject,
    content,
    body_message,
    bcc_emails,
    is_send_attatched_invoice,
):
    try:
        datetime_obj = datetime.strptime(
            content["invoice"]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        formatted_date = datetime_obj.strftime("%d-%m-%Y")
        pdf_name = f"{content['invoice']['vendor_name']}_{formatted_date}.pdf"
        email = EmailMessage(
            subject=f"{env('EMAIL_SUBJECT_INITIAL', default='')} {email_subject}",
            body=body_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=user_email,
            bcc=bcc_emails,
        )
        if is_send_attatched_invoice:
            attachment_url = content["invoice"]["attatched_invoice"]
            # attachment_file_name = attachment_url.split('/')[-1].split('?')[0]
            attachment_response = requests.get(attachment_url)
            if attachment_response.status_code == 200:
                email.attach(pdf_name, attachment_response.content, "application/pdf")
            else:
                pass
        else:
            image_url = f"{content['invoice']['signature']}"
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            image_base64 = base64.b64encode(image_response.content).decode("utf-8")
            content["image_base64"] = image_base64
            email_message = render_to_string(file_name, content)
            pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)
            result = BytesIO(pdf)
            email.attach(
                pdf_name,
                result.getvalue(),
                "application/pdf",
            )

        # Convert the downloaded image to base64
        # Attach the PDF to the email
        email.content_subtype = "html"
        email.send()

    except Exception as e:
        print(str(e))

