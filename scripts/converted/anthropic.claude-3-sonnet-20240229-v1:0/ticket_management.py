import cx_Oracle


def sellTickets(db_conn, person_id, event_id, quantity=1):
    not_enough_seats = Exception("Not enough seats")

    p_person_id = person_id
    p_event_id = event_id
    p_quantity = quantity

    event_rec = get_event_details(db_conn, p_event_id)

    try:
        with db_conn.cursor() as cursor:
            query = """
                SELECT seat_level, seat_section, seat_row
                FROM (
                    SELECT seat_level, seat_section, seat_row
                    FROM sporting_event_ticket
                    WHERE sporting_event_id = :event_id
                    AND ticketholder_id IS NULL
                    GROUP BY seat_level, seat_section, seat_row
                    HAVING COUNT(*) >= :quantity
                )
                WHERE rownum < 2
            """
            cursor.execute(query, {'event_id': p_event_id, 'quantity': p_quantity})
            r_seat_level, r_seat_section, r_seat_row = cursor.fetchone()

        adjacent_seats_query = """
            SELECT *
            FROM sporting_event_ticket
            WHERE sporting_event_id = :event_id
            AND seat_level = :seat_level
            AND seat_section = :seat_section
            AND seat_row = :seat_row
            ORDER BY seat_level, seat_section, seat_row
            FOR UPDATE OF ticketholder_id
        """

        with db_conn.cursor() as adjacent_seats_cursor:
            adjacent_seats_cursor.execute(adjacent_seats_query, {
                'event_id': p_event_id,
                'seat_level': r_seat_level,
                'seat_section': r_seat_section,
                'seat_row': r_seat_row
            })

            for _ in range(p_quantity):
                cur_ticket = adjacent_seats_cursor.fetchone()

                if cur_ticket is None:
                    raise not_enough_seats

                adjacent_seats_cursor.updateRow([p_person_id])

                insert_purchase_query = """
                    INSERT INTO ticket_purchase_hist (
                        sporting_event_ticket_id,
                        purchased_by_id,
                        transaction_date_time,
                        purchase_price
                    ) VALUES (
                        :ticket_id,
                        :person_id,
                        SYSDATE,
                        :ticket_price
                    )
                """
                with db_conn.cursor() as insert_cursor:
                    insert_cursor.execute(insert_purchase_query, {
                        'ticket_id': cur_ticket[0],
                        'person_id': p_person_id,
                        'ticket_price': cur_ticket[6]
                    })

            db_conn.commit()

    except not_enough_seats:
        print(f"Sorry, there aren't {p_quantity} adjacent seats for event:")
        print(f"   {event_rec.home_team_name} VS {event_rec.away_team_name}   ({event_rec.sport_name})")
        print(f"   {event_rec.home_field}:  {event_rec.date_time.strftime('%d-%b-%Y %H:%M')}")

def get_event_details(db_conn, event_id):
    # Assume this function already exists and returns an EventRecType object
    pass



def transferTicket(db_conn, ticket_id, new_ticketholder_id, transfer_all=False, price=None):
    p_ticket_id = ticket_id
    p_new_ticketholder_id = new_ticketholder_id
    p_price = price
    xferall = 1 if transfer_all else 0
    old_ticketholder_id = None
    last_txn_date = None

    # Retrieve the last transaction date and old ticketholder ID
    cursor = db_conn.cursor()
    query = """
        SELECT MAX(h.transaction_date_time) AS transaction_date_time,
               t.ticketholder_id AS ticketholder_id
        FROM ticket_purchase_hist h
        JOIN sporting_event_ticket t ON t.id = :p_ticket_id
        WHERE h.purchased_by_id = t.ticketholder_id
        AND (h.sporting_event_ticket_id = :p_ticket_id OR :xferall = 1)
        GROUP BY t.ticketholder_id
    """
    cursor.execute(query, {'p_ticket_id': p_ticket_id, 'xferall': xferall})
    result = cursor.fetchone()
    if result:
        last_txn_date, old_ticketholder_id = result

    if last_txn_date and old_ticketholder_id:
        # Retrieve the ticket purchase history for the old ticketholder
        txfr_cur = """
            SELECT * FROM ticket_purchase_hist
            WHERE purchased_by_id = :old_ticketholder_id
            AND transaction_date_time = :last_txn_date
        """
        cursor.execute(txfr_cur, {'old_ticketholder_id': old_ticketholder_id, 'last_txn_date': last_txn_date})
        txfr_records = cursor.fetchall()

        for xrec in txfr_records:
            # Update the ticketholder ID for the ticket
            update_query = """
                UPDATE sporting_event_ticket
                SET ticketholder_id = :p_new_ticketholder_id
                WHERE id = :ticket_id
            """
            cursor.execute(update_query, {'p_new_ticketholder_id': p_new_ticketholder_id, 'ticket_id': xrec[0]})

            # Insert a new record in the ticket purchase history
            purchase_price = p_price if p_price is not None else xrec[4]
            insert_query = """
                INSERT INTO ticket_purchase_hist (sporting_event_ticket_id, purchased_by_id, transferred_from_id, transaction_date_time, purchase_price)
                VALUES (:ticket_id, :p_new_ticketholder_id, :old_ticketholder_id, SYSDATE, :purchase_price)
            """
            cursor.execute(insert_query, {'ticket_id': xrec[0], 'p_new_ticketholder_id': p_new_ticketholder_id, 'old_ticketholder_id': old_ticketholder_id, 'purchase_price': purchase_price})

        db_conn.commit()
    else:
        db_conn.rollback()
        raise Exception("No ticket found or transaction history not available.")

    cursor.close()

