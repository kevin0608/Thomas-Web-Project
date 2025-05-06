import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date
import json
import os

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("/Users/Kevin/Streamlit Thomas Project/thomas-web-eb178-firebase-adminsdk-fbsvc-e8cce9c266.json")  # replace with your file path
        firebase_admin.initialize_app(cred)
        st.info("Firebase initialized successfully.")
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.stop()  # Stop the app if Firebase fails to initialize

# Validate Firestore client
db = firestore.client()
st.write(f"Firestore client initialized: {db}")

# Set up the Streamlit app
st.title("Event Registration Form")

# Create a form for event registration
with st.form("event_form"):
    full_name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=0, step=1)
    secrets = st.text_area("Secrets")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    event_date = st.date_input("Event Date")
    submit = st.form_submit_button("Submit")

    if submit:
        # Ensure that all fields are filled out
        if not full_name or not age or not secrets or not email or not phone:
            st.error("All fields are required!")
        else:
            new_user = {
                "full_name": full_name,
                "age": age,
                "secrets": secrets,
                "email": email,
                "phone": phone,
                "event_date": str(event_date),  # Convert date to string format
                "currency": 2000  # Set default currency for the user
            }

            # Use event date as a unique key for the event document
            event_key = event_date.isoformat()  # Ensure that event_key is a valid string
            event_ref = db.collection("events").document(event_key)

            try:
                # Fetch the existing event document or create a new one
                event_doc = event_ref.get()
                if event_doc.exists:
                    event_data = event_doc.to_dict()
                    players = event_data.get("players", [])
                else:
                    players = []

                # Append the new user to the players list
                players.append(new_user)

                # Update the event document with the new list of players and any existing notes
                event_ref.set({
                    "players": players,
                    "notes": event_doc.to_dict().get("notes", "") if event_doc.exists else ""  # Retain existing notes if present
                })

                # Success message and balloons to celebrate the form submission
                st.success("Form Submitted!")
                st.balloons()  # Celebrate with balloons

            except Exception as e:
                st.error(f"Error submitting form: {e}")  # Handle any errors during Firestore interaction
                st.write(f"Exception details: {e}")
