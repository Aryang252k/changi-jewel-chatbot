import time
from typing import Literal,List,Dict,Any
import re
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from model.llms import LLMs
from utils.contextual_retriever import get_cached_components
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel,Field
from prompts.system_prompt import chitchathandler,query_classifier,vectorsearch,websearch
from concurrent.futures import ThreadPoolExecutor
import asyncio

class TaskType(BaseModel):
    type: Literal["chitchat", "vector_search", "web_search"] = Field(..., description="Type of user request")

class ChatbotState(BaseModel):
    user_query: str = ""
    query_type: Literal["chitchat", "vector_search", "web_search", "unknown"] = "unknown"
    search_results: str = ""
    vector_results: str = ""
    final_response: str = "" 
    conversation_history: List[Dict[str, Any]]

#components with caching and faster models
class ChatbotComponents:
    def __init__(self):
        self.llm=LLMs()

        self.classifier_llm = self.llm.gemini_llm(
            temperature=0.1,
            max_tokens=50,  # Very short responses for classification
        )
        
        # Use better model for final responses
        self.response_llm = self.llm.gemini_llm(
            temperature=0.7 
        )

        if not self.classifier_llm:
            self.classifier_llm = self.llm.openai_llm(
            temperature=0.1,
            max_tokens=50,  # Very short responses for classification
        )
            
        if not self.response_llm:
            self.llm.openai_llm(
            temperature=0.7 
        )

        
        
        # Initialize web search with timeout
        self.web_search = DuckDuckGoSearchRun()
        
        # Enhanced chitchat patterns for faster classification
        self.chitchat_patterns = [
            r'\b(hello|hi|hey|hii|howdy|sup)\b',
            r'\b(how are you|what\'s up|whats up|wassup)\b',
            r'\b(good morning|good afternoon|good evening|gm|gn)\b',
            r'\b(bye|goodbye|see you|take care|cya|ttyl)\b',
            r'\b(thank you|thanks|thx|ty)\b',
            r'\b(please|sorry|excuse me)\b',
            r'\b(yes|no|ok|okay|sure|alright)\b'
        ]
        
        # Cache for recent classifications
        self.classification_cache = {}
        self.cache_max_size = 100

        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=3)

 
# query analyzer with caching and pattern matching
def query_analyzer(state: ChatbotState, components: ChatbotComponents) -> ChatbotState:
    """Optimized query analysis with caching and pattern matching"""
    
    query = state.user_query.lower().strip()
    
    # Check cache first
    if query in components.classification_cache:
        state.query_type = components.classification_cache[query]
        return state
    
    # Fast pattern matching for chitchat
    for pattern in components.chitchat_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            state.query_type = "chitchat"
            components.classification_cache[query] = "chitchat"
            return state
    
    # Quick heuristics before LLM call
    web_indicators = [
    "news", "today", "current", "latest", "recent", "update", "updates",
    "weather", "temperature", "rain", "forecast",
    "promotion", "promotions", "events", "happening", "sale", "discount",
    "now", "live", "open now", "closed now",
    "today's flights", "flight status", "delay", "cancellation",
    "2024", "2025", "this week", "this weekend", "next week"
]

    
    if any(word in query for word in web_indicators):
        state.query_type = "web_search"
    else:
        # Only use LLM for ambiguous cases
        try:
            classification_prompt = ChatPromptTemplate.from_template(query_classifier)
            
            messages = classification_prompt.format_messages(query=state.user_query,context=state.conversation_history)
            llm_struct = components.classifier_llm.with_structured_output(TaskType)
            response=llm_struct.invoke(messages)
            classification = response.type.strip().lower()
            
            if classification in ["chitchat", "vector_search", "web_search"]:
                state.query_type = classification
            else:
                state.query_type = "chitchat"
                
        except Exception as e:
            print(f"Classification error: {e}")
            state.query_type = "chitchat"
    
    # Cache the result
    if len(components.classification_cache) < components.cache_max_size:
        components.classification_cache[query] = state.query_type
    
    return state

