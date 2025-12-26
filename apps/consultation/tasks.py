from celery import shared_task
from django.conf import settings
from django.template import Template, Context
from django.core.mail import send_mail
import os
from .models import Consultation


@shared_task(bind=True, max_retries=3)
def send_consultation_request_confirmation_email(self, consultation_id):
    """Send confirmation email to user when they create a consultation request"""
    try:
        consultation = Consultation.objects.select_related('user', 'package').get(id=consultation_id)

        context = {
            'user_name': consultation.user.get_full_name(),
            'package_name': consultation.package.name,
            'scheduled_date': consultation.scheduled_date,
            'scheduled_time': consultation.scheduled_time,
            'site_url': settings.SITE_URL,
        }

        # Load email template
        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'consultation', 'emails', 'consultation_request_confirmation.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'consultation', 'emails', 'consultation_request_confirmation.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=f"Consultation Request Received - {consultation.package.name}",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[consultation.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "success", "consultation_id": consultation_id}

    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except:
            return {"status": "failure", "consultation_id": consultation_id, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_admin_consultation_notification_email(self, consultation_id):
    """Send notification email to admin when a new consultation request is created"""
    try:
        consultation = Consultation.objects.select_related('user', 'package').get(id=consultation_id)

        context = {
            'user_name': consultation.user.get_full_name(),
            'user_email': consultation.user.email,
            'package_name': consultation.package.name,
            'scheduled_date': consultation.scheduled_date,
            'scheduled_time': consultation.scheduled_time,
            'notes': consultation.notes,
            'site_url': settings.SITE_URL,
        }

        # Load email template
        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'consultation', 'emails', 'admin_consultation_notification.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'consultation', 'emails', 'admin_consultation_notification.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=f"New Consultation Request - {consultation.package.name}",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "success", "consultation_id": consultation_id}

    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except:
            return {"status": "failure", "consultation_id": consultation_id, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_consultation_confirmation_email(self, consultation_id):
    """Send confirmation email to user when admin confirms the consultation"""
    try:
        consultation = Consultation.objects.select_related('user', 'package').get(id=consultation_id)

        context = {
            'user_name': consultation.user.get_full_name(),
            'package_name': consultation.package.name,
            'scheduled_date': consultation.scheduled_date,
            'scheduled_time': consultation.scheduled_time,
            'zoom_link': consultation.zoom_link,
            'site_url': settings.SITE_URL,
        }

        # Load email template
        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'consultation', 'emails', 'consultation_confirmation.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'consultation', 'emails', 'consultation_confirmation.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=f"Consultation Confirmed - {consultation.package.name}",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[consultation.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "success", "consultation_id": consultation_id}

    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except:
            return {"status": "failure", "consultation_id": consultation_id, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_consultation_update_email(self, consultation_id, update_type):
    try:
        consultation = Consultation.objects.select_related('user', 'package').get(id=consultation_id)

        context = {
            'user_name': consultation.user.get_full_name(),
            'package_name': consultation.package.name,
            'scheduled_date': consultation.scheduled_date,
            'scheduled_time': consultation.scheduled_time,
            'status': consultation.get_status_display(),
            'site_url': settings.SITE_URL,
        }

        subject_map = {
            'cancelled': f"Consultation Cancelled - {consultation.package.name}",
            'completed': f"Consultation Completed - {consultation.package.name}",
        }

        subject = subject_map.get(update_type, f"Consultation Update - {consultation.package.name}")

        # Load email template
        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'consultation', 'emails', f'consultation_{update_type}.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'consultation', 'emails', f'consultation_{update_type}.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[consultation.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "success", "consultation_id": consultation_id, "update_type": update_type}

    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except:
            return {"status": "failure", "consultation_id": consultation_id, "update_type": update_type, "error": str(e)}