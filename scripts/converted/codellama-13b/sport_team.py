import cx_Oracle
def LoadMLBTeams(db_conn):
    v_div = None

    cursor = db_conn.cursor()
    cursor.execute("""
        select distinct decode(TRIM(mlb_team),'AAA','LAA',mlb_team) a_name,
                       decode(TRIM(mlb_team_long),'Anaheim Angels', 'Los Angeles Angels',mlb_team_long) l_name
        from mlb_data
    """)

    for trec in cursor:
        if trec.a_name in ('BAL', 'BOS', 'TOR', 'TB', 'NYY'):
            v_div = 'AL East'
        elif trec.a_name in ('CLE', 'DET', 'KC', 'CWS', 'MIN'):
            v_div = 'AL Central'
        elif trec.a_name in ('TEX', 'SEA', 'HOU', 'OAK', 'LAA'):
            v_div = 'AL West'
        elif trec.a_name in ('WSH', 'MIA', 'NYM', 'PHI', 'ATL'):
            v_div = 'NL East'
        elif trec.a_name in ('CHC', 'STL', 'PIT', 'MIL', 'CIN'):
            v_div = 'NL Central'
        elif trec.a_name in ('COL', 'SD', 'LAD', 'SF', 'ARI'):
            v_div = 'NL West'

        cursor.execute("""
            insert into sport_team(name, abbreviated_name, sport_type_name, sport_league_short_name, sport_division_short_name)
            values(:1, :2, 'baseball', 'MLB', :3)
        """, (trec.l_name, trec.a_name, v_div))

    cursor.close()

