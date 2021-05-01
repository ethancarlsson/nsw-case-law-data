'''
Updates legislation using coversheet dictionary.
'''
from io import StringIO
import re

from update_coversheet import Updater
from connect_to_db import DBConnector


def pull_legislation(case):
    legislation_cited = case.get('legislation cited')
    
    legislation_list = list()
    if legislation_cited:
        legislation_list = legislation_cited.replace('\t', '').split('\n')
        legislation_list = [leg.replace(';', '').strip() for leg in legislation_list if leg != '']
        if len(legislation_list) == 1:
            splitting_pattern = re.compile(r'(.+ \d{4}(,? ?s? ?\d{0,4}(\(\w+\))?)+)')
            legislation_list = splitting_pattern.split(legislation_list[0])
            fixed_legi_list = [
                leg.replace(';', '').strip() for leg in legislation_list
                if leg != ''
                if leg is not None
                if len(leg) > 5
                ]
            return fixed_legi_list

    return legislation_list


# strategy: 1. add all legislation cited. 2. go through cases cited again grab id of each legislation and case to add to the manytomany relationship

# I am building a many to many relationship between cases and legislation. 
# However I want to preserve specific pinpoints in the legislation citation page for later use in more complicated queries.

def there_are_hyphenated_words(word) -> bool:
    legislation_match = re.compile(r'[a-z]+(-|–)[a-z]+').match(word)
    return bool(legislation_match)

def remove_kuringgai_hyphens(word) -> str:
    return word.replace('ku–ring-gai', 'kuringgai').replace('ku-ring-gai', 'kuringgai').replace('ku–ring–gai', 'kuringgai')

def split_on_hyphen(word) -> list:
    return re.split(r'-|–', word)

# class LegislationUpdater(DBConnector):
#     def __init__(self):
#         sql = '''
#             SELECT case_dictionary, case_id FROM case_law; 
#         '''

#         print('fetching...')
#         self.cases = self.fetch_records(sql)
#         self.counter = 0
#         self.updater = Updater()
#         print(self.cases)

#     def loop_over_dictionaries(self):
#         for case in self.cases:
#             print(case[1])

#             legislation = pull_legislation(case[0])
#             for leg in legislation:
                
#                 self.updater.query += f'''
#                 INSERT INTO legislation_citations (legislation_citation)
#                 VALUES ('{self.clean_apostrophes(leg)}')
#                 ON CONFLICT (legislation_citation)
#                 DO NOTHING;
#                 '''
#             # print(legislation)
#         self.update_records(self.updater.query)

#     def pull_legislation(self, case):
#         legislation_cited = case.get('legislation cited')
        
#         legislation_list = list()
#         if legislation_cited:
#             legislation_list = legislation_cited.replace('\t', '').split('\n')
#             legislation_list = [leg.replace(';', '').strip() for leg in legislation_list if leg != '']
#             if len(legislation_list) == 1:
#                 splitting_pattern = re.compile(r'(.+ \d{4}(,? ?s? ?\d{0,4}(\(\w+\))?)+)')
#                 legislation_list = splitting_pattern.split(legislation_list[0])
#                 fixed_legi_list = [
#                     leg.replace(';', '').strip() for leg in legislation_list
#                     if leg != ''
#                     if leg is not None
#                     if len(leg) > 5
#                     ]
#                 return fixed_legi_list

#         return legislation_list

class LegislationReferences(DBConnector):

    def __init__(self):
        sql = '''
            SELECT legislation_citations FROM legislation_citations; 
        '''
        self.legislation_citations = self.fetch_records(sql)
        self.counter = 0
        self.updater = Updater()
        self.table = StringIO()

    def split_grouped_citations(self):
        for citation in self.legislation_citations:
            try:
                cited_legislation = eval(citation[0])
                legislation = cited_legislation[1]
                if isinstance(legislation, str):
                    if '–' in legislation:
                        if there_are_hyphenated_words(legislation):
                            legislation = remove_kuringgai_hyphens(legislation)
                        legislation_list = split_on_hyphen(legislation)
                        for legislation in legislation_list:
                            self.updater.query += f'''
                            INSERT INTO legislation_citations (legislation_citation)
                            VALUES ('{self.clean_apostrophes(legislation).strip()}')
                            ON CONFLICT (legislation_citation)
                            DO NOTHING;
                            '''
                        self.updater.query += f'''
                        DELETE FROM legislation_citations
                        WHERE legislation_citation_id = {cited_legislation[0]};
                        '''
                        self.update_records(self.updater.query)
                
            except NameError:
                continue
                # print('NameError. String was probably read as a variable')
            except SyntaxError:
                continue
                # print('SyntaxError. String was probably full-stop, byte or comma.')



    def loop_over_citations(self):
        for citation in self.legislation_citations:
            try:
                legislation = eval(citation[0])[1]
                if isinstance(legislation, str):
                    acts = InstrumentChooser(legislation).instrument_list
                    for act in acts:
                        self.updater.query += f'''
                        INSERT INTO legislation (legislation_cited)
                        VALUES ('{self.clean_apostrophes(act).strip().lstrip(')')}')
                        ON CONFLICT (legislation_cited)
                        DO NOTHING;
                        '''
            except NameError:
                print('NameError. String was probably read as a variable')
            except SyntaxError:
                print('SyntaxError. String was probably full-stop, comma or other piece of grammar.')

        self.update_records(self.updater.query)

