import cx_Oracle
def get_artist_by_album(db_conn, p_artist_id):
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
    # Converted Python code goes here
    cursor = db_conn.cursor()
    query = "SELECT CUSTOMERID, CUSTNAME, LOW_YEAR, HIGH_YEAR, CUST_AVG FROM TMP_CUST_INVOICE_ANALYSE"
    cursor.execute(query)
    results = cursor.fetchall()
    for row in results:
        customer_id = row[0]
        cust_name = row[1]
        low_year = row[2]
        high_year = row[3]
        cust_avg = row[4]
        if int(low_year[-4:]) > int(high_year[-4:]):
            query = "SELECT LISTAGG(GENRE, ',') WITHIN GROUP (ORDER BY GENRE) FROM (SELECT DISTINCT FUNC_GENRE_BY_ID(TRC.GENREID) AS GENRE FROM TMP_CUST_INVOICE_ANALYSE TMPTBL JOIN INVOICE INV USING(CUSTOMERID) JOIN INVOICELINE INVLIN ON INV.INVOICEID = INVLIN.INVOICEID JOIN TRACK TRC ON TRC.TRACKID = INVLIN.TRACKID WHERE CUSTOMERID=:customer_id)"
            cursor.execute(query, {"customer_id": customer_id})
            genres = cursor.fetchone()[0]
            print(f"Customer: {cust_name} - Offer a Discount According to Preferred Genres: {genres}")

