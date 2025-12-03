import numpy as np
from sentence_transformers import SentenceTransformer

class TextVectorizer:
    """
    A class responsible for converting text into vector representations using a pre-trained SentenceTransformer model.
    """

    def __init__(self, logger=None, model_path=None):
        self.logger = logger
        
        if model_path is None:
            raise ValueError("model_path must be provided. Please configure 'vectorizer_model_path' in config.yaml")

        self.logger.info(f"Loading pre-trained SentenceTransformer model from {model_path}")
        try:
            self.model = SentenceTransformer(model_path)
        except Exception as e:
            self.logger.error(f"Error loading SentenceTransformer model: {str(e)}")
            raise


    def compute_similarity_from_vector(self, vector1, vector2):
        """
        Compute the similarity between two vectors using cosine similarity.

        Args:
            vector1 (np.ndarray): The first vector.
            vector2 (np.ndarray): The second vector.

        Returns:
            float: The cosine similarity between the two vectors.
        """
        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        similarity = dot_product / (norm1 * norm2)
        return similarity


    def vectorize_text(self, text):
        """
        Convert the input text into a vector representation using a pre-trained model.

        Args:
            text (str): The text to be vectorized.

        Returns:
            numpy.ndarray: The vector representation of the input text.
        """
        self.logger.info("Vectorizing text of length %d", len(text))
        try:
            return self.model.encode(text)
        except Exception as e:
            self.logger.error(f"Error during vectorization: {str(e)}")
            raise


    def vectorize_chunks_with_context(self, chunks, window=1):
        """
        Vectorize chunks with context using similarity-based dynamic weighting.

        Args:
            chunks (list): List of text chunks.
            window (int): Number of neighboring chunks to include on each side.

        Returns:
            list: List of context-enhanced vectors for each chunk.
        """
        # Step 1: Concatenate neighbors and vectorize each chunk
        concatenated_vectors = []
        for i in range(len(chunks)):
            start = max(0, i - window)
            end = min(len(chunks), i + window + 1)
            combined_chunk = " ".join(chunks[start:end])
            vector = self.vectorize_text(combined_chunk)
            concatenated_vectors.append(vector)

        # Step 2: Apply dynamic weighting based on similarity
        enhanced_vectors = []
        for i in range(len(concatenated_vectors)):
            central_vector = concatenated_vectors[i]
            
            left_context = concatenated_vectors[max(0, i - 1)]
            right_context = concatenated_vectors[min(len(concatenated_vectors) - 1, i + 1)]
            
            left_similarity = self.compute_similarity_from_vector(central_vector, left_context)
            right_similarity = self.compute_similarity_from_vector(central_vector, right_context)
            
            total_similarity = left_similarity + right_similarity + 1
            central_weight = 1 / total_similarity
            left_weight = left_similarity / total_similarity
            right_weight = right_similarity / total_similarity

            enhanced_vector = (
                central_weight * central_vector + 
                left_weight * left_context + 
                right_weight * right_context
            )
            enhanced_vectors.append(enhanced_vector)

        return enhanced_vectors
