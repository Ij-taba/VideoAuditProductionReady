import os
import logging
import yt_dlp
import time
import requests
from azure.identity import DefaultAzureCredential
logger=logging.getLogger("brand_guardian")

class VideoIndexerService:
    def __init__(self):
        # Enable mock mode for offline testing if env var set to 'true'
        self.mock = os.getenv("VIDEO_INDEXER_MOCK", "false").lower() == "true"
        self.account_id=os.getenv("AZURE_VI_ACCOUNT_ID")
        self.location=os.getenv("AZURE_VI_LOCATION")
        self.subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group=os.getenv("AZURE_RESOURCE_GROUP")
        self.vi_name=os.getenv("AZURE_VI_NAME")
        self.credential=DefaultAzureCredential()
    def genrate_token(self):
        # genrate Arm token
        try:  
                    if self.mock:
                            logger.info("Mock: generating ARM token")
                            return "mock-arm-token"
                    token=self.credential.get_token("https://management.azure.com/.default")
                    return token.token
        except Exception as e:
            logger.error(f"Error genrating token: {e}")
            return None
    def get_account_token(self,arm_token):
        # Build the full URL for generating an account access token
        url = (
            f"https://management.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
            f"/generateAccessToken?api-version=2021-11-01"
        )
        headers={"Authorization": f"Bearer {arm_token}"}
        payload={"permissionType": "Contributor","scope": "Account"}
        if self.mock:
            logger.info("Mock: generating account token")
            return "mock-account-token"
        response=requests.post(url,headers=headers,json=payload)
        if response.status_code!=200:
            logger.error(f"Error genrating account token: {response.text}")
            raise Exception(f"Error genrating account token: {response.text}")
        return response.json().get("accessToken")
    def download_youtube_video(self,url,output_path="temp_video.mp4"):
        ydl_opts={
            "format": "best[ext=mp4]",
            "outtmpl": output_path,
            "quiet": False,
            "no_warnings": False,
            "extractor_args":{"youtube":{"player_clieent":["web","android"]}},
            "http_headers":{
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"Video downloaded successfully: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise Exception(f"Error downloading video: {e}")
    def upload_video(self,video_path,video_name):
        arm_token=self.genrate_token()
        access_token=self.get_account_token(arm_token)
        upload_url=f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
        parms={
            "name": video_name,
            "privacy": "Private",
            "accessToken": access_token,
            "indexingPreset": "Default",
        }
        logger.info(f"Uploading video: {video_name}")
        try:
            if self.mock:
                logger.info(f"Mock: uploaded video, returning mock id for {video_name}")
                return f"mock-{video_name}"
            with open(video_path,"rb") as video_file:
                files={"file":video_file}
                response=requests.post(upload_url,params=parms,files=files)
            if response.status_code!=200:
                logger.error(f"Error uploading video: {response.text}")
            # Try to extract and return the uploaded video id
            try:
                data = response.json()
                return data.get("id") or data.get("videoId")
            except Exception:
                return None
            logger.info(f"Video uploaded successfully: {video_name}")
            
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            raise Exception(f"Error uploading video: {e}")
    def wait_for_processing(self,video_id):
        logger.info(f"Waiting for video processing: {video_id}")
        while True:
            if self.mock:
                logger.info("Mock: simulating processing completion")
                # Return a simplified structure compatible with `extract_data`
                return {
                    "videos": [
                        {"insights": {"transcript": [{"text": "This is a mocked transcript."}], "ocr": [{"text": "Mock OCR text."}]} }
                    ],
                    "summarizedInsights": {"duration": 42}
                }
            arm_token=self.genrate_token()
            vi_token=self.get_account_token(arm_token)
            status_url=f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
            params={"accessToken": vi_token}
            response=requests.get(status_url,params=params)

            if response.status_code!=200:
                logger.error(f"Error checking video status: {response.text}")
                raise Exception(f"Error checking video status: {response.text}")
            
            state=response.json().get("state")
            
            logger.info(f"Current video state: {state}")
            if state=="Processed":
                logger.info(f"Video processing completed: {video_id}")
                return response.json()
                
            elif state in ["Failed","Deleted"]:
                logger.error(f"Video processing failed: {video_id}")
                raise Exception(f"Video processing failed: {video_id}")
            time.sleep(30)    
    def extract_data(self,vi_json):
        transcript_lines=[]
        for v in vi_json.get("videos",[]):
            insights=v.get("insights",{})
            transcript=insights.get("transcript",[])
            for t in transcript:
                text=t.get("text")
                if text:
                    transcript_lines.append(text)   
        ocr_lines=[]
        for v in vi_json.get("videos",[]):
            insights=v.get("insights",{})
            ocr=insights.get("ocr",[])
            for o in ocr:
                text=o.get("text")
                if text:
                    ocr_lines.append(text)
        return{
            "transcript":" ".join(transcript_lines),
            "ocr":" ".join(ocr_lines),
            "video_metadata":{
                "duration":vi_json.get("summarizedInsights",{}).get("duration"),
                "plateform":"youtube",
            }}                                