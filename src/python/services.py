import os
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config_loader import ConfigLoader
from custom_logger import CustomLogger
from database_manager import DatabaseManager
from document_indexer import DocumentIndexer
from document_retriever import DocumentRetriever
from response_generator import ResponseGenerator
from text_extractor import TextExtractor
from text_vectorizer import TextVectorizer

class Services:
    """
    Singleton class for initializing and configuring essential components for the application.
    """
    _instance = None

    def __new__(cls):
        """
        Create or return the singleton instance of Services.

        Returns:
            Services: The singleton instance of the Services class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initializes various components of the application.
        """
        self.logger = CustomLogger.get_logger(__name__)

        self.logger.info("Initializing config loader.")
        config_loader = ConfigLoader()
        self.config = config_loader.load_config()

        self.logger.info("Initializing text extractor.")
        self.text_extractor = TextExtractor(
            logger=self.logger
        )

        self.logger.info("Initializing text vectorizer.")
        self.text_vectorizer = TextVectorizer(
            logger=self.logger,
            model_path=self.config['settings']['vectorizer_model_path']
        )

        self.logger.info("Initializing database manager.")
        self.database_manager = DatabaseManager(
            logger=self.logger,
            sqlite_db_path=self.config['sqlite3']['path'],
            faiss_db_path=self.config['faiss']['path']
        )

        self.logger.info("Initializing document indexer.")
        self.document_indexer = DocumentIndexer(
            logger=self.logger,
            database_manager=self.database_manager,
            text_extractor=self.text_extractor,
            text_vectorizer=self.text_vectorizer
        )

        self.logger.info("Initializing document retriever.")
        self.document_retriever = DocumentRetriever(
            logger=self.logger,
            database_manager=self.database_manager,
            text_vectorizer=self.text_vectorizer,
            use_hybrid_search=self.config['settings']['use_hybrid_search'],
            max_keywords=self.config['settings']['max_keywords']
        )

        self.logger.info("Initializing response generator.")
        self.response_generator = ResponseGenerator(
            logger=self.logger,
            model=self.config['settings']['model'],
            master_prompt=self.config['settings']['master_prompt'],
            document_retriever=self.document_retriever
        )

        self.logger.info("Initializing FastAPI application.")
        self.app = FastAPI()

        static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/static"))
        html_templates_path = os.path.join(static_path, 'html')
        self.logger.debug(f"Mounting static files from {static_path}.")
        self.app.mount("/static", StaticFiles(directory=static_path), name="static")
        self.templates = Jinja2Templates(directory=html_templates_path)

        self.rag_enabled = False

        self.generating_response = False
        self._response_lock = asyncio.Lock()

    def get_app(self):
        """
        Returns the FastAPI application instance.
        """
        return self.app

    def get_templates(self):
        """
        Returns the Jinja2 template instance used for rendering HTML pages.
        """
        return self.templates

    def get_logger(self):
        """
        Returns the logger instance used for logging application events.
        """
        return self.logger

    def get_config(self):
        """
        Returns the configuration dictionary loaded from the configuration file.
        """
        return self.config

    def get_text_extractor(self):
        """
        Returns the text extractor instance responsible for extracting text from files or documents.
        """
        return self.text_extractor

    def get_text_vectorizer(self):
        """
        Returns the text vectorizer instance responsible for converting text into vector representations.
        """
        return self.text_vectorizer

    def get_database_manager(self):
        """
        Returns the database manager instance used to interact with the SQLite
        and FAISS databases.
        """
        return self.database_manager

    def get_document_retriever(self):
        """
        Returns the document retriever instance used for retrieving relevant documents.
        """
        return self.document_retriever

    def get_document_indexer(self):
        """
        Returns the document indexer instance responsible for indexing and
        searching documents.
        """
        return self.document_indexer

    def get_response_generator(self):
        """
        Returns the response generator instance that handles generating
        responses based on the model and prompt.
        """
        return self.response_generator

    def is_rag_enabled(self):
        """
        Returns the current state of the RAG (retrieval-augmented generation) flag.
        This flag determines whether retrieval-augmented generation is enabled or not.
        """
        return self.rag_enabled

    def set_rag_enabled(self, value: bool):
        """
        Sets the RAG (retrieval-augmented generation) flag to the specified value.
        This flag determines whether retrieval-augmented generation is enabled or not.
        
        Args:
        - value: Boolean value to enable or disable RAG.
        """
        self.rag_enabled = value
    
    async def is_generating_response(self):
        """
        Returns the current state of the response generation flag.
        This flag determines whether a response is being generated or not.
        Thread-safe using asyncio.Lock.
        """
        async with self._response_lock:
            return self.generating_response

    async def set_generating_response(self, value: bool):
        """
        Sets the current state of the generation flag to the specified value.
        This flag determines whether a response is being generated or not.
        Thread-safe using asyncio.Lock.
        
        Args:
        - value: Boolean value to set if a response is being generated or not.
        """
        async with self._response_lock:
            self.generating_response = value

    def get_response_lock(self):
        """
        Returns the asyncio.Lock used for thread-safe access to generating_response.
        
        Returns:
            asyncio.Lock: The lock object.
        """
        return self._response_lock
