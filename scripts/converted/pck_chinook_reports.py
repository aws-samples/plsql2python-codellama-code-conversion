import cx_Oracle
def get_artist_by_album(p_artist_id, conn):
    cursor = conn.cursor()
    query = "SELECT ART.NAME FROM ALBUM ALB JOIN ARTIST ART USING (ARTISTID) WHERE ALB.TITLE = :p_artist_id"
    cursor.execute(query, {"p_artist_id": p_artist_id})
    artist_name = cursor.fetchone()[0]
    print(f"ArtistName: {artist_name}")

def cust_invoice_by_year_analyze(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT CUSTOMERID, CUSTNAME, LOW_YEAR, HIGH_YEAR, CUST_AVG FROM TMP_CUST_INVOICE_ANALYSE")
    rows = cursor.fetchall()
    for row in rows:
        customer_id = row[0]
        cust_name = row[1]
        low_year = row[2]
        high_year = row[3]
        cust_avg = row[4]
        if low_year > high_year:
            cursor.execute("SELECT LISTAGG(GENRE, ',') WITHIN GROUP (ORDER BY GENRE) FROM (SELECT DISTINCT FUNC_GENRE_BY_ID(TRC.GENREID) AS GENRE FROM TMP_CUST_INVOICE_ANALYSE TMPTBL JOIN INVOICE INV USING(CUSTOMERID) JOIN INVOICELINE INVLIN ON INV.INVOICEID = INVLIN.INVOICEID JOIN TRACK TRC ON TRC.TRACKID = INVLIN.TRACKID WHERE CUSTOMERID=:customer_id)", {"customer_id": customer_id})
            genres = cursor.fetchone()[0]
            print(f"Customer: {cust_name} - Offer a Discount According To Preferred Genres: {genres}")

