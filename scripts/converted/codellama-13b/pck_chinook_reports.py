import cx_Oracle
def get_artist_by_album(db_conn, p_artist_id):
    # Converted Python code goes here
    v_artist_name = None
    with db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT ART.NAME
            FROM ALBUM ALB
            JOIN ARTIST ART USING (ARTISTID)
            WHERE ALB.TITLE = :p_artist_id
        """, {"p_artist_id": p_artist_id})
        v_artist_name = cursor.fetchone()[0]
    print(f"ArtistName: {v_artist_name}")
    return v_artist_name

def cust_invoice_by_year_analyze(db_conn):
    # Define a variable to store the customer genres
    cust_genres = ""

    # Loop through the result set of the query
    for row in db_conn.execute("SELECT CUSTOMERID, CUSTNAME, LOW_YEAR, HIGH_YEAR, CUST_AVG FROM TMP_CUST_INVOICE_ANALYSE"):
        # Extract the customer ID, name, and years from the row
        customer_id = row[0]
        customer_name = row[1]
        low_year = row[2]
        high_year = row[3]
        cust_avg = row[4]

        # Check if the low year is greater than the high year
        if low_year > high_year:
            # Call the function to get the customer genres
            cust_genres = get_customer_genres(db_conn, customer_id)

            # Print the customer name and genres
            print("Customer: " + customer_name.upper() + " - Offer a Discount According to Preferred Genres: " + cust_genres.upper())

    # Return the customer genres
    return cust_genres

# Define a function to get the customer genres
def get_customer_genres(db_conn, customer_id):
    # Define a variable to store the customer genres
    cust_genres = ""

    # Loop through the result set of the query
    for row in db_conn.execute("SELECT DISTINCT FUNC_GENRE_BY_ID(TRC.GENREID) AS GENRE FROM TMP_CUST_INVOICE_ANALYSE TMPTBL JOIN INVOICE INV USING(CUSTOMERID) JOIN INVOICELINE INVLIN ON INV.INVOICEID = INVLIN.INVOICEID JOIN TRACK TRC ON TRC.TRACKID = INVLIN.TRACKID WHERE CUSTOMERID=:customer_id", {"customer_id": customer_id}):
        # Extract the genre from the row
        genre = row[0]

        # Add the genre to the list of genres
        cust_genres += genre + ", "

    # Return the list of genres
    return cust_genres

