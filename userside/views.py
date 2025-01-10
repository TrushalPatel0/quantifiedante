from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import User
import json
import random
import json
from django.core.mail import send_mail

CLIENT_ID =  4788 
CLIENT_SECRET = "6b33308f-47cb-4209-b5e3-e52a1cc12b34" #os.getenv("TRADOVATE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"
AUTH_URL = "https://trader.tradovate.com/oauth"
TOKEN_URL = "https://live-api.tradovate.com/auth/oauthtoken"

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
    return render(request, 'index.html')


@csrf_exempt
def trading_view_signal_webhook_listener(request):
    user_id_from_url = '6762e68e7894a01d32c51a28'

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
        print("====================",trading_signal)
        
    return render(request, 'index.html')


def broker_login(request):
    auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return redirect(auth_url)


def callback(request):
    user_id = '6762e68e7894a01d32c51a28'
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
        print(token_data)
        
        if "access_token" not in token_data:
            print("not getting token data")
        else:
            access_token = token_data['access_token']
            print(access_token)

    if renew_access_token:
        url = "https://live.tradovateapi.com/v1/auth/renewAccessToken"

        headers = {
            'Authorization': f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        renewed_token = response.json()

    return render(request, 'index.html')

    



# def refresh_access_token(access_token):


        




# def brokerLogin():

#     form = brokerCredentialForm()
#     broker_type = request.args.get("broker", "alpaca")

#     # Handle GET request for Tradovate OAuth redirect
#     if request.method == "GET" and broker_type == "tradovate":
#         user_id = session.get("user_id")
#         if not user_id:
#             raise ValueError("User session not found. Please log in again.")

#         # Remove existing broker credentials for the user
#         broker_credentials.delete_many({"user_id": user_id})

#         user_id = session.get("user_id")

#         # Save only the user_id and broker type without tokens
#         broker_credentials.insert_one(
#             {
#                 "user_id": user_id,
#                 "broker": broker_type,
#             }
#         )

#         auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
#         return redirect(auth_url)

#     elif request.method == "POST":
#         try:
#             user_id = session.get("user_id")
#             if not user_id:
#                 raise ValueError("User session not found. Please log in again.")

#             # Remove existing broker credentials for the user
#             broker_credentials.delete_many({"user_id": user_id})

#             if broker_type == "alpaca":
#                 api_key = request.form.get("api_key")
#                 api_secret = request.form.get("api_secret")

#                 # Validate Alpaca credentials
#                 try:
#                     trade_client = TradingClient(
#                         api_key, api_secret, paper=True, url_override=None
#                     )
#                     trade_client.get_account()  # Throws APIError if credentials are invalid
#                 except APIError:
#                     flash(
#                         "Alpaca login failed, Please Enter Correct Credentials",
#                         "danger",
#                     )
#                     return redirect(url_for("broker.brokerLogin", broker="alpaca"))

#                 encrypted_api_key = encrypt_data(api_key)
#                 encrypted_api_secret = encrypt_data(api_secret)

#                 access_token_database.insert_one(
#                     {
#                         "user_id": user_id,
#                         "broker": broker_type,
#                         "api_key": encrypted_api_key,
#                         "api_secret": encrypted_api_secret,
#                     }
#                 )
#                 flash("Alpaca credentials saved successfully!", "success")

#             elif broker_type == "tradovate":

#                 flash("Tradovate broker type saved successfully!", "success")

#             return redirect(url_for("main_route.index"))

#         except ValueError as ve:
#             flash(str(ve), "warning")
#             return redirect(url_for("broker.brokerLogin", broker=broker_type))

#         except Exception as e:
#             flash("An unexpected error occurred. Please try again.", "danger")
#             return redirect(url_for("broker.brokerLogin", broker=broker_type))

#     return render_template("broker_login.html", form=form, broker=broker_type)




        
       


