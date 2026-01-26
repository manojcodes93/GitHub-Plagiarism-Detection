"""
Similarity computation module using cosine similarity.
Compares embeddings to find similar code across repositories.
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy.spatial.distance import cosine
import logging

logger = logging.getLogger(__name__)


class SimilarityAnalyzer:
    """
    Computes similarity between embeddings using cosine similarity.
    Provides file-level, commit-level, and repository-level scoring.
    """
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        Range: [-1, 1]. Values close to 1 indicate high similarity.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        try:
            # Normalize vectors
            vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
            vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-10)
            
            # Compute cosine similarity
            similarity = np.dot(vec1_norm, vec2_norm)
            return float(similarity)
        except Exception as e:
            logger.error(f"Similarity computation failed: {str(e)}")
            return 0.0
    
    @staticmethod
    def compare_files(
        files_repo1: Dict[str, np.ndarray],
        files_repo2: Dict[str, np.ndarray],
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Compare files between two repositories.
        Returns pairs with similarity above threshold.
        
        Args:
            files_repo1: {file_path: embedding} for repo 1
            files_repo2: {file_path: embedding} for repo 2
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of similar file pairs: [
                {
                    "file1": "path",
                    "file2": "path",
                    "similarity": 0.85,
                    "status": "suspicious"
                }
            ]
        """
        similar_pairs = []
        
        for path1, emb1 in files_repo1.items():
            for path2, emb2 in files_repo2.items():
                similarity = SimilarityAnalyzer.cosine_similarity(emb1, emb2)
                
                if similarity >= threshold:
                    # Classify suspicion level
                    if similarity >= 0.95:
                        status = "critical"
                    elif similarity >= 0.85:
                        status = "high"
                    elif similarity >= 0.75:
                        status = "medium"
                    else:
                        status = "low"
                    
                    similar_pairs.append({
                        "file1": path1,
                        "file2": path2,
                        "similarity": similarity,
                        "status": status,
                    })
        
        # Sort by similarity (descending)
        similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)
        
        logger.info(f"Found {len(similar_pairs)} similar file pairs")
        return similar_pairs
    
    @staticmethod
    def compute_repository_similarity(
        embeddings_repo1: Dict[str, np.ndarray],
        embeddings_repo2: Dict[str, np.ndarray]
    ) -> float:
        """
        Compute overall similarity between two repositories.
        Uses average of maximum similarities for each file in repo1.
        
        Args:
            embeddings_repo1: {file_path: embedding} for repo 1
            embeddings_repo2: {file_path: embedding} for repo 2
            
        Returns:
            Repository-level similarity score (0-1)
        """
        if not embeddings_repo1 or not embeddings_repo2:
            return 0.0
        
        similarities = []
        
        # For each file in repo1, find max similarity in repo2
        for emb1 in embeddings_repo1.values():
            max_sim = 0.0
            for emb2 in embeddings_repo2.values():
                sim = SimilarityAnalyzer.cosine_similarity(emb1, emb2)
                max_sim = max(max_sim, sim)
            similarities.append(max_sim)
        
        # Return average of max similarities
        repo_similarity = np.mean(similarities) if similarities else 0.0
        logger.info(f"Repository similarity: {repo_similarity:.3f}")
        
        return float(repo_similarity)
    
    @staticmethod
    def compute_similarity_matrix(
        embeddings_list: List[Dict[str, np.ndarray]],
        repo_names: List[str]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Compute similarity matrix for multiple repositories.
        
        Args:
            embeddings_list: List of {file_path: embedding} dicts
            repo_names: List of repository names
            
        Returns:
            (similarity_matrix, repo_names) where matrix is NxN
        """
        n = len(embeddings_list)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i, n):
                sim = SimilarityAnalyzer.compute_repository_similarity(
                    embeddings_list[i],
                    embeddings_list[j]
                )
                matrix[i, j] = sim
                matrix[j, i] = sim  # Symmetric
        
        return matrix, repo_names
    
    @staticmethod
    def rank_suspicious_pairs(
        comparison_results: List[Dict],
        threshold: float = 0.75
    ) -> List[Dict]:
        """
        Rank repository pairs by suspicion level.
        
        Args:
            comparison_results: List of comparison results
            threshold: Minimum similarity to flag
            
        Returns:
            Sorted list of suspicious pairs
        """
        suspicious = []
        
        for result in comparison_results:
            if result.get("similarity", 0) >= threshold:
                suspicious.append(result)
        
        # Sort by similarity (descending)
        suspicious.sort(key=lambda x: x["similarity"], reverse=True)
        
        return suspicious
