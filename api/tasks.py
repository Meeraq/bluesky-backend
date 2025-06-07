from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from operationsBackend import settings
from celery import shared_task
import environ

env = environ.Env()

@shared_task
def scheduled_send_mail_templates(
    file_name, user_email, email_subject, content, bcc_emails
):
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
       
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")