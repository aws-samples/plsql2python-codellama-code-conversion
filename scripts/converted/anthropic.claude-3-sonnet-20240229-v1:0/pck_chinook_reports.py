import cx_Oracle
def GET_ARTIST_BY_ALBUM(db_conn, p_artist_id):
    # Assuming you have a function to execute SQL queries
    # and return the result as a list of tuples
    query = """
        SELECT ART.NAME
        FROM ALBUM ALB
        JOIN ARTIST ART USING (ARTISTID)
        WHERE ALB.TITLE = :p_artist_id
    """
    result = execute_query(db_conn, query, p_artist_id=p_artist_id)

    if result:
        v_artist_name = result[0][0]
        print(f'ArtistName: {v_artist_name}')
    else:
        print('No artist found for the given album title.')



def cust_invoice_by_year_analyze(db_conn):
    cursor = db_conn.cursor()
    
    # Execute the query to fetch customer data
    query = """
        SELECT CUSTOMERID, CUSTNAME, LOW_YEAR, HIGH_YEAR, CUST_AVG
        FROM TMP_CUST_INVOICE_ANALYSE
    """
    cursor.execute(query)
    customer_data = cursor.fetchall()
    
    for cust in customer_data:
        customerid, custname, low_year, high_year, cust_avg = cust
        
        if int(low_year[-4:]) > int(high_year[-4:]):
            # Fetch customer's preferred genres
            query = """
                SELECT LISTAGG(GENRE, ',') WITHIN GROUP (ORDER BY GENRE)
                FROM (
                    SELECT DISTINCT FUNC_GENRE_BY_ID(TRC.GENREID) AS GENRE
                    FROM TMP_CUST_INVOICE_ANALYSE TMPTBL
                    JOIN INVOICE INV USING(CUSTOMERID)
                    JOIN INVOICELINE INVLIN ON INV.INVOICEID = INVLIN.INVOICEID
                    JOIN TRACK TRC ON TRC.TRACKID = INVLIN.TRACKID
                    WHERE CUSTOMERID = :customerid
                )
            """
            cursor.execute(query, customerid=customerid)
            cust_genres = cursor.fetchone()[0]
            
            print(f"Customer: {custname.upper()} - Offer a Discount According To Preferred Genres: {cust_genres.upper()}")
    
    cursor.close()

