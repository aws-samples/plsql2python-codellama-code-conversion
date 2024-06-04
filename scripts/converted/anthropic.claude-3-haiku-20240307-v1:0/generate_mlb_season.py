import cx_Oracle

from datetime import datetime, timedelta
import random

def generat_mib_season(db_conn):
    sport_type_name = None
    event_date = None
    date_offset = 0

    with db_conn.cursor() as cursor:
        # Get the sport type name for 'baseball'
        cursor.execute("SELECT name FROM sport_type WHERE LOWER(name) = 'baseball'")
        sport_type_name = cursor.fetchone()[0]

    # Every team plays every other team twice, each has home field advantage once
    with db_conn.cursor() as cursor:
        # Get the list of MLB baseball teams
        cursor.execute("""
            SELECT id, home_field_id
            FROM sport_team
            WHERE sport_league_short_name = 'MLB'
            AND sport_type_name = 'baseball'
            ORDER BY id
        """)
        for hrec in cursor:
            home_team_id, home_field_id = hrec

            # Calculate the first event date
            event_date = (
                NEXT_DAY(datetime(SYSDATE.year, 3, 31), 'saturday') +
                timedelta(days=7 * date_offset)
            )

            # Schedule games against teams with higher IDs
            with db_conn.cursor() as cursor2:
                cursor2.execute("""
                    SELECT id, home_field_id
                    FROM sport_team
                    WHERE id > :home_team_id
                    AND sport_league_short_name = 'MLB'
                    AND sport_type_name = 'baseball'
                    ORDER BY id
                """, {'home_team_id': home_team_id})
                for arec in cursor2:
                    away_team_id, away_field_id = arec
                    event_date += timedelta(hours=random.uniform(12, 19))
                    insert_sporting_event(
                        db_conn, sport_type_name, home_team_id, away_team_id,
                        home_field_id, event_date
                    )
                    event_date += timedelta(days=7)

            # Schedule games against teams with lower IDs
            event_date = datetime.combine(
                NEXT_DAY(event_date, 'wednesday'), datetime.min.time()
            )
            with db_conn.cursor() as cursor3:
                cursor3.execute("""
                    SELECT id, home_field_id
                    FROM sport_team
                    WHERE id < :home_team_id
                    AND sport_league_short_name = 'MLB'
                    AND sport_type_name = 'baseball'
                    ORDER BY id
                """, {'home_team_id': home_team_id})
                for h2_rec in cursor3:
                    away_team_id, away_field_id = h2_rec
                    event_date -= timedelta(days=7)
                    event_date += timedelta(hours=random.uniform(12, 19))
                    insert_sporting_event(
                        db_conn, sport_type_name, home_team_id, away_team_id,
                        home_field_id, event_date
                    )

            date_offset += 1

def insert_sporting_event(db_conn, sport_type_name, home_team_id, away_team_id, location_id, start_date_time):
    with db_conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id, start_date_time)
            VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)
        """, {
            'sport_type_name': sport_type_name,
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'location_id': location_id,
            'start_date_time': start_date_time
        })
        db_conn.commit()

