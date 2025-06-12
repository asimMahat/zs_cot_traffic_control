import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from model_manager import ModelType, get_model_config, format_prompt
import re

class LocalLLM:
    """
    A wrapper around various LLM models that loads the model into CPU (or GPU) memory
    and handles chat formatting for different model types.
    Usage:
        llm = LocalLLM.get_instance(
            model_type=ModelType.LLAMA,  # or any other model type
            device="cpu",              # or "cuda" if you have a GPU
            max_new_tokens=128,
            temperature=0.0            # deterministic, greedy decoding
        )
        reply = llm.query(system_msg, user_msg)
    """
    
    _instance = None
    _initialized = False

    @classmethod
    def get_instance(cls, model_type: ModelType, device: str = None, max_new_tokens: int = 16, temperature: float = 0.0):
        """Get or create the singleton instance of LocalLLM."""
        if cls._instance is None:
            cls._instance = cls(model_type, device, max_new_tokens, temperature)
        return cls._instance

    def __init__(
        self,
        model_type: ModelType,
        device: str = None,
        max_new_tokens: int = 8,
        temperature: float = 0.0,
    ):
        if LocalLLM._initialized:
            return
            
        # Choose device: if user did not pass one, default to GPU if available, else CPU
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self.model_type = model_type
        # Get model configuration
        self.model_config = get_model_config(model_type)
        model_name = self.model_config.model_id

        print(f"Loading model: {self.model_config.name}")
        print(f"Model ID: {model_name}")
        print(f"Using device: {self.device}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with appropriate settings
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.float16 if self.device.startswith("cuda") else torch.float32,
            load_in_8bit=False,  # Set to True if you want quantization and have bitsandbytes
        )

        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        # Build generation config
        self.gen_config = GenerationConfig(
            temperature=self.temperature,
            top_p=0.95,
            do_sample=True if self.temperature > 0 else False,
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        LocalLLM._initialized = True
        print("Model loaded successfully!")

    def _build_prompt(self, system_msg: str, user_msg: str) -> str:
        """
        Build prompt using the model's specific format.
        """
        return format_prompt(self.model_type, system_msg, user_msg)

    def query(self, system_msg: str, user_msg: str) -> str:
        """
        Send (system_msg + user_msg) as a prompt to the model and
        return the generated response.
        """
        prompt = self._build_prompt(system_msg, user_msg)
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = inputs.to(self.model.device)

        # Generate response
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                generation_config=self.gen_config,
                max_new_tokens=self.max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode full output
        full_output = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        # Extract only the response part based on model type
        if self.model_type == ModelType.FALCON:
            if "[ASSISTANT]:" in full_output:
                response = full_output.split("[ASSISTANT]:", 1)[-1].strip()
            else:
                response = full_output[len(prompt):].strip()
        else:  # For Mistral, Llama, Phi, TinyLlama
            if "[/INST]" in full_output:
                response = full_output.split("[/INST]", 1)[-1].strip()
            else:
                response = full_output[len(prompt):].strip()
            
        return response
