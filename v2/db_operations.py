import pg8000

def get_psql_conn():
    return pg8000.connect(
        user="ro1",
        password="2x8g8w949tynkaka1",
        host="gasfree.cluster-ro-cmlrx8br13wh.us-east-1.rds.amazonaws.com",
        port="5432",
        database="gasfree"
    )

def execute_query(connection, query):
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Exception as error:
        print("Error while connecting to PostgreSQL or executing query", error)
        return []
    finally:
        if cursor:
            cursor.close()

def query_trx(connection, start_time, end_time, agg_type, state=None, bound=None, gt=None, address_relate=False):
    query_column = 'count(go.amount)' if agg_type == 'count' else 'sum(go.amount)'
    state_query = ""
    if state is not None:
        state_query += f" and go.state = '{state}'"
    if bound is not None and gt is not None:
        state_query += f" and go.amount {'>=' if gt else '<'} {bound}"
    if address_relate:
        query = (f"select {query_column} from gasfree_addresses ga inner join gasfree_offchains go on ga.gasfree_address = go.gasfree_address where go.created_at between '{start_time}' and '{end_time}' and ga.created_at between '{start_time}' and '{end_time}' {state_query}")
    else:
        query = (f"select {query_column} from gasfree_offchains go where go.created_at between '{start_time}' and '{end_time}' {state_query}")
    results = execute_query(connection, query)
    return results[0][0] if results else 0

def query_addresses(connection, lower_bound, upper_bound):
    query = (f"""
        SELECT COUNT(*) 
        FROM (
            SELECT ga.account_address 
            FROM gasfree_addresses ga 
            INNER JOIN gasfree_offchains go ON ga.gasfree_address = go.gasfree_address 
            GROUP BY ga.account_address 
            HAVING COUNT(go.id) >= {lower_bound} and COUNT(go.id) < {upper_bound}
        ) AS temp;
    """)
    results = execute_query(connection, query)
    return results[0][0] if results else 0

API_KEY_MAPPING = """
WITH api_key_mapping (api_key, company) AS (
    VALUES 
        ('0d834840-9b15-46e3-9af3-5eed9cba5f5d', 'Coin Wallet'),
        ('bb683af1-2d29-4bcb-bf28-ece532bcc5ae', 'Trigger'),
        ('56729450-99e2-4705-b2b6-817ad3abf5d6', 'Guarda Wallet'),
        ('ed69157d-a338-4da8-b355-641f243164cf', 'SafeWallet'),
        ('320e4c64-ef90-49f4-b462-cc614b4263f8', 'Walletverse'),
        ('19ebf423-1466-444e-bbc3-84be5cf2103f', 'Coinsenda'),
        ('d2dc932a-29d4-4b56-a21a-8276a68163a4', 'BitGo'),
        ('38df29b6-8a43-43a3-83a3-b724a8b0f10d', 'IM Token'),
        ('d6448b6f-92e8-4865-804c-aeacdca69a0b', 'BitGet'),
        ('d0795e19-0ba1-4e3b-bb8a-b18e2949aa78', 'Klever Wallet'),
        ('ccb3dfca-b3cf-41e2-b083-988079397041', 'Clicklead'),
        ('26394b70-32ce-4a88-8f13-5cd7d94cf2dd', 'Switchain'),
        ('91bbbde3-196b-43b3-8185-d7a4788338ca', 'edir by bixi'),
        ('b486c3da-2f4e-4443-8dfe-775c9b15629b', 'Banexcoin'),
        ('58c04d51-727d-43b2-85a4-da95bfb0a3b5', 'BitAfrika'),
        ('60c360fc-e1b5-4c00-93b7-c00a9198a489', 'Alua'),
        ('b737fd4d-15de-42b4-a6a0-9a206b910662', 'BitGate'),
        ('03d4c82a-0896-48e9-8851-5a9ad2edc9c2', 'Atomic Wallet'),
        ('3d622152-1cf7-4352-805c-5fbb30a6100d', 'Payouter'),
        ('107f5718-11c1-4e29-a9c4-20390435e57d','Armcoinwallet'),
        ('851adcbb-ad4d-45c6-87da-5a3c38fd67fe','SequoyaPay'),
        ('5e02d433-2e36-4a35-bcbf-fe32c5be17f0','Kobbex'),
        ('f187b074-7f7a-4a13-b435-f0ceb49934ea','Pixel'),
        ('8fb6caa0-a496-478c-bc0e-0e87fd5894b8','hero'),
        ('d4e22e20-f178-488b-ba1a-3117a48ee867','KObbex'),
        ('679fa663-babe-4683-9f0f-d429344557ad','NOW'),
        ('5b713c43-e5b0-44b1-9537-5b22ef95f9b5','MartianPay'),
        ('b0faac21-704c-4b37-8766-4061ff96331f','Accelerator'),
        ('3fb36ab6-82cc-476d-9161-4d97e53062e3','Billigans'),
        ('f33ade31-76e0-423c-9ad6-7f4c788e96e6','tether'),
        ('fd58f46e-6f73-483e-bc14-6fe2841b2bdf','Bitrace'),
        ('f1277684-b267-4322-8c5e-f5154604fe97','energylink'),
        ('d2c27313-71a5-49b2-8e49-acd3f2d15118','deppso'),
        ('cb0f674b-1141-4e56-9d25-9c24b51eca7a','AK'),
        ('242477f3-1739-4a57-b828-ff4bb2f03752','seek940'),
        ('02c1094d-acc1-47d6-8837-677a5ef23a47','Bitcoin'),
        ('a85a1bc3-3156-484d-8b52-654da6a97dc4','energyMarst'),
        ('96e309b7-be0f-414a-babf-c14cc6a72da9','Auther')
)
"""

def query_last_day_trx_cnt_rank(connection):
    sql = f"""
    {API_KEY_MAPPING}
    , stats_since_march_4 AS (
        SELECT 
            am.api_key,
            am.company,
            COUNT(go.id) AS transaction_count_since_march_4,
            SUM(go.amount) AS transaction_amount_since_march_4
        FROM 
            api_key_mapping am
        LEFT JOIN 
            gasfree_offchains go ON am.api_key = go.api_key
        WHERE 
            go.created_at BETWEEN NOW() - INTERVAL '1 day' AND NOW()
        GROUP BY 
            am.api_key, am.company
    )
    SELECT 
        api_key,
        company,
        transaction_count_since_march_4,
        transaction_amount_since_march_4
    FROM 
        stats_since_march_4 
    ORDER BY 
        transaction_amount_since_march_4 DESC
    LIMIT 3;
    """
    return execute_query(connection, sql)

def query_all_time_trx_cnt_rank(connection):
    sql = f"""
    {API_KEY_MAPPING}
    , stats_since_march_4 AS (
        SELECT 
            am.api_key,
            am.company,
            COUNT(go.id) AS transaction_count_since_march_4,
            SUM(go.amount) AS transaction_amount_since_march_4
        FROM 
            api_key_mapping am
        LEFT JOIN 
            gasfree_offchains go ON am.api_key = go.api_key
        WHERE 
            go.created_at BETWEEN '2025-03-04' AND NOW()
        GROUP BY 
            am.api_key, am.company
    )
    SELECT 
        api_key,
        company,
        transaction_count_since_march_4,
        transaction_amount_since_march_4
    FROM 
        stats_since_march_4 
    ORDER BY 
        transaction_amount_since_march_4 DESC
    LIMIT 3;
    """
    return execute_query(connection, sql)
