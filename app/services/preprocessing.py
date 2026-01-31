import re

def preprocess_code(code):
    code = re.sub(r"#.*", "", code)          # remove comments
    code = re.sub(r"\s+", " ", code)         # normalize spaces
    code = re.sub(r"\b[a-zA-Z_]\w*\b", "VAR", code)
    return code.strip()
