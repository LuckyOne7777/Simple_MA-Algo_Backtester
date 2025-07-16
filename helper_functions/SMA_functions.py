#SMA_functions.py
import pandas as pd
import numpy as np
import time
from numba import jit 
import math
import line_profiler
from helper_functions.utils import Utils, update_stoploss
from helper_functions.indicators import Indicators
from helper_functions.get_data import Get_Historical_Data

class SMA_Functions:

    def __init__(self, trade, cash):
        
        self.trade = trade
        self.cash = cash
        
        
# Check trading conditions: buy signal logic only
# Returns "buy" or "hold" based on indicator conditions
    def SMAbuying_conditions(self, price, last_SMA_50, last_SMA_200, last_RSI):
        cash_per_trade = self.cash * 0.05
        if last_SMA_50 > last_SMA_200 and last_RSI < 70 and cash_per_trade >= price * 1.01:
            return "buy"
        return "hold"
    # check and execute selling trades
    def sell_execution(self, price, date):
        if len(self.trade) > 0 and np.any(self.trade[:, 6] == 1):
            sell_mask = (
                (self.trade[:, 6] == 1) & # mask for active trades (col 6)
                (self.trade[:, 1] > price) # and check if price is less than stoploss (col 1)
            )
            sell_index_list = np.where(sell_mask)[0]
            # exit trades for all trades that meet sell conditions
            for sell_index in sell_index_list:
                adjusted_price = price * 0.99  # Slippage
                self.cash += self.trade[sell_index, 2] * adjusted_price # cash = position * adjusted_price

                self.trade[sell_index, 5] = date # exit date
                self.trade[sell_index, 11] = adjusted_price # exit price
                self.trade[sell_index, 6] = 0  # set active status to 0

                # Win condition, col 9 is the end value and col 8 is start value
                if self.trade[sell_index, 9] > self.trade[sell_index, 8]:
                # was the trade profitable? set 1 for true and 0 for false
                    self.trade[sell_index, 7] = 1
                else:
                    self.trade[sell_index, 7] = 0

    def trade_execution(self, price, last_SMA_50, last_SMA_200, last_RSI, last_atr, date):
        cash_per_trade = self.cash * 0.05
        self.sell_execution(price, date)
        buying_evaluation = self.SMAbuying_conditions(price, last_SMA_50, last_SMA_200, last_RSI)
        adjusted_price = price * 1.01 # slippage
        position = math.floor(cash_per_trade / adjusted_price + 1e-14)
        if buying_evaluation == "buy" and not (position == 0):
            self.cash -= position * adjusted_price
            # stoploss = adj_price - atr * 3
            stoploss = round(adjusted_price - (last_atr * 3), 2)
            # -999 is unknown value, 1 is true and 0 is false.
            # I plan to make a dates array (so it won't be dtype=object) for speed
            new_trade = np.zeros((1, 12), dtype=object)
            new_trade[0, 1] = stoploss # stoploss
            new_trade[0, 2] = position # position
            new_trade[0, 3] = date # date
            new_trade[0, 4] = adjusted_price # buying price  
            new_trade[0, 5] = -999 # exit date (unknown)
            new_trade[0, 6] = 1  # Is it active? 
            new_trade[0, 7] = -999 # was the trade profitable? (unknown)
            new_trade[0, 8] = position * adjusted_price # starting trade val
            new_trade[0, 9] = position * adjusted_price # current trade val
            new_trade[0, 10] = price # last updated price (or buying price for no updates)
            new_trade[0, 11] = -999 # exitprice (unknown)

            self.trade = np.vstack((self.trade, new_trade))
    def update_stoploss(self, price, last_atr, control_position, portfolio_value, control_portfolio_value):
        total_position = 0
        new_stop = price - (3 * last_atr)

    # mask for active trades
        active_trade_mask = (self.trade[:, 6] == 1)

        update_condition_mask = (
            (self.trade[:, 6] == 1) &
            # is price at least 20% more compared to last updated price (column 10)? 
            (price >= self.trade[:, 10] * 1.2) & 
            (self.trade[:, 1] < new_stop)
                                )

        if len(self.trade) > 0:
            if np.any(active_trade_mask):
                total_position = self.trade[active_trade_mask, 2].sum()
                self.trade[active_trade_mask, 9] = (self.trade[active_trade_mask, 2] * price).astype(int)

        # update stoploss if condition is met
                stoploss = new_stop
                self.trade[update_condition_mask, 10] = price
                self.trade[update_condition_mask, 1] = stoploss

            total_value = total_position * price + self.cash
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)

        else:
            total_value = total_position * price + self.cash
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)

        return self.cash, self.trade

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
    cash = capital
    portfolio_value = []
    control_portfolio_value = []
    price_data = []
    total_position = 0
    current_year = 0
    first_price = data[0, 1] # col 1 is dates
    control_position = math.floor(starting_cap / first_price)
    # there are 252 trading days in a year
    num_of_years = math.ceil(len(data) / 252)

    print("Starting test, please stand by...")
    time_start = time.time()
    SMA = SMA_Functions(trade, cash)
    for i in range(len(data)):
        date = data[i, 0] # date col
        price = data[i, 1] # price col
        last_SMA_50 = data[i, 6] # 50 SMA col
        last_SMA_200 = data[i, 7] # 200 SMA col
        last_RSI = data[i, 8] # RSI col
        last_atr = data[i, 9] # ATR col
        active_trade_mask = trade[trade[:, 6] == 1]
        trading_val = active_trade_mask[:, 9].sum() 
        if i % 50 == 0 or i == len(data) - 1:
        
            print(f"{i}/{len(data)}: {date}, price: {price:.2f}, cash: {cash:,.2f}, money in trades: {trading_val}")


        SMA.trade_execution(price, last_SMA_50, last_SMA_200, last_RSI, last_atr, date)


        cash, trade = SMA.update_stoploss( price, last_atr, control_position, 
                        portfolio_value, control_portfolio_value)

        if num_of_years - current_year >= 1:
            if i % 252 == 0 and not (num_of_years - current_year == 1):
                print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} years left.")
                current_year += 1
            elif i % 252 == 0 and num_of_years - current_year == 1:
                print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} year left.")
                current_year += 1

    end_time = time.time()

    price_data = pd.DataFrame({
        'Date': data[:, 0], # date col
        'Price': data[:, 1]  # price col
    })
    price_df = price_data
    price_df.set_index('Date', inplace=True)

    sell_mask = trade[trade[:, 6] == 0]  # col for checking if trade exited
    #col 5 is exit date, 11 is exit price
    sell_points = pd.DataFrame({'X': sell_mask[:, 5], 'Y': sell_mask[:, 11]})
    # col 3 is buy date, 4 is buy price
    buy_points = pd.DataFrame({'X': trade[:, 3], 'Y': trade[:, 4]})  # Buy signals (no need for mask)

    # create DataFrames for both portfolio and control portfolio for plotting
    portfolio_df = pd.DataFrame({
        'Date': data[:, 0], # date col
        'Portfolio_Value': portfolio_value
    })

    control_portfolio_df = pd.DataFrame({
        'Date': data[:, 0], # date col
        'Control_Portfolio_Value': control_portfolio_value
    })

    portfolio_df.set_index('Date', inplace=True)

    control_portfolio_df.set_index('Date', inplace=True)

    if len(portfolio_value) == 0 or len(control_portfolio_value) == 0:
        raise ValueError("Cannot save: Empty portfolio data.")
    
    print(f"Program time: {round(end_time - time_start, 2)} secs")

    utils = Utils(
        portfolio_value, num_of_years, ticker, starting_cap,
        portfolio_df, control_portfolio_value, trade, data, capital, 
        user_data_choice, buy_points, sell_points, price_df, 
        control_portfolio_df, price, last_atr, total_position, 
        cash, control_position
            )

    utils.CSV_handling()

    utils.plot_results()


if __name__ == "__main__":
    complete_SMA_function()