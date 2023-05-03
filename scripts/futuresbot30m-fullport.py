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

# Market API, used to get previous candlestick data for indicators via API call and live data via websockets
marketClient = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'), os.getenv('API_PASSPHRASE'))

# Futures user API, used to get account balance

# ----- REAL API -----
api_key = os.getenv('API_KEY_FUTURES')
api_secret = os.getenv('API_SECRET_FUTURES')
api_passphrase = os.getenv('API_PASSPHRASE_FUTURES')

# Create trade and user endpoints
tradeClient = Trade(key = api_key, secret = api_secret, passphrase = api_passphrase, is_sandbox = False)
userClient = User(api_key, api_secret, api_passphrase)

takeProfit = 20
stopLoss = 10

# Current position details
class currentPosition:
    inPosition = False
    buyPrice = 0
    amtLots = 0
    TP = 0
    SL = 0

# Establish previous state in the event of a crash/restart
if(len(tradeClient.get_all_position()) == 1):
    currentPosition.inPosition = True
    while True:
        try:
            currentPosition.buyPrice = tradeClient.get_all_position()[0]['avgEntryPrice']
            break
        except:
            time.sleep(1)
            print('error')
            pass
    currentPosition.TP = currentPosition.buyPrice + takeProfit
    currentPosition.SL = currentPosition.buyPrice - stopLoss

# Buy conditions
def kupward(rsi_k_current, rsi_k_trailing, rsi_d_current):
    return (((rsi_k_current - rsi_k_trailing) > 0.05) and 
            (rsi_k_current > rsi_d_current) and 
            (rsi_k_current > 0.5))

def smaupward(sma_9_current, sma_9_trailing):
    return (sma_9_current - sma_9_trailing) > 0.7

def priceup(price_current, ema_200_current, sma_9_current):
    # return ((price_current > ema_200_current) and 
    #         (price_current > sma_9_current) and 
    #         (sma_9_current > ema_200_current))
    return (price_current > sma_9_current)

# Request large enough data set for accurate indicators and create dataframe
df = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '30min', 
                                            round(datetime(2023, 3, 5).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(time.time())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])

# Get user balance for executeBuy() and executeSell()
balance = userClient.get_account_overview('USDT')['availableBalance']

# Execute a buy, endpoint occationally throws error due to an API issue, current official Kucoin fix is "retry the call"
def executeBuy():
    while True:
        try:
            buyAmt = int((balance/float(marketClient.get_ticker('ETH-USDT')['price']))/0.01)
            tradeClient.create_market_order('ETHUSDTM', 'buy', '5', 'UUID', size=buyAmt)
            currentPosition.amtLots = buyAmt
            break
        except:
            time.sleep(1)
            print('error')
            pass
    currentPosition.inPosition = True
    time.sleep(2)
    while True:
        try:
            currentPosition.buyPrice = tradeClient.get_all_position()[0]['avgEntryPrice']
            break
        except:
            time.sleep(1)
            print('error')
            pass
    currentPosition.TP = currentPosition.buyPrice + takeProfit
    currentPosition.SL = currentPosition.buyPrice - stopLoss

# Execute a sell, endpoint occationally throws error due to an API issue, current official Kucoin fix is "retry the call"
def executeSell():
    global balance
    while True:
        try:
            tradeClient.create_market_order('ETHUSDTM', 'sell', '5', 'UUID', size=currentPosition.amtLots)
            break
        except:
            time.sleep(1)
            print('error')
            pass
    currentPosition.inPosition = False
    currentPosition.buyPrice = 0
    currentPosition.amtLots = 0
    while True:
        try:
            balance = userClient.get_account_overview('USDT')['availableBalance']
            break
        except:
            time.sleep(1)
            print('error')
            pass

completeUpdate = False
while True:
    time.sleep(5)
    if(datetime.now().minute == 1 or datetime.now().minute == 31):
        completeUpdate = False
    if((datetime.now().minute == 30 or datetime.now().minute == 0) and completeUpdate == False):
        time.sleep(2)
        print('updated')
        while True:
            try:
                df = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '30min', 
                                            round(datetime(2023, 3, 5).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(time.time())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])
                break
            except:
                time.sleep(1)
                print('error')
                pass
        completeUpdate = True
    while True:
        try:
            df.iloc[0]["close"] = marketClient.get_ticker('ETH-USDT')['price']
            break
        except:
            time.sleep(11)
            print('error')
            pass

    # Indicators
    price_current = pd.to_numeric(df.iloc[::-1]['close'])[0]
    ema_200_current = ema_indicator(pd.to_numeric(df.iloc[::-1]['close']), 200, False)[0]
    sma_9_current = ema_indicator(pd.to_numeric(df.iloc[::-1]['close']), 17, False)[0]
    sma_9_trailing = ema_indicator(pd.to_numeric(df.iloc[::-1]['close']), 17, False)[1]
    rsi_k_current = stochrsi_k(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[0]
    rsi_d_current = stochrsi_d(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[0]
    rsi_k_trailing = stochrsi_k(pd.to_numeric(df.iloc[::-1]['close']), 14, 3, 3, True)[1]

    # Buying conditions
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

    print(df)
    print(price_current)
    print(kupward(rsi_k_current, rsi_k_trailing, rsi_d_current), smaupward(sma_9_current, sma_9_trailing), priceup(price_current, ema_200_current, sma_9_current))
    print(ema_200_current, sma_9_current, rsi_k_current, rsi_k_trailing)
    if(currentPosition.inPosition == True):
        print("---IN POSITION---")
        print(currentPosition.buyPrice, currentPosition.TP, currentPosition.SL)
