import cx_Oracle
def get_artist_by_album(p_artist_id, connection):
    cursor = connection.cursor()
    query = "SELECT ART.NAME FROM ALBUM ALB JOIN ARTIST ART USING (ARTISTID) WHERE ALB.TITLE = :p_artist_id"
    cursor.execute(query, {"p_artist_id": p_artist_id})
    artist_name = cursor.fetchone()[0]
    print(f"ArtistName: {artist_name}")

def cust_invoice_by_year_analyze(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT CUSTOMERID, CUSTNAME, LOW_YEAR, HIGH_YEAR, CUST_AVG FROM TMP_CUST_INVOICE_ANALYSE")
    rows = cursor.fetchall()
    for row in rows:
        if int(row[2]) > int(row[3]):
            cursor.execute("SELECT LISTAGG(GENRE, ',') WITHIN GROUP (ORDER BY GENRE) FROM (SELECT DISTINCT FUNC_GENRE_BY_ID(TRC.GENREID) AS GENRE FROM TMP_CUST_INVOICE_ANALYSE TMPTBL JOIN INVOICE INV USING(CUSTOMERID) JOIN INVOICELINE INVLIN ON INV.INVOICEID = INVLIN.INVOICEID JOIN TRACK TRC ON TRC.TRACKID = INVLIN.TRACKID WHERE CUSTOMERID=:CUSTOMERID)", {"CUSTOMERID": row[0]})
            genres = cursor.fetchone()[0]
            print("Customer: " + row[1].upper() + " - Offer a Discount According To Preferred Genres: " + genres.upper())

