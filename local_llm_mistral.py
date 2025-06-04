import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    GenerationConfig,
)

class LocalLLM:
    """
    A simple "chat" wrapper around a local HF model, optimized for Mistral.
    Usage:
        llm = LocalLLM(model_name="mistralai/Mistral-7B-Instruct-v0.1")
        reply = llm.query(system_msg, user_msg)
    """

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.1",
        device: str = None,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
    ):
        """
        model_name: HF identifier or local path
        device: "cpu", "cuda", or let accelerate pick automatically
        """
        self.model_name = model_name
        
        # Decide device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Loading model: {model_name}")
        print(f"Using device: {self.device}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        
        # Handle pad token
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

        print("Model loaded successfully!")

    def _build_prompt(self, system_msg: str, user_msg: str) -> str:
        """
        Build prompt using Mistral's instruction format.
        Mistral format: <s>[INST] {system_msg}\n\n{user_msg} [/INST]
        """
        return f"<s>[INST] {system_msg.strip()}\n\n{user_msg.strip()} [/INST]"

    def query(self, system_msg: str, user_msg: str) -> str:
        """
        Query the model with system and user messages.
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
        
        # Extract only the response part (after [/INST])
        if "[/INST]" in full_output:
            response = full_output.split("[/INST]", 1)[-1].strip()
        else:
            # Fallback if format is unexpected
            response = full_output[len(prompt):].strip()
            
        return response