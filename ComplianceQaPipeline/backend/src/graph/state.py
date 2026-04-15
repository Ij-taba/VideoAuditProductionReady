import operator
from typing import Any, TypedDict,Dict, List, Optional, Tuple,Annotated

class Compliance(TypedDict):
    description:str
    category:str
    severity:str
    timestamp:Optional[str]

class VideoAuditState(TypedDict):
    video_url:str
    video_id:str
    local_file_path:Optional[str]
    video_metaData:Dict[str, Any]
    transcript:Optional[str]
    ocr_text:Optional[list[str]]
    Compliance_results:Annotated[list[Compliance], operator.add] 
    final_status:str
    final_report:str
    errors:Annotated[List[str], operator.add]
    
