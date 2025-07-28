

def parameter_check(params):
        params_copy = params.copy()
        if 'ticker' not in params:
            raise ValueError("missing vital key 'ticker'. ")
        params_copy.pop("ticker")
        if 'data_type' in params:
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
        print("Parameters are verified!")
