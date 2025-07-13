#SMA_functions.py
import pandas as pd
import numpy as np
import time
from numba import jit 
import math
import line_profiler
from utils import Utils, update_stoploss
from indicators import calculate_rsi, calculate_atr
from get_data import Get_Historical_Data

def class_generator(*args, **kwargs):
    vars = args
    var_list = ", ".join(args)
    class_name = kwargs.get("name", "(class name)")
    print(f"""class {class_name}:

    def __init__({var_list}):""")
    for varible in vars:
        print(f"        self.{varible} = {varible}")


class_generator( 'last_SMA_50', 'last_SMA_200', 'last_RSI', 'cash_per_trade', 
                 'price', 'trade', 'last_atr', 'date', 'position', 'trade_num', 'cash', 
                 'buy_num', 'stoploss', name ="test")

# Check trading conditions: buy signal logic only
# Returns "buy" or "hold" based on indicator conditions

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
        
    def SMAtrading_conditions(self):
        if np.isnan(self.last_SMA_50) or np.isnan(self.last_SMA_200) or np.isnan(self.last_RSI):
            return "hold"
        if self.last_SMA_50 > self.last_SMA_200 and self.last_RSI < 70 and self.cash_per_trade >= self.price * 1.01:
            return "buy"
        return "hold"

# Go through all open trades and check if current price hits stoploss
# Returns list of indices of trades that should be closed

# Execute sells for trades that hit stoploss
# Updates trade matrix and cash
    def sell_execution(self):

        if len(self.trade) > 0 and np.any(self.trade[:, 6] == 1):
            sell_mask = (
                (self.trade[:, 6] == 1) &
                (self.trade[:, 1] > self.price)
                        )
        index_list = np.where(sell_mask)[0]

        for i in range(len(index_list)):
            index = index_list[i]
            adjusted_price = self.price * 0.999  # Slippage assumption
            cash += self.trade[index, 2] * adjusted_price  # Sell value added to cash

            self.trade[index, 5] = self.date  # Exit date
            self.trade[index, 11] = adjusted_price  # Exit price
            self.trade[index, 6] = 0  # Mark trade inactive
            # Determine if trade was profitable
            if self.trade[index, 9] > self.trade[index, 8]:
                self.trade[index, 7] = 1  # Win
            else:
                self.trade[index, 7] = 0  # Loss
        return self.trade, self.cash

# Execute buexecutiony signals and update trade log accordingly

    def SMA_execution(self):
        trade, cash = self.sell_execution
        result = self.SMAtrading_conditions(self)

        if result == "buy":
            adjusted_price = self.price * 1.001  # Slippage assumption
            position = math.floor(self.cash_per_trade / adjusted_price)
            cash -= position * adjusted_price
            trade_num += 1
            buy_num += 1
            # stoploss gives price 3x atr to move 
            stoploss = round((adjusted_price - (self.last_atr * 3)), 2)

            # Create and add new trade row
            new_trade = np.zeros((1, 12), dtype=object)
            new_trade[0, 1] = stoploss             # Stoploss
            new_trade[0, 2] = position             # Shares
            new_trade[0, 3] = self.date            # Buy date
            new_trade[0, 4] = adjusted_price       # Price bought
            new_trade[0, 5] = -999                 # Exit date
            new_trade[0, 6] = 1                    # Active flag (true)
            new_trade[0, 7] = -999                 # Win flag (unknown currently)
            new_trade[0, 8] = position * adjusted_price  # Initial value
            new_trade[0, 9] = position * adjusted_price  # Current value
            new_trade[0, 10] = self.price               # Last update price
            new_trade[0, 11] = -999                # Exit price (unknown currently)

            trade = np.vstack((trade, new_trade))

        return position, trade_num, cash, buy_num, stoploss, trade

# Main strategy runner
# Handles indicator calculation, looping, trade execution, logging, and plotting
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
    data['RSI'] = calculate_rsi(data)
    data['ATR'] = calculate_atr(data, 14)

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


