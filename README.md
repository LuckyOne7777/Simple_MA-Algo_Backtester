# Simple Trading Algo Backtest

Hi! Thanks for checking out my project. I'm a high school student who's just starting out with coding and experimenting with stock trading algorithms. This is a very simple backtesting engine with a Simple Moving Average (so far). Ignore some of my first commit messages, was still getting used to GitHub (I'll try to fix them using rebase later).

---

## Background

This was my **first real Python project** — and also my first attempt at algorithmic trading. I know moving averages are basic and ineffective compared to more advanced models, but the goal here was to:

- Get familiar with data manipulation and common Python libraries
- Learn how to fetch and process stock data
- Backtest simple strategies using logic like:
  - 50/200 SMA crossovers
  - RSI filtering
  - ATR-based stop-loss
- Track trades, monitor portfolio value, and compare to a benchmark (buy & hold)

---

## Requirements

To run the files, you'll need the following libraries:

- `yfinance`
- `pandas`
- `numpy`
- `matplotlib`
- `alpaca-py`
- `lxml`

You can install them with:
```bash
pip install yfinance pandas numpy matplotlib alpaca-py lxml
```
---

## What's Inside

### `Strategies Folder`
Many of the files are just for function calls, the important one is `main.py`. To see the code, look inside `SMA_Stratgies.py`.

  ### `main.py`
  
  The second version of my strategy, currently being refined and improved. Major updates so far include:

  - Cleaner, faster code
  - Dynamic ATR-based stop-loss
  - Position sizing
  - Trade tracking with a dedicated DataFrame
  - Benchmark and portfolio performance over time
  - graph of buy and sell signals
  - modularized functions
    
  Once you start the program, you will have the option to choose between YahooFinance and Alpaca for historical data. To use Alpaca's data, you will need to have an Alpaca API key: `ALPACA_SECRET_KEY` and Alpaca   secret key: `ALPACA_SECRET_KEY` in your system's environmental varibles. If this is an issue, using YahooFinance is an easy alternative.

---
### `Archive` folder 
Inside, you will find some older stratgies I created first. To make any changes to the ticker or timeframe, you will have to edit the file. I'm not planning on updating them - just keeping them as reference.

  ### `backtesting.py`
  My first-ever algo! It's a bit messy, but it works somewhat.
  
  Trades based on:
  - 50/200 Moving Average Crossover
  - RSI filtering
  - Backtests using `yfinance` data
  - Visualizes results with matplotlib
  - Saves summary stats to CSV
  - Tracks portfolio value and compares to a buy-and-hold benchmark

---

  ### `backtesting sp500.py`
  Runs the same strategy as above, however runs a loop across all S&P 500 tickers and saves a summary of each backtest to the CSV file.

---
### `Data Folder`

Just an experimental idea I'm trying to store free data from YF so I won't have to download everytime.

---

## Notes

- This is **strictly a learning exercise** — far from a solid trading strategy (it kinda sucks). 
- I know it isn't perfect, but it's part of the process!

---

## Future Plans

Here’s what I would like to do next:

- Refine the current logic and filters
- Improve the structure of CSV outputs
- Explore more advanced indicators and maybe even ML in the future
- Create more strategies when I'm finished working on Moving-Averages

---

## Why I'm Sharing This

I want to document my progress and maybe help someone else who's just getting started.  
Eventually, I hope to turn this into something more powerful — and learn along the way.

If you’re reading this and have feedback, feel free to open an issue or reach out!

---

## Contact

I'd love to hear your thoughts or maybe even collaborate on this with someone!

**Gmail:** nathanbsmith729@gmail.com

