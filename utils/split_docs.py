from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json


def get_docs():

    with open("./data/scraped_changi_jewel.json", "r") as f:
        scraped_data=json.load(f)

    docs = [Document(page_content=entry["text"].replace("\n",'').replace('\u00a0',''), metadata=entry["metadata"]) for entry in scraped_data]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", "",'.',',',':']
    )

    split_docs = splitter.split_documents(docs)

    return split_docs
