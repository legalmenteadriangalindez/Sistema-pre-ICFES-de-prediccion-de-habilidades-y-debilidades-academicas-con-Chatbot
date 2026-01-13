# ==========================================IMPORTACIONES================================================
# from langchain_community.vectorstores import Chroma  # base de datos 
from langchain_community.vectorstores import FAISS  # base de datos 
import os

from Principal.IA.embeddings import get_embedding

from langchain_ollama import OllamaEmbeddings

from langchain_community.vectorstores import Chroma  # base de datos

#*******************************************IMPORTACIONES**********************************************************
CHROMA_DB = "ProyectoDeGrado\\ChromaDB"  # ruta de la base de datos vectorial
embedings = get_embedding("mxbai-embed-large")


vectorStoreChroma = Chroma(
    collection_name= "memory_chat",
    embedding_function=embedings,
    persist_directory=CHROMA_DB
)

print("Inicializando Chroma en:", CHROMA_DB)

# vectore store con  chroma 
# def build_vectorestore(documents: list, persist_directory: str,embeddings):
#    if not documents:
#       raise ValueError("No hay documentos para indexar")
   

#    if os.path.isdir(persist_directory) and os.listdir(persist_directory):
#        print(f"base de datos vectorial ya creada reutilizando {persist_directory}")
#        return Chroma( # crea la base de datos vectorial
#             persist_directory=persist_directory,
#             embedding=embeddings,           
#         )

#    os.makedirs(persist_directory,exist_ok=True)


#    vectorstore = Chroma.from_documents( # crea la base de datos vectorial
#      documents=documents,
#      embedding=embeddings,
#      persist_directory=persist_directory,
#     )
   
#    vectorstore.persist()
#    # Confirmación de persistencia
#    if os.listdir(persist_directory):
#        print(f"Base de datos persistida correctamente en: {persist_directory}")
#    else:
#        print(f"No se encontraron archivos en el directorio: {persist_directory}")
#    return vectorstore

def build_vectorestore(documents: list, persist_directory: str,embeddings):
   if not documents:
      raise ValueError("No hay documentos para indexar")
   

   if os.path.isdir(persist_directory) and os.listdir(persist_directory):
       print(f"base de datos vectorial ya creada reutilizando {persist_directory}")
       return FAISS.load_local( # crea la base de datos vectorial
            folder_path=persist_directory,
            embeddings=embeddings,  
            allow_dangerous_deserialization=True         
        )

   os.makedirs(persist_directory,exist_ok=True)


   vectorstore = FAISS.from_documents( # crea la base de datos vectorial
     documents=documents,
     embedding=embeddings,
    #  persist_directory=persist_directory,
    )
   
   vectorstore.save_local(persist_directory)
   # Confirmación de persistencia
   if os.listdir(persist_directory):
       print(f"Base de datos persistida correctamente en: {persist_directory}")
   else:
       print(f"No se encontraron archivos en el directorio: {persist_directory}")
   return vectorstore



