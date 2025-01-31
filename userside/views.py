
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
import json
import random
import json
from django.core.mail import send_mail
import requests
from datetime import timedelta,datetime
from userside.models import *
from django.utils import timezone
from userside.tradovate_functionalities import *
from quantifiedante.celery import add
from userside.tasks import *
from django.shortcuts import get_object_or_404
from userside.weekly_calender import *
import asyncio
from userside.bracket_order import *
import time
from asgiref.sync import async_to_sync

import logging
logger_trades = logging.getLogger('django.success_failure_trades')



CLIENT_ID =  4788 
CLIENT_ID2 =  4745 
# localhost_backend_clientid = 47
CLIENT_SECRET = "6b33308f-47cb-4209-b5e3-e52a1cc12b34" #os.getenv("TRADOVATE_CLIENT_SECRET")
REDIRECT_URI = "https://predictiveapi.quantifiedante.com/callback"
# REDIRECT_URI = "http://localhost:8000/callback"
REDIRECT_URI2 = "http://localhost:3000"
AUTH_URL = "https://trader.tradovate.com/oauth"
TOKEN_URL = "https://live-api.tradovate.com/auth/oauthtoken"
URL = "https://demo.tradovateapi.com/v1"
BackEnd = 'https://predictiveapi.quantifiedante.com'
# BackEnd = 'http://127.0.0.1:8000'
FrontEnd = 'http://predictive.quantifiedante.com'
# FrontEnd = 'http://localhost:3000'
    # auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"


def utc_to_newtork(datee):
    new_york_tz = pytz.timezone('America/New_York')
    utc_datetime = datee.replace(tzinfo=pytz.utc)
    new_york_time = utc_datetime.astimezone(new_york_tz)
    return new_york_time
  



def check_calender_data(request):
    current_time = timezone.now()
    print("=========================",current_time)
    cal_data = calender_data.objects.filter(Event_Start__lt=current_time, Event_End__gt=current_time)
    current_event = {}
    for x in cal_data:
        print('cal datttta',x)
        current_event.update({'event_name':x.title,'impact':x.impact,'Event_End': utc_to_newtork(x.Event_End).strftime("%Y-%m-%d %H:%M:%S"),'endtime': utc_to_newtork(x.Event_End).strftime("%H:%M")})
    
    cal_data_count = calender_data.objects.filter(Event_Start__lt=current_time, Event_End__gt=current_time).count()
    if cal_data_count>0:
        current_event.update({'events':cal_data_count})
        return current_event
    else:
        current_event.update({'events':cal_data_count})
        return current_event
   


