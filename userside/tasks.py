from celery import shared_task
from time import sleep
from django.core.mail import send_mail  
from django.conf import settings
from userside.models import *
import requests
from django.utils import timezone
from datetime import timedelta,datetime

@shared_task
def sub():
    subject = "Greetings"  
    msg     = "Congratulations for your success"  
    to      = "prvnbharti@gmail.com"
    fromm = settings.EMAIL_HOST_USER
    print('hellooooooooooooo')
    send_mail(subject, msg, fromm, [to])  
    return 1

@shared_task
def renew_access_token():
    for x in Userdata.objects.filter(user_signal_on=True):
        token_avail = Access_Token.objects.filter(user_id=x).count()
        if token_avail > 0:
            token_data = Access_Token.objects.get(user_id=x)
            url = "https://live.tradovateapi.com/v1/auth/renewAccessToken"

            headers = {
                'Authorization': f"Bearer {token_data.access_token}"
            }
            current_time = timezone.now()  # Set to the specified date
            
            access_token_data = Access_Token.objects.get(user_id = x)
            expiration_time = access_token_data.expiry_at

            if current_time < expiration_time:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                renewed_token_data = response.json()
                renewed_token = renewed_token_data['accessToken']
                expiration_time = current_time + timedelta(seconds=3600)
                update_access_token = Access_Token.objects.get(user_id = x)
                update_access_token.access_token = renewed_token
                update_access_token.expiry_at = expiration_time
                update_access_token.save()
    return 1


# celery -A quantifiedante worker --loglevel=info
# elery -A quantifiedante beat --loglevel=info
