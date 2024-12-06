import os
import pandas as pd
from sqlalchemy import create_engine
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from datetime import datetime

# -------------------------------------Credentials--------------------------------------------------------------
# Load configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
SEARCH_CLIENT_ENDPOINT = os.getenv("SEARCH_CLIENT_ENDPOINT")
SEARCH_CLIENT_API_KEY = os.getenv("SEARCH_CLIENT_API_KEY")
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
DB_username = os.getenv("DHW_Username")
DB_password = os.getenv("DHW_Password")

# Create clients
search_client = SearchClient(endpoint=SEARCH_CLIENT_ENDPOINT,
                             index_name="azd-uks-ai-framework",
                             credential=AzureKeyCredential(SEARCH_CLIENT_API_KEY))

client = AzureOpenAI(api_key=OPENAI_API_KEY,
                     api_version="2023-07-01-preview",
                     azure_endpoint=OPENAI_ENDPOINT)

# --------------------------------------Useful functions ------------------------------------------------------

def get_embedding(text, client=client):
    
    return client.embeddings.create(model="text-embedding-ada-002", input=text).data[0].embedding

def chunk_text(text, chunk_size=100, overlap_percent=30):
    words = text.split()
    overlap_size = int(chunk_size * overlap_percent / 100)
    
    for i in range(0, len(words), chunk_size - overlap_size):
        yield " ".join(words[i:i + chunk_size])

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

# Define variables
current_date = datetime.now().strftime("%Y%m%d")


# Iterate over files in the directory
for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):  # Process only .txt files
        file_path = os.path.join(directory_path, filename)
        fwno= filename[0:len(filename)-4]
        frameworkname = df_retrieval.loc[df_retrieval['FrameworkNumber']==fwno, 'Framework'].unique()[0]
        
        with open(file_path, 'r', encoding='latin-1') as file:
            content = file.read()
        
        if content:
            #"id, frameworknumber, framework, frameworkdescchunk, embeddings" 
            actions = []
            count = 0
            for chunck_idx, chunk_content in enumerate(chunk_text(content)):
                ids = f"{fwno.replace('.','')}--{current_date}-{count}"

                action = {"id": ids,
                          "frameworknumber": fwno,
                          "framework": frameworkname,
                          "frameworkdescchunk":chunk_content,
                          "embeddings": get_embedding(chunk_content)}    
                actions.append(action)
                count+=1

            results = search_client.upload_documents(documents = actions)
            print(ids)
            print(f"Upload succeeded: {results[0].succeeded}, {count}")              

        