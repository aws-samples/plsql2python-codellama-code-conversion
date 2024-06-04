import cx_Oracle
import random

def generate_tickets(db_conn, p_event_id):
    # Fetch event details
    event_cur = db_conn.cursor()
    event_cur.execute("""
        SELECT id, location_id
        FROM sporting_event
        WHERE id = :p_event_id
    """, p_event_id=p_event_id)
    event_rec = event_cur.fetchone()
    event_cur.close()

    if event_rec is None:
        return  # Event not found

    event_id, location_id = event_rec

    # Generate standard ticket price
    standard_price = random.uniform(30, 50)

    # Fetch seat details and insert tickets
    seat_cur = db_conn.cursor()
    seat_cur.execute("""
        SELECT seat.sport_location_id, seat.seat_level, seat.seat_section, seat.seat_row, seat.seat, seat.seat_type
        FROM seat
        WHERE seat.sport_location_id = :location_id
    """, location_id=location_id)

    tickets = []
    for seat_rec in seat_cur:
        location_id, seat_level, seat_section, seat_row, seat, seat_type = seat_rec

        if seat_type == 'luxury':
            ticket_price = 3 * standard_price
        elif seat_type == 'premium':
            ticket_price = 2 * standard_price
        elif seat_type == 'standard':
            ticket_price = standard_price
        elif seat_type == 'sub-standard':
            ticket_price = 0.8 * standard_price
        elif seat_type == 'obstructed':
            ticket_price = 0.5 * standard_price
        elif seat_type == 'standing':
            ticket_price = 0.5 * standard_price

        ticket_id = call_sequence_function(db_conn, 'sporting_event_ticket_seq')
        ticket = (ticket_id, event_id, location_id, seat_level, seat_section, seat_row, seat, ticket_price)
        tickets.append(ticket)

    seat_cur.close()

    # Insert tickets into the database
    ticket_cur = db_conn.cursor()
    ticket_cur.executemany("""
        INSERT /*+ APPEND */ INTO sporting_event_ticket
            (id, sporting_event_id, sport_location_id, seat_level, seat_section, seat_row, seat, ticket_price)
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
    """, tickets)
    db_conn.commit()
    ticket_cur.close()

# Helper function to call a sequence and get the next value
def call_sequence_function(db_conn, sequence_name):
    seq_cur = db_conn.cursor()
    seq_cur.execute(f"SELECT {sequence_name}.nextval FROM dual")
    next_val = seq_cur.fetchone()[0]
    seq_cur.close()
    return next_val

