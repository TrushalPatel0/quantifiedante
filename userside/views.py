from django.shortcuts import render,redirect
from datetime import timedelta,datetime
import json
import requests
from userside.models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
import os

CLIENT_ID =  4788 
CLIENT_SECRET = "6b33308f-47cb-4209-b5e3-e52a1cc12b34" #os.getenv("TRADOVATE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"
AUTH_URL = "https://trader.tradovate.com/oauth"
TOKEN_URL = "https://live-api.tradovate.com/auth/oauthtoken"


# create new account
# user login
# user password change


def home(request):
    print("hello world")
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




        
       


