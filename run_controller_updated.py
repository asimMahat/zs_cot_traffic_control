import time
import sys
import os
import traci
from model_manager import ModelType
from actor_agent import ActorAgent


def get_current_state():
    N_queue = traci.edge.getLastStepVehicleNumber("N2C")
    E_queue = traci.edge.getLastStepVehicleNumber("E2C")
    S_queue = traci.edge.getLastStepVehicleNumber("S2C")
    W_queue = traci.edge.getLastStepVehicleNumber("W2C")
    return {"N": N_queue, "E": E_queue, "S": S_queue, "W": W_queue}

def apply_phase(phase: str, duration: int):
    """Apply the given phase for the specified duration."""
    tls_id = "C"
    if phase == "GREEN_NORTH_SOUTH":
        traci.trafficlight.setPhase(tls_id, 0)
    else:
        traci.trafficlight.setPhase(tls_id, 1)
    for _ in range(duration):
        traci.simulationStep()
        time.sleep(0.3)  # Add delay for smoother visualization

def run():
    # Initialize the agent with LightGPT model
    agent = ActorAgent(
        model_type=ModelType.LIGHTGPT,
        device="cpu",
        fixed_duration=20
    )

    # Check if SUMO is in PATH, otherwise try common installation paths
    sumo_binary = "sumo-gui"
    
    # Common SUMO installation paths
    possible_paths = [
        "sumo-gui",  # If in PATH
        "/usr/bin/sumo-gui",  # Linux
        "/usr/local/bin/sumo-gui",  # Linux/Mac
        "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\sumo-gui.exe",  # Windows
        "C:\\sumo\\bin\\sumo-gui.exe",  # Windows alternative
    ]
    
    sumo_found = False
    for path in possible_paths:
        try:
            # Test if the binary exists and is executable
            if os.path.isfile(path) or path == "sumo-gui":
                sumo_binary = path
                sumo_found = True
                break
        except:
            continue
    
    if not sumo_found:
        print("Error: SUMO not found. Please install SUMO or add it to your PATH.")
        return
    
    # Check if config file exists
    config_file = "intersection.sumocfg"
    if not os.path.isfile(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        print("Please ensure the SUMO configuration file is in the current directory.")
        return
    
    sumo_cmd = [sumo_binary, "-c", config_file]
    
    try:
        print(f"Starting SUMO with command: {' '.join(sumo_cmd)}")
        traci.start(sumo_cmd)
        
        while traci.simulation.getMinExpectedNumber() > 0:
            state = get_current_state()
            phase, duration = agent.decide_phase(state)
            apply_phase(phase, duration)
            
        print("Simulation completed successfully.")
        
    except traci.exceptions.FatalTraCIError as e:
        print(f"TraCI Fatal Error: {e}")
        print("This usually means SUMO couldn't start or the configuration is invalid.")
    except Exception as e:
        print("Error during SUMO/TraCI loop:", e)
    finally:
        try:
            traci.close()
        except:
            pass

if __name__ == "__main__":
    run()