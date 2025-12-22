"""
Configuration File - Manages API keys, file paths, and other settings.
Supports new configuration management systems and backward compatibility.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseModel, validator
from enum import Enum

# ==========================================
# 1. ENUMERAÇÕES E CATEGORIAS
# ==========================================

class VideoCategory(str, Enum):
    DEFAULT = "default"
    KNOWLEDGE = "knowledge"
    BUSINESS = "business"
    OPINION = "opinion"
    EXPERIENCE = "experience"
    SPEECH = "speech"
    CONTENT_REVIEW = "content_review"
    ENTERTAINMENT = "entertainment"

VIDEO_CATEGORIES_CONFIG = {
    VideoCategory.OPINION: {
        "name": "Opinion & Commentary",
        "description": "Expression of views, critical analysis, and discussions",
        "icon": "💭",
        "color": "#722ed1"
    },
    # ... (outras categorias podem ser mantidas conforme sua necessidade)
}

# ==========================================
# 2. DEFINIÇÃO DE CAMINHOS (PATHS)
# ==========================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

# ==========================================
# 3. SISTEMA DE CONFIGURAÇÃO DINÂMICA (Pydantic)
# ==========================================

class Settings(BaseModel):
    """
    Mapeia exatamente a estrutura do seu settings.json.
    Adicione novos campos aqui para que sejam reconhecidos pelo sistema.
    """
    # Provedores e Chaves
    llm_provider: str = "openrouter"
    dashscope_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    siliconflow_api_key: str = ""
    groq_api_key: str = ""
    together_api_key: str = ""
    openrouter_api_key: str = ""
    g4f_api_key: str = ""
    
    # Modelo e Parâmetros de Processamento
    model_name: str = "mistralai/devstral-2512:free"
    chunk_size: int = 1500
    min_score_threshold: float = 0.3
    max_clips_per_collection: int = 5
    
    # Timeouts e Retentativas
    max_retries: int = 3
    timeout_seconds: int = 60
    
    # Parâmetros de Extração de Tópicos (Padrões)
    min_topic_duration_minutes: int = 2
    max_topic_duration_minutes: int = 12
    target_topic_duration_minutes: int = 5
    min_topics_per_chunk: int = 3
    max_topics_per_chunk: int = 8

    @validator('min_score_threshold')
    def validate_score_threshold(cls, v):
        return max(0.0, min(1.0, v))

@dataclass
class APIConfig:
    """Configuração final para ser consumida pelo LLMClient"""
    provider: str
    model_name: str
    api_key: str
    base_url: str
    max_tokens: int = 4096

# ==========================================
# 4. GERENCIADOR DE CONFIGURAÇÃO (MANAGER)
# ==========================================

class ConfigManager:
    """Centraliza o carregamento do JSON e a lógica de Provedores"""
    
    def __init__(self):
        self.settings = Settings()
        self.load()

    def load(self):
        """Carrega dados do settings.json"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # O Pydantic valida e preenche o objeto settings automaticamente
                    self.settings = Settings(**data)
            except Exception as e:
                print(f"⚠️ Erro ao carregar {SETTINGS_FILE}: {e}")
        else:
            print(f"ℹ️ {SETTINGS_FILE} não encontrado. Usando padrões.")

    def get_api_config(self) -> APIConfig:
        """
        Retorna a URL e a Chave correta baseada no 'llm_provider' do JSON
        """
        p = self.settings.llm_provider.lower()
        s = self.settings

        # Mapeamento de URLs de API
        base_urls = {
            "openrouter": "https://openrouter.ai/api/v1",
            "groq": "https://api.groq.com/openai/v1",
            "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "siliconflow": "https://api.siliconflow.cn/v1",
            "openai": "https://api.openai.com/v1",
            "together": "https://api.together.xyz/v1"
        }

        # Mapeamento de Chaves de API
        api_keys = {
            "openrouter": s.openrouter_api_key,
            "groq": s.groq_api_key,
            "dashscope": s.dashscope_api_key,
            "openai": s.openai_api_key,
            "siliconflow": s.siliconflow_api_key,
            "gemini": s.gemini_api_key,
            "together": s.together_api_key
        }

        return APIConfig(
            provider=p,
            model_name=s.model_name,
            api_key=api_keys.get(p, ""),
            base_url=base_urls.get(p, "https://api.openai.com/v1")
        )

    def get_project_paths(self, project_id: str) -> Dict[str, Path]:
        """Gera caminhos específicos para um projeto"""
        project_base = DATA_DIR / "projects" / project_id
        return {
            "base": project_base,
            "raw": project_base / "raw",
            "output": project_base / "output",
            "metadata": project_base / "metadata",
            "logs": project_base / "logs"
        }

# Instância global para ser importada por outros módulos
config_manager = ConfigManager()

# ==========================================
# 5. COMPATIBILIDADE COM CÓDIGO LEGADO
# ==========================================

def get_legacy_config() -> Dict[str, Any]:
    """Mantém suporte para partes do sistema que ainda usam dicionários fixos"""
    s = config_manager.settings
    api = config_manager.get_api_config()
    
    return {
        'PROJECT_ROOT': PROJECT_ROOT,
        'MODEL_NAME': s.model_name,
        'LLM_PROVIDER': s.llm_provider,
        'API_KEY': api.api_key,
        'BASE_URL': api.base_url,
        'CHUNK_SIZE': s.chunk_size,
        'MIN_SCORE_THRESHOLD': s.min_score_threshold,
        'MAX_CLIPS_PER_COLLECTION': s.max_clips_per_collection,
        'METADATA_DIR': DATA_DIR / "output" / "metadata",
    }