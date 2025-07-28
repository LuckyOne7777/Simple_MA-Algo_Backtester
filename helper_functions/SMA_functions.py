#SMA_functions.py
import pandas as pd
import numpy as np
import time
from numba import jit 
import math
import line_profiler
from helper_functions.utils import Utils
from helper_functions.indicators import Indicators
from helper_functions.get_data import Get_Historical_Data

class SMA_Functions:

    def __init__(self, params):
        
        self.trade = np.empty((0, 12), dtype=object)
        self.cash = params.get('capital', 10_000)
        self.fastSMA = params.get('fastSMA', 50)
        self.slowSMA = params.get('slowSMA', 200)
        self.rsi_limit = params.get('rsi_limit', 60) 
        self.pos_sizing = params.get('pos_sizing', 0.05)      
        self.atr_range = params.get('atr_range', 3)
        self.ticker = params['ticker']
        self.data_type = params.get('data_type', 'YF')
# Check trading conditions: buy signal logic only
# Returns "buy" or "hold" based on indicator conditions
    def SMAbuying_conditions(self, price, last_RSI, last_sma_fast, last_sma_slow):
        cash_per_trade = self.cash * self.pos_sizing
        if last_sma_fast > last_sma_slow and last_RSI < self.rsi_limit and cash_per_trade >= price * 1.01:
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

    def trade_execution(self, price, last_RSI, last_atr, date, last_sma_fast, last_sma_slow):
        cash_per_trade = self.cash * self.pos_sizing

        self.sell_execution(price, date) # sell trades before buying
        buying_evaluation = self.SMAbuying_conditions(price, last_RSI, last_sma_fast, last_sma_slow)
        adjusted_price = price * 1.01 # slippage
        position = math.floor(cash_per_trade / adjusted_price + 1e-14)
        if buying_evaluation == "buy" and not (position == 0):
            self.cash -= position * adjusted_price
            # stoploss = adj_price - atr * atr_range
            stoploss = round(adjusted_price - (last_atr * self.atr_range), 2)

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
        new_stop = price - (self.atr_range * last_atr)

    # mask for active trades
        active_trade_mask = (self.trade[:, 6] == 1)

        update_condition_mask = (
            (self.trade[:, 6] == 1) &
            # is price at least 20% more compared to last updated price? (column 10) 
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
    def run_backtest(self):
        parameter_check(params)
        data = Get_Historical_Data.choose_data(self.ticker, self.data_type)

        print(data)
        data = data.dropna()
        if len(data) < 200:
            raise ValueError(f"Backtest needs at least 200 days and dataframe only has {len(data)}, Try increasing or checking timeframe format.")

        data['SMA_fast'] = data['close'].rolling(window=self.fastSMA).mean()
        data['SMA_slow'] = data['close'].rolling(window=self.slowSMA).mean()
        data = data.dropna()
        print(data['SMA_fast'])
        print(data['SMA_slow'])
        indicators = Indicators(data)
        data['RSI'] = indicators.calculate_rsi()
        data['ATR'] = indicators.calculate_atr()
        data = data.values
        capital = self.cash
        starting_cap = capital
        cash = capital
        portfolio_value = []
        control_portfolio_value = []
        total_position = 0
        current_year = 0
        first_price = data[0, 1]
        control_position = math.floor(starting_cap / first_price)
        num_of_years = math.ceil(len(data) / 252)
        print("Starting test, please stand by...")
        time_start = time.time()
        for i in range(len(data)):
            date = data[i, 0]
            price = data[i, 1]
            last_sma_fast = data[i, 6]
            last_sma_slow = data[i, 7]
            last_RSI = data[i, 8]
            last_atr = data[i, 9]

            self.trade_execution(price, last_RSI, last_atr, date, last_sma_fast, last_sma_slow)
            cash, trade = self.update_stoploss(price, last_atr, control_position, portfolio_value, control_portfolio_value)
            if num_of_years - current_year >= 1:
                if i % 252 == 0 and not (num_of_years - current_year == 1):
                    print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} years left.")
                    current_year += 1
                elif i % 252 == 0 and num_of_years - current_year == 1:
                    print(f"Year {current_year}: done! {math.ceil(num_of_years - current_year)} year left.")
                    current_year += 1
        end_time = time.time()
        price_data = pd.DataFrame({
            'Date': data[:, 0],
            'Price': data[:, 1]
        })
        price_df = price_data
        price_df.set_index('Date', inplace=True)
        sell_mask = trade[trade[:, 6] == 0]
        sell_points = pd.DataFrame({'X': sell_mask[:, 5], 'Y': sell_mask[:, 11]})
        buy_points = pd.DataFrame({'X': trade[:, 3], 'Y': trade[:, 4]})
        portfolio_df = pd.DataFrame({
            'Date': data[:, 0],
            'Portfolio_Value': portfolio_value
        })
        control_portfolio_df = pd.DataFrame({
            'Date': data[:, 0],
            'Control_Portfolio_Value': control_portfolio_value
        })
        portfolio_df.set_index('Date', inplace=True)
        control_portfolio_df.set_index('Date', inplace=True)
        if len(portfolio_value) == 0 or len(control_portfolio_value) == 0:
            raise ValueError("Cannot save: Empty portfolio data.")
        print(f"Program time: {round(end_time - time_start, 2)} secs")
        utils = Utils(
            portfolio_value, num_of_years, self.ticker, starting_cap,
            portfolio_df, control_portfolio_value, trade, data, capital, 
            self.data_type, buy_points, sell_points, price_df, 
            control_portfolio_df, price, last_atr, total_position, 
            cash, control_position
        )
        utils.CSV_handling()
        utils.plot_results()
def parameter_check(params):
        params_copy = params.copy()
        params_copy.pop("ticker")
        params_copy.pop("data_type")
        if 'fastSMA'and 'slowSMA' in params:
            fastSMA = params['fastSMA']
            slowSMA = params['slowSMA']  
            if fastSMA >= slowSMA:
                raise ValueError(f"fastSMA range ({fastSMA}) is greater than slowSMA range ({slowSMA}).")
        if 'pos_sizing' in params:
            pos_sizing = params['pos_sizing']      
            if pos_sizing > 1:
                raise ValueError(f"position sizing is greater than 100%.")
            
        for key, value in params_copy.items():
            if not isinstance (value, (float, int)):
                raise TypeError(f"{key} is not a number. It is currently set to {value}")
if __name__ == "__main__":
    params = {
          "ticker": "NVDA", "data_type": "YF"}
    SMA = SMA_Functions(params)
    SMA.run_backtest()