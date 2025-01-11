def monitor_and_trade(user_id, access_token):
        credentials = get_broker_credentials(user_id)
        user_preferences = userPreferenceData.find_one({"user_id": user_id})
        if user_preferences:
            order_size = user_preferences.get("order_size")
            order_type = user_preferences.get("order_type")

        # Check for ongoing or imminent economic events
        events = list(get_ongoing_events())
        if events:
            print("Trading paused due to economic events:", events)
            time.sleep(60)  # Pause for 1 minute before rechecking
            continue

        signals = list(
            trading_signals.find({"user_id": user_id}).sort([("_id", -1)]).limit(10)
        )
        broker_type = credentials.get("broker")

        if broker_type == "tradovate":
            for signal in signals:
                signal_id = signal["_id"]
                symbol = convert_ticker(signal["ticker"])
                action = signal["action"]
                tp1_line = signal["tp1Line"]
                tp2_line = signal["tp2Line"]
                tp3_line = signal["tp3Line"]
                sl_line = signal["slLine"]

                if signal_id in processed_signals_store:
                    continue

                trade_data = {
                    "symbol": symbol,
                    "action": action,
                    "order_size": order_size,
                    "tp1_line": tp1_line,
                    "tp2_line": tp2_line,
                    "tp3_line": tp3_line,
                    "sl_line": sl_line,
                }

                print("this is the trade data ", trade_data)
                asyncio.run(
                    execute_tv_trade(
                        access_token,
                        action,
                        symbol,
                        user_id,
                        tp1_line,
                        tp2_line,
                        tp3_line,
                        sl_line,
                    )
                )

                exe_trade.update_one(
                    {"user_id": user_id, "signal_id": signal_id},
                    {"$set": {"exeTrade": trade_data, "processed": True}},
                    upsert=True,
                )

                processed_signals_store.add(signal_id)
                trading_signals.delete_one({"_id": signal["_id"]})

                orders = asyncio.run(get_order_details(access_token))

                if orders:
                    for order in orders:
                        order_data = {
                            "orderId": order["orderId"],
                            "price": order["price"],
                            "action": order["action"],
                            "qty": order["qty"],
                            "timestamp": order["timestamp"],
                            "contractId": order["contractId"],
                        }

                        order_history_collection.update_one(
                            {"user_id": user_id, "orderId": order["orderId"]},
                            {"$setOnInsert": order_data},
                            upsert=True,
                        )

            asyncio.run(asyncio.sleep(1))

        elif broker_type == "alpaca":
            current_positions = {}
            for signal in signals:
                signal_id = signal["_id"]
                if signal_id in processed_signals_store:
                    continue

                

                processed_signals_store.add(signal_id)
                trading_signals.delete_one({"_id": signal["_id"]})

            asyncio.run(asyncio.sleep(1))