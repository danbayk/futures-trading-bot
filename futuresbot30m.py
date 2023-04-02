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

# Market API, used to get previous candlestick data for indicators via API call and live data via websockets
marketClient = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'), os.getenv('API_PASSPHRASE'))

# ----- REAL API -----
api_key = os.getenv('API_KEY_FUTURES')
api_secret = os.getenv('API_SECRET_FUTURES')
api_passphrase = os.getenv('API_PASSPHRASE_FUTURES')
tradeClient = Trade(key = api_key, secret = api_secret, passphrase = api_passphrase, is_sandbox = False)

takeProfit = 25
stopLoss = 15

# Current position details
class currentPosition:
    inPosition = False
    buyPrice = 0
    TP = 0
    SL = 0

# Establish previous state in the event of a crash/restart
if(len(tradeClient.get_all_position()) == 1):
    currentPosition.inPosition = True
    currentPosition.buyPrice = tradeClient.get_all_position()[0]['avgEntryPrice']
    currentPosition.TP = currentPosition.buyPrice + takeProfit
    currentPosition.SL = currentPosition.buyPrice - stopLoss

# Buy conditions
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

# Request large enough data set for accurate indicators and create dataframe
df = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '30min', 
                                            round(datetime(2023, 3, 20).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(time.time())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])


def executeBuy():
    try:
        tradeClient.create_market_order('ETHUSDTM', 'buy', '1', 'UUID', size=1)
    except:
        time.sleep(1)
        tradeClient.create_market_order('ETHUSDTM', 'buy', '1', 'UUID', size=1)
    currentPosition.inPosition = True
    time.sleep(2)
    currentPosition.buyPrice = tradeClient.get_all_position()[0]['avgEntryPrice']
    currentPosition.TP = currentPosition.buyPrice + takeProfit
    currentPosition.SL = currentPosition.buyPrice - stopLoss

def executeSell():
    try:
        tradeClient.create_market_order('ETHUSDTM', 'sell', '1', 'UUID', size=1)
    except:
        time.sleep(1)
        tradeClient.create_market_order('ETHUSDTM', 'sell', '1', 'UUID', size=1)
    currentPosition.inPosition = False
    currentPosition.buyPrice = 0

completeUpdate = False
while True:
    time.sleep(5)
    if(datetime.now().minute == 1 or datetime.now().minute == 31):
        completeUpdate = False
    if((datetime.now().minute == 30 or datetime.now().minute == 0) and completeUpdate == False):
        while True:
            try:
                df = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '30min', 
                                            round(datetime(2023, 3, 1).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(time.time())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])
                break
            except:
                time.sleep(1)
                print('error')
                pass
        completeUpdate = True
    df.iloc[0]["close"] = marketClient.get_ticker('ETH-USDT')['price']

    # Indicators
    price_current = pd.to_numeric(df.iloc[::-1]['close'])[0]
    ema_200_current = ema_indicator(pd.to_numeric(df.iloc[::-1]['close']), 200, False)[0]
    sma_9_current = ema_indicator(pd.to_numeric(df.iloc[::-1]['close']), 17, False)[0]
    sma_9_trailing = ema_indicator(pd.to_numeric(df.iloc[::-1]['close']), 17, False)[1]
    rsi_k_current = stochrsi_k(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[0]
    rsi_d_current = stochrsi_d(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[0]
    rsi_k_trailing = stochrsi_k(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[1]

    # Buying conditions --------------------- check for kucoin position before running
    if(kupward(rsi_k_current, rsi_k_trailing, rsi_d_current) and
        smaupward(sma_9_current, sma_9_trailing) and 
        priceup(price_current, ema_200_current, sma_9_current) and
        currentPosition.inPosition == False):
        # Execute a buy
        executeBuy()

    # Selling conditions, can sell on the same tick as buy
    if((price_current > currentPosition.TP or price_current < currentPosition.SL) and currentPosition.inPosition == True):
        # Execute a sell
        executeSell()

    
    # print(ema_200_current, sma_9_current, rsi_k_current)
    print(len(df))
    print(price_current)
    print(ema_200_current, sma_9_current, rsi_k_current)
    print(kupward(rsi_k_current, rsi_k_trailing, rsi_d_current), smaupward(sma_9_current, sma_9_trailing), priceup(price_current, ema_200_current, sma_9_current))
    print(ema_200_current, sma_9_current, rsi_k_current, rsi_k_trailing)
    if(currentPosition.inPosition == True):
        print("---IN POSITION---")
        print(currentPosition.buyPrice, currentPosition.TP, currentPosition.SL)
