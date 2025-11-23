

import uvicorn
import os
from virtual_hardware_lab.mcp_server_api.mcp_server import app, HOST, PORT

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

