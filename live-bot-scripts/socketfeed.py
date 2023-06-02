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
import traceback
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
frameLen = 0
while True:
    while True:
        try:
            # Request large enough data set for accurate indicators and create dataframe
            df = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '1min', 
                                            round(datetime(2023, 5, 10).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(time.time())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])
            break
        except:
            time.sleep(11)
            traceback.print_exc()
            pass
    print(frameLen, len(df))
    print((frameLen != len(df) and frameLen != 0))
    frameLen = len(df)
    time.sleep(5)