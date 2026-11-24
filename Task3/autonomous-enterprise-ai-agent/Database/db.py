from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any
from uuid import uuid4

DB_PATH = Path(os.getenv("DATABASE_PATH", Path(__file__).resolve().parents[1] / "enterprise.db"))


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect()) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY,
                product_id TEXT NOT NULL UNIQUE,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity >= 0)
            );
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY,
                lead_id TEXT NOT NULL UNIQUE,
                customer TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                ticket_id TEXT NOT NULL UNIQUE,
                customer TEXT NOT NULL,
                issue TEXT NOT NULL,
                status TEXT NOT NULL,
                idempotency_key TEXT UNIQUE
            );
            """
        )
        ticket_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(tickets)").fetchall()
        }
        if "idempotency_key" not in ticket_columns:
            connection.execute("ALTER TABLE tickets ADD COLUMN idempotency_key TEXT")
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS tickets_idempotency_key "
                "ON tickets (idempotency_key)"
            )
        if connection.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO inventory (product_id, product_name, quantity) VALUES (?, ?, ?)",
                [
                    ("P101", "Dell Laptop", 25),
                    ("P102", "HP Laptop", 15),
                    ("P103", "Lenovo Laptop", 30),
                    ("P104", "Wireless Mouse", 42),
                    ("P105", "USB-C Dock", 12),
                ],
            )
        if connection.execute("SELECT COUNT(*) FROM leads").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO leads (lead_id, customer, status) VALUES (?, ?, ?)",
                [
                    ("L101", "Rahul", "New"),
                    ("L102", "Priya", "Contacted"),
                    ("L103", "Arjun", "Qualified"),
                ],
            )


def seed_data() -> None:
    initialize_database()


def _records(query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    initialize_database()
    with closing(_connect()) as connection:
        return [dict(row) for row in connection.execute(query, parameters).fetchall()]


def get_inventory(search: str | None = None) -> list[dict[str, Any]]:
    if not search:
        return _records("SELECT product_id, product_name, quantity FROM inventory ORDER BY product_id")
    term = f"%{search.strip()}%"
    return _records(
        """
        SELECT product_id, product_name, quantity FROM inventory
        WHERE product_id LIKE ? COLLATE NOCASE OR product_name LIKE ? COLLATE NOCASE
        ORDER BY product_id
        """,
        (term, term),
    )


def get_leads() -> list[dict[str, Any]]:
    return _records("SELECT lead_id, customer, status FROM leads ORDER BY lead_id")


def update_lead(lead_id: str, status: str) -> dict[str, Any] | None:
    initialize_database()
    with closing(_connect()) as connection, connection:
        cursor = connection.execute(
            "UPDATE leads SET status = ? WHERE lead_id = ? COLLATE NOCASE",
            (status, lead_id.strip()),
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute(
            "SELECT lead_id, customer, status FROM leads WHERE lead_id = ? COLLATE NOCASE",
            (lead_id.strip(),),
        ).fetchone()
        return dict(row) if row else None


def get_tickets() -> list[dict[str, Any]]:
    return _records(
        "SELECT ticket_id, customer, issue, status FROM tickets ORDER BY rowid DESC"
    )


def create_ticket(
    customer: str,
    issue: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    initialize_database()
    with closing(_connect()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if idempotency_key:
            existing = connection.execute(
                """
                SELECT ticket_id, customer, issue, status FROM tickets
                WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            ).fetchone()
            if existing:
                return dict(existing)
        ticket_id = f"TKT-{uuid4().hex[:8].upper()}"
        connection.execute(
            """
            INSERT INTO tickets (ticket_id, customer, issue, status, idempotency_key)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, customer.strip(), issue.strip(), "Open", idempotency_key),
        )
    return {
        "ticket_id": ticket_id,
        "customer": customer.strip(),
        "issue": issue.strip(),
        "status": "Open",
    }