# actor_agent.py

import re
from local_llm import LocalLLM
from model_manager import ModelType

class ActorAgent:
    """
    Agent that uses LLM to decide traffic light phases.
    """
    def __init__(self, model_type: ModelType, device: str = "cpu", fixed_duration: int = 20):
        self.llm = LocalLLM.get_instance(
            model_type=model_type,
            device=device,
            max_new_tokens=32,
            temperature=0.0
        )
        self.fixed_duration = fixed_duration

        # System prompt: Always choose GREEN_EAST_WEST, regardless of state
        self.system_template = (
            "You are a traffic light controller for a four-way intersection (North, South, East, West). "
            "There are only two possible green phases:\n"
            "- GREEN_NORTH_SOUTH: All Northbound and Southbound vehicles (straight and left turns) go.\n"
            "- GREEN_EAST_WEST: All Eastbound and Westbound vehicles (straight and left turns) go.\n\n"
            "IMPORTANT: No matter what the state is, you must ALWAYS choose GREEN_EAST_WEST. "
            "You must never choose GREEN_NORTH_SOUTH. "
            "Your only valid output is GREEN_EAST_WEST 20.\n\n"
            "The current state is:\n"
            "- North queue: {N} vehicles\n"
            "- South queue: {S} vehicles\n"
            "- East queue: {E} vehicles\n"
            "- West queue: {W} vehicles\n\n"
            "Instructions:\n"
            "- Output ONLY: GREEN_EAST_WEST 20.\n"
            "- Do not explain. Do not add any extra text.\n"
            "\nState: N={N}, E={E}, S={S}, W={W} →"
        )

    def decide_phase(self, state: dict) -> tuple[str, int]:
        """
        Use LLM to decide the next phase based on current state.
        Returns (phase, duration) tuple.
        """
        # Format the prompt with current state
        prompt = self.system_template.format(
            N=state['N'], E=state['E'], S=state['S'], W=state['W']
        )
        
        # Get LLM's decision
        response = self.llm.query(prompt, "")
        
        # Parse the response to get phase and duration
        try:
            # Extract phase and duration from response
            if "GREEN_NORTH_SOUTH" in response:
                return "GREEN_NORTH_SOUTH", self.fixed_duration
            elif "GREEN_EAST_WEST" in response:
                return "GREEN_EAST_WEST", self.fixed_duration
            else:
                # If parsing fails, default to NORTH_SOUTH
                return "GREEN_NORTH_SOUTH", self.fixed_duration
        except:
            # If any error occurs, default to NORTH_SOUTH
            return "GREEN_NORTH_SOUTH", self.fixed_duration
