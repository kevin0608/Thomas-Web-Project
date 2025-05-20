import streamlit as st
import pandas as pd
from datetime import datetime, date
import altair as alt
import firebase_admin
from firebase_admin import credentials, firestore
import json
from matplotlib.colors import to_rgb

# Initialize Firebase only once
if not firebase_admin._apps:
    cred_dict = json.loads(st.secrets["firebase"]["credentials"])
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()
ACCESS_CODE = "2706"
st.set_page_config(page_title="Admin Dashboard", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# CSS
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

# Firebase functions
def load_event_data(event_date_str):
    doc_ref = db.collection("events").document(event_date_str)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else {"players": [], "notes": "", "currency_pot": 0}

def save_event_data(event_date_str, data):
    db.collection("events").document(event_date_str).set(data)

def update_players(event_date_str, new_players):
    db.collection("events").document(event_date_str).update({"players": new_players})

# Login flow
if not st.session_state.logged_in:
    st.title("Enter Access Code")
    code_input = st.text_input("", type="password", placeholder="Enter code", max_chars=6, key="code_input", label_visibility="collapsed")
    if st.button("Enter", key="login_button"):
        if code_input == ACCESS_CODE:
            st.session_state.logged_in = True
            st.success("Login successful! Redirecting...")
            st.balloons()
            st.rerun()
        else:
            st.error("Invalid code. Please try again.")
    st.stop()

# Logged-in view
st.sidebar.markdown("### Welcome Mr. Gom !")
page = st.sidebar.radio("📂 Navigation", ["Calendar", "Event"])

event_docs = db.collection("events").list_documents()
event_dates = sorted([doc.id for doc in event_docs])

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

    # Total player card
    st.markdown(f"""
        <div style="padding: 0.75rem; background: linear-gradient(to right, #667eea, #764ba2, #ff512f); color: white; border-radius: 0.75rem; text-align: center; width: 160px; margin: auto;">
            <h4 style="margin: 0; font-size: 0.85rem;">Total Players</h4>
            <p style="font-size: 1.5rem; margin: 0; font-weight: 600;">{len(players)}</p>
        </div>
    """, unsafe_allow_html=True)

    show_dataframe = st.checkbox("Show data as table")

    if show_dataframe:
        if players:
            df = pd.DataFrame([{
                "Name": p.get("name", ""),
                "Age": p.get("age", ""),
                "Email": p.get("email", ""),
                "Phone": p.get("phone", ""),
                "Secrets": p.get("secrets", ""),
                "Currency": p.get("currency", 2000)
            } for p in players])
            st.dataframe(df)
        else:
            st.warning("No players found.")
    else:
        for i, player in enumerate(players, 1):
            key_prefix = f"{i}_{selected_date_str}"
            edit_name_key = f"edit_name_mode_{key_prefix}"
            if edit_name_key not in st.session_state:
                st.session_state[edit_name_key] = False

            with st.expander(f"{i}. {player.get('name', 'No Name')}"):
                if not st.session_state[edit_name_key]:
                    st.write(f"**Age:** {player.get('age', '')}")
                    st.write(f"**Email:** {player.get('email', '')}")
                    st.write(f"**Phone:** {player.get('phone', '')}")
                    st.write(f"**Secrets:** {player.get('secrets', '')}")
                    st.write(f"**Currency:** {player.get('currency', 2000)}")

                    player_note_key = f"note_player_{key_prefix}"
                    default_note = player.get("note", "")
                    st.text_area("Player Note", key=player_note_key, value=default_note, height=100)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Edit Name", key=f"edit_name_btn_{key_prefix}"):
                            st.session_state[edit_name_key] = True
                            st.rerun()
                    with col2:
                        if st.button("Save Note", key=f"save_note_btn_{key_prefix}"):
                            event_data["players"][i - 1]["note"] = st.session_state[player_note_key]
                            save_event_data(selected_date_str, event_data)
                            st.success("Note saved!")
                            st.rerun()
                    with col3:
                        if st.button("Delete Player", key=f"delete_btn_{key_prefix}"):
                            new_players = [p for j, p in enumerate(players) if j != i - 1]
                            update_players(selected_date_str, new_players)
                            st.success(f"Deleted {player.get('name', '')}")
                            st.rerun()
                else:
                    new_name = st.text_input("Edit Name", value=player.get("name", ""), key=f"name_input_{key_prefix}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save", key=f"save_name_btn_{key_prefix}"):
                            players[i - 1]["name"] = new_name
                            event_data["players"] = players
                            save_event_data(selected_date_str, event_data)
                            st.session_state[edit_name_key] = False
                            st.success(f"Name updated to {new_name}")
                            st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_name_btn_{key_prefix}"):
                            st.session_state[edit_name_key] = False
                            st.rerun()

        st.subheader("📓 Notes Space")
        note_input = st.text_area("Write notes for this event date here...", value=note)
        if st.button("💾 Save Notes"):
            event_data["notes"] = note_input
            save_event_data(selected_date_str, event_data)
            st.success("Notes saved.")

elif page == "Event":
    col1, col2 = st.columns([3, 1])
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
        df = pd.DataFrame([{
            "Player": p.get("name", ""),
            "Currency": p.get("currency", 2000)
        } for p in players])

        custom_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        players_list = sorted(df['Player'].unique())
        color_scale = alt.Scale(domain=players_list, range=custom_colors[:len(players_list)])

        chart = alt.Chart(df).mark_bar(size=15).encode(
            x=alt.X('Currency:Q'),
            y=alt.Y('Player:N', sort='-x'),
            color=alt.Color('Player:N', scale=color_scale, legend=None),
            tooltip=["Player", "Currency"]
        )

        st.markdown("""
            <style>
                .tile {
                    background: linear-gradient(to right, #ff512f, #dd2476);
                    color: white;
                    padding: 5px;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: bold;
                    margin: 10px auto;
                    text-align: center;
                    width: 300px;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="tile">Current Currency Pot:<br>{currency_pot}</div>', unsafe_allow_html=True)
        st.altair_chart(chart, use_container_width=True)

        def get_font_color(bg):
            r, g, b = to_rgb(bg)
            brightness = r*0.299 + g*0.587 + b*0.114
            return "#000" if brightness > 0.6 else "#fff"

        for i, player in enumerate(players, 1):
            name = player.get("name", "No Name")
            current = player.get("currency", 2000)
            color = custom_colors[(i - 1) % len(custom_colors)]
            font_color = get_font_color(color)

            st.write(f"**{name}** : {current}")
            with st.expander("Adjust Currency", expanded=False):
                lose = st.number_input("Lose", min_value=0, value=0, key=f"lose_{i}")
                gain = st.number_input("Gain", min_value=0, value=0, key=f"gain_{i}")

                if st.button("Update", key=f"update_currency_{i}"):
                    net_change = gain - lose
                    new_total = max(0, current + net_change)
                    players[i - 1]["currency"] = new_total
                    event_data["players"] = players
                    event_data["currency_pot"] += gain
                    save_event_data(selected_date_str, event_data)
                    st.success(f"{name}'s currency updated.")
                    st.rerun()
