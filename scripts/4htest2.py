import backtrader as bt
from backtrader.feeds import GenericCSVData
import pandas as pd
from ta.trend import ema_indicator
from ta.momentum import stochrsi_k, stochrsi_d
import math
from math import floor
import random
import datetime

#1h TP: 25, SL: 15
#30m TP: 25 SL: 5 0.04 and 1.5 
#4h TP: 30 SL: previous low 1.5 SMA 0.05 RSI k
# Variable values for testing

# Interchange with any chart with the same column format
chart = 'charts/kucoin4h.csv'
# chart = 'charts/largeDataSetETH.csv'
# Starting capital
initialCapital = 1000
# Set take profit (dollars)
takeprofit = 15
# Set stop loss (dollars)
stoploss = 10
# Futures leverage amount (ex. '5' --> 5x leverage)
leverage = 5

cerebro = bt.Cerebro()
feed = GenericCSVData(dataname=chart,
                      dtformat = ('%m/%d/%Y'),
                      # dtformat = ('%Y-%m-%d'),
                      fromdate = datetime.datetime(2022, 1, 5),
                      date = 0,
                      open = 1,
                      high = 2,
                      low = 3,
                      close = 4,
                      volume = 5,
                      openinterest = -1)

df = pd.DataFrame(columns=['close'])
df_open = pd.DataFrame(columns=['open'])
df_low = pd.DataFrame(columns=['low'])

# Separate dataframe for indicators, only difference is the price for calculation is the high not the close to include all buys that will occur live
df_for_indicators = pd.DataFrame(columns=['close'])

class positionStats:
    startingCapital = initialCapital
    capital = startingCapital
    wins = 0
    losses = 0
    fees = 0

class currentPosition:
    inPosition = False
    buyPrice = 0

positionCooldown = False

class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.dataopen = self.datas[0].open
        self.datavolume = self.datas[0].volume
        self.datalow = self.datas[0].low

    def next(self):
        global positionStats
        df.loc[len(df.index)] = [self.dataclose[0]]
        df_low.loc[len(df_low.index)] = [self.datalow[0]]
        if(len(df_for_indicators) == 0 or len(df_for_indicators) == 1):
            df_for_indicators.loc[len(df_for_indicators.index)] = [self.dataclose[0]]
        else:
            df_for_indicators.loc[len(df_for_indicators.index) - 2] = [self.dataclose[-2]]
            df_for_indicators.loc[len(df_for_indicators.index) - 1] = [self.datahigh[-1]]
            df_for_indicators.loc[len(df_for_indicators.index)] = [self.dataclose[0]]

        df_open.loc[len(df_open.index)] = [self.dataopen[0]]
        price_current = pd.to_numeric(df['close'])[len(df) - 1]
        price_previous_open = pd.to_numeric(df_open['open'])[0 if len(df) == 1 else len(df) - 2]
        price_previous_low = pd.to_numeric(df_low['low'])[0 if len(df_low) == 1 else len(df_low) - 2]
        ema_200_current = ema_indicator(pd.to_numeric(df['close']), 200, False)[len(df) - 1]
        price_current_high = self.datahigh[0]
        price_current_open = self.dataopen[0]
        price_current_low = self.datalow[0]
        price_volume = self.datavolume[0]
        sma_9_current = ema_indicator(pd.to_numeric(df['close']), 17, False)[len(df) - 1]
        sma_9_trailing = ema_indicator(pd.to_numeric(df['close']), 17, False)[0 if len(df) == 1 else len(df) - 2]
        rsi_k_current = stochrsi_k(pd.to_numeric(df['close']), 14, 3, 3, True)[len(df) - 1]
        rsi_d_current = stochrsi_d(pd.to_numeric(df['close']), 14, 3, 3, True)[len(df) - 1]
        rsi_k_trailing = stochrsi_k(pd.to_numeric(df['close']), 14, 3, 3, True)[0 if len(df) == 1 else len(df) - 2]
        rsi_d_trailing = stochrsi_d(pd.to_numeric(df['close']), 14, 3, 3, True)[0 if len(df) == 1 else len(df) - 2]

        # Buying conditions
        def kupward():
            return (((rsi_k_current - rsi_k_trailing) > 0.05) and (rsi_k_current > rsi_d_current) and (rsi_k_current > 0.5))

        def smaupward():
            return (sma_9_current - sma_9_trailing) > 1.5

        def priceup():
            # return ((price_current > ema_200_current) and (price_current > sma_9_current) and (sma_9_current > ema_200_current))
            return ((price_current > sma_9_current))

        if(kupward() and smaupward() and priceup() and currentPosition.inPosition == False):
            currentPosition.inPosition = True
            currentPosition.buyPrice = price_current
            positionStats.fees = positionStats.fees + ((positionStats.capital * leverage)/100)*0.06
            print('--------------------')
            self.log('BUY')
            print('buy price: ')
            print(currentPosition.buyPrice)
            print('--------------------')
            self.buy()
        
        lossStop = sma_9_current
        # Option to sell on buy tick
        if(((rsi_k_trailing - rsi_k_current > 0) or (price_current < lossStop)) and currentPosition.inPosition == True):
            self.log('SELL')
            # Win
            if(rsi_k_trailing - rsi_k_current > 0):
                if(currentPosition.buyPrice < price_current):
                    positionStats.wins += 1
                elif(currentPosition.buyPrice > price_current):
                    positionStats.losses += 1
                feeWin = ((((positionStats.capital * leverage))/100)*0.06) * 2
                print('profit: ')
                print((((positionStats.capital * leverage)/currentPosition.buyPrice)*(price_current)) - ((((positionStats.capital * leverage)/currentPosition.buyPrice)*(currentPosition.buyPrice))) - feeWin)
                positionStats.capital = positionStats.capital + ((((positionStats.capital * leverage)/currentPosition.buyPrice)*(price_current)) - ((((positionStats.capital * leverage)/currentPosition.buyPrice)*(currentPosition.buyPrice))) - feeWin)
                print('capital:')
                print(positionStats.capital)
                print('sell price: ' )
                print(price_current)
            # Loss
            elif(price_current < lossStop and False):
                positionStats.losses += 1
                # Fee calculation --> closing price / 100 * 0.06 (maker fee) * 2 (fee taken on buy and sell)
                feeLoss = (((positionStats.capital * leverage)/100)*0.06) * 2
                # Post trade capital calculation --> capital + ((capital * leverage) / buy price in ETH) * sell price in ETH - (initial capital * leverage) - fee for both buy/sell 
                positionStats.capital = ((positionStats.capital + ((((positionStats.capital * leverage)/currentPosition.buyPrice)*(lossStop)) - (positionStats.capital * leverage))) - feeLoss)
                print('sell price: ')
                print(price_current)

            currentPosition.inPosition = False
            currentPosition.buyPrice = 0
            self.sell()

cerebro.addstrategy(TestStrategy)
cerebro.adddata(feed)   
cerebro.run()
print('\n')
print('-----RESULTS-----')
print('Starting capital:')
print(positionStats.startingCapital)
print('--------------------')
print('Ending capital:')
print(floor(positionStats.capital))
print('--------------------')
print('PnL:')
print(floor(positionStats.capital - positionStats.startingCapital))
print('--------------------')
print('Wins:')
print(positionStats.wins)
print('--------------------')
print('Losses:')
print(positionStats.losses)
print('--------------------')
print('Win rate:')
print((positionStats.wins)/(positionStats.wins + positionStats.losses))
print('--------------------')
print('Final profit:')
print(floor((positionStats.capital - positionStats.startingCapital)))
print('--------------------')
# cerebro.plot()