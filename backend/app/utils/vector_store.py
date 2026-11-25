import os
from functools import lru_cache
from pathlib import Path

from app.config.settings import settings
logger = settings.get_logger()

from langchain_community.document_loaders import (
    TextLoader
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)



from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()
hf_token = os.getenv("hf_token")

if hf_token:
    os.environ["HF_TOKEN"] = hf_token

from langchain_chroma import (
    Chroma
)

# --------------------------------------------------
# Constants
# --------------------------------------------------

<<<<<<< HEAD
VECTOR_DB_PATH = settings.vector_db_path

DRUG_DATA_FILE = (
    #"../data/drugs.txt"
    settings.data_dir
=======
VECTOR_DB_PATH = "vector_db"

DRUG_DATA_FILE = (
    "../data/drugs.txt"
>>>>>>> afa54285879c9934f132cfce60228967bd595849
)

@lru_cache(maxsize=1)
def get_embeddings():
    """Load the embedding model once per process and reuse it."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# --------------------------------------------------
# Load/Create Vector Store
# --------------------------------------------------

def load_vectorstore():

    try:

        logger.info(
            "Initializing Vector Store"
        )

        

        embeddings = get_embeddings()

        # ------------------------------------------
        # Load Existing Vector DB
        # ------------------------------------------

        if os.path.exists(
            VECTOR_DB_PATH
        ):

            logger.info(
                f"Loading existing vector database "
                f"from {VECTOR_DB_PATH}"
            )

            vectordb = Chroma(
                persist_directory=VECTOR_DB_PATH,
                embedding_function=embeddings
            )

            logger.success(
                "Existing vector database loaded"
            )

            return vectordb

        # ------------------------------------------
        # Create New Vector DB
        # ------------------------------------------

        logger.info(
            "Vector database not found."
        )

        logger.info(
            f"Loading file: "
            f"{DRUG_DATA_FILE}"
        )

        loader = TextLoader(
            DRUG_DATA_FILE,
            encoding="utf-8"
        )

        documents = loader.load()

        logger.info(
            f"Loaded {len(documents)} documents"
        )

        splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
        )

        chunks = splitter.split_documents(
            documents
        )

        logger.info(
            f"Created {len(chunks)} chunks"
        )

        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=VECTOR_DB_PATH
        )

        logger.success(
            "Vector database created successfully"
        )

        return vectordb

    except Exception as ex:

        logger.exception(
            "Error creating/loading vector store"
        )

        raise ex


# --------------------------------------------------
# Retriever Factory
# --------------------------------------------------

def get_retriever():

    try:

        logger.info(
            "Creating Retriever"
        )

        vectordb = load_vectorstore()

        retriever = (
            vectordb.as_retriever(
                search_kwargs={
                    "k": 3
                }
            )
        )

        logger.success(
            "Retriever created successfully"
        )

        return retriever

    except Exception as ex:

        logger.exception(
            "Failed to create retriever"
        )

        raise ex