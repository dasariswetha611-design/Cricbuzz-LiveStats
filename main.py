import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Cricbuzz LiveStats", layout="wide")

conn = sqlite3.connect("cricket.db", check_same_thread=False)

st.title("🏏 Cricbuzz LiveStats Dashboard")

menu = st.sidebar.selectbox(
    "Select Page",
    [
"Home",
"Live Matches",
"Top Player Stats",
"Players",
"Matches",
"SQL Analytics",
"CRUD Operations",
"Documentation"        
]
)

if menu == "Home":
    st.header("Project Overview")
    st.write("""
    This dashboard shows cricket analytics using Python, SQL, SQLite and Streamlit.
    
    Features:
    - Player statistics
    - Match details
    - SQL analytics queries
    - CRUD operations
    """)

elif menu == "Live Matches":
    st.header("Live / Upcoming Cricket Matches")

    st.write("This page displays cricket fixture data fetched from Cricbuzz API and saved in SQLite.")

    if st.button("Refresh Fixtures from API"):

        import requests

        url = "https://free-cricbuzz-cricket-api.p.rapidapi.com/cricket-schedule"

        headers = {
    "X-RapidAPI-Key": "YOUR_API_KEY_HERE",
    "X-RapidAPI-Host": "free-cricbuzz-cricket-api.p.rapidapi.com"
}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            fixtures_data = response.json()

            matches = []

            for item in fixtures_data["response"]["schedules"]:
                wrapper = item["scheduleAdWrapper"]
                date = wrapper.get("date")

                for schedule in wrapper.get("matchScheduleList", []):
                    for match in schedule.get("matchInfo", []):
                        matches.append({
                            "date": date,
                            "match_id": match.get("matchId"),
                            "series_name": match.get("seriesName"),
                            "match_desc": match.get("matchDesc"),
                            "match_format": match.get("matchFormat"),
                            "team1": match.get("team1", {}).get("teamName"),
                            "team2": match.get("team2", {}).get("teamName"),
                            "venue": match.get("venueInfo", {}).get("ground"),
                            "city": match.get("venueInfo", {}).get("city"),
                            "country": match.get("venueInfo", {}).get("country")
                        })

            df_refresh = pd.DataFrame(matches)

            df_refresh.to_sql(
                "api_fixtures",
                conn,
                if_exists="replace",
                index=False
            )

            st.success("Fixtures refreshed from API and saved to database")
            st.dataframe(df_refresh)

        else:
            st.error(f"API error: {response.status_code}")

    try:
        df_api = pd.read_sql_query("""
            SELECT
                date,
                match_id,
                team1,
                team2,
                match_desc,
                match_format,
                venue,
                city,
                country
            FROM api_fixtures
            LIMIT 50
        """, conn)

        st.success("API fixture data loaded from SQLite")
        st.dataframe(df_api)

        st.subheader("Matches by Format")
        st.bar_chart(df_api["match_format"].value_counts())

    except Exception as e:
        st.error("API fixture data not found. Please fetch data from API first.")
        st.write(e)

elif menu == "Top Player Stats":

    st.header("Top Player Statistics")

    top_runs = pd.read_sql_query("""

    SELECT
    player_name,
    runs,
    highest_score

    FROM batting_stats

    ORDER BY runs DESC

    LIMIT 10

    """, conn)

    st.subheader("Top Run Scorers")

    st.dataframe(top_runs)

    st.bar_chart(
        top_runs.set_index("player_name")["runs"]
    )


    top_wickets = pd.read_sql_query("""

    SELECT
    player_name,
    wickets

    FROM bowling_stats

    ORDER BY wickets DESC

    LIMIT 10

    """, conn)

    st.subheader("Top Wicket Takers")

    st.dataframe(top_wickets)

    st.bar_chart(
        top_wickets.set_index("player_name")["wickets"]
    )

elif menu == "Players":
    st.header("Player Statistics")

    df = pd.read_sql_query("SELECT * FROM players", conn)
    st.dataframe(df)

    st.subheader("Players by Role")

    role_count = df["playing_role"].value_counts()
    st.bar_chart(role_count)

elif menu == "Matches":
    st.header("Match Details")

    df = pd.read_sql_query("SELECT * FROM matches", conn)
    st.dataframe(df)

    st.subheader("Wins by Team")

    wins = df["winning_team"].value_counts()
    st.bar_chart(wins)

