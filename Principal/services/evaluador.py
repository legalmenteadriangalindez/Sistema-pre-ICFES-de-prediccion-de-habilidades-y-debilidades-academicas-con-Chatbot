
# ==========================================IMPORTACIONES================================================

from Principal.IA.llm import chat_bot

# ******************************************IMPORTACIOONES****************************************************


# =============================================EVALUAR PDFs=========================================================



# def evaluar(texto_pdf: str,descripcion: str):
#     try:
        

#         resultado = evaluar_pdf.invoke({
#             "texto_pdf": texto_pdf,
#             "descripcion": descripcion
#         })
#         return resultado
#     except Exception as e: 
#         return "error "
# ***********************************************************************************************************************

# services/evaluador.py


# def evaluar_pdf(texto_pdf: str, descripcion: str):
#     """
#     Evalúa un PDF usando el modelo LLM.
#     """
#     try:
#         return chat_bot.invoke({
#             "texto_pdf": texto_pdf,
#             "descripcion": descripcion
#         })
#     except Exception:
#         return None
