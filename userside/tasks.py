from celery import shared_task
from time import sleep
from django.core.mail import send_mail  
from django.conf import settings
from userside.models import *
import requests
from django.utils import timezone
from datetime import timedelta,datetime
from userside.weekly_calender import *
from userside.tradovate_functionalities import *

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
    for x in Userdata.objects.filter():
        token_avail = Access_Token.objects.filter(user_id=x).count()
        if token_avail > 0:
            token_data = Access_Token.objects.get(user_id=x)
            url = "https://live.tradovateapi.com/v1/auth/renewAccessToken"

            headers = {
                'Authorization': f"Bearer {token_data.access_token}"
            }
            current_time = timezone.now()  # Set to the specified date

            expiration_time = token_data.expiry_at

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



# ===================================setup calendar things======================================================


    
@shared_task
def get_store_calender_data():
    calender_dataa = process_calendar_data()
    print(calender_dataa)
    print(len(calender_dataa['Datetime']))
    print(calender_dataa['Datetime'])
    calender_data.objects.all().delete()
    for x in range(0,len(calender_dataa['Datetime'])):
        calender_data.objects.create(Datetimee=list(calender_dataa['Datetime'])[x],Event_Start=list(calender_dataa['EventStart'])[x],Event_End=list(calender_dataa['EventEnd'])[x],title=list(calender_dataa['title'])[x],country=list(calender_dataa['country'])[x],impact=list(calender_dataa['impact'])[x])
    context = {'message':'success'}
# ===================================setup calendar things======================================================


@shared_task
def on_event_end_trade():
    current_time = timezone.now()
    cal_data_count = calender_data.objects.filter(Event_Start__lt=current_time, Event_End__gt=current_time).count()
    if cal_data_count>0:
        access_tokenn = Access_Token.objects.all()
        for x in access_tokenn:
            if current_time < x.expiry_at:
                position = get_position(x.access_token)
                if position[0]['netPos'] != 0:
                    liquidate_position(x.access_token, position[0]['accountId'], position[0]['contractId'],False,None)

    






# celery -A quantifiedante worker --loglevel=info
# celery -A quantifiedante beat --loglevel=info
# supervisorctl status
# supervisorctl restart all


