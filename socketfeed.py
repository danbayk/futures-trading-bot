from kucoin.client import Client
from kucoin_futures.client import Trade
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
# ----- SANDBOX API -----
# api_key = os.getenv('API_KEY_SANDBOX')
# api_secret = os.getenv('API_SECRET_SANDBOX')
# api_passphrase = os.getenv('API_PASSPHRASE_SANDBOX')
tradeClient = Trade(key = api_key, secret = api_secret, passphrase = api_passphrase, is_sandbox = False)

# print(tradeClient.get_open_order_details('ETHUSDTM'))

takeProfit = 25
stopLoss = 15

class currentPosition:
    inPosition = False
    buyPrice = 0
    TP = 0
    SL = 0

def kupward(rsi_k_current, rsi_k_trailing, rsi_d_current):
    return (((rsi_k_current - rsi_k_trailing) > 0.05) and 
            (rsi_k_current > rsi_d_current) and 
            (rsi_k_current > 0.5))

def smaupward(sma_9_current, sma_9_trailing):
    return (sma_9_current - sma_9_trailing) > 0.9

def priceup(price_current, ema_200_current, sma_9_current):
    return ((price_current > ema_200_current) and 
            (price_current > sma_9_current) and 
            (sma_9_current > ema_200_current))
# tradeClient.create_market_order('ETHUSDTM', 'sell', '1', 'UUID', size=1)
# print(tradeClient.get_all_position()["code"])

# Request large enough data set for accurate indicators and create dataframe
def updateDataFrame():
    return pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '1hour', 
                                            round(datetime(2023, 2, 1).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(time.time())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])
df = updateDataFrame()

def DF():
    df = updateDataFrame()

class currentPosition:
    inPosition = False
    buyPrice = 0
    TP = 0
    SL = 0

if(len(tradeClient.get_all_position()) == 1):
    currentPosition.inPosition = True

tradeClient.create_market_order('ETHUSDTM', 'buy', '1', 'UUID', size=1)
currentPosition.inPosition = True
currentPosition.buyPrice = tradeClient.get_all_position()[0]['avgEntryPrice']
currentPosition.TP = currentPosition.buyPrice + takeProfit
currentPosition.SL = currentPosition.buyPrice - stopLoss
print(currentPosition.inPosition, currentPosition.buyPrice, currentPosition.TP, currentPosition.SL)

# async def main():
#     global loop

#     # callback function that receives messages from the socket
#     async def handle_evt(msg):
#         if msg['topic'] == '/market/ticker:ETH-USDT':
#             current_hour = datetime.now().hour
#             if(datetime.now().hour != current_hour):
#                 DF()
#             df.iloc[0]["close"] = f'{msg["data"]["price"]}'

#             # Indicators
#             price_current = pd.to_numeric(df.iloc[::-1]['close'])[0]
#             print(currentPosition.inPosition)
    
#     ksm = await KucoinSocketManager.create(loop, marketClient, handle_evt)

#     # ETH-USDT Market Ticker
#     await ksm.subscribe('/market/ticker:ETH-USDT')

#     while True:
#         await asyncio.sleep(1)

# if __name__ == "__main__":

#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())