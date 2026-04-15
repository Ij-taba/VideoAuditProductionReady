import json 
import logging 
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from .state import VideoAuditState, Compliance

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage,SystemMessage
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from ..services.video_indexer import VideoIndexerService
from langchain_community.vectorstores import AzureSearch
logger=logging.getLogger("brand_guardian")
logging.basicConfig(level=logging.INFO)


# node 1
# video inder
def index_video_node(VideoAuditState:VideoAuditState)->Dict[str, Any]:
    logger.info("Indexing video...")
    # Simulate video indexing and metadata extraction
    url=VideoAuditState['video_url']
    video_id=VideoAuditState['video_id']

    temp_path="/tmp/video.mp4"
    try:
        vi = VideoIndexerService()
        if "youtube.com" in url or "youtu.be" in url:
            vi.download_youtube_video(url, output_path=temp_path)
        else:
            raise Exception("provide a valid Url")
        azure_video_id = vi.upload_video(temp_path, video_id)
        if azure_video_id is None:
            azure_video_id = video_id
        logger.info(f"Video indexed successfully with Azure Video ID: {azure_video_id}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raw_data = vi.wait_for_processing(azure_video_id)
        clean_data = vi.extract_data(raw_data)
        return clean_data
    except Exception as e:
        logger.error(f"Error initializing VideoIndexer: {e}")
        return{
            "errors":[str(e)],
            "final_status":"failed",
            "ocr_text":[],
            "transcript":""
        }
    

#Node 2 
# complince check
def audio_content(VideoAuditState:VideoAuditState)->Dict[str, Any]:  
    transcript=VideoAuditState.get("transcript","")
    if not transcript:
        logger.warning("No transcript available for audio content analysis.")
        return {
            "final_status":"FAILED",
            "final_report":"No transcript available for analysis.because video inder failed"
        }
    llm=AzureChatOpenAI(
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        temperature=0.0,
    )
    embeddings=AzureOpenAIEmbeddings(
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYEMENT"),
    )

    vector_store=AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX"),
            embedding_function=embeddings.embed_query
    )
    ocr_text=VideoAuditState.get("ocr_text",[])
    text=transcript+" ".join(ocr_text)
    doc=vector_store.similarity_search(query=text,k=3)
    text="\n\n".join([d.page_content for d in doc])
    system_prompt = f"""
    You are a Senior Brand Compliance Auditor.
    
    OFFICIAL REGULATORY RULES:
    {text}
    
    INSTRUCTIONS:
    1. Analyze the Transcript and OCR text below.
    2. Identify ANY violations of the rules.
    3. Return strictly JSON in the following format:
    
    {{
        "compliance_results": [
            {{
                "category": "Claim Validation",
                "severity": "CRITICAL",
                "description": "Explanation of the violation..."
            }}
        ],
        "status": "FAIL", 
        "final_report": "Summary of findings..."
    }}

    If no violations are found, set "status" to "PASS" and "compliance_results" to [].
    """

    user_message = f"""
    VIDEO METADATA: {VideoAuditState.get('video_metadata', {})}
    TRANSCRIPT: {transcript}
    ON-SCREEN TEXT (OCR): {ocr_text}
    """
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        # --- FIX: Clean Markdown if present (```json ... ```) ---
        content = response.content
        if "```" in content:
            # Regex to find JSON inside code blocks
            content = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL).group(1)
            
        audit_data = json.loads(content.strip())
        
        return {
            "Compliance_results": audit_data.get("compliance_results", []),
            "final_status": audit_data.get("status", "FAIL"),
            "final_report": audit_data.get("final_report", "No report generated.")
        }

    except Exception as e:
        logger.error(f"System Error in Auditor Node: {str(e)}")
        # Log the raw response to see what went wrong
        logger.error(f"Raw LLM Response: {response.content if 'response' in locals() else 'None'}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL"
        }