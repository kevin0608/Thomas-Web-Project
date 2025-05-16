import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt
import firebase_admin
from firebase_admin import credentials, firestore
import json


# Initialize Firebase app only if not already initialized
if not firebase_admin._apps:
    cred_dict = json.loads(st.secrets["firebase"]["credentials"])
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

# Now get the Firestore client
db = firestore.client()

ACCESS_CODE = "2706"

# Instead of JSON file, we use Firestore document for storing data
DATA_DOC = "admin_dashboard/data"  # Firestore document path

# Load data from Firestore
def load_data():
    doc_ref = db.document(DATA_DOC)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        # Return initial empty structure
        return {"events": {}}

# Save data to Firestore
def save_data(data):
    doc_ref = db.document(DATA_DOC)
    doc_ref.set(data)

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Login logic remains same
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.markdown("""
    <style>
        .stTextInput > div > div > input {
            width: 100px;  
            margin: 0 auto;  
            display: block;
        }
        .stButton > button {
            margin: 0 auto;  
            display: block;
        }
        .stContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get('logged_in', False):
    st.title("Enter Access Code")
    
    with st.container():
        code_input = st.text_input("", type="password", key="code_input", label_visibility="collapsed", placeholder="Enter code", help="Enter your access code here", max_chars=6)

    if st.button("Enter", key="login_button"):
        if code_input == ACCESS_CODE:
            st.session_state.logged_in = True
            st.success("Login successful! Redirecting...")
            st.balloons()
            st.experimental_rerun()
        else:
            st.error("Invalid code. Please try again.")

else:
    st.title("My Dashboard")
    st.divider()
    st.sidebar.markdown("### Welcome Mr. Gom !")
    page = st.sidebar.radio("📂 Navigation", ["Calendar", "Event"])

    # Load event data from Firestore
    data = load_data()

    if page == "Calendar":
        event_dates = list(data.get("events", {}).keys())
        event_dates.sort()

        if not event_dates:
            st.info("No events found.")
            st.stop()

        date_objects = [datetime.strptime(d, "%Y-%m-%d").date() for d in event_dates]
        selected_date = st.selectbox("Select a booked event date:", date_objects)

        selected_date_str = selected_date.isoformat()
        event_data = data["events"].get(selected_date_str, {})

        players = event_data.get("players", [])
        note = event_data.get("notes", "")

        with st.container():
            st.markdown(f"""
                <div style="padding: 0.75rem; background: linear-gradient(to right, #667eea, #764ba2, #ff512f); color: white; border-radius: 0.75rem; text-align: center; width: 160px; margin: auto;">
                    <h4 style="margin: 0; font-size: 0.85rem;">Total Players</h4>
                    <p style="font-size: 1.5rem; margin: 0; font-weight: 600;">{len(players)}</p>
                </div>
            """, unsafe_allow_html=True)

        show_dataframe = st.checkbox("Show data as table")
        
        if show_dataframe:
            if players:
                player_data = [{
                    "Full Name": player['full_name'],
                    "Age": player['age'],
                    "Email": player['email'],
                    "Phone": player['phone'],
                    "Secrets": player['secrets'],
                    "Currency": player['currency']
                } for player in players]

                df = pd.DataFrame(player_data)
                st.dataframe(df)
            else:
                st.warning("No players found for this date.")
        else:
            if players:
                for i, player in enumerate(players, 1):
                    with st.expander(f"{i}. {player['full_name']}"):
                        st.write(f"**Age:** {player['age']}")
                        st.write(f"**Email:** {player['email']}")
                        st.write(f"**Phone:** {player['phone']}")
                        st.write(f"**Secrets:** {player['secrets']}")
                        st.write(f"**Currency:** {player.get('currency', 2000)}")
                        
                        if st.button(f"Delete Player {i}", key=f"delete_{i}_{selected_date_str}"):
                            players = [p for p in players if p["full_name"] != player["full_name"]]
                            data["events"][selected_date_str]["players"] = players
                            save_data(data)
                            st.success(f"Deleted {player['full_name']}")
                            st.rerun()

            st.subheader("📓Notes Space")
            note_input = st.text_area("Write notes for this event date here...", value=note)

            if st.button("💾 Save Notes"):
                data["events"][selected_date_str]["notes"] = note_input
                save_data(data)
                st.success("Notes saved successfully!")

    elif page == "Event":
        st.subheader("Event Players")
        event_dates = list(data.get("events", {}).keys())
        event_dates.sort()

        if not event_dates:
            st.info("No events found.")
            st.stop()

        selected_date = st.selectbox("Select a booked event date for the event", event_dates)
        event_data = data["events"].get(selected_date, {})

        players = event_data.get("players", [])

        bar_data = pd.DataFrame([
            {"Player": p["full_name"], "Currency": p.get("currency", 2000)}
            for p in players
        ])

        stacked_bar_chart = alt.Chart(bar_data).mark_bar().encode(
            x='Currency:Q',
            y='Player:N',
            color='Player:N',
            tooltip=["Player", "Currency"]
        ).properties(
            title="Players Currency Overview"
        )

        st.altair_chart(stacked_bar_chart, use_container_width=True)

        if players:
            currency_pot = event_data.get("currency_pot", 0)
            tile_style = """
                <style>
                .tile-container {
                    display: flex;
                    justify-content: center;
                }

                .tile {
                    background: linear-gradient(to right, #ff512f, #dd2476, #00bcd4, #8e44ad, #f39c12);
                    color: white;   
                    padding: 5px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    font-size: 15px;
                    font-weight: bold;
                    margin: 10px;
                    text-align: center;
                    width: 1200px;
                }
                </style>
            """
            st.markdown(tile_style, unsafe_allow_html=True)
            st.markdown(f'<div class="tile-container"><div class="tile">Current Currency Pot:<br>{currency_pot}</div></div>', unsafe_allow_html=True)

            for i, player in enumerate(players, 1):
                current_currency = player.get("currency", 2000)
                bar_df = pd.DataFrame({
                    "Player": [player['full_name']],
                    "Currency": [current_currency]
                })

                bar = alt.Chart(bar_df).mark_bar(
                    color="#FF6F00",
                    size=40
                ).encode(
                    x=alt.X('Currency:Q', scale=alt.Scale(domain=[0, 16000])),
                    y=alt.Y('Player:N')
                ).properties(
                    height=60
                )

                st.write(f"**{player['full_name']}** - Currency: {current_currency}")

                with st.expander(f"Adjust Currency for {player['full_name']}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        lose_currency = st.number_input(f"Amount to deduct for {player['full_name']}", min_value=0, value=0)
                        if st.button(f"❌ Deduct Currency for {player['full_name']}", key=f"lose_{player['full_name']}"):
                            if lose_currency > current_currency:
                                st.warning(f"Cannot deduct more currency than {player['full_name']} has!")
                            else:
                                new_currency = current_currency - lose_currency
                                currency_pot += lose_currency
                                data["events"][selected_date]["players"][i - 1]["currency"] = new_currency
                                data["events"][selected_date]["currency_pot"] = currency_pot
                                save_data(data)
                                st.success(f"{lose_currency} currency deducted from {player['full_name']}.")
                                st.rerun()

                    with col2:
                        add_currency = st.number_input(f"Amount to add for {player['full_name']}", min_value=0, value=0)
                        if st.button(f"✅ Add Currency to {player['full_name']}", key=f"add_{player['full_name']}"):
                            if add_currency > currency_pot:
                                st.warning(f"Not enough currency in the pot to add {add_currency} to {player['full_name']}.")
                            else:
                                new_currency = current_currency + add_currency
                                currency_pot -= add_currency
                                data["events"][selected_date]["players"][i - 1]["currency"] = new_currency
                                data["events"][selected_date]["currency_pot"] = currency_pot
                                save_data(data)
                                st.success(f"{add_currency} currency added to {player['full_name']}.")
                                st.rerun()