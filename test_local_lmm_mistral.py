# test_local_llm.py

from local_llm import LocalLLM
import torch

def test_model(model_name, description):
    """Test a specific model"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Model: {model_name}")
    print('='*60)
    
    try:
        llm = LocalLLM(
            model_name=model_name,
            device="cuda" if torch.cuda.is_available() else "cpu",
            max_new_tokens=100,
            temperature=0.1,  # Low temperature for more focused responses
        )

        system_msg = """You are an expert traffic engineer. Given an intersection state, you must recommend either GREEN_NORTH_SOUTH or GREEN_EAST_WEST with a duration in seconds. Be concise and clear."""

        user_msg = "Current queue lengths: North=5, East=0, South=4, West=1. Recommend a phase."

        print(f"\nSystem: {system_msg}")
        print(f"User: {user_msg}")
        print(f"\nResponse:")
        
        reply = llm.query(system_msg, user_msg)
        print(reply)
        
        return True
        
    except Exception as e:
        print(f"Error with {model_name}: {str(e)}")
        return False

def main():
    print("Testing unrestricted models for traffic control...")
    
    # List of models to try (in order of preference)
    models_to_test = [
        ("microsoft/DialoGPT-medium", "Microsoft DialoGPT (conversational, ~300MB)"),
        ("gpt2", "GPT-2 (classic, ~500MB)"),
        ("gpt2-medium", "GPT-2 Medium (larger, ~1.5GB)"),
        ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", "TinyLlama Chat (small but capable, ~2GB)"),
        ("microsoft/phi-1_5", "Microsoft Phi-1.5 (good reasoning, ~3GB)"),
    ]
    
    successful_model = None
    
    for model_name, description in models_to_test:
        success = test_model(model_name, description)
        if success:
            successful_model = model_name
            break
        print(f"Failed to load {model_name}, trying next...")
    
    if successful_model:
        print(f"\n🎉 SUCCESS! Working model: {successful_model}")
        print("You can now use this model in your traffic control system.")
    else:
        print("\n❌ All models failed. Check your internet connection or try:")
        print("pip install --upgrade transformers torch")

if __name__ == "__main__":
    main()