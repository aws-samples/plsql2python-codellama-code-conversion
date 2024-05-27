import cx_Oracle
def sellTickets(db_conn, person_id, event_id, quantity=1):
    class not_enough_seats(Exception):
        pass

    p_person_id = person_id
    p_event_id = event_id
    p_quantity = quantity

    r_seat_level = None
    r_seat_section = None
    r_seat_row = None

    event_rec = get_event_details(db_conn, p_event_id)

    try:
        with db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT seat_level, seat_section, seat_row
                FROM (
                    SELECT seat_level, seat_section, seat_row
                    FROM sporting_event_ticket
                    WHERE sporting_event_id = %s
                    AND ticketholder_id IS NULL
                    GROUP BY seat_level, seat_section, seat_row
                    HAVING COUNT(*) >= %s
                )
                WHERE ROWNUM < 2
            """, (p_event_id, p_quantity))
            r_seat_level, r_seat_section, r_seat_row = cursor.fetchone()
    except:
        raise not_enough_seats

    with db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM sporting_event_ticket
            WHERE sporting_event_id = %s
            AND seat_level = %s
            AND seat_section = %s
            AND seat_row = %s
            ORDER BY seat_level, seat_section, seat_row
            FOR UPDATE OF ticketholder_id
        """, (p_event_id, r_seat_level, r_seat_section, r_seat_row))
        for i in range(p_quantity):
            cur_ticket = cursor.fetchone()
            cursor.execute("""
                UPDATE sporting_event_ticket
                SET ticketholder_id = %s
                WHERE CURRENT OF CURSOR
            """, (p_person_id,))
            cursor.execute("""
                INSERT INTO ticket_purchase_hist(sporting_event_ticket_id, purchased_by_id, transaction_date_time, purchase_price)
                VALUES(%s, %s, CURRENT_TIMESTAMP, %s)
            """, (cur_ticket.id, p_person_id, cur_ticket.ticket_price))
        db_conn.commit()

    if r_seat_level is None or r_seat_section is None or r_seat_row is None:
        raise not_enough_seats

    return None

def get_event_details(db_conn, event_id):
    # Implement the get_event_details function here
    pass

def transferTicket(db_conn, ticket_id, new_ticketholder_id, transfer_all=False, price=None):
    p_ticket_id = ticket_id
    p_new_ticketholder_id = new_ticketholder_id
    p_price = price
    xferall = 1 if transfer_all else 0
    old_ticketholder_id = None

    with db_conn.cursor() as cursor:
        # Get the last transaction date and the old ticketholder ID
        cursor.execute("""
            SELECT MAX(h.transaction_date_time) AS transaction_date_time,
                   t.ticketholder_id AS ticketholder_id
            FROM ticket_purchase_hist h
            JOIN sporting_event_ticket t ON t.id = :p_ticket_id
            WHERE h.purchased_by_id = t.ticketholder_id
              AND (h.sporting_event_ticket_id = :p_ticket_id OR :xferall = 1)
            GROUP BY t.ticketholder_id
        """, {'p_ticket_id': p_ticket_id, 'xferall': xferall})
        last_txn_date, old_ticketholder_id = cursor.fetchone()

        # Transfer the ticket(s)
        cursor.execute("""
            SELECT *
            FROM ticket_purchase_hist
            WHERE purchased_by_id = :old_ticketholder_id
              AND transaction_date_time = :last_txn_date
        """, {'old_ticketholder_id': old_ticketholder_id, 'last_txn_date': last_txn_date})
        for xrec in cursor:
            cursor.execute("""
                UPDATE sporting_event_ticket
                SET ticketholder_id = :p_new_ticketholder_id
                WHERE id = :sporting_event_ticket_id
            """, {'p_new_ticketholder_id': p_new_ticketholder_id, 'sporting_event_ticket_id': xrec.sporting_event_ticket_id})
            cursor.execute("""
                INSERT INTO ticket_purchase_hist(sporting_event_ticket_id, purchased_by_id, transferred_from_id, transaction_date_time, purchase_price)
                VALUES(:sporting_event_ticket_id, :p_new_ticketholder_id, :old_ticketholder_id, CURRENT_TIMESTAMP, NVL(:p_price, :purchase_price))
            """, {'sporting_event_ticket_id': xrec.sporting_event_ticket_id,
                  'p_new_ticketholder_id': p_new_ticketholder_id,
                  'old_ticketholder_id': old_ticketholder_id,
                  'p_price': p_price,
                  'purchase_price': xrec.purchase_price})

        db_conn.commit()

