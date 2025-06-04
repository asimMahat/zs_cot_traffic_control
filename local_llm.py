# local_llm.py

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

class LocalLLM:
    """
    A simple wrapper around 'tiiuae/falcon-rw-1b' that loads the entire model
    into CPU (or GPU) memory without offloading to disk, and chooses sampling vs.
    greedy decoding based on temperature.
    Usage:
        llm = LocalLLM(
            model_name="tiiuae/falcon-rw-1b",
            device="cpu",              # or "cuda" if you have a GPU
            max_new_tokens=128,
            temperature=0.0            # deterministic, greedy decoding
        )
        reply = llm.query(system_msg, user_msg)
    """

    def __init__(
        self,
        model_name: str = "tiiuae/falcon-rw-1b",
        device: str = None,
        max_new_tokens: int = 128,
        temperature: float = 0.7,
    ):
        # Choose device: if user did not pass one, default to GPU if available, else CPU
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        # Load model fully into memory (no offloading). We use float16 on GPU, float32 on CPU.
        dtype = torch.float16 if (self.device.startswith("cuda")) else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            low_cpu_mem_usage=False,
        )
        if self.device.startswith("cuda"):
            self.model = self.model.to(self.device)

        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        # If temperature == 0.0, use greedy (do_sample=False). Otherwise, sample.
        do_sample_flag = False if (self.temperature == 0.0) else True
        self.gen_config = GenerationConfig(
            temperature=self.temperature if (self.temperature > 0.0) else 1.0,
            top_p=0.95,
            do_sample=do_sample_flag,
        )

    def _build_prompt(self, system_msg: str, user_msg: str) -> str:
        """
        Construct a simple prompt for Falcon RW:
        [SYSTEM]: <system_msg>
        [USER]: <user_msg>
        [ASSISTANT]:
        """
        system_msg = system_msg.strip()
        user_msg = user_msg.strip()
        prompt = (
            f"[SYSTEM]: {system_msg}\n"
            f"[USER]: {user_msg}\n"
            f"[ASSISTANT]:"
        )
        return prompt

    def query(self, system_msg: str, user_msg: str) -> str:
        """
        Send (system_msg + user_msg) as a prompt to Falcon RW and
        return everything it generates after “[ASSISTANT]:”.
        """
        prompt = self._build_prompt(system_msg, user_msg)

        # Tokenize the prompt
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = inputs.to(self.model.device)

        # Generate continuation
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                generation_config=self.gen_config,
                max_new_tokens=self.max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode the entire sequence: prompt + generated tokens (including “[ASSISTANT]:”)
        decoded = self.tokenizer.decode(output_ids[0], skip_special_tokens=False)

        # Split on “[ASSISTANT]:” and take everything after it as the model’s reply
        split_token = "[ASSISTANT]:"
        if split_token in decoded:
            parts = decoded.rsplit(split_token, 1)
            return parts[-1].strip()
        else:
            # If somehow “[ASSISTANT]:” is missing, return the raw decoded text
            return decoded.strip()
