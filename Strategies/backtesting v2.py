import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import math
import os
import time


def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    gain_series = pd.Series(gain.flatten(), index=data.index)
    loss_series = pd.Series(loss.flatten(), index=data.index)
    avg_gain = gain_series.rolling(window=window, min_periods=1).mean()
    avg_loss = loss_series.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(data, window):
    if data.empty:
        raise ValueError("Downloaded data is empty. Check the ticker symbol or internet connection.")

    high = data['High']
    low = data['Low']
    close = data['Close']
    last_close = close.shift(1)

    required_cols = {'High', 'Low', 'Close'}
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
    atr = true_range.rolling(window=window).mean()
    return atr

def SMAtrading_conditions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade):

    if np.isnan(last_SMA_50) or np.isnan(last_SMA_200) or np.isnan(last_RSI):
                    return "hold", None
            #if buy conditions are met, buy and add a row to trade tracking df
    if last_SMA_50 > last_SMA_200 and last_RSI < 70 and cash_per_trade >= price:
        return "buy", None
    
    if len(trade) > 0:
        for l in range (len(trade)):
             if trade.at[trade.index[l],'ACTIVE?'] == True:
                        if price < trade.at[trade.index[l],'STOPLOSS']:
                             index = trade.index[l]
                             return "sell", index
    return "hold", None

def SMAtrade_excution(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade, last_atr, date, position, trade_num, cash, buy_num, stoploss):
     result, index = SMAtrading_conditions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade)

     if result == "buy":
        position =  math.floor(cash_per_trade / price)
        cash -= position * price
        trade_num += 1
        buy_num += 1
        stoploss = round((price - (last_atr * 3)), 2)
        trade.loc[len(trade)] = {
            'NUMBER': buy_num,
            'STOPLOSS': stoploss,
            'SHARES_BOUGHT': position,
            'DATE': date,
            'PRICE_BOUGHT': price,
            'ACTIVE?': True,
            'VALUE': int(position * price),
            'INTIAL_VAL': int(position * price),
            'EXITDATE': None,
            'W_TRADE?': None,
            'LAST_UPDATE': price,
        }
     if result == "sell":
        
        cash += trade.at[index, 'SHARES_BOUGHT'] * price

        trade.at[index, 'EXITDATE'] = date
        trade.at[index, 'ACTIVE?'] = False

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
'SHARES_BOUGHT',
'DATE',
'PRICE_BOUGHT',
'EXITDATE',
'ACTIVE?',
'W_TRADE?',
'INTIAL_VAL',
'VALUE',
'LAST_UPDATE',
]
)


# Get list of S&P 500 tickers
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
sp500_table = pd.read_html(url)[0]
sp500_tickers = sp500_table["Symbol"].tolist()

# Choose a random ticker
ticker = "MRNA"

if "." in ticker:
    ticker = ticker.replace(".", "-")

sp500 = "^GSPC"

#get the maximium timeframe for the ticker
data_check = yf.download(ticker, period="max", auto_adjust= False)



if not data_check.empty:
    first_date = data_check.index[0]
    last_date = data_check.index[-1]
    data = yf.download(ticker, start=first_date, end=last_date, auto_adjust=False)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data.columns = data.columns.get_level_values(0)
    market_data = yf.download(sp500, period="40y")

    if data.empty or len(data) < 200:
        print(f"No sufficient data for {ticker}")
    else:
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
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
        buy_num = 0
        stoploss = 0
        active_trades = 0
        total_position = 0
        current_year = 0

        #for loop for number of trading days avalible for the ticker
        print("starting loop, please stand by..")
        time_start = time.time()
        for i in range(200, len(data)):
            last_SMA_50 = data.at[data.index[i],'SMA_50']
            last_SMA_200 = data.at[data.index[i],'SMA_200']
            last_RSI = data.at[data.index[i],'RSI']
            last_atr = data.at[data.index[i],'ATR']

            price = round(data.at[data.index[i],'Open'], 2)
            if price == 0:
                continue
            yesterdays_price = round(data.at[data.index[i - 1],'Close'], 2)
            last_week_price = round(data.at[data.index[i - 5], 'Close'], 2)
            first_price = float(data['Close'].iloc[200])

            num_of_years = len(data) / 251
            control_position = math.floor(starting_cap / first_price)

            #postition sizing of 5% of total value to trade
            cash_per_trade = cash * 0.05
            date = data.index[i]

            position, trade_num, cash, buy_num, stoploss = SMAtrade_excution(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, price, trade, last_atr, date,position, trade_num, cash, buy_num, stoploss)
            
