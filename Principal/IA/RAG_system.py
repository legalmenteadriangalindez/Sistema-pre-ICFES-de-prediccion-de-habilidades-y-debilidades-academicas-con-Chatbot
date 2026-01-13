# ==========================================IMPORTACIONES================================================
from .processor_PDF import open_documents_by_area,clean_text
from .splitters import split_documents
from .chains import get_chain_rag
from .embeddings import get_embedding
from .vectorstore import build_vectorestore
from .retrievers import get_base_retriever
from .llm import chat_bot
from .prompts import prompt_rag,multiquery_retriver
from .retrievers_multi_query import get_mmr_multi_retriever
import time
#*******************************************IMPORTACIONES**********************************************************

class RAGSystem:

    def __init__(self,
                data_path: str,
                chroma_path: str,
                chunk_size:int,
                chunk_overlap:int,
                embedding_model: str
                ):
        
        self.data_path = data_path
        self.chroma_path =chroma_path
        self.chunk_size= chunk_size
        self.chunk_overlap= chunk_overlap
        self.embedding_model= embedding_model
        
        self.vectorstore= None
        self.retriever= None
        self.multi_retriever= None
        self.chain_rag = None
        self.initialized = False

    def initialize(self):
        star= time.time()
        # cargar documentos 
        documents =open_documents_by_area(self.data_path)
        
        # split dividir documentos
        docs_split = split_documents(
            documents,
            chunk_size= self.chunk_size,
            chunk_overlap= self.chunk_overlap,                                     
            )
        
        # embeddings
        embedding= get_embedding(self.embedding_model)

        # vectorstore
        self.vectorstore = build_vectorestore(
            persist_directory=self.chroma_path,
            embeddings=embedding,
            documents=docs_split if not self.initialized else None
        )
       
        # retriever base 
        self.retriever = get_base_retriever(self.vectorstore)
        
        # multiquery retriever
        self.multi_retriever= get_mmr_multi_retriever(
            vectorstore=self.vectorstore,
            llm=chat_bot,
            prompt=multiquery_retriver
        )

        # chain RAG
        self._build_chain_rag()

        self.initialized = True
        end = time.time()
        print(f"inicializacion =: {star-end}")

    # construccion del chain rag 
    def _build_chain_rag(self):
        star= time.time()
        if self.multi_retriever is None:
            raise RuntimeError("MultiQueryRetriever no inicializado")
        self.chain_rag= get_chain_rag(
            retriever=self.multi_retriever,
            prompt= prompt_rag,
            llm=chat_bot
        )
        end = time.time()
        print(f"build =: {end-star}")


    # consulta
    def ask(self, question: str)->str:
        star= time.time()
        if not self.initialized:
           self.initialize()
        if self.chain_rag is None:
            raise RuntimeError("el sistema RAG no se ha inicializado")
        docs = self.multi_retriever.invoke(question,run_manager=None)
        for doc in docs : 
            doc.page_content=clean_text(doc.page_content)
        for i,d in enumerate(docs[:5]):
            print(f"--- Documento {i+1} ---")
            print("Fuente:", d.metadata)
            print(d.page_content)
            print("\n")
        docs_simples = self.similarity_search(question, k=5)

        for i, d in enumerate(docs_simples):
          print(f"[SIMILARITY] Documento {i+1}")
          print(d.page_content)
        context = "\n\n".join(d.page_content for d in docs)
        print(context[:2000])
        end = time.time()
        respuesta = self.chain_rag.invoke({
            "context": context,
            "question": question
             }
             )
        print(f"ask =: {end-star}") 
        return respuesta
        
    
    # busqueda directa
    def similarity_search(self, query: str, k: int = 3):
        star= time.time()
        if self.vectorstore is None:
            raise RuntimeError("vectorstore no inicializado")
        end = time.time()
        print(f"ask =: {end-star}")
        return self.vectorstore.similarity_search(query, k=k)
        
    
    