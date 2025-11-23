
# Virtual Hardware Lab Documentation

## Purpose
The Virtual Hardware Lab (VHL) is a sophisticated simulation environment designed to manage and execute SPICE (Simulation Program with Integrated Circuit Emphasis) simulations in a deterministic and reproducible manner. It provides a structured framework for experimenting with electronic circuits, particularly useful for scenarios requiring precise control over model definitions and experimental conditions, such as battery modeling or sensor characterization.

## Core Concepts

### SPICE
SPICE is a general-purpose open-source analog electronic circuit simulator. The VHL leverages `ngspice`, a popular open-source SPICE engine, to perform the actual simulations.

### Models
In the VHL, "models" refer to the fundamental SPICE netlist definitions of the hardware or component being simulated (e.g., a battery, a sensor, a resistor-capacitor network). These are typically stored as Jinja2 templates (`.j2` files in plain text format) in the `models/` directory. They contain the circuit topology, component values, and other physical parameters.

### Controls
"Controls" define the experimental conditions and analysis commands for a SPICE simulation. This includes aspects like the type of analysis (e.g., AC sweep, transient analysis), stimulus signals, measurement points, and output formats. Like models, controls are also Jinja2 templates (`.j2` files in plain text format) located in the `controls/` directory.

### Jinja2 Templating
Both models and controls are written as Jinja2 templates. This allows for dynamic parameterization of simulations. Users can inject specific values (e.g., resistance, capacitance, temperature, current levels) into the templates at runtime, enabling flexible and varied experimentation without modifying the base template files.

### Metadata
Each model and control template can embed YAML metadata at its beginning. This metadata block, delimited by `* ---` and `* ---`, describes the template's purpose, available parameters, their types, default values, and valid ranges. This allows for self-documenting templates and enables validation of input parameters, ensuring simulations are run with valid configurations.

Example Metadata Structure:
```yaml
name: "RC Circuit Model"
description: "A simple Resistor-Capacitor circuit model."
parameters:
  R1:
    type: float
    unit: Ohm
    default: 100
    range: [1, 1000]
  C1:
    type: float
    unit: Farad
    default: 1e-6
    range: [1e-9, 1e-3]
```

### SPICE Code Rendering from Controls and Models

The VHL dynamically generates the final SPICE netlist used by `ngspice` by combining a model template and a control template. This process involves:

1.  **Template Selection**: Based on the `model_name` and `control_name` provided to `start_sim`, the corresponding Jinja2 templates are loaded from the `models/` and `controls/` directories.
2.  **Parameter Injection**: The `model_params` and `control_params` dictionaries are used to render their respective templates. Jinja2 replaces placeholders in the templates (e.g., `{{ R1 }}`) with the actual values supplied. This allows for flexible and dynamic circuit configurations and experimental setups.
3.  **Forbidden Directive Checks (Implicit)**: While not explicitly detailed in the `SimulationManager` code for external agents, the underlying design prevents unsafe or non-compliant SPICE directives from being introduced, ensuring simulation integrity. This is handled internally during the template processing and merging.
4.  **Deterministic Merging**: The rendered model and control netlists are merged into a single `.cir` file. The VHL ensures this merging process is deterministic, meaning the order and structure of the combined netlist are consistent for identical inputs. The control netlist is appended after the model netlist, typically with a separator like `* --- control ---` for clarity and debugging.
5.  **Final Netlist Generation**: The merged content forms the complete SPICE input file (`merged.cir`) which is then passed to the `ngspice` simulator for execution.

This structured approach guarantees that the generated SPICE code is consistent, parameterized, and reproducible for every simulation run.

### Determinism and Reproducibility
A key feature of the VHL is its emphasis on determinism and reproducibility. Every simulation run is assigned a unique simulation ID (`sim_id`) based on its inputs. The system ensures that running the same model with the same parameters and control program will always yield identical results. All generated artifacts and a `manifest.json` are stored for each run, allowing for full traceability and recreation of past experiments.

