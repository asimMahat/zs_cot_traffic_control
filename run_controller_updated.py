# run_controller.py

import traci
from actor_agent import ActorAgent

def get_current_state() -> dict:
    """
    Query SUMO/TraCI for the number of vehicles currently queued on each incoming edge.
    Returns a dict: {"N": int, "E": int, "S": int, "W": int}
    """
    # These edge IDs must match what you defined in edges.edg.xml and intersection.net.xml
    N_queue = traci.edge.getLastStepVehicleNumber("N2C")
    E_queue = traci.edge.getLastStepVehicleNumber("E2C")
    S_queue = traci.edge.getLastStepVehicleNumber("S2C")
    W_queue = traci.edge.getLastStepVehicleNumber("W2C")
    return {"N": N_queue, "E": E_queue, "S": S_queue, "W": W_queue}

def apply_phase(phase: str, duration: int):
    """
    Apply a traffic light phase in SUMO for `duration` seconds.
    Assumes a single traffic light with ID "TL" and two phases:
      0 = green N-S, red E-W
      1 = green E-W, red N-S
    Adjust the TL ID and phase indices if yours are different.
    """
    tl_id = "TL"  # Change this to your actual traffic light ID in the .add.xml or .net.xml
    if phase == "GREEN_NORTH_SOUTH":
        traci.trafficlight.setPhase(tl_id, 0)
    else:  # "GREEN_EAST_WEST"
        traci.trafficlight.setPhase(tl_id, 1)

    # Advance the simulation by 'duration' seconds
    for _ in range(duration):
        traci.simulationStep()

def run():
    """
    Launch SUMO/TraCI and run the ZS-CoT controller loop using Falcon-RW-1B.
    Each simulation cycle:
      1. Read queue lengths from the four incoming edges.
      2. Use ActorAgent to choose phase + duration.
      3. Apply that phase for the requested duration.
      4. Repeat until no vehicles remain.
    """
    # Initialize the ActorAgent with Falcon-RW-1B on CPU
    agent = ActorAgent(model_name="tiiuae/falcon-rw-1b", device="cpu")

    # Launch SUMO via TraCI (use "sumo-gui" instead of "sumo" if you want the GUI window)
    sumo_binary = "sumo"
    sumo_cmd = [sumo_binary, "-c", "intersection.sumocfg"]
    traci.start(sumo_cmd)

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            state = get_current_state()
            phase, duration = agent.decide_phase(state)
            apply_phase(phase, duration)

        traci.close()
    except Exception as e:
        print("Error during SUMO/TraCI loop:", e)
        traci.close()

if __name__ == "__main__":
    run()
