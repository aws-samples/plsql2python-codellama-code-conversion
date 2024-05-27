import cx_Oracle
import random
from datetime import datetime, timedelta

def generate_mib_season(db_conn):
    # Assuming you have functions to execute SQL queries and insert data
    def execute_query(query):
        # Execute the query using db_conn and return the result
        pass

    def insert_data(table, data):
        # Insert the data into the specified table using db_conn
        pass

    sport_type_name = execute_query("SELECT name FROM sport_type WHERE LOWER(name) = 'baseball'")[0][0]
    date_offset = 0

    team1_query = """
        SELECT id, home_field_id
        FROM sport_team
        WHERE sport_league_short_name = 'MLB'
        AND sport_type_name = :sport_type_name
        ORDER BY id
    """
    team1_result = execute_query(team1_query, {'sport_type_name': sport_type_name})

    for team1_rec in team1_result:
        event_date = (datetime(datetime.now().year, 3, 31) + timedelta(days=(5 - datetime(datetime.now().year, 3, 31).weekday()) % 7 + 7 * date_offset)).date()

        team2_query = """
            SELECT id, home_field_id
            FROM sport_team
            WHERE id > :team_id
            AND sport_league_short_name = 'MLB'
            AND sport_type_name = :sport_type_name
            ORDER BY id
        """
        team2_result = execute_query(team2_query, {'team_id': team1_rec[0], 'sport_type_name': sport_type_name})

        for team2_rec in team2_result:
            event_date += timedelta(days=random.uniform(0.5, 1.5))
            insert_data('sporting_event', {
                'sport_type_name': sport_type_name,
                'home_team_id': team1_rec[0],
                'away_team_id': team2_rec[0],
                'location_id': team1_rec[1],
                'start_date_time': event_date
            })
            event_date += timedelta(days=7)

        event_date = (event_date + timedelta(days=(2 - event_date.weekday()) % 7)).date()

        team3_query = """
            SELECT id, home_field_id
            FROM sport_team
            WHERE id < :team_id
            AND sport_league_short_name = 'MLB'
            AND sport_type_name = :sport_type_name
            ORDER BY id
        """
        team3_result = execute_query(team3_query, {'team_id': team1_rec[0], 'sport_type_name': sport_type_name})

        for team3_rec in team3_result:
            event_date -= timedelta(days=7)
            event_date += timedelta(days=random.uniform(0.5, 1.5))
            insert_data('sporting_event', {
                'sport_type_name': sport_type_name,
                'home_team_id': team1_rec[0],
                'away_team_id': team3_rec[0],
                'location_id': team1_rec[1],
                'start_date_time': event_date
            })

        date_offset += 1