### Artifacts and Manifest
Each successful simulation run generates a dedicated directory under `runs/` identified by its `sim_id`. This directory contains:
- `model.cir`: The rendered SPICE netlist for the model.
- `control.cir`: The rendered SPICE netlist for the control program.
- `merged.cir`: The combined and final SPICE netlist submitted to `ngspice`.
- `ngspice.log`: The raw output log from the `ngspice` simulator.
- `manifest.json`: A comprehensive JSON file detailing all aspects of the simulation, including `sim_id`, model and control names, input parameters, SHA256 hashes of the rendered netlists, tool versions, and paths to all generated artifacts.

## Defining New Models and Controls

The Virtual Hardware Lab is designed to be extensible, allowing users to define their own SPICE models and control programs. This is done by creating Jinja2 template files (`.j2`) in the `models/` and `controls/` directories, respectively.

### Creating Model and Control Templates

1.  **File Location**:
    *   Place new model templates (e.g., `my_new_device.j2`) in the `models/` directory.
    *   Place new control templates (e.g., `my_new_experiment.j2`) in the `controls/` directory.

2.  **Jinja2 Syntax**:
    *   Use standard Jinja2 templating syntax to define variable placeholders. For example, `{{ my_parameter }}` will be replaced by the value of `my_parameter` provided during simulation.
    *   These templates should contain valid SPICE netlist syntax.

3.  **Embedding Metadata**:
    *   Each `.j2` file **must** include a YAML metadata block at the top. This block provides essential information about the template, its purpose, and the parameters it expects.
    *   The metadata block is delimited by `* ---` (start) and `* ---` (end) on separate lines.
    *   Each line within the metadata block (excluding the delimiters) must start with `* ` (an asterisk followed by a space) to be correctly parsed by the `SimulationManager`.

### Metadata Structure

The YAML metadata block should follow a defined structure to ensure proper validation and introspection.

```yaml
* ---
* name: "Descriptive Name for Model/Control"
* description: "A brief explanation of what this model/control does."
* parameters:
*   parameter_name_1:
*     type: [float, int, str, bool] # Expected data type (e.g., float, int, str)
*     unit: "Unit of measurement (e.g., Ohm, Farad, Hz)" # Optional unit
*     default: 100 # Optional default value
*     range: [min_value, max_value] # Optional, for numeric types
*     options: [option1, option2] # Optional, for string/enum types
*   parameter_name_2:
*     # ... more parameters
* ---
```

*   **`name`**: (Required) A human-readable name for the model or control.
*   **`description`**: (Required) A brief explanation of the model's or control's function.
*   **`parameters`**: (Optional) A dictionary defining the input parameters that the Jinja2 template expects. Each key in this dictionary should correspond to a variable name used in the template (e.g., `R1` if your template has `{{ R1 }}`).
    *   For each parameter, the following attributes can be defined:
        *   **`type`**: (Required) The expected data type of the parameter (`float`, `int`, `str`, `bool`). This is used for validation.
        *   **`unit`**: (Optional) A string indicating the physical unit of the parameter (e.g., "Ohm", "Farad", "Hz", "V", "A").
        *   **`default`**: (Optional) A default value for the parameter.
        *   **`range`**: (Optional) For numeric types, a two-element list `[min_value, max_value]` specifying the valid numerical range.
        *   **`options`**: (Optional) For string or enum-like types, a list of allowed string values.

### Example

Here's an example of a simple RC circuit model (`rc_model.j2`) with embedded metadata:

```jinja2
* ---
* name: "Simple RC Circuit"
* description: "A basic series RC circuit for transient analysis."
* parameters:
*   R1:
*     type: float
*     unit: Ohm
*     default: 100
*     range: [1, 1e6]
*   C1:
*     type: float
*     unit: Farad
*     default: 1e-6
*     range: [1e-12, 1e-3]
* ---
.subckt RC_CIRCUIT input output
R1 input 1 {{ R1 }}
C1 1 output {{ C1 }}
.ends RC_CIRCUIT
```

## Functionality (How to use the Lab)

The `SimulationManager` class provides the programmatic interface to the Virtual Hardware Lab. Clients interact with these functionalities, typically through an MCP server that exposes these methods.

