#get_data.py
import pandas as pd
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import yfinance as yf

def grab_Alpaca_data():
    ticker = input("What is the ticker symbol? ")
    ticker = ticker.upper()

    user_time_preference = input("Would you like to use the max timeframe or custom? (1 for max), (2 for custom) ")

    api_key = os.getenv("ALPACA_API_KEY")
    secret_api_key = os.getenv("ALPACA_SECRET_KEY")
    client = StockHistoricalDataClient(api_key, secret_api_key)


    if user_time_preference == "1":
        request_params = StockBarsRequest(
        symbol_or_symbols=[ticker],
        timeframe=TimeFrame.Day,     
        start=datetime(1999, 1, 1),
        end=datetime.now(),
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
            end=datetime(end_year, end_month, end_day),
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
    if data.empty or len(data) < 200:
        print(f"No sufficient data for {ticker}")
    return data, ticker

def grab_YFdata():
     
    ticker = input("What is the ticker symbol? ")

    user_time_preference = input("Would you like to use the max timeframe or custom? (1 for max), (2 for custom) ")
    if user_time_preference == "1":
        data = yf.download(ticker, period="max")

    elif user_time_preference == "2":
     
        start_year = input("What start year should it test on? (YYYY form) ")
        start_year = start_year + "-"

        start_month = input("What start month should it test on? (MM form) ")
        start_month = start_month + "-"

        start_day = input("What start day should it test on? (DD form) ")
        start_date = start_year + start_month + start_day

        end_year = input("What end year should it stop? (YYYY form) ")
        end_year = end_year + "-"

        end_month = input("What end month should it stop? (MM form) ")
        end_month = end_month + "-"

        end_day = input("What end day should it stop? (DD form) ")
        end_date = end_year + end_month + end_day


        data = yf.download(ticker, start=start_date, end=end_date)

    else:
        raise ValueError("Did not choose valid option. (1 or 2)")
    return data, ticker

def choose_data():
    user_data_choice = input("Would you like historical data from Alpaca or Yahoo Finance? (1 for Alpaca/ 2 for YF) ")
    if user_data_choice == "1":
        user_data_choice == "Alpaca"
        data, ticker = grab_Alpaca_data()
    elif user_data_choice == "2":
        user_data_choice = "YF"
        data, ticker = grab_YFdata()
    else:
        raise ValueError(f"{user_data_choice} is not a option. (1 or 2) ")
    
    return data, ticker, user_data_choice
