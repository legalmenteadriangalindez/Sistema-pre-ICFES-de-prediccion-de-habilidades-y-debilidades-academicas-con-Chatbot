# ==========================================IMPORTACIONES================================================

from langchain_community.embeddings import OllamaEmbeddings  # librreria para convertir texto a vectores "embedings"

from langchain_huggingface import HuggingFaceEmbeddings
#*******************************************IMPORTACIONES**********************************************************


def get_embedding(model_name:str):
    return OllamaEmbeddings(model=model_name,
    base_url="http://localhost:11434"
    )

# def get_embedding(model_name:str):
#     return HuggingFaceEmbeddings(
#         model_name=model_name,
#         model_kwargs={"device": "cpu"},
#         encode_kwargs={"normalize_embeddings": True}
#     )
