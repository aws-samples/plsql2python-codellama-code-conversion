import cx_Oracle
def set_nfl_team_home_field(db_conn):
    """
    Set the home field for each NFL team based on the data in the nfl_stadium_data table.
    
    Args:
        db_conn (cx_Oracle.Connection): The database connection object.
    """
    with db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT sport_location_id, team 
            FROM nfl_stadium_data
        """)
        for row in cursor:
            sport_location_id, team = row
            cursor.execute("""
                UPDATE sport_team s
                SET s.home_field_id = :sport_location_id
                WHERE s.name = :team
                  AND s.sport_league_short_name = 'NFL'
                  AND s.sport_type_name = 'football'
            """, {
                'sport_location_id': sport_location_id,
                'team': team
            })
        db_conn.commit()

