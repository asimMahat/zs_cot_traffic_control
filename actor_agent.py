# actor_agent.py

import re
from local_llm import LocalLLM

class ActorAgent:
    """
    Zero‐Shot Chain‐of‐Thought “actor” agent using Falcon-RW-1B (or another LLM).
    The agent decides between two phases: GREEN_NORTH_SOUTH or GREEN_EAST_WEST,
    based on current queue lengths and a starvation‐avoidance rule.
    """

    def __init__(
        self,
        model_name: str = "tiiuae/falcon-rw-1b",
        device: str = None,
        starvation_threshold: int = 20,
    ):
        # Initialize the LocalLLM (Falcon-RW-1B or similar)
        self.llm = LocalLLM(model_name=model_name, device=device)

        # Few‐shot system prompt with placeholders for {N}, {E}, {S}, {W}, {EW_waited}
        self.system_template = (
            "You are an expert traffic engineer. Always output exactly:\n"
            "    <PHASE> <DURATION>\n"
            "Valid phases: GREEN_NORTH_SOUTH or GREEN_EAST_WEST.\n\n"
            "Examples:\n"
            "  State: N=4, E=4, S=4, W=4 → GREEN_NORTH_SOUTH 10  (tie broken to N‐S)\n"
            "  State: N=5, E=6, S=5, W=6 → GREEN_EAST_WEST 15  (EW > NS)\n"
            "  State: N=2, E=10, S=2, W=1 → GREEN_EAST_WEST 20  (EW >> NS)\n"
            "  State: N=8, E=7, S=8, W=7 → GREEN_NORTH_SOUTH 12  (NS > EW)\n"
            "  State: N=5, E=5, S=5, W=5, EW_waited=20 → GREEN_EAST_WEST 10  (forced by starvation)\n"
            "\n"
            "Now given the current state, choose phase.\n"
            "State: N={N}, E={E}, S={S}, W={W}, EW_waited={EW_waited} →"
        )

        # Maximum seconds E–W may be held red before we force it green
        self.starvation_threshold = starvation_threshold
        self.ew_starvation_timer = 0  # Accumulates N–S durations when E–W is red

    def decide_phase(self, state: dict) -> tuple[str, int]:
        """
        Given a state dict like {"N": int, "E": int, "S": int, "W": int},
        build a few‐shot prompt, query the LLM, then possibly override if
        E–W has been starved too long. Returns (phase, duration).
        """
        N = state.get("N", 0)
        E = state.get("E", 0)
        S = state.get("S", 0)
        W = state.get("W", 0)
        EW_waited = self.ew_starvation_timer

        # 1) Starvation override: if E–W has waited ≥ threshold, force it now
        if EW_waited >= self.starvation_threshold:
            self.ew_starvation_timer = 0
            forced_duration = 10
            print(f">>> Starvation‐break: forcing GREEN_EAST_WEST {forced_duration}s")
            return "GREEN_EAST_WEST", forced_duration

        # 2) Otherwise, format the few‐shot prompt with current values
        prompt = self.system_template.format(
            N=N, E=E, S=S, W=W, EW_waited=EW_waited
        )
        print(f">>> Full prompt sent to LLM:\n{prompt}\n")

        # Query the LLM; second argument unused, all instructions are in prompt
        raw_reply = self.llm.query(prompt, "")
        print(f">>> LLM raw reply: '{raw_reply}'")

        # 3) Parse the LLM’s response as "<PHASE> <DURATION>"
        pattern = r"^(GREEN_NORTH_SOUTH|GREEN_EAST_WEST)\s+(\d+)"
        match = re.search(pattern, raw_reply.strip())
        if match:
            phase = match.group(1)
            duration = int(match.group(2))
        else:
            # Fallback if parsing fails: default to N–S for 10s
            phase = "GREEN_NORTH_SOUTH"
            duration = 10
            print(f">>> Failed to parse LLM reply, defaulting to {phase} {duration}s")

        # 4) Update starvation timer: add duration if N–S chosen, reset if E–W chosen
        if phase == "GREEN_NORTH_SOUTH":
            self.ew_starvation_timer += duration
        else:  # GREEN_EAST_WEST
            self.ew_starvation_timer = 0

        return phase, duration
