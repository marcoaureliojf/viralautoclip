"""
LLM Client - Compatibility wrapper, using the new LLM Manager
"""
import json
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

# Importação robusta do ConfigManager e LLMManager
try:
    from core.config import config_manager
    from core.llm_manager import get_llm_manager
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import config_manager
    from core.llm_manager import get_llm_manager

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM Client - Wrapper de compatibilidade com limpeza robusta de JSON"""
    
    def __init__(self):
        # Busca dinamicamente do config_manager
        self.llm_manager = get_llm_manager()
    
    @property
    def model(self):
        """Retorna o modelo atual definido no settings.json"""
        return config_manager.settings.model_name
    
    def call(self, prompt: str, input_data: Any = None, language: Optional[str] = None) -> str:
        try:
            if language:
                prompt = self._inject_language_instruction(prompt, language)
            return self.llm_manager.call(prompt, input_data)
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise
    
    def call_with_retry(self, prompt: str, input_data: Any = None, max_retries: int = None, language: Optional[str] = None) -> str:
        # Se max_retries não for passado, usa o do config
        retries = max_retries or config_manager.settings.max_retries
        try:
            if language:
                prompt = self._inject_language_instruction(prompt, language)
            return self.llm_manager.call_with_retry(prompt, input_data, max_retries=retries)
        except Exception as e:
            logger.error(f"LLM retry call failed: {str(e)}")
            raise

    def _inject_language_instruction(self, prompt: str, language: str) -> str:
        """Injeta instrução de idioma no final do prompt original"""
        lang_instruction = f"\n\nIMPORTANT: You MUST output all textual content (titles, descriptions, reasons, etc.) in {language}. Keep JSON keys and structural identifiers in English."
        return prompt + lang_instruction

    def parse_json_response(self, response: str) -> Any:
        """
        Versão ultra-robusta para extrair JSON de modelos "chatty" (como Mistral/Llama).
        """
        if not response or not isinstance(response, str):
            return []

        # 1. Tentar extrair conteúdo entre blocos de código markdown ```json ... ```
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if code_block_match:
            candidate = code_block_match.group(1).strip()
            result = self._try_load_json(candidate)
            if result is not None:
                return result

        # 2. Se falhar, tentar encontrar o primeiro '[' ou '{' e o último ']' ou '}'
        # Isso remove textos explicativos antes ou depois do JSON
        json_pattern = re.search(r'([\\[\{][\s\S]*[\}\]])', response)
        if json_pattern:
            candidate = json_pattern.group(1).strip()
            result = self._try_load_json(candidate)
            if result is not None:
                return result

        # 3. Tentativa final: limpeza agressiva de caracteres de controle
        cleaned = self._aggressive_clean(response)
        result = self._try_load_json(cleaned)
        if result is not None:
            return result

        logger.error(f"Falha total ao parsear JSON. Resposta original: {response[:200]}...")
        raise ValueError("A resposta do modelo não contém um JSON válido.")

    def _try_load_json(self, json_str: str) -> Optional[Any]:
        """Tenta carregar JSON e aplicar correções comuns em caso de erro"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                # Tenta corrigir vírgulas extras ou aspas simples
                fixed = self._fix_common_errors(json_str)
                return json.loads(fixed)
            except:
                return None

    def _fix_common_errors(self, s: str) -> str:
        """Correções rápidas de sintaxe JSON"""
        # Remove vírgulas antes de fechamento de chaves/colchetes
        s = re.sub(r',\s*([\]\}])', r'\1', s)
        # Tenta converter aspas simples em duplas (arriscado, mas ajuda em muitos casos)
        s = re.sub(r"(\s*)'([^']*)'(\s*):", r'\1"\2"\3:', s)
        return s

    def _aggressive_clean(self, s: str) -> str:
        """Remove BOM e caracteres invisíveis"""
        s = s.replace('\ufeff', '').strip()
        # Remove caracteres de controle ASCII
        s = "".join(ch for ch in s if ord(ch) >= 32 or ch in "\n\r\t")
        return s

    def _validate_json_structure(self, data: Any) -> bool:
        """
        Validação básica de estrutura para garantir que o LLM não retornou lixo.
        Aceita listas ou dicionários não vazios.
        """
        if data is None:
            return False
        if isinstance(data, (list, dict)):
            # Se for lista ou dict, consideramos válido se o parse ocorreu
            # (Pode ser expandido conforme a necessidade de cada Step)
            return True
        return False

    def get_current_provider_info(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "provider": config_manager.settings.llm_provider,
            "chunk_size": config_manager.settings.chunk_size
        }