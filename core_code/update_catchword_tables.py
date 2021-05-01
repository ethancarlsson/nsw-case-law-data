'''
Module creates many to many between catchwords and cases
'''
import re
from io import StringIO
from connect_to_db import DBConnector

class Catchwords(DBConnector):
    '''
    A class for adding catchwords to the database in a new format.
    '''
    sql = '''
    SELECT catchwords FROM case_law;
    '''
    def __init__(self):
        print('fetching records...')
        self.cases = self.fetch_records(self.sql)
        self.catchword_table = str()
        self.set_of_all_catchwords = set()
        self.sql_query = str()
        
    @staticmethod
    def split_catchwords(catchwords):
        '''
        Makes a list from the catchword string by splitting on dashes.
        '''
        # adds space before or after to avoid words like "co-operate"
        # and capture typose where there is no space before and after
        # â€“ is an encoding error present on nswcaselaw
        return re.split(
            r'- |– |:- | -| –| :-|—| â€“|â€“ |: | :|---|--',
            catchwords)

    def parse_over_catchwords(self):
        '''
        Loops over every case splitting the keywords and adding them to the
        catchword set.
        '''
        print('parsing over all cases...')
        for case in self.cases:
            catchword_list = self.split_catchwords(case[0])
            if len(catchword_list[0]) > 1000:
                catchword_list = re.split(
                    r'- |– |:- | -| –| :-|—| â€“|â€“ |: | :|---|--|\. |; |: |, ',
                    case[0])
            self.set_of_all_catchwords.update({catchword.strip() for catchword in catchword_list})

    def create_catchword_table(self):
        '''
        Builds a table in a string to later be copied into postgres.
        '''
        print('creating table...')
        self.catchword_table += '\n'.join(self.set_of_all_catchwords)

    def copy_tables_to_pg(self):
        '''
        Transforms the table into an StringIO and copies it to the database
        '''
        self.parse_over_catchwords()
        self.create_catchword_table()
        if self.catchword_table:
            self.copy_str_tables_to_pg(
                self.catchword_table,
                'catchwords',
                'catchword'
            )


class CatchwordConnector(DBConnector):
    '''
    Connects the catchwords to the cases.
    '''
    sql_catchwords = '''
    SELECT catchword, catchword_id FROM catchwords;
    '''
    sql_cases = '''
    SELECT case_id, catchwords FROM case_law;
    '''
    def __init__(self):
        self.catchword_dict = dict(self.fetch_records(self.sql_catchwords))
        self.all_cases = self.fetch_records(self.sql_cases)

        self.m2m_table_set = set()
        self.m2m_table = str()

    def parse_over_catchwords(self):
        '''
        Loops over every case splitting the keywords, comparing them to the dict
        and building a table for the many to many relationship.
        '''
        print('parsing over all cases...')
        for case in self.all_cases:
            catchword_list = Catchwords.split_catchwords(case[1])
            if len(catchword_list[0]) > 1000:
                catchword_list = re.split(
                    r'- |– |:- | -| –| :-|—| â€“|â€“ |: | :|---|--|\. |; |: |, ',
                    case[1])

            self.update_m2m_table(case[0], catchword_list)
        
        

    def update_m2m_table(self, case_id, catchwords):
        '''
        Builds a table into a set to avoid duplicate keys.
        '''
        for catchword in catchwords:
            catchword_id = self.catchword_dict.get(catchword.strip())

            self.m2m_table_set.add(f'{case_id}\t{catchword_id}\n')

    def create_m2m_str(self):
        '''
        Translates set to string.
        '''
        print('translating table to string...')
        self.m2m_table = ''.join(self.m2m_table_set)

    def copy_tables_to_pg(self):
        '''
        Transforms the table into a StringIO and copies it to the database.
        '''
        self.parse_over_catchwords()
        self.create_m2m_str()
        if self.m2m_table:
            self.copy_str_tables_to_pg(
                self.m2m_table,
                'catchwords_case_law',
                'case_id',
                'catchword_id'
            )




if __name__ == "__main__":
    CatchwordConnector().copy_tables_to_pg()
