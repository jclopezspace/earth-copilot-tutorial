import os
import json
from dotenv import load_dotenv, find_dotenv
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings 
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, RecursiveJsonSplitter

   
load_dotenv()
AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT")
AOAI_KEY = os.getenv("AOAI_KEY")
AOAI_VERSION = os.getenv("AOAI_VERSION")    
AOAI_EMBEDDING_DEPLOYMENT = os.getenv("AOAI_EMBEDDING_DEPLOYMENT")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
SEARCH_INDEX = os.getenv("SEARCH_INDEX")
    
embeddings: AzureOpenAIEmbeddings = AzureOpenAIEmbeddings(
    azure_deployment=AOAI_EMBEDDING_DEPLOYMENT,
    openai_api_version=AOAI_VERSION,
    azure_endpoint=AOAI_ENDPOINT,
    api_key=AOAI_KEY,
)
    
vector_store: AzureSearch = AzureSearch(
    azure_search_endpoint=SEARCH_ENDPOINT,
    azure_search_key=SEARCH_KEY,
    index_name=SEARCH_INDEX,
    embedding_function=embeddings.embed_query,
    additional_search_client_options={"retry_total": 4},
)

path_to_json = '/Users/minh/veda_collections/'
for file_name in [file for file in os.listdir(path_to_json) if file.endswith('.json')]:
  with open(path_to_json + file_name) as json_file:
    data = json.load(json_file)
    text_splitter = RecursiveJsonSplitter(max_chunk_size = 5000)
    chunks = text_splitter.split_json(json_data=data, convert_lists=True)

    docs = text_splitter.create_documents(texts=[data], convert_lists=True)

    print(f"Number of docs: {len(docs)}")
    for doc in docs:
        vector_store.add_documents(documents=[doc])
        print(doc.page_content)
        print('\n')

# with open("/Users/minh/Downloads/open_veda_collections_minimized.json", 'r') as file:
#     data = json.load(file)


    

print("DONE!")