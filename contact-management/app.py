"""app.py - the Flask backend for the contact manager.

Start it with:  python app.py   (or press F5 in VS Code)
The API runs at http://127.0.0.1:5000/
"""
import re
import subprocess
import sys

# Install Flask automatically the first time, so no setup steps are needed.
try:
    import flask  # noqa: F401
except ImportError:
    print("Installing Flask (first run only, needs internet)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask"])

from flask import Flask, jsonify, render_template, request

import database as db

app = Flask(__name__)

PHONE_RE = re.compile(r"^[0-9+\-() ]{7,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Create the database file and table when the app starts.
db.init_db()


@app.after_request
def allow_live_server(response):
    """Lets a page opened with VS Code Live Server (port 5500) talk to this API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


def clean_contact(data):
    """Trim and check the contact fields. Returns (contact, list_of_errors)."""
    if not isinstance(data, dict):
        data = {}
    contact = {key: str(data.get(key, "")).strip()
               for key in ("name", "phone", "email", "address")}
    errors = []

    if not 2 <= len(contact["name"]) <= 60:
        errors.append("Name must be 2-60 characters.")
    digits = sum(ch.isdigit() for ch in contact["phone"])
    if not PHONE_RE.match(contact["phone"]) or digits < 7:
        errors.append("Enter a valid phone number (7-20 digits, + - ( ) and spaces allowed).")
    if contact["email"] and (len(contact["email"]) > 100 or not EMAIL_RE.match(contact["email"])):
        errors.append("Enter a valid email address or leave it empty.")
    if len(contact["address"]) > 200:
        errors.append("Address must be 200 characters or fewer.")
    return contact, errors


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/contacts", methods=["GET"])
def list_contacts():
    search = request.args.get("q", "").strip()[:60]
    return jsonify({"contacts": db.get_contacts(search)})


@app.route("/api/contacts", methods=["POST"])
def create_contact():
    contact, errors = clean_contact(request.get_json(silent=True))
    if errors:
        return jsonify({"errors": errors}), 400
    new_id = db.add_contact(**contact)
    return jsonify({"message": "Contact added successfully.",
                    "contact": db.get_contact(new_id)}), 201


@app.route("/api/contacts/<int:contact_id>", methods=["PUT"])
def edit_contact(contact_id):
    contact, errors = clean_contact(request.get_json(silent=True))
    if errors:
        return jsonify({"errors": errors}), 400
    if not db.update_contact(contact_id, **contact):
        return jsonify({"errors": ["Contact not found."]}), 404
    return jsonify({"message": "Contact updated successfully.",
                    "contact": db.get_contact(contact_id)})


@app.route("/api/contacts/<int:contact_id>", methods=["DELETE"])
def remove_contact(contact_id):
    if not db.delete_contact(contact_id):
        return jsonify({"errors": ["Contact not found."]}), 404
    return jsonify({"message": "Contact deleted successfully."})


if __name__ == "__main__":
    # use_reloader=False keeps the VS Code debugger (F5) working properly.
    app.run(debug=True, use_reloader=False)
