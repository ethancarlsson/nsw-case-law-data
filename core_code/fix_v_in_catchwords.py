from connect_to_db import DBConnector

class VFixer(DBConnector):
    '''
    Removes -v- instance in catchwords to avoid bad splitting
    '''
    sql = '''SELECT case_id, catchwords FROM case_law WHERE catchwords LIKE '%-v-%' '''
    def __init__(self):
        self.catchwords_to_fix = self.fetch_records(self.sql)
        self.update_sql = str()

    def fix_catchwords(self):
        '''
        fixes the problem catchwords
        '''
        for catchwords in self.catchwords_to_fix:
            
            new_catchwords = catchwords[1].replace('-v-', 'v')
            self.update_sql += f'''
            
            UPDATE case_law
            SET catchwords = '{new_catchwords}'
            WHERE case_id = {catchwords[0]};

            '''
        self.update_records(self.update_sql)

if __name__ == '__main__':
    VFixer().fix_catchwords()
