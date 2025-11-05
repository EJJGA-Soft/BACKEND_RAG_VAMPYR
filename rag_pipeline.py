import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableMap
from langchain.schema import Document

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
assert GOOGLE_API_KEY, "Falta GOOGLE_API_KEY en .env"

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")
GEN_MODEL = os.environ.get("GEN_MODEL", "gemini-2.5-flash")
PERSIST_DIR = os.environ.get("PERSIST_DIR", "./data/chroma_menu_db_v2")
PDF_PATH = os.environ.get("PDF_PATH", "./data/juego.pdf")
K_RETRIEVAL = int(os.environ.get("K_RETRIEVAL", "5"))

def build_or_load_vectorstore(pdf_path: str, persist_dir: str):
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    collection_name = "vampyr_knowledge"  # Nombre actualizado para Vampyr

    if os.path.isdir(persist_dir) and any(os.scandir(persist_dir)):
        # IMPORTANTE: Especificar el mismo collection_name al cargar
        return Chroma(
            persist_directory=persist_dir, 
            embedding_function=embeddings,
            collection_name=collection_name
        )

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # Chunk size mayor para capturar secciones completas con sus IDs
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Aumentado para capturar tablas completas
        chunk_overlap=200,  # Overlap mayor para mantener contexto entre secciones
        separators=["## [ID:", "\n\n", "\n", ". ", " ", ""]  # Prioriza separar por secciones ID
    )
    chunks = splitter.split_documents(documents)
    docs = [Document(page_content=c.page_content, metadata=c.metadata) for c in chunks]

    return Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name=collection_name
    )

def build_chain():
    vectorstore = build_or_load_vectorstore(PDF_PATH, PERSIST_DIR)
    retriever = vectorstore.as_retriever(search_kwargs={"k": K_RETRIEVAL})

    def format_context(docs):
        parts = []
        for d in docs:
            page = d.metadata.get("page", "?")
            parts.append(f"(p.{page}) {d.page_content}")
        return "\n\n".join(parts)[:6000]  # Aumentado para respuestas más completas

    retrieve = RunnableMap({
        "context": lambda x: format_context(retriever.invoke(x["question"])),
        "question": lambda x: x["question"]
    })

    prompt_template = """Usa SOLO el siguiente contexto para responder la pregunta sobre Vampyr: Rise of the Night Walkers.

Si encuentras información con etiquetas [ID: XXX], úsala para estructurar mejor tu respuesta.
Para preguntas sobre personajes, incluye: biografía, habilidades, clanes, y características si están disponibles.
Para mecánicas del juego, explica claramente los sistemas y estrategias.

Si no está en el contexto, responde: "Lo siento, no tengo información específica sobre eso en mi base de datos de Vampyr. ¿Puedes hacer otra pregunta sobre el juego?"

Contexto:
{context}

Pregunta: {question}

Respuesta:"""

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres Vampyr Assistant, un experto asistente sobre el juego Vampyr: Rise of the Night Walkers. 
        Respondes en español de forma clara, precisa y envolvente sobre personajes, clanes, historia, 
        mecánicas, estrategias y todo relacionado con Vampyr.
        
        Cuando des información sobre:
        - Personajes: incluye biografía, clan, habilidades y rol en la historia
        - Clanes: explica características, poderes y filosofías
        - Historia: sé detallado e inmersivo
        - Mecánicas: explica de forma clara con ejemplos prácticos
        
        Mantén un tono oscuro, misterioso y apasionado acorde a la temática vampírica."""),
        ("user", prompt_template),
    ])

    llm = ChatGoogleGenerativeAI(model=GEN_MODEL, temperature=0.2)
    parser = StrOutputParser()

    return retrieve | chat_prompt | llm | parser

CHAIN = build_chain()
