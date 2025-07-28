from helper_functions.SMA_functions import SMA_Functions
params = {"capital": 5000, "fastSMA": 10, "slowSMA": 50, 
          "rsi_limit": 60, "pos_sizing": 0.1, "atr_range": 2,
          "ticker": "NVDA", "data_type": "Alpaca"}
sma = SMA_Functions(params)
sma.run_backtest()

# === TODO ===:

    # add obscure stock symbols like "BRK.A"

# === function index ====

    # get_data.py

        # grab_Alpaca_data()
        # grab_YFdata()
        # choose_data()

    # indicators.py
        # calculate_atr()
        # calculate_rsi()

    # utils.py

        # CSV_handling()
        # line_break()
        # plot_results()

    # SMA_functions.py

        # complete_SMA_function()
        # sell_execution()
        # SMA_trading_conditions()
        # SMAtrade_execution()
        # update_stoploss()

 