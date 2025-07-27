                                                Changi AI Chatbot


Description:
Changi + Jewel RAG chatbot uses a Large Language Model and Vector Database .
This chatbot has knowledge based on website's [Changi Airport](https://www.changiairport.com/in/en.html) and [Jewel Changi Airport](https://www.jewelchangiairport.com/) i.e the data which is scrapable from it.

Feature: 
Used advanced RAG i.e perform vector search with contextual compression and documuent reranking model to retrive accurate and contextual data.
It is capable to do websearch if required.
It handles chitchats of user properly.

Chatbot workflow:
                          
                                              +-----------+
                                              | __start__ |
                                              +-----------+
                                                    *
                                                    *
                                                    *
                                            +---------------+
                                            | analyze_query |
                                          ..+---------------+..
                                      .....         .          .....
                                  ....              .               ....
                              ...                   .                   ...
                      +----------+           +---------------+           +------------+
                      | chitchat |*          | vector_search |         * | web_search |
                      +----------+ ****      +---------------+      ****+------------+
                                      *****         *          *****
                                          ****      *      ****
                                              ***   *   ***
                                               +---------+
                                               | __end__ |
                                               +---------+




Techstack used:
langchain,langgraph,pinecone,langchain_google_genai,langchain_pinecone,bs4,playwright,duckduckgo-search,fastapi
Used Google gen ai embedding 
Used "cross-encoder/ms-marco-MiniLM-L-2-v2" for contextual compression and document reranking. 
Used Google "gemini-flash-2.0" LLM
Used pincone vector database
Used langraph create graph (workflow) of chatbot
Used duckduckgo-search for web search
Used fastapi for creating REST API
Deployment google cloud run