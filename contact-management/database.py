"""database.py - all SQLite code for the contact manager.

Every query uses ? placeholders so typed text can never run as SQL.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# The database file is created next to this script.
DB_PATH = Path(__file__).with_name("contacts.db")


@contextmanager
def get_db():
    """Open a connection, save changes if all went well, always close it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dictionaries
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create the contacts table if it does not exist yet."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                phone   TEXT NOT NULL,
                email   TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT ''
            )
            """
        )


def get_contacts(search=""):
    """Return all contacts, or only those matching a name / phone number."""
    with get_db() as conn:
        if search:
            like = f"%{search}%"
            rows = conn.execute(
                "SELECT * FROM contacts WHERE name LIKE ? OR phone LIKE ? "
                "ORDER BY name COLLATE NOCASE",
                (like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contacts ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [dict(row) for row in rows]


def get_contact(contact_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        return dict(row) if row else None


def add_contact(name, phone, email, address):
    """Save a new contact and return its new id."""
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO contacts (name, phone, email, address) VALUES (?, ?, ?, ?)",
            (name, phone, email, address),
        )
        return cur.lastrowid


def update_contact(contact_id, name, phone, email, address):
    """Change a contact. Returns True if it existed."""
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE contacts SET name = ?, phone = ?, email = ?, address = ? WHERE id = ?",
            (name, phone, email, address, contact_id),
        )
        return cur.rowcount > 0


def delete_contact(contact_id):
    """Delete a contact. Returns True if it existed."""
    with get_db() as conn:
        cur = conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        return cur.rowcount > 0
