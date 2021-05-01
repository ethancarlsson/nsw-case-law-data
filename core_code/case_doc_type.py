from update_coversheet import OldCoversheetParser, NewCoversheetParser
from connect_to_db import DBConnector
from psycopg2 import ProgrammingError

def old_or_new_doc(case) -> str:
    coversheet = NewCoversheetParser(case)
    doc_type = 'new'
    if coversheet.html_coversheet is None:
        coversheet = OldCoversheetParser(case)
        doc_type = 'old'
        if coversheet.html_coversheet is None:
            doc_type = 'n/a'
    return doc_type

class DocumentTypeUpdater(DBConnector):
    def __init__(self):
        print('selecting cases...')
        sql = '''
        SELECT case_id, uncleaned_html FROM case_law WHERE doc_type IS NULL;
        '''
        self.update_query = str()
        self.cases = self.fetch_records(sql)

    
    def run_update(self):
        print('looping over cases...')
        for case in self.cases:
            doc_type = old_or_new_doc(case[1])
            self.update_query += f'''
                UPDATE case_law
                SET doc_type = '{doc_type}'

                WHERE case_id = '{case[0]}';
                '''
        print('update records...')
        if self.update_query:
            self.update_records(self.update_query)

if __name__ == "__main__":
    DocumentTypeUpdater().run_update()
