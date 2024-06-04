import cx_Oracle
def generate_nfl_season(db_conn):
    sport_type_name = None
    event_date = None
    date_offset = 0

    with db_conn.cursor() as cursor:
        # Get the sport type name for 'football'
        cursor.execute("SELECT name FROM sport_type WHERE LOWER(name) = 'football'")
        sport_type_name = cursor.fetchone()[0]

        # Each team plays each team in their own division twice
        cursor.execute("SELECT DISTINCT sport_division_short_name FROM sport_team WHERE sport_type_name = 'football' AND sport_league_short_name = 'NFL'")
        div_records = cursor.fetchall()

        for div_record in div_records:
            division = div_record[0]
            date_offset = 0

            # Get the teams in the current division
            cursor.execute("""
                SELECT id, home_field_id 
                FROM sport_team
                WHERE sport_division_short_name = %s
                AND sport_type_name = 'football'
                AND sport_league_short_name = 'NFL'
                ORDER BY id
            """, (division,))
            team1_records = cursor.fetchall()

            for team1_record in team1_records:
                team1_id, team1_field_id = team1_record
                event_date = get_next_sunday(db_conn) + datetime.timedelta(days=7 * date_offset)

                # Get the teams in the current division that come after the current team
                cursor.execute("""
                    SELECT id, home_field_id
                    FROM sport_team
                    WHERE sport_division_short_name = %s
                    AND sport_type_name = 'football'
                    AND sport_league_short_name = 'NFL'
                    AND id > %s
                    ORDER BY id
                """, (division, team1_id))
                team2_records = cursor.fetchall()

                for team2_record in team2_records:
                    team2_id, team2_field_id = team2_record
                    event_date += datetime.timedelta(hours=random.randint(12, 19))
                    insert_sporting_event(db_conn, sport_type_name, team1_id, team2_id, team1_field_id, event_date)
                    event_date += datetime.timedelta(days=7)

                event_date = get_next_sunday(db_conn, event_date) + datetime.timedelta(days=7)

                # Get the teams in the current division that come before the current team
                cursor.execute("""
                    SELECT id, home_field_id
                    FROM sport_team
                    WHERE sport_division_short_name = %s
                    AND sport_type_name = 'football'
                    AND sport_league_short_name = 'NFL'
                    AND id < %s
                    ORDER BY id
                """, (division, team1_id))
                team3_records = cursor.fetchall()

                for team3_record in team3_records:
                    team3_id, team3_field_id = team3_record
                    event_date -= datetime.timedelta(days=7)
                    event_date += datetime.timedelta(hours=random.randint(12, 19))
                    insert_sporting_event(db_conn, sport_type_name, team1_id, team3_id, team1_field_id, event_date)

                date_offset += 1

        # Each team plays each team in another division once
        nfc_divisions = ['NFC North', 'NFC East', 'NFC South', 'NFC West']
        afc_divisions = ['AFC North', 'AFC East', 'AFC South', 'AFC West']

        for i in range(4):
            cursor.execute("""
                SELECT rownum AS cur_row, DECODE(MOD(rownum,2),0,a.id,1,b.id) AS home_id,
                       a.id AS t2_id, a.home_field_id AS t2_field_id,
                       b.id AS t1_id, b.home_field_id AS t1_field_id
                FROM sport_team a, sport_team b
                WHERE a.sport_division_short_name = %s
                AND b.sport_division_short_name = %s
                ORDER BY a.name, b.name
            """, (nfc_divisions[i], afc_divisions[i]))
            cross_div_records = cursor.fetchall()

            for cross_div_record in cross_div_records:
                cur_row, home_id, t2_id, t2_field_id, t1_id, t1_field_id = cross_div_record
                event_date = get_next_sunday(db_conn, event_date) + datetime.timedelta(days=7)
                event_date += datetime.timedelta(hours=random.randint(12, 19))

                if home_id == t2_id:
                    insert_sporting_event(db_conn, sport_type_name, t2_id, t1_id, t2_field_id, event_date)
                else:
                    insert_sporting_event(db_conn, sport_type_name, t1_id, t2_id, t1_field_id, event_date)

        # Play three more random games
        for i in range(3):
            cursor.execute("""
                SELECT rownum AS cur_row, DECODE(MOD(rownum,2),0,a.id,1,b.id) AS home_id,
                       a.id AS t2_id, a.home_field_id AS t2_field_id,
                       b.id AS t1_id, b.home_field_id AS t1_field_id
                FROM sport_team a, sport_team b
                WHERE a.sport_division_short_name = %s
                AND b.sport_division_short_name = %s
                ORDER BY a.name, b.name
            """, (nfc_divisions[i], afc_divisions[i]))
            cross_div_records = cursor.fetchall()

            for cross_div_record in cross_div_records:
                cur_row, home_id, t2_id, t2_field_id, t1_id, t1_field_id = cross_div_record
                event_date = get_next_sunday(db_conn, event_date) + datetime.timedelta(days=7)
                event_date += datetime.timedelta(hours=random.randint(12, 19))

                if home_id == t2_id:
                    insert_sporting_event(db_conn, sport_type_name, t2_id, t1_id, t2_field_id, event_date)
                else:
                    insert_sporting_event(db_conn, sport_type_name, t1_id, t2_id, t1_field_id, event_date)

def get_next_sunday(db_conn, start_date=None):
    if start_date is None:
        start_date = datetime.date.today()
    return start_date + datetime.timedelta(days=(6 - start_date.weekday()) % 7)

def insert_sporting_event(db_conn, sport_type_name, home_team_id, away_team_id, location_id, start_date_time):
    with db_conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id, start_date_time)
            VALUES(%s, %s, %s, %s, %s)
        """, (sport_type_name, home_team_id, away_team_id, location_id, start_date_time))
        db_conn.commit()

