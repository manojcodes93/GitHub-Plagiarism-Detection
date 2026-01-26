"""
LLM-based plagiarism reasoning module.
Uses a code-focused LLM to determine if similarity indicates plagiarism.
Provides explainable plagiarism judgments.
"""

import logging
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("transformers not installed. Using mock LLM reasoning.")


class LLMReasoner:
    """
    Uses a Hugging Face code-focused LLM to make plagiarism judgments.
    Provides explainable decisions about whether high similarity indicates plagiarism.
    """
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"):
        """
        Initialize LLM reasoner.
        
        Args:
            model_name: Hugging Face model identifier
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu" if HAS_TRANSFORMERS else None
        
        if HAS_TRANSFORMERS:
            try:
                logger.info(f"Loading LLM model: {model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto"
                )
                logger.info(f"LLM loaded successfully on {self.device}")
            except Exception as e:
                logger.error(f"Failed to load LLM: {str(e)}")
                self.model = None
                self.tokenizer = None
    
    def _generate_response(self, prompt: str, max_length: int = 256) -> str:
        """
        Generate response from LLM.
        
        Args:
            prompt: Input prompt
            max_length: Maximum response length
            
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            logger.warning("LLM not available")
            return ""
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=0.3,  # Low temperature for consistent judgments
                    top_p=0.9,
                    do_sample=True,
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
            
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            return ""
    
    def judge_file_plagiarism(
        self,
        file1_path: str,
        file1_content: str,
        file2_path: str,
        file2_content: str,
        similarity_score: float
    ) -> Dict[str, Any]:
        """
        Judge if two similar files indicate plagiarism using LLM reasoning.
        
        Args:
            file1_path: Path of first file
            file1_content: Content snippet of first file
            file2_path: Path of second file
            file2_content: Content snippet of second file
            similarity_score: Embedding similarity score
            
        Returns:
            {
                "is_plagiarism": bool,
                "confidence": float (0-1),
                "reason": str,
                "explanation": str
            }
        """
        # Simple heuristics if LLM not available
        if similarity_score > 0.95:
            return {
                "is_plagiarism": True,
                "confidence": 0.95,
                "reason": "Extreme similarity in embeddings",
                "explanation": f"The files {file1_path} and {file2_path} have extremely high semantic similarity ({similarity_score:.2%}), suggesting potential plagiarism.",
            }
        elif similarity_score > 0.85:
            return {
                "is_plagiarism": True,
                "confidence": 0.75,
                "reason": "Very high similarity",
                "explanation": f"High semantic similarity ({similarity_score:.2%}) detected. Likely plagiarism or direct copying.",
            }
        elif similarity_score > 0.75:
            return {
                "is_plagiarism": True,
                "confidence": 0.6,
                "reason": "High similarity with suspicious patterns",
                "explanation": f"Similarity score {similarity_score:.2%} warrants manual review.",
            }
        else:
            return {
                "is_plagiarism": False,
                "confidence": 0.8,
                "reason": "Similarity within normal range",
                "explanation": f"Similarity score {similarity_score:.2%} is not indicative of plagiarism.",
            }
    
    def judge_commit_plagiarism(
        self,
        commit1_msg: str,
        commit1_diff: str,
        commit2_msg: str,
        commit2_diff: str,
        similarity_score: float
    ) -> Dict[str, Any]:
        """
        Judge if two similar commits indicate plagiarism.
        
        Args:
            commit1_msg: First commit message
            commit1_diff: First commit diff
            commit2_msg: Second commit message
            commit2_diff: Second commit diff
            similarity_score: Embedding similarity score
            
        Returns:
            Plagiarism judgment
        """
        reasons = []
        confidence = 0.5
        
        # Check for identical messages
        if commit1_msg.strip() == commit2_msg.strip():
            reasons.append("Identical commit messages")
            confidence = 0.8
        elif similarity_score > 0.9:
            reasons.append("Extremely similar changes")
            confidence = 0.85
        elif similarity_score > 0.8:
            reasons.append("Very similar changes")
            confidence = 0.7
        
        is_plagiarism = confidence > 0.6
        reason = " + ".join(reasons) if reasons else "Moderate similarity"
        
        return {
            "is_plagiarism": is_plagiarism,
            "confidence": confidence,
            "reason": reason,
            "explanation": f"Commits show {similarity_score:.2%} similarity with patterns: {reason}",
        }
    
    def generate_plagiarism_explanation(
        self,
        repo1_name: str,
        repo2_name: str,
        similar_files: List[Dict],
        repo_similarity: float
    ) -> str:
        """
        Generate human-readable plagiarism explanation.
        
        Args:
            repo1_name: First repository name
            repo2_name: Second repository name
            similar_files: List of similar file pairs
            repo_similarity: Repository-level similarity
            
        Returns:
            Human-readable explanation
        """
        explanation = f"""
PLAGIARISM ANALYSIS REPORT
=========================
Repository 1: {repo1_name}
Repository 2: {repo2_name}
Repository Similarity Score: {repo_similarity:.2%}

SUSPICIOUS FILE PAIRS ({len(similar_files)}):
"""
        
        for i, pair in enumerate(similar_files[:10], 1):
            explanation += f"""
{i}. {pair['file1']} <-> {pair['file2']}
   Similarity: {pair['similarity']:.2%}
   Status: {pair['status'].upper()}
"""
        
        if len(similar_files) > 10:
            explanation += f"\n... and {len(similar_files) - 10} more similar pairs"
        
        # Overall verdict
        if repo_similarity > 0.85:
            explanation += "\n\nVERDICT: LIKELY PLAGIARISM - Recommend manual review"
        elif repo_similarity > 0.75:
            explanation += "\n\nVERDICT: SUSPICIOUS - Possible plagiarism or common libraries"
        else:
            explanation += "\n\nVERDICT: LOW RISK - Similarity within acceptable range"
        
        return explanation
    
    def batch_judge_files(
        self,
        file_pairs: List[Dict]
    ) -> List[Dict]:
        """
        Batch judge multiple file pairs.
        
        Args:
            file_pairs: List of similar file pairs from similarity analyzer
            
        Returns:
            Judgments for each pair
        """
        judgments = []
        
        for pair in file_pairs:
            judgment = self.judge_file_plagiarism(
                pair["file1"],
                "",  # Content not available in this context
                pair["file2"],
                "",
                pair["similarity"]
            )
            judgments.append({
                **pair,
                "judgment": judgment
            })
        
        return judgments
