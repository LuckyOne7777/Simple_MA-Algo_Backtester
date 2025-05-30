#utils.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import math
import os

def line_break():
     print("==============================================================================================")

def CSV_handling(portfolio_value, trade_num, num_of_years, ticker, starting_cap, portfolio_df, control_portfolio_value):
     #calculate stats for CSV summary
        cagr = ((portfolio_value[-1] / starting_cap) ** (1 / num_of_years) - 1) * 100
        running_max = portfolio_df['Portfolio_Value'].cummax()
        drawdown = (portfolio_df['Portfolio_Value'] - running_max) / running_max
        max_drawdown = drawdown.min()

        #DF for summary to CSV file
        summary = pd.DataFrame([{
            'symbol': ticker,
            'end_val': f"${math.floor(portfolio_value[-1]):,.0f}",
            'winner': 'Strategy' if portfolio_value[-1] > control_portfolio_value[-1] else 'Benchmark',
            'trades': f"{round(trade_num / num_of_years, 1):,.1f}",
            'cagr': f"{round(cagr, 2)}%",
            'median': f"${round(float(np.median(portfolio_value))):,.0f}",
            'average': f"${round(float(np.mean(portfolio_value))):,.0f}",
            'max_drawdown': f"{round(max_drawdown * 100, 2)}%",
            'running_max': f"${running_max.iloc[-1]:,.0f}",
            'version': "V2",
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

            line_break()
            print(summary)
            line_break()
        else:
            line_break()
            print(summary)
            line_break()
        
def plot_results(ticker, buy_points, sell_points, price_df, portfolio_df, control_portfolio_df):
            
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex= True, figsize=(10, 6))

# Plot on first subplot (ax1)
    ax1.scatter(buy_points['X'], buy_points['Y'] - 1, color = 'blue', marker = '^', s =10, label = "Buy Signal")
    ax1.scatter(sell_points['EXITDATE'], sell_points['EXIT_PRICE'] + 1, color='red', marker = 'v', s=10, label = "Sell Signal")
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

    