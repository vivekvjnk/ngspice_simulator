# app.py
import os
import logging
import json
import base64
import inspect
import asyncio
from typing import Any, Dict, Optional, Callable, Union, List
from fastapi.responses import JSONResponse, FileResponse, Response

import uvicorn
from fastapi import (
    FastAPI,
    Body,
    Request,
    HTTPException,
    UploadFile,
    File,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

# Import your SimulationManager - adjust path if needed
from virtual_hardware_lab.simulation_manager import SimulationManager

# -------------------------
# Logging + basic settings
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("virtual_hardware_lab")
logger.setLevel(logging.DEBUG)

HOST = "0.0.0.0"
PORT = int(os.getenv("MCP_SERVER_PORT", 53328))
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}")

# -------------------------
# Application and manager
# -------------------------
app = FastAPI(
    title="Virtual Hardware Lab MCP Server",
    description="API and JSON-RPC dispatcher for SPICE simulations (MCP-compatible).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = SimulationManager()

# -------------------------
# Pydantic models
# -------------------------
class RunExperimentRequest(BaseModel):
    model_name: str = Field(..., description="Model template file name (e.g., randles_cell.j2)")
    model_params: dict = Field(default_factory=dict)
    control_name: str = Field(..., description="Control template file name (e.g., eis_control.j2)")
    control_params: dict = Field(default_factory=dict)
    sim_id: Optional[str] = None

class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Union[dict, list]] = None
    id: Optional[Union[int, str]] = None

# -------------------------
# Helpers
# -------------------------
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

