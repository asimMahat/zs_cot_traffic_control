# actor_agent.py

import re
from local_llm import LocalLLM

class ActorAgent:
    """
    Zero‐Shot Chain‐of‐Thought “actor” agent using Falcon-RW-1B.
    Given a dictionary of queue lengths at four approaches, it queries
    the local LLM to decide which phase to run and for how many seconds.
    """

    def __init__(self, model_name: str = "tiiuae/falcon-rw-1b", device: str = None):
        # Initialize the LocalLLM (Falcon-RW-1B)
        self.llm = LocalLLM(model_name=model_name, device=device)

        # System prompt template: instructs the model to output exactly "<PHASE> <DURATION>"
        self.system_template = (
            "You are an expert traffic engineer. As vehicles queue at each intersection approach, "
            "you must decide which signal phase to run. Valid phases:\n"
            "    GREEN_NORTH_SOUTH\n"
            "    GREEN_EAST_WEST\n"
            "Output must follow this exact format:\n"
            "    <PHASE> <DURATION>\n"
            "where <PHASE> is one of the two strings above, and <DURATION> is an integer (seconds)."
        )

    def decide_phase(self, state: dict) -> tuple[str, int]:
        """
        Given a state dict like {"N": int, "E": int, "S": int, "W": int},
        build a user prompt, query Falcon, and parse "<PHASE> <DURATION>".
        """
        # Build the user prompt from the state
        user_prompt = (
            f"Queue lengths → North: {state['N']}, East: {state['E']}, "
            f"South: {state['S']}, West: {state['W']}. Recommend a phase."
        )

        # Query the LLM
        raw_reply = self.llm.query(self.system_template, user_prompt)

        # Parse expecting "GREEN_NORTH_SOUTH 15" or "GREEN_EAST_WEST 10"
        pattern = r"^(GREEN_NORTH_SOUTH|GREEN_EAST_WEST)\s+(\d+)"
        match = re.search(pattern, raw_reply.strip())
        if match:
            phase = match.group(1)
            duration = int(match.group(2))
        else:
            # Fallback: if parsing fails, default to north-south for 10 seconds
            phase = "GREEN_NORTH_SOUTH"
            duration = 10

        return phase, duration

