import cx_Oracle
def GET_ARTIST_BY_ALBUM(db_conn, p_album_title):
    with db_conn.cursor() as cursor:
        query = """
            SELECT ART.NAME
            FROM ALBUM ALB
            JOIN ARTIST ART USING (ARTISTID)
            WHERE ALB.TITLE = :album_title
        """
        cursor.execute(query, album_title=p_album_title)
        result = cursor.fetchone()

        if result:
            v_artist_name = result[0]
            print(f"ArtistName: {v_artist_name}")
        else:
            print("No artist found for the given album title.")

def cust_invoice_by_year_analyze(db_conn):
    # Assume FUNC_GENRE_BY_ID is a separate Python function that takes a genre ID and returns the genre name
    # You'll need to define this function separately

    # Execute the query and fetch the results
    query = """
        SELECT CUSTOMERID, CUSTNAME, LOW_YEAR, HIGH_YEAR, CUST_AVG
        FROM TMP_CUST_INVOICE_ANALYSE
    """
    cursor = db_conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()

    for row in results:
        customer_id = row[0]
        customer_name = row[1]
        low_year = row[2]
        high_year = row[3]
        cust_avg = row[4]

        if int(low_year[-4:]) > int(high_year[-4:]):
            # Execute the subquery to get the customer's preferred genres
            sub_query = """
                SELECT LISTAGG(GENRE, ',') WITHIN GROUP (ORDER BY GENRE)
                FROM (
                    SELECT DISTINCT FUNC_GENRE_BY_ID(TRC.GENREID) AS GENRE
                    FROM TMP_CUST_INVOICE_ANALYSE TMPTBL
                    JOIN INVOICE INV USING (CUSTOMERID)
                    JOIN INVOICELINE INVLIN ON INV.INVOICEID = INVLIN.INVOICEID
                    JOIN TRACK TRC ON TRC.TRACKID = INVLIN.TRACKID
                    WHERE CUSTOMERID = :cust_id
                )
            """
            sub_cursor = db_conn.cursor()
            sub_cursor.execute(sub_query, cust_id=customer_id)
            cust_genres = sub_cursor.fetchone()[0]
            sub_cursor.close()

            print(f"Customer: {customer_name.upper()} - Offer a Discount According To Preferred Genres: {cust_genres.upper()}")

    cursor.close()

