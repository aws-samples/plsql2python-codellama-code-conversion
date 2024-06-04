import cx_Oracle
def sell_tickets(db_conn, person_id, event_id, quantity=1):
    not_enough_seats = Exception

    p_person_id = person_id
    p_event_id = event_id
    p_quantity = quantity

    r_seat_level = None
    r_seat_section = None
    r_seat_row = None

    event_rec = None

    cur_ticket = None

    try:
        event_rec = get_event_details(db_conn, p_event_id)

        with db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT seat_level, seat_section, seat_row
                FROM (
                    SELECT seat_level, seat_section, seat_row
                    FROM sporting_event_ticket
                    WHERE sporting_event_id = :p_event_id
                    AND ticketholder_id IS NULL
                    GROUP BY seat_level, seat_section, seat_row
                    HAVING COUNT(*) >= :p_quantity
                )
                WHERE rownum < 2
            """, {"p_event_id": p_event_id, "p_quantity": p_quantity})

            row = cursor.fetchone()
            if row is None:
                raise not_enough_seats

            r_seat_level, r_seat_section, r_seat_row = row

        with db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM sporting_event_ticket
                WHERE sporting_event_id = :p_event_id
                AND seat_level = :r_seat_level
                AND seat_section = :r_seat_section
                AND seat_row = :r_seat_row
                ORDER BY seat_level, seat_section, seat_row
                FOR UPDATE OF ticketholder_id
            """, {"p_event_id": p_event_id, "r_seat_level": r_seat_level, "r_seat_section": r_seat_section, "r_seat_row": r_seat_row})

            for i in range(p_quantity):
                cur_ticket = cursor.fetchone()
                cursor.execute("""
                    UPDATE sporting_event_ticket
                    SET ticketholder_id = :p_person_id
                    WHERE CURRENT OF :cursor
                """, {"p_person_id": p_person_id, "cursor": cursor})

                cursor.execute("""
                    INSERT INTO ticket_purchase_hist(sporting_event_ticket_id, purchased_by_id, transaction_date_time, purchase_price)
                    VALUES(:cur_ticket_id, :p_person_id, SYSDATE, :cur_ticket_price)
                """, {"cur_ticket_id": cur_ticket.id, "p_person_id": p_person_id, "cur_ticket_price": cur_ticket.ticket_price})

        db_conn.commit()

    except not_enough_seats:
        print("Sorry, there aren't {} adjacent seats for event:".format(p_quantity))
        print("   {} VS {}   ({})".format(event_rec.home_team_name, event_rec.away_team_name, event_rec.sport_name))
        print("   {}  {}".format(event_rec.home_field, event_rec.date_time.strftime("%d-%b-%Y %H:%M")))

def transferTicket(db_conn, ticket_id, new_ticketholder_id, transfer_all=False, price=None):
    # Declare variables
    p_ticket_id = ticket_id
    p_new_ticketholder_id = new_ticketholder_id
    p_price = price
    xferall = 0
    old_ticketholder_id = None
    last_txn_date = None

    # Define cursor
    txfr_cur = db_conn.cursor()

    # Check if transfer_all is True
    if transfer_all:
        xferall = 1

    # Get last transaction date and old ticketholder ID
    txfr_cur.execute("""
        SELECT max(h.transaction_date_time) as transaction_date_time,
               t.ticketholder_id as ticketholder_id
        FROM ticket_purchase_hist h, sporting_event_ticket t
        WHERE t.id = :ticket_id
        AND h.purchased_by_id = t.ticketholder_id
        AND ((h.sporting_event_ticket_id = :ticket_id) OR (xferall = 1))
        GROUP BY t.ticketholder_id
        """, {"ticket_id": ticket_id})
    last_txn_date, old_ticketholder_id = txfr_cur.fetchone()

    # Loop through ticket purchase history
    for xrec in txfr_cur.execute("""
        SELECT * FROM ticket_purchase_hist
        WHERE purchased_by_id = :old_ticketholder_id
        AND transaction_date_time = :last_txn_date
        """, {"old_ticketholder_id": old_ticketholder_id, "last_txn_date": last_txn_date}):
        # Update sporting event ticket
        db_conn.execute("""
            UPDATE sporting_event_ticket
            SET ticketholder_id = :new_ticketholder_id
            WHERE id = :ticket_id
            """, {"ticket_id": xrec["sporting_event_ticket_id"], "new_ticketholder_id": new_ticketholder_id})

        # Insert into ticket purchase history
        db_conn.execute("""
            INSERT INTO ticket_purchase_hist(sporting_event_ticket_id, purchased_by_id, transferred_from_id, transaction_date_time, purchase_price)
            VALUES(:ticket_id, :new_ticketholder_id, :old_ticketholder_id, SYSDATE, NVL(:price, :purchase_price))
            """, {"ticket_id": xrec["sporting_event_ticket_id"], "new_ticketholder_id": new_ticketholder_id, "old_ticketholder_id": old_ticketholder_id, "price": price, "purchase_price": xrec["purchase_price"]})

    # Commit changes
    db_conn.commit()

    # Return old ticketholder ID
    return old_ticketholder_id

def generateTicketActivity(db_conn, transaction_delay, max_transactions=1000):
    txn_count = 0
    while txn_count < max_transactions:
        sellRandomTickets(db_conn)
        txn_count += 1
        db_conn.sleep(transaction_delay)

def get_event_details(db_conn, event_id):
    eventRec = {}
    p_event_id = db_conn.var(cx_Oracle.NUMBER)
    p_event_id.setvalue(0, event_id)

    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT e.sport_type_name, h.name, a.name, l.name, e.start_date_time
        FROM sporting_event e, sport_team h, sport_team a, sport_location l
        WHERE e.id = :p_event_id
        AND e.home_team_id = h.id
        AND e.away_team_id = a.id
        AND e.location_id = l.id
    """, p_event_id=p_event_id)

    for row in cursor:
        eventRec['sport_name'] = row[0]
        eventRec['home_team_name'] = row[1]
        eventRec['away_team_name'] = row[2]
        eventRec['home_field'] = row[3]
        eventRec['date_time'] = row[4]

    return eventRec

def sell_random_tickets(db_conn):
    event_tab = get_open_events(db_conn)
    row_ct = event_tab.count()
    event_idx = int(dbms_random.value(1, row_ct))
    event_id = event_tab[event_idx].id
    ticket_holder = int(dbms_random.value(g_min_person_id, g_max_person_id))
    quantity = int(dbms_random.value(1, 6))
    sell_tickets(db_conn, ticket_holder, event_id, quantity)

def get_open_events(db_conn):
    event_tab = []

    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM sporting_event WHERE sold_out = 0 ORDER BY start_date_time")

    for row in cursor:
        event_tab.append(row)

    return event_tab

