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
    
    def token_similarity(self, code1: str, code2: str) -> float:
        """
        Compute Jaccard similarity between token sets.
        """
        if not code1 or not code2:
            return 0.0
        
        tokens1 = set(code1.split())
        tokens2 = set(code2.split())
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    @staticmethod
    def compare_files(
        repo1_embeddings: Dict[str, np.ndarray],
        repo2_embeddings: Dict[str, np.ndarray],
        repo1_code: Dict[str, str],
        repo2_code: Dict[str, str],
        threshold: float = 0.75
    ) -> List[Dict]:
        ## Comparing the files across two repositories
        similar_files = []
        analyzer = SimilarityAnalyzer()

        for file1, emb1 in repo1_embeddings.items():
            for file2, emb2 in repo2_embeddings.items():
                code1 = repo1_code.get(file1, "")
                code2 = repo2_code.get(file2, "")

                embed_sim = analyzer.cosine_similarity(emb1, emb2)
                token_sim = analyzer.token_similarity(code1, code2)

                # Weighted plagiarism score
                plagiarism_score = (0.6 * token_sim) + (0.4 * embed_sim)

                if plagiarism_score >= threshold:
                    similar_files.append({
                        "file1": file1,
                        "file2": file2,
                        "embedding_similarity": embed_sim,
                        "token_similarity": token_sim,
                        "similarity": plagiarism_score,
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
        
        return float(np.median(max_similarities))