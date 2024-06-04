PROCEDURE generateTransferActivity(transaction_delay IN NUMBER DEFAULT 5, max_transactions IN NUMBER DEFAULT 100) IS
  txn_count NUMBER := 0;
  min_tik_id sporting_event_ticket.id%TYPE;
  max_tik_id sporting_event_ticket.id%TYPE;
  tik_id     sporting_event_ticket.id%TYPE;
  new_ticketholder person.id%TYPE;
  xfer_all  BOOLEAN;
  chg_price BOOLEAN;
  new_price sporting_event_ticket.ticket_price%TYPE;


BEGIN
  WHILE txn_count < max_transactions LOOP
      SELECT min(sporting_event_ticket_id), max(sporting_event_ticket_id)
      INTO   min_tik_id, max_tik_id
      FROM  ticket_purchase_hist;

      SELECT MAX(sporting_event_ticket_id)
      INTO   tik_id
      FROM   ticket_purchase_hist
      WHERE  sporting_event_ticket_id <= dbms_random.value(min_tik_id,max_tik_id);

      new_ticketholder := TRUNC(dbms_random.value(g_min_person_id,g_max_person_id));

      xfer_all := (ROUND(dbms_random.value(1,5)) < 5);   -- transfer all tickets 80% of the time

      new_price := NULL;

      chg_price := (ROUND(dbms_random.value(1,3)) = 1);  --  30% of the time change price
      IF chg_price  THEN 
        SELECT dbms_random.value(0.8,1.2) * ticket_price INTO new_price
        FROM   sporting_event_ticket
        WHERE  id = tik_id;
      END IF;

      transferTicket(tik_id, new_ticketholder, xfer_all, new_price);

      txn_count := txn_count +1;
      dbms_lock.sleep(transaction_delay);
    END LOOP;
EXCEPTION WHEN NO_DATA_FOUND THEN
    dbms_output.put_line('No tickets available to transfer.');

END;

