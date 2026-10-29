# ====================================================IMPORTS=========================================================

from typing import List,Dict, Any, Optional

from typing_extensions import TypedDict,Annotated

from langchain_core.messages import BaseMessage

from pydantic import BaseModel,Field

from langgraph.graph.message import add_messages

from langchain_core.output_parsers import PydanticOutputParser

# **********************************************IMPORTS********************************************************



# estado extendido que combina mensages con menmoria vectorial 

class MemoryState(TypedDict):
    messages: Annotated[List[BaseMessage],add_messages]
    vector_memories: List[str]
    user_profile: Dict[str,Any]
    last_memory_extraction: Optional[str]
    user_dir: str
    chat_id: str


class ExtractedMemory(BaseModel):
    category : str = Field(description="categoria: personal,profesional,aspiraciones, hechos importantes")
    content: str = Field(description="contenido de la memoria extraida")
    importance: int = Field(description="importancia de la memoria del 1 al 5", ge=2,le=5)

parser_extract_memory = PydanticOutputParser(pydantic_object=ExtractedMemory)


