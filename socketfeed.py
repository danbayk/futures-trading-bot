from kucoin.client import Client
from kucoin_futures.client import Trade
from kucoin_futures.client import User
from kucoin.asyncio import KucoinSocketManager
from dotenv import load_dotenv
from ta.trend import ema_indicator
from ta.momentum import stochrsi_k, stochrsi_d
import pandas as pd
from datetime import datetime
from datetime import timezone
import asyncio
import time
import os

load_dotenv()

# Market API
marketClient = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'), os.getenv('API_PASSPHRASE'))

# Futures API
# ----- REAL API -----
api_key = os.getenv('API_KEY_FUTURES')
api_secret = os.getenv('API_SECRET_FUTURES')
api_passphrase = os.getenv('API_PASSPHRASE_FUTURES')

tradeClient = Trade(key = api_key, secret = api_secret, passphrase = api_passphrase, is_sandbox = False)
userClient = User(api_key, api_secret, api_passphrase)

balance = userClient.get_account_overview('USDT')['availableBalance']
buyAmt = int((balance/float(marketClient.get_ticker('ETH-USDT')['price']))/0.01)
print(buyAmt*5)