import os
import faiss
import sqlite3
import numpy as np

class DatabaseManager:
    """
    Singleton class for managing interactions with SQLite and FAISS databases.
    Provides initialization, CRUD operations, and search functionalities.
    """
    _instance = None

    def __new__(cls, logger=None, sqlite_db_path=None, faiss_db_path=None):
        """
        Create or return the singleton instance of DatabaseManager.

        Args:
            sqlite_db_path (str, optional): Path to the SQLite database file.
            faiss_db_path (str, optional): Path to the FAISS index file.

        Returns:
            DatabaseManager: The singleton instance of the DatabaseManager class.
        """
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.logger = logger
            cls._instance.sqlite_db_path = None
            cls._instance.faiss_db_path = None
            cls._instance.index = None

        # Initialize paths if provided
        if sqlite_db_path or faiss_db_path:
            cls._instance._initialize(sqlite_db_path, faiss_db_path)
        return cls._instance


    def _initialize(self, sqlite_db_path, faiss_db_path):
        """
        Initialize the DatabaseManager with paths to the databases.

        Args:
            sqlite_db_path (str): Path to the SQLite database file.
            faiss_db_path (str): Path to the FAISS index file.
        """
        if not sqlite_db_path or not faiss_db_path:
            raise ValueError("Both SQLite and FAISS database paths must be provided for initialization.")

        if not self.sqlite_db_path or not self.faiss_db_path:
            self.sqlite_db_path = sqlite_db_path
            self.faiss_db_path = faiss_db_path
            self._initialize_sqlite()
            self._initialize_faiss()
        else:
            self.logger.info("DatabaseManager is already initialized.")


    def _check_initialized(self):
        """
        Ensure the DatabaseManager has been initialized.

        Raises:
            ValueError: If the manager is not properly initialized.
        """
        if not self.sqlite_db_path or not self.faiss_db_path:
            raise ValueError("DatabaseManager is not initialized. Please provide paths to initialize it.")


    def _initialize_sqlite(self):
        """
        Initialize the SQLite database, ensuring necessary tables exist.
        """
        self._check_initialized()
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()

            # Create the documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL
                )
            ''')
            self.logger.info("Ensured 'documents' table exists in SQLite database.")

            # Create the chunks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    chunk_text TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            ''')
            self.logger.info("Ensured 'chunks' table exists in SQLite database.")

            conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error initializing the SQLite database: {e}")
        finally:
            conn.close()


    def _initialize_faiss(self):
        """
        Initialize the FAISS index, creating or loading it as needed.
        """
        self._check_initialized()
        try:
            if os.path.exists(self.faiss_db_path):
                # Load existing FAISS index
                self.index = faiss.read_index(self.faiss_db_path)
                self.logger.info("Loaded FAISS index.")
            else:
                # Create a new FAISS index
                self.index = faiss.IndexFlatL2(384)  # Assuming a vector dimension of 384
                self.index = faiss.IndexIDMap(self.index)
                faiss.write_index(self.index, self.faiss_db_path)
                self.logger.info("Created a new FAISS index.")
        except Exception as e:
            self.logger.error(f"Error initializing FAISS index: {e}")

    
    def insert_document(self, title):
        """
        Insert a document's title into the documents table.

        Args:
            title (str): The title of the document.

        Returns:
            int: The ID of the inserted document.
        """
        self._check_initialized()
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO documents (title) VALUES (?)', (title,))
            doc_id = cursor.lastrowid
            self.logger.info(f"Inserted document with ID {doc_id}.")
            conn.commit()
            return doc_id
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting the document: {e}")
            return None
        finally:
            conn.close()

    
    def insert_chunk(self, chunk_text, document_id):
        """
        Insert a chunk of text into the chunks table.

        Args:
            chunk_text (str): The chunk text to insert.
            document_id (int): The ID of the document that this chunk belongs to.

        Returns:
            int: The ID of the inserted chunk.
        """
        self._check_initialized()
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO chunks (document_id, chunk_text) VALUES (?, ?)', (document_id, chunk_text))
            chunk_id = cursor.lastrowid
            self.logger.info(f"Inserted chunk with ID {chunk_id}.")
            conn.commit()
            return chunk_id
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting the chunk: {e}")
            return None
        finally:
            conn.close()

    
    def add_vector_to_faiss(self, chunk_id, vector):
        """
        Add a vector to the FAISS index with its corresponding chunk ID.

        Args:
            chunk_id (int): The ID of the chunk.
            vector (numpy.ndarray): The vector to add.
        """
        self._check_initialized()
        try:
            self.index.add_with_ids(np.array([vector]), np.array([chunk_id]))
            self.save_faiss_index()
            self.logger.info(f"Vector added for chunk ID {chunk_id} to FAISS index.")
        except Exception as e:
            self.logger.error(f"Error adding vector for chunk ID {chunk_id} to FAISS index: {e}")


    def search_sqlite(self, keywords, top_k=5):
        """
        Search for chunks in the SQLite database containing specific keywords.

        Args:
            keywords (list): The list of keywords to search for.
            top_k (int): The number of top matches to return.

        Returns:
            list: A list of dictionaries containing 'id' and 'chunk_text'.
        """
        self._check_initialized()
        results = []
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()

            for keyword in keywords:
                query = """
                    SELECT id, chunk_text
                    FROM chunks
                    WHERE chunk_text LIKE ?
                    LIMIT ?
                """
                cursor.execute(query, (f'%{keyword}%', top_k))
                rows = cursor.fetchall()
                results.extend([{"id": row[0], "text": row[1]} for row in rows])

            # Removing duplicates and keeping unique results
            unique_results = {result['id']: result for result in results}.values()

            return list(unique_results)
        except sqlite3.Error as e:
            self.logger.error(f"Error during SQLite search: {e}")
            return []
        finally:
            conn.close()


    def search_faiss(self, query_vector, top_k=5):
        """
        Search for the top_k nearest neighbors of a query vector in the FAISS index.

        Args:
            query_vector (numpy.ndarray): The query vector.
            top_k (int): The number of nearest neighbors to retrieve.

        Returns:
            list: A list of tuples (chunk_id, distance).
        """
        self._check_initialized()
        try:
            distances, indices = self.index.search(np.array([query_vector]), top_k)
            results = [(int(idx), float(dist)) for idx, dist in zip(indices[0], distances[0]) if idx != -1]
            return results
        except Exception as e:
            self.logger.error(f"Error during FAISS search: {e}")
            return []


    def fetch_chunks_by_ids(self, chunk_ids):
        """
        Fetch chunks from SQLite based on their IDs.

        Args:
            chunk_ids (list): A list of chunk IDs.

        Returns:
            dict: A dictionary mapping chunk IDs to chunk texts.
        """
        if not chunk_ids:
            self.logger.warning("Empty chunk IDs provided.")
            return {}

        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()

            unique_ids = list(set(chunk_ids))
            placeholders = ','.join('?' for _ in unique_ids)
            query = f"SELECT id, chunk_text FROM chunks WHERE id IN ({placeholders})"
            cursor.execute(query, unique_ids)
            rows = cursor.fetchall()

            chunks_map = {row[0]: row[1] for row in rows}

            self.logger.debug(f"Retrieved chunks for IDs: {list(chunks_map.keys())}")

            return chunks_map
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching chunks: {e}")
            return {}
        finally:
            conn.close()


    def save_faiss_index(self):
        """
        Save the FAISS index to the file system.
        """
        self._check_initialized()
        try:
            faiss.write_index(self.index, self.faiss_db_path)
            self.logger.info(f"FAISS index saved to {self.faiss_db_path}.")
        except Exception as e:
            self.logger.error(f"Error saving FAISS index: {e}")

    
    def clean_database(self):
        """
        Perform a full cleanup by removing all data from both the SQLite database and the FAISS index.
        """
        self._check_initialized()
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chunks')
            cursor.execute('DELETE FROM documents')
            self.logger.info("Both SQLite tables have been completely cleared.")
            conn.commit()
            self.index.reset()
            self.save_faiss_index()
            self.logger.info("FAISS index has been completely cleared.")
        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning the SQLite database: {e}")
        except Exception as e:
            self.logger.error(f"Error cleaning the FAISS index: {e}")
        finally:
            conn.close()
