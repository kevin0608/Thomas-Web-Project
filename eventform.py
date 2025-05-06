import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date
import json
import os

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("firebase_credentials.json")  # replace with your file name
        firebase_admin.initialize_app(cred)
        st.info("Firebase initialized successfully.")
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.stop()  # Stop the app if Firebase fails to initialize

# Initialize Firestore
db = firestore.client()

st.title("Event Registration Form")

with st.form("event_form"):
    full_name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=0, step=1)
    secrets = st.text_area("Secrets")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    event_date = st.date_input("Event Date")
    submit = st.form_submit_button("Submit")

    if submit:
        if not full_name or not age or not secrets or not email or not phone:
            st.error("All fields are required!")
        else:
            new_user = {
                "full_name": full_name,
                "age": age,
                "secrets": secrets,
                "email": email,
                "phone": phone,
                "event_date": str(event_date),
                "currency": 2000  # Set default currency for the user
            }

            event_key = event_date.isoformat()  # Use the event date as a key
            event_ref = db.collection("events").document(event_key)

            try:
                # Get existing event or create a new one if none exists
                event_doc = event_ref.get()
                if event_doc.exists:
                    event_data = event_doc.to_dict()
                    players = event_data.get("players", [])
                else:
                    players = []

                # Add the new user to the list of players
                players.append(new_user)

                # Update the event document with new player data
                event_ref.set({
                    "players": players,
                    "notes": event_doc.to_dict().get("notes", "") if event_doc.exists else ""  # Retain existing notes if available
                })

                st.success("Form Submitted!")
                st.balloons()  # Celebrate with balloons
            except Exception as e:
                st.error(f"Error submitting form: {e}")
