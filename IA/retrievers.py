# ==========================================IMPORTACIONES================================================

from langchain_community.vectorstores import Chroma  # base de datos 
from langchain_community.vectorstores import FAISS  # base de datos 

#*******************************************IMPORTACIONES**********************************************************


def get_base_retriever(vectorstore: FAISS):
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 10, #4
                       "lambda_mult": 0.7, 
                       "fetch_k": 20}
    )



# def get_base_retriever(vectorstore: Chroma):
#     return vectorstore.as_retriever(
#         # search_type="similarity",
#         search_kwargs={"k": 6}
#     )