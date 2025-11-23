
# Virtual Hardware Lab

This project provides a Virtual Hardware Lab (VHL) for managing and running ngspice simulations. It leverages FastAPI for building a web interface or API, Jinja2 for templating, Matplotlib and NumPy for data processing and visualization, Pydantic for data validation, Uvicorn as an ASGI server, and PyYAML for configuration.

## Features

*   **ngspice Simulation Management**: Facilitates the setup, execution, and analysis of ngspice circuit simulations.
*   **Model and Control Upload**: Allows users to upload their own ngspice model and control template files (`.j2`) to the server.
*   **Web Interface/API**: Built with FastAPI, allowing for interaction with the simulator through a web interface or programmatic API calls.
*   **Data Validation**: Uses Pydantic for robust data validation, ensuring consistency and correctness of simulation parameters and results.
*   **Data Visualization**: Integrates Matplotlib and NumPy for processing and visualizing simulation outputs.

## Installation

To install the `virtual_hardware_lab`, first clone the repository:

```bash
git clone https://github.com/vivekvjnk/virtual_hardware_laboratary.git
cd virtual_hardware_laboratary
```

Then, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the VHL Server
To start the VHL server, navigate to the project's root directory and run:

```bash
python -m virtual_hardware_lab.main
```

The server will be accessible at `http://0.0.0.0:53328` (or the port specified in the `MCP_SERVER_PORT` environment variable).

### Interacting with the JSON-RPC API
The VHL exposes a JSON-RPC 2.0 API for all its functionalities. You can interact with it using `curl` or any HTTP client.

**Example: Listing Available Tools**
```bash
curl -X POST http://localhost:53328/jsonrpc \
     -H "Content-Type: application/json" \
     -d '{
           "jsonrpc": "2.0",
           "method": "tools/list",
           "id": 1
         }'
```

**Example: Uploading a Model File**
You would typically encode the file content in base64.
```bash
curl -X POST http://localhost:53328/jsonrpc \
     -H "Content-Type: application/json" \
     -d '{
           "jsonrpc": "2.0",
           "method": "upload_model",
           "params": {
             "filename": "my_model.j2",
             "content_base64": "base64_encoded_content_here"
           },
           "id": 2
         }'
```

## Project Structure

*   `virtual_hardware_lab/`: The core Python package containing:
    *   `mcp_server_api/`: Contains files related to the MCP server API.
        *   `mcp_server.py`: FastAPI application setup and JSON-RPC endpoint.
        *   `schemas.py`: Pydantic models for data validation.
        *   `utils.py`: Helper functions.
        *   `rpc_methods.py`: Implementation of JSON-RPC methods.
        *   `tool_definitions.py`: Definitions for available tools.
    *   `simulation_core/`: Contains files related to the core simulation logic.
        *   `simulation_manager.py`: Manages the ngspice simulation process.
    *   `main.py`: The entry point for running the VHL server.
*   `controls/`: Contains control scripts or configuration files for simulations.
*   `docs/`: Documentation files for the project.
*   `models/`: Contains model templates for simulations.
*   `runs/`: Directory for storing simulation run outputs or results.
*   `requirements.txt`: Lists all Python dependencies.

## Dependencies

The project relies on the following Python libraries:

*   `fastapi`: For building APIs.
*   `jinja2`: A modern and designer-friendly templating language for Python.
*   `matplotlib`: For creating static, animated, and interactive visualizations in Python.
*   `numpy`: The fundamental package for scientific computing with Python.
*   `pydantic`: Data validation and settings management using Python type hints.
*   `uvicorn`: An ASGI web server for Python.
*   `PyYAML`: A YAML parser and emitter for Python.

## Contributing

Contributions are welcome! Please refer to the project's issue tracker for open tasks or submit pull requests with improvements.

## License

This project is licensed under the MIT License. See the `LICENSE` file in the repository root for details.

