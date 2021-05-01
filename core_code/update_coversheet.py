'''
All the tools used to extract information from the coversheet
'''
import json
import re
from psycopg2 import ProgrammingError


from bs4 import BeautifulSoup as bs
from connect_to_db import DBConnector
from connect_to_db import clean_apostrophes

def remove_html_tags(text):
    """Remove html tags from a string"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


class CourtAdder(DBConnector):
    '''
    Initiates with all the citations and then uses the citations to find court ids.
    '''
    def __init__(self):
        sql = '''
        SELECT citation, case_id FROM case_law WHERE decision_date >= '2021-01-15';
        '''
        self.citations = self.fetch_records(sql)
        self.court_pattern = re.compile(r'] NSW[A-Za-z]+')

    def get_court_match(self, citation):
        court_match = self.court_pattern.search(citation)
        if court_match:
            court_match = court_match.group().replace('] ', '')
            return court_match
        
    def write_query(self):
        update_sql = '''
        
        '''
        print('writing query...')
        for citation in self.citations:
            court = self.get_court_match(citation[0])
            if court:
                update_sql += f'''
                UPDATE case_law
                SET court = '{court}'
                WHERE case_id = {citation[1]};
                '''
        print('updating records...')
        self.update_records(update_sql)

class AppAndResp():
    '''
    Finds applicant and respondent parties within a string.
    '''
    def __init__(self, parties) -> str:
        self.parties = parties
        self.applicant = str()
        self.respondent = str()

        self.find_first_party()
        self.find_second_party()


    def find_first_party(self):
        '''
        Finds the applicant within a the parties section of the coversheet.
        '''
        applicant_pattern = re.compile(r'(\w|\s)+\(applicant\)')
        prosecutor_pattern = re.compile(r'(\w|\s)+\(prosecutor\)')

        respondent_pattern = re.compile(r'(\w|\s)+\(respondent\)')
        defendant_pattern = re.compile(r'(\w|\s)+\(defendant\)')

        applicant = applicant_pattern.search(self.parties)
        respondent = respondent_pattern.search(self.parties)

        prosecutor = prosecutor_pattern.search(self.parties)
        defendant = defendant_pattern.search(self.parties)
        # this quadruple check is very inneficient, but it the courts aren't always consistent with the position of the two
        # efficiency could be gained by checking for respondent only if applicant is None; applicant is 1st 90% of the time.
        # This makes the code very ugly though and the text is short enough that it feels nicer to keep this inneficient algo in the interest of code looks
        if applicant:
            self.applicant = applicant.group().strip()
        elif prosecutor:
            self.applicant = prosecutor.group().strip()
        elif defendant:
            self.respondent = defendant.group().strip()
        elif respondent:
            self.respondent = respondent.group().strip()

    def find_second_party(self) -> str:
        '''
        Finds the respondent within a the parties section of the coversheet.
        '''
        applicant_pattern = re.compile(r'\n(\w|\s)+\(applicant\)')
        respondent_pattern = re.compile(r'\n(\w|\s)+\(respondent\)')

        prosecutor_pattern = re.compile(r'\n(\w|\s)+\(prosecutor\)')
        defendant_pattern = re.compile(r'\n(\w|\s)+\(defendant\)')

        applicant = applicant_pattern.search(self.parties)
        respondent = respondent_pattern.search(self.parties)

        prosecutor = prosecutor_pattern.search(self.parties)
        defendant = defendant_pattern.search(self.parties)

        if applicant:
            self.applicant = applicant.group().strip()
        if prosecutor:
            self.applicant = prosecutor.group().strip()
        if defendant:
            self.respondent = defendant.group().strip()     
        elif respondent:
            self.respondent = respondent.group().strip()


class RepresentationOld():
    '''
    Finds representation in the old coversheets
    '''
    def __init__(self, representation):
        self.representation = representation
        self.reps_dict = dict()
        self.find_for_app()
        self.find_for_res()

    def get_app_text(self):
        rep_pattern = re.compile(r'for applicant:(.|\s)*(for respondent:)') #everything in between 'for applicant' and 'for respondent'
        reps = rep_pattern.search(self.representation)
        if reps is not None:
            return reps.group().replace('for applicant:', '').replace('for respondent:', '').strip()
        return None
        
    def get_res_text(self):
        rep_pattern = re.compile(r'for respondent:(.|\s)*') #everything in between 'for respondent' and 'for applicant'
        reps = rep_pattern.search(self.representation)
        if reps is not None:
            return reps.group().replace('for applicant:', '').replace('for respondent:', '').strip()
        return None

    
    def find_counsel(self, app_rep):
        counsel_pattern = re.compile(r'(.|\s)*(instructed by)?')
        counsel = counsel_pattern.search(app_rep)
        if counsel is not None:
            return counsel.group().replace('instructed by', '').replace('appeared for the applicant', '').replace('appeared for the respondent', '').strip()
        return None
            
    def find_solicitor(self, app_rep):
        solicitor_pattern = re.compile(r'(instructed by)(.|\s)*')
        solicitor = solicitor_pattern.search(app_rep)
        if solicitor is not None:
            return solicitor.group().replace('instructed by', '').replace('appeared for the applicant', '').replace('appeared for the respondent', '').strip()
        return None


    def find_for_app(self):
        app_rep = self.get_app_text()
        if app_rep:
            self.reps_dict['applicant_solicitors'] = [self.find_solicitor(app_rep)]
            self.reps_dict['applicant_counsel'] = [self.find_counsel(app_rep)]


    def find_for_res(self):
        app_rep = self.get_res_text()
        if app_rep:
            self.reps_dict['respondent_solicitors'] = [self.find_solicitor(app_rep)]
            self.reps_dict['respondent_counsel'] = [self.find_counsel(app_rep)]


class NewCoversheetParser():
    def __init__(self, html_doc):
        self.soup = bs(html_doc, 'lxml')
        self.html_coversheet = self.get_new_coversheet() # is set within a list so that it works the same as the old coversheet
        self.full_coversheet = dict()
        self.type = 'new'

    def get_new_coversheet(self):
        return self.soup.find('div', {'class': 'coversheet'})
    
    def build_coversheet(self):
        left_col = self.html_coversheet.find_all('dt')
        right_col = self.html_coversheet.find_all('dd')
        left_col = [
            clean_apostrophes(i.text.lower().replace(':', '').strip()) for i in left_col
        ]
        right_col = [
            clean_apostrophes(i.text.lower().strip()) for i in right_col
        ]
        self.full_coversheet.update(dict(zip(left_col, right_col)))



class OldCoversheetParser():
    def __init__(self, html_doc):
        self.soup = bs(html_doc, 'lxml')
        self.html_coversheet = self.get_old_coversheet()
        self.full_coversheet = dict()
        self.type = 'old'
        
    
    def get_old_coversheet(self):
        return self.soup.find_all('table', {
                'width': "100%",
                'border':"0",
                'cellspacing':"0",
                'cellpadding': "0"
                })

    def build_coversheet(self):
        for table in self.html_coversheet:
            for row in table.find_all('tr'):
                row = row.find_all('td')
                row = [remove_html_tags(str(ele).replace('<br/>', '\n')) for ele in row][1:3]
                if len(row) > 1:
                    self.full_coversheet[clean_apostrophes(row[0].lower().replace(':', '').strip())] = clean_apostrophes(row[1].lower().strip())

class Updater():
    def __init__(self):
        self.query = str()
        self.values_to_update = dict()


class CoversheetMaster(DBConnector):
    sql = '''
    SELECT uncleaned_html, case_id, case_link, case_dictionary
    FROM case_law WHERE court = 'NSWLEC' 
    AND doc_type = 'old';
    '''

    def __init__(self):
        print(self.sql)
        print('Fetching records...')
        self.cases = self.fetch_records(self.sql)
        self.coversheet = None
        self.counter = 0
        self.query = str()
        self.updater = Updater()


    def update_for_coversheet(self):
        print('Building query...')
        for case in self.cases:
            coversheet = self.grab_coversheet(case[0])
            coversheet_dict = coversheet.full_coversheet
            coversheet_type = coversheet.type
            json_coversheet = json.dumps(coversheet_dict, indent=4)
            self.query += f'''
                UPDATE case_law
                SET 
                    case_dictionary = '{json_coversheet}',
                    doc_type = '{coversheet_type}'
                WHERE case_id = '{case[1]}';
            '''
        print('Updating records...')
        try:
            if self.query:
                self.update_records(self.query)
        except ProgrammingError:
            print('''
            Programming error. Cannot execute an empty query.
            There were no null cases.
            ''')

    def grab_coversheet(self, case):
        coversheet_parser = NewCoversheetParser(case)
        if coversheet_parser.html_coversheet is None:
            coversheet_parser = OldCoversheetParser(case)
        coversheet_parser.build_coversheet()
        return coversheet_parser

class CoversheetWithHtml(CoversheetMaster):
    sql = '''
    SELECT uncleaned_html, case_id, case_link 
    FROM case_law
    WHERE case_dictionary IS NULL;
    '''

class PartiesUpdater(CoversheetMaster):

    def parse_cases_for_parties(self):
        for case in self.cases:
            self.pull_party_info(case)
            parties = self.updater.values_to_update.get('parties')
            applicant = self.updater.values_to_update.get('applicant')
            respondent = self.updater.values_to_update.get('respondent')
            self.updater.query += f'''
                UPDATE case_law
                SET parties = '{self.clean_apostrophes(parties)}',
                applicant = '{self.clean_apostrophes(applicant)}',
                respondent = '{self.clean_apostrophes(respondent)}'

                WHERE case_id = '{case[1]}';
            '''
        self.update_records(self.updater.query)

    def pull_party_info(self, case):
        coversheet_dict = self.grab_coversheet(case[0]).full_coversheet

        if 'parties' in coversheet_dict:
            raw_parties = str(coversheet_dict.get('parties'))
            
            parties = AppAndResp(raw_parties)
            self.updater.values_to_update['parties'] = parties.parties
            self.updater.values_to_update['applicant'] = parties.applicant
            self.updater.values_to_update['respondent'] = parties.respondent

if __name__ == "__main__":
    CoversheetWithHtml().update_for_coversheet()
