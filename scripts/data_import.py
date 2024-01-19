#This is the file for the main import loop for the bet data values. This will pull
#the values and push them to a holding database. From that database or table, the
#values can be pulled.

#The idea of this file is keep the costs of requests down the number of calculations
#computed by the program to a reasonable level, between: 10,000,000 - 200,000,000 / day.

import http.client as client
import http
import uuid
from datetime import datetime, timezone

apiKey = "098b369ca52dc641b2bea6c901c24887"
host = "api.the-odds-api.com"

conn = client.HTTPSConnection(host)

#Add the sports and market arrays

#Pull the data from the api

#Save to its own table - create table named all_data
# - add columns later today...