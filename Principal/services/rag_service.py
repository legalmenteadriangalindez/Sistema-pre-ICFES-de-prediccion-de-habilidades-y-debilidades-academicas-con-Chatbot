from Principal.IA.RAG_system import RAGSystem

import time 


star= time.time()
rag_system= RAGSystem(
    data_path="C:\\Users\\User\\Downloads\\ProyectoDeGrado\\data",
    chroma_path="C:\\Users\\User\\Downloads\\ProyectoDeGrado\\Chroma_DB",
    chunk_size=400,
    chunk_overlap=50,
    # embedding_model="nomic-embed-text"
    # embedding_model="all-MiniLM-L6-v2"
    embedding_model="mxbai-embed-large"

    )

rag_system.initialize()

end = time.time()

print(f"inicilaizacion= {end-star}")