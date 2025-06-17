def SMAtrading_conditions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade):
    #skip NaN rows
    if np.isnan(last_SMA_50) or np.isnan(last_SMA_200) or np.isnan(last_RSI):
                    return "hold", None
            #if buy conditions are met, buy and add a row to trade tracking df
    if last_SMA_50 > last_SMA_200 and last_RSI < 70 and cash_per_trade >= price * 1.01:
        return "buy", None
    #check current trades and sell if stoploss has been met
    if len(trade) > 0:
        for l in range (len(trade)):
             if trade[l,6] == 1:
                        if price < trade[l, 1]:
                             index = l
                             return "sell", index
    #return hold otherwise
    return "hold", None


def SMAtrade_execution(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade, last_atr, date, position, trade_num, cash, buy_num, stoploss):
    result, index = SMAtrading_conditions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade)
    #if signaled buy, execute contitions
    if result == "buy":
        #assume slippage was 1% more for buying
        adjusted_price = price * 1.01
        position =  math.floor(cash_per_trade / adjusted_price)
        cash -= position * adjusted_price
        trade_num += 1
        buy_num += 1
        stoploss = round((adjusted_price - (last_atr * 3)), 2)

# Index mapping for trade DataFrame after conversion to NumPy array:
#  0: 'NUMBER'        - Trade number or ID
#  1: 'STOPLOSS'      - Stop-loss price level
#  2: 'SHARE_#'       - Number of shares bought
#  3: 'BUY_DATE'      - Date the position was opened
#  4: 'PRICE_BOUGHT'  - Price at which the asset was purchased
#  5: 'EXITDATE'      - Date the position was closed
#  6: 'ACTIVE?'       - Boolean flag for whether the trade is still open
#  7: 'W_TRADE?'      - Win flag (1 if trade was profitable, 0 if not)
#  8: 'INTIAL_VAL'    - Initial dollar value of the trade
#  9: 'VALUE'         - Current or exit value of the trade
# 10: 'LAST_UPDATE'   - Last price used to update stop-loss
# 11: 'EXIT_PRICE'    - Price at which the trade was exited


# 1 is true and 0 is false, -999 means unused value that will be updated later.

#CHANGE THIS AT SOME POINT, just use another array for dates
        new_trade = np.zeros((1, 12), dtype=object)

        new_trade[0,1] = stoploss
        new_trade[0, 2] = position
        new_trade[0,3] = date
        new_trade[0,4] = adjusted_price
        new_trade[0,5] = -999
        new_trade[0,6] = 1
        new_trade[0,7] = -999
        new_trade[0,8] = position * adjusted_price
        new_trade[0,9] = position * adjusted_price
        new_trade[0,10] = price
        new_trade[0,11] = -999

        trade = np.vstack((trade, new_trade))

    # if signaled sell, go to trade's index and update the row
    if result == "sell":
        #assume slippage was 1% less for selling
        adjusted_price = price * 0.99
        
        cash += trade[index, 2] * adjusted_price

        trade[index, 5] = date
        trade[index, 11] = adjusted_price
        trade[index, 6] = 0
        if trade[index, 9] > trade[index, 8]:
            trade[index, 7] = 1
        else:
            trade[index, 7] = 0
    return position, trade_num, cash, buy_num, stoploss, trade