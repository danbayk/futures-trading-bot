from kucoin.client import Client
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timezone, date, timedelta
import traceback
import time
import os

load_dotenv()


marketClient = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'), os.getenv('API_PASSPHRASE'))

df = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '1min', 
                                            round(datetime(2023, 5, 1).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(datetime(2023, 5, 2).replace(tzinfo=timezone.utc).timestamp())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])
# df.to_csv('test.csv')

# i = 0
# for row in df.iterrows():
#     df['timestamp'][i] = df['timestamp'][0].replace(df['timestamp'][i], datetime.utcfromtimestamp(int(df['timestamp'][i])).strftime('%m/%d/%Y'))
#     i += 1

runningFrame = pd.DataFrame(columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 5, 1)

startDay = start_date
count = 0
for single_date in daterange(start_date, end_date):
    if(count == 0):
        pass
    else:
        endDay = single_date
        while True:
            try:
                currFrame = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                                    '1min', 
                                                    round(startDay.replace(tzinfo=timezone.utc).timestamp()), 
                                                    round(endDay.replace(tzinfo=timezone.utc).timestamp())), 
                                                    columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])
                break
            except:
                time.sleep(5)
                traceback.print_exc()
                pass
        i = 0
        for row in currFrame.iterrows():
            currFrame['timestamp'][i] = currFrame['timestamp'][0].replace(currFrame['timestamp'][i], datetime.utcfromtimestamp(int(currFrame['timestamp'][i])).strftime('%m/%d/%Y'))
            i += 1
        
        runningFrame = pd.concat([runningFrame, currFrame.iloc[::-1]])
        startDay = single_date
    count += 1

print(runningFrame)