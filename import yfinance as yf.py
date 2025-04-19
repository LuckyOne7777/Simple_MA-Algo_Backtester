import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import math
import os
import random


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
        'tr3': tr3
    })

    # Find the maximum of the three True Range components for each row
    true_range = true_range.max(axis=1)

    # Calculate the ATR as the rolling mean of true_range
    atr = true_range.rolling(window=window).mean()
    return atr


# Get list of S&P 500 tickers
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
sp500_table = pd.read_html(url)[0]
sp500_tickers = sp500_table["Symbol"].tolist()

# Choose a random ticker
#ticker = random.choice(sp500_tickers)
ticker = "NVDA"
if "." in ticker:
    ticker = ticker.replace(".", "-")

sp500 = "^GSPC"
vix = "^VIX"

buy_num = 0
stoploss = 0
active_trades = 0

data_check = yf.download(ticker, period="max", auto_adjust= False)

#create dataframe for tracking trades 
trade = pd.DataFrame(
columns=[
'NUMBER',
'STOPLOSS',
'SHARES_BOUGHT'
'DATE'
'PRICE_BOUGHT',
'EXITDATE',
'ACTIVE?',
'CASH'
]
)
total_position = 0
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

        capital = 10000
        starting_cap = capital
        position = 0
        cash = capital
        portfolio_value = []
        control_portfolio_value = []
        trade_size = cash * 0.05

        control_capital = capital
        trade_num = 0

        for i in range(200, len(data)):    
            last_SMA_50 = data['SMA_50'].iloc[i]
            last_SMA_200 = data['SMA_200'].iloc[i]
            last_RSI = data['RSI'].iloc[i]
            last_atr = data['ATR'].iloc[i]
            price = float(data['Close'].iloc[i])
            yesterdays_price = float(data['Close'].iloc[i - 1])
            last_week_price = float(data['Close'].iloc[i - 5])
            first_price = float(data['Close'].iloc[200])
            num_of_years = len(data) / 365
            control_position = math.floor(starting_cap / first_price)
            cash_per_trade = cash * 0.05

            if np.isnan(last_SMA_50) or np.isnan(last_SMA_200) or np.isnan(last_RSI):
                continue
            if position == 0 and last_SMA_50 > last_SMA_200 and last_RSI < 70:
                    position = math.floor(cash_per_trade / price)
                    cash -= position * price
                    trade_num += 1

            elif position and price >= last_week_price * 0.90:
                    position = math.floor(cash_per_trade / price)
                    cash -= position * price
                    trade_num += 1

            elif position > 0 and (last_SMA_50 < last_SMA_200 or price <= yesterdays_price * 0.90 or price <= last_week_price * 0.90):
                    cash += position * price
                    trade_num += 1
                    position = 0

            #update all the values 
            total_value = total_position * price + cash
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)

            print(trade.head())

        portfolio_df = pd.DataFrame({'Date': data.index[200:], 'Portfolio_Value': portfolio_value})
        portfolio_df.set_index('Date', inplace=True)

        control_portfolio_df = pd.DataFrame({'Date': data.index[200:], 'Control_Portfolio_Value': control_portfolio_value})
        control_portfolio_df.set_index('Date', inplace=True)

        if len(portfolio_value) == 0 or len(control_portfolio_value) == 0:
            raise ValueError("Cannot save: Empty portfolio data!")

        end_val = math.floor(portfolio_value[-1])
        trades_per_year = trade_num / num_of_years
        cagr = ((portfolio_value[-1] / starting_cap) ** (1 / num_of_years) - 1) * 100
        median_val = round(float(np.median(portfolio_value)), 2)
        avg_val = round(float(np.mean(portfolio_value)), 2)
        running_max = portfolio_df['Portfolio_Value'].cummax()
        drawdown = (portfolio_df['Portfolio_Value'] - running_max) / running_max
        max_drawdown = drawdown.min()
        #make df to plot 
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
        ]

        summary.to_csv(
            "MA_backtest.csv",
            mode='a' if os.path.exists("MA_backtest.csv") else 'w',
            header=not os.path.exists("MA_backtest.csv"),
            index=False,
            columns=ALL_COLUMNS
        )
        #plotting
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

        print(f"Results saved successfully! Done with {ticker}")

#AIG
#add multiple trading and a table for tracking buying and selling for each one
#track last price when it bought ad=nd upate stoploss if it exceeds that value, explains why its not selling