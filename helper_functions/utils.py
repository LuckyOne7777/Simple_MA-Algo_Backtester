#utils.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import math
import os
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

#generate the defination for simple python classes (may expand on this)
def class_generator(*args, **kwargs):
    vars = args
    var_list = ", ".join(args)
    class_name = kwargs.get("name", "(class name)")
    print(f"""class {class_name}:

    def __init__({var_list}):""")
    for varible in vars:
        print(f"        self.{varible} = {varible}")

class Utils:

    def __init__(self, portfolio_value, trade_num, num_of_years, ticker, starting_cap,
             portfolio_df, control_portfolio_value, trade, data, capital, 
             user_data_choice, buy_points, sell_points, price_df, 
             control_portfolio_df, price, last_atr, total_position, 
            cash, control_position):
        
        self.portfolio_value = portfolio_value
        self.trade_num = trade_num
        self.num_of_years = num_of_years
        self.ticker = ticker
        self.starting_cap = starting_cap
        self.portfolio_df = portfolio_df
        self.control_portfolio_value = control_portfolio_value
        self.trade = trade
        self.data = data
        self.capital = capital
        self.user_data_choice = user_data_choice
        self.buy_points = buy_points
        self.sell_points = sell_points
        self.price_df = price_df
        self.control_portfolio_df = control_portfolio_df
        self.price = price
        self.last_atr = last_atr
        self.total_position = total_position
        self.cash = cash
        self.control_position = control_position
    @staticmethod
    def line_break():
        print("=" * 94)
    @staticmethod
    def print_head():
        print(" " + "=" * 37 + " BACKTEST RESULTS " + "=" * 37 + " ")

    def CSV_handling(self):
     #calculate stats for CSV summary
        cagr = ((self.portfolio_value[-1] / self.starting_cap) ** (1 / self.num_of_years) - 1) * 100
        running_max = self.portfolio_df['Portfolio_Value'].cummax()
        drawdown = (self.portfolio_df['Portfolio_Value'] - running_max) / running_max
        max_drawdown = drawdown.min()
        #include winning trades in the count
        active_trade_indexes = np.where(self.trade[:, 6] == 1)[0]
        for index in active_trade_indexes:
            if self.trade[index, 9] > self.trade[index, 8]:
                self.trade[index, 7] = 1
            else:
                self.trade[index, 7] = 0

        winning_trades = self.trade[self.trade[:, 7] == 1]
        losing_trades = self.trade[self.trade[:, 7] == 0]
        print(winning_trades)
        print(losing_trades)
            
        win_percent = len(winning_trades) / (len(losing_trades) + len(winning_trades) + 1e-10)

        winning_trade_start_val = winning_trades[:, 8]
        winning_trade_end_val = winning_trades[:, 9]

        losing_trade_start_val = losing_trades[:, 8]
        losing_trade_end_val = losing_trades[:, 9]
        # add checks incase no trades were ever made
        average_capital_win = np.mean(winning_trade_end_val - winning_trade_start_val)
        if math.isnan(average_capital_win):
            average_capital_win = 0

        average_capital_loss = np.mean(losing_trade_end_val - losing_trade_start_val)
        if math.isnan(average_capital_loss):
            average_capital_loss = 0
        #DF for summary to CSV file
        summary = pd.DataFrame([{
            'symbol': self.ticker,
            'start': self.data[0, 0],
            'end': self.data[-1, 0],
            'start_val': f"${(self.capital):,.0f}",
            'end_val': f"${math.floor(self.portfolio_value[-1]):,.0f}",
            'winner': 'Strategy' if self.portfolio_value[-1] > self.control_portfolio_value[-1] else 'Benchmark',
            'version': "V2",
            'cagr': f"{round(cagr, 2)}%",
            'trades': f"{round(self.trade_num, 1):,.1f}",
            'win_%': f"{round(win_percent, 3):,.2%}",
            'avg_win':f"${round(average_capital_win):,.2f}",
            'loss_%': f"{round(1 - win_percent, 3):,.2%}",
            'avg_loss':f"-${abs(round(average_capital_loss)):,.2f}",
            'median': f"${round(float(np.median(self.portfolio_value))):,.0f}",
            'average': f"${round(float(np.mean(self.portfolio_value))):,.0f}",
            'max_drawdown': f"{round(max_drawdown * 100, 2)}%",
            'running_max': f"${running_max.iloc[-1]:,.0f}",
        }])

        ALL_COLUMNS = [
            'symbol',
            'start',
            'end',
            'start_val',
            'end_val',
            'winner',
            'version',
            'cagr',
            'trades',
            'win_%',
            'avg_win',
            'loss_%',
            'avg_loss',
            'median',
            'average',
            'max_drawdown',
            'running_max',
        ]
        
        user_CSV_preference = input("Would you like to save results to CSV? (y/n) ")
        if user_CSV_preference == "y":
            print("Saving results...")
        #make sure folder exists
            output_folder = "CSV files"
            os.makedirs(output_folder, exist_ok=True)

            file_path = os.path.join(output_folder, "MA_backtest.csv")

            if os.path.exists(file_path):
                df_existing = pd.read_csv(file_path)

    # Append new summary
                df_updated = pd.concat([df_existing, summary], ignore_index=True)

    # Drop duplicates by 'symbol' and 'version' if needed
                df_updated.drop_duplicates(subset=["symbol", "version"], keep="last", inplace=True)

    # Save it back
                df_updated.to_csv(file_path, index=False, columns=ALL_COLUMNS)
            else:
                summary.to_csv(file_path, index=False, columns=ALL_COLUMNS)

        main_summary = summary.iloc[:, :8]
        secondary_summary = summary.iloc[:, 8:]
        Utils.print_head()
        Utils.line_break()
        print(main_summary.to_string(index=False))
        Utils.line_break()
        print(secondary_summary.to_string(index=False))
        Utils.line_break()
        print(f"Results saved successfully! Finshed with {self.ticker}")
        if self.user_data_choice == "1":
            print("Note: Alpaca data may not account for stock splits. This may lead to misleading results.")

        
    def plot_results(self):

        plt.style.use('dark_background')
            
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex= True, figsize=(10, 6))

