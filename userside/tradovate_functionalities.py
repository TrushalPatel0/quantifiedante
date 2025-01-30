import requests
import json

URL = "https://demo.tradovateapi.com/v1"

# Convert tradingview ticker name to tradovate ticker name format 
def convert_ticker(tradingview_ticker):
    if len(tradingview_ticker) >= 4 and tradingview_ticker[-4:].isdigit():
        year = tradingview_ticker[-4:]
        last_digit_of_year = year[-1]
        broker_ticker = tradingview_ticker[:-4] + last_digit_of_year
        return broker_ticker
    else:
        return tradingview_ticker

def get_accounts(access_token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(f"{URL}/account/list", headers=headers)
    response.raise_for_status()
    return response.json()


def get_cash_balance(access_token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(f"{URL}/cashBalance/list", headers=headers)
    response.raise_for_status()
    return response.json()



def get_position(access_token):

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    
    response = requests.get(f"{URL}/position/list", headers=headers)
    return response.json()



def get_order_history(access_token):
    headers={'Authorization': f"Bearer {access_token}"} 
    response = requests.get(f"{URL}/fill/list", headers=headers)
    return response.json()


def place_order(access_token,account_spec,account_id,action,symbol,order_qty,order_type,is_automated,order_price=None,stopPrice=None):
    body = {
        "accountSpec": account_spec,
        "accountId": account_id,
        "action": action,
        "symbol": symbol,
        "orderQty": order_qty,
        "orderType": order_type,
        "price": order_price,
        "stopPrice": stopPrice,
        "isAutomated": is_automated,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    print(f"Placing order with payload: {json.dumps(body)}") 

    response = requests.post(f"{URL}/order/placeorder", headers=headers, json=body)
    print("Response Body:", response.text)
    response.raise_for_status() 
    return response.json()






def place_brc_order(paramss,access_token,action, account_id, account_spec,symbol):

    params = {
            "entryVersion": {
                "orderQty": 1,
                "orderType": "Market"
            },
            "brackets": [{
                "qty": 1,
                "profitTarget": -30,
                "stopLoss": 15,
                "trailingStop": False
            }]
        }

    body = {
            "accountId": account_id,
            "accountSpec": account_spec,
            "symbol": "MNQH5",
            "action": action,
            "orderStrategyTypeId": 2,  # 2 is 'multibracket', we currently only offer this strategy but more may exist in the future.
            "params": json.dumps(paramss)
        }


    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    print(f"Placing order with payload: {json.dumps(body)}") 

    response = requests.post(f"https://demo.tradovateapi.com/v1/orderStrategy/startorderstrategy", headers=headers, json=body)
    print("Response Body:", response.text)
    response.raise_for_status() 
    return response.json()

def place_oco_order(access_token, account_spec, account_id, symbol, action, order_qty, stop_price, limit_price):
    print('Enter in oco')
    limit = {"action": action, "orderType": "Stop", "stopPrice": stop_price}
    oco = {
        "accountSpec": account_spec,
        "accountId": account_id,
        "action": action,
        "symbol": symbol,
        "orderQty": order_qty,
        "orderType": "Limit",
        "price": limit_price,
        "isAutomated": True,
        "other": limit,
    }
    print(oco)
    oco_json = json.dumps(oco)
    print(oco_json)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    print(f"Placing order with payload: {json.dumps(oco)}") 
    response = requests.post(f"{URL}/order/placeoco", headers=headers, data=oco_json)
    print("Response Body:", response.text)
    response.raise_for_status() 
    return response.json()

def place_oso_order(access_token,account_spec,account_id,action,symbol,order_qty,order_type,is_automated,order_price=None,oso=None):
    body = {
        "accountSpec": account_spec,
        "accountId": account_id,
        "action": action,
        "symbol": symbol,
        "orderQty": order_qty,
        "orderType": order_type,
        "price": order_price,
        "isAutomated": is_automated,
        "bracket1": oso,
    }

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.get(f"{URL}/order/placeOSO", json=body, headers=headers)
    print("Response Body:", response.text)
    return response.json()



def cancel_order(access_token,order_id,cl_ord_id=None,activation_time=None,custom_tag50=None,is_automated=False):
    body = {
        "orderId": order_id,
        "clOrdId": cl_ord_id,
        "activationTime": activation_time,
        "customTag50": custom_tag50,
        "isAutomated": is_automated,
    }

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.get(f"{URL}/order/cancelorder", json=body, headers=headers)
    return response.json()



def liquidate_position(access_token, account_id, contract_id, admin, custom_tag50=None):
    body = {
        "accountId": account_id,
        "contractId": contract_id,
        "admin": admin,
        "customTag50": custom_tag50,
    }

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(f"{URL}/order/liquidateposition", json=body, headers=headers)
    return response.json()


# def liquidate_position(accessToken):

#     account_info = (accessToken)
#     positions = get_position(accessToken) 

#     if not account_info:
#         return {"status": "error", "message": "No active positions available"}
    
#     liquidate_response = liquidate_position(
#         accessToken,
#         account_info[0]["accountId"],
#         account_info[0]["contractId"],
#         False,
#     )
#     return liquidate_response


def modify_order(access_token, orderId, orderQty=None, orderType=None, price=None, stopPrice=None):
    print('==================we are modifing error')
    body = {
            "orderId": orderId,
            "orderQty": orderQty,
            "orderType": orderType,
            "price": price,
            "stopPrice": stopPrice,
            "isAutomated": True
          }
    print("============body=======",body)

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }    
    response = requests.post(f"{URL}/order/modifyorder", json=body, headers=headers)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")  
    return response.json()