async def _save_and_validate_template_file(directory: str, filename: str, content_bytes: bytes):
    if not filename.endswith(".j2"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .j2 files are allowed.")
    os.makedirs(directory, exist_ok=True)
    file_path = safe_join(directory, filename)
    
    def write_file():
        with open(file_path, "wb") as f:
            f.write(content_bytes)
    await asyncio.to_thread(write_file)
    
    return {"filename": filename, "message": f"Successfully uploaded {filename} to {directory}"}

# -------------------------
# RPC Implementation Methods
# -------------------------

def rpc_initialize(params: Dict[str, Any]):
    protocol = params.get("protocolVersion", "2025-06-18")
    return {
        "protocolVersion": protocol,
        "serverInfo": {
            "name": "virtual_hardware_lab",
            "version": "0.1.0",
            "description": "A Virtual Hardware Lab for deterministic and reproducible SPICE simulations.",
        },
        "capabilities": {
            "supportsNotifications": True,
        },
    }

def rpc_shutdown(params: Dict[str, Any]):
    return {"shutdown": True}

def rpc_list_models(params: Dict[str, Any]):
    try:
        models = manager.list_models()
        return {"models": models}
    except Exception as e:
        logger.exception("Error in rpc_list_models")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

def rpc_list_controls(params: Dict[str, Any]):
    try:
        controls = manager.list_controls()
        return {"controls": controls}
    except Exception as e:
        logger.exception("Error in rpc_list_controls")
        raise HTTPException(status_code=500, detail=f"Failed to list controls: {str(e)}")

def rpc_get_results(params: Dict[str, Any]):
    sim_id = None
    if isinstance(params, dict):
        sim_id = params.get("sim_id") or params.get("id") or params.get("simId")
    if not sim_id:
        return None
    return manager.read_results(sim_id)

def rpc_get_documentation(params: Dict[str, Any]):
    try:
        doc_path = "docs/VIRTUAL_HARDWARE_LAB_DOCUMENTATION.md"
        if not os.path.exists(doc_path):
            return {"error": "Documentation file not found."}
        with open(doc_path, "r") as f:
            return {"documentation": f.read()}
    except Exception as e:
        logger.exception("Failed to read documentation")
        return {"error": f"Error retrieving documentation: {str(e)}"}

def rpc_run_experiment(params: Dict[str, Any]):
    if isinstance(params, list):
        try:
            params_obj = {
                "model_name": params[0],
                "model_params": params[1] if len(params) > 1 else {},
                "control_name": params[2] if len(params) > 2 else None,
                "control_params": params[3] if len(params) > 3 else {},
                "sim_id": params[4] if len(params) > 4 else None,
            }
        except Exception:
            params_obj = {}
    else:
        params_obj = params or {}

    req = RunExperimentRequest.parse_obj(params_obj)
    return manager.start_sim(
        model_name=req.model_name,
        model_params=req.model_params,
        control_name=req.control_name,
        control_params=req.control_params,
        sim_id=req.sim_id,
    )

async def rpc_upload_model(params: Dict[str, Any]):
    filename = params.get("filename")
    content_base64 = params.get("content_base64")
    if not filename or not content_base64:
        raise HTTPException(status_code=400, detail="Missing filename or content_base64")
    try:
        content_bytes = base64.b64decode(content_base64)
        return await _save_and_validate_template_file(manager.models_dir, filename, content_bytes)
    except Exception as e:
        logger.exception("rpc_upload_model failed")
        raise HTTPException(status_code=500, detail=f"Failed to upload model: {str(e)}")

async def rpc_upload_control(params: Dict[str, Any]):
    filename = params.get("filename")
    content_base64 = params.get("content_base64")
    if not filename or not content_base64:
        raise HTTPException(status_code=400, detail="Missing filename or content_base64")
    try:
        content_bytes = base64.b64decode(content_base64)
        return await _save_and_validate_template_file(manager.controls_dir, filename, content_bytes)
    except Exception as e:
        logger.exception("rpc_upload_control failed")
        raise HTTPException(status_code=500, detail=f"Failed to upload control: {str(e)}")

def rpc_get_artifact_link(params: Dict[str, Any]):
    sim_id = params.get("sim_id")
    artifact_filename = params.get("artifact_filename")
    if not sim_id or not artifact_filename:
        raise HTTPException(status_code=400, detail="Missing sim_id or artifact_filename")
    try:
        artifact_path = safe_join(manager.runs_dir, sim_id, artifact_filename)
        if not os.path.exists(artifact_path):
             raise HTTPException(status_code=404, detail="Artifact not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    uri = f"{BASE_URL}/results/{sim_id}/artifact/{artifact_filename}"
    mime_type = "application/octet-stream"
    if artifact_filename.endswith(".json"): mime_type = "application/json"
    elif artifact_filename.endswith(".txt") or artifact_filename.endswith(".log"): mime_type = "text/plain"
    elif artifact_filename.endswith(".png"): mime_type = "image/png"

    return {
        "uri": uri,
        "mimeType": mime_type,
        "name": artifact_filename
    }

def rpc_tools_list(params: Dict[str, Any]):
    try:
        run_exp_schema = RunExperimentRequest.model_json_schema()
    except Exception:
        run_exp_schema = {"type": "object", "additionalProperties": True}

    # IMPORTANT: outputSchema is set to None.
    # We return text (JSON strings) via CallToolResult. 
    # Providing an outputSchema causes the client to fail validation on text results.
    tools = [
        {
            "id": "list_models",
            "name": "list_models",
            "title": "List Models",
            "description": "List available NGSpice model templates (GET /models).",
            "inputSchema": {"type": "object", "properties": {}}, 
            "outputSchema": None, # <--- FIXED
            "version": "1.0",
        },
        {
            "id": "list_controls",
            "name": "list_controls",
            "title": "List Controls",
            "description": "List available control templates (GET /controls).",
            "inputSchema": {"type": "object", "properties": {}},
            "outputSchema": None, # <--- FIXED
            "version": "1.0",
        },
        {
            "id": "run_experiment",
            "name": "run_experiment",
            "title": "Run Experiment",
            "description": "Start a SPICE simulation (POST /run_experiment).",
            "inputSchema": run_exp_schema,
            "outputSchema": None, # <--- FIXED
            "version": "1.0",
        },
        {
            "id": "get_results",
            "name": "get_results",
            "title": "Get Results",
            "description": "Get simulation manifest for a given sim_id.",
            "inputSchema": {
                "type": "object",
                "properties": {"sim_id": {"type": "string"}},
                "required": ["sim_id"],
            },
            "outputSchema": None, # <--- FIXED
            "version": "1.0",
        },
        {
            "id": "upload_model",
            "name": "upload_model",
            "title": "Upload Model Template",
            "description": "Upload a new NGSpice model template.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content_base64": {"type": "string"},
                },
                "required": ["filename", "content_base64"],
            },
            "outputSchema": None, # <--- FIXED
            "version": "1.0",
        },
        {
            "id": "upload_control",
            "name": "upload_control",
            "title": "Upload Control Template",
            "description": "Upload a new NGSpice control template.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content_base64": {"type": "string"},
                },
                "required": ["filename", "content_base64"],
            },
            "outputSchema": None, # <--- FIXED
            "version": "1.0",
        },
        {
            "id": "get_artifact_link",
            "name": "get_artifact_link",
            "title": "Get Artifact Link",
            "description": "Get a downloadable link for a simulation artifact.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sim_id": {"type": "string"},
                    "artifact_filename": {"type": "string"},
                },
                "required": ["sim_id", "artifact_filename"],
            },
            "outputSchema": None, # <--- FIXED
            "version": "1.0",
        },
        {
            "id": "get_documentation",
            "name": "get_documentation",
            "title": "Get Virtual Hardware Lab Documentation",
            "description": "Retrieve the comprehensive documentation.",
            "inputSchema": {"type": "object", "properties": {}},
            "outputSchema": None, # <--- FIXED
            "version": "1.0",
        },
    ]
    return {"tools": tools}

async def rpc_tools_call(params: Dict[str, Any]):
    """
    Handles 'tools/call' method.
    Returns standard MCP CallToolResult structure: { "content": [ { "type": "text", "text": "..." } ] }
    """
    method_name = params.get("name")
    arguments = params.get("arguments", {})

    if method_name not in RPC_METHODS:
        logger.warning("tools/call: Unknown method %s", method_name)
        raise HTTPException(status_code=404, detail=f"Method '{method_name}' not found.")

    handler = RPC_METHODS[method_name]
    
    if inspect.iscoroutinefunction(handler):
        result = await handler(arguments)
    else:
        result = handler(arguments)

    # Convert the dict result to a JSON string for the "text" field
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }

