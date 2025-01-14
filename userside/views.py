
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect
from django.http import JsonResponse
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



CLIENT_ID =  4788 
CLIENT_SECRET = "6b33308f-47cb-4209-b5e3-e52a1cc12b34" #os.getenv("TRADOVATE_CLIENT_SECRET")
REDIRECT_URI = "https://test.matipro.in/callback"
AUTH_URL = "https://trader.tradovate.com/oauth"
TOKEN_URL = "https://live-api.tradovate.com/auth/oauthtoken"
URL = "https://demo.tradovateapi.com/v1"
BackEnd = 'http://test.matipro.in'
FrontEnd = 'http://predictive.quantifiedante.com'

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
    print(request.GET.get('broker_logout'))
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
        print(context)
    return Response(context)

def trade_execution(request):
    user_id = 4
    if user_id:
        user_instance = Userdata.objects.get(user_id=user_id)
        token_data = Access_Token.objects.get(user_id=user_instance)
    
    userpreference = User_Preference.objects.filter(user_id=user_instance)

    account_info = get_accounts(token_data.access_token)  # HTTP call
    print(account_info)
    current_account = {'acc_id':None, 'acc_name':None}
    for x in account_info:
        if userpreference:
           if x['id'] == int(userpreference[0].account):
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



@api_view(['POST','GET'])
def trading_view_signal_webhook_listener(request):
    user_id_from_url = 4
    user_id_from_webhook = request.GET.get('user_id')
    print('=================================signal got')
    user_instance = Userdata.objects.get(user_id=user_id_from_webhook)
    if user_instance.user_signal_on == True:
        if request.body:
            webhook_message = json.loads(request.body)

            print("Webhook message:", webhook_message)
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
            }
            symbol = webhook_message["ticker"]
            symbol = convert_ticker(symbol)
            order_price = None
            stopPrice=None
            action = {}
            if webhook_message["action"] == 'buy': 
                action.update({'action':'Buy'})
            else:

                action.update({'action':'Sell'})
            
            data = trade_execution(request)

            order_type = {}

            order_type.update({'order_type': 'Market'})

            order_data = place_order(data['access_token'],data['account_spec'],data['account_id'],action['action'], symbol, data['order_qty'], order_type['order_type'] ,data['is_automated'],order_price=None,stopPrice=None)
            print(order_data)
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'message':'outof body'})
    else:
        return JsonResponse({'message':'Trade is Not On, Please on Trade.'})


def broker_login(request):
    auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    context = {'auth_url':auth_url}
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
    user_id = 4
    if user_id:
        user_instance = Userdata.objects.get(user_id = user_id)
    code = request.GET.get("code")
    renew_access_token = request.GET.get('renew_access_token')

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


   
    
   

    






        
       


