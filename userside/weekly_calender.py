from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta
import requests
import time
import pytz


mongo_uri = "mongodb+srv://QuantifiedAnte:bVrclrzFSc86BStZ@cluster0.mkl2h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client['user_db']
calender_data = db['calender_data']


def download_file_respecting_rate_limit():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.csv?version=885584ebdf78fdfebf4ea80bcd304fb8"
        save_path =  "calender.csv"
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



def process_calendar_data(file_path):
    # Load data
    data = pd.read_csv(file_path)
    
    # Filter for USD
    data = data[data['Country'] == 'USD'].drop(columns=['Forecast', 'Previous', 'URL'])
    
    # Define New York timezone
    new_york_tz = pytz.timezone('America/New_York')
    
    # Combine 'Date' and 'Time' columns, parse into naive datetime, then localize to New York time
    data['Datetime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'], format='%m-%d-%Y %I:%M%p').apply(
        lambda x: new_york_tz.localize(x)
    )
    
    # Calculate EventStart and EventEnd while retaining the timezone
    data['EventEnd'] = data['Datetime'].apply(lambda x: x + timedelta(minutes=10))
    data['EventStart'] = data['Datetime'].apply(lambda x: x - timedelta(minutes=10))
    
    # Return the updated dataframe
    return data[['Datetime', 'EventStart', 'EventEnd', 'Title', 'Country', 'Impact']]



def pushCalenderData():
    calender_data = db['calender_data']
    data = process_calendar_data("calender.csv")
    print
    calender_data.insert_many(data.to_dict(orient='records'))
    print("Data inserted successfully")




def is_trading_suspended(event_data, current_time):
    """Check if trading should be suspended due to news events."""
    return any((event_data['EventStart'] <= current_time) & (event_data['EventEnd'] >= current_time))



if _name_ == "_main_":
    download_file_respecting_rate_limit()
    pushCalenderData()
    current_datetime = datetime.now()
    current_datetime_gmt_neg_5 = pytz.timezone('America/New_York').localize(current_datetime)
    # event_data = pd.DataFrame(list(calender_data.find()))
    # if is_trading_suspended(event_data, current_datetime_gmt_neg_5):
    #     print("Trading suspended due to news events.")
    # else:
    #     print("Trading is active.")


# gmt_neg_5 = pytz.timezone('America/New_York')  
# current_datetime_gmt_plus_530 = datetime.now(gmt_neg_5)