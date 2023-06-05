# Momentum-based futures trading bot
## Overview
A momentum-based crypto trading bot trading the ETH-USDT trading pair on Kucoin.
## Bot Scripts
Bot scripts located in `/live-bot-scripts` folder.
 To setup and run the trading bot (assuming Python and pip are already installed):
 1. Create an account on [kucoin.com](kucoin.com)
 2. Get a trading API key for **futures trading.**
 3. Create a `.env` file in the root directory and include the following three variables obtained from the futures API (single quotes around string values):
````
API_KEY_FUTURES=<YOUR API KEY>
API_SECRET_FUTURES=<YOUR API SECRET>
API_PASSPHRASE_FUTURES=<YOUR API PASSPHRASE>
````
4. Deposit/move funds into Kucoin futures trading account.
5. Run `pip install -r requirements.txt` to install required Python modules.
6. To run the bot: `python bot.py` (most recent version). Modifiable leverage, set to 1 by default.
## Backtesting Scripts and Trading Strategies Overview
**Backtesting scripts:**
Backtesting scripts are located in `/backtesting-scripts` folder. Each has a source file which can be replaced with any of the `.csv` files located in the `/charts` folder. Backtesting programs use the candle close price as the entry, the trading bot does the same for similar backtest performance. `rsi_macd.py` has code for minute-by-minute price within a larger timeframe for realistic market entires/exits.
**Trading strategies overview:**
1. `rsi_macd.py`:
This is a momentum-based strategy that uses SMA and Stochastic RSI for entries and MACD for exits. Can be run on all timeframes but is still a work in progress due to poor performance during periods of consistent downtrends.
2. `rsi_sma.py`:
This is a momentum-based strategy that uses SMA and Stochastic RSI for both entires and exits. This is currently the best-performing strategy on the 4h timeframe.
3. `ichimoku.py`:
This is a backtest for the Ichimoku Cloud trading strategy.
4. `intra_candle_backtest.py`:
This is a backtest for `rsi_sma.py` which takes entries and exits that are unbound by the close price, looping through all 1min price data within a larger time frame. See code comments for detailed usage.
# Misc Scripts
The `/misc-scripts` folder contains chart generating programs.
1. `pandas-to-csv.py`:
This is a program used to generate charts for any timeframe and date range. Uses Kucoin historical kline data and produces a `.csv` file which can be used in the backtesting scripts.
# Future updates
1. Switch to websockets for live price data.
2. Add portfolio risk management (currently fullports entire futures balance).
3. Clean up code/uneeded files and modules.
