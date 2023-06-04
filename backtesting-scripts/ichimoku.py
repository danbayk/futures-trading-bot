import pandas as pd
from ta.trend import IchimokuIndicator
import math

file = 'charts/ETH30min.csv'
BD = pd.read_csv(file)

class positionStats:
    capital = 1000
    wins = 0
    losses = 0

class currentPosition:
    inPosition = False
    buyPrice = 0
    TP = 0
    SL = 0

DF = pd.DataFrame(columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])

i = 0
for row in BD.iterrows():
    DF = pd.concat([DF, BD.loc[i:i]])
    close = pd.to_numeric(DF['close'])[len(DF) - 1]
    cloud = IchimokuIndicator(DF['high'], DF['low'])
    a_leading = cloud.ichimoku_a()[len(DF) - 1]
    b_leading = cloud.ichimoku_b()[len(DF) - 1]
    a_current = cloud.ichimoku_a()[0 if len(DF) <= 26 else len(DF) - 26]
    b_current = cloud.ichimoku_b()[0 if len(DF) <= 26 else len(DF) - 26]
    base = cloud.ichimoku_base_line()[len(DF) - 1]
    conv = cloud.ichimoku_conversion_line()[len(DF) - 1]
    lagspan = pd.to_numeric(DF['close'])[0 if len(DF) <= 26 else len(DF) - 26]

    if(math.isnan(a_leading) or math.isnan(b_leading) or math.isnan(base) or math.isnan(conv)):
        i += 1
        continue

    # BUY
    if(close > a_current and close > b_current and a_leading > b_leading and close > base and conv > base and currentPosition.inPosition == False):
        currentPosition.inPosition = True
        currentPosition.buyPrice = close
        currentPosition.SL = close - 10
        # currentPosition.TP = ((close - base)) + close
        currentPosition.TP = close + 20
        print('--------------------')
        print('date:')
        print(DF['timestamp'][len(DF) - 1], close)
        print('buy price: ')
        print(close)


    # SELL win
    if(close > currentPosition.TP and currentPosition.inPosition == True):
        currentPosition.inPosition = False
        positionStats.wins += 1
        positionStats.capital = (positionStats.capital/currentPosition.buyPrice)*close
    # SELL loss
    if(close < currentPosition.SL and currentPosition.inPosition == True):
        currentPosition.inPosition = False
        positionStats.losses += 1
        positionStats.capital = (positionStats.capital/currentPosition.buyPrice)*close
        
    i += 1
print(positionStats.wins)
print(positionStats.losses)
print(positionStats.capital)