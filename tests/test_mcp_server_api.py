
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi.responses import Response, JSONResponse

# Import the FastAPI app instance from your application
from virtual_hardware_lab.mcp_server_api.mcp_server import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_simulation_manager():
    """
    Fixture to mock the SimulationManager instance globally for all tests in this module.
    """
    with patch('virtual_hardware_lab.mcp_server_api.mcp_server.SimulationManager', autospec=True) as mock_manager_class:
        mock_instance = mock_manager_class.return_value
        with patch('virtual_hardware_lab.mcp_server_api.rpc_methods.set_rpc_globals') as mock_set_rpc_globals:
            yield mock_instance
        

@pytest.mark.asyncio
async def test_root_get():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Virtual Hardware Lab MCP Server is running!"}

@pytest.mark.asyncio
async def test_root_post_no_payload():
    response = client.post("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Virtual Hardware Lab MCP Server received a POST request!"}

@pytest.mark.asyncio
async def test_root_post_empty_dict_payload():
    response = client.post("/", json={})
    assert response.status_code == 200
    assert response.json() == {"message": "Virtual Hardware Lab MCP Server received a POST request!"}

@pytest.mark.asyncio
@patch('virtual_hardware_lab.mcp_server_api.mcp_server.rpc_methods.dispatch_jsonrpc')
async def test_jsonrpc_endpoint_success(mock_dispatch_jsonrpc):
    mock_dispatch_jsonrpc.return_value = (200, {"jsonrpc": "2.0", "result": "test_result", "id": "1"})
    payload = {"jsonrpc": "2.0", "method": "test_method", "id": "1"}
    response = client.post("/jsonrpc", json=payload)
    assert response.status_code == 200
    assert response.json() == {"jsonrpc": "2.0", "result": "test_result", "id": "1"}
    mock_dispatch_jsonrpc.assert_awaited_once_with(payload)

@pytest.mark.asyncio
@patch('virtual_hardware_lab.mcp_server_api.mcp_server.rpc_methods.dispatch_jsonrpc')
async def test_jsonrpc_endpoint_error(mock_dispatch_jsonrpc):
    mock_dispatch_jsonrpc.return_value = (500, {"jsonrpc": "2.0", "error": {"code": -32000, "message": "Server error"}, "id": "1"})
    payload = {"jsonrpc": "2.0", "method": "test_method", "id": "1"}
    response = client.post("/jsonrpc", json=payload)
    assert response.status_code == 500
    assert response.json() == {"jsonrpc": "2.0", "error": {"code": -32000, "message": "Server error"}, "id": "1"}
    mock_dispatch_jsonrpc.assert_awaited_once_with(payload)

@pytest.mark.asyncio
@patch('virtual_hardware_lab.mcp_server_api.mcp_server.rpc_methods.dispatch_jsonrpc')
async def test_jsonrpc_endpoint_returns_response_object(mock_dispatch_jsonrpc):
    mock_dispatch_jsonrpc.return_value = Response(status_code=202, content="Accepted")
    payload = {"jsonrpc": "2.0", "method": "test_method", "id": "1"}
    response = client.post("/jsonrpc", json=payload)
    assert response.status_code == 202
    assert response.text == "Accepted"
    mock_dispatch_jsonrpc.assert_awaited_once_with(payload)

@pytest.mark.asyncio
@patch('virtual_hardware_lab.mcp_server_api.mcp_server.rpc_methods.dispatch_jsonrpc')
async def test_jsonrpc_endpoint_no_content_204(mock_dispatch_jsonrpc):
    mock_dispatch_jsonrpc.return_value = (204, None)
    payload = {"jsonrpc": "2.0", "method": "notify_method"}
    response = client.post("/jsonrpc", json=payload)
    assert response.status_code == 204
    assert not response.content # Ensure no content for 204

@pytest.mark.asyncio
@patch('virtual_hardware_lab.mcp_server_api.mcp_server.rpc_methods.dispatch_jsonrpc')
async def test_root_post_with_jsonrpc_payload_success(mock_dispatch_jsonrpc):
    mock_dispatch_jsonrpc.return_value = (200, {"jsonrpc": "2.0", "result": "root_post_result", "id": "2"})
    payload = {"jsonrpc": "2.0", "method": "another_test_method", "id": "2"}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    assert response.json() == {"jsonrpc": "2.0", "result": "root_post_result", "id": "2"}
    mock_dispatch_jsonrpc.assert_awaited_once_with(payload)

@pytest.mark.asyncio
@patch('virtual_hardware_lab.mcp_server_api.mcp_server.rpc_methods.dispatch_jsonrpc')
async def test_root_post_with_jsonrpc_payload_returns_response_object(mock_dispatch_jsonrpc):
    mock_dispatch_jsonrpc.return_value = Response(status_code=202, content="Accepted by root post")
    payload = {"jsonrpc": "2.0", "method": "test_method", "id": "1"}
    response = client.post("/", json=payload)
    assert response.status_code == 202
    assert response.text == "Accepted by root post"
    mock_dispatch_jsonrpc.assert_awaited_once_with(payload)

@pytest.mark.asyncio
@patch('virtual_hardware_lab.mcp_server_api.mcp_server.rpc_methods.dispatch_jsonrpc')
async def test_root_post_with_jsonrpc_payload_no_content_204(mock_dispatch_jsonrpc):
    mock_dispatch_jsonrpc.return_value = (204, None)
    payload = {"jsonrpc": "2.0", "method": "notify_method"}
    response = client.post("/", json=payload)
    assert response.status_code == 204
    assert not response.content # Ensure no content for 204

