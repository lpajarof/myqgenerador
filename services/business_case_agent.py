import os
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from utils.models_IA import ModelsIA

class BusinessCaseAgent:
    def __init__(self, prompt_path: str = r"services/system_prompt/business_case_analyst_prompt.md"):
        """
        Inicializa el Agente 1 cargando el modelo de IA y su respectivo System Prompt.
        """
        self.prompt_path = prompt_path
        self.model = ModelsIA().get_model()
        self.system_prompt = self._load_system_prompt()
        self.agent = self._initialize_agent()

    def _load_system_prompt(self) -> str:
        """Lee el archivo de System Prompt desde la ruta especificada."""
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"No se encontró el archivo de prompt en: {self.prompt_path}")
            
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _initialize_agent(self):
        """Crea e inicializa la instancia interna del agente de LangChain."""
        return create_agent(
            model=self.model,
            system_prompt=self.system_prompt
        )

    def get_response(self, user_input: str) -> str:
        """
        Envía el input del usuario al agente y retorna la respuesta de texto plano.
        """
        query = HumanMessage(content=user_input)
        response = self.agent.invoke({"messages": [query]})
        
        # Retorna el contenido del último mensaje de la cadena
        return response["messages"][-1].content