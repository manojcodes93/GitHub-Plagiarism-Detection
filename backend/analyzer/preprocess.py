import re
from typing import Dict
import keyword

class CodePreprocessor:
    def remove_comments(self, code: str, language: str = "python") -> str:
        ## Removing comments from code
        if language == "python":
            code = re.sub(r"#.*$", "", code, flags=re.MULTILINE)
            code = re.sub(r'"""[\s\S]*?"""', "", code)
            code = re.sub(r"'''[\s\S]*?'''", "", code)
        
        elif language in ["java", "javascript"]:
            code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
            code = re.sub(r"/\*[\s\S]*?\*/", "", code)
        
        return code
    
    def remove_imports(self, code: str, language: str = "python") -> str:
        ## Removing import statements
        if language == "python":
            code = re.sub(r"^(import|from).*$", "", code, flags=re.MULTILINE)

        elif language in ["java", "javascript"]:
            code = re.sub(r"^import.*$", "", code, flags=re.MULTILINE)

        return code
    
    def normalize_whitespace(self, code: str) -> str:
        ## Normalizing whitespace
        lines = code.split("\n")
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)

        code = "\n".join(cleaned_lines)
        code = re.sub(r"\s+", " ", code)

        return code
    
    def normalize_identifiers(self, code: str, language: str = "python") -> str:
        """
        Normalize user-defined identifiers while preserving keywords and structure.
        """
        if language != "python":
            return code
        
        python_keywords = set(keyword.kwlist)
        python_builtins = set(dir(__builtins__))
        
        def replacer(match):
            token = match.group(0)
            if token in python_keywords or token in python_builtins:
                return token
            return "VAR"
        
        # Replace variable and function names, not keywords
        
        code = re.sub(r"\b[a-zA-Z_]\w*\b", replacer, code)
        
        # Normalize numbers and strings
        code = re.sub(r"\b\d+\b", "NUM", code)
        code = re.sub(r'(["\']).*?\1', "STR", code)
        
        return code

    def preprocess(
        self,
        code: str,
        language: str = "python",
        aggressive: bool = False
    ) -> str:
        ## Full preprocessing pipeline
        code = self.remove_comments(code, language)
        code = self.remove_imports(code, language)
        code = self.normalize_whitespace(code)

        if aggressive:
            code = self.normalize_identifiers(code, language)
            code = self.normalize_whitespace(code)

        return code
    
    @staticmethod
    def preprocess_files(
        files: Dict[str, str],
        language: str = "python",
        aggressive: bool = False
    ) -> Dict[str, str]:
        ## Applying preprocessing to multiple files

        processed_files = {}
        preprocessor = CodePreprocessor()
        
        for path, content in files.items():
            processed_files[path] = preprocessor.preprocess(
                content,
                language,
                aggressive
            )

        return processed_files