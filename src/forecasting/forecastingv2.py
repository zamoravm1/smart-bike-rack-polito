from threading import Timer
import pandas as pd
import time
import numpy as np
import datetime
import pymongo
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from pymongo import MongoClient
import signal

def x1(df, groupby_cols, target_col_name, new_col_name):
    grouped_df = df.groupby(groupby_cols)[target_col_name].mean().reset_index()
    grouped_df[new_col_name] = grouped_df[target_col_name].round().astype(int)
    grouped_df.drop(columns=target_col_name, inplace=True)
    result_df = pd.merge(df, grouped_df, on=groupby_cols, how='left')
    return result_df

def x2(df):
    def float_to_time(x):
        hour = int(x)
        minute = int((x - hour) * 100)
        return '{:02d}:{:02d}'.format(hour, minute)
    def rolling_mean(x):
        return x.rolling(window=18, min_periods=1).mean().iloc[-1]
    df['Time'] = df['Hour'].apply(float_to_time)
    df['x2'] = df.groupby(['Weekday', 'Time'])['busy_slots'].transform(rolling_mean).astype(int)
    df = df.drop('Time', axis=1)
    return df

def x3(df):
    df['hour_int'] = df['Hour'].apply(lambda x: int(x*100))
    df['hourly_avg_bikes'] = df.groupby(['Weekday', 'hour_int'])['busy_slots'].rolling(window=72, min_periods=1).mean().reset_index(0, drop=True).reset_index(drop=True)
    df['x3'] = (df['busy_slots'] - df['hourly_avg_bikes'])
    df['x3'] = df['x3'].astype(int)
    df = df.drop(['hour_int','hourly_avg_bikes'],axis=1)
    return df