# -------------------------
# RPC Method Registry
# -------------------------
RPC_METHODS: Dict[str, Callable] = {
    "initialize": rpc_initialize,
    "shutdown": rpc_shutdown,
    "list_tools": rpc_tools_list,
    "tools/list": rpc_tools_list,
    "list_models": rpc_list_models,
    "list_controls": rpc_list_controls,
    "run_experiment": rpc_run_experiment,
    "get_results": rpc_get_results,
    "get_documentation": rpc_get_documentation,
    "upload_model": rpc_upload_model,
    "upload_control": rpc_upload_control,
    "get_artifact_link": rpc_get_artifact_link,
    "tools/call": rpc_tools_call,
}

# -------------------------
# Dispatcher
# -------------------------
async def dispatch_jsonrpc(payload: dict):
    try:
        req = JSONRPCRequest.model_validate(payload)
    except ValidationError as e:
        logger.warning("Invalid JSON-RPC request payload: %s", e)
        return 400, jsonrpc_error(-32600, "Invalid Request", None, data=e.errors())

    method = req.method
    params = req.params or {}
    id_val = req.id
    is_notification = id_val is None

    if method not in RPC_METHODS:
        if is_notification:
            return Response(status_code=204)
        return 404, jsonrpc_error(-32601, f"Method not found: {method}", id_val)

    try:
        handler = RPC_METHODS[method]
        
        if inspect.iscoroutinefunction(handler):
            result = await handler(params)
        else:
            result = handler(params)

        if is_notification:
            return Response(status_code=204)

        if result is None:
            return 200, jsonrpc_success(None, id_val)

        return 200, jsonrpc_success(result, id_val)
    
    except HTTPException as http_exc:
        return http_exc.status_code, jsonrpc_error(
            -32000 - http_exc.status_code, 
            http_exc.detail, 
            id_val
        )
    except ValidationError as e:
        return 400, jsonrpc_error(-32602, "Invalid params", id_val, data=e.errors())
    except Exception as e:
        logger.exception("Internal error in RPC handler for %s", method)
        return 500, jsonrpc_error(-32603, "Internal error", id_val, data=str(e))

# -------------------------
# Endpoints
# -------------------------

@app.post("/jsonrpc", summary="JSON-RPC 2.0 endpoint")
async def jsonrpc_endpoint(payload: Dict = Body(...)):
    status_or_resp = await dispatch_jsonrpc(payload)
    if isinstance(status_or_resp, Response):
        return status_or_resp
    status, content = status_or_resp
    if status == 204:
        return Response(status_code=204)
    return JSONResponse(status_code=status, content=content)

@app.post("/", summary="Root POST (compat json-rpc)")
async def root_post(request: Request, payload: Dict = Body(None)):
    if not payload:
        return {"message": "Virtual Hardware Lab MCP Server received a POST request!"}
    if isinstance(payload, dict) and payload.get("jsonrpc") == "2.0" and payload.get("method"):
        status_or_resp = await dispatch_jsonrpc(payload)
        if isinstance(status_or_resp, Response):
            return status_or_resp
        status, content = status_or_resp
        if status == 204:
            return Response(status_code=204)
        return JSONResponse(status_code=status, content=content)
    return {"message": "Virtual Hardware Lab MCP Server received a POST request!"}

@app.get("/", summary="Root GET")
async def root_get():
    return {"message": "Virtual Hardware Lab MCP Server is running!"}

@app.get("/models")
async def list_models():
    return JSONResponse(content=manager.list_models())

@app.get("/controls")
async def list_controls():
    return JSONResponse(content=manager.list_controls())

@app.post("/run_experiment")
async def run_experiment(request: RunExperimentRequest):
    manifest = manager.start_sim(
        model_name=request.model_name,
        model_params=request.model_params,
        control_name=request.control_name,
        control_params=request.control_params,
        sim_id=request.sim_id,
    )
    return JSONResponse(content=manifest)

@app.get("/results/{sim_id}")
@app.post("/results/{sim_id}")
async def get_results(sim_id: str):
    manifest = manager.read_results(sim_id)
    if manifest:
        return JSONResponse(content=manifest)
    raise HTTPException(status_code=404, detail=f"Simulation with ID '{sim_id}' not found.")

@app.get("/results/{sim_id}/artifact/{artifact_filename}")
@app.post("/results/{sim_id}/artifact/{artifact_filename}")
async def get_artifact(sim_id: str, artifact_filename: str):
    try:
        artifact_path = safe_join(manager.runs_dir, sim_id, artifact_filename)
        if not os.path.exists(artifact_path):
            raise HTTPException(status_code=404, detail="Artifact not found.")
        return FileResponse(artifact_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

@app.post("/upload_model")
async def upload_model(file: UploadFile = File(...)):
    content_bytes = await file.read()
    return await _save_and_validate_template_file(manager.models_dir, file.filename, content_bytes)

@app.post("/upload_control")
async def upload_control(file: UploadFile = File(...)):
    content_bytes = await file.read()
    return await _save_and_validate_template_file(manager.controls_dir, file.filename, content_bytes)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)