import numpy as np
from typing import Dict, List

class SimilarityAnalyzer:
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        ## Computing cosine similarity between two vectors
        if vec1 is None or vec2 is None:
            return 0.0
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(similarity)
    
    @staticmethod
    def compare_files(
        repo1_embeddings: Dict[str, np.ndarray],
        repo2_embeddings: Dict[str, np.ndarray],
        threshold: float = 0.75
    ) -> List[Dict]:
        ## Comparing the files across two repositories
        similar_files = []
        analyzer = SimilarityAnalyzer()

        for file1, emb1 in repo1_embeddings.items():
            for file2, emb2 in repo2_embeddings.items():

                similarity = analyzer.cosine_similarity(emb1, emb2)

                if similarity >= threshold:
                    similar_files.append({
                        "file1": file1,
                        "file2": file2,
                        "similarity": similarity,
                        "status": "flagged"
                    })
        
        similar_files.sort(
            key=lambda x: x["similarity"],
            reverse=True
        )

        return similar_files
    
    @staticmethod
    def compute_repository_similarity(
        repo1_embeddings: Dict[str, np.ndarray],
        repo2_embeddings: Dict[str, np.ndarray]
    ) -> float:
        ## Computing overall repository similarity
        if not repo1_embeddings or not repo2_embeddings:
            return 0.0
        
        max_similarities = []
        analyzer = SimilarityAnalyzer()

        for emb1 in repo1_embeddings.values():
            best_match = 0.0

            for emb2 in repo2_embeddings.values():
                similarity = analyzer.cosine_similarity(emb1, emb2)
                best_match = max(best_match, similarity)
            
            max_similarities.append(best_match)
        
        return float(np.mean(max_similarities))