def chitchat_handler(state: ChatbotState, components: ChatbotComponents) -> ChatbotState:
    """Fast chitchat with predefined responses for common queries"""
    query_lower = state.user_query.lower().strip()
    
    # Quick responses for very common queries
    quick_responses = {
    'hi': "Hello! Welcome to Changi Airport ✈️ How can I assist you today?",
    'hello': "Hi there! I'm your Changi & Jewel assistant. How can I help?",
    'hey': "Hey! Ready to explore Changi or Jewel? Let me know what you need.",
    'how are you': "I'm doing great and ready to help! What can I assist you with at Changi or Jewel?",
    'thanks': "You're very welcome! Let me know if there's anything else you’d like to explore.",
    'bye': "Goodbye! Have a pleasant journey through Changi ✈️",
    'ok': "Got it! Feel free to ask me about facilities, food, or anything else.",
    'yes': "Great! Just let me know what you'd like to find out next.",
    'no': "Alright! If you have any questions about the airport, I’m here to help."
}

    
    if query_lower in quick_responses:
        state.final_response = quick_responses[query_lower]
        return state
    
    chitchat_prompt = ChatPromptTemplate.from_template(chitchathandler)
    
    try:
        messages = chitchat_prompt.format_messages(query=state.user_query,context=state.conversation_history)
        response = components.response_llm.invoke(messages)
        state.final_response = response.content
     
    except Exception as e:
        state.final_response = "Hello! I'm here to help you. How can I assist you today?"
    
    return state

async def fast_contextual_compression_async(query):
    """Fully async contextual compression"""
    try:
        compression_retriever, connected = await get_cached_components()
        if connected and compression_retriever:
            print("Using cached DB connection")
            # Use ainvoke for async operation
            compressed_docs = await compression_retriever.ainvoke(query)
            return compressed_docs
        return []
    except Exception as e:
        print(f"Vector search error: {e}")
        return []

async def vector_search_handler(state: ChatbotState, components: ChatbotComponents) -> ChatbotState:
    """fast parallel processing version"""
    try:
        
        # Create async task for vector search
        vector_task = asyncio.create_task(
            fast_contextual_compression_async(state.user_query)
        )
        
        # Prepare LLM prompt template while vector search runs
        rag_prompt = ChatPromptTemplate.from_template(vectorsearch)
        
        # Wait for vector search with timeout
        docs = await asyncio.wait_for(vector_task, timeout=20)
        
        if docs:
            state.vector_results = "\n".join([
                doc.page_content + "\nlink:" + doc.metadata['source'] 
                for doc in docs
            ])
        else:
            state.vector_results = "No relevant documents found."
        
        # Generate response immediately after vector search completes
        messages = rag_prompt.format_messages(
            query=state.user_query,
            knowledge_base=state.vector_results,
            context=state.conversation_history
            
        )
        
        response = await asyncio.wait_for(
            components.response_llm.ainvoke(messages),
            timeout=40
        )
        state.final_response = response.content
    
        
    except asyncio.TimeoutError:
        state.final_response = "Search timeout - please try again."
    except Exception as e:
        state.final_response = f"Knowledge base error: {str(e)}"
    
    return state

def timeout_web_search_handler(state: ChatbotState, components: ChatbotComponents) -> ChatbotState:
    """Web search with timeout and fallback"""
    def search_with_timeout():
        try:
            return components.web_search.invoke(state.user_query)
        except Exception as e:
            return f"Search unavailable: {str(e)}"
        
    try:
        future = components.executor.submit(search_with_timeout)
        search_results = future.result(timeout=10)  # 10 second timeout
        state.search_results = search_results
        
        # Generate response
        web_prompt = ChatPromptTemplate.from_template(websearch)
        
        messages = web_prompt.format_messages(
            search_results=state.search_results,
            query=state.user_query,
            context=state.conversation_history
        )
        response = components.response_llm.invoke(messages)
        state.final_response = response.content
       
        
    except Exception as e:
        state.final_response = f"Sorry, I couldn't search the web right now. Please try again later."
    
    return state



def create_vector_search_node(components):
    async def vector_search_node(state):
        return await vector_search_handler(state, components)
    return vector_search_node


def create_chatbot_graph():
    """Create speed-optimized LangGraph chatbot"""
    components = ChatbotComponents()
    workflow = StateGraph(ChatbotState)
    workflow.add_node("analyze_query", lambda state: query_analyzer(state, components))
    workflow.add_node("chitchat", lambda state: chitchat_handler(state, components))
    workflow.add_node("vector_search", create_vector_search_node(components))
    workflow.add_node("web_search", lambda state: timeout_web_search_handler(state, components))
   
    
    def route_query(state: ChatbotState) -> str:
        return state.query_type if state.query_type != "unknown" else "chitchat"
    
    # Set up graph flow
    workflow.set_entry_point("analyze_query")
    workflow.add_conditional_edges(
        "analyze_query",
        route_query,
        {
            "chitchat": "chitchat",
            "vector_search": "vector_search", 
            "web_search": "web_search"
        }
    )
    
    workflow.add_edge("chitchat",END)
    workflow.add_edge("vector_search", END)
    workflow.add_edge("web_search", END)
   
    
    app = workflow.compile()
    return app, components






# see graph flow

# app,comp=create_chatbot_graph()

# print(app.get_graph().draw_ascii())