import re
from local_llm import LocalLLM
from model_manager import ModelType

class FastRuleAgent:
    """
    Simple rule-based agent that serves as a fallback when LLM fails.
    Uses basic queue length comparison and starvation prevention.
    """
    def __init__(self, fixed_duration: int = 20):
        self.fixed_duration = fixed_duration
        self.last_phase = None
        self.ew_wait_time = 0
        self.ns_wait_time = 0
        self.max_wait_time = 60  # Maximum wait time in seconds before forcing a phase change

    def decide_phase(self, state: dict) -> tuple[str, int]:
        """
        Decision making with starvation prevention:
        1. Check if any direction has waited too long
        2. If one direction has significantly more vehicles, choose that direction
        3. If queues are similar, alternate between phases
        """
        N = state.get("N", 0)
        E = state.get("E", 0)
        S = state.get("S", 0)
        W = state.get("W", 0)
        
        ns_total = N + S
        ew_total = E + W
        
        # Update wait times
        if self.last_phase == "GREEN_NORTH_SOUTH":
            self.ew_wait_time += self.fixed_duration
            self.ns_wait_time = 0
        elif self.last_phase == "GREEN_EAST_WEST":
            self.ns_wait_time += self.fixed_duration
            self.ew_wait_time = 0
        
        # Starvation prevention - force phase change if waited too long
        if self.ew_wait_time >= self.max_wait_time:
            self.last_phase = "GREEN_EAST_WEST"
            self.ew_wait_time = 0
            return "GREEN_EAST_WEST", self.fixed_duration
        elif self.ns_wait_time >= self.max_wait_time:
            self.last_phase = "GREEN_NORTH_SOUTH"
            self.ns_wait_time = 0
            return "GREEN_NORTH_SOUTH", self.fixed_duration
        
        # If one direction has significantly more vehicles (difference > 2)
        if abs(ns_total - ew_total) > 2:
            if ns_total > ew_total:
                self.last_phase = "GREEN_NORTH_SOUTH"
                return "GREEN_NORTH_SOUTH", self.fixed_duration
            else:
                self.last_phase = "GREEN_EAST_WEST"
                return "GREEN_EAST_WEST", self.fixed_duration
        
        # If queues are similar, alternate between phases
        if self.last_phase == "GREEN_NORTH_SOUTH":
            self.last_phase = "GREEN_EAST_WEST"
            return "GREEN_EAST_WEST", self.fixed_duration
        else:
            self.last_phase = "GREEN_NORTH_SOUTH"
            return "GREEN_NORTH_SOUTH", self.fixed_duration

