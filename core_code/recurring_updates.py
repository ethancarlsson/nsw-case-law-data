'''
This module creates recurring classes that will fill in missing information recurrently.
'''
from update_coversheet import CoversheetMaster
from update_catchword_tables import Catchwords, CatchwordConnector
from update_legislation import Legislation, LegislationConnections
from case_doc_type import DocumentTypeUpdater
from update_full_text import FullText

class CoversheetUpdater(CoversheetMaster):
    '''
    Adds missing coversheets.
    '''
    sql = '''
    SELECT uncleaned_html, case_id, case_link 
    FROM case_law
    WHERE case_dictionary IS NULL;
    '''

    def run(self):
        self.update_for_coversheet()

class CatchwordUpdater(Catchwords):
    '''
    Adds missing catchwords.
    '''
    sql = '''
    SELECT catchwords 
    FROM case_law 
    WHERE NOT EXISTS 
        (SELECT * 
        FROM catchwords_case_law 
        WHERE catchwords_case_law.case_id = case_law.case_id
        )
    AND catchwords != '[]' 
    AND catchwords != ':-';
    '''
    def write_conflict_sensitive_sql_query(self):
        for catchword in self.set_of_all_catchwords:
            if (catchword):
                self.sql_query += f'''

                INSERT INTO catchwords (catchword)
                VALUES ('{catchword}')
                ON CONFLICT DO NOTHING;

                '''
    def run(self):
        self.parse_over_catchwords()
        self.write_conflict_sensitive_sql_query()
        if self.sql_query:
            self.update_records(self.sql_query)

class CatchwordConnectionUpdater(CatchwordConnector):
    '''
    Adds missing connections between catchwords and case_law.
    '''
    sql_catchwords = '''
    SELECT catchword, catchword_id
    FROM catchwords
    WHERE NOT EXISTS 
        (SELECT * 
        FROM catchwords_case_law 
        WHERE catchwords_case_law.catchword_id = catchwords.catchword_id
        );
    '''
    sql_cases = '''
    SELECT case_id, catchwords 
    FROM case_law 
    WHERE NOT EXISTS 
        (SELECT * 
        FROM catchwords_case_law 
        WHERE catchwords_case_law.case_id = case_law.case_id
        )
    AND catchwords != '[]' 
    AND catchwords != ':-';
    '''
    def run(self):
        self.parse_over_catchwords()

class LegislationUpdater(Legislation):
    '''
    Adds missing legislaiton.
    '''

    sql = '''
    SELECT case_dictionary, case_id 
    FROM case_law 
    WHERE NOT EXISTS 
        (SELECT * 
        FROM legislation_citations_case_law 
        WHERE legislation_citations_case_law.case_id = case_law.case_id
        )
    '''
    def run(self):
        self.copy_legislation_table()

class LegislationConnectionUpdater(LegislationConnections):
    '''
    Adds missing connections between legislation and case law.
    '''
    case_sql = '''
        SELECT case_dictionary, case_id 
        FROM case_law 
        WHERE NOT EXISTS 
            (SELECT * 
            FROM legislation_citations_case_law 
            WHERE legislation_citations_case_law.case_id = case_law.case_id
            )
    '''

    citation_sql = '''
        SELECT legislation_citation, legislation_citation_id 
        FROM legislation_citations
        WHERE NOT EXISTS
            (SELECT * 
            FROM legislation_citations_case_law 
            WHERE legislation_citations_case_law.legislation_citation_id = legislation_citations.legislation_citation_id
            );
    '''
    def run(self):
        self.add_connection_table()

if __name__ == "__main__":
    print('|||DocumentTypeUpdater||||')
    DocumentTypeUpdater().run_update()
    print('||||CoversheetUpdater|||||')
    CoversheetUpdater().run()
    print('||||CatchwordUpdater||||')
    CatchwordUpdater().run()
    print('||||CatchwordConnectionUpdater|||||')
    CatchwordConnectionUpdater().run()
    print('||||LegislationUpdater||||')
    LegislationUpdater().run()
    print('||||LegislationConnectionUpdater||||')
    LegislationConnectionUpdater().run()
    print('||||FullText||||')
    FullText().run_update()

