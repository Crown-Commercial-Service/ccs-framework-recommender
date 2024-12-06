import os
import pandas as pd
from sqlalchemy import create_engine
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from o

# -------------------------------------Credentials--------------------------------------------------------------
# Load configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
SEARCH_CLIENT_ENDPOINT = os.getenv("SEARCH_CLIENT_ENDPOINT")
SEARCH_CLIENT_API_KEY = os.getenv("SEARCH_CLIENT_API_KEY")
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
DB_username = os.getenv("DHW_Username")
DB_password = os.getenv("DHW_Password")


# --------------------------------------Useful functions ------------------------------------------------------

def get_embedding():
    pass



#-------------------------------------Frame work Data extraction from DWH-------------------------------------------

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

# ------------------------------------------Reading the framework description-----------------------------------------
# reading the framework description
# Directory containing the text files
directory_path = r"C:\Users\Naresh.Sampara\PycharmProjects\P9_FRAMEWORD_recommender\Data\Framework"

# Iterate over files in the directory
for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):  # Process only .txt files
        file_path = os.path.join(directory_path, filename)
        
        with open(file_path, 'r', encoding='latin-1') as file:
            content = file.read()
        
        if len(content.split(' '))<50:
            # get the embeddings
            print('yes')

        