class InstrumentChooser():
    '''
    Figures out which kind of instrument the program is looking at.
    '''

    def __init__(self, citation):
        self.instrument_list = list()
        self.legislation_citation = citation
        self.get_acts()
        # self.get_plans()
        self.get_policies()
        self.get_regulations()
        self.get_schemes()
        self.get_rules()

    def get_acts(self) -> list:
        legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ act \d{4}')
        legislation_list = legislation_pattern.findall(self.legislation_citation)
        if len(legislation_list) == 0:
            legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ act')
            legislation_list = legislation_pattern.findall(self.legislation_citation)
        self.instrument_list += legislation_list

    def get_plans(self) -> list:
        legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ plan no\.? \d{1,3}?')
        legislation_list = legislation_pattern.findall(self.legislation_citation)
        if len(legislation_list) == 0:
            legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ plan')
            legislation_list = legislation_pattern.findall(self.legislation_citation)
        self.instrument_list += legislation_list

    def get_policies(self) -> list:
        legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ policy no\.? \d{1,3}?')
        legislation_list = legislation_pattern.findall(self.legislation_citation)
        if len(legislation_list) == 0:
            legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ policy \w+ \d{4}')
            legislation_list = legislation_pattern.findall(self.legislation_citation)
        self.instrument_list += legislation_list


    def get_schemes(self) -> list:
        legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ scheme ordinance \d{4}')
        legislation_list = legislation_pattern.findall(self.legislation_citation)
        if len(legislation_list) == 0:
            legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ scheme ordinance')
            legislation_list = legislation_pattern.findall(self.legislation_citation)
        self.instrument_list += legislation_list

    def get_regulations(self) -> list:
        legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ regulation \d{4}')
        legislation_list = legislation_pattern.findall(self.legislation_citation)
        if len(legislation_list) == 0:
            legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ regulation')
            legislation_list = legislation_pattern.findall(self.legislation_citation)
        self.instrument_list += legislation_list
        
    def get_rules(self) -> list:
        legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ rules \d{4}')
        legislation_list = legislation_pattern.findall(self.legislation_citation)
        if len(legislation_list) == 0:
            legislation_pattern = re.compile(r'[a-z|\(|\|\s|&)]+ rules')
            legislation_list = legislation_pattern.findall(self.legislation_citation)
        self.instrument_list += legislation_list

class CaseToLegislationConnector(DBConnector):

    def __init__(self):
        case_sql = '''
            SELECT case_dictionary, case_id FROM case_law WHERE court = 'NSWLEC'; 
        '''
        legislation_sql = '''
            SELECT legislation_citation, legislation_citaiton_id FROM legislation; 
        '''
        print('Executing select statement...')
        self.cases = self.fetch_records(case_sql)
        self.legislation = dict(self.fetch_records(legislation_sql))
        self.updater = Updater()

    def match_case_to_legislation(self):
        print('connecting cases to legislation...')
        for case in self.cases:
            if case[0]:
                legislation_list = pull_legislation(case[0])
                for legislation in legislation_list:
                    for instrument in InstrumentChooser(legislation).instrument_list:
                        if instrument in self.legislation:
                            # print(self.legislation.get(instrument))
                            self.updater.query += f'''
                            INSERT INTO case_law_legislation (legislation_id, case_id)
                            VALUES ({self.legislation.get(instrument)}, {case[1]})
                            ON CONFLICT DO NOTHING;
                            '''            
        print('executing insert statement...')
        self.update_records(self.updater.query)

class Legislation(DBConnector):
    sql = '''
        SELECT case_dictionary, case_id FROM case_law; 
    '''

    def __init__(self):
        print('fetching...')
        self.cases = self.fetch_records(self.sql)
        self.legislation_hashtable = set()
        self.legislation_table = str()

    def build_legislation_table_set(self):
        '''
        Builds the original set. Avoiding duplicates.
        '''
        for case in self.cases:
            legislation = pull_legislation(case[0])
            self.legislation_hashtable.update(set(legislation))

    def build_legislation_table_str(self):
        '''
        Translates set to string.
        '''
        counter = self.fetch_records('SELECT MAX(catchword_id) FROM catchwords;')[0][0]
        for legislation in self.legislation_hashtable:
            counter +=1
            citation = legislation.replace("\\", "")
            self.legislation_table += f'{counter}\t{citation}\n'

    def copy_legislation_table(self):
        '''
        Handles the whole process of building the table and copying it to the db.
        '''
        self.build_legislation_table_set()
        self.build_legislation_table_str()
        if self.legislation_table:
            self.copy_str_tables_to_pg(
                self.legislation_table,
                'legislation_citations',
                'legislation_citation_id',
                'legislation_citation'
            )

class LegislationConnections(DBConnector):
    case_sql = '''
        SELECT case_dictionary, case_id FROM case_law; 
    '''

    citation_sql = '''
        SELECT legislation_citation, legislation_citation_id FROM legislation_citations;
    '''

    def __init__(self):
        print('fetching...')
        self.cases = self.fetch_records(self.case_sql)
        self.citations_dict = dict(self.fetch_records(self.citation_sql))
        self.legislation_hashtable = set()
        self.legislation_table = str()

    def add_connection_table(self):
        '''
        Build the connection table and add it to the postgres server
        '''
        print('building table...')
        for case in self.cases:
            legislation = pull_legislation(case[0])
            self.find_connection(legislation, case[1])

        print('translating table to string...')
        self.legislation_table = ''.join(self.legislation_hashtable)

        self.copy_str_tables_to_pg(
            self.legislation_table,
            'legislation_citations_case_law',
            'case_id',
            'legislation_citation_id'
            )

    def find_connection(self, legi_list, case_id):
        '''
        Adds a connection to the hashtable.
        '''
        for legislation in legi_list:
            citation = legislation.replace("\\", "")
            citation_id = self.citations_dict.get(citation)
            self.legislation_hashtable.add(f'{case_id}\t{citation_id}\n')


if __name__ == "__main__":
    LegislationConnections().add_connection_table()
