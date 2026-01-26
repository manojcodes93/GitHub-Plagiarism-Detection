"""
Embeddings module using Hugging Face sentence transformers.
Generates semantic embeddings for code and text fragments.
These embeddings enable semantic similarity detection beyond string matching.
"""

import numpy as np
from typing import Dict, List, Union
import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed. Using mock embeddings.")


class EmbeddingGenerator:
    """
    Generates embeddings for code using Hugging Face models.
    Uses sentence-transformers for efficiency.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Hugging Face model identifier
        """
        self.model_name = model_name
        self.model = None
        
        if HAS_TRANSFORMERS:
            try:
                logger.info(f"Loading embedding model: {model_name}")
                self.model = SentenceTransformer(model_name)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {str(e)}")
                self.model = None
        else:
            logger.warning("sentence-transformers not available")
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode text(s) into embeddings.
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Numpy array of embeddings (shape: [n, 384] for all-MiniLM-L6-v2)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model is None:
            logger.warning("Model not available, returning random embeddings")
            return np.random.randn(len(texts), 384).astype(np.float32)
        
        try:
            # Encode with mean pooling
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embeddings
        except Exception as e:
            logger.error(f"Encoding failed: {str(e)}")
            return np.random.randn(len(texts), 384).astype(np.float32)
    
    def embed_code_files(self, files: Dict[str, str]) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for multiple code files.
        
        Args:
            files: Dictionary mapping file paths to contents
            
        Returns:
            Dictionary mapping file paths to embeddings
        """
        embeddings = {}
        
        for path, content in files.items():
            try:
                # Truncate very long files to avoid memory issues
                truncated = content[:10000] if len(content) > 10000 else content
                
                # Generate embedding
                embedding = self.encode(truncated)[0]
                embeddings[path] = embedding
                
            except Exception as e:
                logger.warning(f"Failed to embed {path}: {str(e)}")
        
        logger.info(f"Generated embeddings for {len(embeddings)} files")
        return embeddings
    
    def embed_code_snippets(self, snippets: List[str]) -> np.ndarray:
        """
        Generate embeddings for code snippets.
        
        Args:
            snippets: List of code snippets
            
        Returns:
            Numpy array of embeddings
        """
        return self.encode(snippets)
    
    def embed_commit_diffs(self, diffs: List[str]) -> np.ndarray:
        """
        Generate embeddings for commit diffs.
        
        Args:
            diffs: List of unified diff strings
            
        Returns:
            Numpy array of embeddings
        """
        # Preprocess diffs: keep only added/removed lines
        processed_diffs = []
        for diff in diffs:
            lines = [line for line in diff.split("\n") if line.startswith(("+", "-"))]
            processed_diffs.append("\n".join(lines[:100]))  # Limit to first 100 lines
        
        return self.encode(processed_diffs)
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        if self.model is None:
            return {"status": "not_loaded"}
        
        return {
            "model_name": self.model_name,
            "status": "loaded",
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
        }