#check all data rows for still active trades, and then check if stoploss has been met, or needs to be updated

            if len(trade) > 0:
                for l in range (len(trade)):
                    if trade.at[trade.index[l],'ACTIVE?'] == True:
                        #conditional for updating stoploss

                        new_stop = price - (2 * last_atr)

                        if price >=  1.2 * trade.at[trade.index[l],'LAST_UPDATE'] and new_stop > trade.at[trade.index[l], 'STOPLOSS']:
                            stoploss = price - float((last_atr * 3))
                            trade.at[trade.index[l], 'LAST_UPDATE'] = price
                            trade.at[trade.index[l], 'STOPLOSS'] = stoploss


                        total_position += trade.at[trade.index[l],'SHARES_BOUGHT']
                        trade.at[trade.index[l],'VALUE'] = int(trade.at[trade.index[l],'SHARES_BOUGHT'] * price)

            if i % 252 == 0:
                current_year+= 1
                #'max_drawdown': f"{round(max_drawdown * 100, 2)}%"
                print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} year(s) left.")

            #update all the values at end of that day 
            total_value = total_position * price + cash
            total_position = 0
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)

        portfolio_df = pd.DataFrame({'Date': data.index[200:], 'Portfolio_Value': portfolio_value})
        portfolio_df.set_index('Date', inplace=True)

        control_portfolio_df = pd.DataFrame({'Date': data.index[200:], 'Control_Portfolio_Value': control_portfolio_value})
        control_portfolio_df.set_index('Date', inplace=True)

        if len(portfolio_value) == 0 or len(control_portfolio_value) == 0:
            raise ValueError("Cannot save: Empty portfolio data!")

        

        #calculate stats for CSV summary
        end_val = math.floor(portfolio_value[-1])
        trades_per_year = trade_num / num_of_years
        cagr = ((portfolio_value[-1] / starting_cap) ** (1 / num_of_years) - 1) * 100
        median_val = round(float(np.median(portfolio_value)), 2)
        avg_val = round(float(np.mean(portfolio_value)), 2)
        running_max = portfolio_df['Portfolio_Value'].cummax()
        drawdown = (portfolio_df['Portfolio_Value'] - running_max) / running_max
        max_drawdown = drawdown.min()

        #DF for summary
        summary = pd.DataFrame([{
            'symbol': ticker,
            'end_val': f"${end_val:,.0f}",
            'winner': 'Strategy' if portfolio_value[-1] > control_portfolio_value[-1] else 'Benchmark',
            'trades': round(trades_per_year, 1),
            'cagr': f"{round(cagr, 2)}%",
            'median': f"${median_val:,.0f}",
            'average': f"${avg_val:,.0f}",
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

        output_folder = "CSV files"
        os.makedirs(output_folder, exist_ok=True)  # makes folder if it doesn't exist

        file_path = os.path.join(output_folder, "MA_backtest.csv")

        if os.path.exists(file_path):
            df_existing = pd.read_csv(file_path)
                # Ensure all rows have the "version" column set to V2
            df_existing["version"] = "V2"

    # Append new summary
            df_updated = pd.concat([df_existing, summary], ignore_index=True)

    # Drop duplicates by 'symbol' and 'version' if needed
            df_updated.drop_duplicates(subset=["symbol", "version"], keep="last", inplace=True)

    # Save it back
            df_updated.to_csv(file_path, index=False, columns=ALL_COLUMNS)
        else:
            summary.to_csv(file_path, index=False, columns=ALL_COLUMNS)
      
        summary.to_csv(
            file_path,
            mode='a' if os.path.exists(file_path) else 'w',
            header=not os.path.exists(file_path),
            index=False,
            columns=ALL_COLUMNS,
        )
        #create a matplotlib plot
        plt.figure(figsize=(12, 6))
        plt.plot(portfolio_df.index, portfolio_df['Portfolio_Value'], label="Strategy Portfolio Value")
        plt.plot(control_portfolio_df.index, control_portfolio_df['Control_Portfolio_Value'], label=f"Benchmark", linestyle="dashed")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value ($)")
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
        plt.legend()
        plt.title(f"Backtest Results for {ticker}")
        plt.grid(True)
        plt.show()
        #print  the head and tail of trade results

        print(trade.head())
        print(trade.tail())
        print(f"Results saved successfully! Done with {ticker}")
        end_time = time.time()
        print(f" program time: {round(end_time - time_start, 2)} secs")