import time

def generateTicketActivity(db_conn, transaction_delay, max_transactions=1000):
    txn_count = 0

    while txn_count < max_transactions:
        sellRandomTickets(db_conn)
        txn_count += 1
        time.sleep(transaction_delay)

    return None

def sellRandomTickets(db_conn):
    # Implement the logic to sell random tickets
    # This function should be defined separately
    pass

import random
import time

def generateTransferActivity(db_conn, transaction_delay=5, max_transactions=100):
    txn_count = 0
    
    while txn_count < max_transactions:
        with db_conn.cursor() as cursor:
            # Get the minimum and maximum ticket IDs
            cursor.execute("SELECT MIN(sporting_event_ticket_id), MAX(sporting_event_ticket_id) FROM ticket_purchase_hist")
            min_tik_id, max_tik_id = cursor.fetchone()
            
            # Get a random ticket ID
            cursor.execute("SELECT MAX(sporting_event_ticket_id) FROM ticket_purchase_hist WHERE sporting_event_ticket_id <= %s", (random.uniform(min_tik_id, max_tik_id),))
            tik_id = cursor.fetchone()[0]
            
            # Get a random new ticket holder
            new_ticketholder = random.randint(g_min_person_id, g_max_person_id)
            
            # Decide whether to transfer all tickets or not
            xfer_all = random.randint(1, 5) < 5  # 80% of the time
            
            new_price = None
            
            # Decide whether to change the price
            chg_price = random.randint(1, 3) == 1  # 30% of the time
            if chg_price:
                cursor.execute("SELECT ticket_price FROM sporting_event_ticket WHERE id = %s", (tik_id,))
                ticket_price = cursor.fetchone()[0]
                new_price = ticket_price * random.uniform(0.8, 1.2)
            
            transferTicket(db_conn, tik_id, new_ticketholder, xfer_all, new_price)
            
            txn_count += 1
            time.sleep(transaction_delay)
    
    return None

# Assuming the transferTicket function is already defined
def transferTicket(db_conn, tik_id, new_ticketholder, xfer_all, new_price):
    with db_conn.cursor() as cursor:
        # Implement the logic to transfer the ticket(s)
        pass

def get_event_details(db_conn, event_id):
    """
    Retrieves the details of a sporting event.

    Args:
        db_conn (cx_Oracle.Connection): The database connection object.
        event_id (int): The ID of the sporting event.

    Returns:
        dict: A dictionary containing the event details, with the following keys:
            - sport_name
            - home_team_name
            - away_team_name
            - home_field
            - date_time
    """
    eventRec = {}

    with db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT e.sport_type_name,
                   h.name AS home_team_name,
                   a.name AS away_team_name,
                   l.name AS home_field,
                   e.start_date_time AS date_time
            FROM sporting_event e
            JOIN sport_team h ON e.home_team_id = h.id
            JOIN sport_team a ON e.away_team_id = a.id
            JOIN sport_location l ON e.location_id = l.id
            WHERE e.id = :event_id
        """, event_id=event_id)

        row = cursor.fetchone()
        if row:
            eventRec = {
                "sport_name": row[0],
                "home_team_name": row[1],
                "away_team_name": row[2],
                "home_field": row[3],
                "date_time": row[4]
            }

    return eventRec

import random

def sellRandomTickets(db_conn):
    event_tab = get_open_events(db_conn)
    row_ct = len(event_tab)
    event_idx = int(random.uniform(1, row_ct))
    event_id = event_tab[event_idx-1].id
    ticket_holder = int(random.uniform(g_min_person_id, g_max_person_id))
    quantity = int(random.uniform(1, 6))
    sellTickets(db_conn, ticket_holder, event_id, quantity)

def get_open_events(db_conn):
    # Implement the logic to fetch the list of open events
    # and return it as a list of event objects
    pass

def sellTickets(db_conn, ticket_holder, event_id, quantity):
    # Implement the logic to sell the specified number of tickets
    # for the given event to the specified ticket holder
    pass

# Assuming these global variables are defined elsewhere
g_min_person_id = 1
g_max_person_id = 1000000

def get_open_events(db_conn):
    event_tab = []

    with db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM sporting_event
            WHERE sold_out = 0
            ORDER BY start_date_time
        """)
        rows = cursor.fetchall()

    for row in rows:
        event_tab.append(row)

    return event_tab

