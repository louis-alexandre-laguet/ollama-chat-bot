import os

class DocumentIndexer:
    """
    A class to handle indexing of documents from a specified folder.
    It extracts text from various file types, processes the text into chunks,
    vectorizes the chunks, and stores them in a database and FAISS index.
    """

    def __init__(self, logger=None, database_manager=None, text_extractor=None, text_vectorizer=None):
        self.logger = logger
        self.database_manager = database_manager
        self.text_extractor = text_extractor
        self.text_tectorizer = text_vectorizer


    def index_documents(self, folder_path):
        """
        Index documents from a specified folder by extracting their text and converting it to vectors.
        This function now recursively processes subdirectories as well and stores data in a database.

        Args:
            folder_path (str): Path to the folder containing documents to be indexed.

        Returns:
            None
        """
        if not os.path.isdir(folder_path):
            self.logger.error(f"Directory not found: {folder_path}")
            return

        document_count = 0

        for root, _, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)

                self.logger.info(f"Processing file: {filename}")

                text = self.extract_text_from_file(file_path, filename)
                if text is None:
                    continue

                doc_id = self.database_manager.insert_document(filename)
                if doc_id is None:
                    continue

                chunks = self.chunk_text(text)
                vectors = self.text_tectorizer.vectorize_chunks_with_context(chunks, window=1)

                for chunk, vector in zip(chunks, vectors):
                    try:
                        chunk_id = self.database_manager.insert_chunk(chunk, doc_id)
                        if chunk_id:
                            self.database_manager.add_vector_to_faiss(chunk_id, vector)
                            document_count += 1
                    except Exception as e:
                        self.logger.error(f"Error adding chunk or vector to database/FAISS: {str(e)}")

        self.logger.info(f"Indexed {document_count} documents from {folder_path} into database")


    def extract_text_from_file(self, file_path, filename):
        """
        Extract text from a file based on its extension.

        Args:
            file_path (str): The path to the file.
            filename (str): The name of the file.

        Returns:
            str: The extracted text from the file.
            None: If the file type is unsupported or extraction fails.
        """
        try:
            if filename.endswith('.docx'):
                return self.text_extractor.extract_text_from_docx(file_path)
            elif filename.endswith('.pptx'):
                return self.text_extractor.extract_text_from_pptx(file_path)
            elif filename.endswith('.pdf'):
                return self.text_extractor.extract_text_from_pdf(file_path)
            elif filename.endswith('.txt'):
                return self.text_extractor.extract_text_from_txt(file_path)
            elif filename.endswith('.xlsx'):
                return self.text_extractor.extract_text_from_xlsx(file_path)
            elif filename.endswith('.csv'):
                return self.text_extractor.extract_text_from_csv(file_path)
            elif filename.endswith('.html') or filename.endswith('.htm'):
                return self.text_extractor.extract_text_from_html(file_path)
            elif filename.endswith('.md'):
                return self.text_extractor.extract_text_from_md(file_path)
            elif filename.endswith('.rtf'):
                return self.text_extractor.extract_text_from_rtf(file_path)
            elif filename.endswith('.odt'):
                return self.text_extractor.extract_text_from_odt(file_path)
            else:
                self.logger.warning(f"Unsupported file type: {filename}")
                return None
        except Exception as e:
            self.logger.error(f"Error extracting text from file {filename}: {str(e)}")
            return None


    def chunk_text(self, text, chunk_size=500, overlap=50):
        """
        Divide text into overlapping chunks of a specified size.

        Args:
            text (str): The input text to be chunked.
            chunk_size (int): The maximum number of tokens per chunk.
            overlap (int): The number of tokens overlapping between chunks.

        Returns:
            list: A list of text chunks.
        """
        assert chunk_size > overlap, "chunk_size must be greater than overlap"

        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
