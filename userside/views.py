import aiohttp
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import User
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

CLIENT_ID =  4788 
CLIENT_SECRET = "6b33308f-47cb-4209-b5e3-e52a1cc12b34" #os.getenv("TRADOVATE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"
AUTH_URL = "https://trader.tradovate.com/oauth"
TOKEN_URL = "https://live-api.tradovate.com/auth/oauthtoken"
URL = "https://demo.tradovateapi.com/v1"


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
    if User.objects.filter(user_email=user_email).exists():
        return JsonResponse({'error': 'Email already registered'}, status=400)

    # Create the user
    try:
        user = User.objects.create(
            user_name=user_name,
            user_email=user_email,
            user_password=user_password,
            user_contact=user_contact,
            user_dob=user_dob,
            user_gender=user_gender,
            user_address=user_address
        )
        return JsonResponse({
            'message': 'User registered successfully',
            'user_id': user.user_id,
            'user_email': user.user_email,
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def user_login(request):
    """
    API endpoint to log in a user.
    Accepts POST requests with JSON body containing required fields: user_email and user_password.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))  # Decode body to string before parsing
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format or empty request body'}, status=400)

    # Ensure required fields are present
    required_fields = ['user_email', 'user_password']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return JsonResponse({'error': f'Missing required fields: {", ".join(missing_fields)}'}, status=400)

    # Extract fields
    user_email = data.get('user_email')
    user_password = data.get('user_password')

    try:
        # Check if user exists
        user = User.objects.filter(user_email=user_email).first()
        if not user:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

        # Verify password (no hashing, plain text comparison)
        if user.user_password != user_password:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

        # Login successful, return user details
        return JsonResponse({
            'message': 'Login successful',
            'user_id': user.user_id,
            'user_name': user.user_name,
            'user_email': user.user_email,
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
        user = User.objects.filter(user_email=user_email).first()
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
        user = User.objects.filter(user_email=user_email).first()
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

# Home view
def home(request):
    print("Hello, world!")
    # result2 = sub.delay()
    # print(result2)
    return render(request, 'index.html')




def trade_execution(request):
    user_id = 1
    if user_id:
        user_instance = User.objects.get(user_id=user_id)
        token_data = Access_Token.objects.get(user_id=user_instance)
    
    account_info = get_accounts(token_data.access_token)  # HTTP call
   
    account_spec = account_info[0]['name']
    account_id = account_info[0]['id']

    access_token = token_data.access_token
    
    prefrencess_data = User_Preference.objects.get(user_id=user_instance)
    order_qty = prefrencess_data.order_size
    order_typee = 'Market'
    order_type = prefrencess_data.account_type
    # if order_type == 'market_order':
    #     order_typee = 'Market'
    # elif order_type == 'limit_order':
    #     order_typee = 'Limit'
    # elif order_type == 'stop_loss_limit_order':
    #     order_typee = 'Market'
    # elif order_type == 'market_order':
    #     order_typee = 'Market'
    is_automated = True
    data = {'account_spec':account_spec,'account_id':account_id,'access_token':access_token,'order_qty':order_qty,'order_type':order_typee,'is_automated':is_automated}
    return data



@csrf_exempt
def trading_view_signal_webhook_listener(request):
    user_id_from_url = 1
    user_id_from_webhook = request.GET.get('user_id')
    user_instance = User.objects.get(user_id=user_id_from_webhook)
    if user_instance == True:
        print(user_id_from_webhook)
        if request.body:
            webhook_message = json.loads(request.body)

            print("Webhook message:", webhook_message)
            user_passphrase_data = User.objects.get(user_passphrase = webhook_message['passphrase'])

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
            elif webhook_message["action"] == 'sell':
                action.update({'action':'Sell'})
            
            data = trade_execution(request)

            order_type = {}

            if order_type == "market_order":
                order_type.update({'order_type': 'market_order'})

            elif order_type == "stop_loss_limit_order":
                order_type.update({'order_type': 'stop_loss_limit_order'})

            elif order_type == "multiple_take_profit":
                order_type.update({'order_type': 'multiple_take_profit'})


            order_data = place_order(data['access_token'],data['account_spec'],data['account_id'],action['action'], symbol, data['order_qty'], order_type['order_type'] ,data['is_automated'],order_price=None,stopPrice=None)

        
            # take stop_loss limit order
            action_oco = action['action']
            data = get_position(data['access_token'])
            if data[0]['netPos'] > 0:
                positions = get_position(data['access_token'])
                liquidated_position = liquidate_position(data['access_token'], positions[0]["accountId"], positions[0]["contractId"], False)
            
            if action_oco == 'Buy':
                response_market = place_order(data['access_token'], data['account_spec'],data['account_id'], "Buy", symbol, data['order_qty'], "Market", True)
                response_oco = place_oco_order(URL, data['account_spec'],data['account_id'], data['access_token'], symbol, "Sell", data['order_qty'],  float(trading_signal['slLine']), float(trading_signal['slLine']))
            else:
                response_market = place_order(data['access_token'], data['account_spec'],data['account_id'], "Sell", symbol, data['order_qty'], "Market", True)
                response_oco = place_oco_order(URL, data['account_spec'],data['account_id'], data['access_token'], symbol, "Buy", data['order_qty'],  float(sl), float(tp1))




            # if order_type == "multiple_take_profit":
                # response_entry = place_order(data['access_token'], ,data['account_spec'],data['account_id'], "Buy", symbol, 3, "Market", True)  # order qty = 3
                # response_tp1 = place_order(accessToken, account_spec, account_id, "Sell", symbol, 1, "Limit", True, order_price=float(tp1))  # order qty = 1
                # response_tp2 = place_order(accessToken, account_spec, account_id, "Sell", symbol, 1, "Limit", True, order_price=float(tp2))  # order qty = 1
                # response_tp3 = place_order(accessToken, account_spec, account_id, "Sell", symbol, 1, "Limit", True, order_price=float(tp3))  # order qty = 1
                # response_sl = place_order(accessToken, account_spec, account_id, "Sell", symbol, 3, "Stop", True, stopPrice=float(sl))  # order qty = 3
            
            
            
            
            # print(order_data)
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'message':'Trade is Not On, Please on Trade.'})


def broker_login(request):
    auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return redirect(auth_url)


def trade_signal_update(request):
    user_id = request.GET.get('user_id')
    user_instance = User.objects.get(user_id=user_id)
    
    if user_instance.user_signal_on == True:
        user_instance.user_signal_on = False
        print(user_instance.user_signal_on)
    elif user_instance.user_signal_on == False:
        user_instance.user_signal_on = True
        print(user_instance.user_signal_on)

    user_instance.save()
    return JsonResponse({'message':'your signal is {}'.format(user_instance.user_signal_on)})    


def callback(request):
    user_id = 1
    if user_id:
        user_instance = User.objects.get(user_id = user_id)
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
            if Access_Token.objects.filter(user_id = user_instance).count() < 0:
                store_access_token = Access_Token.objects.create(user_id = user_instance, access_token = access_token, expiry_at = expiration_time)
            else:
                update_access_token = Access_Token.objects.get(user_id = user_instance)
                update_access_token.access_token = access_token
                update_access_token.expiry_at = expiration_time
                update_access_token.save()

    return render(request, 'index.html')

def tradovate_functionalities_data(request):
    user_id = 1  # This would typically come from the request or authentication
    # tradovate_functionality = request.GET.get('tradovate_functionality')
    tradovate_functionality = 'account_info'


    if user_id:
        user_instance = User.objects.get(user_id=user_id)
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
        print(positions)
        return JsonResponse(positions, safe=False)
    
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




   
    
   

    






        
       


