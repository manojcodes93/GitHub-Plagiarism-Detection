import re

def preprocess_code(code: str) -> str:
    # remove comments
    code = re.sub(r"#.*", "", code)

    # remove multiline strings
    code = re.sub(r'""".*?"""', "", code, flags=re.S)
    code = re.sub(r"'''.*?'''", "", code, flags=re.S)

    # normalize whitespace
    code = re.sub(r"\s+", " ", code)

    return code.strip()
