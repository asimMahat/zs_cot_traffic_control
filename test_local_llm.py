# test_local_llm.py

import torch
from local_llm import LocalLLM

def main():
    # Initialize the LLM. Pass device="cuda" if you have a suitable GPU.
    llm = LocalLLM(
        model_name="tiiuae/falcon-rw-1b",
        device="cpu",            # or "cuda"
        max_new_tokens=64,
        temperature=0.0          # deterministic output
    )

    # Example system prompt describing the ZS-CoT task
    system_msg = (
        "You are an expert traffic engineer. Given an intersection state, "
        "you must output exactly one of:\n"
        "    GREEN_NORTH_SOUTH\n"
        "    GREEN_EAST_WEST\n"
        "followed by a space and an integer duration in seconds."
    )

    # Example user prompt describing queue lengths
    user_msg = (
        "Current queue lengths: North=5, East=0, South=4, West=1. Recommend a phase."
    )

    # Query the local LLM
    reply = llm.query(system_msg, user_msg)

    print("=== Model Reply ===")
    print(reply)

if __name__ == "__main__":
    main()
