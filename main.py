from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
from contextlib import asynccontextmanager
from graph.chatbot_graph import ChatbotState,create_chatbot_graph
import uvicorn

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]]

class ChatResponse(BaseModel):
    response: str
    query_type: str
    conversation_history: List[Dict[str, Any]]
    
class PerformanceTestResponse(BaseModel):
    total_time: float
    average_time: float
    results: List[Dict[str, Any]]

class Chatbot:
    def __init__(self):
        # Assuming you have this function defined elsewhere
        self.app, self.components = create_chatbot_graph()
        self.default_thread_id = "1"
    
    async def chat(self, user_input: str,conversation_history:List) -> Dict[str, Any]:
        """Fast chat processing with timing"""

        # Assuming you have ChatbotState defined elsewhere
        initial_state = ChatbotState(user_query=user_input,conversation_history=conversation_history)
    
        try:
            result = await self.app.ainvoke(initial_state.model_dump())
            return {
                "response": result["final_response"],
                "query_type": result["query_type"], 
                "conversation_history": result.get("conversation_history", []),
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "query_type": "error",
                "conversation_history": [],
            }
        

# Global chatbot instance
chatbot_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global chatbot_instance
    print("🚀 Initializing Changi Chatbot...")
    chatbot_instance = Chatbot()
    print("✅ Changi Chatbot initialized successfully!")
    yield
    # Shutdown
    print("🔄 Shutting down Changi Chatbot...")

 # Create FastAPI app
app = FastAPI(
    title="Changi Chatbot",
    description="chatbot API with multiple query types",
    version="1.0.0",
    lifespan=lifespan
)


    
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Fast Chatbot API is running!", "status": "healthy"}



@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    try:
        result = await chatbot_instance.chat(request.message,request.conversation_history)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "chatbot_initialized": chatbot_instance is not None,
        "timestamp": time.time()
    }

    
if __name__ == "__main__":
        print("🚀 Starting Fast Chatbot API...")
        uvicorn.run(
            "main:app",  
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )

    # To run the application:
    # 1. Install dependencies:
    #    pip install fastapi uvicorn python-multipart
    # 
    # 2. Set environment variable:
    #    export OPENAI_API_KEY="your-openai-api-key-here"
    # 
    # 3. Run the server:
    #    python main.py
    #    or
    #    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    #
    # 4. Access the API:
    #    - Swagger UI: http://localhost:8000/docs
    #    - ReDoc: http://localhost:8000/redoc
    #    - Health check: http://localhost:8000/health
        