### 1. Listing Available Models
Clients can inquire about the available hardware models in the lab.
- **Method:** `list_models()`
- **Purpose:** Returns a list of all model templates, including their names and parsed metadata.
- **Output:** A list of dictionaries, where each dictionary contains:
    - `name`: The filename of the model template (e.g., "battery_model.j2").
    - `metadata`: A dictionary containing the YAML metadata extracted from the template.

### 2. Getting Specific Model Metadata
Clients can retrieve detailed information about a particular model.
- **Method:** `get_model_metadata(model_name)`
- **Purpose:** Fetches the metadata for a specified model template.
- **Input:**
    - `model_name` (string): The name of the model template (e.g., "battery_model.j2").
- **Output:** A dictionary containing the YAML metadata for the model, or `None` if the model is not found.

### 3. Listing Available Controls
Clients can inquire about the available control programs/experiment definitions.
- **Method:** `list_controls()`
- **Purpose:** Returns a list of all control templates, including their names and parsed metadata.
- **Output:** A list of dictionaries, similar to `list_models()`.

### 4. Getting Specific Control Metadata
Clients can retrieve detailed information about a particular control program.
- **Method:** `get_control_metadata(control_name)`
- **Purpose:** Fetches the metadata for a specified control template.
- **Input:**
    - `control_name` (string): The name of the control template (e.g., "eis_sweep.j2").
- **Output:** A dictionary containing the YAML metadata for the control, or `None` if the control is not found.

### 5. Starting a Simulation
This is the primary method for running an experiment.

-   **Method:** `start_sim(model_name, model_params, control_name, control_params, sim_id=None)`
-   **Purpose:** Initiates a SPICE simulation using the specified model and control templates with the given parameters. It orchestrates the rendering, merging, `ngspice` execution, and artifact generation.
-   **Inputs:**
    *   `model_name` (string): The name of the model template to use (e.g., "battery_model.j2"). This corresponds to a `.j2` file in the `models/` directory.
    *   `model_params` (dictionary): A dictionary of parameters to inject into the model template. Keys should match parameter names defined in the model's metadata (e.g., `{"R_batt": 10, "C_dl": 1e-6}`). These parameters are critical for customizing the model's behavior and will be validated against the metadata.
    *   `control_name` (string): The name of the control template to use (e.g., "eis_sweep.j2"). This corresponds to a `.j2` file in the `controls/` directory.
    *   `control_params` (dictionary): A dictionary of parameters to inject into the control template. Keys should match parameter names defined in the control's metadata (e.g., `{"freq_start": 0.1, "freq_end": 10000}`). These parameters define the experimental conditions and simulation analyses, and will be validated.
    *   `sim_id` (string, optional): An optional, user-defined simulation ID. If not provided, a unique ID will be generated based on the current timestamp and a hash of the combined `model_params` and `control_params`. This ensures reproducibility and easy identification of simulation runs.
-   **Process Flow (Internal to `start_sim`):**
    1.  **Unique Simulation ID**: A `sim_id` is determined or generated, and a dedicated directory (`runs/<sim_id>/`) is created for all simulation artifacts.
    2.  **Template Rendering**:
        *   The `model_name` template is loaded and rendered using `model_params`.
        *   The `control_name` template is loaded and rendered using `control_params`.
        *   This step replaces all `{{ parameter }}` placeholders in the Jinja2 templates with their corresponding values.
    3.  **Netlist Merging**: The rendered model and control netlists are combined into a single `merged.cir` file. This file contains the complete SPICE deck ready for simulation.
    4.  **ngspice Execution**: The `merged.cir` file is passed to the `ngspice` simulator. The VHL captures all `ngspice` output (stdout and stderr) into an `ngspice.log` file, enabling detailed debugging if simulations fail. A timeout mechanism is also in place to prevent indefinitely running simulations.
    5.  **Artifact Generation**: Beyond the raw `ngspice` output, the VHL processes simulation results to generate relevant artifacts. For example, in EIS (Electrochemical Impedance Spectroscopy) simulations, it parses impedance data and automatically generates a Nyquist plot (`nyquist_plot.png`).
    6.  **Manifest Creation**: A `manifest.json` file is created within the `runs/<sim_id>/` directory. This file comprehensively documents the simulation, including:
        *   The `sim_id` itself.
        *   Details of the model and control used, including their names, input parameters, and SHA256 hashes of their rendered content (ensuring traceability).
        *   Versions of the simulation tools (e.g., `ngspice`).
        *   Paths to all generated artifacts, making them easy to locate and retrieve.
