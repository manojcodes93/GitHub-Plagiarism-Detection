"""Code embeddings generation."""

import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for code and commit messages."""

    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        """Initialize with sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def _chunk_code(self, code, chunk_size=100):
        """
        Split code into chunks by lines.
        
        Args:
            code: Source code string
            chunk_size: Number of lines per chunk
            
        Returns:
            List of code chunks
        """
        lines = code.split('\n')
        chunks = []
        for i in range(0, len(lines), chunk_size):
            chunk = '\n'.join(lines[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks if chunks else [code]

    def _generate_embeddings(self, texts):
        """
        Generate embeddings for list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            numpy array of embeddings
        """
        if not texts:
            return np.array([])

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return np.array([])

    def embed_code_files(self, files):
        """
        Generate embeddings for source files.
        
        Args:
            files: Dict of {filename: content}
            
        Returns:
            Dict of {filename: embedding_vector}
        """
        embeddings = {}

        try:
            for filename, content in files.items():
                chunks = self._chunk_code(content)
                if chunks:
                    chunk_embeddings = self._generate_embeddings(chunks)
                    if len(chunk_embeddings) > 0:
                        # Average embeddings across chunks
                        file_embedding = np.mean(chunk_embeddings, axis=0)
                        embeddings[filename] = file_embedding
                    else:
                        logger.warning(f"Failed to embed {filename}")

            logger.info(f"Generated embeddings for {len(embeddings)} files")
            return embeddings

        except Exception as e:
            logger.error(f"File embedding failed: {e}")
            return {}

    def embed_commit_diffs(self, commits):
        """
        Generate embeddings for commit diffs.
        
        Args:
            commits: List of commit dicts with 'diff' field
            
        Returns:
            List of embedding vectors
        """
        diffs = []

        try:
            for commit in commits:
                if commit.get('diff'):
                    diffs.append(commit['diff'][:1000])  # Limit diff size

            if diffs:
                embeddings = self._generate_embeddings(diffs)
                logger.info(f"Generated embeddings for {len(embeddings)} commits")
                return embeddings.tolist() if len(embeddings) > 0 else []
            else:
                logger.warning("No diffs to embed")
                return []

        except Exception as e:
            logger.error(f"Commit embedding failed: {e}")
            return []
