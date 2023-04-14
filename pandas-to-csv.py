from kucoin.client import Client
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from datetime import timezone
import time
import os

load_dotenv()

# Market API, used to get previous candlestick data for indicators via API call and live data via websockets
marketClient = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'), os.getenv('API_PASSPHRASE'))


df = pd.DataFrame(marketClient.get_kline_data('ETH-USDT', 
                                            '1hour', 
                                            round(datetime(2022, 8, 1).replace(tzinfo=timezone.utc).timestamp()), 
                                            round(datetime(2023, 4, 1, 0, 30).replace(tzinfo=timezone.utc).timestamp())), 
                                            columns=['timestamp', 'open', 'close', 'high', 'low', 'tx amt', 'tx vol'])

df.to_csv('augtoapr4h-kucoin.csv')