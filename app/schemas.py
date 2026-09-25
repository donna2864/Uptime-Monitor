from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
class MonitorCreate(BaseModel):
    name : str
    url: HttpUrl
    interval_seconds: int = Field(default=60, ge=10)

class MonitorUpdate(BaseModel):
    name: str|None = None
    url: HttpUrl | None = None
    interval_seconds :int |None = Field(default=None, ge=10)
    active: bool | None = None

class MonitorResponse(BaseModel):
    id : int
    name : str
    url : str
    interval_seconds : int 
    active : bool

    class Config:
        from_attributes = True

class CheckResultResponse(BaseModel):
    id: int
    monitor_id : int
    checked_at: datetime
    status_code : int | None
    response_time_ms : float | None
    is_up : bool
    error_message : str | None

    class Config:
        from_attributes = True

class MonitorStatusResponse(BaseModel):
    monitor_id: int
    name: str
    url: str
    current_status: str
    uptime_percentage: float
    average_response_time_ms: float|None
    total_checks: int
    failed_checks: int