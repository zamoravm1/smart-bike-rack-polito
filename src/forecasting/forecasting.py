from threading import Timer
import pandas as pd
import time
import numpy as np
import datetime
import pymongo
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.metrics import accuracy_score
from pymongo import MongoClient
import signal

def accuracy_with_tolerance(arr1, arr2):
    accurate_values = np.logical_or(np.isclose(arr1, arr2, rtol=0, atol=2),
                                    np.isclose(arr1, arr2, rtol=0, atol=-2))
    accuracy = accurate_values.sum() / len(arr1)
    return accuracy

accu_y_test = 0
accu_y_test_hat = 0

def EveryN(i, iter=0):
    global connection 
    global counts_collection
    global query
    global accu_y_test
    global accu_y_test_hat
    global forecasting_collection
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
    forecasting_collection.delete_many({})               
    if connection:
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

        for i in range(len(df)):
            df.loc[i, ['Weekday']]=[time.strptime(df.iloc[i][8], "%A").tm_wday]
            df.loc[i, ['Year']]=float(df.iloc[i][5])
            df.loc[i, ['Month']]=float(df.iloc[i][6])
            df.loc[i, ['Day']]=float(df.iloc[i][7])
            hours,minutes = df.iloc[i][9].split(':')
            df.loc[i, ['Hour']]=float(hours+'.'+minutes)
            df.loc[i, ['busy_slots']]=float(df.iloc[i][4])

        for i in range(len(df)):
            df.loc[i, ['Weekday']]=float(df.iloc[i][8])

        regressor = RandomForestRegressor(n_estimators = 100, random_state = 0)
        MSE = []
        accuracy = []
        for i in range(35):
            window = df.iloc[:100+i*30]
            training = window.iloc[:len(window)-30]
            testing = window.iloc[len(window)-30:]
            x_train = training[['Year','Month','Day','Weekday','Hour']]
            x_test = testing[['Year','Month','Day','Weekday','Hour']]
            y_train = training[['busy_slots']]
            y_test = testing[['busy_slots']]
            X = x_train.copy()
            y = y_train.copy()
            regression = regressor.fit(X, y)
            y_test_hat = (regression.predict(x_test))
            rounded_y_test_hat = np.round(y_test_hat).astype(int)
            df_rounded_y_hat = pd.DataFrame(rounded_y_test_hat)

            y_test_array = y_test['busy_slots'].values

            #print(type(rounded_y_test_hat))
            #print(type(y_test_array))
            #print(y_test_array)
            accu_y_test = accu_y_test + sum(y_test_array)
            accu_y_test_hat = accu_y_test_hat + sum(rounded_y_test_hat)
            accuracy_result = accuracy_with_tolerance(rounded_y_test_hat, y_test_array)
            accuracy.append(accuracy_result)  
            MSE.append(mean_squared_error(y_test, y_test_hat))

        last_count = df.iloc[len(df)-1]
        prediction_df = last_count.to_frame().transpose()
        row_to_duplicate = prediction_df.iloc[0]
        duplicated_rows = pd.concat([row_to_duplicate] * 3, axis=1).transpose()
        prediction_df = pd.concat([prediction_df, duplicated_rows], ignore_index=True)
        prediction_df = prediction_df.drop(['busy_slots'],axis=1)
        prediction_df = prediction_df.drop(['free_slots'],axis=1)
        prediction_df.iloc[1][7]=prediction_df.iloc[0][7]+0.3
        prediction_df.iloc[2][7]=prediction_df.iloc[0][7]+1
        prediction_df.iloc[3][7]=prediction_df.iloc[0][7]+1.3
        initial_hour = datetime.datetime.strptime(prediction_df.iloc[0][8], '%H:%M')
        prediction_df.iloc[1][8]=(initial_hour + datetime.timedelta(minutes=30)).strftime('%H:%M')
        prediction_df.iloc[2][8]=(initial_hour + datetime.timedelta(minutes=60)).strftime('%H:%M')
        prediction_df.iloc[3][8]=(initial_hour + datetime.timedelta(minutes=90)).strftime('%H:%M')

        X = df[['Year','Month','Day','Weekday','Hour']]
        y = df[['busy_slots']]
        regression = regressor.fit(X, y)
        prediction = regressor.predict(prediction_df[['Year','Month','Day','Weekday','Hour']])
        prediction = np.round(prediction)
        prediction = prediction.astype('int')

        prediction_df = prediction_df.assign(busy_slots=prediction)

        
        for i in range(len(prediction_df)):
            year = int(prediction_df.iloc[i][3])
            month = int(prediction_df.iloc[i][4])
            day = int(prediction_df.iloc[i][5])
            timestamp_string = prediction_df.iloc[i]['Hour2']
            timestamp = datetime.datetime.strptime(timestamp_string, '%H:%M').time()
            date = datetime.datetime(year, month, day)
            datetime_object = datetime.datetime.combine(date, timestamp)
            result_string = datetime_object.strftime('%Y-%m-%d-%H-%M')
            prediction_df.loc[i,['timestamp']] = result_string
        
        
        prediction_df['free_slots'] = 22-prediction_df['busy_slots']
        prediction_df = prediction_df.drop(['_id','Year','Month','Day','Weekday','Hour','Hour2'],axis=1)
        data = prediction_df.to_dict(orient='records')
        forecasting_collection.insert_many(data)
        #print(data)




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
    
    try:
        EveryN(timer)
        signal.pause()
    except KeyboardInterrupt:
        alive = False