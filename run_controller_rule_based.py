import time
import sys
import os

# Ensure SUMO is properly configured
if 'SUMO_HOME' not in os.environ:
    print("Warning: SUMO_HOME environment variable not set")

# Import traci with error handling
try:
    import traci
    print("TraCI imported successfully")
except ImportError as e:
    print(f"Error importing TraCI: {e}")
    print("Please ensure SUMO is properly installed and SUMO_HOME is set")
    sys.exit(1)

class FastRuleAgent:
    def decide_phase(self, state):
        ns = state["N"] + state["S"]
        ew = state["E"] + state["W"]
        if ns >= ew:
            return "GREEN_NORTH_SOUTH", 20
        else:
            return "GREEN_EAST_WEST", 20

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
        time.sleep(0.3)

def run():
    agent = FastRuleAgent()

    # Check if SUMO is in PATH, otherwise try common installation paths
    sumo_binary = "sumo"
    
    # Common SUMO installation paths
    possible_paths = [
        "sumo",  # If in PATH
        "/usr/bin/sumo",  # Linux
        "/usr/local/bin/sumo",  # Linux/Mac
        "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\sumo.exe",  # Windows
        "C:\\sumo\\bin\\sumo.exe",  # Windows alternative
    ]
    
    sumo_found = False
    for path in possible_paths:
        try:
            # Test if the binary exists and is executable
            if os.path.isfile(path) or path == "sumo":
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