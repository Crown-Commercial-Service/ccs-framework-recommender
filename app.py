from flask import Flask, render_template, request
import os
from azure.search.documents.models import VectorizedQuery
from azure.search.documents import SearchClient
from numpy import index_exp
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
import re


# -------------------Credentials---------------------------
# Load configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
SEARCH_CLIENT_ENDPOINT = os.getenv("SEARCH_CLIENT_ENDPOINT")
SEARCH_CLIENT_API_KEY = os.getenv("SEARCH_CLIENT_API_KEY")
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
DB_username = os.getenv("DHW_Username")
DB_password = os.getenv("DHW_Password")
DB_Server = os.getenv('DB_SERVER')

app = Flask(__name__)
app.config['SECRET_KEY'] = "Any scret key"

openai_client = AzureOpenAI(api_key=OPENAI_API_KEY,
                     api_version="2023-07-01-preview",
                     azure_endpoint=OPENAI_ENDPOINT)

search_client = SearchClient(endpoint=SEARCH_CLIENT_ENDPOINT, 
                             index_name="azd-uks-ai-framework_v2",
                             credential=AzureKeyCredential(SEARCH_CLIENT_API_KEY))

#--------------------Useful functions ---------------------
def get_embeddings(text, client = openai_client):
    return client.embeddings.create(model = "text-embedding-ada-002", input=text).data[0].embedding

def search_service(query):
    queryEmbeddings = get_embeddings(query)
    vector_query = VectorizedQuery(vector=queryEmbeddings, k_nearest_neighbors=20, fields="embeddings")
    search_results = search_client.search(search_text=None, vector_queries=[vector_query], select=['frameworknumber', 'framework', 'frameworkdescchunk'])

    results = []
    for result in search_results:

        if result['@search.score']>0.8:
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

def format_llm_response(llm_response):
    """
    Formats the LLM response for HTML rendering:
    - Converts numbered lists into <ul><li> elements.
    - Converts **text** into <strong>text>.
    """
    lines = llm_response.split('\n')
    formatted_lines = []
    for line in lines:
        # Check if the line starts with a numbered bullet point
        if re.match(r"^\d+\.", line.strip()):
            # Wrap in <li> and replace **text** with <strong>text</strong>
            line = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line.strip())
            formatted_lines.append(f"<li>{line[3:].strip()}</li>")  # Skip "1. " at the start
        else:
            # Process lines not part of the numbered list (e.g., general text)
            line = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line.strip())
            formatted_lines.append(f"<p>{line}</p>")

    # Wrap the numbered items in <ul> if present
    if formatted_lines:
        formatted_content = "<ul>" + "".join(formatted_lines) + "</ul>"
    else:
        formatted_content = "<p>No content provided.</p>"

    return formatted_content

# --------------------------- Main app -----------------------------------------

#main route 
@app.route('/', methods=['GET','POST'])
def index():

    query = ''
    reply=''
    if request.method == 'POST':
        query = request.form['query']
        results = search_service(query)
        reply = LLM_response(query, results)
        reply = format_llm_response(reply)

    return render_template('index.html', reply=reply, query=query)

if __name__ == "__main__":
    app.run(debug=True)
