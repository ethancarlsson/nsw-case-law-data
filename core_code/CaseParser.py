'''
A module for parsing case law html.
'''
import re
from bs4 import BeautifulSoup as bs
import psycopg2


import datetime

from .connect_to_db import connect_to_db




class CoversheetParser():
    def __init__(self, html_doc):
        self.soup = bs(html_doc, 'lxml')
        self.full_coversheet = {
            'regular_coversheet': None,
            'appeal_info': None
            }
        self.select_correct_coversheet_parser()
        
    def select_correct_coversheet_parser(self):
        html_coversheet = self.soup.find('div', {'class': 'coversheet'})
        if html_coversheet is None:
            html_coversheet = self.soup.find_all('table', {
                'width': "100%",
                'border':"0",
                'cellspacing':"0",
                'cellpadding': "0"
                })

            coversheet_dictionary = self.parse_old_coversheet(html_coversheet)

            if html_coversheet is None:
                print('Incorrect parser')
        else:
            coversheet_dictionary = self.parse_normal_coversheet(html_coversheet)
        return coversheet_dictionary



    def parse_normal_coversheet(self, html_coversheet):
        def coversheet_to_dictionary(html_coversheet):
            left_col = [
                ele.text.strip().replace(':', '') for ele in
                html_coversheet.find_all('dt')
                ]
            right_col = [
                ele.text.strip() for ele in
                html_coversheet.find_all('dd')
                ]

            coversheet_dictionary = {k.lower():v for k, v in zip(left_col, right_col)}

            return coversheet_dictionary

        appeal = html_coversheet.find('div', {'class': 'row appeal'})

        if appeal:
            appeal.extract()
            self.full_coversheet['appeal_info'] = coversheet_to_dictionary(appeal)

        self.full_coversheet['regular_coversheet'] = coversheet_to_dictionary(html_coversheet)

        return self.full_coversheet

    def parse_old_coversheet(self, html_coversheet):
        coversheet_dictionary = {}

        def coversheet_to_dictionary_old(table):
            
            for table_row in table.find_all('tr'):
                row = table_row.find_all('td')
                if len(row) > 2:
                    key = row[1].text.lower().replace(':', '').strip().lower()
                    judgement_date_pattern = re.compile(r'(judgment date|date of judgment|decision date|date of decision)')
                    if key.find('ex tempore judgment date') > -1:
                        key = 'ex tempore judgment'
                    elif judgement_date_pattern.search(key):
                        if key.find('lower court date of decision') == -1:
                            key = 'decision date'



                    dictionary_item = {
                        key: row[2].text}
                    coversheet_dictionary.update(dictionary_item)

        for table in html_coversheet:
            coversheet_to_dictionary_old(table)
        
        self.full_coversheet['regular_coversheet'] = coversheet_dictionary
        return self.full_coversheet




    def get_decision_date(self, court, citation):
        coversheet_dict = self.full_coversheet.get('regular_coversheet')
        raw_date = coversheet_dict.get('decision date')

        if raw_date is None:
            raw_date_ex = coversheet_dict.get('ex tempore')
            if raw_date_ex:
                date_format1 = re.compile(r'[0-9]{2}/[0-9]{2}/[0-9]{4}') #checks for 00/00/0000 type dates
                check_date1 = date_format1.search(raw_date_ex)

                date_format2 = re.compile(r'[0-9]{1} \w+ [0-9]{4}') # chacks for 0 Month 0000 type dates
                check_date2 = date_format2.search(raw_date_ex)
                
                if check_date1:
                    clean_date = datetime.datetime.strptime(check_date1.group(), '%m/%d/%Y')
                elif date_format2:
                    if check_date2.group()[0] == '0': # ensures that it is 0 Month 0000 and not 00 Month 0000 then fixes it 
                        date_format2 = re.compile(r'[0-9]{2} \w+ [0-9]{4}') # chacks for 00 Month 0000 type dates
                        check_date2 = date_format2.search(raw_date_ex)
                    clean_date = datetime.datetime.strptime(check_date2.group(), '%d %B %Y')

        clean_date = None
        if raw_date:
            if citation.lower().find('number not in use') == -1 and citation.lower().find('decision restricted') == -1:
                raw_date.replace(r'\n', '').strip()
                date_format1 = re.compile(r'[0-9]{2}/[0-9]{2}/[0-9]{4}') #checks for 00/00/0000 type dates
                date_format2 = re.compile(r'[0-9]{2} \w+ [0-9]{4}') # chacks for 00 Month 0000 type dates

                check_date1 = date_format1.search(raw_date)
                check_date2 = date_format2.search(raw_date)
                
                if court == '] NSWCC' and len(raw_date) > 1:
                    clean_date = datetime.datetime.strptime(check_date1.group(), '%m/%d/%Y') # NSWCC uses month first format
                elif court == 'NSWIRCOMM':
                    clean_date = datetime.datetime.strptime(check_date1.group(), '%m/%d/%Y') # NSWIRCOMM uses month first format
                elif court == 'NSWADT':
                    if check_date1:
                        try:
                            clean_date = datetime.datetime.strptime(check_date1.group(), '%d/%m/%Y') # NSWADT uses month first format
                        except ValueError:
                            clean_date = datetime.datetime.strptime(check_date1.group(), '%m/%d/%Y') # NSWADT uses month first format
                    elif check_date2:
                        clean_date = datetime.datetime.strptime(check_date2.group(), '%d %B %Y')
                elif court == 'NSWIRC':   #NSWIRC uses month first and day first format, but 00/00/00 for month first
                                        #and 0 Month 0000 for day first
                    print(coversheet_dict)
                    if check_date1:                       
                        clean_date = datetime.datetime.strptime(check_date1.group(), '%m/%d/%Y')
                    else:
                        try:
                            clean_date = datetime.datetime.strptime(check_date2.group(), '%d %B %Y')
                        except AttributeError:

                            date_format3 = re.compile(r'[0-9] \w+ [0-9]{4}')
                            check_date3 = date_format3.search(raw_date)
                            clean_date = datetime.datetime.strptime(check_date3.group(), '%d %B %Y')

                elif check_date1:
                    try:
                        clean_date = datetime.datetime.strptime(check_date1.group(), '%d/%m/%Y')
                    except ValueError:
                        clean_date = datetime.datetime.strptime(check_date1.group(), '%m/%d/%Y')

                elif check_date2:
                    clean_date = datetime.datetime.strptime(check_date2.group(), '%d %B %Y')

            return clean_date


