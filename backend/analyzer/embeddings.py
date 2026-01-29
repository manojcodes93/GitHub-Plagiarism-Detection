from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Union

class EmbeddingGenerator:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def get_model_info(self):
        ## Getting model information.
        return self.model_name
    
    def _chunk_code(self, code: str, max_lines: int = 40) -> List[str]:
        """
        Split code into chunks of N lines to capture partial plagiarism.
        """
        lines = code.split("\n")
        chunks = []

        for i in range(0, len(lines), max_lines):
            chunk = "\n".join(lines[i:i + max_lines]).strip()
            if chunk:
                chunks.append(chunk)
        
        return chunks

    def _convert_to_list(self, texts: Union[str, List[str]]) -> List[str]:
        """
        Normalising the input format
        single str -> List
        List stays as a list
        """
        if isinstance(texts, str):
            return [texts]
        return texts
    
    def _generate_embeddings(self, texts : List[str]) -> np.ndarray:
        texts = self._convert_to_list(texts)
        ## Generating embeddings using Transformer model
        return self.model.encode(
            texts, 
            convert_to_numpy = True, 
            show_progress_bar = False, 
            batch_size=16
        )
    
    
    def embed_code_files(self, files: Dict[str, str]) -> Dict[str, np.ndarray]:
        ## Generate aggregated embeddings for code files using chunking.
        embeddings = {}

        for path, content in files.items():
            # Skip empty files
            if not content or not content.strip():
                continue
            
            chunks = self._chunk_code(content)

            if not chunks:
                continue

            chunk_embeddings = self._generate_embeddings(chunks)

            # Aggregate chunk embeddings (mean pooling)
            file_embedding = np.mean(chunk_embeddings, axis=0)
            embeddings[path] = file_embedding
        
        return embeddings
    
    def embed_commit_diffs(self, diffs: List[str]) -> np.ndarray:
        ## Generating embeddings for commit diff
        processed_diffs = []
        
        for diff in diffs:
            lines = diff.split("\n")
            ## Keeping only added and removed lines
            relevant_lines = []
            for line in lines:
                if line.startswith("+") or line.startswith("-"):
                    relevant_lines.append(line)
            
            trimmed_diff = "\n".join(relevant_lines[:100])
            processed_diffs.append(trimmed_diff)

        return self._generate_embeddings(processed_diffs)