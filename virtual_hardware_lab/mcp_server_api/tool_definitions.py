

from virtual_hardware_lab.mcp_server_api.schemas import RunExperimentRequest

try:
    run_exp_schema = RunExperimentRequest.model_json_schema()
except Exception:
    run_exp_schema = {"type": "object", "additionalProperties": True}

TOOLS = [
    {
        "id": "list_models",
        "name": "list_models",
        "title": "List Models",
        "description": "List available NGSpice model templates (GET /models).",
        "inputSchema": {"type": "object", "properties": {}}, 
        "outputSchema": None,
        "version": "1.0",
    },
    {
        "id": "list_controls",
        "name": "list_controls",
        "title": "List Controls",
        "description": "List available control templates (GET /controls).",
        "inputSchema": {"type": "object", "properties": {}},
        "outputSchema": None,
        "version": "1.0",
    },
    {
        "id": "run_experiment",
        "name": "run_experiment",
        "title": "Run Experiment",
        "description": "Start a SPICE simulation (POST /run_experiment).",
        "inputSchema": run_exp_schema,
        "outputSchema": None,
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
        "outputSchema": None,
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
        "outputSchema": None,
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
        "outputSchema": None,
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
        "outputSchema": None,
        "version": "1.0",
    },
    {
        "id": "get_documentation",
        "name": "get_documentation",
        "title": "Get Virtual Hardware Lab Documentation",
        "description": "Retrieve the comprehensive documentation.",
        "inputSchema": {"type": "object", "properties": {}},
        "outputSchema": None,
        "version": "1.0",
    },
]