elif menu == "SQL Analytics":
    st.header("SQL Analytics")

    query_options = {
        "Q2 Recent Matches": """
    SELECT m.match_description, m.team1, m.team2, m.venue_name, v.city, m.match_date
    FROM matches m
    JOIN venues v ON m.venue_name = v.venue_name
    ORDER BY m.match_date DESC
""",

"Q4 Large Venues": """
    SELECT venue_name, city, country, capacity
    FROM venues
    WHERE capacity > 25000
    ORDER BY capacity DESC
""",

"Q7 Highest Score by Format": """
    SELECT match_format, MAX(highest_score) AS highest_individual_score
    FROM batting_stats
    GROUP BY match_format
""",

"Q23 Player Form": """
    SELECT player_name,
           ROUND(AVG(runs),2) AS avg_runs,
           ROUND(AVG(strike_rate),2) AS avg_sr,
           CASE
               WHEN AVG(runs)>=100 THEN 'Excellent Form'
               WHEN AVG(runs)>=50 THEN 'Good Form'
               WHEN AVG(runs)>=30 THEN 'Average Form'
               ELSE 'Poor Form'
           END AS form_category
    FROM batting_stats
    GROUP BY player_name
    ORDER BY avg_runs DESC
"""
    }

    selected_query = st.selectbox("Choose SQL Query", list(query_options.keys()))

    st.code(query_options[selected_query], language="sql")

    result = pd.read_sql_query(query_options[selected_query], conn)
    st.dataframe(result)

elif menu == "CRUD Operations":
    st.header("Add New Player")

    name = st.text_input("Player Name")
    country = st.text_input("Country")
    role = st.selectbox("Playing Role", ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"])
    batting = st.text_input("Batting Style")
    bowling = st.text_input("Bowling Style")

    if st.button("Add Player"):
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO players
            (full_name, country, playing_role, batting_style, bowling_style)
            VALUES (?, ?, ?, ?, ?)
        """, (name, country, role, batting, bowling))
        conn.commit()
        st.success("Player added successfully")

    st.subheader("Current Players")
    df = pd.read_sql_query("SELECT * FROM players", conn)
    st.dataframe(df)
    st.subheader("Delete Player")

    delete_name = st.selectbox(
        "Select player to delete",
        df["full_name"].tolist()
    )

    if st.button("Delete Player"):
        cursor = conn.cursor()

        cursor.execute("""
        DELETE FROM players
        WHERE full_name = ?
        """, (delete_name,))

        conn.commit()

        st.success(f"{delete_name} deleted successfully")

        st.rerun()
        
        st.subheader("Update Player Role")

    update_name = st.selectbox(
        "Select player to update",
        df["full_name"].tolist()
    )

    new_role = st.selectbox(
        "Select new role",
        ["Batsman", "Bowler", "All-rounder", "Wicket-keeper", "Wicket-keeper Batsman"]
    )

    if st.button("Update Player"):
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE players
            SET playing_role = ?
            WHERE full_name = ?
        """, (new_role, update_name))
        conn.commit()
        st.success(f"{update_name} updated successfully")
        st.rerun()

elif menu == "Documentation":

    st.title("📘 Project Documentation")

    st.header("Project Name")
    st.write("""
    Cricbuzz LiveStats Dashboard using Python, SQL, SQLite, Streamlit and Cricbuzz API.
    """)


    st.header("Project Objective")

    st.write("""
    The objective of this project is to build an interactive cricket analytics dashboard that:

    - Fetches live/upcoming cricket fixtures using Cricbuzz API
    - Stores API data in SQLite database
    - Performs SQL analytics on player and match statistics
    - Displays interactive dashboards using Streamlit
    - Implements CRUD operations on player data
    """)


    st.header("Technologies Used")

    tech = pd.DataFrame({
        "Technology":[
            "Python",
            "SQLite",
            "SQL",
            "Pandas",
            "Streamlit",
            "RapidAPI",
            "Requests"
        ],

        "Purpose":[
            "Programming",
            "Database",
            "Analytics Queries",
            "Data Manipulation",
            "Dashboard",
            "Cricbuzz API",
            "API Requests"
        ]
    })

    st.dataframe(tech)


    st.header("Database Tables")

    st.write("""

    Database tables used:

    • players

    • matches

    • batting_stats

    • bowling_stats

    • venues

    • partnerships

    • api_fixtures (Live API data)

    """)


    st.header("Dashboard Features")

    st.write("""

    ✅ Home Page

    ✅ Live Matches (API Integration)

    ✅ Top Player Statistics

    ✅ Player Analytics

    ✅ Match Analytics

    ✅ SQL Queries

    ✅ CRUD Operations

    ✅ Documentation Page

    """)


    st.header("API Integration")

    st.write("""

    Cricbuzz API was connected using RapidAPI.

    Live fixture data is:

    API → JSON → Pandas → SQLite → Streamlit Dashboard

    """)


    st.header("Project Workflow")

    st.write("""

    Step 1:
    Fetch cricket data from API

    ↓

    Step 2:
    Store data in SQLite

    ↓

    Step 3:
    Execute SQL analysis

    ↓

    Step 4:
    Visualize in Streamlit

    ↓

    Step 5:
    Perform CRUD operations

    """)


    st.header("Conclusion")

    st.success("""
    This project demonstrates SQL analytics,
    API integration,
    database management,
    Python programming,
    and dashboard development.
    """)