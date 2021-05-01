'''
Module with helper functions for making connections to the postgres databas
'''
from io import StringIO
import psycopg2
from nsw_scraper import CaseLawScraper
from secret_things import HOST, DB_NAME, USER, PASSWORD

def connect_to_db():
    conn = psycopg2.connect(
    host=HOST,
    dbname=DB_NAME,
    user=USER,
    password=PASSWORD,
    )
    return conn


def update_records(sql):
    '''
    For inserting or updating rows in a table.
    '''
    conn = connect_to_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
    conn.close()

def copy_str_tables_to_pg(str_table: str, pg_table: str, *table_columns: str):
    '''
    Transforms a string table table into a StringIO and copies it to the database.
    String table should be formatted as f'{cell}\t{cell}\n'
    '''
    print('copying reps to db...')
    conn = connect_to_db()
    with conn:
        with conn.cursor() as cur:
            cur.copy_from(
                StringIO(str_table),
                pg_table,
                columns=table_columns)
            conn.commit()
    conn.close()

def fetch_records(sql):
    '''
    Return results of a select query.
    '''
    conn = connect_to_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    conn.close()


class DBConnector:
    '''
    Has methods that makes connections to the DB a little cleaner
    '''
    def connect_to_db(self):
        return connect_to_db()
    
    def update_records(self, sql):
        conn = self.connect_to_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                conn.commit()
        conn.close()

    def copy_str_tables_to_pg(self, str_table, pg_table, *table_columns):
        '''
        Transforms a string table table into a StringIO and copies it to the database.
        String table should be formatted as f'{cell}\t{cell}\n'
        '''
        print('copying reps to db...')
        conn = self.connect_to_db()
        with conn:
            with conn.cursor() as cur:
                cur.copy_from(
                    StringIO(str_table),
                    pg_table,
                    columns=table_columns)
                conn.commit()
        conn.close()

    def fetch_records(self, sql):
        '''
        Return results of a select query.
        '''
        conn = self.connect_to_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                return cur.fetchall()
        conn.close()

    def newest_cases(self, date):
        select_latest_links = f'''
        SELECT case_link FROM case_law WHERE decision_date >= '{date}';
        '''
        return [link[0] for link in self.fetch_records(select_latest_links)]

    def get_latest_case_date(self):
        select_latest_links = '''
        SELECT MAX(decision_date) FROM case_law;            
        '''
        return self.fetch_records(select_latest_links)[0][0]

    def clean_apostrophes(self, string):
        '''
        Prevents names like O'Neil ruining the whole thing.
        '''
        return string.replace("'", "''")

def clean_apostrophes(string):
    '''
    Prevents names like O'Neil ruining the whole thing. 
    '''
    return string.replace("'", "''")

class DBConnectedScraper(CaseLawScraper, DBConnector):
    '''
    For scraping law and adding info to the database
    '''
