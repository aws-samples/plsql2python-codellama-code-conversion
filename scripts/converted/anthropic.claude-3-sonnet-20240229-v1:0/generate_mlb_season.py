import cx_Oracle
import random
from datetime import datetime, timedelta

def generate_mib_season(db_conn):
    sport_type_name = get_sport_type_name(db_conn, 'baseball')
    date_offset = 0

    teams = get_teams(db_conn, 'MLB', sport_type_name)

    for home_team in teams:
        event_date = next_saturday(datetime(datetime.now().year, 3, 31)) + timedelta(days=7 * date_offset)

        for away_team in get_teams(db_conn, 'MLB', sport_type_name, home_team['id'], '>'):
            event_date += timedelta(days=random.uniform(0.5, 0.8))
            insert_sporting_event(db_conn, sport_type_name, home_team['id'], away_team['id'], home_team['home_field_id'], event_date)
            event_date += timedelta(days=7)

        event_date = next_wednesday(event_date)

        for away_team in get_teams(db_conn, 'MLB', sport_type_name, home_team['id'], '<'):
            event_date -= timedelta(days=7)
            event_date += timedelta(days=random.uniform(0.5, 0.8))
            insert_sporting_event(db_conn, sport_type_name, home_team['id'], away_team['id'], home_team['home_field_id'], event_date)

        date_offset += 1

def get_sport_type_name(db_conn, sport_type_name):
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sport_type WHERE LOWER(name) = :sport_type_name", sport_type_name=sport_type_name.lower())
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def get_teams(db_conn, sport_league_short_name, sport_type_name, team_id=None, operator=None):
    cursor = db_conn.cursor()
    query = "SELECT id, home_field_id FROM sport_team WHERE sport_league_short_name = :sport_league_short_name AND sport_type_name = :sport_type_name"
    params = {'sport_league_short_name': sport_league_short_name, 'sport_type_name': sport_type_name}

    if team_id and operator:
        query += f" AND id {operator} :team_id"
        params['team_id'] = team_id

    query += " ORDER BY id"
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    return result

def insert_sporting_event(db_conn, sport_type_name, home_team_id, away_team_id, location_id, start_date_time):
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id, start_date_time) VALUES (:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)",
        sport_type_name=sport_type_name,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        location_id=location_id,
        start_date_time=start_date_time
    )
    db_conn.commit()
    cursor.close()

def next_saturday(date):
    days_ahead = 5 - date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return date + timedelta(days=days_ahead)

def next_wednesday(date):
    days_ahead = 2 - date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return date + timedelta(days=days_ahead)

