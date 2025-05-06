import streamlit as st
import json
from datetime import date
import os

DATA_FILE = "data.json"

# Load existing data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"events": {}}

# Save data to JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

# Streamlit UI
st.title("Event Registration Form")

with st.form("event_form"):
    full_name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=0, step=1)
    secrets = st.text_area("Secrets")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    event_date = st.date_input("Event Date")
    submit = st.form_submit_button("Submit")

    # Check if any field is empty
    if submit:
        key = event_date.isoformat()  # Use date only (YYYY-MM-DD)

        # Load and update data
        data = load_data()
        if not full_name or not age or not secrets or not email or not phone:
            st.error("All fields are required!")
        else:
            new_user = {
            "full_name": full_name,
            "age": age,
            "secrets": secrets,
            "email": email,
            "phone": phone,
            "event_date": event_date,
            "currency": 2000  # Add default currency
        }

            # Check if the event date already exists
            if event_date.isoformat() not in data["events"]:
                data["events"][event_date.isoformat()] = {
                    "players": [],  # Initialize players list
                    "notes": ""     # Initialize notes as an empty string
                }

            # Add the new player to the players list
            data["events"][event_date.isoformat()]["players"].append(new_user)

            # Save updated data
            save_data(data)
            st.success(f"Form Submitted!")
            st.balloons()
