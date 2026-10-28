"""Cadenas activas de chatbot (títulos), cuestionarios y materiales."""
from .llm import chat_bot, llm, parser, parser_Material
from .prompts import GENERAR_CUESTIONARIOS_TEMPLATE, GENERAR_MATERIAL_TEMPLATE, get_chat_tittle_prompt


def get_chat_tittle_chain():
    return get_chat_tittle_prompt() | chat_bot


cuestionario_prompt = GENERAR_CUESTIONARIOS_TEMPLATE.partial(
    format_instructions=parser.get_format_instructions()
)
chain_cuestionarios = cuestionario_prompt | llm | parser

materiales_prompt = GENERAR_MATERIAL_TEMPLATE.partial(
    format_instructions=parser_Material.get_format_instructions()
)
chain_maateriales = materiales_prompt | llm | parser_Material
