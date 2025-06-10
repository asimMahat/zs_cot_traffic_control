import time
import sys
import os
import traci
from model_manager import ModelType, get_available_models
from actor_agent import ActorAgent

class FastRuleAgent:
    def decide_phase(self, state):
        ns = state["N"] + state["S"]
        ew = state["E"] + state["W"]
        if ns >= ew:
            return "GREEN_NORTH_SOUTH", 10
        else:
            return "GREEN_EAST_WEST", 10

def get_current_state():
    N_queue = traci.edge.getLastStepVehicleNumber("N2C")
    E_queue = traci.edge.getLastStepVehicleNumber("E2C")
    S_queue = traci.edge.getLastStepVehicleNumber("S2C")
    W_queue = traci.edge.getLastStepVehicleNumber("W2C")
    return {"N": N_queue, "E": E_queue, "S": S_queue, "W": W_queue}

def apply_phase(phase: str, duration: int):
    tls_id = "C"
    if phase == "GREEN_NORTH_SOUTH":
        traci.trafficlight.setPhase(tls_id, 0)
    else:
        traci.trafficlight.setPhase(tls_id, 1)
    for _ in range(duration):
        traci.simulationStep()

def select_model() -> ModelType:
    """Allow user to select a model from available options."""
    available_models = get_available_models()
    
    print("\nAvailable Models:")
    for i, (name, _) in enumerate(available_models.items(), 1):
        print(f"{i}. {name}")
    
    while True:
        try:
            choice = int(input("\nSelect a model (enter number): "))
            if 1 <= choice <= len(available_models):
                model_name = list(available_models.keys())[choice - 1]
                return available_models[model_name]
            else:
                print(f"Please enter a number between 1 and {len(available_models)}")
        except ValueError:
            print("Please enter a valid number")

def run():
    # Let user select the model
    model_type = select_model()
    print(f"\nSelected model: {model_type.name}")
    
    # Initialize the agent with the selected model
    agent = ActorAgent(model_type=model_type, device="cpu")

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
        
        step = 0
        phase = "GREEN_NORTH_SOUTH"
        duration = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            if duration == 0:
                state = get_current_state()
                phase, duration = agent.decide_phase(state)
                # Set the phase in SUMO
                if phase == "GREEN_NORTH_SOUTH":
                    traci.trafficlight.setPhase("C", 0)
                else:
                    traci.trafficlight.setPhase("C", 1)
            traci.simulationStep()
            duration -= 1
            step += 1
        traci.close()
        print("Simulation completed successfully.")
        
    except traci.exceptions.FatalTraCIError as e:
        print(f"TraCI Fatal Error: {e}")
        print("This usually means SUMO couldn't start or the configuration is invalid.")
        try:
            traci.close()
        except:
            pass
    except Exception as e:
        print("Error during SUMO/TraCI loop:", e)
        try:
            traci.close()
        except:
            pass

if __name__ == "__main__":
    run()