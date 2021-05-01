import re
from connect_to_db import DBConnector
from io import StringIO

def re_find(str_list, regex) -> int:
    for i in enumerate(str_list):
        if re.search(regex, i[1]):
            return i[0]
def between_strings(str_list) -> list:
    index1 = re_find(str_list, r'counsel')
    index2 = re_find(str_list, r'solicitor')
    if (index1 is not None) and (index2 is not None):
        if index2-1 == index1:
            return str_list[index2]
        
        return str_list[index1+1:index2]

    if index2 == 0:
        str_list.pop(0)
        return str_list


def after_sting(str_list) -> list:
    for i in enumerate(str_list):
        if re.search(r'solicitors|solicitor', i[1]):
            return str_list[i[0]+1:]

def get_representation(case) -> str:
    if bool(case[0]):
        representation = case[0].get('representation')
        if representation is None:
            representation = case[0].get('legal representatives')
            if representation is None:
                pass
        return representation

def make_rep_list(representation) -> list:
    if representation:
        splitting_pattern = re.compile(r'\s{2,}|\n|:')
        rep_list = splitting_pattern.split(representation)

        # if len(rep_list) == 1:
        #     splitting_pattern = re.compile(r'(respondents|respondent|applicants|applicant|solicitors|solicitor)')
        #     rep_list = splitting_pattern.split(representation)

        return rep_list
    else:
        return ['counsel:', 'litigant in person (respondent)', 'litigant in person (applicant)']



def find_client_coordinates(rep) -> str:
    client_pattern = re.compile(r'\(.+\)')
    match = client_pattern.search(rep)
    if match:
        return match.span()

class ReusableVariables:
    '''
    Saves needing to build a new string object everytime I need them.
    '''
    # Only saves a small amount of space in memory but the code looks a little nicer.
    applicant_str = 'applicant'
    respondent_str = 'respondent'
    prosecutor_str = 'prosecutor'
    defendant_str = 'defendant'

class RepresentationUpdater(DBConnector, ReusableVariables):
    def __init__(self):
        case_sql = '''
            SELECT case_dictionary, case_id, case_link FROM case_law
            WHERE citation NOT LIKE '%Decision number not in use%'
            AND citation NOT LIKE '%Decision restricted%'
            AND doc_type = 'new';
        '''
        solicitor_sql = '''
            SELECT solicitor, solicitor_id FROM solicitors;
        '''
        counsel_sql = '''
            SELECT counsel, counsel_id FROM counsel;
        '''
        self.cases = self.fetch_records(case_sql)
        self.solicitors = dict(self.fetch_records(solicitor_sql))
        self.counsel = dict(self.fetch_records(counsel_sql))

        self.counsel_update_hashtable = set()
        self.solicitor_update_hashtable = set()
        self.counsel_update_table = str()
        self.solicitor_update_table = str()

    def copy_reps_to_db(self):
        print('copying reps to db...')
        conn = self.connect_to_db()
        with conn:
            with conn.cursor() as cur:
                cur.copy_from(StringIO(self.counsel_update_table), 'counsel', columns=('counsel',))
                cur.copy_from(StringIO(self.solicitor_update_table), 'solicitors', columns=('solicitor',))
                conn.commit()
        conn.close()


    def copy_rep_conns(self):
        print('copying connections to db...')
        conn = self.connect_to_db()
        with conn:
            with conn.cursor() as cur:
                cur.copy_from(StringIO(self.counsel_update_table), 'counsel_case_law', columns=('counsel_id', 'case_id', 'client'))
                cur.copy_from(StringIO(self.solicitor_update_table), 'solicitors_case_law', columns=('solicitor_id', 'case_id', 'client'))
                conn.commit()
        conn.close()

    def parse_cases_for_reps(self):
        print('Creating tables...')
        for case in self.cases:
            
            representation = get_representation(case)
            if representation:
                rep_list = make_rep_list(representation)
                counsel_list = between_strings(rep_list)
                solicitor_list = after_sting(rep_list)
                if solicitor_list:
                    self.add_solicitors(solicitor_list)
                if counsel_list:
                    self.add_counsel(counsel_list)
                else:
                    self.add_counsel(rep_list)
            
        print('translating hashtables to strings')
        for soli in self.solicitor_update_hashtable:
            self.solicitor_update_table += soli
        for couns in self.counsel_update_hashtable:
            self.counsel_update_table += couns

        self.copy_reps_to_db()

    def respondent_or_applicant(self, client) -> str:
        if self.respondent_str in client:
            return self.respondent_str
        if self.applicant_str in client:
            return self.applicant_str
        if self.prosecutor_str in client:
            return self.prosecutor_str
        if self.defendant_str in client:
            return self.defendant_str
        
        return client

    def parse_for_connecting_reps(self):
        print('Creating tables...')
        for case in self.cases:
            representation = get_representation(case)
            if representation:
                rep_list = make_rep_list(representation)
                counsel_list = between_strings(rep_list)
                solicitor_list = after_sting(rep_list)
                if solicitor_list:
                    self.connect_solicitors(solicitor_list, case[1])
                if counsel_list:
                    self.connect_counsel(counsel_list, case[1])
                else:
                    self.connect_counsel(rep_list, case[1])

        print('translating hashtables to strings')
        for soli in self.solicitor_update_hashtable:
            self.solicitor_update_table += soli
        for couns in self.counsel_update_hashtable:
            self.counsel_update_table += couns

        self.copy_rep_conns()


    def connect_solicitors(self, solicitor_list, case_id):
        for rep in solicitor_list:
            client_coordinates = find_client_coordinates(rep)
            if client_coordinates:
                solicitor = rep[
                    0:client_coordinates[0]
                    ].replace('mr', '').replace('mrs', '').replace('ms', '').replace('respondents:', '').replace('respondent:', '').strip()
                client = rep[client_coordinates[0]:client_coordinates[1]].replace('(', '').replace(')', '').strip()
                client = self.respondent_or_applicant(client).strip()

                duplicate_dodger = set()
                for soli in solicitor.split(','):
                    if soli not in duplicate_dodger:
                        soli_id = self.solicitors.get(soli.strip())
                        self.solicitor_update_hashtable.add(f'{soli_id}\t{case_id}\t{client}\n')            
                    duplicate_dodger.add(soli)

    def connect_counsel(self, counsel_list, case_id):
        for rep in counsel_list:
            client_coordinates = find_client_coordinates(rep)
            if client_coordinates:
                counsel = rep[
                    0:client_coordinates[0]
                    ].replace('mr', '').replace('mrs', '').replace('ms', '').replace('respondent:', '').replace('respondents:', '').strip()
                client = rep[client_coordinates[0]:client_coordinates[1]].replace('(', '').replace(')', '').strip()
                client = self.respondent_or_applicant(client)
                
                duplicate_dodger = set()
                for couns in counsel.split(','):
                    if couns not in duplicate_dodger:
                        counsel_id = self.counsel.get(couns.strip())
                        self.counsel_update_hashtable.add(f'{counsel_id}\t{case_id}\t{client}\n')

                    duplicate_dodger.add(couns)


    def add_solicitors(self, solicitor_list):
        for rep in solicitor_list:
            client_coordinates = find_client_coordinates(rep)
            if client_coordinates:
                solicitor = rep[
                    0:client_coordinates[0]
                    ].replace('mr', '').replace('mrs', '').replace('ms', '').replace('respondents:', '').replace('respondent:', '').strip()
                
                for soli in solicitor.split(','):
                    self.solicitor_update_hashtable.add(f'{soli.strip()}\n')

    def add_counsel(self, counsel_list):
        for rep in counsel_list:
            client_coordinates = find_client_coordinates(rep)
            if client_coordinates:
                counsel = rep[
                    0:client_coordinates[0]
                    ].replace('mr', '').replace('mrs', '').replace('ms', '').replace('respondent:', '').replace('respondents:', '').strip()
                for couns in counsel.split(','):
                    self.counsel_update_hashtable.add(f'{couns.strip()}\n')



