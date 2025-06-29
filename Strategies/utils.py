#utils.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import math
import os

def line_break():
     print("==============================================================================================")

def CSV_handling(portfolio_value, trade_num, num_of_years, ticker, starting_cap, portfolio_df, control_portfolio_value, trade, data, capital):
     #calculate stats for CSV summary
        cagr = ((portfolio_value[-1] / starting_cap) ** (1 / num_of_years) - 1) * 100
        running_max = portfolio_df['Portfolio_Value'].cummax()
        drawdown = (portfolio_df['Portfolio_Value'] - running_max) / running_max
        max_drawdown = drawdown.min()

        winning_trades = trade[trade[:, 7] == 1]
        losing_trades = trade[trade[:, 7] == 0]

        win_percent = len(winning_trades) / (len(losing_trades) + len(winning_trades) + 1e-10)

        winning_trade_start_val = winning_trades[:, 8]
        winning_trade_end_val = winning_trades[:, 9]

        losing_trade_start_val = losing_trades[:, 8]
        losing_trade_end_val = losing_trades[:, 9]

        average_capital_win = np.mean(winning_trade_end_val - winning_trade_start_val)

        average_capital_loss = np.mean(losing_trade_end_val - losing_trade_start_val)
        #DF for summary to CSV file
        summary = pd.DataFrame([{
            'symbol': ticker,
            'start': data[0, 0],
            'end': data[-1, 0],
            'start_val': f"${(capital):,.0f}",
            'end_val': f"${math.floor(portfolio_value[-1]):,.0f}",
            'winner': 'Strategy' if portfolio_value[-1] > control_portfolio_value[-1] else 'Benchmark',
            'version': "V2",
            'cagr': f"{round(cagr, 2)}%",
            'trades': f"{round(trade_num, 1):,.1f}",
            'win_%': f"{round(win_percent, 3):,.2%}",
            'avg_win':f"${round(average_capital_win):,.2f}",
            'loss_%': f"{round(1 - win_percent, 3):,.2%}",
            'avg_loss':f"-${abs(round(average_capital_loss)):,.2f}",
            'median': f"${round(float(np.median(portfolio_value))):,.0f}",
            'average': f"${round(float(np.mean(portfolio_value))):,.0f}",
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
        line_break()
        print(main_summary.to_string(index=False))
        line_break()
        print(secondary_summary.to_string(index=False))
        line_break()
        print(f"Results saved successfully! Finshed with {ticker}")

        
def plot_results(ticker, buy_points, sell_points, price_df, portfolio_df, control_portfolio_df):
            
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex= True, figsize=(10, 6))

# Plot on first subplot (ax1)
    ax1.scatter(buy_points['X'], buy_points['Y'] - 1, color = 'blue', marker = '^', s =10, label = "Buy Signal")
    ax1.scatter(sell_points['X'], sell_points['Y'] + 1, color='red', marker = 'v', s=10, label = "Sell Signal")

    ax1.plot(portfolio_df.index, price_df['Price'], color="green", alpha = 0.7)
    ax1.set_ylabel('Price')
    ax1.set_title('Price Chart')
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.2f}'))
    ax1.grid(True)
    ax1.legend()


    # Plot on second subplot (ax2)
    ax2.plot(portfolio_df.index, portfolio_df['Portfolio_Value'], label="Strategy Portfolio Value")
    ax2.plot(control_portfolio_df.index, control_portfolio_df['Control_Portfolio_Value'], label=f"Benchmark", color ="orange")
    ax2.set_ylabel('Portfolio Value')
    ax2.set_xlabel('Date')
    ax2.set_title(f'Backtest Results for {ticker}')
    ax2.ticklabel_format(style='plain', axis='y')
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax2.grid(True)
    ax2.legend()

    plt.show()
    
def update_stoploss(trade, price, last_atr, total_position, portfolio_value, control_portfolio_value, cash, control_position):
 #make a mask to filter through inactive trades and run loop over mask
    total_position = 0
    new_stop = price - (3 * last_atr)
    #mask for still active trades
    active_trade_mask = (trade[:, 6] == 1)

    update_condition_mask = (
         (trade[:, 6] == 1) & 
         (trade[:, 10] * price >=  1.2 ) & 
         (trade[:,1] < new_stop ))

    if len(trade) > 0:
        if np.any(trade[:, 6] == 1):
            total_position = trade[active_trade_mask, 2].sum()
            trade[active_trade_mask, 9] = (trade[active_trade_mask, 2] * price).astype(int)

            #conditional for updating stoploss:

            stoploss = new_stop
            trade[update_condition_mask, 10] = price
            trade[update_condition_mask, 1] = stoploss
            total_value = total_position * price + cash
            
            total_control_value = control_position * price
            portfolio_value.append(total_value)
            control_portfolio_value.append(total_control_value)
        elif np.all(trade[:, 6] == 0):
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