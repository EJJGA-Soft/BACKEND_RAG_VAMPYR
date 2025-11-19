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
# Defaults adaptados al PDF de tu juego
PERSIST_DIR = os.environ.get("PERSIST_DIR", "./data/chroma_vampyr_db")
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

    # Ajustes de split para respetar secciones del PDF del juego (A) PERSONAJES, C) MECÁNICAS, etc.)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
        # Priorizar saltos de sección y viñetas para mantener la coherencia de cada bloque
        separators=["\n\n", "\n", "A)", "B)", "C)", "D)", "E)", "F)", "G)", "•", "- ", ". ", " ", ""]
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
            # Normalizar espacios y recortar bloques excesivamente largos
            content = d.page_content.strip()
            parts.append(f"(p.{page}) {content}")
        return "\n\n".join(parts)[:8000]  # Permitimos un contexto mayor para respuestas estructuradas

    retrieve = RunnableMap({
        "context": lambda x: format_context(retriever.invoke(x["question"])),
        "question": lambda x: x["question"]
    })

    prompt_template = """Usa SÓLO el siguiente contexto extraído del PDF del juego Vampyr: Rise Of The Night Walkers para responder la pregunta. 

**Contexto del juego:**
{context}

**Pregunta del usuario:** {question}

**Instrucciones para tu respuesta:**
1. **Tono amigable y conversacional**: Habla de manera natural, como si estuvieras ayudando a un amigo con el juego.
2. **Respuestas claras y directas**: Ve al grano, sin rodeos innecesarios.
3. **Estructura la información**:
   - Para personajes: nombre, características principales, habilidades
   - Para enemigos: descripción, ubicación, cómo derrotarlos
   - Para mecánicas: explicación simple con ejemplos
   - Para historia: cuenta de forma narrativa e interesante
4. **Si NO tienes la información**, responde: "Hmm, no encuentro información específica sobre eso en mi base de datos del juego. ¿Quieres preguntarme sobre los personajes, enemigos, objetos o la historia del castillo?"

**Ejemplos de buen tono:**
- "El Vampyr es el protagonista del juego. Es un vampiro antiguo que..."
- "Para derrotar a este enemigo necesitarás..."
- "En el nivel 2 encontrarás..."

Responde ahora:"""

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un asistente experto y amigable del videojuego "Vampyr: Rise Of The Night Walkers". 

Tu personalidad:
- Entusiasta del juego y siempre dispuesto a ayudar
- Conversacional y cercano, como un amigo gamer
- Conocedor profundo del lore y mecánicas del juego

Reglas IMPORTANTES:
1. SOLO usa información del contexto provisto (nunca inventes datos del juego)
2. Si no sabes algo, admítelo y sugiere temas sobre los que SÍ puedes ayudar
3. Mantén respuestas concisas pero completas (2-4 párrafos máximo)
4. Usa formato Markdown para estructurar (**, ##, listas, etc.)
5. Siempre responde en español y con entusiasmo por el juego
6. NO uses emojis en tus respuestas

Recuerda: Tu objetivo es hacer que el jugador se emocione por jugar y entienda mejor el mundo de Vampyr."""),
        ("user", prompt_template),
    ])

    llm = ChatGoogleGenerativeAI(model=GEN_MODEL, temperature=0.2)
    parser = StrOutputParser()

    return retrieve | chat_prompt | llm | parser

CHAIN = build_chain()
