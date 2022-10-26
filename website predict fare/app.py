# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 14:25:13 2022

@author: zacha
"""

from flask import Flask,render_template, request
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)
model = joblib.load('gbht.sav')

@app.route('/')
def home():
    return render_template('home.html')



@app.route('/result',methods=['POST'])
def result():
    df = {}
    df['Airline'] = [request.values['Airline']]
    df['Date_of_Journey'] = [request.values['Date_of_Journey']]
    df['Source'] = [request.values['Source']]
    df["Destination"] = [request.values["Destination"]]
    df["Dep_Time"] = [request.values["Dep_Time"]]
    df["Arrival_Time"] = [request.values["Arrival_Time"]]
    df["Duration"] = [request.values["Duration"]]
    df["Total_Stops"] = [request.values["stops"]]
    df['Airline range'] = ['init']
    
    df = pd.DataFrame(df) 
    AdditionalInfo = ['Additional Info_1 Long layover', 'Additional Info_1 Short layover',
       'Additional Info_2 Long layover', 'Additional Info_Business class',
       'Additional Info_Change airports',
       'Additional Info_In-flight meal not included',
       'Additional Info_No check-in baggage included']
    for i in AdditionalInfo:
        df[i] = 0
   
    
    info = request.values['info']
    if info == "In-flight meal not included":
        df['Additional Info_In-flight meal not included'] = 1
    elif info == "No check-in baggage included":
        df['Additional Info_No check-in baggage included'] =1
    elif  info ==  "1 Long layover":
        df['Additional Info_1 Long layover'] =1
    elif   info ==  "Change airports":
        df['Additional Info_Change airports'] =1
    elif  info ==   "1 Short layover ":
        df['Additional Info_1 Short layover'] =1
    elif   info ==  "2 Long layover":
        df['Additional Info_2 Long layover'] =1
    elif  info ==  "Business class":   
        df['Additional Info_Business class']= 1
    
       
        
    low = ['IndiGo','SpiceJet','GoAir','Air Asia','Trujet']
    medium = ['Air India','Jet Airways','Multiple carriers', 'Vistara','Vistara Premium economy',
          'Multiple carriers Premium economy']
    high = ['Jet Airways Business']


   
    df.loc[df['Airline'].isin(low),'Airline range'] = 'low'
    df.loc[df['Airline'].isin(medium),'Airline range'] = 'medium'
    df.loc[df['Airline'].isin(high),'Airline range'] = 'high'
    
    Airlines = {'Air Asia': 0, 'Air India': 1, 'GoAir': 2, 'IndiGo': 3, 'Jet Airways': 4, 'Jet Airways Business': 5, 'Multiple carriers': 6, 
                'Multiple carriers Premium economy': 7, 'SpiceJet': 8, 'Trujet': 9, 'Vistara': 10, 'Vistara Premium economy': 11}
   
    range = {'high': 0, 'low': 1, 'medium': 2}
    
    df['Airline'] = df['Airline'].map(Airlines)
    df['Airline range'] = df['Airline range'].map(range)
    
    import re
    def getSeason(month):
        if (month in [12, 1, 2]):
            return "winter"
        elif (month in [3, 4, 5]):
            return "summer"
        elif (month in [6, 7, 8]):
            return "monsoon"
        else:
            return "spring"
    
    # function for period extraction 
    def getPeriodOfDay(x):
        x = int(x[:2])
        if (x > 4) and (x <= 8):
            return 'Early Morning'
        elif (x > 8) and (x <= 12 ):
            return 'Morning'
        elif (x > 12) and (x <= 16):
            return'Noon'
        elif (x > 16) and (x <= 20) :
            return 'Eve'
        elif (x > 20) and (x <= 24):
            return'Night'
        elif (x <= 4):
            return'Late Night'
    # function for duration counting     
    def getDuration(x):
        replacements = [
        ('h', ':'),
        ('m', ''),
        (' ', '')]
        for old, new in replacements:
            x = re.sub(old, new, x) # regular expression 
        splt = x.split(':')
        hours_to_min = int(splt[0])*60
        if len(splt) == 2 and splt[1].isdigit(): # to add the remaining minutes
            fin = hours_to_min + int(splt[1])
        else:
            fin = hours_to_min
        return fin
    # function for duration counting     
    def getDurationHours(x):
        replacements = [
        ('h', ':'),
        ('m', ''),
        (' ', '')]
        for old, new in replacements:
            x = re.sub(old, new, x)
        splt = x.split(':')
        hours_to_min = int(splt[0])*60
        if len(splt) == 2 and splt[1].isdigit():
            min = int(splt[1])
        else:
            min =0
        return float(splt[0])+round(min/60,2)

    df['month'] = pd.DatetimeIndex(df['Date_of_Journey']).month # month
    df['day'] = pd.DatetimeIndex(df['Date_of_Journey']).day # day
    df['season'] = df['month'].apply(getSeason) # season
    df['Dep_Time_Period'] = df['Dep_Time'].apply(getPeriodOfDay) # period of day (departure time)
    df['Arrival_Time_Period'] =df['Arrival_Time'].apply(getPeriodOfDay) # period of day (arrival time)
    df['Duration_Minutes'] = df['Duration'].apply(getDuration).astype(int) # duration of a flight
    df['Duration_Hours'] =df['Duration'].apply(getDurationHours) # duration of a flight in hours
    df['weekday'] = pd.DatetimeIndex(df['Date_of_Journey']).weekday #The day of the week with Monday=0, Sunday=6.

    #Encoding
    df["Total_Stops"] = df["Total_Stops"].map({'non-stop': 0, '1 stop': 1, '2 stops': 2, '3 stops': 3, '4 stops': 4})  # total stops in a period of flight 
    df["season_enc"] = df["season"].map({'spring': 0, 'summer': 1, 'monsoon': 2, 'winter': 3}) # season of flight 
    df["Arrival_Time_Period_enc"] = df["Arrival_Time_Period"].map({'Early Morning': 0, 'Morning': 1,
                                                                               'Noon': 2, 'Eve': 3, 'Night': 4, 'Late Night': 5}) # name of day periods 
    df["Dep_Time_Period_enc"] = df["Dep_Time_Period"].map({'Early Morning': 0, 'Morning': 1,
                                                                               'Noon': 2, 'Eve': 3, 'Night': 4, 'Late Night': 5}) # name of day periods 
    df['Source'] = df['Source'].map({'Delhi':1, 'Kolkata':2, 'Banglore':3, 'Mumbai':4, 'Chennai':5})
    df['Destination'] = df['Destination'].map({'Cochin':1, 'Banglore':2, 'Delhi':3, 'New Delhi':4, 'Hyderabad':5, 'Kolkata':6})
    
    drop = ['Date_of_Journey','Dep_Time','Arrival_Time','Duration','Dep_Time_Period', 'Arrival_Time_Period','season']
    df =df.drop(drop, axis =1)
    
    df['Duration_Minutes'] = (df['Duration_Minutes'] - 640.23403857)/499.44841461740924
    df['Duration_Hours'] = (df['Duration_Hours'] -10.67044561)/ 8.324281856204824
    ypred = model.predict(df)
    from scipy.special import inv_boxcox
    param_1 = joblib.load('invBoxcox.sav')
    output = inv_boxcox(ypred, param_1)
    
   
    
    return render_template('result.html',prediction_text = "Predicted fare is {} ".format(output))
                           
if __name__ =='__main__':
    app.run()   
