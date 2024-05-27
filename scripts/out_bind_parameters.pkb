PROCEDURE test_pg.calc_stats_new1 (a NUMBER, b NUMBER, result out NUMBER)
IS
BEGIN
result:=a+b;
END;
/
/* Testing */
set serveroutput on 
DECLARE
  a NUMBER := 4;
  b NUMBER := 7;
  plsql_block VARCHAR2(100);
  output number;
BEGIN
  plsql_block := 'BEGIN test_pg.calc_stats_new1(:a, :b,:output); END;';
  EXECUTE IMMEDIATE plsql_block USING a, b,out output;  -- calc_stats(a, a, b, a)
  DBMS_OUTPUT.PUT_LINE('output:'||output);
END;