def get_court_from_citation(citation):
    find_court_pattern = re.compile(r'(NSW[A-Z]+|ADT)')
    
    return find_court_pattern.search(citation).group()


def connect_to_db():
    conn = connect_to_db()
    return conn

def pull_from_db(lower_bound):
    conn = connect_to_db()
    with conn.cursor() as cur:

        select_1000_cases = f'''
        SELECT case_id, uncleaned_html, case_link, citation FROM case_law
        WHERE case_id > {lower_bound}8584 AND case_id < {lower_bound+1}8584
        ORDER BY case_id;    
            '''
        cur.execute(select_1000_cases)
        uncleaned_html = cur.fetchall()
        return uncleaned_html

def update_date_record(case_id, date):
    conn = connect_to_db()
    with conn.cursor() as cur:
        update_query = f'''
        UPDATE case_law
        SET decision_date = '{date}'
        WHERE case_id = {case_id};
        '''
        cur.execute(update_query)
        conn.commit()



if __name__ == "__main__":
    for i in range(14, 25):
        cases = pull_from_db(i)
        for case in cases:
            print(case[2])
            coversheet = CoversheetParser(case[1])
            found_court = get_court_from_citation(case[3])
            print(found_court)

            date = coversheet.get_decision_date(found_court, case[3])

            if date:
                update_date_record(case[0], date.date())
            else:
                print(date)
