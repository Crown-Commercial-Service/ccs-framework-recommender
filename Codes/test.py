import os
import pandas as pd
from sqlalchemy import create_engine
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from datetime import datetime

DB_username = os.getenv("DHW_Username")
DB_password = os.getenv("DHW_Password")

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

engine = create_engine(conn_string)

conn = engine.connect()

# Read the data from the framework
sql = """select RecordID, Category, SubCategory, Framework, Framework_key, FrameworkNumber, FrameworkLotsID, LotNumber, LotDescription, Status, FrameworkStatus from Frameworks
where FrameworkStatus = 'Live'"""

df_retrieval = pd.read_sql(sql, conn)

directory_path = r"C:\Users\Naresh.Sampara\PycharmProjects\P9_FRAMEWORD_recommender\Data\Framework"

# Iterate over files in the directory
for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):  # Process only .txt files
        fwno= filename[0:len(filename)-4]

        frameworkname = df_retrieval.loc[df_retrieval['FrameworkNumber']==fwno, 'Framework'].unique()[0]
        print(fwno, frameworkname)
