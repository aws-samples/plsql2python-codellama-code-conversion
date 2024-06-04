import cx_Oracle
import random
from datetime import datetime, timedelta

def generate_nfl_season(db_conn):
    # Fetch sport_type_name
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sport_type WHERE LOWER(name) = 'football'")
    sport_type_name = cursor.fetchone()[0]
    cursor.close()

    # Get distinct sport divisions for NFL
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT DISTINCT sport_division_short_name
        FROM sport_team
        WHERE sport_type_name = 'football'
        AND sport_league_short_name = 'NFL'
    """)
    divisions = [row[0] for row in cursor.fetchall()]
    cursor.close()

    # Helper function to get teams for a division
    def get_teams(division):
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT id, home_field_id
            FROM sport_team
            WHERE sport_division_short_name = %s
            AND sport_type_name = 'football'
            AND sport_league_short_name = 'NFL'
            ORDER BY id
        """, (division,))
        teams = cursor.fetchall()
        cursor.close()
        return teams

    # Generate games within divisions
    start_date = datetime(datetime.now().year, 9, 1)
    start_date = start_date + timedelta(days=(6 - start_date.weekday()))  # Next Sunday
    date_offset = 0
    for division in divisions:
        teams = get_teams(division)
        for home_team in teams:
            event_date = start_date + timedelta(weeks=date_offset)
            for away_team in [t for t in teams if t != home_team]:
                event_date += timedelta(hours=random.randint(12, 19))
                cursor = db_conn.cursor()
                cursor.execute("""
                    INSERT INTO sporting_event (sport_type_name, home_team_id, away_team_id, location_id, start_date_time)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sport_type_name, home_team[0], away_team[0], home_team[1], event_date))
                db_conn.commit()
                cursor.close()
                event_date += timedelta(days=7)

            event_date = event_date + timedelta(days=(6 - event_date.weekday()))
            for away_team in [t for t in teams if t[0] < home_team[0]]:
                event_date += timedelta(hours=random.randint(12, 19))
                cursor = db_conn.cursor()
                cursor.execute("""
                    INSERT INTO sporting_event (sport_type_name, home_team_id, away_team_id, location_id, start_date_time)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sport_type_name, home_team[0], away_team[0], home_team[1], event_date))
                db_conn.commit()
                cursor.close()
            date_offset += 1

    # Generate games between divisions
    nfc_divisions = ['NFC North', 'NFC East', 'NFC South', 'NFC West']
    afc_divisions = ['AFC North', 'AFC East', 'AFC South', 'AFC West']

    def generate_cross_division_games(nfc_divs, afc_divs, event_dates):
        for i in range(4):
            nfc_teams = get_teams(nfc_divs[i])
            afc_teams = get_teams(afc_divs[i])
            for j, (home_team, away_team) in enumerate(zip(nfc_teams, afc_teams), start=1):
                cursor = db_conn.cursor()
                cursor.execute("""
                    INSERT INTO sporting_event (sport_type_name, home_team_id, away_team_id, location_id, start_date_time)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sport_type_name, home_team[0], away_team[0], home_team[1], event_dates[j]))
                db_conn.commit()
                cursor.close()

    event_date = event_date + timedelta(days=7)
    event_dates = [event_date + timedelta(hours=random.randint(12, 19)) for _ in range(16)]
    generate_cross_division_games(nfc_divisions, afc_divisions, event_dates)

    event_date = event_date + timedelta(weeks=1)
    event_dates = [event_date + timedelta(hours=random.randint(12, 19)) for _ in range(16)]
    generate_cross_division_games(nfc_divisions, afc_divisions[::-1], event_dates)

    event_date = event_date + timedelta(weeks=1)
    event_dates = [event_date + timedelta(hours=random.randint(12, 19)) for _ in range(16)]
    generate_cross_division_games(nfc_divisions[:3], afc_divisions[1:], event_dates[:12])

# No return value in the original PL/SQL code

