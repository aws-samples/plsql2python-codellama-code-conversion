import cx_Oracle
def generate_mib_season(db_conn):
    sport_type_name = db_conn.execute("SELECT name FROM sport_type WHERE LOWER(name) = 'baseball'").fetchone()[0]
    date_offset = 0

    team1 = db_conn.execute("SELECT id, home_field_id FROM sport_team WHERE sport_league_short_name = 'MLB' AND sport_type_name = 'baseball' ORDER BY id")
    for hrec in team1:
        event_date = db_conn.execute("SELECT NEXT_DAY(TO_DATE('31-MAR-' || TO_CHAR(SYSDATE,'YYYY'),'DD-MON-YYYY'),'saturday') + 7*:date_offset", date_offset=date_offset).fetchone()[0]
        team2 = db_conn.execute("SELECT id, home_field_id FROM sport_team WHERE ID > :id AND sport_league_short_name = 'MLB' AND sport_type_name = 'baseball' ORDER BY ID", id=hrec.id)
        for arec in team2:
            event_date = event_date + db_conn.execute("SELECT TRUNC(dbms_random.value(12,19))/24 FROM dual").fetchone()[0]
            db_conn.execute("INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id, start_date_time) VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)", sport_type_name=sport_type_name, home_team_id=hrec.id, away_team_id=arec.id, location_id=hrec.home_field_id, start_date_time=event_date)
            event_date = db_conn.execute("SELECT TRUNC(event_date) +7 FROM dual").fetchone()[0]

        event_date = db_conn.execute("SELECT TRUNC(NEXT_DAY(EVENT_DATE,'wednesday')) FROM dual").fetchone()[0]

        team3 = db_conn.execute("SELECT id, home_field_id FROM sport_team WHERE ID < :id AND sport_league_short_name = 'MLB' AND sport_type_name = 'baseball' ORDER BY ID", id=hrec.id)
        for h2_rec in team3:
            event_date = (event_date - 7) + db_conn.execute("SELECT TRUNC(dbms_random.value(12,19))/24 FROM dual").fetchone()[0]
            db_conn.execute("INSERT INTO sporting_event(sport_Type_name, home_team_id, away_team_id, location_id, start_date_time) VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)", sport_type_name=sport_type_name, home_team_id=hrec.id, away_team_id=h2_rec.id, location_id=hrec.home_field_id, start_date_time=event_date)

        date_offset = date_offset + 1

