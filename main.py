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
    st.write("Explore 25 SQL questions using the Cricbuzz SQLite database.")

    query_options = {

        # =========================
        # BEGINNER LEVEL
        # =========================

        "Beginner - Q1 India Players": """
            SELECT
                player_id,
                full_name,
                country,
                playing_role,
                batting_style,
                bowling_style
            FROM players
            WHERE LOWER(country) = 'india'
            ORDER BY full_name;
        """,

        "Beginner - Q2 Recent Matches": """
            SELECT
                m.match_description,
                m.team1,
                m.team2,
                m.winning_team,
                m.venue_name,
                v.city,
                m.match_date,
                m.match_format
            FROM matches m
            LEFT JOIN venues v
                ON m.venue_name = v.venue_name
            ORDER BY m.match_date DESC;
        """,

        "Beginner - Q3 Top ODI Run Scorers": """
            SELECT
                player_name,
                SUM(runs) AS total_runs,
                AVG(strike_rate) AS average_strike_rate,
                SUM(centuries) AS total_centuries
            FROM batting_stats
            WHERE UPPER(match_format) = 'ODI'
            GROUP BY player_name
            ORDER BY total_runs DESC
            LIMIT 10;
        """,

        "Beginner - Q4 Large Venues": """
            SELECT
                venue_name,
                city,
                country,
                capacity
            FROM venues
            WHERE capacity > 25000
            ORDER BY capacity DESC;
        """,

        "Beginner - Q5 Team Wins": """
            SELECT
                winning_team,
                COUNT(*) AS total_wins
            FROM matches
            WHERE winning_team IS NOT NULL
              AND TRIM(winning_team) != ''
            GROUP BY winning_team
            ORDER BY total_wins DESC;
        """,

        "Beginner - Q6 Players by Role": """
            SELECT
                playing_role,
                COUNT(*) AS total_players
            FROM players
            WHERE playing_role IS NOT NULL
            GROUP BY playing_role
            ORDER BY total_players DESC;
        """,

        "Beginner - Q7 Highest Individual Score by Format": """
            SELECT
                match_format,
                MAX(runs) AS highest_individual_score
            FROM batting_stats
            GROUP BY match_format
            ORDER BY highest_individual_score DESC;
        """,

        "Beginner - Q8 Matches in 2024": """
            SELECT
                match_description,
                team1,
                team2,
                match_format,
                match_date,
                venue_name
            FROM matches
            WHERE SUBSTR(match_date, 1, 4) = '2024'
            ORDER BY match_date;
        """,

        # =========================
        # INTERMEDIATE LEVEL
        # =========================

        "Intermediate - Q9 All-Rounder Performance": """
            SELECT
                p.full_name,
                p.playing_role,
                COALESCE(b.total_runs, 0) AS total_runs,
                COALESCE(w.total_wickets, 0) AS total_wickets,
                w.average_economy
            FROM players p
            LEFT JOIN (
                SELECT
                    player_name,
                    SUM(runs) AS total_runs
                FROM batting_stats
                GROUP BY player_name
            ) b
                ON LOWER(p.full_name) = LOWER(b.player_name)
            LEFT JOIN (
                SELECT
                    player_name,
                    SUM(wickets) AS total_wickets,
                    ROUND(AVG(economy), 2) AS average_economy
                FROM bowling_stats
                GROUP BY player_name
            ) w
                ON LOWER(p.full_name) = LOWER(w.player_name)
            WHERE LOWER(p.playing_role) LIKE '%all-round%'
            ORDER BY total_runs DESC;
        """,

        "Intermediate - Q10 Last 20 Completed Matches": """
            SELECT
                match_description,
                team1,
                team2,
                winning_team,
                match_format,
                match_date
            FROM matches
            WHERE winning_team IS NOT NULL
              AND TRIM(winning_team) != ''
            ORDER BY match_date DESC
            LIMIT 20;
        """,

        "Intermediate - Q11 Player Performance Across Formats": """
            SELECT
                player_name,
                match_format,
                COUNT(*) AS innings_records,
                SUM(runs) AS total_runs,
                ROUND(AVG(runs), 2) AS average_runs,
                ROUND(AVG(strike_rate), 2) AS average_strike_rate,
                SUM(centuries) AS total_centuries
            FROM batting_stats
            GROUP BY player_name, match_format
            ORDER BY player_name, total_runs DESC;
        """,

        "Intermediate - Q12 Team 1 vs Team 2 Win Records": """
            SELECT
                team_name,
                COUNT(*) AS matches_played,
                SUM(wins) AS matches_won
            FROM (
                SELECT
                    team1 AS team_name,
                    CASE WHEN winning_team = team1 THEN 1 ELSE 0 END AS wins
                FROM matches

                UNION ALL

                SELECT
                    team2 AS team_name,
                    CASE WHEN winning_team = team2 THEN 1 ELSE 0 END AS wins
                FROM matches
            )
            GROUP BY team_name
            ORDER BY matches_won DESC;
        """,

        "Intermediate - Q13 Partnerships": """
            SELECT
                'Partnership analysis is unavailable because the current '
                || 'database does not contain a partnerships table.'
                AS information;
        """,

        "Intermediate - Q14 Bowling Performance by Format": """
            SELECT
                player_name,
                match_format,
                SUM(wickets) AS total_wickets,
                SUM(runs_given) AS total_runs_conceded,
                ROUND(AVG(economy), 2) AS average_economy
            FROM bowling_stats
            GROUP BY player_name, match_format
            ORDER BY total_wickets DESC;
        """,

        "Intermediate - Q15 Top Individual Batting Performances": """
            SELECT
                player_name,
                match_format,
                MAX(runs) AS highest_runs,
                MAX(strike_rate) AS highest_strike_rate
            FROM batting_stats
            GROUP BY player_name, match_format
            ORDER BY highest_runs DESC
            LIMIT 20;
        """,

        "Intermediate - Q16 Matches by Year Since 2020": """
            SELECT
                SUBSTR(match_date, 1, 4) AS match_year,
                COUNT(*) AS total_matches
            FROM matches
            WHERE match_date IS NOT NULL
              AND SUBSTR(match_date, 1, 4) >= '2020'
            GROUP BY SUBSTR(match_date, 1, 4)
            ORDER BY match_year;
        """,

        # =========================
        # ADVANCED LEVEL
        # =========================

        "Advanced - Q17 Toss Winning Advantage": """
            SELECT
                'Toss analysis is unavailable because the current '
                || 'matches table does not contain toss_winner or '
                || 'toss_decision columns.'
                AS information;
        """,

        "Advanced - Q18 Most Economical Bowlers": """
            SELECT
                player_name,
                SUM(wickets) AS total_wickets,
                ROUND(AVG(economy), 2) AS average_economy,
                SUM(overs) AS total_overs,
                SUM(runs_given) AS total_runs_conceded
            FROM bowling_stats
            GROUP BY player_name
            HAVING SUM(overs) > 0
            ORDER BY average_economy ASC
            LIMIT 10;
        """,

        "Advanced - Q19 Consistent Batsmen": """
            SELECT
                player_name,
                COUNT(*) AS innings_records,
                ROUND(AVG(runs), 2) AS average_runs,
                ROUND(
                    MAX(
                        0,
                        AVG(runs * runs) - AVG(runs) * AVG(runs)
                    ),
                    2
                ) AS runs_variance
            FROM batting_stats
            GROUP BY player_name
            HAVING COUNT(*) >= 2
            ORDER BY runs_variance ASC, average_runs DESC
            LIMIT 10;
        """,

        "Advanced - Q20 Match Summary by Format": """
            SELECT
                match_format,
                COUNT(*) AS total_matches,
                COUNT(DISTINCT team1) AS team1_count,
                COUNT(DISTINCT team2) AS team2_count,
                COUNT(DISTINCT winning_team) AS different_winning_teams
            FROM matches
            GROUP BY match_format
            ORDER BY total_matches DESC;
        """,

        "Advanced - Q21 Weighted Player Ranking": """
            SELECT
                player_name,
                SUM(runs) AS total_runs,
                ROUND(AVG(strike_rate), 2) AS average_strike_rate,
                SUM(centuries) AS total_centuries,
                ROUND(
                    SUM(runs) * 0.5
                    + AVG(strike_rate) * 0.3
                    + SUM(centuries) * 20,
                    2
                ) AS performance_score
            FROM batting_stats
            GROUP BY player_name
            ORDER BY performance_score DESC
            LIMIT 10;
        """,

        "Advanced - Q22 Head-to-Head Team Records": """
            SELECT
                CASE
                    WHEN team1 < team2 THEN team1
                    ELSE team2
                END AS team_a,

                CASE
                    WHEN team1 < team2 THEN team2
                    ELSE team1
                END AS team_b,

                COUNT(*) AS matches_played,

                SUM(
                    CASE
                        WHEN winning_team =
                            CASE
                                WHEN team1 < team2 THEN team1
                                ELSE team2
                            END
                        THEN 1 ELSE 0
                    END
                ) AS team_a_wins,

                SUM(
                    CASE
                        WHEN winning_team =
                            CASE
                                WHEN team1 < team2 THEN team2
                                ELSE team1
                            END
                        THEN 1 ELSE 0
                    END
                ) AS team_b_wins

            FROM matches
            GROUP BY
                CASE WHEN team1 < team2 THEN team1 ELSE team2 END,
                CASE WHEN team1 < team2 THEN team2 ELSE team1 END
            ORDER BY matches_played DESC;
        """,

        "Advanced - Q23 Player Recent Form Summary": """
            SELECT
                player_name,
                COUNT(*) AS innings_records,
                ROUND(AVG(runs), 2) AS avg_runs,
                ROUND(AVG(strike_rate), 2) AS avg_strike_rate,
                CASE
                    WHEN AVG(runs) >= 100 THEN 'Excellent Form'
                    WHEN AVG(runs) >= 50 THEN 'Good Form'
                    WHEN AVG(runs) >= 30 THEN 'Average Form'
                    ELSE 'Needs Improvement'
                END AS form_category
            FROM batting_stats
            GROUP BY player_name
            ORDER BY avg_runs DESC;
        """,

        "Advanced - Q24 Best Batting Partnerships": """
            SELECT
                'Partnership analysis is unavailable because the current '
                || 'database does not contain partnership player names '
                || 'or partnership runs.'
                AS information;
        """,

        "Advanced - Q25 Quarterly Match Trends": """
            SELECT
                SUBSTR(match_date, 1, 4) AS match_year,
                'Q' || (
                    CAST(
                        (CAST(SUBSTR(match_date, 6, 2) AS INTEGER) - 1) / 3
                        AS INTEGER
                    ) + 1
                ) AS match_quarter,
                COUNT(*) AS total_matches
            FROM matches
            WHERE match_date IS NOT NULL
              AND LENGTH(match_date) >= 7
            GROUP BY
                SUBSTR(match_date, 1, 4),
                CAST(
                    (CAST(SUBSTR(match_date, 6, 2) AS INTEGER) - 1) / 3
                    AS INTEGER
                )
            ORDER BY match_year, match_quarter;
        """
    }

    # Query selection
    selected_query = st.selectbox(
        "Choose a SQL Analytics Question",
        list(query_options.keys())
    )

    # Display SQL
    st.subheader(selected_query)
    st.code(query_options[selected_query], language="sql")

    # Execute selected query
    try:
        result = pd.read_sql_query(
            query_options[selected_query],
            conn
        )

        st.success(
            f"Query executed successfully! "
            f"{len(result)} record(s) returned."
        )

        if not result.empty:
            st.dataframe(
                result,
                use_container_width=True
            )
        else:
            st.info(
                "The query ran successfully, but no records were found."
            )

    except Exception as e:
        st.error("Unable to execute this SQL query.")
        st.code(str(e))

    st.caption(
        "Note: Results depend on the records currently stored "
        "in your SQLite database. Some analyses are unavailable "
        "because the current database does not store the required data."
    )



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
