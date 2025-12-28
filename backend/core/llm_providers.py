"""
多模型提供商统一接口
支持OpenAI、Gemini、硅基流动、阿里DashScope等
"""
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """模型提供商类型"""
    DASHSCOPE = "dashscope"  # 阿里通义千问
    OPENAI = "openai"        # OpenAI
    GEMINI = "gemini"        # Google Gemini
    SILICONFLOW = "siliconflow"  # 硅基流动
    GROQ = "groq"            # Groq
    TOGETHER = "together"    # Together AI
    OPENROUTER = "openrouter" # OpenRouter
    G4F = "g4f"              # GPT4Free (Custo Zero)
    CEREBRAS = "cerebras"    # Cerebras

@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    display_name: str
    provider: ProviderType
    max_tokens: int
    cost_per_token: Optional[float] = None
    description: Optional[str] = None
    is_free: bool = False

@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None

class LLMProvider(ABC):
    """LLM提供商抽象基类"""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        self.api_key = api_key
        self.model_name = model_name
        self.kwargs = kwargs
    
    @abstractmethod
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        """
        调用模型API
        
        Args:
            prompt: 提示词
            input_data: 输入数据
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 模型响应
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[ModelInfo]:
        """
        获取可用模型列表
        
        Returns:
            List[ModelInfo]: 可用模型列表
        """
        pass
    
    def _build_full_input(self, prompt: str, input_data: Any = None) -> str:
        """构建完整的输入"""
        if input_data:
            if isinstance(input_data, dict):
                return f"{prompt}\n\n输入内容：\n{json.dumps(input_data, ensure_ascii=False, indent=2)}"
            else:
                return f"{prompt}\n\n输入内容：\n{input_data}"
        return prompt

class DashScopeProvider(LLMProvider):
    """阿里DashScope提供商"""
    
    def __init__(self, api_key: str, model_name: str = "qwen-plus", **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        try:
            from dashscope import Generation
            self.generation = Generation
        except ImportError:
            raise ImportError("请安装dashscope: pip install dashscope")
    
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        """调用DashScope API"""
        try:
            full_input = self._build_full_input(prompt, input_data)
            
            response_or_gen = self.generation.call(
                model=self.model_name,
                prompt=full_input,
                api_key=self.api_key,
                stream=False,
                **kwargs
            )
            
            # 处理响应
            # DashScope的GenerationResponse虽然有__iter__方法，但不是真正的迭代器
            # 直接使用响应对象本身
            response = response_or_gen
            
            if response and response.status_code == 200:
                if response.output and response.output.text is not None:
                    return LLMResponse(
                        content=response.output.text,
                        model=self.model_name,
                        finish_reason=getattr(response.output, 'finish_reason', None)
                    )
                else:
                    finish_reason = getattr(response.output, 'finish_reason', 'unknown') if response.output else 'unknown'
                    logger.warning(f"API请求成功，但输出为空。结束原因: {finish_reason}")
                    return LLMResponse(content="")
            else:
                code = getattr(response, 'code', 'N/A')
                message = getattr(response, 'message', '未知API错误')
                raise Exception(f"API调用失败 - Status: {response.status_code}, Code: {code}, Message: {message}")
                
        except Exception as e:
            logger.error(f"DashScope调用失败: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """测试DashScope连接"""
        try:
            response = self.call("请回复'测试成功'")
            return "测试成功" in response.content or "success" in response.content.lower()
        except Exception as e:
            logger.error(f"DashScope连接测试失败: {e}")
            return False
    
    def get_available_models(self) -> List[ModelInfo]:
        """获取DashScope可用模型"""
        return [
            ModelInfo(
                name="qwen-plus",
                display_name="通义千问Plus",
                provider=ProviderType.DASHSCOPE,
                max_tokens=8192,
                description="阿里云通义千问Plus模型",
                is_free=False
            ),
            ModelInfo(
                name="qwen-max",
                display_name="通义千问Max",
                provider=ProviderType.DASHSCOPE,
                max_tokens=8192,
                description="阿里云通义千问Max模型",
                is_free=False
            ),
            ModelInfo(
                name="qwen-turbo",
                display_name="通义千问Turbo",
                provider=ProviderType.DASHSCOPE,
                max_tokens=8192,
                description="阿里云通义千问Turbo模型",
                is_free=False
            )
        ]

class OpenAIProvider(LLMProvider):
    """OpenAI提供商"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("请安装openai: pip install openai")
    
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        """调用OpenAI API"""
        try:
            full_input = self._build_full_input(prompt, input_data)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": full_input}],
                **kwargs
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=self.model_name,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            logger.error(f"OpenAI调用失败: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """测试OpenAI连接"""
        try:
            response = self.call("请回复'测试成功'")
            return "测试成功" in response.content or "success" in response.content.lower()
        except Exception as e:
            logger.error(f"OpenAI连接测试失败: {e}")
            return False
    
    def get_available_models(self) -> List[ModelInfo]:
        """获取OpenAI可用模型"""
        return [
            ModelInfo(
                name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                provider=ProviderType.OPENAI,
                max_tokens=4096,
                description="OpenAI GPT-3.5 Turbo模型",
                is_free=False
            ),
            ModelInfo(
                name="gpt-4",
                display_name="GPT-4",
                provider=ProviderType.OPENAI,
                max_tokens=8192,
                description="OpenAI GPT-4模型",
                is_free=False
            ),
            ModelInfo(
                name="gpt-4-turbo",
                display_name="GPT-4 Turbo",
                provider=ProviderType.OPENAI,
                max_tokens=128000,
                description="OpenAI GPT-4 Turbo模型",
                is_free=False
            )
        ]

class GeminiProvider(LLMProvider):
    """Google Gemini提供商"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash", **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        except ImportError:
            raise ImportError("请安装google-generativeai: pip install google-generativeai")
    
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        """调用Gemini API"""
        try:
            full_input = self._build_full_input(prompt, input_data)
            
            response = self.model.generate_content(full_input, **kwargs)
            
            return LLMResponse(
                content=response.text,
                model=self.model_name,
                finish_reason=getattr(response, 'finish_reason', None)
            )
            
        except Exception as e:
            logger.error(f"Gemini调用失败: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """测试Gemini连接"""
        try:
            response = self.call("请回复'测试成功'")
            return "测试成功" in response.content or "success" in response.content.lower()
        except Exception as e:
            logger.error(f"Gemini连接测试失败: {e}")
            return False
    
    def get_available_models(self) -> List[ModelInfo]:
        """获取Gemini可用模型"""
        return [
            ModelInfo(
                name="gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                provider=ProviderType.GEMINI,
                max_tokens=1000000,
                description="Google Gemini 2.5 Flash模型",
                is_free=False
            ),
            ModelInfo(
                name="gemini-1.5-pro",
                display_name="Gemini 1.5 Pro",
                provider=ProviderType.GEMINI,
                max_tokens=2000000,
                description="Google Gemini 1.5 Pro模型",
                is_free=False
            ),
            ModelInfo(
                name="gemini-1.5-flash",
                display_name="Gemini 1.5 Flash",
                provider=ProviderType.GEMINI,
                max_tokens=1000000,
                description="Google Gemini 1.5 Flash模型",
                is_free=False
            )
        ]

class SiliconFlowProvider(LLMProvider):
    """硅基流动提供商"""
    
    def __init__(self, api_key: str, model_name: str = "Qwen/Qwen2.5-7B-Instruct", **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.base_url = "https://api.siliconflow.cn/v1"
    
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        """调用硅基流动API"""
        try:
            import requests
            
            full_input = self._build_full_input(prompt, input_data)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": full_input}],
                "stream": False,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage")
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=self.model_name,
                finish_reason=result["choices"][0].get("finish_reason")
            )
            
        except Exception as e:
            logger.error(f"硅基流动调用失败: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """测试硅基流动连接"""
        try:
            response = self.call("请回复'测试成功'")
            return "测试成功" in response.content or "success" in response.content.lower()
        except Exception as e:
            logger.error(f"硅基流动连接测试失败: {e}")
            return False
    
    def get_available_models(self) -> List[ModelInfo]:
        """获取硅基流动可用模型"""
        return [
            ModelInfo(
                name="Qwen/Qwen2.5-7B-Instruct",
                display_name="Qwen2.5-7B",
                provider=ProviderType.SILICONFLOW,
                max_tokens=32768,
                description="硅基流动Qwen2.5-7B模型",
                is_free=True
            ),
            ModelInfo(
                name="Qwen/Qwen2.5-14B-Instruct",
                display_name="Qwen2.5-14B",
                provider=ProviderType.SILICONFLOW,
                max_tokens=32768,
                description="硅基流动Qwen2.5-14B模型",
                is_free=True
            ),
            ModelInfo(
                name="Qwen/Qwen2.5-32B-Instruct",
                display_name="Qwen2.5-32B",
                provider=ProviderType.SILICONFLOW,
                max_tokens=32768,
                description="硅基流动Qwen2.5-32B模型",
                is_free=False
            ),
            ModelInfo(
                name="deepseek-ai/DeepSeek-V2.5",
                display_name="DeepSeek-V2.5",
                provider=ProviderType.SILICONFLOW,
                max_tokens=65536,
                description="硅基流动DeepSeek-V2.5模型",
                is_free=True
            )
        ]

class GroqProvider(LLMProvider):
    """Groq提供商 (极速)"""
    
    def __init__(self, api_key: str, model_name: str = "llama-3.1-70b-versatile", **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        except ImportError:
            raise ImportError("请安装openai: pip install openai")
    
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        try:
            full_input = self._build_full_input(prompt, input_data)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": full_input}],
                **kwargs
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model_name,
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            logger.error(f"Groq调用失败: {str(e)}")
            raise

    def test_connection(self) -> bool:
        try:
            self.call("Hi", max_tokens=5)
            return True
        except:
            return False

    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("llama-3.1-8b-instant", "Llama 3.1 8B (Groq)", ProviderType.GROQ, 131072, is_free=True),
            ModelInfo("llama-3.3-70b-versatile", "Llama 3.3 70B (Groq)", ProviderType.GROQ, 131072, is_free=False),
            ModelInfo("meta-llama/llama-guard-4-12b", "Llama Guard 4 12B (Groq)", ProviderType.GROQ, 131072, is_free=False),
            ModelInfo("openai/gpt-oss-120b", "GPT OSS 120B (Groq)", ProviderType.GROQ, 131072, is_free=False),
            ModelInfo("openai/gpt-oss-20b", "GPT OSS 20B (Groq)", ProviderType.GROQ, 131072, is_free=False),
            ModelInfo("mixtral-8x7b-32768", "Mixtral 8x7B (Groq)", ProviderType.GROQ, 32768, is_free=True),
        ]

class TogetherProvider(LLMProvider):
    """Together AI提供商"""
    
    def __init__(self, api_key: str, model_name: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.together.xyz/v1"
            )
        except ImportError:
            raise ImportError("请安装openai: pip install openai")
    
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        try:
            full_input = self._build_full_input(prompt, input_data)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": full_input}],
                **kwargs
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model_name,
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            logger.error(f"Together调用失败: {str(e)}")
            raise

    def test_connection(self) -> bool:
        try:
            self.call("Hi", max_tokens=5)
            return True
        except:
            return False

    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "Llama 3.1 70B (Together)", ProviderType.TOGETHER, 131072, is_free=False),
            ModelInfo("meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "Llama 3.1 8B (Together)", ProviderType.TOGETHER, 131072, is_free=False),
        ]

class OpenRouterProvider(LLMProvider):
    """OpenRouter提供商"""
    
    def __init__(self, api_key: str, model_name: str = "google/gemini-flash-1.5", **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        except ImportError:
            raise ImportError("请安装openai: pip install openai")
    
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        try:
            full_input = self._build_full_input(prompt, input_data)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": full_input}],
                **kwargs
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model_name,
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            logger.error(f"OpenRouter调用失败: {str(e)}")
            raise

    def test_connection(self) -> bool:
        try:
            self.call("Hi", max_tokens=5)
            return True
        except:
            return False

    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("xiaomi/mimo-v2-flash:free", "Xiaomi MiMo-V2-Flash (Free)", ProviderType.OPENROUTER, 262144, is_free=True),
            ModelInfo("mistralai/mistral-devstral-2512:free", "Mistral Devstral 2 2512 (Free)", ProviderType.OPENROUTER, 262144, is_free=True),
            ModelInfo("kwaipilot/kat-coder-pro-v1:free", "Kwaipilot KAT-Coder-Pro V1 (Free)", ProviderType.OPENROUTER, 256000, is_free=True),
            ModelInfo("tngtech/deepseek-r1t2-chimera:free", "TNG DeepSeek R1T2 Chimera (Free)", ProviderType.OPENROUTER, 164000, is_free=True),
            ModelInfo("nex-agi/deepseek-v3.1-nex-n1:free", "Nex AGI DeepSeek V3.1 Nex N1 (Free)", ProviderType.OPENROUTER, 131000, is_free=True),
            ModelInfo("nvidia/nemotron-3-nano-30b-a3b:free", "NVIDIA Nemotron 3 Nano 30B A3B (Free)", ProviderType.OPENROUTER, 256000, is_free=True),
            ModelInfo("tngtech/deepseek-r1t-chimera:free", "TNG DeepSeek R1T Chimera (Free)", ProviderType.OPENROUTER, 164000, is_free=True),
            ModelInfo("z-ai/glm-4.5-air:free", "Z.AI GLM 4.5 Air (Free)", ProviderType.OPENROUTER, 131000, is_free=True),
            ModelInfo("nvidia/nemotron-nano-12b-2-vl:free", "NVIDIA Nemotron Nano 12B 2 VL (Free)", ProviderType.OPENROUTER, 128000, is_free=True),
            ModelInfo("tngtech/r1t-chimera:free", "TNG R1T Chimera (Free)", ProviderType.OPENROUTER, 164000, is_free=True),
            ModelInfo("google/gemini-flash-1.5", "Gemini Flash 1.5", ProviderType.OPENROUTER, 1000000, is_free=False),
            ModelInfo("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet", ProviderType.OPENROUTER, 200000, is_free=False),
        ]

class G4FProvider(LLMProvider):
    """GPT4Free提供商 (Custo Zero)"""
    
    def __init__(self, api_key: str = "not-needed", model_name: str = "gpt-4o", **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        try:
            import g4f
            self.g4f = g4f
        except ImportError:
            raise ImportError("请安装g4f: pip install g4f")
    
    def call(self, prompt: str, input_data: Any = None, **kwargs) -> LLMResponse:
        try:
            full_input = self._build_full_input(prompt, input_data)
            
            # g4f 的模型映射
            model = self.g4f.models.gpt_4o
            if hasattr(self.g4f.models, self.model_name):
                model = getattr(self.g4f.models, self.model_name)
            
            response = self.g4f.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": full_input}],
                **kwargs
            )
            
            # 清理响应内容 (处理 JSON 块)
            content = str(response)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return LLMResponse(
                content=content,
                model=self.model_name
            )
        except Exception as e:
            logger.error(f"G4F调用失败: {str(e)}")
            raise

    def test_connection(self) -> bool:
        try:
            self.call("Hi")
            return True
        except:
            return False

    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("gpt-4o", "GPT-4o (G4F)", ProviderType.G4F, 4096, is_free=True),
            ModelInfo("gpt-4", "GPT-4 (G4F)", ProviderType.G4F, 4096, is_free=True),
            ModelInfo("claude-3.5-sonnet", "Claude 3.5 Sonnet (G4F)", ProviderType.G4F, 4096, is_free=True),
        ]

class CerebrasProvider(OpenAIProvider):
    """Cerebras AI提供商 (超高速)"""
    
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b", **kwargs):
        # Cerebras 使用 OpenAI 兼容的 SDK
        super().__init__(api_key, model_name, **kwargs)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.cerebras.ai/v1"
            )
        except ImportError:
            raise ImportError("请安装openai: pip install openai")
            
    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("gpt-oss-120b", "GPT OSS 120B (Cerebras)", ProviderType.CEREBRAS, 65536, is_free=False),
            ModelInfo("llama-3.3-70b", "Llama 3.3 70B (Cerebras)", ProviderType.CEREBRAS, 65536, is_free=False),
            ModelInfo("llama3.1-8b", "Llama 3.1 8B (Cerebras)", ProviderType.CEREBRAS, 8192, is_free=True),
            ModelInfo("qwen-3-235b-a22b-instruct-2507", "Qwen 3 235B (Cerebras)", ProviderType.CEREBRAS, 65536, is_free=False),
            ModelInfo("qwen-3-32b", "Qwen 3 32B (Cerebras)", ProviderType.CEREBRAS, 65536, is_free=False),
            ModelInfo("zai-glm-4.6", "GLM 4.6 (Cerebras)", ProviderType.CEREBRAS, 64000, is_free=False),
        ]

class LLMProviderFactory:
    """LLM提供商工厂"""
    
    _providers = {
        ProviderType.DASHSCOPE: DashScopeProvider,
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.GEMINI: GeminiProvider,
        ProviderType.SILICONFLOW: SiliconFlowProvider,
        ProviderType.GROQ: GroqProvider,
        ProviderType.TOGETHER: TogetherProvider,
        ProviderType.OPENROUTER: OpenRouterProvider,
        ProviderType.G4F: G4FProvider,
        ProviderType.CEREBRAS: CerebrasProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_type: ProviderType, api_key: str, model_name: str, **kwargs) -> LLMProvider:
        """创建提供商实例"""
        if provider_type not in cls._providers:
            raise ValueError(f"不支持的提供商类型: {provider_type}")
        
        provider_class = cls._providers[provider_type]
        return provider_class(api_key, model_name, **kwargs)
    
    @classmethod
    def get_all_available_models(cls) -> Dict[ProviderType, List[ModelInfo]]:
        """获取所有提供商的可用模型"""
        models = {}
        for provider_type, provider_class in cls._providers.items():
            try:
                # 创建临时实例来获取模型列表
                temp_provider = provider_class("dummy_key", "dummy_model")
                models[provider_type] = temp_provider.get_available_models()
            except Exception as e:
                logger.warning(f"无法获取{provider_type.value}的模型列表: {e}")
                models[provider_type] = []
        return models
