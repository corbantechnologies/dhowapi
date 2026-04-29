import string
import secrets
import resend
import logging
from datetime import datetime
from django.template.loader import render_to_string

from dhowapi.settings import DOMAIN

logger = logging.getLogger(__name__)


current_year = datetime.now().year


def generate_reference():
    characters = string.ascii_letters + string.digits
    random_string = "".join(secrets.choice(characters) for _ in range(12))
    return random_string.upper()


def generate_user_number():
    year = datetime.now().year % 100
    random_number = "".join(secrets.choice(string.digits) for _ in range(5))
    return f"DHOW{year}{random_number}"


# welcome email
def send_welcome_email(user):
    """
    A function to send a welcome email
    """
    try:
        email_body = render_to_string(
            "welcome.html",
            {
                "user": user,
                "current_year": datetime.now().year,
            },
        )
        params = {
            "from": "Dhow Onboarding <dhow-onboarding@corbantechnologies.org>",
            "to": [user.email],
            "subject": "Welcome to Dhow",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(f"Welcome email sent to {user.email} with response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
        return None


# forgot password email
def send_forgot_password_email(user, code):
    """
    A function to send a forgot password email
    """
    try:
        email_body = render_to_string(
            "forgot_password.html",
            {
                "user": user,
                "code": code,
                "current_year": datetime.now().year,
            },
        )
        params = {
            "from": "Dhow Security <dhow-security@corbantechnologies.org>",
            "to": [user.email],
            "subject": "Reset Your Dhow Password",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(
            f"Forgot password email sent to {user.email} with response: {response}"
        )
        return response
    except Exception as e:
        logger.error(f"Error sending forgot password email to {user.email}: {str(e)}")
        return None


# password success
def send_password_reset_success_email(user):
    """
    A function to send a password reset success email
    """
    try:
        email_body = render_to_string(
            "password_reset_success.html",
            {
                "user": user,
                "current_year": datetime.now().year,
            },
        )
        params = {
            "from": "Dhow Security <dhow-security@corbantechnologies.org>",
            "to": [user.email],
            "subject": "Password Reset Successful - Dhow",
            "html": email_body,
        }
        response = resend.Emails.send(params)
        logger.info(
            f"Password reset success email sent to {user.email} with response: {response}"
        )
        return response
    except Exception as e:
        logger.error(
            f"Error sending password reset success email to {user.email}: {str(e)}"
        )
        return None
