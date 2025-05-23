import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.message import EmailMessage
from datetime import date
import json


# Initialize Firebase app only if not already initialized
if not firebase_admin._apps:
    cred_dict = json.loads(st.secrets["firebase"]["credentials"])
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

# Now get the Firestore client
db = firestore.client()
# --- Email Function ---
def send_confirmation_email(to_email, user_name, event_date):
    email_address = st.secrets["email"]["address"]
    email_password = st.secrets["email"]["password"]

    msg = EmailMessage()
    msg["Subject"] = "Event Booking!"
    msg["From"] = "Tom Gom"
    msg["To"] = to_email
    msg.set_content(f"""
    Hi {user_name},

    Thank you for registering for the event on {event_date}.
    We're excited to have you with us!

    Best regards,  
    Gom 
    """)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"Failed to send confirmation email: {e}")

# --- Streamlit UI ---
st.title("Event Registration Form")


with st.form("event_form"):
    full_name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=0, step=1)
    secrets = st.text_area("Secret")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    event_date = st.date_input("Event Date", min_value=date.today())
    submit = st.form_submit_button("Submit")

    import re

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

if submit:
    if not full_name or not age or not secrets or not email or not phone:
        st.error("All fields are required!")
    elif not is_valid_email(email):
        st.error("Please enter a valid email address!")
    else:
        doc_id = event_date.isoformat()
        event_ref = db.collection("events").document(doc_id)

        try:
            doc = event_ref.get()
            if not doc.exists:
                event_ref.set({"players": []})
                players = []
            else:
                players = doc.to_dict().get("players", [])

            email_exists = any(
                p.get("email", "").strip().lower() == email.strip().lower()
                for p in players
            )

            if email_exists:
                st.error(f"The email **{email}** is already registered for this event date.")
            else:
                event_ref.update({
                    "players": firestore.ArrayUnion([{
                        "name": full_name,
                        "age": age,
                        "secrets": secrets,
                        "email": email,
                        "phone": phone
                    }])
                })
                send_confirmation_email(email, full_name, event_date)
                st.success("✅ Registration successful!")
                st.balloons()

        except Exception as e:
            st.error(f"❌ Error saving to Firestore: {e}")
