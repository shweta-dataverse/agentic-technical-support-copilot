from dataclasses import dataclass, field
from typing import List, Optional, Literal
from datetime import datetime

# define allowed types to ensure data integrity
TicketStatus = Literal["open", "in_progress", "resolved", "closed"]
TicketPriority = Literal["low", "medium", "high", "critical"]
S7Component = Literal["cpu", "power_supply", "et200sp", "tia_portal", "communication_module"]

@dataclass
class JiraComment:
    author: str  # customer or engineer
    message: str
    created_at: datetime

@dataclass
class JiraTicket:
    ticket_id: str
    title: str
    description: str
    
    # use a default factory to ensure a new list is created for every ticket
    comments: List[JiraComment] = field(default_factory=list)

    status: TicketStatus
    priority: TicketPriority
    component: S7Component

    # technical metadata for industrial diagnostics [1]
    error_code: Optional[str] = None 
    tags: List[str] = field(default_factory=list)
    resolution_summary: Optional[str] = None

    created_at: datetime
    updated_at: datetime