-   **Output:** A dictionary representing the `manifest.json` for the completed simulation. This manifest serves as the primary record of the simulation and its results, providing all necessary details to understand, analyze, and reproduce the experiment.

### 6. Reading Simulation Results
Clients can retrieve the manifest of a previously run simulation.
- **Method:** `read_results(sim_id)`
- **Purpose:** Retrieves the `manifest.json` for a given `sim_id`, allowing access to run details and artifact paths.
- **Input:**
    - `sim_id` (string): The unique identifier of a completed simulation run.
- **Output:** A dictionary containing the contents of the `manifest.json` for the specified `sim_id`, or `None` if the `sim_id` is not found.

## General Guidelines and Design Principles

The Virtual Hardware Lab is built upon several core design principles to ensure robust, reproducible, and efficient simulations. Understanding these principles will help users and developers interact with the VHL effectively.

### 1. Reproducibility by Design

*   **Deterministic Simulation IDs**: Every simulation run is assigned a unique `sim_id` derived from a hash of its input parameters (model, control, and their respective parameter sets) and a timestamp. This guarantees that running the exact same experiment with the exact same inputs will always produce the same `sim_id` and therefore, if cached, the same results.
*   **Immutable Artifacts**: Once a simulation is run, all its generated artifacts (netlists, logs, plots, manifest) are stored in a dedicated, immutable directory identified by its `sim_id`. This prevents accidental modification and ensures that past results can always be retrieved and verified.
*   **Comprehensive Manifest**: The `manifest.json` file is central to reproducibility. It captures every detail of a simulation run, from input parameters and rendered netlist hashes to tool versions and output artifact paths. This allows for complete traceability and recreation of any experiment.

### 2. Separation of Concerns (Model vs. Control)

*   **Clear Boundaries**: The VHL strictly separates the definition of the physical system (Model) from the experimental setup and analysis (Control). This modular approach promotes reusability and simplifies the development and debugging of both models and experiments.
*   **Jinja2 Templating**: The use of Jinja2 for both models and controls enables dynamic parameterization without intertwining the core logic. This means you can use the same base model with different parameters, or test a single model under various experimental conditions defined by different controls.

### 3. LLM-Friendly Interface

*   **Metadata-Driven**: The embedded YAML metadata in model and control templates makes the system highly discoverable and interpretable for AI agents. LLMs can read this metadata to understand the purpose of a model or control, its configurable parameters, and their expected types and ranges. This facilitates automated experiment design and parameter selection.
*   **Structured Outputs**: Simulation results, particularly the `manifest.json`, provide structured data that is easy for machines (and humans) to parse and understand, aiding in automated analysis and reporting.

### 4. Safety and Validation

*   **Parameter Validation**: Input parameters provided for models and controls are validated against the schema defined in their respective metadata. This helps prevent common errors, ensures data integrity, and guides users/agents to provide valid inputs.
*   **Forbidden Directives (Internal)**: The system is designed to prevent the introduction of potentially unsafe or non-compliant SPICE directives, maintaining the integrity and security of the simulation environment.

### 5. Efficiency Through Caching

*   **Automatic Caching**: The VHL automatically caches the results of simulations. If an identical simulation (same model, control, and parameters) is requested again, the system can retrieve the cached results instead of re-running the `ngspice` process, saving computational resources and time. This is seamless and transparent to the user.

## Client Interaction (MCP Protocol)

When interacting with the Virtual Hardware Lab through an MCP server, clients should expect to send requests that map to the `SimulationManager` methods. The MCP protocol will define the message formats for these requests and their corresponding responses.
