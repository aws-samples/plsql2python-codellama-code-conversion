import cx_Oracle


def set_nfl_team_home_field(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT sport_location_id, team FROM nfl_stadium_data")
    nsd_data = cursor.fetchall()
    cursor.close()

    for nrec in nsd_data:
        sport_location_id, team = nrec
        cursor = db_conn.cursor()
        cursor.execute("""
            UPDATE sport_team s
            SET s.home_field_id = :sport_location_id
            WHERE s.name = :team
            AND s.sport_league_short_name = 'NFL'
            AND s.sport_type_name = 'football'
        """, sport_location_id=sport_location_id, team=team)
        db_conn.commit()
        cursor.close()

