'''
Helper functions for adding extra informaiton from the search page of NSW Case Law website.
'''
import pickle
import datetime
import re

from connect_to_db import connect_to_db

def find_date(date_html):
    date_format = re.compile(r'[0-9]{2} \w+ [0-9]{4}') # chacks for 00 Month 0000 type dates
    for html in date_html:
        soup = html.text
        if soup:
            check_date = date_format.search(soup)
            if check_date:
                return datetime.datetime.strptime(check_date.group(), '%d %B %Y')
    return None

def find_judge(judge_html):
    return judge_html[1].text.strip().replace("'", "`")

def find_catchwords(catchwords_html):
    if len(catchwords_html) > 0:
        return catchwords_html[0].text.lower().replace('catchwords:', '').strip().replace("'", "`")
    else: 
        return catchwords_html

def find_court_match(citation):
    court_pattern = re.compile(r'] NSW[A-Za-z]+')
    court_match = court_pattern.search(citation)
    if court_match:
        court_match = court_match.group().replace('] ', '')
        return court_match


def update_sql_query(link, date, judge, catchwords):
    if date:
        sql = f'''

        UPDATE case_law
        SET decision_date = '{date}',
            judge = '{judge}',
            catchwords = '{catchwords}'


        WHERE case_link = '{link}';
        '''
    else:
        sql = f'''
        UPDATE case_law
        SET judge = '{judge}',
            catchwords = '{catchwords}'

        WHERE case_link = '{link}';
        '''

    return sql

def update_records(sql):
    conn = connect_to_db()
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()

def add_search_info(pickle_file_name):
    print(f'adding information from {pickle_file_name}...')
    SQL_QUERY = '''

    '''

    with open(f"{pickle_file_name}.pickle", "rb") as pickle_off:
        cases = pickle.load(pickle_off)
        print('writing query...')
        for case in cases:
            lnk = case[1]
            dte = find_date(case[3])
            jdge = find_judge(case[3])
            ctchwords = find_catchwords(case[2])

            SQL_QUERY += update_sql_query(lnk, dte, jdge, ctchwords)
    print('updating records...')
    update_records(SQL_QUERY)
    print('finished!')

if __name__ == "__main__":
    add_search_info('case_list_data_appellates')
    add_search_info('case_list_data_childrens_and_comp')
    add_search_info('case_list_data_district_drug_IR')
    add_search_info('case_list_data_LnE_local')
    add_search_info('case_list_data_supreme')

