 # take stop_loss limit order
            action_oco = action['action']
            Position_Data= get_position(Position_Data['access_token'])
            response_sl_list = []
            if order_type == "stop_loss_limit_order":
                if Position_Data[0]['netPos'] > 0:
                    liquidated_position = liquidate_position(data['access_token'], Position_Data[0]["accountId"], Position_Data[0]["contractId"], False)
                
                if action_oco == 'Buy':
                    response_market = place_order(data['access_token'], data['account_spec'],data['account_id'], "Buy", symbol, data['order_qty'], "Market", True)
                    response_oco = place_oco_order(URL, data['account_spec'],data['account_id'], data['access_token'], symbol, "Sell", data['order_qty'],  float(trading_signal['slLine']), float(trading_signal['tp1Line']))
                else:
                    response_market = place_order(data['access_token'], data['account_spec'],data['account_id'], "Sell", symbol, data['order_qty'], "Market", True)
                    response_oco = place_oco_order(URL, data['account_spec'],data['account_id'], data['access_token'], symbol, "Buy", data['order_qty'],  float(trading_signal['slLine']), float(trading_signal['tp1Line']))

            elif order_type == "multiple_take_profit":
                if action_oco == 'Buy':
                    response_entry = place_order(data['access_token'], data['account_spec'],data['account_id'], "Buy", symbol, 3, "Market", True)  # order qty = 3
                    response_tp1 = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp1Line']))  # order qty = 1
                    response_tp2 = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp2Line']))  # order qty = 1
                    response_tp3 = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp3Line']))  # order qty = 1
                    response_sl = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 3, "Stop", True, stopPrice=float(trading_signal['slLine']))  # order qty = 3
                    response_sl_list.append(response_sl)
                elif action_oco == 'Sell':
                    response_entry = place_order(data['access_token'], data['account_spec'],data['account_id'], "Buy", symbol, 3, "Market", True)  # order qty = 3
                    response_tp1 = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp1Line']))  # order qty = 1
                    response_tp2 = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp2Line']))  # order qty = 1
                    response_tp3 = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 1, "Limit", True, order_price=float(trading_signal['tp3Line']))  # order qty = 1
                    response_sl = place_order(data['access_token'], data['account_spec'], data['account_id'], "Sell", symbol, 3, "Stop", True, stopPrice=float(trading_signal['slLine']))  # order qty = 3
                    response_sl_list.append(response_sl)
           
        
                elif action_oco == "Tp1":
                    modify_sl1 = modify_order(data['access_token'], response_sl_list['orderId'], orderQty=2, orderType="Stop", stopPrice=float(trading_signal['slLine']))
                    # response_id.clear()
                    # response_id.append(response_sl)

                elif action_oco == "Tp2":
                    modify_sl2 = modify_order(data['access_token'], response_sl_list['orderId']['orderId'], orderQty=1, orderType="Stop", stopPrice=float(trading_signal['slLine']))
                    # response_id.clear()
        
        # elif action == "Sl Hit":
        #     liquidation_resp = await liquidate_active_pos(accessToken)
            # print(order_data)