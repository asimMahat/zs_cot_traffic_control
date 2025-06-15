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

        # System prompt with examples to guide the LLM
        self.system_template = (
            "You are an expert traffic engineer. Output ONLY:\n"
            "    <PHASE> <DURATION>\n"
            "Valid phases: GREEN_NORTH_SOUTH or GREEN_EAST_WEST.\n\n"
            "IMPORTANT: Output ONLY the phase and duration, e.g. GREEN_NORTH_SOUTH 20\n"
            "Do NOT explain. Do NOT add any extra text.\n\n"
            "Examples:\n"
            "  State: N=4, E=4, S=4, W=4 → GREEN_NORTH_SOUTH 20  (tie broken to N‐S)\n"
            "  State: N=5, E=6, S=5, W=6 → GREEN_EAST_WEST 20  (EW > NS)\n"
            "  State: N=2, E=10, S=2, W=1 → GREEN_EAST_WEST 20  (EW >> NS)\n"
            "  State: N=8, E=7, S=8, W=7 → GREEN_NORTH_SOUTH 20  (NS > EW)\n"
            "\n"
            "Now given the current state, choose phase.\n"
            "State: N={N}, E={E}, S={S}, W={W} →"
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
