'''
For downloading all the cases
'''

import pickle


import concurrent.futures
import time
from random import randint

import requests
from bs4 import BeautifulSoup as bs

import psycopg2

from .connect_to_db import connect_to_db

class CaseScraper():
    case_data_structure = []


    def __init__(self):
        pickle_off = open("case_list_data.pickle", "rb")
        case_lists = pickle.load(pickle_off)
        pickle_off.close()

        grouped_case_lists = [case_lists[int(f'{i}000'): int(f'{i+1}000')] for i in range(70, 97)]
        for case_list in grouped_case_lists:
            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                future_to_url = {executor.submit(self.case_scraper, case[0], case[1]): case for case in case_list}
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        data = len(self.case_data_structure)
                        
                    except Exception as exc:
                        print('%r generated an exception: %s' % (url, exc))

                    else:
                        print(f'{data} cases have been scraped')
            self.upload_cases()
            self.case_data_structure.clear()

    def case_scraper(self, citation, link):
        time.sleep(randint(1, 2))

        page_url = f'https://www.caselaw.nsw.gov.au{link}'
        case = requests.get(page_url)

        body = str(case.text)

        self.case_data_structure += [
                (
                citation, # Case Name
                link, # Case Link
                body, # Uncleaned html
                )
            ]

    def upload_cases(self):
        conn = connect_to_db()
        cur = conn.cursor()
        print('inserting rows...')
        for case in self.case_data_structure:

            insert_case = f'''
                INSERT INTO case_law(citation, case_link, uncleaned_html)
                VALUES ('{str(case[0]).replace("'", '"')}', '{case[1]}', '{str(case[2]).replace("'", '"')}')
            '''
            cur.execute(insert_case)
        print('making the commit...')
        conn.commit()
        print('closing postgres...')
        cur.close()



            
if __name__ == "__main__":
    CaseScraper()
