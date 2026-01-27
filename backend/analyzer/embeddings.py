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

    def _prepare_text(self, text: str) -> str:
        ## Preparing the the text by avoiding memory/ token issue
        max_length = 10000
        return text[:max_length]

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
        return self.model.encode(texts, convert_to_numpy = True, show_progress_bar = False)
    
    
    def embed_code_files(self, files : Dict[str, str]) -> Dict[str, np.ndarray]:
        ## Generate embeddings for code files
        embeddings = {}

        for path, content in files.items():
            # Skip empty files
            if not content or not content.strip():
                continue
            
            prepared_text = self._prepare_text(content)
            embedding_result = self._generate_embeddings(prepared_text)
            if len(embedding_result) > 0:
                # Model returns batch embeddings: (1, embedding_dim) → extract single vector (embedding_dim,)
                embeddings[path] = embedding_result[0]
        
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
            
            trimmed_diff = self._prepare_text("\n".join(relevant_lines[:100]))
            processed_diffs.append(trimmed_diff)

        return self._generate_embeddings(processed_diffs)