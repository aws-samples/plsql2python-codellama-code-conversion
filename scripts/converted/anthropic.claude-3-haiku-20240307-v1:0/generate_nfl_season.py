import cx_Oracle
def generate_nfl_season(db_conn):
    sport_type_name = None
    event_date = None
    date_offset = 0

    # Fetch the sport type name
    with db_conn.cursor() as cursor:
        cursor.execute("SELECT name FROM sport_type WHERE LOWER(name) = 'football'")
        sport_type_name = cursor.fetchone()[0]

    # Each team plays each team in their own division twice
    with db_conn.cursor() as cursor:
        cursor.execute("SELECT DISTINCT sport_division_short_name FROM sport_team WHERE sport_type_name = 'football' AND sport_league_short_name = 'NFL'")
        for drec in cursor:
            division = drec[0]
            date_offset = 0

            # Get home teams in the division
            cursor.execute("SELECT id, home_field_id FROM sport_team WHERE sport_division_short_name = %s AND sport_type_name = 'football' AND sport_league_short_name = 'NFL' ORDER BY id", (division,))
            for hrec in cursor:
                home_team_id, home_field_id = hrec

                # Get away teams in the division
                cursor.execute("SELECT id, home_field_id FROM sport_team WHERE sport_division_short_name = %s AND sport_type_name = 'football' AND sport_league_short_name = 'NFL' AND id > %s ORDER BY id", (division, home_team_id))
                for arec in cursor:
                    away_team_id, away_field_id = arec
                    event_date = (
                        NEXT_DAY(TO_DATE('01-SEP-' + str(datetime.now().year), 'DD-MON-YYYY'), 'sunday')
                        + datetime.timedelta(days=7 * date_offset)
                        + datetime.timedelta(hours=random.uniform(12, 19))
                    )
                    insert_sporting_event(db_conn, sport_type_name, home_team_id, away_team_id, home_field_id, event_date)
                    event_date = event_date + datetime.timedelta(days=7)

                # Get remaining away teams in the division
                cursor.execute("SELECT id, home_field_id FROM sport_team WHERE sport_division_short_name = %s AND sport_type_name = 'football' AND sport_league_short_name = 'NFL' AND id < %s ORDER BY id", (division, home_team_id))
                for h2_rec in cursor:
                    away_team_id, away_field_id = h2_rec
                    event_date = (
                        TRUNC(event_date - datetime.timedelta(days=7))
                        + datetime.timedelta(hours=random.uniform(12, 19))
                    )
                    insert_sporting_event(db_conn, sport_type_name, home_team_id, away_team_id, home_field_id, event_date)

                date_offset += 1

    # Each team plays each team in another division once
    nfc_divisions = ['NFC North', 'NFC East', 'NFC South', 'NFC West']
    afc_divisions = ['AFC North', 'AFC East', 'AFC South', 'AFC West']

    date_tab = {}
    for i in range(1, 17):
        event_date = (
            TRUNC(event_date + datetime.timedelta(days=7))
            + datetime.timedelta(hours=random.uniform(12, 19))
        )
        date_tab[i] = event_date

    for i in range(1, 5):
        with db_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT rownum AS cur_row, DECODE(MOD(rownum, 2), 0, a.id, 1, b.id) AS home_id,
                       a.id AS t2_id, a.home_field_id AS t2_field_id,
                       b.id AS t1_id, b.home_field_id AS t1_field_id
                FROM sport_team a, sport_team b
                WHERE a.sport_division_short_name = %s
                  AND b.sport_division_short_name = %s
                  AND a.sport_type_name = 'football'
                  AND b.sport_type_name = 'football'
                  AND a.sport_league_short_name = 'NFL'
                  AND b.sport_league_short_name = 'NFL'
                ORDER BY a.name, b.name
                """,
                (nfc_divisions[i - 1], afc_divisions[i - 1]),
            )
            for trec in cursor:
                cur_row, home_id, t2_id, t2_field_id, t1_id, t1_field_id = trec
                if home_id == t2_id:
                    insert_sporting_event(db_conn, sport_type_name, t2_id, t1_id, t2_field_id, date_tab[cur_row])
                else:
                    insert_sporting_event(db_conn, sport_type_name, t1_id, t2_id, t1_field_id, date_tab[cur_row])

    # Play three more random games
    for i in range(1, 4):
        with db_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT rownum AS cur_row, DECODE(MOD(rownum, 2), 0, a.id, 1, b.id) AS home_id,
                       a.id AS t2_id, a.home_field_id AS t2_field_id,
                       b.id AS t1_id, b.home_field_id AS t1_field_id
                FROM sport_team a, sport_team b
                WHERE a.sport_division_short_name = %s
                  AND b.sport_division_short_name = %s
                  AND a.sport_type_name = 'football'
                  AND b.sport_type_name = 'football'
                  AND a.sport_league_short_name = 'NFL'
                  AND b.sport_league_short_name = 'NFL'
                ORDER BY a.name, b.name
                """,
                (nfc_divisions[i - 1], afc_divisions[i - 1]),
            )
            for trec in cursor:
                cur_row, home_id, t2_id, t2_field_id, t1_id, t1_field_id = trec
                if home_id == t2_id:
                    insert_sporting_event(db_conn, sport_type_name, t2_id, t1_id, t2_field_id, date_tab[cur_row])
                else:
                    insert_sporting_event(db_conn, sport_type_name, t1_id, t2_id, t1_field_id, date_tab[cur_row])

def insert_sporting_event(db_conn, sport_type_name, home_team_id, away_team_id, location_id, start_date_time):
    with db_conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO sporting_event (sport_type_name, home_team_id, away_team_id, location_id, start_date_time) VALUES (%s, %s, %s, %s, %s)",
            (sport_type_name, home_team_id, away_team_id, location_id, start_date_time),
        )
        db_conn.commit()

