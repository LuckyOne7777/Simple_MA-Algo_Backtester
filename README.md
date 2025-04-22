README.md

# Simple Trading Algo Backtest

Hello, thanks for checking out my project! I'm just a high school student who's new to Coding and experimenting with stock trading algorithms. This is my attempt at creating a somewhat passable algo using a basic moving average crossover strategy.

---

##  Background
This was my **first real Python project** — and also my first attempt at algorithmic trading. I am aware that moving averges are basic and usually ineffective compared to other models. 

The goal was just to:
- be familar with data manuplation and common Python libraries
- Learn how to fetch and manipulate stock data
- Backtest simple strategies using logic like:
  - 
  - 50/200 SMA crossovers
  - RSI filtering
  - ATR-based stop-loss
- Track trades, portfolio value, and compare to a benchmark (buy & hold)

---
## Requirements
  to run the files, you will need the following libraries (you should have all of them):
    yfinance
    pandas
    numpy
    matplotlib.pyplot

## What's Inside

- `backtesting.py`:  
  My first-ever algo! Super messy, but it works.
  Not planning on making changes, only to the current V2 

  Trades based on SMA, RSI, Includes:
  - Moving Average Crossover (50/200)
  - backtesting potential of any stock from yf
  - matlib plot of results
  - summary to CSV file
  - Portfolio tracking
  - Benchmark comparison

- `backtesting sp500.py`:
  pretty much the same algo as above, however loops through every S&P 500 stock and saves results

  - `MA_backtest.csv`:  
  Outputs summary stats of the `backtesting.py` (planning to have a singular CSV file)
---

-`backtesting v2.py`
  exactly how it sounds, second attempt at a trading algo based on the last one
  still refactoring and refining this one
  includes:
    many minor coding fixes for performance
    dynamic ATR stop-loss
    actual postion sizing for trades
    trade DataFrame to track and manange multiple trades at once

-`MA_backtestingV2.py`
  CSV file for V2


## Notes

- This is mainly a **learning exercise**, not financial advice.
- I know it’s not optimal — but that’s the point: Just learning and experimenting.
- Planning to refactor into a modular framework later.

---

## Future Plans

  I plan to expand my V2, here are some of my following ideas:

  reduce maxdrawdowns and refine logic
  centralized and more detailed CSV file
  Converting algo into a modular framework



## Why I'm Sharing This

I want to track my growth and maybe help someone else just getting started.  
Eventually, I hope to improve this and build smarter models using more advanced indicators or even ML.

If you’re reading this and have advice or critiques, feel free to open an issue or shoot me a message!

---

## Contact

Just open an issue or leave a comment.

I’d love to hear your thoughts or potentially work on this with someone.

Thanks for reading! 

Gmail: nathanbsmith729@gmail.com
