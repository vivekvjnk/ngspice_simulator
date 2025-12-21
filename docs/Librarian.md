# Librarian: Conceptualization 
- We need a library of devices for circuit design. Devices from this library would be added to the scheamtic/layout as we proceed with the design. This library should contain all the primitive passive components and most widely used ics out of the box. There should be provision to add new components to the library. Library should be persistent and easily accessible to LLM agents.
    - How does the circuit builder agent know which all components(functionality and pin mapping) are already available in the Library? 
    - What are the steps to add a new component into the library? 


## The approach
Two parts:
1. The library      : MCP Server
2. The librarian    : Agent

## What are the minimum features of the library?
1. Pass through for all standard library components available in `tscircuit`
2. Interface to create library component
    - Validate new library component before adding them to the library; Either automated test code, or the test code from component provider(the library agent) can be used for validating.
        - Each new component should have: 1. symbol definition, 2. footprint
        - Brief description(Functionality, how to use, any other special instructions) about the component as structured comment in `tscircuit` .tsx file format
    - New component should behave like any other existing component in the library; There should not be any special conditions or procedures for using/importing the new component.
3. Interface to list local library components
    - This doesn't include legacy components available in `tscircuit`
        - Because `tscircuit` include all components from KiCAD. There are numerous components available under KiCAD library. Returning all these components would pollute the context of the requesting agent. Hence we chose to ignore them for this interface
    - Only Librarian added/created components will be displayed
4. Interface for searching **any** library component 
    - Support `fuzzy` and `regex` search
        - `Regex`: Regex pattern based search
        - `Fuzzy`: Regular string based search. Case insensitive, does fuzzy matching, ie if the searched string is present anywhere in the component name, return it. 
    - Support `deep` and `surface` search
        - Deep: Detailed description including pin mapping for the searched components 
        - Surface: Brief overview on all matched components from library
    - This interface search through all the available libraries including legacy ones from KiCAD, Librarian added components, and any other libraries available in `tscircuit` 
    - Support adding new libraries without much effort
    - User can invoke deep search with accurate component name for picking a specific component. 

## What are the minimum features of Librarian agent?
1. Create new component/s from SCUD descriptions
    - Then add new component/s to the library
2. Check if the components in SCUD are available in Library. If present validate if it matches with SCUD description. If not present create new component/s.

## Capabilities of Librarian agent
1. Use all tools available in Library MCP server
    - `Add component to library` tool for feature 1
    - `Search component` and `list components` tools for feature 2
    - Optional: Ability to modify/replace existing library component
2. Read and understand SCUD file. Compare and clarify understanding by comparing SCUD file with schematic image file or any other resources available to the agent.
3. Create new component in .tsx format. The component file should be complete; ie every information required by the downstream process(like footprint, symbol, spice placeholder etc.) should be present in the same file.
    - We plan to include .kicad_mod footprint files for new components. The .tsx component file should include the respective .kicad_mod file. 
    - As per the VHL Library implementation, if agent is using any .kicad_mod imports in the .tsx file, the respective file should be uploaded into the library first before using. 
    - Hence when Librarian want to add a new component, he should follow the steps:
        - Read SCUD file and decide the component to be added
        - Collect the right footprint .kicad_mod file
        - Add the footprint .kicad_mod file to the VHL Library using `addComponents`
        - Prepare .tsx component definition file. Ensure footprint files are imported correctly. (VHL stores footprint files and .tsx files in the same directory. So simple relative import will work fine. `addComponents` api stores files under same library directory.)
        - Upload .tsx file to VHL Library using `addComponents` endpoint

4. Generate simple `tscircuit` test code to validate the new component : Out of scope for now. 

### Tools for the agent
1. text_editor : to create .tsx files
2. Library MCP server

## Responsibilities of Librarian agent
- Input: 
    - SCUD file 

- Librarian is responsible for ensuring the availability of all the components captured in SCUD file in Library
- If any components are missing in Library, agent should create and add the component to the library

## Typical workflow of Librarian 
1. Starts with a SCUD file input
2. Analyse the `Components Inventory` section.
Then interact with `VHL Library`.
3. Use `searchComponent` to identify all standard/local library components which matches the `Component Inventory` devices. Prepare a list with the source library name.
4. List all the new components for which .tsx library should be prepared. 
    - Check if footprints are available in local directory(from which agent runs) for the new library components. If not, prompt user to upload them(For now, footprint selection is manual)
5. Create new component libraries. Follow [Capability 3 guidelines](#capabilities-of-librarian-agent)
6. Output of Librarian 
    - Updated SCUD document. 
    - Create a sub section under `Component Inventory` section in SCUD document. 
    - Map all the components with it's library location(local or global). Also update the library name corresponding to each component.

- Expectation: Agent 3 should be able to import all the libraries accurately, given the updated SCUD document. 
    - Hence, for 100% validation of Librarian, we need Agent 3 implementation. 
    - ie, we should keep open mind with the first implementation of Librarian agent. We can do basic validation on the output of Librarian(updated SCUD). If all special components are properly mapped to an available tscircuit library component, we could assume Librarian is complete at this point. Later, if necessary we would make changes to the agent according to our Agent 3 integration.
