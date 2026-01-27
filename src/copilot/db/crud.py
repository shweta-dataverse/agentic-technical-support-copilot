# src/copilot/db/crud.py

from copilot.db.models import JiraTicket, Resolution

def save_ticket(db, ticket):
    db_ticket = JiraTicket(
        ticket_id=ticket.get("ticket_id"),
        title=ticket.get("title"),
        description=ticket.get("description"),
    )
    db.add(db_ticket)
    db.commit()


def save_resolution(db, ticket_id, content):
    db_res = Resolution(
        ticket_id=ticket_id,
        content=content,
    )
    db.add(db_res)
    db.commit()


def get_all_tickets(db):
    return db.query(JiraTicket).order_by(JiraTicket.created_at.desc()).all()


def get_resolution(db, ticket_id):
    return (
        db.query(Resolution)
        .filter(Resolution.ticket_id == ticket_id)
        .order_by(Resolution.created_at.desc())
        .first()
    )