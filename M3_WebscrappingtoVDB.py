import pandas as pd
from openai import AzureOpenAI
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from sqlalchemy import create_engine
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from lxml import html

# -------------------------------------Credentials--------------------------------------------------------------
# Load configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
SEARCH_CLIENT_ENDPOINT = os.getenv("SEARCH_CLIENT_ENDPOINT")
SEARCH_CLIENT_API_KEY = os.getenv("SEARCH_CLIENT_API_KEY")
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
DB_username = os.getenv("DHW_Username")
DB_password = os.getenv("DHW_Password")
DB_Server = os.getenv('DB_SERVER')

# Create clients
search_client = SearchClient(endpoint=SEARCH_CLIENT_ENDPOINT,
                             index_name="azd-uks-ai-framework_v2",
                             credential=AzureKeyCredential(SEARCH_CLIENT_API_KEY))

client = AzureOpenAI(api_key=OPENAI_API_KEY,
                     api_version="2023-07-01-preview",
                     azure_endpoint=OPENAI_ENDPOINT)


# ---------------------------------Useful Functions-------------------------------------------------------------
def get_embedding(text, client=client):
    """
    Generate an embedding for a given text using the specified model.

    Args:
        text (str): The input text to generate the embedding for.
        client (object): The API client used to interact with the embedding model.

    Returns:
        list[float]: The embedding vector for the input text.
    """
    
    return client.embeddings.create(model="text-embedding-ada-002", input=text).data[0].embedding

def Description_Summary(frameworknumber, framework, Content, client=client):
    """
    Generate a summary for the CCS framework description using the specified framework number and content.

    Args:
        frameworknumber (str): The identifier for the framework.
        framework (str): The name of the framework.
        Content (str): The description of the framework to be summarized.
        client (object): The API client for generating completions.

    Returns:
        str: A concise summary of the CCS framework description.
    """
    system_prompt = ("You are an expert at summarizing technical descriptions for clarity and conciseness, "
                     "specializing in the CCS framework. Ensure the response does not exceed 190 words.")
    user_prompt = (f"Summarize the description of the CCS framework '{framework}' (Framework Number: {frameworknumber}). "
                   "The summary should be concise and highlight the key aspects or purpose of the framework, and not exceed 190 words. "
                   f"Here is the content: {Content}")
    
    message_text = [{'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}]

    response = client.chat.completions.create(model='gpt-4o-code', messages=message_text).choices[0].message.content
    
    return response 

def Benefits_Summary(frameworknumber, framework, Content, client=client):
    """
    Generate a summary for the CCS framework description using the specified framework number and content.

    Args:
        frameworknumber (str): The identifier for the framework.
        framework (str): The name of the framework.
        Content (str): The benefits of the framework to be summarized.
        client (object): The API client for generating completions.

    Returns:
        str: A concise summary of the CCS framework description.
    """
    system_prompt = ("You are an expert in identifying and summarizing key benefits of technical frameworks." 
                     "Focus on clarity and conciseness to provide a professional summary suitable for stakeholders or decision-makers. "
                     "Ensure the response does not exceed 190 words.")
    user_prompt = (f"Summarize the primary benefits of the CCS framework '{framework}' (Framework Number: {frameworknumber})"
                   "Highlight the advantages it offers in terms of functionality, usability, and overall value. Ensure the summary is concise and focuses on actionable insight."
                   "Make sure the summary should not exceed 190 words"
                   f"Here is the content: {Content}")
    
    message_text = [{'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}]

    response = client.chat.completions.create(model='gpt-4o-code', messages=message_text).choices[0].message.content
    
    return response 
# --------------------------------DHW--------------------------------------------------------------------------
# Input details for the SQL database
DB_TYPE = "mssql"
DB_USER = DB_username
DB_PWD = DB_password
DB_SERVER = DB_Server
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

# ========================================Web scrapping ========================================================
No_frameworks = df_retrieval['FrameworkNumber'].unique()
current_date = datetime.now().strftime("%Y%m%d")

for framework in No_frameworks:

    url = f'https://www.crowncommercial.gov.uk/agreements/{framework}'
    frameworkname = df_retrieval.loc[df_retrieval['FrameworkNumber']==framework, 'Framework'].unique()[0]

    try: 

        response = requests.get(url)
        #print(framework, response.raise_for_status()) # if it is None, no error
        soup = BeautifulSoup(response.text, 'html.parser')

        tree = html.fromstring(response.content)

        # title
        title = tree.xpath('/html/body/div[4]/main/div[2]/div[1]/h1/text()')[0].strip()
        #print(title)

        # Small description
        desc_small = tree.xpath('/html/body/div[4]/main/div[2]/div[1]/div[1]/text()')[0].strip()

        # Description and Benefits 
        section_headers = soup.find_all('div', class_='govuk-accordion__section-header')
        Headings = []
        for idx, header in enumerate(section_headers):
            sub_title = header.find('h2').find('span').get_text(strip=True)
            Headings.append(sub_title)
        
        wysiwyg_div = soup.find_all('div', class_='wysiwyg-content')

        desc=''
        desc = f'This is the description of the {title} agreement. \n'
        for element in wysiwyg_div[Headings.index('Description')].find_all(['p','li','h4', 'b']):
            desc = desc + element.get_text(strip=True) + '\n'

        benefits =''
        benefits = f'These are the benefits of the {title} agreement. \n'
        for element in wysiwyg_div[Headings.index('Benefits')].find_all(['p', 'li', 'h4', 'b']):
            benefits = benefits + element.get_text(strip=True) + '\n'

        desc_full = desc_small + '\n' + desc
        desc_summary = Description_Summary(framework, frameworkname, desc_full)

        benefit_full = desc_small + '\n' + benefits
        benefit_summary = Benefits_Summary(framework, frameworkname, benefit_full)

        # print(f"-----{framework} Description---")
        # print(desc_summary)
        # print(f"---- {framework} benefits-----")
        # print(benefit_summary)
        # print(len(benefit_summary.split(' ')))

        actions=[]
        count=0
        for  i in range(2):

            if i==0:
                chunk = desc_summary
                ids = f"{framework.replace('.','')}--{current_date}--desc"
            elif i==1:
                chunk = benefit_summary
                ids = f"{framework.replace('.','')}--{current_date}--benefits"

            action = {"id": ids,
                        "frameworknumber": framework,
                        "framework": frameworkname,
                        "frameworkdescchunk":chunk,
                        "embeddings": get_embedding(chunk)}    
            actions.append(action)
        results = search_client.upload_documents(documents = actions)
        print(ids)
        print(f"Upload succeeded: {results[0].succeeded}, {count}") 
    
    except Exception as e:
        print(url)
