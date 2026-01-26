"""
Code preprocessing module for plagiarism detection.
Normalizes code by removing comments, whitespace, and other noise.
Focus: semantic similarity, not syntactic variations.
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class CodePreprocessor:
    """
    Preprocesses code to remove noise while preserving semantic meaning.
    Handles multiple languages (Python, Java, JavaScript, etc.)
    """
    
    # Language-specific comment patterns
    COMMENT_PATTERNS = {
        "python": {
            "line": r"#.*$",
            "block": (r'"""[\s\S]*?"""', r"'''[\s\S]*?'''"),
        },
        "java": {
            "line": r"//.*$",
            "block": (r"/\*[\s\S]*?\*/",),
        },
        "javascript": {
            "line": r"//.*$",
            "block": (r"/\*[\s\S]*?\*/",),
        },
        "typescript": {
            "line": r"//.*$",
            "block": (r"/\*[\s\S]*?\*/",),
        },
        "csharp": {
            "line": r"//.*$",
            "block": (r"/\*[\s\S]*?\*/",),
        },
        "cpp": {
            "line": r"//.*$",
            "block": (r"/\*[\s\S]*?\*/",),
        },
    }
    
    @staticmethod
    def remove_comments(code: str, language: str = "python") -> str:
        """
        Remove comments from code while preserving string literals.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Code with comments removed
        """
        patterns = CodePreprocessor.COMMENT_PATTERNS.get(language, {})
        
        # Remove block comments
        for pattern in patterns.get("block", []):
            code = re.sub(pattern, " ", code, flags=re.MULTILINE)
        
        # Remove line comments
        code = re.sub(patterns.get("line", ""), "", code, flags=re.MULTILINE)
        
        return code
    
    @staticmethod
    def normalize_whitespace(code: str) -> str:
        """
        Normalize whitespace: collapse multiple spaces/newlines.
        
        Args:
            code: Source code
            
        Returns:
            Code with normalized whitespace
        """
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in code.split("\n")]
        
        # Remove empty lines
        lines = [line for line in lines if line.strip()]
        
        # Join with single newline
        code = "\n".join(lines)
        
        # Collapse multiple spaces
        code = re.sub(r" +", " ", code)
        
        return code
    
    @staticmethod
    def normalize_identifiers(code: str) -> str:
        """
        Replace variable/function names with generic tokens.
        AGGRESSIVE: Helps detect logic similarity despite renames.
        
        Args:
            code: Source code
            
        Returns:
            Code with identifiers normalized
        """
        # Replace string literals with TOKEN_STRING
        code = re.sub(r'["\'].*?["\']', 'TOKEN_STRING', code)
        
        # Replace numbers with TOKEN_NUMBER
        code = re.sub(r'\b\d+\b', 'TOKEN_NUMBER', code)
        
        # Replace common variable names (but keep keywords)
        keywords = {
            "if", "else", "for", "while", "return", "def", "class",
            "import", "from", "try", "except", "function", "const", "let", "var",
            "public", "private", "static", "void", "int", "string", "bool"
        }
        
        # Simple identifier normalization (replace lowercase identifiers)
        def replace_identifier(match):
            word = match.group(0)
            if word.lower() in keywords:
                return word
            if word[0].isupper():  # Likely class name
                return "TokenClass"
            return "TokenVar"
        
        code = re.sub(r'\b[a-zA-Z_]\w*\b', replace_identifier, code)
        
        return code
    
    @staticmethod
    def remove_imports(code: str, language: str = "python") -> str:
        """
        Remove import statements (less relevant for plagiarism).
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Code without imports
        """
        if language == "python":
            code = re.sub(r"^(import|from).*$", "", code, flags=re.MULTILINE)
        elif language in ["java", "csharp"]:
            code = re.sub(r"^using.*$", "", code, flags=re.MULTILINE)
            code = re.sub(r"^import.*$", "", code, flags=re.MULTILINE)
        elif language in ["javascript", "typescript"]:
            code = re.sub(r"^(import|require).*$", "", code, flags=re.MULTILINE)
        
        return code
    
    @staticmethod
    def preprocess(
        code: str,
        language: str = "python",
        aggressive: bool = False
    ) -> str:
        """
        Full preprocessing pipeline.
        
        Args:
            code: Source code
            language: Programming language
            aggressive: If True, also normalize identifiers
            
        Returns:
            Preprocessed code
        """
        # Step 1: Remove comments
        code = CodePreprocessor.remove_comments(code, language)
        
        # Step 2: Normalize whitespace
        code = CodePreprocessor.normalize_whitespace(code)
        
        # Step 3: Remove imports
        code = CodePreprocessor.remove_imports(code, language)
        
        # Step 4: Aggressive - normalize identifiers
        if aggressive:
            code = CodePreprocessor.normalize_identifiers(code)
        
        # Final normalize
        code = CodePreprocessor.normalize_whitespace(code)
        
        return code
    
    @staticmethod
    def preprocess_files(
        files: Dict[str, str],
        language: str = "python",
        aggressive: bool = False
    ) -> Dict[str, str]:
        """
        Preprocess a collection of files.
        
        Args:
            files: Dictionary mapping file paths to contents
            language: Programming language
            aggressive: Aggressive normalization flag
            
        Returns:
            Dictionary with preprocessed contents
        """
        preprocessed = {}
        for path, content in files.items():
            try:
                preprocessed[path] = CodePreprocessor.preprocess(
                    content,
                    language,
                    aggressive
                )
            except Exception as e:
                logger.warning(f"Failed to preprocess {path}: {str(e)}")
                preprocessed[path] = content
        
        return preprocessed
