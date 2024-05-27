import cx_Oracle

import random
from datetime import datetime, timedelta

def generate_mib_season(db_conn):
    sport_type_name = None
    event_date = None
    date_offset = 0

    with db_conn.cursor() as cursor:
        # Get the sport type name for 'baseball'
        cursor.execute("SELECT name FROM sport_type WHERE LOWER(name) = 'baseball'")
        sport_type_name = cursor.fetchone()[0]

        # Iterate over the home teams
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

            # Iterate over the away teams
            cursor.execute("""
                SELECT id, home_field_id
                FROM sport_team
                WHERE id > :home_team_id
                AND sport_league_short_name = 'MLB'
                AND sport_type_name = 'baseball'
                ORDER BY id
            """, home_team_id=home_team_id)
            for arec in cursor:
                away_team_id, away_field_id = arec

                # Generate a random event time and insert the event
                event_date += timedelta(hours=random.uniform(12, 19))
                cursor.execute("""
                    INSERT INTO sporting_event(
                        sport_type_name, home_team_id, away_team_id,
                        location_id, start_date_time
                    ) VALUES (
                        :sport_type_name, :home_team_id, :away_team_id,
                        :home_field_id, :event_date
                    )
                """, {
                    'sport_type_name': sport_type_name,
                    'home_team_id': home_team_id,
                    'away_team_id': away_team_id,
                    'home_field_id': home_field_id,
                    'event_date': event_date
                })

                # Set the next event date
                event_date = (event_date + timedelta(days=7)).replace(hour=0, minute=0, second=0)

            # Iterate over the remaining away teams
            cursor.execute("""
                SELECT id, home_field_id
                FROM sport_team
                WHERE id < :home_team_id
                AND sport_league_short_name = 'MLB'
                AND sport_type_name = 'baseball'
                ORDER BY id
            """, home_team_id=home_team_id)
            for h2_rec in cursor:
                away_team_id, away_field_id = h2_rec

                # Generate a random event time and insert the event
                event_date = (event_date - timedelta(days=7)) + timedelta(hours=random.uniform(12, 19))
                cursor.execute("""
                    INSERT INTO sporting_event(
                        sport_type_name, home_team_id, away_team_id,
                        location_id, start_date_time
                    ) VALUES (
                        :sport_type_name, :home_team_id, :away_team_id,
                        :home_field_id, :event_date
                    )
                """, {
                    'sport_type_name': sport_type_name,
                    'home_team_id': home_team_id,
                    'away_team_id': away_team_id,
                    'home_field_id': home_field_id,
                    'event_date': event_date
                })

            date_offset += 1

    return None

