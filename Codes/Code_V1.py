import pandas as pd
import numpy as np
import os

from sqlalchemy import create_engine
import time
import numpy as np
# import tensorflow as tf
# import tensorflow_recommenders as tfrs
from itertools import product
from random import shuffle
from sklearn.model_selection import TimeSeriesSplit

DB_username = os.getenv("DHW_Username")
DB_password = os.getenv("DHW_Password")

# step 1 databse connection 
# Input details for the SQL database
DB_TYPE = "mssql"
DB_USER = DB_username
DB_PWD = DB_password
DB_SERVER = "azp-ukw-sql01.database.windows.net"
DB_PORT = "1433"
DB_NAME = "PBI"
DB_DRIVER = "SQL Server"
# Connect to the database
conn_string = '{}://{}:{}@{}:{}/{}?driver={}'.format(DB_TYPE, DB_USER, DB_PWD, DB_SERVER, DB_PORT, DB_NAME, DB_DRIVER)
from sqlalchemy import create_engine
engine = create_engine(conn_string)
# Open a connection
conn = engine.connect()


