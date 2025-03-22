import nltk
from nltk import pos_tag
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class DocumentRetriever:
    """
    A class responsible for retrieving the most relevant documents based on a prompt.
    It supports both FAISS-based vector search and a hybrid approach combining vector and lexical searches.
    """

    def __init__(self, logger=None, database_manager=None, text_vectorizer=None, use_hybrid_search=True, max_keywords=10):
        self.logger = logger
        self.database_manager = database_manager
        self.text_vectorizer = text_vectorizer
        self.use_hybrid_search = use_hybrid_search
        if(use_hybrid_search): 
            self.logger.info("Using hybrid search for document retrieving.")
            self._initialize_nltk_resources()
        self.max_keywords = max_keywords


    def _initialize_nltk_resources(self):
        """
        Initialize NLTK resources such as stopwords and POS tagging.
        This method checks if the resources are already downloaded to avoid redundant downloads.
        """
        try:
            # Check if required resources are already downloaded
            nltk.data.find('corpora/stopwords')
            nltk.data.find('tokenizers/punkt_tab')
            nltk.data.find('taggers/averaged_perceptron_tagger_eng')
        except LookupError:
            # If resources are not found, download them
            self.logger.info("Downloading necessary NLTK resources...")
            nltk.download('stopwords')
            nltk.download('punkt_tab')
            nltk.download('averaged_perceptron_tagger_eng')

        self.stop_words = set(stopwords.words('english')).union(set(stopwords.words('french')))


    def search_in_index(self, prompt_vector, top_n):
        """
        Search for the most similar documents to the given prompt vector by querying the FAISS index.

        Args:
            prompt_vector (np.ndarray): The vector representation of the query.
            top_n (int): The number of top similar documents to return.

        Returns:
            list: A list of the most similar documents' metadata (e.g., ID and text).
        """
        try:
            self.logger.info("Searching for the most similar documents in FAISS.")
            
            # Retrieve the top_n nearest neighbors from the FAISS index
            results = self.database_manager.search_faiss(prompt_vector, top_k=top_n)
            
            # Extract chunk IDs from the search results
            chunk_ids = [result[0] for result in results]

            if not chunk_ids:
                self.logger.warning("No similar documents found in FAISS.")
                return []

            # Fetch chunks using the chunk IDs (fetch_chunks_by_ids now returns a dictionary)
            chunks_map = self.database_manager.fetch_chunks_by_ids(chunk_ids)

            if len(chunks_map) < top_n:
                self.logger.warning(f"Requested {top_n} chunks, but only {len(chunks_map)} chunks were found in the database.")

            self.logger.info(f"Initial search retrieved {len(chunks_map)} document IDs: {list(chunks_map.keys())}.")
            
            # Return the chunks as a list of dictionaries with ID and text
            return [{"id": chunk_id, "text": chunk_text} for chunk_id, chunk_text in chunks_map.items()]
        except Exception as e:
            self.logger.error(f"Error during search: {e}")
            return []


    def extract_keywords(self, prompt):
        """
        Extract significant keywords from a given prompt by focusing on the least frequent words.
        
        Args:
            prompt (str): The input text prompt.

        Returns:
            list: A list of unique keywords sorted by ascending frequency.
        """
        try:
            # Tokenize the prompt
            words = word_tokenize(prompt.lower())
            
            # Filter out stopwords and short words (length <= 2)
            filtered_words = [word for word in words if word not in self.stop_words and len(word) > 2]
            
            # POS tagging to filter out non-significant words (e.g., focus on nouns)
            pos_tags = pos_tag(filtered_words)
            keywords = [word for word, tag in pos_tags if tag in {'NN', 'NNS', 'NNP', 'NNPS'}]

            # Count word frequencies in the prompt
            word_freq = nltk.FreqDist(filtered_words)

            # Remove duplicates while preserving order
            unique_keywords = []
            seen = set()
            for word in keywords:
                if word not in seen:
                    unique_keywords.append(word)
                    seen.add(word)

            # Sort unique keywords by ascending frequency (least frequent first)
            sorted_keywords = sorted(unique_keywords, key=lambda word: word_freq[word])
            return sorted_keywords[:self.max_keywords]

        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []


    def hybrid_search(self, prompt, prompt_vector, top_n):
        """
        Perform a hybrid search combining vector and lexical search results.

        Args:
            prompt (str): The textual query to search for.
            top_n (int): The number of top results to retrieve.

        Returns:
            list: A list of the most relevant documents' metadata (ID, text, and score).
        """
        self.logger.info("Performing hybrid search.")

        # Extract keywords from the prompt
        keywords = self.extract_keywords(prompt)
        self.logger.debug(f"Extracted keywords for SQLite search.")

        # Search FAISS results and SQLite results
        faiss_results = self.database_manager.search_faiss(prompt_vector, top_k=top_n)
        sqlite_results = self.database_manager.search_sqlite(keywords, top_k=top_n)

        # Log the found IDs
        self.logger.info(f"Found {len(faiss_results)} results in FAISS for the query vector.")
        faiss_ids = [chunk_id for chunk_id, _ in faiss_results]
        self.logger.info(f"FAISS returned document IDs: {faiss_ids}")

        self.logger.info(f"Found {len(sqlite_results)} results in SQLite for keywords '{keywords}'.")
        sqlite_ids = [result["id"] for result in sqlite_results]
        self.logger.info(f"SQLite returned document IDs: {sqlite_ids}")

        faiss_chunk_ids = [chunk_id for chunk_id, _ in faiss_results]
        chunks_map = self.database_manager.fetch_chunks_by_ids(faiss_chunk_ids)

        # Use a dictionary to store the results and avoid duplicates by chunk_id
        combined_results = {}

        # Add FAISS results with their distances as scores
        for chunk_id, distance in faiss_results:
            chunk_text = chunks_map.get(chunk_id, "")
            combined_results[chunk_id] = {
                "id": chunk_id,
                "text": chunk_text,
                "score": 1 / (1 + distance)  # Using FAISS score
            }

        # Add SQLite results, ensuring no duplicates by chunk_id
        for result in sqlite_results:
            chunk_id = result["id"]
            if chunk_id not in combined_results:
                combined_results[chunk_id] = {
                    "id": chunk_id,
                    "text": result["text"],
                    "score": 0.5  # Lower weight for lexical matches
                }
            else:
                # If document already exists, update its score to keep the higher one
                combined_results[chunk_id]["score"] = max(combined_results[chunk_id]["score"], 0.5)

        # Convert the dictionary back to a sorted list based on scores
        sorted_results = sorted(combined_results.values(), key=lambda x: x["score"], reverse=True)

        self.logger.info("Hybrid search retrieved %d unique results.", len(sorted_results))
        return sorted_results[:top_n]


    def rerank_documents(self, documents, prompt_vector, top_n):
        """
        Rerank the retrieved documents based on similarity to the prompt vector.

        Args:
            documents (list): The list of documents retrieved from the index.
            prompt_vector (np.ndarray): The vector representation of the query.
            top_n (int): The number of top documents to return after reranking.

        Returns:
            list: The top_n most relevant documents after reranking.
        """
        try:
            self.logger.info("Reranking documents based on similarity to the prompt vector.")

            # Compute similarity scores for each document
            scored_documents = [
                {
                    "id": doc["id"],
                    "text": doc["text"],
                    "score": self.text_vectorizer.compute_similarity_from_vector(
                        prompt_vector,
                        self.text_vectorizer.vectorize_text(doc["text"])
                    ),
                }
                for doc in documents
            ]
            
            # Sort the documents by their similarity score in descending order
            scored_documents.sort(key=lambda x: x["score"], reverse=True)

            # Extract the top_n documents' IDs and log the reranking result
            reranked_ids = [doc["id"] for doc in scored_documents[:top_n]]
            self.logger.info(f"Reranking completed. Top {top_n} document IDs: {reranked_ids}.")
            
            # Return the top_n documents' texts, but limit to the available number of documents
            return [doc["text"] for doc in scored_documents[:min(top_n, len(scored_documents))]]
        except Exception as e:
            self.logger.error(f"Error during reranking: {e}")
            return []


    def retrieve_documents(self, prompt, top_n, expansion_factor=3):
        """
        Retrieve the most relevant documents based on a textual prompt.

        Args:
            prompt (str): The textual query to search for.
            top_n (int): The number of most relevant documents to retrieve.
            expansion_factor (int): The factor by which to expand the search scope.

        Returns:
            list: A list of the most relevant documents' text.
        """
        self.logger.info("Retrieving documents for prompt: %s", prompt)

        prompt_vector = self.text_vectorizer.vectorize_text(prompt)

        if self.use_hybrid_search:
            results = self.hybrid_search(prompt, prompt_vector, top_n * expansion_factor)
        else:
            results = self.search_in_index(prompt_vector, top_n * expansion_factor)
        
        return self.rerank_documents(results, prompt_vector, top_n)
