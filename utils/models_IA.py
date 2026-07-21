import os
from typing import Optional
from langchain_ollama import ChatOllama

class ModelsIA:
    """Clase que decide qué modelo usar para los agentes según la
    variable de entorno MODEL y el proveedor solicitado.

    Uso:
        m = ModelsIA()  # leerá os.environ.get('MODEL')
        model_name = m.get_model_for_provider('openai')
    """

    # Mapeo por defecto por proveedor; se puede sobrescribir pasando
    # una variable de entorno MODEL con un nombre de modelo preferido.
    DEFAULTS = {
        "openai": "gpt-5.4-nano",        
        "anthropic": "claude-haiku-4-5",
        "google_genai:": "gemini-3.1-flash-lite",
        "ollama": "gpt-oss:120b",
    }

    def __init__(self, model_env: Optional[str] = None):
        # si no se pasa, lee la variable de entorno MODEL
        self.model_env = model_env or os.environ.get("MODEL")

    def get_model(self) -> str:
        """
        """

        if self.model_env:
            env_val = self.model_env.strip()
            # formato esperado opcional: 'provider:modelname' -> usar modelname
            if ":" in env_val:
                left, right = env_val.split(":", 1)
                if left.lower() == 'openai' or left.lower() == 'anthropic':
                    return right
                elif left.lower() == 'google_genai':
                    return env_val
                elif left.lower() == 'ollama':
                    model_ollama = ChatOllama(
                        model=right,
                        base_url="https://ollama.com",
                        temperature=0.1,
                        client_kwargs={
                            "headers": {
                                'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')
                            }
                        }
                    )
                    return model_ollama
                return env_val           
            return env_val

        
        raise ValueError(f"Proveedor desconocido y sin MODEL definido")


__all__ = ["ModelsIA"]
