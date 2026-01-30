"""Similarity analysis module."""

import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SimilarityAnalyzer:
    """Compute similarity between code embeddings."""

    def __init__(self, threshold=0.7):
        """Initialize with similarity threshold."""
        self.threshold = threshold
        logger.info(f"Initialized SimilarityAnalyzer with threshold: {threshold}")

    def cosine_similarity(self, vec1, vec2):
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        try:
            if not isinstance(vec1, np.ndarray):
                vec1 = np.array(vec1)
            if not isinstance(vec2, np.ndarray):
                vec2 = np.array(vec2)

            if len(vec1) == 0 or len(vec2) == 0:
                return 0.0

            # Compute cosine similarity
            similarity = cosine_similarity(
                vec1.reshape(1, -1),
                vec2.reshape(1, -1)
            )[0][0]

            return float(similarity)
        except Exception as e:
            logger.warning(f"Similarity computation failed: {e}")
            return 0.0

    def compare_files(self, candidate_embeddings, reference_embeddings):
        """
        Compare files between candidate and reference.
        
        Args:
            candidate_embeddings: Dict of {filename: embedding} for candidate
            reference_embeddings: Dict of {filename: embedding} for reference
            
        Returns:
            Dict of {filename: max_similarity_score}
        """
        comparisons = {}

        try:
            for candidate_file, candidate_emb in candidate_embeddings.items():
                max_similarity = 0.0

                for reference_file, reference_emb in reference_embeddings.items():
                    similarity = self.cosine_similarity(candidate_emb, reference_emb)
                    max_similarity = max(max_similarity, similarity)

                comparisons[candidate_file] = max_similarity

            logger.info(f"Compared {len(comparisons)} candidate files")
            return comparisons

        except Exception as e:
            logger.error(f"File comparison failed: {e}")
            return {}

    def compute_repository_similarity(self, file_comparisons):
        """
        Compute overall repository similarity from file-level comparisons.
        
        Args:
            file_comparisons: Dict of {filename: similarity_score}
            
        Returns:
            Overall similarity score (0-1)
        """
        try:
            if not file_comparisons:
                logger.warning("No file comparisons to aggregate")
                return 0.0

            similarities = list(file_comparisons.values())
            repo_similarity = np.mean(similarities) if similarities else 0.0

            logger.info(f"Repository similarity: {repo_similarity:.4f}")
            return float(repo_similarity)

        except Exception as e:
            logger.error(f"Repository similarity computation failed: {e}")
            return 0.0
