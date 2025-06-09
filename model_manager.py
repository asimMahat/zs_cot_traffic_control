# model_manager.py

from enum import Enum
from typing import Dict, Any

class ModelType(Enum):
    FALCON = "falcon"
    MISTRAL = "mistral"
    LLAMA = "llama"
    PHI = "phi"
    TINYLLAMA = "tinyllama"

class ModelConfig:
    def __init__(self, name: str, model_id: str, prompt_format: str):
        self.name = name
        self.model_id = model_id
        self.prompt_format = prompt_format

# Model configurations
MODEL_CONFIGS: Dict[ModelType, ModelConfig] = {
    ModelType.FALCON: ModelConfig(
        name="Falcon RW 1B",
        model_id="tiiuae/falcon-rw-1b",
        prompt_format="[SYSTEM]: {system_msg}\n[USER]: {user_msg}\n[ASSISTANT]:"
    ),
    ModelType.MISTRAL: ModelConfig(
        name="Mistral 7B",
        model_id="mistralai/Mistral-7B-Instruct-v0.1",
        prompt_format="<s>[INST] {system_msg}\n\n{user_msg} [/INST]"
    ),
    ModelType.LLAMA: ModelConfig(
        name="Llama 2 7B",
        model_id="meta-llama/Llama-2-7b-chat-hf",
        prompt_format="<s>[INST] <<SYS>>\n{system_msg}\n<</SYS>>\n\n{user_msg} [/INST]"
    ),
    ModelType.PHI: ModelConfig(
        name="Microsoft Phi 1.5",
        model_id="microsoft/phi-1_5",
        prompt_format="<s>[INST] {system_msg}\n\n{user_msg} [/INST]"
    ),
    ModelType.TINYLLAMA: ModelConfig(
        name="TinyLlama 1.1B",
        model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        prompt_format="<s>[INST] {system_msg}\n\n{user_msg} [/INST]"
    )
}

def get_available_models() -> Dict[str, ModelType]:
    """Returns a dictionary of available models for selection."""
    return {config.name: model_type for model_type, config in MODEL_CONFIGS.items()}

def get_model_config(model_type: ModelType) -> ModelConfig:
    """Returns the configuration for a specific model type."""
    return MODEL_CONFIGS[model_type]

def format_prompt(model_type: ModelType, system_msg: str, user_msg: str) -> str:
    """Formats the prompt according to the model's requirements."""
    config = get_model_config(model_type)
    return config.prompt_format.format(system_msg=system_msg, user_msg=user_msg) 