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
    cerebras_api_key: Optional[str] = None
    
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
        "cerebras_api_key": "",
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
            "together_api_key", "openrouter_api_key", "g4f_api_key", "cerebras_api_key",
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
        get_llm_manager().refresh()
        
        return {"message": "Configurações atualizadas com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def get_settings():
    return load_settings()

@router.post("/test-api-key")
async def test_api_key(request: Dict[str, Any]):
    """Testa se uma chave de API é válida para o provedor especificado"""
    provider_name = request.get("provider")
    api_key = request.get("api_key")
    model_name = request.get("model_name")
    
    if not provider_name or not api_key:
        raise HTTPException(status_code=400, detail="Provedor e Chave de API são obrigatórios")
    
    try:
        from ...core.llm_providers import LLMProviderFactory, ProviderType
        from ...core.shared_config import config_manager
        
        # Converte string para ProviderType
        try:
            p_type = ProviderType(provider_name.lower())
        except ValueError:
            return {"status": "error", "message": f"Provedor não suportado: {provider_name}"}
            
        # Busca URL base padrão para o provedor se necessário
        # Temporariamente usamos o config_manager para pegar as URLs mapeadas
        s = config_manager.settings
        # Backup do provider original para não afetar o sistema global
        original_provider = s.llm_provider
        s.llm_provider = provider_name
        api_cfg = config_manager.get_api_config()
        s.llm_provider = original_provider # Restaura
        
        # Cria provedor temporário
        provider = LLMProviderFactory.create_provider(
            provider_type=p_type,
            api_key=api_key,
            model_name=model_name or api_cfg.model_name,
            base_url=api_cfg.base_url
        )
        
        is_valid = provider.test_connection()
        if is_valid:
            return {"status": "success", "message": "Chave de API válida! Conexão estabelecida."}
        else:
            return {"status": "error", "message": "Falha na conexão. Verifique a chave e tente novamente."}
            
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"status": "error", "message": f"Erro ao testar API: {str(e)}"}
@router.get("/available-models")
async def get_available_models():
    """Retorna todos os modelos disponíveis por provedor"""
    try:
        from ...core.llm_providers import LLMProviderFactory
        all_models = LLMProviderFactory.get_all_available_models()
        
        # Converte para formato serializável (Enum para string)
        result = {}
        for provider_type, models in all_models.items():
            result[provider_type.value] = [
                {
                    "name": m.name,
                    "display_name": m.display_name,
                    "max_tokens": m.max_tokens,
                    "description": m.description,
                    "is_free": m.is_free
                } for m in models
            ]
        return result
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current-provider")
async def get_current_provider():
    """Retorna informações sobre o provedor configurado no momento"""
    try:
        from ...core.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()
        
        if not llm_manager.provider:
            return {"available": False, "message": "Nenhum provedor configurado"}
            
        settings = load_settings()
        return {
            "available": True,
            "provider_type": settings.get("llm_provider"),
            "display_name": settings.get("llm_provider", "").upper(),
            "model": settings.get("model_name"),
            "config": {
                "chunk_size": settings.get("chunk_size"),
                "min_score": settings.get("min_score_threshold")
            }
        }
    except Exception as e:
        return {"available": False, "error": str(e)}