# Plot on first subplot (ax1)
        ax1.scatter(self.buy_points['X'], self.buy_points['Y'] - 1, color = 'blue', marker = '^', s =10, label = "Buy Signal")
        ax1.scatter(self.sell_points['X'], self.sell_points['Y'] + 1, color='red', marker = 'v', s=10, label = "Sell Signal")

        ax1.plot(self.portfolio_df.index, self.price_df['Price'], color="white")
        ax1.set_ylabel('Price')
        ax1.set_title('Price Chart')
        ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.2f}'))
        ax1.grid(True)
        ax1.legend()


    # Plot on second subplot (ax2)
        ax2.plot(self.portfolio_df.index, self.portfolio_df['Portfolio_Value'], label="Strategy Portfolio Value", color="orange")
        ax2.plot(self.control_portfolio_df.index, self.control_portfolio_df['Control_Portfolio_Value'], label=f"Benchmark", color ="green")
        ax2.set_ylabel('Portfolio Value')
        ax2.set_xlabel('Date')
        ax2.set_title(f'Backtest Results for {self.ticker}')
        ax2.ticklabel_format(style='plain', axis='y')
        ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
        ax2.grid(True)
        ax2.legend()

        plt.show()
    
def update_stoploss(trade, price, last_atr, cash, control_position, portfolio_value, control_portfolio_value):
        total_position = 0
        new_stop = price - (3 * last_atr)

    # mask for active trades
        active_trade_mask = (trade[:, 6] == 1)

        update_condition_mask = (
            (trade[:, 6] == 1) & 
            (trade[:, 10] * price >= 1.2) & 
            (trade[:, 1] < new_stop)
                                )

        if len(trade) > 0:
            if np.any(active_trade_mask):
                total_position = trade[active_trade_mask, 2].sum()
                trade[active_trade_mask, 9] = (trade[active_trade_mask, 2] * price).astype(int)

            # update stoploss if condition is met
                stoploss = new_stop
                trade[update_condition_mask, 10] = price
                trade[update_condition_mask, 1] = stoploss

            total_value = total_position * price + cash
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)

        else:
            total_value = total_position * price + cash
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)

        return trade