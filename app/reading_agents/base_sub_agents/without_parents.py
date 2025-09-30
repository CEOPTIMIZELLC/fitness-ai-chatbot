from langgraph.graph import StateGraph, START, END

from .base import BaseAgent, determine_read_operation

class BaseAgentWithoutParents(BaseAgent):
    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("read_user_current_element", self.read_user_current_element)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "operation_is_read")

        # Whether the read operations is for a single element or plural elements.
        workflow.add_conditional_edges(
            "operation_is_read",
            determine_read_operation, 
            {
                "singular": "read_user_current_element",                # Read the current element.
                "plural": "get_user_list"                               # Read all user elements.
            }
        )

        workflow.add_edge("read_user_current_element", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

