'''
Original module for scraping case law in NSW. 
'''
from random import randint
from math import ceil
import concurrent.futures
import time
import sys
import re
import pickle
import requests
from bs4 import BeautifulSoup as bs

sys.setrecursionlimit(10000)

class CaseLawScraper():
    '''
    A spider that uses concurrency to rapidly take all cases from NSW Case Law.
    '''
    case_data_structure = {}

    def __init__(self, link_list=None, workers=1):
        self.case_list_links = link_list
        self.workers = workers

    def pickle_cases(self, pickle_name):
        '''
        Function for picking case law.
        '''
        self.pull_cases()
        with open(f'{pickle_name}.pickle', 'wb') as case_data_storage:
            pickle.dump(self.case_data_structure, case_data_storage)


    def build_case_list(self):
        case_list = []

        for cases in self.case_list_links:
            search_range = self.find_search_range(cases)

            case_list += [(cases, page) for page in range(search_range)]

        return case_list

    def pull_cases(self):
        case_list = self.build_case_list()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_url = {executor.submit(self.case_scraper, court_id[1], court_id[0]): court_id for court_id in case_list}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = len(self.case_data_structure)
                    
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                
                else:
                    print(f'{data} cases have been scraped')
        

    def case_scraper(self, page_number, court_code):
        time.sleep(randint(1,2))

        page_url = f'https://www.caselaw.nsw.gov.au/search/advanced?page={page_number}{court_code}'
        page = requests.post(page_url)
        soup = bs(page.text, 'lxml')
        body = soup.find('body')
        cases = body.find_all('div', class_='row result')
        for case in cases:
            link = case.find('a', href=True)['href']
            self.case_data_structure[link] = (
                    case.find('a', href=True).get_text(), # Case Name
                    link, # Case Link
                    # requests.get(f'https://www.caselaw.nsw.gov.au{case.find("a", href=True)["href"]}').text
                    case.find_all('div', {'class': 'hidden-xs hidden-sm'}), # Catchwords uncleaned
                    case.find_all('li', {'class': 'list-group-item'}) # Judge and dates uncleaned
                )
    def find_search_range(self, court_code):
        page_url = f'https://www.caselaw.nsw.gov.au/search/advanced?page={court_code}'
        page = requests.get(page_url)
        soup = bs(page.text, 'lxml')
        pagination_container = soup.find('div', {'id': "paginationcontainer"})

        displayed_results = pagination_container.text.strip()

        number_checker = re.compile(r'[0-9]+') #checks for 00/00/0000 type dates
        numbers = number_checker.findall(displayed_results)

        full_length = int(numbers[2])

        search_range = ceil(full_length / 20)

        return search_range


class CaseLawNSW(CaseLawScraper):
    case_list_links = [
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&courts=54a634063004de94513d827a&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        5), # childrens court
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&courts=54a634063004de94513d827b&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        14), # compensation court
        (r'&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=01%2F01%2F2000&endDate=31%2F12%2F2020&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&courts=54a634063004de94513d8278&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        424), #court of appeal 2000 to 2020
        (r'&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=01%2F01%2F1966&endDate=01%2F01%2F2000&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&courts=54a634063004de94513d8278&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        201), #court of appeal 1966 to 2000 (1966 is the founding of the court of appeal)
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d8279&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        422), #criminal court of appeal
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d827c&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        339), # District court
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d827d&_courts=on&courts=54a634063004de94513d828e&_courts=on&courts=54a634063004de94513d8285&_courts=on&courts=54a634063004de94513d827e&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        292), # drug court, industrial court, Industrial Relations Commission (Commissioners) (judges),
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d827f&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        449), # L&E court (commissioners)
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d8286&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        292), # L&E court (judges)
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d8280&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        24), # Local Court
        (r'&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=01%2F01%2F1823&endDate=31%2F12%2F2005&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d8281&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        443), # Supreme court 1823 to 2005
        (r'&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=01%2F01%2F2006&endDate=31%2F12%2F2010&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d8281&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        371), # Supreme court 2006 to 2010
        (r'&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=01%2F01%2F2011&endDate=31%2F12%2F2015&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d8281&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        472), # Supreme court 2011 to 2015
        (r'&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=01%2F01%2F2016&endDate=31%2F12%2F2020&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&courts=54a634063004de94513d8281&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        477), # Supreme court 2016 to 2020
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&tribunals=54a634063004de94513d8282&_tribunals=on&tribunals=54a634063004de94513d8287&_tribunals=on&tribunals=54a634063004de94513d8289&_tribunals=on&tribunals=54a634063004de94513d828d&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on',
        456), # Administrative Decisions Tribunal (Appeal Panel) Administrative Decisions Tribunal (Divisions) Civil and Administrative Tribunal (Administrative and Equal Opportunity Division) Civil and Administrative Tribunal (Appeal Panel)
        ('&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&tribunals=54a634063004de94513d828b&_tribunals=on&tribunals=173b71a8beab2951cc1fab8d&_tribunals=on&tribunals=54a634063004de94513d828c&_tribunals=on&tribunals=54a634063004de94513d828a&_tribunals=on&tribunals=54a634063004de94513d8283&_tribunals=on&tribunals=1723173e41f6b6d63f2105d3&_tribunals=on&tribunals=5e5c92e1e4b0c8604babc749&_tribunals=on&tribunals=5e5c92c5e4b0c8604babc748&_tribunals=on&tribunals=54a634063004de94513d8284&_tribunals=on&tribunals=54a634063004de94513d8288&_tribunals=on',
        167), # Civil and Administrative Tribunal (Consumer and Commercial Division) Civil and Administrative Tribunal (Enforcement) Civil and Administrative Tribunal (Guardianship Division)Civil and Administrative Tribunal (Occupational Division) Dust Diseases Tribunal Equal Opportunity Tribunal Fair Trading Tribunal Legal Services Tribunal Medical Tribunal Transport Appeal Boards
    ]

if __name__ == "__main__":
    CaseLawScraper(link_list=[
        '&sort=&body=&title=&before=&catchwords=&party=&mnc=&startDate=&endDate=&fileNumber=&legislationCited=&casesCited=&courts=54a634063004de94513d827a&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_courts=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on&_tribunals=on'
        ]).pull_cases()