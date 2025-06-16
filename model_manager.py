# model_manager.py

from enum import Enum
from typing import Dict, Any

class ModelType(Enum):
    LIGHTGPT = "lightgpt"

class ModelConfig:
    def __init__(self, name: str, model_id: str, prompt_format: str):
        self.name = name
        self.model_id = model_id
        self.prompt_format = prompt_format

# Model configurations
MODEL_CONFIGS: Dict[ModelType, ModelConfig] = {
    ModelType.LIGHTGPT: ModelConfig(
        name="LightGPT 0.5B",
        model_id="lightgpt/LightGPT-0.5B-Qwen2",
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