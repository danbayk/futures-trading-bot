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

# User-modified parameters, default is best for ETH-USDT 30m trading
takeProfit = 20
stopLoss = 10
leverage = 5

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
            traceback.print_exc()
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

# Execute a buy
def executeBuy():
    while True:
        try:
            # Get account balance and price in USDT
            balance = userClient.get_account_overview('USDT')['availableBalance']
            currentPrice = marketClient.get_ticker('ETH-USDT')['price']
            # Get buy amount in lots (0.01 ETH) * leverage
            buyAmt = int((balance/float(currentPrice))/0.01) * leverage
            # Place a ETH-USDT market order with calculated parameters
            tradeClient.create_market_order('ETHUSDTM', 'buy', '5', 'UUID', size=buyAmt)
            currentPosition.amtLots = buyAmt
            break
        except:
            time.sleep(11)
            traceback.print_exc()
            pass
    currentPosition.inPosition = True
    # Sleep to make sure avgEntryPrice is updated on exchange
    time.sleep(2)
    while True:
        try:
            # Set buyprice to exchange-determined entry price
            currentPosition.buyPrice = tradeClient.get_all_position()[0]['avgEntryPrice']
            break
        except:
            time.sleep(11)
            traceback.print_exc()
            pass
    currentPosition.TP = currentPosition.buyPrice + takeProfit
    currentPosition.SL = currentPosition.buyPrice - stopLoss

# Execute a sell
def executeSell():
    while True:
        try:
            tradeClient.create_market_order('ETHUSDTM', 'sell', '5', 'UUID', size=currentPosition.amtLots)
            break
        except:
            time.sleep(1)
            traceback.print_exc()
            pass
    currentPosition.inPosition = False
    currentPosition.buyPrice = 0
    currentPosition.amtLots = 0

# Bot loop
while True:
    while True:
        try:
            # Request large enough data set for accurate indicators and create dataframe
            df = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '30min', 
                                            round(datetime(2023, 3, 5).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(time.time())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])
            break
        except:
            time.sleep(11)
            traceback.print_exc()
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
    time.sleep(5)