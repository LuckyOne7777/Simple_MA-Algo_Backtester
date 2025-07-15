import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import warnings

warnings.filterwarnings("ignore")

main_tickers = [
# Broad Market Indexes
"SPY", "VIX", "QQQ", "DIA", "IWM",

# Sector ETFs
"XLK", "XLF", "XLE", "XLV", "XLI",
"XLY", "XLP", "XLU", "XLB", "XLRE",

# Technology
"AAPL", "MSFT", "NVDA", "ADBE", "CRM",

# Financials
"JPM", "BAC", "GS", "MS", "SCHW",

# Energy
"XOM", "CVX", "COP", "EOG", "PSX",

# Healthcare
"JNJ", "PFE", "UNH", "LLY", "MRK",

# Industrials
"BA", "CAT", "DE", "LMT", "UNP",

# Consumer Discretionary
"TSLA", "AMZN", "HD", "MCD", "NKE",

# Consumer Staples
"KO", "PEP", "WMT", "PG", "COST",

# Utilities
"NEE", "DUK", "SO", "AEP", "EXC",

# Materials
"LIN", "SHW", "NEM", "APD", "FCX",

# Real Estate
"PLD", "AMT", "CCI", "SPG", "EQIX"
]

# check max drawdown
# remove some decimal places
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    gain_series = pd.Series(gain.flatten(), index=data.index)
    loss_series = pd.Series(loss.flatten(), index=data.index)
    avg_gain = gain_series.rolling(window=window, min_periods=1).mean()
    avg_loss = loss_series.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Select a stock for backtesting
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
sp500_table = pd.read_html(url)[0]
sp500_tickers = sp500_table["Symbol"].tolist()
for j in range(1, len(main_tickers)):
    ticker = main_tickers[j]
    x = j
    #some tickers use . instead of - on yf
    if "." in ticker:
        ticker = ticker.replace(".", "-")

    sp500 = "^GSPC"
    vix = "^VIX" 

    #tbh i had a if statement and now idk how to get rid of it so this is here 
    if 1 == 1:
        data_check = yf.download(ticker, period="max")
        if not data_check.empty:
            first_date = data_check.index[0]
            last_date = data_check.index[-1]
            data = yf.download(ticker, start=first_date, end=last_date)
            market_data = yf.download(sp500, period="40y")
            vix_data = yf.download(vix, start=first_date, end=last_date)

            if data.empty or len(data) < 200:
                print(f"No sufficient data for {ticker}")
            else:
                data['SMA_50'] = data['Close'].rolling(window=50).mean()
                data['SMA_200'] = data['Close'].rolling(window=200).mean()
                data['RSI'] = calculate_rsi(data)

                capital = 10000
                starting_cap = capital
                position = 0
                cash = capital
                portfolio_value = []
                control_portfolio_value = []

                control_capital = capital
                trade_num = 0

                for i in range(200, len(data)):
                    last_SMA_50 = data['SMA_50'].iloc[i]
                    last_SMA_200 = data['SMA_200'].iloc[i]
                    last_RSI = data['RSI'].iloc[i]
                    price = float(data['Close'].iloc[i])
                    vix_price = price = float(data['Close'].iloc[i - 1])
                    yesterdays_price = float(data['Close'].iloc[i - 1])
                    last_week_price = float(data['Close'].iloc[i - 5])
                    first_price = float(data['Close'].iloc[200])
                    num_of_years = len(data) / 365
                    control_position = math.floor(starting_cap / first_price)

                    if np.isnan(last_SMA_50) or np.isnan(last_SMA_200) or np.isnan(last_RSI):
                        continue

                    if position == 0 and last_SMA_50 > last_SMA_200 and last_RSI < 70:
                        position = math.floor(cash / price)
                        cash -= position * price
                        trade_num += 1

                    elif position == 0 and price >= last_week_price * 0.90:
                        position = math.floor(cash / price)
                        cash -= position * price
                        trade_num += 1

                    elif position > 0 and (last_SMA_50 < last_SMA_200 or price <= yesterdays_price * 0.90 or price <= last_week_price * 0.90):
                        cash += position * price
                        trade_num += 1
                        position = 0

                    total_value = position * price + cash
                    total_control_value = control_position * price
                    portfolio_value.append(total_value)
                    control_portfolio_value.append(total_control_value)

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
                    'version': "V1"
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

                output_folder = "Archive"
                os.makedirs(output_folder, exist_ok=True)  # makes folder if it doesn't exist


                file_path = os.path.join(output_folder, "MA_backtestV1.csv")


                if os.path.exists(file_path):
                        df_existing = pd.read_csv(file_path)
                # Ensure all rows have the "version" column set to V2
                        df_existing["version"] = "V1"

                df_existing = pd.read_csv(file_path)
    # Append new summary
                df_updated = pd.concat([df_existing, summary], ignore_index=True)
                df_updated.to_csv(file_path, index=False)

                print(f"Results saved successfully! done with {ticker} loop num:{x}")
                del control_portfolio_df
                del portfolio_df

