import cx_Oracle
def set_nfl_team_home_field(db_conn):
    nsd_cur = db_conn.cursor()
    nsd_cur.execute("SELECT sport_location_id, team FROM nfl_stadium_data")
    for nrec in nsd_cur:
        db_conn.execute("UPDATE sport_team s SET s.home_field_id = nrec.sport_location_id WHERE s.name = nrec.team AND s.sport_league_short_name = 'NFL' AND s.sport_type_name = 'football'")

