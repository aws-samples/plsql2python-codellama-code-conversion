import cx_Oracle
def p_json_test(db_conn, p_in_accounts_json, p_out_accunts_json):
    try:
        # Convert the JSON input to a Python dictionary
        p_in_accounts_json = json.loads(p_in_accounts_json)

        # Define the SQL query to retrieve the data
        query = """
            SELECT
                JSON_OBJECT(
                    'accountCounts' VALUE JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'businessUnitId' VALUE business_unit_id,
                            'parentAccountNumber' VALUE parent_account_number,
                            'accountNumber' VALUE account_number,
                            'totalOnlineContactsCount' VALUE online_contacts_count,
                            'countByPosition' VALUE
                            JSON_OBJECT(
                                'taxProfessionalCount' VALUE tax_count,
                                'attorneyCount' VALUE attorney_count,
                                'nonAttorneyCount' VALUE non_attorney_count,
                                'clerkCount' VALUE clerk_count
                            )
                        )
                    )
                )
            INTO p_out_accunts_json
            FROM (
                SELECT
                    tab_data.business_unit_id,
                    tab_data.parent_account_number,
                    tab_data.account_number,
                    SUM(1) online_contacts_count,
                    SUM(CASE WHEN tab_data.position_id = '0095' THEN 1 ELSE 0 END) tax_count,
                    SUM(CASE WHEN tab_data.position_id = '0100' THEN 1 ELSE 0 END) attorney_count,
                    SUM(CASE WHEN tab_data.position_id = '0090' THEN 1 ELSE 0 END) non_attorney_count,
                    SUM(CASE WHEN tab_data.position_id = '0050' THEN 1 ELSE 0 END) clerk_count
                FROM aws_test_table scco,
                    JSON_TABLE (json_doc, '$' ERROR ON ERROR
                    COLUMNS (
                        parent_account_number NUMBER PATH '$.data.account.parentAccountNumber',
                        account_number NUMBER PATH '$.data.account.accountNumber',
                        business_unit_id NUMBER PATH '$.data.account.businessUnitId',
                        position_id VARCHAR2(4) PATH '$.data.positionId'
                    )
                ) AS tab_data
                INNER JOIN JSON_TABLE (p_in_accounts_json, '$.accounts[*]' ERROR ON ERROR
                    COLUMNS (
                        parent_account_number PATH '$.parentAccountNumber',
                        account_number PATH '$.accountNumber',
                        business_unit_id PATH '$.businessUnitId'
                    )
                ) static_data
                ON (static_data.parent_account_number = tab_data.parent_account_number
                    AND static_data.account_number = tab_data.account_number
                    AND static_data.business_unit_id = tab_data.business_unit_id
                )
                GROUP BY
                    tab_data.business_unit_id,
                    tab_data.parent_account_number,
                    tab_data.account_number
            );
        """

        # Execute the query and retrieve the results
        cursor = db_conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        # Convert the results to a Python dictionary
        p_out_accunts_json = json.dumps(results)

    except Exception as e:
        raise_application_error(-20001, 'Error while running the JSON query')

    return p_out_accunts_json

