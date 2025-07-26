import os
import asyncio

_cached_components = None
_components_lock = asyncio.Lock()

async def get_cached_components():
    """Cache expensive initialization - async version"""
    global _cached_components
    
    if _cached_components is not None:
        return _cached_components
    
    async with _components_lock:
        if _cached_components is not None:
            return _cached_components
        
        try:
            from dotenv import load_dotenv
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            from pinecone import Pinecone
            from langchain_pinecone import PineconeVectorStore
            from langchain_community.cross_encoders import HuggingFaceCrossEncoder
            from langchain.retrievers import ContextualCompressionRetriever
            from langchain.retrievers.document_compressors import CrossEncoderReranker
            
            load_dotenv()
            pinecone_api_key = os.environ.get("PINECONE_API_KEY")
            api_key = os.getenv("GEMINI_API_KEY")
            
            # Initialize components
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001", 
                google_api_key=api_key
            )
            pc = Pinecone(api_key=pinecone_api_key)
            
            index_name = "changi-jewel-index"
            if pc.has_index(index_name):
                index = pc.Index(index_name)
                vector_store = PineconeVectorStore(index=index, embedding=embeddings)
                
                # Optimized retriever settings for speed
                retriever = vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 8}
                )
                
                # Lighter, faster model
                model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-2-v2")
                compressor = CrossEncoderReranker(model=model, top_n=5)
                
                compression_retriever = ContextualCompressionRetriever(
                    base_compressor=compressor,
                    base_retriever=retriever
                )
                
                _cached_components = (compression_retriever, True)
                print("Components cached successfully")
                return _cached_components
            
            _cached_components = (None, False)
            return _cached_components
            
        except Exception as e:
            print(f"Failed to initialize components: {e}")
            _cached_components = (None, False)
            return _cached_components


# a=contextual_compression(query="hel")      
# print(a)