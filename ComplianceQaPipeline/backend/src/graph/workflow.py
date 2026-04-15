from langgraph.graph import StateGraph,END
from .node import index_video_node,audio_content
from .state import VideoAuditState

def create_graph():
        workflow=StateGraph(initial_state=VideoAuditState, state_schema=VideoAuditState)
        workflow.add_node("indexer",index_video_node)
        workflow.add_node("audio_compliance",audio_content)
        workflow.set_entry_point("indexer")
        workflow.add_edge("indexer","audio_compliance")
        workflow.add_edge("audio_compliance",END)
        app=workflow.compile()
        return app
app=create_graph()
