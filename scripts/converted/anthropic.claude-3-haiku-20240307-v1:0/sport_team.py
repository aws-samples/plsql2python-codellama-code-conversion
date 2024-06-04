import cx_Oracle
def LoadMLBTeams(db_conn):
    """
    Loads MLB team information into the sport_team table.
    
    Args:
        db_conn (cx_Oracle.Connection): The database connection object.
    """
    
    # Define a cursor to execute the query
    cursor = db_conn.cursor()
    
    # Execute the query to get the MLB team information
    cursor.execute("""
        SELECT DISTINCT
            DECODE(TRIM(mlb_team), 'AAA', 'LAA', mlb_team) AS a_name,
            DECODE(TRIM(mlb_team_long), 'Anaheim Angels', 'Los Angeles Angels', mlb_team_long) AS l_name
        FROM mlb_data
    """)
    
    # Iterate through the results
    for trec in cursor:
        # Determine the division based on the team abbreviation
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
        
        # Insert the team information into the sport_team table
        insert_query = """
            INSERT INTO sport_team (name, abbreviated_name, sport_type_name, sport_league_short_name, sport_division_short_name)
            VALUES (:l_name, :a_name, 'baseball', 'MLB', :v_div)
        """
        cursor.execute(insert_query, {'l_name': trec.l_name, 'a_name': trec.a_name, 'v_div': v_div})
    
    # Commit the changes
    db_conn.commit()

