"""LLM-based plagiarism reasoning."""

import logging

logger = logging.getLogger(__name__)


class LLMReasoner:
    """Rule-based plagiarism detection and explanation."""

    def __init__(self):
        """Initialize reasoner with thresholds."""
        self.high_threshold = 0.8
        self.medium_threshold = 0.6
        self.low_threshold = 0.4

    def judge_file_similarity(self, similarity_score):
        """
        Determine plagiarism judgment based on similarity score.
        
        Args:
            similarity_score: Float between 0 and 1
            
        Returns:
            String judgment: 'PLAGIARISM', 'SUSPICIOUS', 'CLEAN'
        """
        try:
            if similarity_score >= self.high_threshold:
                return 'PLAGIARISM'
            elif similarity_score >= self.medium_threshold:
                return 'SUSPICIOUS'
            else:
                return 'CLEAN'
        except Exception as e:
            logger.error(f"Judgment failed: {e}")
            return 'UNKNOWN'

    def judge_commit_similarity(self, commit_embeddings_similarity):
        """
        Determine if commit history is similar.
        
        Args:
            commit_embeddings_similarity: Similarity score for commits
            
        Returns:
            Boolean - True if commits are similar
        """
        try:
            return commit_embeddings_similarity >= self.medium_threshold
        except Exception as e:
            logger.error(f"Commit judgment failed: {e}")
            return False

    def generate_plagiarism_explanation(self, repository_similarity, file_judgments):
        """
        Generate explanation for plagiarism detection.
        
        Args:
            repository_similarity: Overall repo similarity score
            file_judgments: Dict of {filename: judgment}
            
        Returns:
            Explanation string
        """
        try:
            plagiarism_files = sum(1 for j in file_judgments.values() if j == 'PLAGIARISM')
            suspicious_files = sum(1 for j in file_judgments.values() if j == 'SUSPICIOUS')
            total_files = len(file_judgments)

            explanation = (
                f"Repository similarity: {repository_similarity:.2%}. "
                f"Found {plagiarism_files} files with clear plagiarism patterns, "
                f"{suspicious_files} suspicious files out of {total_files} total. "
            )

            if plagiarism_files > 0:
                explanation += "Strong evidence of plagiarism detected."
            elif suspicious_files > total_files * 0.3:
                explanation += "Multiple suspicious patterns warrant further investigation."
            else:
                explanation += "No significant plagiarism indicators found."

            return explanation

        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return "Unable to generate explanation."
