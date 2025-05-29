import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import math
import os
import time
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

def get_Alpaca_data():
    ticker = input("What is the ticker symbol? ")

    user_time_preference = input("Would you like to use the max timeframe or custom? (1 for max), (2 for custom) ")

    api_key = os.getenv("ALPACA_API_KEY")
    secret_api_key = os.getenv("ALPACA_SECRET_KEY")
    client = StockHistoricalDataClient(api_key, secret_api_key)


    if user_time_preference == "1":
        request_params = StockBarsRequest(
        symbol_or_symbols=[ticker],
        timeframe=TimeFrame.Day,     
        start=datetime(1999, 1, 1),
        end=datetime.now()
                                        )
    elif user_time_preference == "2":
     
        start_year = int(input("What start year should it test on? (year number) "))
        start_month = int(input("What start month should it test on? (month number) "))
        start_day = int(input("What start day should it test on? (day number) "))

        end_year = int(input("What end year should it stop? (year number) "))
        end_month = int(input("What end month should it stop? (month number) "))
        end_day = int(input("What end day should it stop? (day number) "))


        request_params = StockBarsRequest(
            symbol_or_symbols=[ticker],
            timeframe=TimeFrame.Day,     
            start=datetime(start_year, start_month, start_day),
            end=datetime(end_year, end_month, end_day)
                                        )

    else:
        raise ValueError("Did not choose valid option. (1 or 2)")

#get bars for the data
    bars = client.get_stock_bars(request_params)

    data = bars.df
    #reset data index back to normal
    data = data.reset_index()

#only get the date from timestamp frame
    data['Date'] = pd.to_datetime(data['timestamp']).dt.date


    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data, ticker


def line_break():
     print("=============================================================================================")
    
def CSV_handling(portfolio_value, trade_num, num_of_years, ticker, starting_cap, portfolio_df, control_portfolio_value):
     #calculate stats for CSV summary
        cagr = ((portfolio_value[-1] / starting_cap) ** (1 / num_of_years) - 1) * 100
        running_max = portfolio_df['Portfolio_Value'].cummax()
        drawdown = (portfolio_df['Portfolio_Value'] - running_max) / running_max
        max_drawdown = drawdown.min()

        #DF for summary to CSV file
        summary = pd.DataFrame([{
            'symbol': ticker,
            'end_val': f"${math.floor(portfolio_value[-1]):,.0f}",
            'winner': 'Strategy' if portfolio_value[-1] > control_portfolio_value[-1] else 'Benchmark',
            'trades': f"{round(trade_num / num_of_years, 1):,.1f}",
            'cagr': f"{round(cagr, 2)}%",
            'median': f"${round(float(np.median(portfolio_value))):,.0f}",
            'average': f"${round(float(np.mean(portfolio_value))):,.0f}",
            'max_drawdown': f"{round(max_drawdown * 100, 2)}%",
            'running_max': f"${running_max.iloc[-1]:,.0f}",
            'version': "V2",
        }])

        ALL_COLUMNS = [
            'symbol',
            'end_val',
            'winner',
            'trades',
            'cagr',
            'median',
            'average',
            'max_drawdown',
            'running_max',
            'version',
        ]
        
        user_CSV_preference = input("Would you like to save results to CSV? (y/n) ")
        if user_CSV_preference == "y":
            print("Saving results...")
        #make sure folder exists
            output_folder = "CSV files"
            os.makedirs(output_folder, exist_ok=True)

            file_path = os.path.join(output_folder, "MA_backtest.csv")

            if os.path.exists(file_path):
                df_existing = pd.read_csv(file_path)

    # Append new summary
                df_updated = pd.concat([df_existing, summary], ignore_index=True)

    # Drop duplicates by 'symbol' and 'version' if needed
                df_updated.drop_duplicates(subset=["symbol", "version"], keep="last", inplace=True)

    # Save it back
                df_updated.to_csv(file_path, index=False, columns=ALL_COLUMNS)
            else:
                summary.to_csv(file_path, index=False, columns=ALL_COLUMNS)

            line_break()
            print(summary)
            line_break()
        else:
            line_break()
            print(summary)
            line_break()
        
def plot_results(buy_points, sell_points, price_df, portfolio_df, control_portfolio_df):
            
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex= True, figsize=(10, 6))

# Plot on first subplot (ax1)
    ax1.scatter(buy_points['X'], buy_points['Y'] - 1, color = 'blue', marker = '^', s =10, label = "Buy Signal")
    ax1.scatter(sell_points['EXITDATE'], sell_points['EXIT_PRICE'] + 1, color='red', marker = 'v', s=10, label = "Sell Signal")
    ax1.plot(portfolio_df.index, price_df['Price'], color="green", alpha = 0.7)
    ax1.set_ylabel('Price')
    ax1.set_title('Price Chart')
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.2f}'))
    ax1.grid(True)
    ax1.legend()


    # Plot on second subplot (ax2)
    ax2.plot(portfolio_df.index, portfolio_df['Portfolio_Value'], label="Strategy Portfolio Value")
    ax2.plot(control_portfolio_df.index, control_portfolio_df['Control_Portfolio_Value'], label=f"Benchmark", color ="orange")
    ax2.set_ylabel('Portfolio Value')
    ax2.set_xlabel('Date')
    ax2.set_title(f'Backtest Results for {ticker}')
    ax2.ticklabel_format(style='plain', axis='y')
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax2.grid(True)
    ax2.legend()

    plt.show()


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


