

from langchain_classic.retrievers.multi_query import MultiQueryRetriever

from .retrievers import get_base_retriever

from langchain_core.output_parsers import StrOutputParser


#===========================================================================================================
def get_mmr_multi_retriever(vectorstore,llm,prompt):
    base_retriever= get_base_retriever(vectorstore)
    
    llm_chain = prompt | llm | StrOutputParser()

    return MultiQueryRetriever(
    retriever=base_retriever,
    llm_chain=llm_chain,
    
) 

#***********************************************************************************************************


# vectorstore = Chroma(
#     embedding_function=get_embedding(),
#     persist_directory="C:\\Users\\User\\Downloads\\ProyectoDeGrado\\media\\Chroma_DB"
# )

# base_retriever = vectorstore.as_retriever(
#     search_type="similarity",
#     search_kwargs={"k": 2}
# )

# retriever = MultiQueryRetriever.from_llm(retriever=base_retriever,llm=chat_bot)

# consulta = "¿cual es el inmueble que forma parte del contrato de María Jiménez Campos?"

# resultados= retriever.invoke(consulta)

# print("retrievers con llm ==========: ")
# for i, doc in enumerate(resultados, start=1):
#     snipped = doc.page_content
#     print(snipped)