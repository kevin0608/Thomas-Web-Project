import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import altair as alt

DATA_FILE = "data.json"

# Define your access code
ACCESS_CODE = "2206"  # Change this to your own secret code

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

# Main interface
st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Check if user is logged in
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Custom CSS to style the input and center it
st.markdown("""
    <style>
        /* Style the input to make it smaller and center it */
        .stTextInput > div > div > input {
            width: 100;  /* Set the width of the input box */
            margin: 0 auto;  /* Center the input box */
            display: block;
        }
        /* Style the button to center it */
        .stButton > button {
            margin: 0 auto;  /* Center the button */
            display: block;
        }
        /* Optional: Style the container to center everything */
        .stContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
    </style>
""", unsafe_allow_html=True)

# Login Section
if not st.session_state.get('logged_in', False):
    st.title("Enter Access Code")
    
    # Centered input field with smaller size
    with st.container():
        code_input = st.text_input("", type="password", key="code_input", label_visibility="collapsed", placeholder="Enter code", help="Enter your access code here", max_chars=6)

    # Centered button
    if st.button("Enter", key="login_button"):
        if code_input == ACCESS_CODE:
            st.session_state.logged_in = True
            st.success("Login successful! Redirecting...")
            st.rerun()  # Redirect to the main app after login
            st.balloons()
        else:
            st.error("Invalid code. Please try again.")
else:
    # Main App Content (After Login)
    st.title("My Dashboard")
    st.divider()
    # Navigation Tab
    st.sidebar.markdown("### Welcome Mr. Gom !")

    page = st.sidebar.radio("📂 Navigation", ["Calendar", "Event"])

    # Load event data
    data = load_data()

    if page == "Calendar":
        event_dates = list(data["events"].keys())
        event_dates.sort()

        if not event_dates:
            st.info("No events found.")
            st.stop()

        # Convert to datetime objects for display
        date_objects = [datetime.strptime(d, "%Y-%m-%d").date() for d in event_dates]
        selected_date = st.selectbox("Select a booked event date:", date_objects)

        selected_date_str = selected_date.isoformat()
        event_data = data["events"].get(selected_date_str, {})

        # Ensure players is a list, even if no players are present
        players = event_data.get("players", [])
        note = event_data.get("notes", "")

        # --- Show Player Info ---
        with st.container():
            st.markdown(
                f"""
                <div style="padding: 0.75rem; background: linear-gradient(to right, #667eea, #764ba2, #ff512f); color: white; border-radius: 0.75rem; text-align: center; width: 160px; margin: auto;">
                    <h4 style="margin: 0; font-size: 0.85rem;">Total Players</h4>
                    <p style="font-size: 1.5rem; margin: 0; font-weight: 600;">{len(players)}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Option to display data as a DataFrame
        show_dataframe = st.checkbox("Show data as table")
        
        if show_dataframe:
            if players:
                # Convert players data to a DataFrame
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
            # Show detailed info with expander
            if players:
                for i, player in enumerate(players, 1):
                    with st.expander(f"{i}. {player['full_name']}"):
                        st.write(f"**Age:** {player['age']}")
                        st.write(f"**Email:** {player['email']}")
                        st.write(f"**Phone:** {player['phone']}")
                        st.write(f"**Secrets:** {player['secrets']}")
                        st.write(f"**Currency:** {player.get('currency', 2000)}")
                        
                        if st.button(f"Delete Player {i}", key=f"delete_{i}_{selected_date_str}"):
                            # Filter out the player by matching full_name
                            players = [p for p in players if p["full_name"] != player["full_name"]]
                            
                            # Update the players list in the data dictionary for the selected event date
                            data["events"][selected_date_str]["players"] = players

                            # Save the updated data to the JSON file
                            save_data(data)

                            st.success(f"Deleted {player['full_name']}")
                            st.rerun()  # Refresh the UI to reflect changes

            # --- Admin Note ---
            st.subheader("📓Notes Space")
            note_input = st.text_area("Write notes for this event date here...", value=note)

            if st.button("💾 Save Notes"):
                data["events"][selected_date_str]["notes"] = note_input
                save_data(data)
                st.success("Notes saved successfully!")

    elif page == "Event":
        st.subheader("Event Players")
        event_dates = list(data["events"].keys())
        event_dates.sort()

        if not event_dates:
            st.info("No events found.")
            st.stop()

        selected_date = st.selectbox("Select a booked event date for the event", event_dates)
        event_data = data["events"].get(selected_date, {})

        # Ensure players is a list, even if no players are present
        players = event_data.get("players", [])

        # Overview bar chart for all players
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

        if players:  # Ensure that players data exists and is not empty
            currency_pot = event_data.get("currency_pot", 0)
            # Define the CSS for the tile
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
                    width: 1200px; /* Wider tile */
                }
                </style>
            """
            # Inject the CSS
            st.markdown(tile_style, unsafe_allow_html=True)

            # Display the currency pot inside a centered tile
            st.markdown(f'<div class="tile-container"><div class="tile">Current Currency Pot:<br>{currency_pot}</div></div>', unsafe_allow_html=True)

            for i, player in enumerate(players, 1):
                current_currency = player.get("currency", 2000)

                # 🎯 Horizontal Bar for this player
                bar_df = pd.DataFrame({
                    "Player": [player['full_name']],
                    "Currency": [current_currency]
                })

                bar = alt.Chart(bar_df).mark_bar(
                    color="#FF6F00",  # Orange tone, change to any hex code or 'red', 'blue', etc.
                    size=40           # Bar thickness in pixels (height of the bar)
                ).encode(
                    x=alt.X('Currency:Q', scale=alt.Scale(domain=[0, 16000])),  # Max value for currency
                    y=alt.Y('Player:N')
                ).properties(
                    height=60  # Total chart height
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
                                # Refresh page to show updated currency
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
                                # Refresh page to show updated currency
                                st.rerun()