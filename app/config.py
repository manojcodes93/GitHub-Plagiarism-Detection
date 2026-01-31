class Config:
    SECRET_KEY = "hackathon-secret"

    # Analysis limits (safe mode)
    MAX_FILES_PER_REPO = 50
    MAX_FILE_SIZE_KB = 200
    MAX_COMMITS = 200

    SKIP_DIRS = {
        "venv",
        "node_modules",
        "dist",
        "build",
        "__pycache__",
        ".git"
    }
