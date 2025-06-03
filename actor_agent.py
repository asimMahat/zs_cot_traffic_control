import json
from llm_interface import LLMInterface
class ActorAgent:
    def __init__(self, model: str = 'gpt-4'):
        self.llm = LLMInterface(model)
        # define your static system prompt template here
        self.system_template = (
            "You are a traffic signal controller. Given the intersection state, output a JSON "
            "object with 'phase' and 'duration' in seconds. Phases: [0,1,2,3]."
        )

    def decide_phase(self, state: dict) -> tuple[int, float]:
        # state: e.g., {'lane_queues': {...}, 'waiting_times': {...}}
        user_prompt = json.dumps(state)
        raw = self.llm.query(self.system_template, user_prompt)
        # expect JSON: {"phase": 1, "duration": 15.0}
        out = json.loads(raw)
        return out['phase'], out['duration']