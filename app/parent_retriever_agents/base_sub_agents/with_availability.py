from logging_config import LogParentSubAgent

from app.utils.agent_state_helpers import goal_classifier_parser

from app.goal_prompts.availability import availability_system_prompt
from app.impact_goal_models.availability import AvailabilityGoal
from app.main_agent.user_weekdays_availability import WeekdayAvailabilityAgentNode as AvailabilityNode

from .base import TState
from .base import BaseAgent
# ----------------------------------------- Base Sub Agent For Schedule Items With Availability -----------------------------------------

class BaseAgentWithAvailability(AvailabilityNode, BaseAgent):
    parent = "availability"
    parent_title = "Availability"
    parent_system_prompt = availability_system_prompt
    parent_goal = AvailabilityGoal
    parent_scheduler_agent = AvailabilityNode.availability_node

    def parent_retriever_agent(self, state: TState):
        pass

    # Retrieve availability item that will be used for the current schedule.
    def retrieve_parent(self, state: TState):
        LogParentSubAgent.agent_steps(f"\t---------Retrieving {self.parent_title} for {self.sub_agent_title} Scheduling---------")
        return self.parent_retriever_agent(state)

    # In between node for when the parent is retrieved.
    def parent_retrieved(self, state: TState):
        return {}

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        return goal_classifier_parser(focus_names, goal_class, f"{self.parent}_other_requests")

    # Find other requests from the previous parent message retrieval.
    def parent_requests_extraction(self, state: TState):
        LogParentSubAgent.agent_steps(f"\n---------Extract Other Requests---------")
        return self.other_requests_information_extractor(state, self.parent, f"{self.parent}_other_requests")
