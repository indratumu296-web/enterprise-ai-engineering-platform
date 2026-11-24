from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LeadStatus = Literal["New", "Contacted", "Qualified", "Converted", "Lost"]


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class TicketCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer: str = Field(min_length=1, max_length=120)
    issue: str = Field(min_length=3, max_length=1000)