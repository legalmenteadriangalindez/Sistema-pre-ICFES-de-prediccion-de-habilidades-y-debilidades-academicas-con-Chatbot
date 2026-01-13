# =====================================IMPPORTACIONES=========================================

from pypdf import PdfReader # libreria para leer PDFs

from io import BytesIO  # leer pdf en bites

from langchain_community.document_loaders import PyPDFLoader,WebBaseLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .llm import chat_bot

from langchain_community.document_loaders import PyPDFDirectoryLoader

import re

import os

BASURA= [
        r"Cuadernillo de preguntas",
        r"Saber\s*11",
        r"Prueba\s*(de)?",
        r"ICFES",
        r"febrero\s*\d{4}",
        r"\d{4}",
    ]

# ************************************ IMPORTACIONES *******************************************

# ===============================FUNCION PARA EXTRAER TEXTO PDFs=======================================================================
def prueba(ruta: str):
    
    loader = PyPDFLoader(ruta)
    pages= loader.load()
    text_spliter =RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=50
    )
    chunks= text_spliter.split_documents(pages)
    sumaries =[]
    for i in range(0,len(chunks),8):
       texto = " ".join(c.page_content for c in chunks[i:i+8])
       respuesta=chat_bot.invoke(f"resume el siguiente texto en un maximo dee 5 frases:  {texto}")
       sumaries.append(respuesta.content)
    intermedios=[]
    for i in range(0,len(sumaries),10):
       texto = " ".join(sumaries[i:i+10])
       respuesta=chat_bot.invoke(f"condensa el siguiente texto en un parrafo corto:  {texto}")
       intermedios.append(respuesta.content)
    resumen_final= chat_bot.invoke(f"haz un resumen final claro y coherente en maximo 10 frases: {" ".join(intermedios)}")
    print(resumen_final.content)



def open_documents_by_area(path_data: str):
    all_documents= []
    seen_sources= set()
    # leer datos
    for area in os.listdir(path_data):
            area_path=os.path.join(path_data,area)
            if not os.path.isdir(area_path):
               continue
            
            loader= PyPDFDirectoryLoader(area_path)   
            documents = loader.load()
            for doc in documents:
               doc.metadata["area"] = area
               doc.page_content= clean_text(doc.page_content)
               source= doc.metadata.get("source")
               if source in seen_sources:
                   continue
               seen_sources.add(source)
               print(f"Documento cargado: {doc.metadata.get('source', 'sin ruta')}")
               all_documents.append(doc)
    return all_documents


   

def clean_text(texto: str)->str:
    texto = texto.lower()

    for patron in BASURA:
        texto = re.sub(patron," ",texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def is_portada(doc) -> bool:
    if doc.metadata.get("page") == 0:
        return True
    if len(doc.page_content.strip()) < 300:
        return True
    return False


def extraer_texto_pdf(archivo_pdf):
    try:
        pdf_reader = PdfReader(BytesIO(archivo_pdf.read()))
        texto_completo = ""
        
        for numero_pagina,pagina in enumerate(pdf_reader.pages,1):
            texto_pagina = pagina.extract_text()
            if texto_pagina and texto_pagina.strip():
                texto_completo += f'\n --- PAGINA {numero_pagina}---\n'
                texto_completo += texto_pagina +'\n'
        
        texto_completo= texto_completo.strip()
        if not texto_completo:
            return "errror: el PDF parece estar vacio o no tiene texto extraible"   
        return texto_completo
    except Exception as e:
        return f'Error: procesar archivo PDF: {str(e)}'
    


def get_texto_PDF(ruta: str):
   try:
      with open(ruta,"rb") as pdf:
       texto = extraer_texto_pdf(pdf)
       return texto
   except FileNotFoundError:
       return "EL ARCHIVO PDF NO EXISTE"
   except Exception as e:
       return f'error al abrir el pdf :{str(e)}'
#**************************************FUNCION PARA EXTRAER TEXTOS PDFs***********************************************************************************************


