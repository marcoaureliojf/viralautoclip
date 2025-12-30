"""
LLM Manager - Gerenciamento Unificado de Provedores (OpenRouter, Groq, etc.)
Sincronizado com o ConfigManager centralizado.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Importação dos Provedores e Factory
from .llm_providers import (
    LLMProvider, LLMProviderFactory, ProviderType
)
# Importação do ConfigManager centralizado
from .config import config_manager

logger = logging.getLogger(__name__)

class LLMManager:
    """
    Manager que atua como ponte entre as configurações do JSON e os 
    provedores de API. Suporta troca dinâmica de modelos e provedores.
    """
    
    def __init__(self):
        self.current_provider: Optional[LLMProvider] = None
        self._initialize_provider()
    
    def _initialize_provider(self):
        """
        Inicializa o provedor de LLM buscando dados dinâmicos do ConfigManager.
        Configura automaticamente a URL Base para OpenRouter, Groq ou OpenAI.
        """
        try:
            # Obtém a configuração ativa do settings.json via ConfigManager
            api_cfg = config_manager.get_api_config()
            provider_type = ProviderType(api_cfg.provider)
            
            if api_cfg.api_key:
                # Criamos o provedor passando a base_url (essencial para OpenRouter)
                self.current_provider = LLMProviderFactory.create_provider(
                    provider_type=provider_type,
                    api_key=api_cfg.api_key,
                    model_name=api_cfg.model_name,
                    base_url=api_cfg.base_url
                )
                logger.info(f"LLMManager: Provedor '{provider_type.value}' inicializado com sucesso.")
                logger.info(f"Modelo Ativo: {api_cfg.model_name}")
            else:
                logger.warning(f"LLMManager: Chave de API ausente para o provedor '{provider_type.value}'.")
                
        except Exception as e:
            logger.error(f"LLMManager: Falha crítica na inicialização: {e}")
            self.current_provider = None

    def call(self, prompt: str, input_data: Any = None, **kwargs) -> str:
        """
        Realiza uma chamada direta ao provedor configurado.
        """
        # Recarrega configurações a cada chamada para suportar troca de chaves "quente"
        self.refresh()

        if not self.current_provider:
            raise ValueError("Nenhum provedor de LLM configurado. Verifique seu settings.json.")
        
        try:
            response = self.current_provider.call(prompt, input_data, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"LLMManager Call Error: {e}")
            raise

    def call_with_retry(self, prompt: str, input_data: Any = None, max_retries: int = None, **kwargs) -> str:
        """
        Executa chamadas com retry inteligente e Exponential Backoff.
        Trata especificamente o erro 429 (Rate Limit) do OpenRouter/Groq.
        """
        settings = config_manager.settings
        total_retries = max_retries or settings.max_retries
        
        for attempt in range(total_retries):
            try:
                return self.call(prompt, input_data, **kwargs)
            
            except Exception as e:
                err_msg = str(e).lower()
                
                # Lógica de espera diferenciada para Rate Limit (429)
                if "429" in err_msg or "rate limit" in err_msg:
                    # Espera progressiva longa: 20s, 40s, 60s...
                    wait_time = (attempt + 1) * 20 
                    logger.warning(f"Rate Limit (429) detectado no {settings.llm_provider}. Pausando por {wait_time}s...")
                else:
                    # Erros genéricos: 2s, 4s, 8s...
                    wait_time = 2 ** (attempt + 1)
                
                if attempt == total_retries - 1:
                    logger.error(f"LLMManager: Máximo de {total_retries} tentativas atingido. Abortando.")
                    raise
                
                time.sleep(wait_time)
                logger.info(f"LLMManager: Tentativa {attempt + 2} de {total_retries}...")
        
        return ""

    def refresh(self):
        """
        Força a recarga das configurações do disco e reinicializa o provedor.
        Útil se o arquivo settings.json for editado manualmente.
        """
        config_manager.load()
        self._initialize_provider()

    def get_current_provider_info(self) -> Dict[str, Any]:
        """Retorna metadados do provedor ativo para interface ou logs"""
        if not self.current_provider:
            return {"provider": None, "model": None, "status": "offline"}
            
        api_cfg = config_manager.get_api_config()
        return {
            "provider": api_cfg.provider,
            "model": api_cfg.model_name,
            "base_url": api_cfg.base_url,
            "status": "online"
        }

# ==========================================
# GESTÃO DE INSTÂNCIA ÚNICA (SINGLETON)
# ==========================================

_llm_manager_instance: Optional[LLMManager] = None

def get_llm_manager() -> LLMManager:
    """Retorna a instância global do LLMManager (Singleton)"""
    global _llm_manager_instance
    if _llm_manager_instance is None:
        _llm_manager_instance = LLMManager()
    return _llm_manager_instance

def initialize_llm_manager() -> LLMManager:
    """Reinicializa a instância global"""
    global _llm_manager_instance
    _llm_manager_instance = LLMManager()
    return _llm_manager_instance