import cx_Oracle
def generate_tickets(db_conn, P_event_id):
    # Define a cursor to retrieve the event information
    event_cur = db_conn.cursor()
    event_cur.execute("SELECT id, location_id FROM sporting_event WHERE ID = :P_event_id", {"P_event_id": P_event_id})

    # Define a variable to store the standard price
    standard_price = db_conn.execute("SELECT DBMS_RANDOM.VALUE(30, 50) FROM DUAL").fetchone()[0]

    # Loop through the event records and generate tickets
    for event_rec in event_cur:
        # Define a cursor to insert the tickets
        ticket_cur = db_conn.cursor()
        ticket_cur.execute("""
            INSERT /*+ APPEND */ INTO sporting_event_ticket(id, sporting_event_id, sport_location_id, seat_level, seat_section, seat_row, seat, ticket_price)
            SELECT sporting_event_ticket_seq.nextval, sporting_event.id, seat.sport_location_id, seat.seat_level, seat.seat_section, seat.seat_row, seat.seat,
                (CASE
                    WHEN seat.seat_type = 'luxury' THEN 3*standard_price
                    WHEN seat.seat_type = 'premium' THEN 2*standard_price
                    WHEN seat.seat_type = 'standard' THEN standard_price
                    WHEN seat.seat_type = 'sub-standard' THEN 0.8*standard_price
                    WHEN seat.seat_type = 'obstructed' THEN 0.5*standard_price
                    WHEN seat.seat_type = 'standing' THEN 0.5*standard_price
                END) ticket_price
            FROM sporting_event, seat
            WHERE sporting_event.location_id = seat.sport_location_id
            AND sporting_event.id = :event_id
        """, {"event_id": event_rec[0]})

        # Commit the changes
        db_conn.commit()

