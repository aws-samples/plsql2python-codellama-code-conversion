import cx_Oracle
def generat_nfl_season(db_conn):
    sport_type_name = db_conn.execute("SELECT name FROM sport_type WHERE LOWER(name) = 'football'").fetchone()[0]

    # Each team plays each team in their own division twice
    for drec in db_conn.execute("SELECT distinct sport_division_short_name FROM sport_team WHERE sport_type_name = 'football' AND sport_league_short_name = 'NFL'"):
        date_offset = 0
        for hrec in db_conn.execute("SELECT id, home_field_id FROM sport_team WHERE sport_division_short_name = :division AND sport_type_name = 'football' AND sport_league_short_name = 'NFL' order by id", division=drec.sport_division_short_name):
            event_date = db_conn.execute("SELECT NEXT_DAY(TO_DATE('01-SEP-' || TO_CHAR(sysdate,'YYYY'),'DD-MON-YYYY'),'sunday') + 7*:date_offset", date_offset=date_offset).fetchone()[0]
            for arec in db_conn.execute("SELECT id, home_field_id FROM sport_team WHERE ID > :id AND sport_division_short_name = :division AND sport_type_name = 'football' AND sport_league_short_name = 'NFL' order by id", id=hrec.id, division=drec.sport_division_short_name):
                event_date = db_conn.execute("SELECT TRUNC(EVENT_DATE)+7 + TRUNC(dbms_random.value(12,19))/24", event_date=event_date).fetchone()[0]
                db_conn.execute("INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id,start_date_time) VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)", sport_type_name=sport_type_name, home_team_id=hrec.id, away_team_id=arec.id, location_id=hrec.home_field_id, start_date_time=event_date)

                event_date = db_conn.execute("SELECT TRUNC(EVENT_DATE)+7", event_date=event_date).fetchone()[0]

            for h2_rec in db_conn.execute("SELECT id, home_field_id FROM sport_team WHERE ID < :id AND sport_division_short_name = :division AND sport_type_name = 'football' AND sport_league_short_name = 'NFL' order by id", id=hrec.id, division=drec.sport_division_short_name):
                event_date = db_conn.execute("SELECT (event_date - 7) + TRUNC(dbms_random.value(12,19))/24", event_date=event_date).fetchone()[0]
                db_conn.execute("INSERT INTO sporting_event(sport_Type_name, home_team_id, away_team_id, location_id, start_date_time) VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)", sport_type_name=sport_type_name, home_team_id=hrec.id, away_team_id=h2_rec.id, location_id=hrec.home_field_id, start_date_time=event_date)

            date_offset = date_offset + 1

    # Each team plays each team in another division once
    event_date = db_conn.execute("SELECT TRUNC(EVENT_DATE)+7 + TRUNC(dbms_random.value(12,19))/24", event_date=event_date).fetchone()[0]
    date_tab = [event_date] * 16

    nfc_tab = ['NFC North', 'NFC East', 'NFC South', 'NFC West']
    afc_tab = ['AFC North', 'AFC East', 'AFC South', 'AFC West']
    for i in range(1, 4):
        for trec in db_conn.execute("SELECT rownum as cur_row, DECODE(mod(rownum,2),0,a.id,1,b.id) as home_id, a.id as t2_id, a.home_field_id as t2_field_id, b.id as t1_id, b.home_field_id as t1_field_id FROM sport_team a, sport_team b WHERE a.sport_division_short_name = :nfc_div AND b.sport_division_short_name = :afc_div ORDER BY a.name,b.name", nfc_div=nfc_tab[i], afc_div=afc_tab[i]):
            if trec.home_id == trec.t2_id:
                db_conn.execute("INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id,start_date_time) VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)", sport_type_name=sport_type_name, home_team_id=trec.t2_id, away_team_id=trec.t1_id, location_id=trec.t2_field_id, start_date_time=date_tab[trec.cur_row])
            else:
                db_conn.execute("INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id,start_date_time) VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)", sport_type_name=sport_type_name, home_team_id=trec.t1_id, away_team_id=trec.t2_id, location_id=trec.t1_field_id, start_date_time=date_tab[trec.cur_row])

    # Play three more random games
    event_date = db_conn.execute("SELECT TRUNC(EVENT_DATE)+7 + TRUNC(dbms_random.value(12,19))/24", event_date=event_date).fetchone()[0]
    date_tab = [event_date] * 16

    nfc_tab = ['NFC North', 'NFC East', 'NFC South', 'NFC West']
    afc_tab = ['AFC South', 'AFC West', 'AFC North', 'AFC East']
    for i in range(1, 3):
        for trec in db_conn.execute("SELECT rownum as cur_row, DECODE(mod(rownum,2),0,a.id,1,b.id) as home_id, a.id as t2_id, a.home_field_id as t2_field_id, b.id as t1_id, b.home_field_id as t1_field_id FROM sport_team a, sport_team b WHERE a.sport_division_short_name = :nfc_div AND b.sport_division_short_name = :afc_div ORDER BY a.name,b.name", nfc_div=nfc_tab[i], afc_div=afc_tab[i]):
            if trec.home_id == trec.t2_id:
                db_conn.execute("INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id,start_date_time) VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)", sport_type_name=sport_type_name, home_team_id=trec.t2_id, away_team_id=trec.t1_id, location_id=trec.t2_field_id, start_date_time=date_tab[trec.cur_row])
            else:
                db_conn.execute("INSERT INTO sporting_event(sport_type_name, home_team_id, away_team_id, location_id,start_date_time) VALUES(:sport_type_name, :home_team_id, :away_team_id, :location_id, :start_date_time)", sport_type_name=sport_type_name, home_team_id=trec.t1_id, away_team_id=trec.t2_id, location_id=trec.t1_field_id, start_date_time=date_tab[trec.cur_row])

