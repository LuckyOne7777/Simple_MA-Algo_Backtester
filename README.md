# Simple Trading Algo Backtest

Hi there! Thanks for checking out my project. I'm a high school student who's just starting out with coding and experimenting with stock trading algorithms. This is my first attempt at building a somewhat passable algo using a basic moving average crossover strategy.

---

## Background

This was my **first real Python project** — and also my first attempt at algorithmic trading. I know moving averages are basic and often ineffective compared to more advanced models, but the goal here was to:

- Get familiar with data manipulation and common Python libraries
- Learn how to fetch and process stock data
- Backtest simple strategies using logic like:
  - 50/200 SMA crossovers
  - RSI filtering
  - ATR-based stop-loss
- Track trades, monitor portfolio value, and compare to a benchmark (buy & hold)

---

## Requirements

To run the files, you'll need the following (very basic) libraries:

- `yfinance`
- `pandas`
- `numpy`
- `matplotlib`

You can install them with:
```bash
pip install yfinance pandas numpy matplotlib
```

---

## What's Inside

### `backtesting.py`
My first-ever algo! It's a bit messy, but it works.

Trades based on:
- 50/200 Moving Average Crossover
- RSI filtering
- Backtests using `yfinance` data
- Visualizes results with matplotlib
- Saves summary stats to CSV
- Tracks portfolio value and compares to a buy-and-hold benchmark

> Not planning to update this file — keeping it as my original version for reference.

---

### `backtesting sp500.py`
Runs the same strategy as above, however runs a loop across all S&P 500 tickers and saves a summary of each backtest.

---

### `backtesting v2.py`
The second version of my strategy, currently being refined and improved. Major updates so far include:

- Cleaner, faster code
- Dynamic ATR-based stop-loss
- Position sizing
- Trade tracking with a dedicated DataFrame
- Benchmark and portfolio performance over time

---

## Notes

- This is **strictly a learning exercise** — far from a solid trading strategy.
- I know the algo isn't perfect, but that’s part of the process!
- 

---

## Future Plans

Here’s what I would like to do next:

- Refine the current logic and filters
- Improve the structure of CSV outputs
- Create a modular framework for running and testing strategies
- Explore more advanced indicators and maybe even ML in the future

---

## Why I'm Sharing This

I want to document my progress and maybe help someone else who's just getting started.  
Eventually, I hope to turn this into something more powerful — and learn a ton along the way.

If you’re reading this and have feedback, feel free to open an issue or reach out!

---

## Contact

Feel free to reach out — I'd love to hear your thoughts or maybe even collaborate on this with someone!

**Gmail:** nathanbsmith729@gmail.com

