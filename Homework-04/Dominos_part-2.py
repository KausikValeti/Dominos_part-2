# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 13:25:44 2019

@author: vkaus
"""

import sqlite3
import pandas as pd
from haversine import haversine,Unit

conn=sqlite3.connect('Dominos_2.db')
cursor=conn.cursor()

cursor.execute('create table if not exists Distributor_data(Distri_Center_ids text,address text,latitude_dis real,longitude_dis real,demand float,cost float)')
distributor_data=[]
distributor_data=pd.read_csv(r'Distributor_Data.csv')
distributor_data = distributor_data.values.tolist()
cursor.executemany('INSERT INTO Distributor_data VALUES(?,?,?,?,?,?)', distributor_data)
rowsA=cursor.fetchall()

cursor.execute('create table if not exists Average_demand(store_id integer, avg_daily_demand integer,Distri_Center_ids text)')
average_demand=[]
average_demand=pd.read_csv(r'average_daily_demand.csv')
average_demand=average_demand.values.tolist()
cursor.executemany('INSERT INTO Average_demand VALUES(?,?,?)', average_demand)
rowsB=cursor.fetchall()

cursor.execute('create table if not exists Ardent_mills(mill_id text,latit_mill real,long_mill real,supply integer,Cost_per_unit float)')
ardent_mills=[]
ardent_mills=pd.read_csv(r'Ardent_Mills_Data.csv')
ardent_mills=ardent_mills.values.tolist()
cursor.executemany('INSERT INTO Ardent_mills VALUES(?,?,?,?,?)', ardent_mills)
rowsC=cursor.fetchall()

cursor.execute('select Ardent_mills.mill_id,Distributor_data.Distri_Center_ids,latit_mill,long_mill,latitude_dis,longitude_dis FROM Ardent_mills cross join Distributor_data')
rows_lat_lon=cursor.fetchall()
distance=dict()
for mill,distri,mil_lat,mil_long,dis_lat,dis_long in rows_lat_lon:
    distance[mill.replace(' ',''),distri.replace(' ','')]=haversine((mil_lat,mil_long),(dis_lat,dis_long),unit=Unit.MILES)

cursor.execute('select Distri_Center_ids,sum(avg_daily_demand)*7 from Average_demand GROUP by Distri_Center_ids')
rows_demand=cursor.fetchall()
demand=dict(rows_demand)

cursor.execute('select mill_id,supply from Ardent_mills')
rows_supply=cursor.fetchall()
Supply=dict()
for center,supply in rows_supply:
    Supply[center.replace(' ','')]=int(supply.replace(',',''))


cursor.execute('select Distri_Center_ids,cost from Distributor_data')
rows_cost=cursor.fetchall()
Trans_Cost=dict()
for dis_id,dis_cost in rows_cost:
    Trans_Cost[dis_id.replace(' ','')]=dis_cost

cursor.execute('select mill_id,Cost_per_unit from Ardent_mills')
rows_prod_cost=cursor.fetchall()
Production_Cost=dict()
for pro_mil_id,pro_cost in rows_prod_cost:
    Production_Cost[pro_mil_id.replace(' ','')]=pro_cost


conn.commit()
conn.close()

abc=dict()

abc['demand']=demand
abc['distance']=distance
abc['Supply']=Supply
abc['Transportation_Cost']=Trans_Cost
abc['Production_Cost']=Production_Cost


from gurobipy import *

Ardent_Dominos=Model()
Ardent_Dominos.modelSense=GRB.MINIMIZE

#indices
mills=abc['Production_Cost'].keys()
distri_centers=abc['Transportation_Cost'].keys()

abc['retool_cost_mill']={m:700000 for m in mills}

#Decision variables

transportation_mill_center={}

for m in mills:
    for d in distri_centers:
        transportation_mill_center[m,d]=Ardent_Dominos.addVar(obj=(abc['distance'][m,d]*abc['Transportation_Cost'][d]* (3.25/(880*50*3.57))*abc['demand'][d] + abc['Production_Cost'][m]*(3.25/(50*3.57))*abc['demand'][d]),vtype=GRB.BINARY,name=f'Transportation{m}_{d}')
        
        
        
production_mill={}

for m in mills:
    production_mill[m]=Ardent_Dominos.addVar(obj=(abc['retool_cost_mill'][m]),vtype=GRB.BINARY,name=f'cost_{m}')
    
    

Ardent_Dominos.update()

my_constr={}      
 
for d in distri_centers:
    cname=f'serviced_{d}'
    my_constr[cname]=Ardent_Dominos.addConstr(quicksum(transportation_mill_center[m,d] for m in mills) == 1,name=cname)
    
    
for m in mills:
    cname=f'supply_{m}'
    my_constr[cname]=Ardent_Dominos.addConstr(quicksum(transportation_mill_center[m,d]*abc['demand'][d]*3.25 for d in distri_centers) <= (production_mill[m]*abc['Supply'][m]*(3.57*50)))



Ardent_Dominos.update()
Ardent_Dominos.write('Ardent_Dominos.lp')
Ardent_Dominos.optimize()
Ardent_Dominos.write('Ardent_Dominos.sol')


for k,v in enumerate(transportation_mill_center.items()):
    if v[1].x !=0:
        print(v[0],v[1].x)


for k,v in enumerate(production_mill.items()):
    if v[1].x !=0:
        print(v[0],v[1].x)














































