from utils.split_docs import get_docs
from uuid import uuid4
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import os
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from utils.scrapper import generate_data_json





def insert_vectors():
    load_dotenv()
    api_key=os.getenv("GEMINI_API_KEY")
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
   
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=api_key)
    pc = Pinecone(api_key=pinecone_api_key)
    
    index_name = "changi-jewel-index" 

    if pc.has_index(index_name):
        print("Connected to db.")
        index = pc.Index(index_name)
        vector_store = PineconeVectorStore(index=index, embedding=embeddings)
        documents=get_docs()
        uuids = [str(uuid4()) for _ in range(len(documents))]
        vector_store.add_documents(documents=documents, ids=uuids)
        print("Successfully inserted data to db")

           
# json data generator
# generate_data_json()

# to insert data
# insert_vectors()