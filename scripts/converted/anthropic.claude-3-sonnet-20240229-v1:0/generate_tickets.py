import cx_Oracle
import math

def generate_tickets(db_conn, p_event_id):
    # Fetch event details
    event_cur = db_conn.cursor()
    event_cur.execute("SELECT id, location_id FROM sporting_event WHERE id = :p_id", p_id=p_event_id)
    event_rec = event_cur.fetchone()
    event_cur.close()

    if event_rec is None:
        return  # Event not found, return early

    # Generate standard ticket price
    standard_price = math.floor(random.uniform(30, 50) * 100) / 100

    # Insert tickets into the database
    ticket_cur = db_conn.cursor()
    for event_id, location_id in event_rec:
        ticket_cur.execute("""
            INSERT /*+ APPEND */ INTO sporting_event_ticket (
                id, sporting_event_id, sport_location_id, seat_level, seat_section, seat_row, seat, ticket_price
            )
            SELECT
                sporting_event_ticket_seq.nextval,
                :event_id,
                seat.sport_location_id,
                seat.seat_level,
                seat.seat_section,
                seat.seat_row,
                seat.seat,
                CASE seat.seat_type
                    WHEN 'luxury' THEN :luxury_price
                    WHEN 'premium' THEN :premium_price
                    WHEN 'standard' THEN :standard_price
                    WHEN 'sub-standard' THEN :sub_standard_price
                    WHEN 'obstructed' THEN :obstructed_price
                    WHEN 'standing' THEN :standing_price
                END AS ticket_price
            FROM seat
            WHERE seat.sport_location_id = :location_id
        """, event_id=event_id, location_id=location_id,
             luxury_price=3 * standard_price,
             premium_price=2 * standard_price,
             standard_price=standard_price,
             sub_standard_price=0.8 * standard_price,
             obstructed_price=0.5 * standard_price,
             standing_price=0.5 * standard_price)
    ticket_cur.close()
    db_conn.commit()