# Create a new user account
@csrf_exempt
def user_register(request):
    """
    API endpoint to register a new user.
    Accepts POST requests with required fields: user_name, user_email, user_password.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    required_fields = ['user_name', 'user_email', 'user_password']
    for field in required_fields:
        if field not in data:
            return JsonResponse({'error': f'{field} is required'}, status=400)

    user_name = data.get('user_name')
    user_email = data.get('user_email')
    user_password = data.get('user_password')
    user_contact = data.get('user_contact', None)
    user_dob = data.get('user_dob', None)
    user_gender = data.get('user_gender', None)
    user_address = data.get('user_address', None)
    
    # Check if email already exists
    if Userdata.objects.filter(user_email=user_email).exists():
        return JsonResponse({'error': 'Email already registered'}, status=400)

    # Create the user
    try:
        user = Userdata.objects.create(
            user_name=user_name,
            user_email=user_email,
            user_password=user_password,
            user_contact=user_contact,
            user_dob=user_dob,
            user_gender=user_gender,
            user_address=user_address
        )

        abcd =  '{}/trading_view_signal_webhook_listener?user_id={}'.format(FrontEnd,user.user_id)
        user.user_tradingview_url = abcd
        user.save()
        return JsonResponse({
            'message': 'User registered successfully',
            'user_id': user.user_id,
            'user_email': user.user_email,
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def user_login(request):
    if request.method == 'POST':
        email = request.data.get('user_email').lower()
        password = request.data.get('user_password').lower()
        val = Userdata.objects.filter(user_email=email ,user_password=password).count()
        print(val)

        if val==1:
            Data = Userdata.objects.get(user_email=email , user_password=password)
            return JsonResponse({
                'message': 'Login successful',
                'user_id': Data.user_id,
                'user_name': Data.user_name,
                'user_email': Data.user_email,
            }, status=200)
        else:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)
    else:
        return JsonResponse({'error': 'Invalid email or password'}, status=401)

            



@csrf_exempt
def user_forgot_password(request):
    """
    API endpoint to handle forgot password.
    Accepts POST requests with JSON body containing the user's email.
    Sends a 6-digit OTP to the user's email and saves it in the database.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format or empty request body'}, status=400)

    # Ensure email is provided
    user_email = data.get('user_email')
    if not user_email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    try:
        # Check if user exists
        user = Userdata.objects.filter(user_email=user_email).first()
        if not user:
            return JsonResponse({'error': 'User with this email does not exist'}, status=404)

        # Generate a 6-digit OTP
        otp = f"{random.randint(100000, 999999)}"

        # Save OTP to the user's record
        user.user_otp = otp
        user.save()

        # Send email with the OTP
        subject = "Password Reset OTP"
        message = f"Hello {user.user_name},\n\nYour OTP for password reset is: {otp}\n\nPlease use this OTP to reset your password."
        from_email = "your_sender_email"
        recipient_list = [user_email]

        send_mail(subject, message, from_email, recipient_list)

        return JsonResponse({
            'message': 'OTP sent to your email',
            'otp': otp  # Include OTP in the response for testing purposes (remove in production)
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def user_change_password(request):
    """
    API endpoint to change the user's password.
    Accepts POST requests with JSON body containing user_email, user_otp, and new_password.
    The OTP must match the one previously sent to the user's email.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))  # Decode body to string before parsing
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format or empty request body'}, status=400)

    # Ensure required fields are provided
    required_fields = ['user_email', 'user_otp', 'new_password']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return JsonResponse({'error': f'Missing required fields: {", ".join(missing_fields)}'}, status=400)

    user_email = data.get('user_email')
    user_otp = data.get('user_otp')
    new_password = data.get('new_password')

    try:
        # Check if user exists
        user = Userdata.objects.filter(user_email=user_email).first()
        if not user:
            return JsonResponse({'error': 'User with this email does not exist'}, status=404)

        # Check if OTP is correct
        if user.user_otp != user_otp:
            return JsonResponse({'error': 'Invalid OTP'}, status=400)

        # Optionally, check OTP expiration (if you set an expiry time)
        # Here, we check if OTP was sent within the last 10 minutes
        # if user.otp_sent_time and (datetime.now() - user.otp_sent_time) > timedelta(minutes=10):
        #     return JsonResponse({'error': 'OTP expired'}, status=400)

        # Update the user's password
        user.user_password =new_password  
        user.save()

        # Clear the OTP after password change (optional)
        user.user_otp = None
        user.save()

        # Send email notification about password change
        subject = "Your Password has been Changed"
        message = f"Hello {user.user_name},\n\nYour password has been successfully changed. If you did not request this change, please contact support immediately."
        from_email = "your_sender_email"
        recipient_list = [user_email]

        send_mail(subject, message, from_email, recipient_list)

        return JsonResponse({'message': 'Password changed successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




@api_view(['GET'])
def home(request):
    user_id = request.GET.get('user_id')
    context ={}
    if user_id:
        user_instance = Userdata.objects.get(user_id=user_id)
        current_time = timezone.now()
        if request.GET.get('broker_logout') == '1':
            token_data = Access_Token.objects.get(user_id=user_instance)
            user_instance.user_signal_on = 0
            user_instance.save()
            token_data.delete()

        if Access_Token.objects.filter(user_id=user_instance, expiry_at__gt=current_time).exists():
            token_data = Access_Token.objects.get(user_id=user_instance)
            context.update({'token':token_data.access_token})
        user_data = {'user_id':user_instance.user_id, 'user_name':user_instance.user_name, 'user_email':user_instance.user_email,'user_passphrase':user_instance.user_passphrase,'user_tradingview_url':user_instance.user_tradingview_url,'user_signal_on':user_instance.user_signal_on}
        context.update({'userdata':user_data})
    
    # ==================calendar things=================
    current_time = timezone.now()
   
    calenderr = check_calender_data(request)
    if calenderr['events']>0:
        context.update({'calender_event':calenderr})
    return Response(context)

def trade_execution(request,user_id_from_webhook):
    user_id = user_id_from_webhook
    if user_id:
        user_instance = Userdata.objects.get(user_id=user_id)
        token_data = Access_Token.objects.get(user_id=user_instance)
    
    userpreference = User_Preference.objects.get(user_id=user_instance)

    account_info = get_accounts(token_data.access_token)  # HTTP call
    print("========================",account_info)
    current_account = {'acc_id':None, 'acc_name':None}
    for x in account_info:
        if userpreference:
           if x['id'] == int(userpreference.account):
               current_account.update({'acc_id':x['id'], 'acc_name':x['name']})
    
    account_spec = account_info[0]['name']
    account_id = account_info[0]['id']
    print(current_account)
    access_token = token_data.access_token
    
    prefrencess_data = User_Preference.objects.get(user_id=user_instance)
    order_qty = prefrencess_data.order_size
    order_typee = 'Market'
    order_type = prefrencess_data.account_type
   
    is_automated = True
    data = {'account_spec':current_account['acc_name'],'account_id':current_account['acc_id'],'access_token':access_token,'order_qty':order_qty,'order_type':order_typee,'is_automated':is_automated}
    return data


response_id = []
@api_view(['POST','GET'])
def trading_view_signal_webhook_listener(request):
    user_id_from_url = 1
    user_id_from_webhook = request.GET.get('user_id')
    current_time = timezone.now()
    for x in calender_data.objects.all():
        pass
    calenderr = check_calender_data(request)
    if calenderr['events']>0:
        return JsonResponse({'message':'Trading Halted: The current trading session is temporarily halted. It will be resume after 15 mins.'})
    user_instance = Userdata.objects.get(user_id=user_id_from_webhook)
    if user_instance.user_signal_on == True:
        if request.body:
            webhook_message = json.loads(request.body)
            user_passphrase_data = Userdata.objects.get(user_passphrase = webhook_message['passphrase'])

            if not user_passphrase_data:
                return redirect('/')

            trading_signal = {
                "user_id": user_id_from_url,
                "timestamp": webhook_message["time"],
                "ticker": webhook_message["ticker"],
                "action": webhook_message["action"],
                "tp1Line": webhook_message["tp1Line"],
                "tp2Line": webhook_message["tp2Line"],
                "tp3Line": webhook_message["tp3Line"],
                "slLine": webhook_message["slLine"],
                "entry_price": webhook_message["entry price"],
            }
            logger_trades.info("trading_signal =>{}".format(trading_signal))
            symbol = webhook_message["ticker"]
            symbol = convert_ticker(symbol)
            order_price = None
            stopPrice=None

            action = {}
            if webhook_message["action"] == 'buy': 
                action.update({'action':'Buy'})
            elif webhook_message["action"] == 'sell':
                action.update({'action':'Sell'})
            elif webhook_message["action"] == 'Tp1':
                action.update({'action':'Tp1'})
            else:
                action.update({'action':'Tp2'})
            
            data = trade_execution(request,user_id_from_webhook)

            user_prefre = User_Preference.objects.get(user_id__user_id = user_id_from_webhook)
            order_type = user_prefre.order_type

            
            print('===orderType{} and action:{}'.format(order_type,action['action']))
            if order_type == 'market_order':
                order_data = place_order(data['access_token'],data['account_spec'],data['account_id'],action['action'], symbol, data['order_qty'], 'Market' ,data['is_automated'],order_price=None,stopPrice=None)
                print(order_data)

            elif order_type == 'limit_order' and action['action'] == 'Buy':
                print('Checking....')
                order_data = place_order(data['access_token'], data['account_spec'], data['account_id'], "Buy",symbol, data['order_qty'], "Limit", True,order_price=float(trading_signal['entry_price']),stopPrice=None)
                print('===================order DATA==================',order_data)
                data['order_data'] = order_data

            elif order_type == 'limit_order' and action['action'] == 'Sell':
                order_data = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol,data['order_qty'], "Limit", True,order_price=float(trading_signal['entry_price']),stopPrice=None)
                print(order_data)


            elif order_type == 'stop_loss_limit_order' and action['action'] == 'Buy':
                position = get_position(data['access_token'])

                if position[0]['netPos'] > 0:
                    liquidate_position(data['access_token'], position[0]['accountId'], position[0]['contractId'],False,None)

                response_market = place_order(data['access_token'], data['account_spec'], data['account_id'], "Buy", symbol, data['order_qty'], "Market", True)
                response_oco = place_oco_order(data['access_token'], data['account_spec'], data['account_id'], symbol, "Sell", data['order_qty'],  float(trading_signal['slLine']), float(trading_signal['tp1Line']))
                print(f"Buy Order Response: {response_market}, {response_oco}")

            elif order_type == 'stop_loss_limit_order' and action['action'] == 'Sell':
                position = get_position(data['access_token'])

                if position[0]['netPos'] > 0:
                    liquidate_position(data['access_token'], position[0]['accountId'], position[0]['contractId'],False,None)
                    
                response_market = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, data['order_qty'], "Market", True)
                response_oco = place_oco_order(data['access_token'], data['account_spec'], data['account_id'], symbol, "Buy", data['order_qty'], float(trading_signal['slLine']), float(trading_signal['tp1Line']))
                print(f"Buy Order Response: {response_market}, {response_oco}")


            elif order_type == 'multiple_take_profit' and action['action'] == 'Buy':
                position = get_position(data['access_token'])

                if position[0]['netPos'] != 0:
                    liquidate_position(data['access_token'], position[0]['accountId'], position[0]['contractId'],False,None)

                time.sleep(0.40)

                response_entry =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Buy", symbol, 3, "Market", True)  # order qty = 3
                response_tp1 =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp1Line']))  # order qty = 1
                response_tp2 =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp2Line']))  # order qty = 1
                response_tp3 =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp3Line']))  # order qty = 1
                response_sl =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 3, "Stop", True, stopPrice=float(trading_signal['slLine']))  # order qty = 3
                create_mtpo = multiple_take_profit_orders.objects.create(user_id=user_instance,order_id=response_sl['orderId'])
                response_id.append(response_sl)
                print(f"Buy Order Response: {response_entry}, {response_tp1}, {response_tp2}, {response_tp3}, {response_sl}, {response_id}")

            elif order_type == 'multiple_take_profit' and action['action'] == 'Sell':
                position = get_position(data['access_token'])

                if position[0]['netPos'] != 0:
                    liquidate_position(data['access_token'], position[0]['accountId'], position[0]['contractId'],False,None)

                time.sleep(0.40)

                response_entry =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 3, "Market", True)  # order qty = 3
                response_tp1 =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Buy", symbol, 1, "Limit", True, order_price=float(trading_signal['tp1Line']))  # order qty = 1
                response_tp2 =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Buy", symbol, 1, "Limit", True, order_price=float(trading_signal['tp2Line']))  # order qty = 1
                response_tp3 =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Buy", symbol, 1, "Limit", True, order_price=float(trading_signal['tp3Line']))  # order qty = 1
                response_sl =  place_order(data['access_token'], data['account_spec'], data['account_id'], "Buy", symbol, 3, "Stop", True, stopPrice=float(trading_signal['slLine']))  # order qty = 3
                create_mtpo = multiple_take_profit_orders.objects.create(user_id=user_instance,order_id=response_sl['orderId'])
                response_id.append(response_sl)
                print(f"Buy Order Response: {response_entry}, {response_tp1}, {response_tp2}, {response_tp3}, {response_sl}, {response_id}")

            elif order_type == 'multiple_take_profit' and action['action'] == "Tp1":
                print('order_type ={} , action={}'.format(order_type,action['action']))
                order_id = multiple_take_profit_orders.objects.filter(user_id = user_instance).last()
                print(order_id.order_id)
                if order_id:
                    modify_sl1 = modify_order(data['access_token'], int(order_id.order_id), orderQty = 2, orderType = "Stop", stopPrice = float(trading_signal['slLine']))

            elif order_type == 'multiple_take_profit' and action['action'] == "Tp2":
                order_id = multiple_take_profit_orders.objects.filter(user_id = user_instance).last()
                print(order_id.order_id)
                if order_id:
                    modify_sl2 = modify_order(data['access_token'], int(order_id.order_id), orderQty=1, orderType="Stop", stopPrice=float(trading_signal['slLine']))

            elif order_type == 'Bracket_Order' and action['action'] == "Sell": 
                logger_trades.info("\n===================================== New Order =============================\n")
                tp1 = float(trading_signal['tp1Line'])
                entry_price = float(trading_signal['entry_price'])
                print("=========EntryPrice", entry_price)
                print("=========tp1", tp1)
                profitTarget = entry_price-tp1
                print('=============================',profitTarget)
                # float(trading_signal['slLine']
                paramss = {
                    "entryVersion": {
                        "orderQty": 3,
                        "orderType": "Market"
                    },
                    "brackets": [{
                        "qty": 3,
                        # "profitTarget": -1*profitTarget,
                        "stopLoss": 1*profitTarget,
                        "trailingStop": False,
                        "autoTrail": {
                            'stopLoss':20,
                            'trigger':20,
                            'freq':20
                        }
                    }]
                }
                print("=========",paramss)
                logger_trades.info("params => {}".format(paramss))

                position = get_position(data['access_token'])
                for x in position:
                    if x['accountId'] == data['account_id']:
                        if x['netPos'] != 0:
                            liquidate_position(data['access_token'], x['accountId'], x['contractId'],False,None)
                # asyncio.run(tradovate_bracketOrder_socket(paramss,data['access_token'],action['action'],data['account_id'], data['account_spec']))
                time.sleep(0.7)
                place_brc_order(paramss,data['access_token'],action['action'], data['account_id'], data['account_spec'], symbol)
            elif order_type == 'Bracket_Order' and action['action'] == "Buy":
                print("======entering")
                logger_trades.info("\n===================================== New Order =============================\n")
                tp1 = float(trading_signal['tp1Line'])
                entry_price = float(trading_signal['entry_price'])
                profitTarget = entry_price-tp1
                # float(trading_signal['slLine']
                print('profitt:{}========entry:{}========{}'.format(-1*profitTarget,entry_price,1*profitTarget))

                paramss = {
                    "entryVersion": {
                        "orderQty": 3,
                        "orderType": "Market"
                    },
                    "brackets": [{
                        "qty": 3,
                        # "profitTarget": -1*profitTarget,
                        "stopLoss": 1*profitTarget,
                        # "profitTarget": 25,
                        # "stopLoss": -25,
                        "trailingStop": False,
                        "autoTrail": {
                            'stopLoss':20,
                            'trigger':20,
                            'freq':20
                        }
                    }]
                }

                logger_trades.info("params => {}".format(paramss))

                print('params:',paramss)
                position = get_position(data['access_token'])
                for x in position:
                    if x['accountId'] == data['account_id']:
                        if x['netPos'] != 0:
                            liquidate_position(data['access_token'], x['accountId'], x['contractId'],False,None)
                
                # asyncio.run(tradovate_bracketOrder_socket(paramss,data['access_token'],action['action'], data['account_id'], data['account_spec']))
                time.sleep(0.7)
                place_brc_order(paramss,data['access_token'],action['action'], data['account_id'], data['account_spec'], symbol)
                
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'message':'outof body'})
    else:
        return JsonResponse({'message':'Trade is Not On, Please on Trade.'})    



def broker_login(request):
    auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    context = {'auth_url':auth_url}
    user_id = request.GET.get('user_id')
    return JsonResponse(context)


def trade_signal_update(request):
    user_id = request.GET.get('user_id')
    user_instance = Userdata.objects.get(user_id=user_id)
    
    if user_instance.user_signal_on == True:
        user_instance.user_signal_on = False
        print(user_instance.user_signal_on)
    elif user_instance.user_signal_on == False:
        user_instance.user_signal_on = True
        print(user_instance.user_signal_on)

    user_instance.save()
    return JsonResponse({'message':'your signal is {}'.format(user_instance.user_signal_on)})    


def callback(request):
    user_id=1
    if user_id:
        print("user id ====================",user_id)
        user_instance = Userdata.objects.get(user_id = user_id)
    code = request.GET.get("code")
    renew_access_token = request.GET.get('renew_access_token')
    print(code)
    if not code:
        print("not getting code")
    else:
        payload = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        response = requests.post(TOKEN_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()
   
        
        if "access_token" not in token_data:
            print("not getting token data")
        else:
            access_token = token_data['access_token']
            current_time = timezone.now()
            expiration_time = current_time + timedelta(seconds=3600)
            if Access_Token.objects.filter(user_id = user_instance).count() == 0:
                store_access_token = Access_Token.objects.create(user_id = user_instance, access_token = access_token, expiry_at = expiration_time)
                context = {'status':True,'message':'Login Successfull'}
                url = '{}'.format(FrontEnd)
                return redirect(url)
            else:
                update_access_token = Access_Token.objects.get(user_id = user_instance)
                update_access_token.access_token = access_token
                update_access_token.expiry_at = expiration_time
                update_access_token.save()
                context = {'status':True,'message':'Login Successfull'}
                url = '{}'.format(FrontEnd)
                return redirect(url)
    return JsonResponse({'message':'your signal is callback'})




@api_view(['GET'])
def tradovate_functionalities_data(request):
    # http://localhost:8000/tradovate_functionalities_data?tradovate_functionality=get_position&user_id=4
    user_id = request.GET.get('user_id')
    tradovate_functionality = request.GET.get('tradovate_functionality')

    if user_id:
        user_instance = Userdata.objects.get(user_id=user_id)
        token_data = Access_Token.objects.get(user_id=user_instance)

    if tradovate_functionality == 'account_info':
        account_info = get_accounts(token_data.access_token)  
        print(account_info)
        return JsonResponse(account_info, safe=False)
    
    elif tradovate_functionality == 'get_cash_balance':
        account_info = get_cash_balance(token_data.access_token) 
        print(account_info)
        return JsonResponse(account_info, safe=False)
    
    elif tradovate_functionality == 'get_position':
        positions = get_position(token_data.access_token) 
        data = {'positions':positions}
        return JsonResponse(data, safe=False)
    
    elif tradovate_functionality == 'get_order_history':
        order_history = get_order_history(token_data.access_token)  
        print(order_history)
        return JsonResponse(order_history, safe=False)
    
    elif tradovate_functionality == 'place_order':
        account_info = place_order(token_data.access_token)  
        print(account_info)
        return JsonResponse(account_info, safe=False)
    
    elif tradovate_functionality == 'place_oso_order':
        oso_order = place_oso_order(token_data.access_token)  
        print(oso_order)
        return JsonResponse(oso_order, safe=False)
    
    elif tradovate_functionality == 'place_oco_order':
        oco_order = place_oco_order(token_data.access_token)  
        print(oso_order)
        return JsonResponse(oco_order, safe=False)
        
    elif tradovate_functionality == 'cancel_order':
        cancelled_order = cancel_order(token_data.access_token)  
        print(cancelled_order)
        return JsonResponse(cancelled_order, safe=False)
    
    elif tradovate_functionality == 'liquidate_position':
        liquidated_position = liquidate_position(token_data.access_token)  
        print(liquidated_position)
        return JsonResponse(liquidated_position, safe=False)
    
    elif tradovate_functionality == 'modify_order':
        modified_order = modify_order(token_data.access_token)  
        print(modified_order)
        return JsonResponse(modified_order, safe=False)



def preferences(request):
    user_id = request.GET.get('user_id')
    context = {}
    accounts = []
    if user_id:
        user_instance = Userdata.objects.get(user_id=user_id)
        user_pref = User_Preference.objects.get(user_id__user_id=user_instance.user_id)
        user_pref = {'user_preference': user_pref.user_preference,'account_type': user_pref.account_type,'order_size':user_pref.order_size,'time_in_force':user_pref.time_in_force,'order_type':user_pref.order_type,'account':user_pref.account}
        token_data = get_object_or_404(Access_Token,user_id=user_instance)
        account_info = get_accounts(token_data.access_token) 
        context.update({'accounts':account_info,'user_pref':user_pref})    
    return JsonResponse(context, safe=False)


@api_view(['POST','GET'])
def user_preference_insert_update(request):
    user_id = request.GET.get('user_id')
    preference_id = request.data.get('user_preference', None)
    print(preference_id)
    user_instance = Userdata.objects.get(user_id=user_id)
    
    if preference_id:
        try:
            # Update existing preference
            preference = User_Preference.objects.get(user_preference=preference_id)
            preference.user_id = user_instance
            preference.account_type = request.data.get('account_type', preference.account_type)
            preference.order_size = request.data.get('order_size', preference.order_size)
            preference.time_in_force = request.data.get('time_in_force', preference.time_in_force)
            preference.order_type = request.data.get('order_type', preference.order_type)
            preference.account = request.data.get('account', preference.account)
            preference.save()
            return Response({"message": "Preference updated successfully."}, status=status.HTTP_200_OK)
        except User_Preference.DoesNotExist:
            return Response({"error": "Preference not found."}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Create new preference
        new_preference = User_Preference(
            user_id=user_instance,
            account_type=request.data.get('account_type'),
            order_size=request.data.get('order_size'),
            time_in_force=request.data.get('time_in_force'),
            order_type=request.data.get('order_type'),
            account=request.data.get('account')
        )
        new_preference.save()
        return JsonResponse({"message": "Preference created successfully."}, status=status.HTTP_201_CREATED)

from time import strftime
import pytz
from datetime import datetime   

@api_view(['GET'])
def show_current_calender(request):
    data = calender_data.objects.all().values('title', 'country', 'impact', 'Datetimee')

    for x in data:
        # Convert the 'Datetimee' field from string to datetime if necessary
        # Assuming 'Datetimee' is a naive datetime
        new_york_time = utc_to_newtork(x['Datetimee'])
        x['Datetimee'] = new_york_time.strftime("%Y-%m-%d %H:%M:%S")  # Format the datetime

    context = {'data': list(data)}  # Convert QuerySet to list for serialization
    return Response(context)



    


@api_view(['GET'])
def liquidate_positions(request):
    user_id = request.GET.get('user_id')
    if user_id:
        user_instance = Userdata.objects.get(user_id=user_id)
        token_data = Access_Token.objects.get(user_id=user_instance)
        position = get_position(token_data.access_token)

        userpreference = User_Preference.objects.get(user_id=user_instance)
        for x in position:
            if x['accountId'] == userpreference.account:
                if x['netPos'] != 0:
                    liquidate_position(token_data.access_token, x['accountId'], x['contractId'],False,None)
        return Response({'message':'Success','status':True})
    return Response({'message':'No Position','status':False})
    



        
       


