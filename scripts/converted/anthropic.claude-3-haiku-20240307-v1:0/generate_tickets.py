import cx_Oracle


def generate_tickets(db_conn, p_event_id):
    # Define cursor to fetch event details
    event_cur = db_conn.cursor()
    event_cur.execute("""
        SELECT id, location_id 
        FROM sporting_event
        WHERE id = :p_event_id
    """, p_event_id=p_event_id)

    # Generate a random standard price
    standard_price = round(cx_Oracle.var(float).getvalue(), 2)

    # Iterate over the events and insert tickets
    for event_rec in event_cur:
        event_id, location_id = event_rec

        # Insert tickets
        ticket_cur = db_conn.cursor()
        ticket_cur.execute("""
            INSERT INTO sporting_event_ticket
            (id, sporting_event_id, sport_location_id, seat_level, seat_section, seat_row, seat, ticket_price)
            SELECT sporting_event_ticket_seq.nextval, :event_id, seat.sport_location_id, seat.seat_level, seat.seat_section, seat.seat_row, seat.seat,
                CASE
                    WHEN seat.seat_type = 'luxury' THEN 3 * :standard_price
                    WHEN seat.seat_type = 'premium' THEN 2 * :standard_price
                    WHEN seat.seat_type = 'standard' THEN :standard_price
                    WHEN seat.seat_type = 'sub-standard' THEN 0.8 * :standard_price
                    WHEN seat.seat_type = 'obstructed' THEN 0.5 * :standard_price
                    WHEN seat.seat_type = 'standing' THEN 0.5 * :standard_price
                END AS ticket_price
            FROM seat
            WHERE seat.sport_location_id = :location_id
        """, event_id=event_id, standard_price=standard_price, location_id=location_id)

        # Commit the changes
        db_conn.commit()

