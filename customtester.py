import pandas as pd
from ta.trend import ema_indicator
from ta.momentum import stochrsi_k, stochrsi_d
import math

# User modified variables, make sure to set interval correctly
basefile = '4hour.csv'
suppfile = '1min.csv'
# Hourly base dataframe time interval. ex. 0.5 --> 30min, 1 --> 1hour, 4 --> 4hour etc.
interval = 4
# Futures leverage amount (ex. '5' --> 5x leverage)
leverage = 5

BD = pd.read_csv(basefile)
SD = pd.read_csv(suppfile)

# Overall statistics
class positionStats:
    capital = 1000
    wins = 0
    losses = 0
    fees = 0

# Track current position
class currentPosition:
    inPosition = False
    buyPrice = 0

# Buy conditions
def kupward(rsi_k_current, rsi_k_trailing, rsi_d_current):
    return (((rsi_k_current - rsi_k_trailing) > 0.7) and 
            (rsi_k_current > rsi_d_current) and 
            (rsi_k_current > 0.5))

def smaupward(sma_9_current, sma_9_trailing):
    return (sma_9_current - sma_9_trailing) > 3

def priceup(price_current, sma_9_current):
    return (price_current > sma_9_current)

DF = pd.DataFrame(columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])

i = 0
x = 0
startpos = 0
addInterval = 1440/(24/interval)
endpos = addInterval

for row in BD.iterrows():
    DF = pd.concat([DF, BD.loc[i:i]])
    for y in range(int(startpos), int(endpos)):
        DF.at[i, 'close'] = SD.loc[y:y]["close"]
        price_current = pd.to_numeric(DF['close'])[len(DF) - 1]
        ema_200_current = ema_indicator(pd.to_numeric(DF['close']), 200, False)[len(DF) - 1]
        sma_9_current = ema_indicator(pd.to_numeric(DF['close']), 17, False)[len(DF) - 1]
        sma_9_trailing = ema_indicator(pd.to_numeric(DF['close']), 17, False)[0 if len(DF) == 1 else len(DF) - 2]
        rsi_k_current = stochrsi_k(pd.to_numeric(DF['close']), 14, 3, 3, False)[len(DF) - 1]
        rsi_d_current = stochrsi_d(pd.to_numeric(DF['close']), 14, 3, 3, False)[len(DF) - 1]
        rsi_k_trailing = stochrsi_k(pd.to_numeric(DF['close']), 14, 3, 3, False)[0 if len(DF) == 1 else len(DF) - 2]

        if(math.isnan(sma_9_current) or math.isnan(rsi_k_current) or math.isnan(ema_200_current)):
            continue
        if(price_current < ema_200_current):
            continue

        if(kupward(rsi_k_current, rsi_k_trailing, rsi_d_current) and 
           smaupward(sma_9_current, sma_9_trailing) and
           priceup(price_current, sma_9_current) and 
           currentPosition.inPosition == False):
            currentPosition.inPosition = True
            currentPosition.buyPrice = price_current
            print('--------------------')
            print('date:')
            print(DF['timestamp'][len(DF) - 1], DF['open'][len(DF) - 1])
            print('buy price: ')
            print(currentPosition.buyPrice)
            print('--------------------')

        # (price_current > currentPosition.buyPrice + 25 or price_current < currentPosition.buyPrice - 5)
        if(rsi_k_trailing - rsi_k_current > 0 and currentPosition.inPosition == True):
            if(currentPosition.buyPrice < price_current):
                positionStats.wins += 1
            elif(currentPosition.buyPrice > price_current):
                positionStats.losses += 1
            fee = ((((positionStats.capital * leverage))/100)*0.06) * 2
            profit = (((positionStats.capital * leverage)/currentPosition.buyPrice)*(price_current)) - ((((positionStats.capital * leverage)/currentPosition.buyPrice)*(currentPosition.buyPrice))) - fee
            positionStats.capital = positionStats.capital + ((((positionStats.capital * leverage)/currentPosition.buyPrice)*(price_current)) - ((((positionStats.capital * leverage)/currentPosition.buyPrice)*(currentPosition.buyPrice))) - fee)
            print('date:')
            print(DF['timestamp'][len(DF) - 1], DF['open'][len(DF) - 1])
            print('sell price:')
            print(price_current)
            print('profit:')
            print(profit)
            print('captial')
            print(positionStats.capital)
            currentPosition.inPosition = False
            currentPosition.buyPrice = 0
        
    startpos = endpos
    endpos += addInterval
    i += 1

print(DF)