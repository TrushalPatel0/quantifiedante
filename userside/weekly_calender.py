import pandas as pd
from datetime import datetime, timedelta
import requests
import time
import pytz


def download_file_respecting_rate_limit():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.csv?version=885584ebdf78fdfebf4ea80bcd304fb8"
        save_path =  "calendar_csv/calender.csv"
        response = requests.get(url, stream=True)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            return download_file_respecting_rate_limit(url, save_path)
        
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File downloaded successfully: {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {e}")



def process_calendar_data():
    # download_file_respecting_rate_limit()
    data = pd.read_csv("calendar_csv/calender.csv")
    
    data = data[data['Country'] == 'USD'].drop(columns=['Forecast', 'Previous', 'URL'])
    
    new_york_tz = pytz.timezone('America/New_York')
    
    # Combine 'Date' and 'Time' columns, parse into naive datetime, then localize to New York time
    data['Datetime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'], format='%m-%d-%Y %I:%M%p').apply(
        lambda x: new_york_tz.localize(x)
    )
    
    # Calculate EventStart and EventEnd while retaining the timezone
    data['EventEnd'] = data['Datetime'].apply(lambda x: x + timedelta(minutes=5))
    data['EventStart'] = data['Datetime'].apply(lambda x: x - timedelta(minutes=5))
    
    
    return data[['Datetime', 'EventStart', 'EventEnd', 'Title', 'Country', 'Impact']]

