#get_data.py
import pandas as pd
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import yfinance as yf

class Get_Historical_Data:

    @staticmethod
    def grab_Alpaca_data():
        api_key = os.getenv("ALPACA_API_KEY")
        secret_api_key = os.getenv("ALPACA_SECRET_KEY")
        client = StockHistoricalDataClient(api_key, secret_api_key)
        ticker = input("What is the ticker symbol? ").upper()

        max_timeframe = StockBarsRequest(
            symbol_or_symbols=[ticker],
            timeframe=TimeFrame.Day,
            start=datetime(1999, 1, 1),
            end=datetime.now(),
        )

        bars = client.get_stock_bars(max_timeframe)
        first_date = bars[ticker][0].timestamp
        last_date = datetime.now()

        user_time_preference = 0
        while user_time_preference not in ["1", "2"]:
            user_time_preference = input(f"""Select timeframe option:
1 - Use full available data (max)
2 - Use a custom date range

Available data range: {first_date.year}-{first_date.month:02d}-{first_date.day:02d} to {last_date.year}-{last_date.month:02d}-{last_date.day:02d})
Enter 1 or 2: """)

        if user_time_preference == "2":
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
            bars = client.get_stock_bars(request_params)

        data = bars.df.reset_index()
        data['date'] = pd.to_datetime(data['timestamp']).dt.date

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.empty or len(data) < 200:
            raise KeyError(f"No sufficient data for {ticker}")

        return data, ticker

    @staticmethod
    def grab_YFdata():
        try:
            ticker = input("What is the ticker symbol? ").upper()
            root = os.path.expanduser("~/Simple Algorithm Backtester")
            folder = os.path.join(root, "data")
            file = f"{ticker} YF Data.parquet"
            print(file)
            file_path = os.path.join(folder, file) # broken
            file_path = f"/Users/natha/Simple Algorithm Backtester/data/{file}"
            print(file_path)
            if os.path.exists(file_path):
                print(f"Grabbing existing data from {file}")
                max_timeframe = pd.read_parquet(file_path)
                print(max_timeframe)
                max_timeframe["Date"] = pd.to_datetime(max_timeframe["Date"])
                max_timeframe = max_timeframe.set_index("Date") # not setting index as date also fix hardcoding
            else:
                print("No existing file found. Downloading data...")
                try:
                    max_timeframe = yf.download(ticker, period="max", auto_adjust=True)
                except Exception as e:
                    raise ConnectionError(f"connection error likely. Error: {e}")
                max_timeframe.to_parquet(file_path)

            if max_timeframe.empty:
                raise ValueError(f"No data was found for {ticker}, try checking ticker symbol.")

        except Exception as e:
            raise KeyError(f"Error fetching data: {e}")

        first_date = max_timeframe.index[0]
        last_date = max_timeframe.index[-1]
        print(f"close type: {max_timeframe["Close"].dtypes}")
        user_time_preference = 0
        while user_time_preference not in ["1", "2"]:
            user_time_preference = input(f"""Select timeframe option:
1 - Use full available data (max)
2 - Use a custom date range

Available data range: {first_date.year}-{first_date.month:02d}-{first_date.day:02d} to {last_date.year}-{last_date.month:02d}-{last_date.day:02d})
Enter 1 or 2: """)

        if user_time_preference == "1":
            data = max_timeframe.reset_index()
        else:
            start_date = f"{input('Start year (YYYY): ')}-{input('Start month (MM): ')}-{input('Start day (DD): ')}"
            end_date = f"{input('End year (YYYY): ')}-{input('End month (MM): ')}-{input('End day (DD): ')}"
            data = max_timeframe[(max_timeframe.index >= start_date) & (max_timeframe.index <= end_date)].reset_index()

        return data, ticker

    @staticmethod
    def choose_data():
        user_data_choice = 0
        while user_data_choice not in ["1", "2"]:
            user_data_choice = input("""Would you like historical data from Alpaca or Yahoo Finance?
1 - Alpaca
2 - YahooFinance
Please enter 1 or 2: """)

            if user_data_choice == "1":
                data, ticker = Get_Historical_Data.grab_Alpaca_data()
            elif user_data_choice == "2":
                data, ticker = Get_Historical_Data.grab_YFdata()

        if user_data_choice == "2":
            data.rename(columns={"Close": "close", "Date": "date", "High": "high", "Low": "low", "Volume": 'volume', "Open": 'open'}, inplace=True)
        elif user_data_choice == "1":
            data['date'] = pd.to_datetime(data['timestamp']).dt.date
            data.drop(columns=['timestamp', 'vwap', 'trade_count', 'symbol'], inplace=True)
            columns = ['date', 'close', 'high', 'low', 'open', 'volume']
            data = data[columns]
        data = data.dropna()
        if len(data) < 200 or len(data) == 0:
            raise ValueError(f"Not enough data for indicators. Data only has {len(data)}.")

        return data, ticker, user_data_choice
