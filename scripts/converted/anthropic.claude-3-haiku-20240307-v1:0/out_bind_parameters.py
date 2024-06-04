import cx_Oracle
def test_pg_calc_stats_new1(db_conn, a, b):
    """
    Calculates the sum of two numbers.

    Args:
        db_conn (cx_Oracle.Connection): Database connection object.
        a (int): First number.
        b (int): Second number.

    Returns:
        int: The sum of a and b.
    """
    result = a + b
    return result

