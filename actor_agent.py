# actor_agent.py

import re
from local_llm import LocalLLM
from model_manager import ModelType

class ActorAgent:
    """
    Zero‐Shot Chain‐of‐Thought "actor" agent using various LLM models.
    The agent decides between two phases: GREEN_NORTH_SOUTH or GREEN_EAST_WEST,
    based on current queue lengths and a starvation‐avoidance rule.
    """

    def __init__(
        self,
        model_type: ModelType = ModelType.FALCON,
        device: str = None,
        starvation_threshold: int = 20,
        fixed_duration: int = 20,       # Fixed duration for each phase
    ):
        # Initialize the LocalLLM with the specified model type using singleton pattern
        self.llm = LocalLLM.get_instance(model_type=model_type, device=device)
        self.model_type = model_type
        self.fixed_duration = fixed_duration

        # Few‐shot system prompt with placeholders for {N}, {E}, {S}, {W}, {EW_waited}
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
            "  State: N=5, E=5, S=5, W=5, EW_waited=20 → GREEN_EAST_WEST 20  (forced by starvation)\n"
            "\n"
            "Now given the current state, choose phase.\n"
            "State: N={N}, E={E}, S={S}, W={W}, EW_waited={EW_waited} →"
        )

        # Maximum seconds E–W may be held red before we force it green
        self.starvation_threshold = starvation_threshold
        self.ew_starvation_timer = 0  # Accumulates N–S durations when E–W is red

    def decide_phase(self, state: dict) -> tuple[str, int]:
        """
        Given a state dict, use LLM to decide the next phase.
        Returns (phase, duration).
        """
        N = state.get("N", 0)
        E = state.get("E", 0)
        S = state.get("S", 0)
        W = state.get("W", 0)
        EW_waited = self.ew_starvation_timer

        # 1) Starvation override: if E–W has waited ≥ threshold, force it now
        if EW_waited >= self.starvation_threshold:
            self.ew_starvation_timer = 0
            print(f">>> Starvation‐break: forcing GREEN_EAST_WEST {self.fixed_duration}s")
            return "GREEN_EAST_WEST", self.fixed_duration

        # 2) Use LLM for decision
        prompt = self.system_template.format(
            N=N, E=E, S=S, W=W, EW_waited=EW_waited
        )
        print(f">>> Full prompt sent to LLM:\n{prompt}\n")

        raw_reply = self.llm.query(prompt, "")
        print(f">>> LLM raw reply: '{raw_reply}'")

        pattern = r"(GREEN_NORTH_SOUTH|GREEN_EAST_WEST)\s+(\d+)"
        match = re.search(pattern, raw_reply)
        if match:
            phase = match.group(1)
        else:
            phase = "GREEN_NORTH_SOUTH"
            print(f">>> Failed to parse LLM reply, defaulting to {phase}")

        # Update starvation timer
        if phase == "GREEN_NORTH_SOUTH":
            self.ew_starvation_timer += self.fixed_duration
        else:  # GREEN_EAST_WEST
            self.ew_starvation_timer = 0

        return phase, self.fixed_duration
