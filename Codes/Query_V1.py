from enum import unique
from azure.search.documents.models import VectorizedQuery
from azure.search.documents import SearchClient
from numpy import index_exp
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
import os

# Load configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
SEARCH_CLIENT_ENDPOINT = os.getenv("SEARCH_CLIENT_ENDPOINT")
SEARCH_CLIENT_API_KEY = os.getenv("SEARCH_CLIENT_API_KEY")
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")

#---------------------Clients --------------------------------
openai_client = AzureOpenAI(api_key=OPENAI_API_KEY,
                     api_version="2023-07-01-preview",
                     azure_endpoint=OPENAI_ENDPOINT)

search_client = SearchClient(endpoint=SEARCH_CLIENT_ENDPOINT, 
                             index_name="azd-uks-ai-framework_v2",
                             credential=AzureKeyCredential(SEARCH_CLIENT_API_KEY))

# ---------------------Useful functions ----------------------
def get_embeddings(text, client = openai_client):
    return client.embeddings.create(model = "text-embedding-ada-002", input=text).data[0].embedding

def search_service(query):
    queryEmbeddings = get_embeddings(query)
    vector_query = VectorizedQuery(vector=queryEmbeddings, k_nearest_neighbors=20, fields="embeddings")
    search_results = search_client.search(search_text=None, vector_queries=[vector_query], select=['frameworknumber', 'framework', 'frameworkdescchunk'])

    results = []
    for result in search_results:

        if result['@search.score']>0.8:
            # results.append({'frameworknumber' : result['frameworknumber'],
            #             'framework' : result['framework'], 
            #             'frameworkdescchunk' : result['frameworkdescchunk'],
            #             "score": result["@search.score"]})
            results.append({'frameworkdescchunk' : result['frameworkdescchunk']})
    
    return results

def LLM_response(Question, Answers, client = openai_client):

    system_prompt = 'You are a chatbot expert in the answering the ccs frameworks recommender .'
    user_prompt = f"Question: {Question}\n\nSearch Results:\n{Answers}\n\nProvide a summary that answers the question:"
    message_text = [{'role':'system', 'content': system_prompt},
                    {'role':'user', 'content':user_prompt}]
    
    response = client.chat.completions.create(model='gpt-4o-code',
                                              messages=message_text).choices[0].message.content
    
    return response 

user_query = "we are from the NHS trust. Which agreements would be suitable for hiring health workers and IT professionals?"
results = search_service(user_query)
chat = LLM_response(user_query, results)

print(user_query)
print(chat)
