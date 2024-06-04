import cx_Oracle
def GET_ARTIST_BY_ALBUM(db_conn, p_artist_id):
    """
    Retrieves the artist name for the given album title.

    Args:
        db_conn (cx_Oracle.Connection): Database connection object.
        p_artist_id (str): Album title.

    Returns:
        str: Artist name.
    """
    # Declare variables
    v_artist_name = None

    # Execute SQL query
    with db_conn.cursor() as cursor:
        query = """
            SELECT ART.NAME
            FROM ALBUM ALB
            JOIN ARTIST ART USING (ARTISTID)
            WHERE ALB.TITLE = :p_artist_id
        """
        cursor.execute(query, {'p_artist_id': p_artist_id})
        result = cursor.fetchone()
        if result:
            v_artist_name = result[0]

    # Print the artist name
    print(f'ArtistName: {v_artist_name}')

    return v_artist_name

def CUST_INVOICE_BY_YEAR_ANALYZE(db_conn):
    """
    Converts the given PL/SQL code to an equivalent Python function.
    
    Args:
        db_conn (cx_Oracle.Connection): The database connection object.
    """
    for v in db_conn.execute("SELECT CUSTOMERID, CUSTNAME, LOW_YEAR, HIGH_YEAR, CUST_AVG FROM TMP_CUST_INVOICE_ANALYSE"):
        if v.LOW_YEAR[-4:] > v.HIGH_YEAR[-4:]:
            v_cust_genres = ",".join([
                FUNC_GENRE_BY_ID(trc.GENREID)
                for trc in db_conn.execute("""
                    SELECT DISTINCT FUNC_GENRE_BY_ID(TRC.GENREID) AS GENRE
                    FROM TMP_CUST_INVOICE_ANALYSE TMPTBL
                    JOIN INVOICE INV USING(CUSTOMERID)
                    JOIN INVOICELINE INVLIN ON INV.INVOICEID = INVLIN.INVOICEID
                    JOIN TRACK TRC ON TRC.TRACKID = INVLIN.TRACKID
                    WHERE CUSTOMERID = :customerid
                """, customerid=v.CUSTOMERID)
            ])
            print(f"Customer: {v.CUSTNAME.upper()} - Offer a Discount According To Preferred Genres: {v_cust_genres.upper()}")

