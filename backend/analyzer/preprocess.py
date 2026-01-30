"""Code preprocessing module."""

import re
import logging

logger = logging.getLogger(__name__)


class CodePreprocessor:
    """Preprocess code for analysis."""

    def __init__(self):
        pass

    def remove_comments(self, code, language='python'):
        """Remove comments from code."""
        if language.lower() == 'python':
            # Remove single-line comments
            code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)
            # Remove docstrings
            code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
            code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
        else:
            # For C-like languages
            # Remove single-line comments
            code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
            # Remove multi-line comments
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        return code

    def remove_imports(self, code):
        """Remove import statements."""
        code = re.sub(r'^import\s+.*?$', '', code, flags=re.MULTILINE)
        code = re.sub(r'^from\s+.*?import\s+.*?$', '', code, flags=re.MULTILINE)
        return code

    def normalize_whitespace(self, code):
        """Normalize whitespace and indentation."""
        # Remove trailing whitespace from lines
        code = '\n'.join(line.rstrip() for line in code.split('\n'))
        # Normalize multiple blank lines to single
        code = re.sub(r'\n\n+', '\n\n', code)
        # Remove leading/trailing whitespace from entire code
        code = code.strip()
        return code

    def normalize_identifiers(self, code):
        """Normalize variable and function names."""
        # Replace function definitions with generic names
        code = re.sub(r'\bdef\s+\w+\s*\(', 'def func(', code)
        # Replace class definitions with generic names
        code = re.sub(r'\bclass\s+\w+\s*[\(:]', 'class Class(', code)
        return code

    def preprocess(self, code, language='python', normalize_ids=False):
        """
        Full preprocessing pipeline.
        
        Args:
            code: Source code string
            language: Programming language
            normalize_ids: Whether to normalize identifiers
            
        Returns:
            Preprocessed code
        """
        try:
            code = self.remove_comments(code, language)
            code = self.remove_imports(code)
            code = self.normalize_whitespace(code)
            
            if normalize_ids:
                code = self.normalize_identifiers(code)
            
            return code
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return code
