import pandas as pd
from datetime import datetime, timedelta
import requests
import time
import pytz


def download_file_respecting_rate_limit():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json?version=8e2b3dc5a168db874374d3c3cf73d272"
    response = requests.get(url)
    
    if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            download_file_respecting_rate_limit()
    else:
         data = response.json()
         return data
    
    


    
    


def process_calendar_data():
    data = download_file_respecting_rate_limit()
    data = pd.DataFrame(data)

    data = data[data['country'] == 'USD'].drop(columns=['forecast', 'previous'])

    data['Datetime'] = pd.to_datetime(data['date'])
    
    # Calculate EventStart and EventEnd while retaining the timezone
    data['EventEnd'] = data['Datetime'].apply(lambda x: x + timedelta(minutes=5))
    data['EventStart'] = data['Datetime'].apply(lambda x: x - timedelta(minutes=5))
    
    return data
    # return data[['Datetime', 'EventStart', 'EventEnd', 'title', 'country', 'impact']]

