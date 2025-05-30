#SMA_functions.py
import pandas as pd
import numpy as np
import time
import math
from utils import CSV_handling, plot_results
from indicators import calculate_rsi, calculate_atr
from get_data import choose_data

def update_stoploss(trade, price, last_atr, total_position, portfolio_value, control_portfolio_value, cash, control_position):
            if len(trade) > 0:
                for l in range (len(trade)):
                    if trade.at[trade.index[l],'ACTIVE?'] == False:
                         continue
                    else:

                        #conditional for updating stoploss

                        new_stop = price - (3 * last_atr)

                        if price >=  1.2 * trade.at[trade.index[l],'LAST_UPDATE'] and new_stop > trade.at[trade.index[l], 'STOPLOSS']:
                            stoploss = new_stop
                            trade.at[trade.index[l], 'LAST_UPDATE'] = price
                            trade.at[trade.index[l], 'STOPLOSS'] = stoploss
                            
                    total_position += trade.at[trade.index[l],'SHARE_#']
                    trade.at[trade.index[l],'VALUE'] = int(trade.at[trade.index[l],'SHARE_#'] * price)
            total_value = total_position * price + cash
            total_position = 0
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)

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
             if trade.at[trade.index[l],'ACTIVE?'] == True:
                        if price < trade.at[trade.index[l],'STOPLOSS']:
                             index = trade.index[l]
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
        trade.loc[len(trade)] = {
            'NUMBER': buy_num,
            'STOPLOSS': stoploss,
            'SHARE_#': position,
            'BUY_DATE': date,
            'PRICE_BOUGHT': adjusted_price,
            'ACTIVE?': True,
            'VALUE': int(position * adjusted_price),
            'INTIAL_VAL': int(position * adjusted_price),
            'EXITDATE': None,
            'EXIT_PRICE': None,
            'W_TRADE?': None,
            'LAST_UPDATE': price,
        }
    # if signaled sell, go to trade's index and update the row
     if result == "sell":
        #assume slippage was 1% less for selling
        adjusted_price = price * 0.99
        
        cash += trade.at[index, 'SHARE_#'] * adjusted_price

        trade.at[index, 'EXITDATE'] = date
        trade.at[index, 'EXIT_PRICE'] = adjusted_price
        trade.at[index, 'ACTIVE?'] = False

        if trade.at[index, 'VALUE'] > trade.at[index, 'INTIAL_VAL']:
            trade.at[index, 'W_TRADE?'] = True
        else:
            trade.at[index, 'W_TRADE?'] = False
     return position, trade_num, cash, buy_num, stoploss,

def complete_SMA_function():
    trade = pd.DataFrame(columns=[
        'NUMBER',
        'STOPLOSS',
        'SHARE_#',
        'BUY_DATE',
        'PRICE_BOUGHT',
        'EXITDATE',
        'ACTIVE?',
        'W_TRADE?',
        'INTIAL_VAL',
        'VALUE',
        'LAST_UPDATE',
        'EXIT_PRICE',
    ])

    # Grab API and secret key from env vars
    data, ticker, user_data_choice, = choose_data()
    
    if user_data_choice == "YF":
        data.rename(columns={"Close": "close", "Date": "date"}, inplace=True)
        data['date'] = pd.to_datetime(data['date'])

    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['SMA_200'] = data['close'].rolling(window=200).mean()
    data['RSI'] = calculate_rsi(data)
    data['ATR'] = calculate_atr(data, 14)

    # Define starting capital and variables
    capital = 10000
    starting_cap = capital
    position = 0
    cash = capital
    portfolio_value = []
    control_portfolio_value = []
    trade_num = 0
    buy_num = 0
    stoploss = 0
    total_position = 0
    current_year = 0
    first_price = float(data['close'].iloc[200])
    control_position = math.floor(starting_cap / first_price)
    num_of_years = len(data) / 251

    # Loop over available trading days
    print("Starting loop, please stand by...")
    time_start = time.time()

    price_data = []

    for i in range(200, len(data)):
        date = data.at[data.index[i], 'Date']
        last_SMA_50 = data.at[data.index[i], 'SMA_50']
        last_SMA_200 = data.at[data.index[i], 'SMA_200']
        last_RSI = data.at[data.index[i], 'RSI']
        last_atr = data.at[data.index[i], 'ATR']
        price = data.at[data.index[i], 'close']
        
        # Position sizing: 5% of cash
        cash_per_trade = cash * 0.05

        price_data.append({
            'Date': data.at[data.index[i], 'Date'],
            'Price': int(data.at[data.index[i], 'close'])
        })

        price_df = pd.DataFrame(price_data)
        price_df.set_index('Date', inplace=True)

        position, trade_num, cash, buy_num, stoploss = SMAtrade_execution(
            last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price,
            trade, last_atr, date, position, trade_num, cash, buy_num, stoploss
        )

        update_stoploss(
            trade, price, last_atr, total_position, portfolio_value,
            control_portfolio_value, cash, control_position
        )

        if i % 252 == 0:
            current_year += 1
            print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} year(s) left.") 

    # After loop is over
    end_time = time.time()

    sell_points = trade[trade['ACTIVE?'] == False]
    buy_points = pd.DataFrame({'X': trade['BUY_DATE'], 'Y': trade['PRICE_BOUGHT']})

    portfolio_df = pd.DataFrame({
        'Date': data.loc[data.index[200:], 'Date'],
        'Portfolio_Value': portfolio_value
    })
    portfolio_df.set_index('Date', inplace=True)

    control_portfolio_df = pd.DataFrame({
        'Date': data.loc[data.index[200:], 'Date'],
        'Control_Portfolio_Value': control_portfolio_value
    })
    control_portfolio_df.set_index('Date', inplace=True)

    if len(portfolio_value) == 0 or len(control_portfolio_value) == 0:
        raise ValueError("Cannot save: Empty portfolio data!")

    CSV_handling(
        portfolio_value, trade_num, num_of_years, ticker,
        starting_cap, portfolio_df, control_portfolio_value
    )

    plot_results(ticker, buy_points, sell_points, price_df, portfolio_df, control_portfolio_df)

    print(trade.head())
    print(trade.tail())
    print(f"Results saved successfully! Done with {ticker}")
    print(f"Program time: {round(end_time - time_start, 2)} secs")