class RepresentationUpdaterOld(RepresentationUpdater):

    def __init__(self):
        print('Pulling cases from PostgreSQL table...')
        case_sql = '''
            SELECT case_dictionary, case_id, case_link FROM case_law
            WHERE citation NOT LIKE '%Decision number not in use%'
            AND citation NOT LIKE '%Decision restricted%'
            AND doc_type = 'old';
        '''
        self.cases = self.fetch_records(case_sql)
        self.rep_update_sql = str()


        self.counsel_update_hashtable = set()
        self.solicitor_update_hashtable = set()
        self.counsel_update_table = str()
        self.solicitor_update_table = str()

    @staticmethod
    def between_app_resp(rep_list, start_word, mid_word) -> dict:
        mid_pos = re_find(rep_list, mid_word)
        if mid_pos:
            rep_dict = {
                start_word: rep_list[0:mid_pos],
                mid_word: rep_list[mid_pos::]
                }
            return rep_dict


    def instructucted_by_format(self, rep_list) -> int:
        '''
        This splits the list in the following way [applicant, ..., solicitors?, ..., respondent, ..., solicitors, ...]
        '''
        first_word = rep_list[0]
        if 'applicant' in first_word:
            rep_dict = self.between_app_resp(rep_list, 'applicant', 'respondent')
            return rep_dict
        if 'prosecutor' in first_word:
            rep_dict = self.between_app_resp(rep_list, 'prosecutor', 'defendant')
            return rep_dict
        if 'appellant' in first_word:
            rep_dict = self.between_app_resp(rep_list, 'appellant', 'respondent')
            return rep_dict

    @staticmethod
    def split_counsel_from_solicitors(rep_list):
        sol_index = re_find(rep_list, r'solicitor')
        if sol_index:
            return rep_list[0: sol_index], rep_list[sol_index::]
        
        return rep_list, None

    @staticmethod
    def instructed_by(representation):
        index = re_find(representation, r'instructed by')
        counsel = representation[0:index]
        solicitors = representation[index::]
        if index:
            middle = re.split(r'(instructed by)', representation[index])
            index_middle = re_find(middle, r'instructed by')
            counsel += middle[0: index_middle]
            solicitors += middle[index_middle::]
            return counsel, solicitors
        else:
            return representation, None

    def add_rep(self, rep_dict):
        for rep in rep_dict:
            counsel_list, solicitor_list = self.split_counsel_from_solicitors(rep_dict.get(rep))
            if counsel_list:
                for couns in counsel_list:
                    self.counsel_update_hashtable.add(f'{couns.strip()}\n')
            if solicitor_list:
                for soli in solicitor_list:
                    self.solicitor_update_hashtable.add(f'{soli.strip()}\n')


    def parse_cases_for_reps(self):
        print('Creating tables...')
        for case in self.cases:

            representation = make_rep_list(get_representation(case))
            rep_dict = self.instructucted_by_format(representation)
            if rep_dict:
                self.add_rep(rep_dict)
            else:
                counsel_list, solicitor_list = self.instructed_by(representation)
                if counsel_list:
                    for couns in counsel_list:
                        self.counsel_update_hashtable.add(f'{couns.strip()}\n')
                
                if solicitor_list:
                    for soli in solicitor_list:
                        self.solicitor_update_hashtable.add(f'{soli.strip()}\n')

        print('Translating hashtables to strings...')

        for soli in self.solicitor_update_hashtable:
            self.solicitor_update_table += soli
        for couns in self.counsel_update_hashtable:
            self.counsel_update_table += couns

        print('Copying to PostgreSQL table...')
        self.copy_reps_to_db()

