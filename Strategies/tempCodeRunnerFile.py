ax1.plot(portfolio_df.index, price_df['Price'])
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Price ($)')
        ax1.set_title('Price Chart')
        ax1.grid(True)


    # Plot on second subplot (ax2)
        ax2.plot(portfolio_df.index, portfolio_df['Portfolio_Value'], label="Strategy Portfolio Value")
        ax2.plot(control_portfolio_df.index, control_portfolio_df['Control_Portfolio_Value'], label=f"Benchmark", linestyle="dashed")
        ax2.set_ylabel('Portfolio Value ($)')
        ax2.set_xlabel('Date')
        ax2.set_title(f'Backtest Results for {ticker}')
        ax2.grid(True)
