import os
from sumolib import checkBinary
import traci
from actor_agent import ActorAgent

# simulation settings
DECISION_INTERVAL = 5  # seconds between decisions
MAX_STEPS = 3600       # total simulation steps


def get_current_state():
    # extract queue lengths, waiting times per lane
    state = {}
    # ... implement using traci.lane.getLastStepHaltingNumber etc.
    return state


def apply_phase(phase: int, duration: float):
    # convert phase index to sumo TLS logic
    # e.g., traci.trafficlights.setPhase('TL', phase)
    pass


def run():
    sumo_binary = checkBinary('sumo')
    traci.start([sumo_binary, "-c", "intersection.sumocfg"])
    agent = ActorAgent()
    step = 0
    while step < MAX_STEPS:
        if step % DECISION_INTERVAL == 0:
            state = get_current_state()
            phase, duration = agent.decide_phase(state)
            apply_phase(phase, duration)
        traci.simulationStep()
        step += 1
    traci.close()


if __name__ == '__main__':
    run()
