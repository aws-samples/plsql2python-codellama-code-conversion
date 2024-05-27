import cx_Oracle


def LoadMLBTeams(db_conn):
    v_div = None

    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT DISTINCT
            DECODE(TRIM(mlb_team), 'AAA', 'LAA', mlb_team) a_name,
            DECODE(TRIM(mlb_team_long), 'Anaheim Angels', 'Los Angeles Angels', mlb_team_long) l_name
        FROM mlb_data
    """)
    mlb_teams = cursor.fetchall()
    cursor.close()

    for trec in mlb_teams:
        if trec[0] in ('BAL', 'BOS', 'TOR', 'TB', 'NYY'):
            v_div = 'AL East'
        elif trec[0] in ('CLE', 'DET', 'KC', 'CWS', 'MIN'):
            v_div = 'AL Central'
        elif trec[0] in ('TEX', 'SEA', 'HOU', 'OAK', 'LAA'):
            v_div = 'AL West'
        elif trec[0] in ('WSH', 'MIA', 'NYM', 'PHI', 'ATL'):
            v_div = 'NL East'
        elif trec[0] in ('CHC', 'STL', 'PIT', 'MIL', 'CIN'):
            v_div = 'NL Central'
        elif trec[0] in ('COL', 'SD', 'LAD', 'SF', 'ARI'):
            v_div = 'NL West'

        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO sport_team (name, abbreviated_name, sport_type_name, sport_league_short_name, sport_division_short_name)
            VALUES (:l_name, :a_name, 'baseball', 'MLB', :v_div)
        """, l_name=trec[1], a_name=trec[0], v_div=v_div)
        db_conn.commit()
        cursor.close()

