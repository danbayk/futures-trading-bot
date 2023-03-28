from kucoin.client import Client
from dotenv import load_dotenv
from datetime import datetime
from datetime import timezone
import pandas as pd
from ta.trend import ema_indicator
from ta.momentum import stochrsi, stochrsi_k, stochrsi_d
import time
import os

# Convert unix timestamp to date
# print(datetime.utcfromtimestamp(round(date_time1.replace(tzinfo=timezone.utc).timestamp())))

# print(client.get_kline_data('ETH-USDT', '1hour', round(date_time1.replace(tzinfo=timezone.utc).timestamp()), round(time.time())))
# print(round(time.time()))

load_dotenv()
client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'), os.getenv('API_PASSPHRASE'))

date_time1 = datetime(2023, 1, 2)
date_time2 = datetime(2023, 3, 5, 1)
# print(date_time1)
# print(datetime.utcfromtimestamp(round(date_time1.replace(tzinfo=timezone.utc).timestamp())))

bars = client.get_kline_data('ETH-USDT', '1hour', round(date_time1.replace(tzinfo=timezone.utc).timestamp()), round(time.time()))
df = pd.DataFrame(bars, columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])

price_current = pd.to_numeric(df.iloc[::-1]['close'])[0]
ema_200 = ema_indicator(pd.to_numeric(df.iloc[::-1]['close']), 200, False)
sma_9 = ema_indicator(pd.to_numeric(df.iloc[::-1]['close']), 17, False)
rsi_k_current = stochrsi_k(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[0]
rsi_d_current = stochrsi_d(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[0]
rsi_k_trailing = stochrsi_k(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[1]
rsi_d_trailing = stochrsi_d(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[1]

# Buying conditions
def kupward():
    return (((rsi_k_current - rsi_k_trailing) > 0.045) and (rsi_k_current > rsi_d_current) and (rsi_k_current > 0.50))

def smaupward():
    return (sma_9[0] - sma_9[1]) > 1

def priceup():
    return ((price_current > ema_200[0]) and (price_current > sma_9[0]) and (sma_9[0] > ema_200[0]))