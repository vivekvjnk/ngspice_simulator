
import os
import asyncio
from typing import Any
from fastapi import HTTPException

def jsonrpc_success(result: Any, id_val: Any):
    return {"jsonrpc": "2.0", "result": result, "id": id_val}

def jsonrpc_error(code: int, message: str, id_val: Any = None, data: Any = None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "error": err, "id": id_val}

def safe_join(base_dir: str, *paths: str) -> str:
    candidate = os.path.abspath(os.path.join(base_dir, *paths))
    base_dir_abs = os.path.abspath(base_dir)
    if not candidate.startswith(base_dir_abs):
        raise ValueError("Invalid path (possible path traversal).")
    return candidate

async def save_and_validate_template_file(directory: str, filename: str, content_bytes: bytes):
    if not filename.endswith(".j2"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .j2 files are allowed.")
    os.makedirs(directory, exist_ok=True)
    file_path = safe_join(directory, filename)
    
    def write_file():
        with open(file_path, "wb") as f:
            f.write(content_bytes)
    await asyncio.to_thread(write_file)
    
    return {"filename": filename, "message": f"Successfully uploaded {filename} to {directory}"}

