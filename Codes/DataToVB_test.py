import requests
from bs4 import BeautifulSoup
from lxml import html
import os
import pandas as pd
from sqlalchemy import create_engine

password = pd.read_csv(r'C:\Users\Naresh.Sampara\PycharmProjects\P9_FRAMEWORD_recommender\Password.csv')

DB_username = password.loc[password['Type']=='Database', 'UserName'].values[0]
DB_password = password.loc[password['Type']=='Database', 'password'].values[0]

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

No_frameworks = df_retrieval['FrameworkNumber'].unique()

for framework in No_frameworks:

    url = f'https://www.crowncommercial.gov.uk/agreements/{framework}'

    try: 

        response = requests.get(url)
        print(framework, response.raise_for_status()) # if it is None, no error
        soup = BeautifulSoup(response.text, 'html.parser')

        tree = html.fromstring(response.content)

        # title
        title = tree.xpath('/html/body/div[4]/main/div[2]/div[1]/h1/text()')[0].strip()
        #print(title)

        # Small description
        desc_small = tree.xpath('/html/body/div[4]/main/div[2]/div[1]/div[1]/text()')[0].strip()
        #rint(desc_small)

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
        #print(desc)

        benefits =''
        benefits = f'These are the benefits of the {title} agreement. \n'
        for element in wysiwyg_div[Headings.index('Benefits')].find_all(['p', 'li', 'h4', 'b']):
            benefits = benefits + element.get_text(strip=True) + '\n'
        #print(benefits)

        framework_details = title + '\n' +desc_small + '\n' + desc + '\n' + benefits

        foldername = r'C:\Users\Naresh.Sampara\PycharmProjects\P9_FRAMEWORD_recommender\Data\Framework'
        filename = os.path.join(foldername, f'{framework}.txt')
        with open(filename,'w') as file:
            file.write(framework_details)
    
    except Exception as e:
        print(url)