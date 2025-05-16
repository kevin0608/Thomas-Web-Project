import streamlit as st
import pandas as pd
from datetime import datetime, date
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

db = firestore.client()

ACCESS_CODE = "2706"

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Session login state
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

def load_event_data(event_date_str):
    doc_ref = db.collection("events").document(event_date_str)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        # Default empty structure for new event date
        return {"players": [], "notes": "", "currency_pot": 0}

def save_event_data(event_date_str, data):
    doc_ref = db.collection("events").document(event_date_str)
    doc_ref.set(data)

def update_players(event_date_str, new_players):
    doc_ref = db.collection("events").document(event_date_str)
    doc_ref.update({"players": new_players})

if not st.session_state.logged_in:
    st.title("Enter Access Code")
    with st.container():
        code_input = st.text_input("", type="password", key="code_input", label_visibility="collapsed", placeholder="Enter code", help="Enter your access code here", max_chars=6)

    if st.button("Enter", key="login_button"):
        if code_input == ACCESS_CODE:
            st.session_state.logged_in = True
            st.success("Login successful! Redirecting...")
            st.balloons()
            st.rerun()
        else:
            st.error("Invalid code. Please try again.")

else:
    st.sidebar.markdown("### Welcome Mr. Gom !")
    page = st.sidebar.radio("📂 Navigation", ["Calendar", "Event"])

    # Load all event dates from Firestore collection 'events'
    # Note: Firestore collection list must be fetched via list_documents()
    event_docs = db.collection("events").list_documents()
    event_dates = [doc.id for doc in event_docs]
    event_dates.sort()

    if page == "Calendar":
        st.title("My Dashboard")
        st.divider()
        if not event_dates:
            st.info("No events found.")
            st.stop()

        date_objects = [datetime.strptime(d, "%Y-%m-%d").date() for d in event_dates]
        selected_date = st.selectbox("Select a booked event date:", date_objects)
        selected_date_str = selected_date.isoformat()

        event_data = load_event_data(selected_date_str)
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
                    "Name": player.get('name', ''),
                    "Age": player.get('age', ''),
                    "Email": player.get('email', ''),
                    "Phone": player.get('phone', ''),
                    "Secrets": player.get('secrets', ''),
                    "Currency": player.get('currency', 2000)
                } for player in players]

                df = pd.DataFrame(player_data)
                st.dataframe(df)
            else:
                st.warning("No players found for this date.")
        else:
            if players:
                for i, player in enumerate(players, 1):
                    with st.expander(f"{i}. {player.get('name', 'No Name')}"):
                        st.write(f"**Age:** {player.get('age', '')}")
                        st.write(f"**Email:** {player.get('email', '')}")
                        st.write(f"**Phone:** {player.get('phone', '')}")
                        st.write(f"**Secrets:** {player.get('secrets', '')}")
                        st.write(f"**Currency:** {player.get('currency', 2000)}")

                        # Load existing note for this player from data (not session_state) for fresh data each run
                        player_note_key = f"note_player_{i}_{selected_date_str}"
                        if player_note_key not in st.session_state:
                            st.session_state[player_note_key] = player.get("note", "")

                        note_text = st.text_area(
                            "Player Note",
                            value=st.session_state[player_note_key],
                            key=player_note_key,
                            height=100,
                            placeholder="Add notes about this player here..."
                        )

                        if st.button(f"💾 Save Note for {player.get('name', 'No Name')}", key=f"save_note_{i}_{selected_date_str}"):
                            # Update note in event_data using session state value from textarea
                            event_data["players"][i-1]["note"] = st.session_state[player_note_key]
                            save_event_data(selected_date_str, event_data)

                            st.success("Player note saved!")
                            st.rerun()

                        if st.button(f"Delete Player {i}", key=f"delete_{i}_{selected_date_str}"):
                            new_players = [p for idx, p in enumerate(players) if idx != i-1]
                            update_players(selected_date_str, new_players)
                            st.success(f"Deleted {player.get('name', 'player')}")
                            st.rerun()

                st.subheader("📓Notes Space")
                note_input = st.text_area("Write notes for this event date here...", value=note)

                if st.button("💾 Save Notes"):
                    event_data["notes"] = note_input
                    save_event_data(selected_date_str, event_data)
                    st.success("Notes saved successfully!")

    elif page == "Event":
        col1, col2 = st.columns([3, 1])  # Adjust width ratio as needed

        with col1:
            st.subheader("")

        with col2:
            if not event_dates:
                st.info("No events found.")
                st.stop()

            selected_date_str = st.selectbox("Select Event Date", event_dates)
        event_data = load_event_data(selected_date_str)
        players = event_data.get("players", [])
        currency_pot = event_data.get("currency_pot", 0)

        if players:
            # Example bar_data, replace with your players list
            bar_data = pd.DataFrame([
                {"Player": p.get("name", ""), "Currency": p.get("currency", 2000)}
                for p in players
            ])

            # Define a large enough palette (here 40 distinct colors)
            custom_colors = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
                '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173',
                '#5254a3', '#9c9ede', '#e7ba52', '#e7969c', '#a55194',
                '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3',
                '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd',
                '#ccebc5', '#ffed6f', '#66c2a5', '#fc8d62', '#8da0cb',
                '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3'
            ]

            players_list = sorted(bar_data['Player'].unique())
            color_scale = alt.Scale(domain=players_list, range=custom_colors[:len(players_list)])

            stacked_bar_chart = alt.Chart(bar_data).mark_bar(size=15).encode(
            x=alt.X('Currency:Q', axis=alt.Axis(title=None)),
            y=alt.Y('Player:N', axis=alt.Axis(title=None), sort=alt.EncodingSortField(field="Currency", order="descending")),
            color=alt.Color('Player:N', scale=color_scale, legend=None),
            tooltip=["Player", "Currency"]
        )

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
                    width: 600px;
                }
                </style>
            """
            st.markdown(tile_style, unsafe_allow_html=True)
            st.markdown(f'<div class="tile-container"><div class="tile">Current Currency Pot:<br>{currency_pot}</div></div>', unsafe_allow_html=True)

            st.altair_chart(stacked_bar_chart, use_container_width=True)

            for i, player in enumerate(players, 1):
                current_currency = player.get("currency", 2000)
                st.write(f"**{player.get('name', 'No Name')}** : {current_currency}")

                st.markdown("""
                <style>
                /* Reduce padding inside the expander container */
                [data-testid="stExpander"] > div {
                    padding-top: 4px !important;
                    padding-bottom: 4px !important;
                }

                /* Reduce margin around the expander header */
                [data-testid="stExpander"] > div > div {
                    margin-bottom: 0 !important;
                    margin-top: 0 !important;
                }
                </style>
                """, unsafe_allow_html=True)

                with st.expander(""):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        lose_currency = st.number_input(f"", min_value=0, value=0, key=f"lose_{i}")
                        if st.button(f"−", key=f"lose_btn_{i}"):
                            if lose_currency > current_currency:
                                st.warning(f"Cannot deduct more currency than {player.get('name', 'No Name')} has!")
                            else:
                                new_currency = current_currency - lose_currency
                                currency_pot += lose_currency
                                players[i - 1]["currency"] = new_currency
                                event_data["players"] = players
                                event_data["currency_pot"] = currency_pot
                                save_event_data(selected_date_str, event_data)
                                st.success(f"{lose_currency} currency deducted from {player.get('name', 'No Name')}.")
                                st.rerun()

                    with col2:
                        add_currency = st.number_input(f"", min_value=0, value=0, key=f"add_{i}")
                        if st.button(f"✚", key=f"add_btn_{i}"):
                            if add_currency > currency_pot:
                                st.warning(f"Not enough currency in the pot to add {add_currency} to {player.get('name', 'No Name')}.")
                            else:
                                new_currency = current_currency + add_currency
                                currency_pot -= add_currency
                                players[i - 1]["currency"] = new_currency
                                event_data["players"] = players
                                event_data["currency_pot"] = currency_pot
                                save_event_data(selected_date_str, event_data)
                                st.success(f"{add_currency} currency added to {player.get('name', 'No Name')}.")
                                st.rerun()
        else:
            st.warning("No players found for this event date.")
