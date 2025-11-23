
from typing import Optional, Union
from pydantic import BaseModel, Field

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
