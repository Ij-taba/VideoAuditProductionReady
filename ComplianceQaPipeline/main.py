import os
import logging
import uuid
import json
from pprint import PrettyPrinter
import glob
from dotenv import load_dotenv
load_dotenv(override=True)
from backend.src.graph.workflow import app
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger=logging.getLogger("brand_guardian_runner")

def run_cli_simulation():
    logger.info("Starting CLI simulation...")
    # Simulate a workflow run with test data
    secesion_id=str(uuid.uuid4())

    initial_input={"video_url": "https://youtu.be/dT7S75eYhcQ",
                   "video_id":secesion_id[:8],
                   "compliance_results":[],
                   "errors":[]}
    print(f"Initial Input:{json.dumps(initial_input,indent=2)}")
    print("initializeing Workflow")
    try:
        result=app.invoke(initial_input)
        print("compliance Audit  Report")
        print(f"video_if->{result.get('video_id')}")
        print(f"final_status->{result.get('final_status')}")
        print("violateing detected")
        res=result.get("compliance_results",[])
        if not res:
            print("No compliance issues detected.")
        else:
            for issue in res:
                print(f"-severirty-> {issue.get('severity')}, -Category-> {issue.get('category')}, -Description-> {issue.get('description')}")
        print("final Report")
        print(result.get("report"))
    except Exception as e:
        logger.error(f"Error during CLI simulation: {e}")

if __name__ == "__main__":
    run_cli_simulation()
