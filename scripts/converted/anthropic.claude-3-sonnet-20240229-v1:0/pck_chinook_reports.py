import cx_Oracle
def GET_ARTIST_BY_ALBUM(db_conn, p_album_title):
    # Declare variables
    v_artist_name = None

    # Execute the query
    query = """
        SELECT ART.NAME
        FROM ALBUM ALB
        JOIN ARTIST ART USING (ARTISTID)
        WHERE ALB.TITLE = :p_album_title
    """
    cursor = db_conn.cursor()
    cursor.execute(query, p_album_title=p_album_title)
    result = cursor.fetchone()

    # Assign the result to the variable
    if result:
        v_artist_name = result[0]

    # Print the result
    print(f'ArtistName: {v_artist_name}')

    # Close the cursor
    cursor.close()



def cust_invoice_by_year_analyze(db_conn):
    cursor = db_conn.cursor()
    
    query = """
        SELECT CUSTOMERID, CUSTNAME, LOW_YEAR, HIGH_YEAR, CUST_AVG
        FROM TMP_CUST_INVOICE_ANALYSE
    """
    cursor.execute(query)
    
    for row in cursor:
        customerid, custname, low_year, high_year, cust_avg = row
        
        if int(low_year[-4:]) > int(high_year[-4:]):
            query = """
                SELECT LISTAGG(GENRE, ',') WITHIN GROUP (ORDER BY GENRE)
                FROM (
                    SELECT DISTINCT FUNC_GENRE_BY_ID(TRC.GENREID) AS GENRE
                    FROM TMP_CUST_INVOICE_ANALYSE TMPTBL
                    JOIN INVOICE INV USING (CUSTOMERID)
                    JOIN INVOICELINE INVLIN ON INV.INVOICEID = INVLIN.INVOICEID
                    JOIN TRACK TRC ON TRC.TRACKID = INVLIN.TRACKID
                    WHERE CUSTOMERID = :customerid
                )
            """
            cursor.execute(query, customerid=customerid)
            v_cust_genres = cursor.fetchone()[0]
            
            print(f"Customer: {custname.upper()} - Offer a Discount According To Preferred Genres: {v_cust_genres.upper()}")
    
    cursor.close()

# Assuming you have a function `func_genre_by_id` that takes a database connection and a genre ID as parameters
def func_genre_by_id(db_conn, genre_id):
    # Implementation goes here
    ...
    return genre_name

