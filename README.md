## Table of Contents
- [Background](##background)
- [Installation](##installation)
- [Setup](##setup)
- [Usage](##usage)
- [What's Inside](##whats-inside)
- [Credits](##credits-and-contact)


# Simple Trading Algo Backtest

Hi! Thanks for checking out my project. I'm a high school student who's just starting out with coding and experimenting with stock trading algorithms. This is my first attempt at building a somewhat passable algo using a basic moving average crossover strategy.

*Ignore some of my first commit messages, I was still getting used to GitHub lol.*

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

## Installation

Download and extract zip, or clone the project:
```bash
git clone https://github.com/LuckyOne7777/Simple_MA-Algo_Backtester.git
```
Move into the project directory:
```bash
cd Simple_MA-Algo_Backtester/
```

---

## Setup

To run the files, you'll need the following (very basic) libraries:

- yfinance
- pandas
- numpy
- matplotlib
- alpaca-py
- lxml

You should use a virtual python environment to avoid installing the dependencies globally. Make sure you are in the main project folder, then you can run this:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This will bring you into a virtual environment, then install all the dependencies for the project.

---

## Usage

You can view and run the main scripts in ./Strategies/

If you haven't already, make sure you set up a python environment for your session, or the dependencies you installed won't load.

In the root folder of the project:
```bash
source .venv/bin/activate
```

Then run a script using python. Example:
```bash
python backtesting\ v2.py
```

To run V2, you will need to have these Alpaca API keys set as environment varibles:
- API_KEY
- SECRET_KEY

Register an Alpaca account here: https://app.alpaca.markets/signup

If this is an issue, you can run `backtestingV2 (no keys).py` for the same result.

---

## What's Inside

### `backtesting.py`
My first-ever algo! It's a bit messy, but it works somewhat.

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
Runs the same strategy as above, however runs a loop across all S&P 500 tickers and saves a summary of each backtest to the CSV file.

---

### `backtesting v2.py`
The second version of my strategy, currently being refined and improved. Major updates so far include:

- Cleaner, faster code
- Dynamic ATR-based stop-loss
- Position sizing
- Trade tracking with a dedicated DataFrame
- Benchmark and portfolio performance over time

---

### `backtestingV2 (no keys).py`

Exactly how it sounds, same as version 2 but Alpaca keys aren't necessary.

---

### `Data Folder`

Just an experimental idea I'm trying to store free data from YF so I won't have to download everytime.

---

## Notes

- This is **strictly a learning exercise** — far from a solid trading strategy.
- I know it isn't perfect, but it's part of the process!

Here’s what I would like to do next:

- Refine the current logic and filters
- Improve the structure of CSV outputs
- Create a modular framework for running and testing strategies
- Explore more advanced indicators and maybe even ML in the future
- Create more strategies when I'm finished working on Moving-Averages

I want to document my progress and maybe help someone else who's just getting started.
Eventually, I hope to turn this into something more powerful — and learn along the way.

If you’re reading this and have feedback, feel free to open an issue or reach out!

And in case anyone was curious, I definitely didn't use ChatGPT to generate most of this readMe file, I definitely bothered to learn the syntax and spent hours writing this whole thing for everyone, because my heart is so huge and filled with love for all of the people I don't know!

---

## Credits and Contact

#### Project Owner/Manager: LuckyOne7777

I'd love to hear your thoughts or maybe even collaborate on this with someone!

**Gmail:** nathanbsmith729@gmail.com

#### Useless helper: Heisenward

This is me i get the last line