def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    gain_series = pd.Series(gain.flatten(), index=data.index)
    loss_series = pd.Series(loss.flatten(), index=data.index)
    avg_gain = gain_series.rolling(window=window, min_periods=1).mean()
    avg_loss = loss_series.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    rsi = round(rsi, 2)
    return rsi

def calculate_atr(data, window):
    if data.empty:
        raise ValueError("Downloaded data is empty. Check the ticker symbol or internet connection.")

    high = data['high']
    low = data['low']
    close = data['close']
    last_close = close.shift(1)

    required_cols = {'high', 'low', 'close'}
    if not required_cols.issubset(data.columns):
        raise ValueError(f"Missing one of the required columns: {required_cols}")

    tr1 = high - low
    tr2 = abs(high - last_close)
    tr3 = abs(low - last_close)

    # Create a DataFrame with correct indices for each True Range component
    true_range = pd.DataFrame({
        'tr1': tr1,
        'tr2': tr2,
        'tr3': tr3,
    })

    # Find the maximum of the three True Range components for each row
    true_range = true_range.max(axis=1)

    # Calculate the ATR as the rolling mean of true_range
    atr = round(true_range.rolling(window=window).mean(), 2)
    return atr

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
    #if signaled buy, execute conditions
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
            'W_TRADE?': None,
            'LAST_UPDATE': adjusted_price,
            'EXIT_PRICE': None,
        }
    # if signaled sell, go to trade's index and update the row
    if result == "sell":
        #assume slippage was 1% less for selling
        adjusted_price = price * 0.99
        cash += trade.at[index, 'SHARE_#'] * adjusted_price

        trade.at[index, 'EXITDATE'] = date
        trade.at[index, 'ACTIVE?'] = False
        trade.at[index, 'EXIT_PRICE'] = adjusted_price


        if trade.at[index, 'VALUE'] > trade.at[index, 'INTIAL_VAL']:
            trade.at[index, 'W_TRADE?'] = True
        else:
            trade.at[index, 'W_TRADE?'] = False
    return position, trade_num, cash, buy_num, stoploss,

#create dataframe for tracking trades 
trade = pd.DataFrame(
columns=[
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
]
)

#grab api and secret key from env vars

data, ticker = get_Alpaca_data()

if data.empty or len(data) < 200:
        print(f"No sufficient data for {ticker}")
else:
        data['SMA_50'] = data['close'].rolling(window=50).mean()
        data['SMA_200'] = data['close'].rolling(window=200).mean()
        data['RSI'] = calculate_rsi(data)
        data['ATR'] = calculate_atr(data, 14)

        #define starting capital and varibles
        capital = 10000
        starting_cap = capital
        position = 0
        cash = capital
        portfolio_value = []
        control_portfolio_value = []
        control_capital = capital
        trade_num = 0
        buy_num = 0
        stoploss = 0
        active_trades = 0
        total_position = 0
        current_year = 0
        first_price = float(data['close'].iloc[200])
        control_position = math.floor(starting_cap / first_price)
        num_of_years = len(data) / 251
        #for loop for number of trading days avalible for the ticker
        print("starting loop, please stand by..")
        time_start = time.time()

        price_data = []

        for i in range(200, len(data)):
            date = data.at[data.index[i],'Date']
            last_SMA_50 = data.at[data.index[i],'SMA_50']
            last_SMA_200 = data.at[data.index[i],'SMA_200']
            last_RSI = data.at[data.index[i],'RSI']
            last_atr = data.at[data.index[i],'ATR']
            price = data.at[data.index[i],'close']
            #postition sizing of 5% of total value to trade
            cash_per_trade = cash * 0.05

            price_data.append({
                'Date': data.at[data.index[i], 'Date'],
                'Price': int(data.at[data.index[i], 'close'])
            })

            price_df = pd.DataFrame(price_data)
            price_df.set_index('Date', inplace=True)

            yesterdays_price = round(data.at[data.index[i - 1],'close'], 2)
            last_week_price = round(data.at[data.index[i - 5], 'close'], 2)

            position, trade_num, cash, buy_num, stoploss = SMAtrade_execution(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade, last_atr, date,position, trade_num, cash, buy_num, stoploss)

            update_stoploss(trade, price, last_atr, total_position, portfolio_value, control_portfolio_value, cash, control_position)




            if i % 252 == 0:
                current_year+= 1
                print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} year(s) left.") 

    #after loop is over

        end_time = time.time()

        sell_points = trade[trade['ACTIVE?'] == False]

        buy_points = pd.DataFrame({'X': trade['BUY_DATE'], 'Y': trade['PRICE_BOUGHT']})

        portfolio_df = pd.DataFrame({'Date': data.loc[data.index[200:], 'Date'], 'Portfolio_Value': portfolio_value})
        portfolio_df.set_index('Date', inplace=True)

        control_portfolio_df = pd.DataFrame({'Date': data.loc[data.index[200:], 'Date'], 'Control_Portfolio_Value': control_portfolio_value})
        control_portfolio_df.set_index('Date', inplace=True)

        if len(portfolio_value) == 0 or len(control_portfolio_value) == 0:
            raise ValueError("Cannot save: Empty portfolio data!")

        CSV_handling(portfolio_value, trade_num, num_of_years, ticker, starting_cap, portfolio_df, control_portfolio_value)

        plot_results(buy_points, sell_points, price_df, portfolio_df, control_portfolio_df)

        print(trade.head())
        print(trade.tail())
        print(f"Results saved successfully! Done with {ticker}")
        print(f" program time: {round(end_time - time_start, 2)} secs")
        
