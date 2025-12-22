from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
import json
from pathlib import Path

router = APIRouter()

class SettingsRequest(BaseModel):
    """Modelo de requisição de configurações atualizado"""
    llm_provider: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    siliconflow_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    g4f_api_key: Optional[str] = None
    
    model_name: Optional[str] = None
    chunk_size: Optional[int] = None
    min_score_threshold: Optional[float] = None
    max_clips_per_collection: Optional[int] = None

def get_settings_file_path() -> Path:
    from ...core.path_utils import get_settings_file_path as get_settings_path
    return get_settings_path()

def load_settings() -> Dict[str, Any]:
    settings_file = get_settings_file_path()
    default_settings = {
        "llm_provider": "dashscope",
        "dashscope_api_key": "",
        "openai_api_key": "",
        "gemini_api_key": "",
        "siliconflow_api_key": "",
        "groq_api_key": "",
        "together_api_key": "",
        "openrouter_api_key": "",
        "g4f_api_key": "",
        "model_name": "qwen-plus",
        "chunk_size": 1500,
        "min_score_threshold": 0.3,
        "max_clips_per_collection": 5
    }
    
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                default_settings.update(saved_settings)
        except Exception as e:
            print(f"Erro ao carregar settings: {e}")
    return default_settings

@router.post("")
async def update_settings(request: SettingsRequest):
    try:
        settings = load_settings()
        
        # Mapeamento de campos para atualização dinâmica
        fields = [
            "llm_provider", "dashscope_api_key", "openai_api_key", 
            "gemini_api_key", "siliconflow_api_key", "groq_api_key",
            "together_api_key", "openrouter_api_key", "g4f_api_key",
            "model_name", "chunk_size", "min_score_threshold", "max_clips_per_collection"
        ]
        
        for field in fields:
            val = getattr(request, field)
            if val is not None:
                settings[field] = val
                # Mantém compatibilidade com env vars se necessário
                if "api_key" in field:
                    os.environ[field.upper()] = str(val)

        # Salva no arquivo settings.json
        settings_file = get_settings_file_path()
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        # Notifica o LLM Manager para recarregar as configs
        from ...core.llm_manager import get_llm_manager
        get_llm_manager().update_settings(settings)
        
        return {"message": "Configurações atualizadas com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def get_settings():
    return load_settings()