class CaseRepConnecter(RepresentationUpdaterOld):
    def __init__(self):
        print('Pulling cases from PostgreSQL table...')
        case_sql = '''
            SELECT case_dictionary, case_id, case_link FROM case_law
            WHERE citation NOT LIKE '%Decision number not in use%'
            AND citation NOT LIKE '%Decision restricted%'
            AND doc_type = 'old';
        '''
        solicitor_sql = '''
            SELECT solicitor, solicitor_id FROM solicitors;
        '''
        counsel_sql = '''
            SELECT counsel, counsel_id FROM counsel;
        '''
        self.cases = self.fetch_records(case_sql)
        self.solicitors = dict(self.fetch_records(solicitor_sql))
        self.counsel = dict(self.fetch_records(counsel_sql))

        self.counsel_update_hashtable = set()
        self.solicitor_update_hashtable = set()
        self.counsel_update_table = str()
        self.solicitor_update_table = str()

    def connect_rep(self, rep_dict, case_id):
        for rep in rep_dict:
            counsel_list, solicitor_list = self.split_counsel_from_solicitors(rep_dict.get(rep))
            if counsel_list:
                for couns in counsel_list:
                    couns_id = self.counsel.get(couns.strip())
                    if couns_id:
                        if 'appl' in couns:
                            client = 'applicant'
                        elif 'resp' in couns:
                            client = 'respondent'
                        else:
                            client = None
                        self.counsel_update_hashtable.add(f'{couns_id}\t{case_id}\t{client}\n')

            if solicitor_list:
                for soli in solicitor_list:
                    soli_id = self.solicitors.get(soli.strip())
                    if soli_id:
                        if 'appl' in soli:
                            client = 'applicant'
                        elif 'resp' in soli:
                            client = 'respondent'
                        else:
                            client = None
                        self.solicitor_update_hashtable.add(f'{soli_id}\t{case_id}\t{client}\n')

    def parse_for_connecting_reps(self):
        print('Connecting tables...')
        for case in self.cases:
            case_id = case[1]
            representation = make_rep_list(get_representation(case))
            rep_dict = self.instructucted_by_format(representation)
            if rep_dict:
                self.connect_rep(rep_dict, case[1])
            else:
                counsel_list, solicitor_list = self.instructed_by(representation)
                if counsel_list:
                    for couns in counsel_list:
                        couns_id = self.counsel.get(couns.strip())
                        if couns_id:
                            if 'appl' in couns:
                                client = 'applicant'
                            elif 'resp' in couns:
                                client = 'respondent'
                            else:
                                client = None

                            self.counsel_update_hashtable.add(f'{couns_id}\t{case_id}\t{client}\n')

                if solicitor_list:
                    for soli in solicitor_list:
                        soli_id = self.solicitors.get(soli.strip())
                        if soli_id:
                            if 'appl' in soli:
                                client = 'applicant'
                            elif 'resp' in soli:
                                client = 'respondent'
                            else:
                                client = None

                            self.solicitor_update_hashtable.add(f'{soli_id}\t{case_id}\t{client}\n')

        print('translating hashtables to strings')
        for soli in self.solicitor_update_hashtable:
            self.solicitor_update_table += soli
        for couns in self.counsel_update_hashtable:
            self.counsel_update_table += couns

        self.copy_rep_conns()

if __name__ == "__main__":
    reps_updater = RepresentationUpdater()
    reps_updater.parse_cases_for_reps()
    RepresentationUpdaterOld().parse_cases_for_reps()
    CaseRepConnecter().parse_for_connecting_reps()