def EveryN(i, iter=0):
    global connection 
    global counts_collection
    global query
    global forecasting_collection
    global closest_prediction
    global closest_time
    global predictions
    global correct_0
    global correct_1
    global correct_2
    global bad
    global aux
    
    if not alive:
        return
    Timer(i, EveryN, (i, iter+1)).start()
    
    if not connection:
        try: 
            myclient = pymongo.MongoClient('mongodb+srv://smartrack2022:Smart*rack2022@smartbikerack.ocijvrf.mongodb.net/test')
            db = myclient['Smart_Bike_Rack']
            counts_collection = db['Bike_Count']
            forecasting_collection = db['Forecasting']
            query = {'rack_id': 1} ###############In case more racks to work with
            connection = True
        except:
            connection = False
            
                 
    if connection:
        
        
            
        
        forecasting_collection.delete_many({})  
        
        documents = list(counts_collection.find(query))
        df = pd.DataFrame(documents)

        year = []
        month = []
        day = []
        weekday = []
        hour = []
        for i in range(len(df)):
            year.append(datetime.datetime.strptime(df.iloc[i][2], '%Y-%m-%d-%H-%M-%S').strftime('%Y'))
            month.append(datetime.datetime.strptime(df.iloc[i][2], '%Y-%m-%d-%H-%M-%S').strftime('%m'))
            day.append(datetime.datetime.strptime(df.iloc[i][2], '%Y-%m-%d-%H-%M-%S').strftime('%d'))
            weekday.append(datetime.datetime.strptime(df.iloc[i][2], '%Y-%m-%d-%H-%M-%S').strftime('%A'))
            hour.append(datetime.datetime.strptime(df.iloc[i][2], '%Y-%m-%d-%H-%M-%S').strftime('%H:%M'))

        df['Year']=year
        df['Month']=month
        df['Day']=day
        df['Weekday']=weekday
        df['Hour']=hour
        df['Hour2']=hour

        df['Year'] = df['Year'].apply(lambda x: int(x))
        df['Month'] = df['Month'].apply(lambda x: int(x))
        df['Day'] = df['Day'].apply(lambda x: int(x))
        df['Weekday'] = df['Weekday'].apply(lambda x: time.strptime(x, '%A').tm_wday)
        to_float_hour = lambda x: float(x.replace(':', '.'))
        df['Hour'] = df['Hour'].apply(to_float_hour)
        
        last_row = df.iloc[-1]
        last_row = last_row.to_frame()
        last_row = last_row.T
        
        predictions = predictions + 1
        if aux==True:
            if closest_prediction == last_row.iloc[0]['busy_slots']:
                correct_0 = correct_0 + 1
            elif abs(closest_prediction-last_row.iloc[0]['busy_slots']) == 1:
                correct_1 = correct_1 + 1
            elif abs(closest_prediction-last_row.iloc[0]['busy_slots']) == 2:
                correct_1 = correct_2 + 1
            else:
                bad = bad + 1
        
                          
        
        df = pd.concat([df, last_row, last_row, last_row], ignore_index=True)
        
        
        
        df.loc[len(df)-3, 'Hour'] = df.loc[len(df)-3, 'Hour'] + 0.30
        df.loc[len(df)-3, 'Hour2'] = (datetime.datetime.strptime(df.loc[len(df)-3, 'Hour2'], '%H:%M') + datetime.timedelta(minutes=30)).strftime('%H:%M')
        df.loc[len(df)-2, 'Hour'] = df.loc[len(df)-2, 'Hour'] + 1.00
        df.loc[len(df)-2, 'Hour2'] = (datetime.datetime.strptime(df.loc[len(df)-2, 'Hour2'], '%H:%M') + datetime.timedelta(hours=1)).strftime('%H:%M')
        df.loc[len(df)-1, 'Hour'] = df.loc[len(df)-1, 'Hour'] + 1.30
        df.loc[len(df)-1, 'Hour2'] = (datetime.datetime.strptime(df.loc[len(df)-1, 'Hour2'], '%H:%M') + datetime.timedelta(hours=1, minutes=30)).strftime('%H:%M')

        df = x1(df,['Weekday','Hour'], 'busy_slots', 'x1')
        df = x2(df)
        df = x3(df)
        prediction_df = df.tail(4)
        df = df.drop(df.tail(3).index)
        
        regressor = RandomForestRegressor(n_estimators = 100, random_state = 0)
        
        X = df[['Month','Day','Weekday','Hour','x1','x2','x3']]
        y = df[['busy_slots']]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=44)
        regressor.fit(X_train,y_train)
        score = regressor.score(X_test, y_test)
        prediction = regressor.predict(prediction_df[['Month','Day','Weekday','Hour','x1','x2','x3']])
        prediction = np.round(prediction)
        prediction = prediction.astype('int')
        prediction_df = prediction_df.assign(busy_slots=prediction)
        prediction_df['timestamp'] = prediction_df.apply(lambda x: f"{x['Year']}-{x['Month']}-{x['Day']}-{x['Hour2'][:2]}-{x['Hour2'][3:]}", axis=1)
        
        prediction_df['free_slots'] = 22-prediction_df['busy_slots']
        prediction_df = prediction_df.drop(['_id','Year','Month','Day','Weekday','Hour','Hour2','x1','x2','x3'],axis=1)
        data = prediction_df.to_dict(orient='records')
        forecasting_collection.insert_many(data)
        closest_prediction = data[1]['busy_slots']
        closest_time = data[1]['timestamp']
        aux = True
        
        closest_hour = int(closest_time.split('-')[3]) 
        
        if 7 <= closest_hour <= 21:
            predictions = predictions + 1
            if aux==True:
                if closest_prediction == last_row['busy_slots'].values:
                    correct_0 = correct_0 + 1
                elif abs(closest_prediction-last_row['busy_slots'].values) == 1:
                    correct_1 = correct_1 + 1
                elif abs(closest_prediction-last_row['busy_slots'].values) == 2:
                    correct_1 = correct_2 + 1
                else:
                    bad = bad + 1
        else:
            pass
        
        print('Out of: ',predictions-1,' predictions: ',correct_0, 'predicted perfectly')
        print('Out of: ',predictions-1,' predictions: ',correct_1, 'predicted with a +- 1 tolerance')
        print('Out of: ',predictions-1,' predictions: ',correct_2, 'predicted with a +- 2 tolerance')
        print('Out of: ',predictions-1,' predictions: ',bad, 'predicted wrongly')
         

if __name__ == "__main__":
    try: 
        myclient = pymongo.MongoClient('mongodb+srv://smartrack2022:Smart*rack2022@smartbikerack.ocijvrf.mongodb.net/test')
        db = myclient['Smart_Bike_Rack']
        counts_collection = db['Bike_Count']
        forecasting_collection = db['Forecasting']
        query = {'rack_id': 1} ###############In case more racks to work with
        connection = True
    except:
        connection = False
            
    timer = 1800
    alive = True
    aux = False
    predictions = 0
    correct_0 = 0
    correct_1 = 0
    correct_2 = 0 
    bad = 0
    try:
        EveryN(timer)
        signal.pause()
        
    except KeyboardInterrupt:
        alive = False