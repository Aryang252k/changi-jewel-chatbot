from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI



class LLMs:
    def __init__(self):
        load_dotenv()
        self.gemini_api_key=os.getenv("GEMINI_API_KEY")
        self.openai_api_key=None

    def gemini_llm(self,model="gemini-2.0-flash",**kwargs):
        if self.gemini_api_key: 
                    return ChatGoogleGenerativeAI(model=model,google_api_key=self.gemini_api_key,**kwargs)
               

    def openai_llm(self,model="gpt-3.5-turbo",**kwargs):
        if self.openai_api_key: 
               return  ChatOpenAI(model=model,google_api_key=self.gemini_api_key,**kwargs)
    
