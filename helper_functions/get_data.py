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
    def grab_Alpaca_data(ticker):
        api_key = os.getenv("ALPACA_API_KEY")
        secret_api_key = os.getenv("ALPACA_SECRET_KEY")
        client = StockHistoricalDataClient(api_key, secret_api_key)
        root = os.path.expanduser("~/Simple Algorithm Backtester")
        folder = os.path.join(root, "data")
        file = f"{ticker} Alpaca Data.parquet"
        file_path = os.path.join(folder, file) # broken
        print(file_path)
        if os.path.exists(file_path):
            print(f"Grabbing existing data from {file}")
            max_timeframe_data = pd.read_parquet(file_path)
            if not max_timeframe_data.index.name == "timestamp":
                if "timestamp" in max_timeframe_data.columns:
                    max_timeframe_data.set_index("timestamp", inplace=True)
        else:
            print("No existing file found. Downloading data...")
            try:
                max_timeframe = StockBarsRequest(
                    symbol_or_symbols=[ticker],
                    timeframe=TimeFrame.Day,
                    start=datetime(1999, 1, 1),
                    end=datetime.now(),
                    )
                max_timeframe_data = client.get_stock_bars(max_timeframe).df
                # set index to timestamp if it isnt already
                if max_timeframe_data.index.name != "timestamp":
                    if "timestamp" in max_timeframe_data.columns:
                        max_timeframe_data.set_index("timestamp", inplace=True)

                if max_timeframe_data.empty or len(max_timeframe_data) < 200:
                    raise KeyError("Downloaded data was empty.")
                # 
                if isinstance(max_timeframe_data.columns, pd.MultiIndex):
                        max_timeframe_data.columns = max_timeframe_data.columns.get_level_values(0)
                if isinstance(max_timeframe_data.index, pd.MultiIndex):
                    max_timeframe_data.reset_index(inplace=True)
                    max_timeframe_data.set_index("timestamp", inplace=True)

                max_timeframe_data.to_parquet(file_path)
            except Exception as e:
                    raise ConnectionError(f"connection error likely. Error: {e}")
        first_date = max_timeframe_data.index[0]
        last_date = max_timeframe_data.index[-1]   

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

            start_date = f"{start_year}-{start_month}-{start_day}"
            end_date = f"{end_year}-{end_month}-{end_day}"
            # data = start_date < existing data < end_date
            valid_data = max_timeframe_data[(max_timeframe_data.index >= start_date) & (max_timeframe_data.index <= end_date)].reset_index()
        else:
            valid_data = max_timeframe_data

        valid_data = valid_data.reset_index()

        if valid_data.empty or len(valid_data) < 200:
            raise KeyError(f"No sufficient data for {ticker}")

        return valid_data

    @staticmethod
    def grab_YFdata(ticker):
        try:
            root = os.path.expanduser("~/Simple Algorithm Backtester")
            folder = os.path.join(root, "data")
            file = f"{ticker} YF Data.parquet"
            file_path = os.path.join(folder, file) # broken
            file_path = f"/Users/natha/Simple Algorithm Backtester/data/{file}"
            if os.path.exists(file_path):
                print(f"Grabbing existing data from {file}")
                max_timeframe = pd.read_parquet(file_path)
                print(max_timeframe)
                if max_timeframe.index.name != "Date":
                    max_timeframe = max_timeframe.set_index("Date") # not setting index as date also fix hardcoding
            else:
                print("No existing file found. Downloading data...")
                try:
                    max_timeframe = yf.download(ticker, period="max", auto_adjust=True)
                    if isinstance(max_timeframe.columns, pd.MultiIndex):
                        max_timeframe.columns = max_timeframe.columns.get_level_values(0)
                except Exception as e:
                    raise ConnectionError(f"connection error likely. Error: {e}")
                max_timeframe.to_parquet(file_path)

            if max_timeframe.empty:
                raise ValueError(f"No data was found for {ticker}, try checking ticker symbol.")

        except Exception as e:
            raise KeyError(f"Error fetching data: {e}")

        first_date = max_timeframe.index[0]
        last_date = max_timeframe.index[-1]
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

        return data

    @staticmethod
    def choose_data(ticker, data_type):
        

        if data_type == "Alpaca":
            data = Get_Historical_Data.grab_Alpaca_data(ticker)
        elif data_type == "YF":
            data = Get_Historical_Data.grab_YFdata(ticker)
        else:
            raise ValueError(f"the data type you requested ({data_type}) is not supported. Try Alpaca or YF")

        if data_type == "YF":
            data.rename(columns={"Close": "close", "Date": "date", "High": "high", "Low": "low", "Volume": 'volume', "Open": 'open'}, inplace=True)
        elif data_type == "Alpaca":
            data['date'] = pd.to_datetime(data['timestamp']).dt.date
            data.drop(columns=['timestamp', 'vwap', 'trade_count', 'symbol'], inplace=True)
            columns = ['date', 'close', 'high', 'low', 'open', 'volume']
            data = data[columns]
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame([data])
        data = data.dropna()
        if len(data) < 200 or len(data) == 0:
            raise ValueError(f"Not enough data for indicators. Data only has {len(data)}.")

        return data
