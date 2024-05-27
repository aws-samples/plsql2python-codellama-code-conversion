import cx_Oracle


def generate_tickets(db_conn, p_event_id):
    standard_price = None

    with db_conn.cursor() as cursor:
        # Execute the cursor to get the event details
        cursor.execute("""
            SELECT id, location_id
            FROM sporting_event
            WHERE id = :p_event_id
        """, p_event_id=p_event_id)
        event_rec = cursor.fetchone()

        # Generate a random standard price
        standard_price = round(cx_Oracle.var(float).getvalue(), 2)

        # Insert tickets for the event
        cursor.execute("""
            INSERT /*+ APPEND */ INTO sporting_event_ticket
            (id, sporting_event_id, sport_location_id, seat_level, seat_section, seat_row, seat, ticket_price)
            SELECT sporting_event_ticket_seq.nextval,
                   :sporting_event_id,
                   seat.sport_location_id,
                   seat.seat_level,
                   seat.seat_section,
                   seat.seat_row,
                   seat.seat,
                   CASE
                       WHEN seat.seat_type = 'luxury' THEN 3 * :standard_price
                       WHEN seat.seat_type = 'premium' THEN 2 * :standard_price
                       WHEN seat.seat_type = 'standard' THEN :standard_price
                       WHEN seat.seat_type = 'sub-standard' THEN 0.8 * :standard_price
                       WHEN seat.seat_type = 'obstructed' THEN 0.5 * :standard_price
                       WHEN seat.seat_type = 'standing' THEN 0.5 * :standard_price
                   END AS ticket_price
            FROM sporting_event, seat
            WHERE sporting_event.location_id = seat.sport_location_id
              AND sporting_event.id = :sporting_event_id
        """, sporting_event_id=event_rec[0], standard_price=standard_price)

        db_conn.commit()