import time

def generate_ticket_activity(db_conn, transaction_delay, max_transactions=1000):
    txn_count = 0

    while txn_count < max_transactions:
        sell_random_tickets(db_conn)
        txn_count += 1
        time.sleep(transaction_delay)

def sell_random_tickets(db_conn):
    # Implement the logic to sell random tickets
    # using the provided database connection (db_conn)
    pass

import random
from typing import Optional

def generate_transfer_activity(db_conn, transaction_delay: int = 5, max_transactions: int = 100):
    txn_count = 0
    cursor = db_conn.cursor()

    while txn_count < max_transactions:
        try:
            cursor.execute("SELECT min(sporting_event_ticket_id), max(sporting_event_ticket_id) FROM ticket_purchase_hist")
            min_tik_id, max_tik_id = cursor.fetchone()

            tik_id = cursor.execute("""
                SELECT MAX(sporting_event_ticket_id)
                FROM ticket_purchase_hist
                WHERE sporting_event_ticket_id <= :random_value
            """, random_value=random.randint(min_tik_id, max_tik_id)).fetchone()[0]

            new_ticketholder = int(random.uniform(g_min_person_id, g_max_person_id))

            xfer_all = random.randint(1, 5) < 5  # transfer all tickets 80% of the time

            new_price: Optional[float] = None

            chg_price = random.randint(1, 3) == 1  # 30% of the time change price
            if chg_price:
                cursor.execute("""
                    SELECT dbms_random.value(0.8, 1.2) * ticket_price
                    FROM sporting_event_ticket
                    WHERE id = :tik_id
                """, tik_id=tik_id)
                new_price = cursor.fetchone()[0]

            transfer_ticket(db_conn, tik_id, new_ticketholder, xfer_all, new_price)

            txn_count += 1
            time.sleep(transaction_delay)
        except NoDataFoundError:
            print('No tickets available to transfer.')
            break

    cursor.close()

def get_event_details(db_conn, event_id):
    event_rec = {}
    p_event_id = event_id

    query = """
        SELECT e.sport_type_name
              ,h.name
              ,a.name
              ,l.name
              ,e.start_date_time
        FROM sporting_event e
             ,sport_team h
             ,sport_team a
             ,sport_location l
        WHERE e.id = :p_event_id
        AND e.home_team_id = h.id
        AND e.away_team_id = a.id
        AND e.location_id = l.id
    """

    cursor = db_conn.cursor()
    cursor.execute(query, {'p_event_id': p_event_id})
    result = cursor.fetchone()

    if result:
        event_rec['sport_name'] = result[0]
        event_rec['home_team_name'] = result[1]
        event_rec['away_team_name'] = result[2]
        event_rec['home_field'] = result[3]
        event_rec['date_time'] = result[4]

    cursor.close()

    return event_rec

import random

def sellRandomTickets(db_conn):
    # Retrieve open events
    event_tab = get_open_events(db_conn)
    row_ct = len(event_tab)
    
    # Select a random event
    event_idx = random.randint(0, row_ct - 1)
    event_id = event_tab[event_idx]['id']
    
    # Select a random person and ticket quantity
    ticket_holder = random.randint(g_min_person_id, g_max_person_id)
    quantity = random.randint(1, 6)
    
    # Sell tickets
    sellTickets(db_conn, ticket_holder, event_id, quantity)



def get_open_events(db_conn):
    event_tab = []

    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT *
        FROM sporting_event
        WHERE sold_out = 0
        ORDER BY start_date_time
    """)

    for row in cursor:
        event_tab.append(row)

    cursor.close()
    return event_tab

