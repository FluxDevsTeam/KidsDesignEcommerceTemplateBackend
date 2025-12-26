from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from .models import NewsletterCampaign, Subscriber
import os


@shared_task(bind=True, max_retries=3)
def send_newsletter_campaign(self, campaign_id):
    try:
        campaign = NewsletterCampaign.objects.get(id=campaign_id)

        # Get subscribers based on filter
        if campaign.recipients_filter == 'active':
            subscribers = Subscriber.objects.filter(status='active')
        elif campaign.recipients_filter == 'all':
            subscribers = Subscriber.objects.filter(status__in=['active', 'unsubscribed'])
        else:
            # For custom, we'd need additional logic, but for now use active
            subscribers = Subscriber.objects.filter(status='active')

        recipient_emails = [sub.email for sub in subscribers]

        if not recipient_emails:
            return {"status": "no_recipients", "campaign_id": campaign_id}

        # Load email template
        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'newsletter', 'emails', 'newsletter.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'newsletter', 'emails', 'newsletter.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context({
            'subject': campaign.subject,
            'content': campaign.content,
            'campaign_id': campaign.id,
        }))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context({
            'subject': campaign.subject,
            'content': campaign.plain_text_content or campaign.content,
            'campaign_id': campaign.id,
        }))

        # Send email
        send_mail(
            subject=campaign.subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipient_emails,
            html_message=html_message,
            fail_silently=False,
        )

        # Update campaign stats
        campaign.total_sent = len(recipient_emails)
        campaign.save()

        return {"status": "success", "campaign_id": campaign_id, "sent_count": len(recipient_emails)}

    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except:
            return {"status": "failure", "campaign_id": campaign_id, "error": str(e)}