class ActorAgent:
    """
    Zero‐Shot Chain‐of‐Thought "actor" agent using various LLM models.
    The agent decides between two phases: GREEN_NORTH_SOUTH or GREEN_EAST_WEST.
    Includes fallback to rule-based agent when LLM fails and starvation prevention.
    """

    def __init__(
        self,
        model_type: ModelType,
        device: str = None,
        fixed_duration: int = 20,       # Fixed duration for each phase
        max_llm_failures: int = 3,      # Maximum consecutive LLM failures before switching to fallback
        max_wait_time: int = 60         # Maximum wait time in seconds before forcing a phase change
    ):
        # Initialize the LocalLLM with the specified model type using singleton pattern
        self.llm = LocalLLM.get_instance(model_type=model_type, device=device)
        self.model_type = model_type
        self.fixed_duration = fixed_duration
        self.max_llm_failures = max_llm_failures
        self.consecutive_failures = 0
        self.using_fallback = False
        self.fallback_agent = FastRuleAgent(fixed_duration=fixed_duration)
        
        # Starvation prevention tracking
        self.last_phase = None
        self.ew_wait_time = 0
        self.ns_wait_time = 0
        self.max_wait_time = max_wait_time

        # Few‐shot system prompt with placeholders for {N}, {E}, {S}, {W}, {EW_waited}
        self.system_template = (
                "You are an expert traffic engineer. Output ONLY:\n"
                "    <PHASE> <DURATION>\n"
                "Valid phases: GREEN_NORTH_SOUTH or GREEN_EAST_WEST.\n\n"
                "IMPORTANT: Output ONLY the phase and duration, e.g. GREEN_NORTH_SOUTH 20\n"
                "Do NOT explain. Do NOT add any extra text.\n\n"
                "Both GREEN_NORTH_SOUTH and GREEN_EAST_WEST are equally important. "
                "To ensure fairness and smooth traffic flow, you must alternate between them over time, "
                "even if one direction sometimes has fewer vehicles. "
                "Do not let any direction wait too long for a green light.\n\n"
                "Examples:\n"
                "  State: N=4, E=4, S=4, W=4 → GREEN_NORTH_SOUTH 20  (tie broken to N‐S)\n"
                "  State: N=5, E=6, S=5, W=6 → GREEN_EAST_WEST 20  (EW > NS)\n"
                "  State: N=2, E=10, S=2, W=1 → GREEN_EAST_WEST 20  (EW >> NS)\n"
                "  State: N=8, E=7, S=8, W=7 → GREEN_NORTH_SOUTH 20  (NS > EW)\n"
                "  State: N=5, E=5, S=5, W=5 → GREEN_EAST_WEST 20  (alternate for fairness)\n"
                "  State: N=3, E=3, S=3, W=3 → GREEN_NORTH_SOUTH 20  (alternate for fairness)\n"
                "\n"
                "Now given the current state, choose phase.\n"
                "State: N={N}, E={E}, S={S}, W={W}, EW_waited={EW_waited} →")

    def check_starvation(self, proposed_phase: str) -> str:
        """
        Check if any direction has waited too long and force a phase change if needed.
        """
        # Update wait times
        if self.last_phase == "GREEN_NORTH_SOUTH":
            self.ew_wait_time += self.fixed_duration
            self.ns_wait_time = 0
        elif self.last_phase == "GREEN_EAST_WEST":
            self.ns_wait_time += self.fixed_duration
            self.ew_wait_time = 0
        
        # Force phase change if waited too long
        if self.ew_wait_time >= self.max_wait_time:
            print(f">>> Forcing GREEN_EAST_WEST due to starvation (waited {self.ew_wait_time}s)")
            self.ew_wait_time = 0
            return "GREEN_EAST_WEST"
        elif self.ns_wait_time >= self.max_wait_time:
            print(f">>> Forcing GREEN_NORTH_SOUTH due to starvation (waited {self.ns_wait_time}s)")
            self.ns_wait_time = 0
            return "GREEN_NORTH_SOUTH"
        
        return proposed_phase

    def decide_phase(self, state: dict) -> tuple[str, int]:
        """
        Given a state dict, use LLM to decide the next phase.
        Falls back to rule-based agent if LLM fails repeatedly.
        After one fallback step, LLM is tried again.
        Returns (phase, duration).
        """
        # If we're using fallback, use it for this step, then reset to try LLM again next time
        if self.using_fallback:
            phase, duration = self.fallback_agent.decide_phase(state)
            self.using_fallback = False  # Reset fallback so LLM is tried next time
            self.consecutive_failures = 0  # Optionally reset failure counter
            return phase, duration

        N = state.get("N", 0)
        E = state.get("E", 0)
        S = state.get("S", 0)
        W = state.get("W", 0)
        EW_waited = self.ew_wait_time  # Pass actual wait time to prompt

        prompt = self.system_template.format(N=N, E=E, S=S, W=W, EW_waited=EW_waited)
        print(f">>> Full prompt sent to LLM:\n{prompt}\n")

        raw_reply = self.llm.query(prompt, "")
        print(f">>> LLM raw reply: '{raw_reply}'")

        pattern = r"(GREEN_NORTH_SOUTH|GREEN_EAST_WEST)\s+(\d+)"
        match = re.search(pattern, raw_reply)
        
        if match:
            phase = match.group(1)
            self.consecutive_failures = 0  # Reset failure counter on success
            # Check for starvation before returning the phase
            phase = self.check_starvation(phase)
            self.last_phase = phase
            return phase, self.fixed_duration
        else:
            print(f">>> Failed to parse LLM reply, got: '{raw_reply}'")
            self.consecutive_failures += 1
            # Check if we should switch to fallback
            if self.consecutive_failures >= self.max_llm_failures:
                print(">>> Switching to fallback rule-based agent due to repeated LLM failures")
                self.using_fallback = True
                return self.fallback_agent.decide_phase(state)
            # If not switching to fallback yet, use rule-based agent for this step
            return self.fallback_agent.decide_phase(state)
