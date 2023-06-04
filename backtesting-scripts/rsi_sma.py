import pandas as pd
from ta.trend import ema_indicator
from ta.momentum import stochrsi_k, stochrsi_d
from ta.trend import MACD
import math

# User modified variables, make sure to set interval correctly
basefile = 'charts/ETH4hlong.csv'
suppfile = 'charts/ETH1min.csv'
# Hourly base dataframe time interval. ex. 0.5 --> 30min, 1 --> 1hour, 4 --> 4hour etc.
interval = 0.5
# Futures leverage amount (ex. '5' --> 5x leverage)
leverage = 5

BD = pd.read_csv(basefile)
SD = pd.read_csv(suppfile)

cntLONGS = 0
cntSHORTS = 0

# Overall statistics
class positionStats:
    capital = 1000
    wins = 0
    losses = 0

# Track current position
class currentPosition:
    inPositionLONG = False
    inPositionSHORT = False
    buyPriceLONG = 0
    buyPriceSHORT = 0

DF = pd.DataFrame(columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])

i = 0
for row in BD.iterrows():
    DF = pd.concat([DF, BD.loc[i:i]])
    # DF.at[i, 'close'] = DF['open'][len(DF) - 1]
    price_current = pd.to_numeric(DF['close'])[len(DF) - 1]
    ema_200_current = ema_indicator(pd.to_numeric(DF['close']), 200, False)[len(DF) - 1]
    ema_200_trailing = ema_indicator(pd.to_numeric(DF['close']), 200, False)[0 if len(DF) == 1 else len(DF) - 2]
    sma_9_current = ema_indicator(pd.to_numeric(DF['close']), 17, False)[len(DF) - 1]
    sma_9_trailing = ema_indicator(pd.to_numeric(DF['close']), 17, False)[0 if len(DF) == 1 else len(DF) - 2]
    rsi_k_current = stochrsi_k(pd.to_numeric(DF['close']), 14, 4, 4, False)[len(DF) - 1]
    rsi_d_current = stochrsi_d(pd.to_numeric(DF['close']), 14, 4, 4, False)[len(DF) - 1]
    rsi_k_trailing = stochrsi_k(pd.to_numeric(DF['close']), 14, 4, 4, False)[0 if len(DF) == 1 else len(DF) - 2]
    macd = MACD(pd.to_numeric(DF['close']))
    macd_line = macd.macd()[len(DF) - 1]
    macd_line_trailing = macd.macd()[0 if len(DF) == 1 else len(DF) - 2]
    macd_signal_line = macd.macd_signal()[len(DF) - 1]
    macd_signal_line_trailing = macd.macd_signal()[0 if len(DF) == 1 else len(DF) - 2]
    
    def kupwardLONG():
        return (((rsi_k_current - rsi_k_trailing) > 0.05) and (rsi_k_current > rsi_d_current) and (rsi_k_current > 0.5))
    def kupwardSHORT():
        return (((rsi_k_trailing - rsi_k_current) > 0.05) and (rsi_k_current < rsi_d_current) and (rsi_k_current < 0.5))

    def smaupwardLONG():
        return (sma_9_current - sma_9_trailing) > 1.5
    def smaupwardSHORT():
        return (sma_9_trailing - sma_9_current) > 1.5
    
    def priceupLONG():
        # return ((price_current > ema_200_current) and (price_current > sma_9_current) and (sma_9_current > ema_200_current))
        return ((price_current > sma_9_current))
    def priceupSHORT():
        return ((price_current < sma_9_current))

    if(math.isnan(sma_9_current) or math.isnan(rsi_k_current) or math.isnan(ema_200_current)):
        DF.at[i, 'close'] = BD.loc[i:i]["close"]
        i += 1
        continue
    if(price_current < ema_200_current):
        DF.at[i, 'close'] = BD.loc[i:i]["close"]
        i += 1
        continue

    # LONG BUY
    if(kupwardLONG() and smaupwardLONG() and priceupLONG() and currentPosition.inPositionLONG == False):
        currentPosition.inPositionLONG = True
        currentPosition.buyPriceLONG = price_current
        print('--------------------')
        print('date:')
        print(DF['timestamp'][len(DF) - 1], price_current)
        print('buy price: ')
        print(currentPosition.buyPriceLONG)
        print('--------------------')

    # SHORT BUY
    if(kupwardSHORT() and smaupwardSHORT() and priceupSHORT() and currentPosition.inPositionSHORT == False):
        currentPosition.inPositionSHORT = True
        currentPosition.buyPriceSHORT = price_current
        print('--------------------')
        print('date:')
        print(DF['timestamp'][len(DF) - 1], price_current)
        print('buy price: ')
        print(currentPosition.buyPriceSHORT)
        print('--------------------')

    # LONG SELL
    lossStop = sma_9_current
    if(((rsi_k_trailing - rsi_k_current > 0) or (price_current < lossStop)) and currentPosition.inPositionLONG == True):
        fee = ((((positionStats.capital * leverage))/100)*0.06) * 2
        profit = (((positionStats.capital * leverage)/currentPosition.buyPriceLONG)*(price_current)) - ((((positionStats.capital * leverage)/currentPosition.buyPriceLONG)*(currentPosition.buyPriceLONG))) - fee
        positionStats.capital = positionStats.capital + profit
        print('LONG')
        print('date:')
        print(DF['timestamp'][len(DF) - 1], price_current)
        print('sell price:')
        print(price_current)
        print('profit:')
        print(profit)
        print('capital')
        print(positionStats.capital)
        currentPosition.inPositionLONG = False
        currentPosition.buyPriceLONG = 0
        cntLONGS += 1

    # SHORT SELL
    if(((rsi_k_current - rsi_k_trailing > 0) or (price_current > lossStop)) and currentPosition.inPositionSHORT == True):
        fee = ((((positionStats.capital * leverage))/100)*0.06) * 2
        profit = ((((positionStats.capital * leverage)/currentPosition.buyPriceSHORT)*(price_current)) - ((((positionStats.capital * leverage)/currentPosition.buyPriceSHORT)*(currentPosition.buyPriceSHORT))) - fee)
        if(profit < 0):
            positionStats.capital = positionStats.capital + abs(profit)
        elif(profit > 0):
            positionStats.capital = positionStats.capital - abs(profit)
        print('SHORT')
        print('date:')
        print(DF['timestamp'][len(DF) - 1], price_current)
        print('sell price:')
        print(price_current)
        print('profit:')
        print(profit)
        print('capital')
        print(positionStats.capital)
        currentPosition.inPositionSHORT = False
        currentPosition.buyPriceSHORT = 0
        cntSHORTS += 1
    
    i += 1

print(cntLONGS, cntSHORTS)