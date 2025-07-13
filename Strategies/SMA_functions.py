#SMA_functions.py
import pandas as pd
import numpy as np
import time
from numba import jit 
import math
import line_profiler
from utils import Utils, update_stoploss
from indicators import Indicators
from get_data import Get_Historical_Data

#generate the defination for simple python classes (may expand on this)
def class_generator(*args, **kwargs):
    vars = args
    var_list = ", ".join(args)
    class_name = kwargs.get("name", "(class name)")
    print(f"""class {class_name}:

    def __init__({var_list}):""")
    for varible in vars:
        print(f"        self.{varible} = {varible}")

class SMA_Functions:

    def __init__(self, last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, 
                 price, trade, last_atr, date, position, trade_num, cash, 
                 buy_num, stoploss):
        
        self.last_SMA_50 = last_SMA_50
        self.last_SMA_200 = last_SMA_200
        self.last_RSI = last_RSI
        self.cash_per_trade = cash_per_trade
        self.price = price
        self.trade = trade
        self.last_atr = last_atr
        self.date = date
        self.position = position
        self.trade_num = trade_num
        self.cash = cash
        self.buy_num = buy_num
        self.stoploss = stoploss
        
# Check trading conditions: buy signal logic only
# Returns "buy" or "hold" based on indicator conditions
    def SMAtrading_conditions(self):
        if np.isnan(self.last_SMA_50) or np.isnan(self.last_SMA_200) or np.isnan(self.last_RSI):
            return "hold"
        if self.last_SMA_50 > self.last_SMA_200 and self.last_RSI < 70 and self.cash_per_trade >= self.price * 1.01:
            return "buy"
        return "hold"

    def sell_execution(self):
        if len(self.trade) > 0 and np.any(self.trade[:, 6] == 1):
            sell_mask = (
                (self.trade[:, 6] == 1) &
                (self.trade[:, 1] > self.price)
            )
            index_list = np.where(sell_mask)[0]

            for index in index_list:
                adjusted_price = self.price * 0.999  # Slippage
                self.cash += self.trade[index, 2] * adjusted_price

                self.trade[index, 5] = self.date
                self.trade[index, 11] = adjusted_price
                self.trade[index, 6] = 0  # Deactivate

                # Win condition
                if self.trade[index, 9] > self.trade[index, 8]:
                    self.trade[index, 7] = 1
                else:
                    self.trade[index, 7] = 0

        return self.trade, self.cash

    def trade_execution(self):
        self.trade, self.cash = self.sell_execution()
        result = self.SMAtrading_conditions()

        if result == "buy":
            adjusted_price = self.price * 1.001  # Slippage
            self.position = math.floor(self.cash_per_trade / adjusted_price)
            self.cash -= self.position * adjusted_price
            self.trade_num += 1
            self.buy_num += 1
            self.stoploss = round(adjusted_price - (self.last_atr * 3), 2)

            new_trade = np.zeros((1, 12), dtype=object)
            new_trade[0, 1] = self.stoploss
            new_trade[0, 2] = self.position
            new_trade[0, 3] = self.date
            new_trade[0, 4] = adjusted_price
            new_trade[0, 5] = -999
            new_trade[0, 6] = 1  # Active
            new_trade[0, 7] = -999
            new_trade[0, 8] = self.position * adjusted_price
            new_trade[0, 9] = self.position * adjusted_price
            new_trade[0, 10] = self.price
            new_trade[0, 11] = -999

            self.trade = np.vstack((self.trade, new_trade))

        return self.position, self.trade_num, self.cash, self.buy_num, self.stoploss, self.trade


# Main strategy runner
# Handles the entire SMA backtest
#@profile #
def complete_SMA_function():

    trade = np.empty((0, 12), dtype=object)

    data, ticker, user_data_choice = Get_Historical_Data.choose_data()
    data = data.dropna()

    if len(data) < 200:

        raise ValueError(f"Backtest needs at least 200 days and dataframe only has {len(data)}, Try increasing or checking timeframe format.")

    # Calculate indicators
    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['SMA_200'] = data['close'].rolling(window=200).mean()

    indicators = Indicators(data)

    data['RSI'] = indicators.calculate_rsi()
    data['ATR'] = indicators.calculate_atr()

    data = data.values  # Convert to NumPy for speed

    # Initialize capital and tracking variables
    capital = 10000
    starting_cap = capital
    position = 0
    cash = capital
    portfolio_value = []
    control_portfolio_value = []
    price_data = []
    trade_num = 0
    buy_num = 0
    stoploss = 0
    total_position = 0
    current_year = 0
    first_price = data[0, 1]
    control_position = math.floor(starting_cap / first_price)
    # there are 252 trading days in a year
    num_of_years = math.ceil(len(data) / 252)

    print("Starting test, please stand by...")
    time_start = time.time()

    for i in range(len(data)):
        date = data[i, 0]
        price = data[i, 1]
        last_SMA_50 = data[i, 6]
        last_SMA_200 = data[i, 7]
        last_RSI = data[i, 8]
        last_atr = data[i, 9]

        cash_per_trade = cash * 0.05 # 5% position sizing 

        SMA = SMA_Functions(last_SMA_50, last_SMA_200, last_RSI, cash_per_trade, 
                 price, trade, last_atr, date, position, trade_num, cash, 
                 buy_num, stoploss)

        position, trade_num, cash, buy_num, stoploss, trade = SMA.trade_execution()

        update_stoploss(trade, price, last_atr, cash, control_position, 
                        portfolio_value, control_portfolio_value)

        if num_of_years - current_year >= 1:
            if i % 252 == 0 and not (num_of_years - current_year == 1):
                print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} years left.")
                current_year += 1
            elif i % 252 == 0 and num_of_years - current_year == 1:
                print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} year left.")
                current_year += 1

    # Wrap-up and export
    end_time = time.time()

    price_data = pd.DataFrame({
        'Date': data[:, 0],
        'Price': data[:, 1]
    })
    price_df = price_data
    price_df.set_index('Date', inplace=True)

    sell_mask = trade[trade[:, 6] == 0]  # Trades that exited
    sell_points = pd.DataFrame({'X': sell_mask[:, 5], 'Y': sell_mask[:, 11]}) # Sell signals, mask needed
    buy_points = pd.DataFrame({'X': trade[:, 3], 'Y': trade[:, 4]})  # Buy signals (no need for mask)

    # create DataFrames for both portfolio and control plotting
    portfolio_df = pd.DataFrame({
        'Date': data[:, 0],
        'Portfolio_Value': portfolio_value
    })

    portfolio_df.set_index('Date', inplace=True)

    control_portfolio_df = pd.DataFrame({
        'Date': data[:, 0],
        'Control_Portfolio_Value': control_portfolio_value
    })
    control_portfolio_df.set_index('Date', inplace=True)

    if len(portfolio_value) == 0 or len(control_portfolio_value) == 0:
        raise ValueError("Cannot save: Empty portfolio data.")
    
    print(f"Program time: {round(end_time - time_start, 2)} secs")

    utils = Utils(
        portfolio_value, trade_num, num_of_years, ticker, starting_cap,
        portfolio_df, control_portfolio_value, trade, data, capital, 
        user_data_choice, buy_points, sell_points, price_df, 
        control_portfolio_df, price, last_atr, total_position, 
        cash, control_position
            )

    utils.CSV_handling()

    utils.plot_results()


