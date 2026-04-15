import os
import glob
import logging
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
load_dotenv(override=True)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger=logging.getLogger("brand_guardian")

def index_document():
    current_dir=os.path.dirname(os.path.abspath(__file__))
    data_folder=os.path.join(current_dir,"../../backend/data")
    # check enviornment veriables
    logger.info("="*60)
    logger.info("Checking environment variables...")
    logger.info(f"AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"AZURE_OPENAI_DEPLOYMENT: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_KEY: {'set' if os.getenv('AZURE_SEARCH_KEY') else 'not set'}")
    logger.info(f"Embedding Deployment: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')}")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info("="*60)
    # validate enviornment variables
    required_env_vars=[
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]
    missing_vars=[var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return
    try:
        logger.info("loadeing openAi embeddings...")
        embeddings=AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        logger.info("embedding model load successfully")
    except Exception as e:
        logger.error(f"Error loading AzureOpenAIEmbeddings: {e}")
        return
    logger.info("Setting Azure Search vector store...")
    try:
        logger.info("loadeing Azure Search...")
        vector_store=AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            embedding=embeddings.embed_query
        )
        logger.info("embedding model load successfully")
    except Exception as e:
        logger.error(f"Error loading AzureOpenAIEmbeddings: {e}")
        return
    pdf_files=glob.glob(os.path.join(data_folder,"*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {data_folder}")
        return
    all_splits=[]
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing file: {pdf_file}")
            loader=PyPDFLoader(pdf_file)
            documents=loader.load()
            text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
            split_docs=text_splitter.split_documents(documents)
            for split in split_docs:
                split.metadata["source"]=os.path.basename(pdf_file)
            all_splits.extend(split_docs)
            # embeddings.add_documents(split_docs)
            logger.info(f"Successfully indexed {pdf_file}")
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")
        if all_splits:
            logger.info(f"Adding {len(all_splits)} document splits to Azure Search...")
            try:
                embeddings.add_documents(all_splits)
                logger.info("Documents added to Azure Search successfully")
                
            except Exception as e:
                logger.error(f"Error adding documents to Azure Search: {e}")    
        else:
            logger.warning("No document splits to add to Azure Search")

if __name__=="__main__":
    index_document()