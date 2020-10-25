#!/usr/bin/env python
# coding: utf-8

#importing libraries
import pandas as pd
from datetime import datetime



def report_generator():

    #acquiring the datetime now
    now = datetime.now()
    #acquiring the year now
    year_now = now.year
    #acquiring the month now
    mth_now = now.month
    #subtracting by one to get last year
    last_year = year_now - 1

    #since the date values are in int
    #we want to maniuplate them in such a way they present YrM from start of year to current month
    #for both this year and last year
    year_now_start = year_now * 100 + 1
    last_year_start = last_year * 100 + 1
    year_now_end = year_now * 100 + mth_now
    last_year_end = last_year * 100 + mth_now

    print('generating start & end')


    ##importing the xlsx and reading the sheets into dataframes
    xls = pd.ExcelFile('PREMIUM_POLICY_DATA.xlsx')
    policy = pd.read_excel(xls, 'POLICY')
    premium = pd.read_excel(xls, 'PREMIUM')

    print("reading excel file")


    #acquiring the lob values from the policy table
    premium['lob'] = policy['lob']

    #acquiring only the important columns
    data = premium[['YrM','TRANTYPE', 'GWP', 'lob']]
    data = data.copy()

    #Creating a separate column to wrangle TRANTYPE
    data['TXN'] = data['TRANTYPE'].copy()

    #Replacing all non CANC transaction type as BOOKED
    data['TXN'] = data['TXN'].replace({'ENDO':'BOOKED', 'RNWL':'BOOKED', 'NWBS':'BOOKED', 'REIN':'BOOKED'})

    #filtering by the start of the year to current month
    data1 = data[(data['YrM']>=year_now_start ) & (data['YrM']<=year_now_end)]

    #filtering by the start of last year to current month
    data2 = data[(data['YrM']>=last_year_start ) & (data['YrM']<=last_year_end)]

    #merging these 2 fitlered dataframes
    data= pd.concat([data1, data2], axis=0, sort=False)
    data.reset_index(inplace=True)

    #creating an empty dataframe for our final table
    final_df = pd.DataFrame(columns= ['Year', 'Month','YrM', 'LOB', 'GWP Cancelled', 'GWP Booked'])

    #listing unique YrM values
    yearmonth = data['YrM'].unique().tolist()

    #listing unique LOB values
    lobiz = data['lob'].unique().tolist()

    #entries for YrM
    YrM = sorted(yearmonth*len(lobiz))

    #entries for LOB
    LOB = lobiz*len(yearmonth)

    #assigning the values in our YrM and LOB columns
    final_df['YrM'] = YrM
    final_df['LOB'] = LOB

    #for loop to impute the year and month separated from YrM
    for index, item in enumerate (final_df['YrM']):
        final_df['Year'][index] = str(item)[0:4]
        final_df['Month'][index] = str(item)[4:]

    #filling our null fields with a 0.0 float
    final_df.fillna(value=0.0, inplace=True)
    
    print('generating final_df')


    #defining function
    def gwp_calc(row):
        year = str(row['YrM'])[0:4]  #getting the year from each row
        month = str(row['YrM'])[4:]  #getting the month from each row
        lob = row['lob']  #getting lob from each row
        gwp_canc = 0  #empty variable for GWP Cancelled
        gwp_booked = 0  #empty variable for GWP Booked
        
        if row['TXN']== 'CANC':  #condition for filter
            gwp_canc = row['GWP']  #assinging value
        elif row['TXN']== 'BOOKED':  #condition for filter
            gwp_booked = row['GWP']  #assigning value
        
        #checking condition by row in final_df and assigning value    
        current_gwp_cancelled = final_df[(final_df["Year"]==year) & (final_df["Month"]==month) & (final_df["LOB"]==lob)]["GWP Cancelled"].values[0] 
        current_gwp_booked = final_df[(final_df["Year"]==year) & (final_df["Month"]==month) & (final_df["LOB"]==lob)]["GWP Booked"].values[0]
    
        #checking condition by row in final_df and incrementing value
        final_df.loc[(final_df["Year"]== year) & (final_df["Month"]== month) & (final_df["LOB"]==lob),"GWP Cancelled"] =  current_gwp_cancelled + gwp_canc
        final_df.loc[(final_df["Year"]== year) & (final_df["Month"]== month) & (final_df["LOB"]==lob),"GWP Booked"] =  current_gwp_booked + gwp_booked

    print("generating function to sum")


    #applying the function for every row in the data
    for i in list(range(len(data))):
        gwp_calc(data.loc[i])

    print("applying function to all rows")


    final_df = final_df[['Year', 'Month', 'LOB', 'GWP Cancelled', 'GWP Booked']]

    #saving the final table to csv for management perusal
    final_df.to_csv('report.csv', index = False)
    
    print("generating final report")


from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
#importing flask and scheduler

#assigning scheduler and dictating time interval of last day of the month to run code
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(report_generator, 'cron', day='L')
scheduler.start()

app = Flask(__name__)


if __name__ == '__main__':
    app.run()