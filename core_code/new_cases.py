'''
A file designed to run daily and scrape new cases from the web.
'''
from time import sleep
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup as bs

from connect_to_db import DBConnectedScraper
from add_search_info import find_date, find_judge, find_catchwords, find_court_match


class NewCaseScraper(DBConnectedScraper):
    '''
    Designed for scraping the latest cases that are not yet in the database.
    Overrides case_scraper in order to crawl into specific cases.
    '''
    def case_scraper(self, page_number, court_code):

        page_url = f'https://www.caselaw.nsw.gov.au/search/advanced?page={page_number}{court_code}'
        page = requests.post(page_url)
        soup = bs(page.text, 'lxml')
        body = soup.find('body')
        cases = body.find_all('div', class_='row result')
        for case in cases:
            sleep(3)
            link = case.find('a', href=True)['href']
            citation = case.find('a', href=True).get_text()
            self.case_data_structure[link] = (
                citation, # Case Name
                link, # Case Link
                requests.get(
                    f'https://www.caselaw.nsw.gov.au{case.find("a", href=True)["href"]}'
                    ).text,
                find_catchwords(case.find_all('div', {'class': 'hidden-xs hidden-sm'})),
                find_date(case.find_all('li', {'class': 'list-group-item'})), # dates
                find_judge(case.find_all('li', {'class': 'list-group-item'})), #judge
                find_court_match(citation),
                )


    def new_search_date_range(self):
        '''
        Gets current date in Australia and latest date already in the database.
        '''
        latest_db_date = self.get_latest_case_date()
        timezone_syd = pytz.timezone('Australia/Sydney')
        today_syd = datetime.now(timezone_syd)

        start_day = latest_db_date.strftime('%d')
        start_month = latest_db_date.strftime('%m')
        start_year = latest_db_date.strftime('%Y')
        start_date = f'{start_day}%2F{start_month}%2F{start_year}'

        end_day = today_syd.strftime('%d')
        end_month = today_syd.strftime('%m')
        end_year = today_syd.strftime('%Y')
        end_date = f'{end_day}%2F{end_month}%2F{end_year}'

        search_date_range = f'startDate={start_date}&endDate={end_date}'
        print(search_date_range)

        return search_date_range

    def make_date_court_code(self):
        self.case_list_links = [f'&sort=&body=&title=&before=&catchwords=&party=&mnc=&{self.new_search_date_range()}&fileNumber=&legislationCited=&casesCited=&courts=54a634063004de94513d827a&_courts=on&courts=54a634063004de94513d827b&_courts=on&courts=54a634063004de94513d8278&_courts=on&courts=54a634063004de94513d8279&_courts=on&courts=54a634063004de94513d827c&_courts=on&courts=54a634063004de94513d827d&_courts=on&courts=54a634063004de94513d828e&_courts=on&courts=54a634063004de94513d8285&_courts=on&courts=54a634063004de94513d827e&_courts=on&courts=54a634063004de94513d827f&_courts=on&courts=54a634063004de94513d8286&_courts=on&courts=54a634063004de94513d8280&_courts=on&courts=54a634063004de94513d8281&_courts=on&tribunals=54a634063004de94513d8282&_tribunals=on&tribunals=54a634063004de94513d8287&_tribunals=on&tribunals=54a634063004de94513d8289&_tribunals=on&tribunals=54a634063004de94513d828d&_tribunals=on&tribunals=54a634063004de94513d828b&_tribunals=on&tribunals=173b71a8beab2951cc1fab8d&_tribunals=on&tribunals=54a634063004de94513d828c&_tribunals=on&tribunals=54a634063004de94513d828a&_tribunals=on&tribunals=54a634063004de94513d8283&_tribunals=on&tribunals=1723173e41f6b6d63f2105d3&_tribunals=on&tribunals=5e5c92e1e4b0c8604babc749&_tribunals=on&tribunals=5e5c92c5e4b0c8604babc748&_tribunals=on&tribunals=54a634063004de94513d8284&_tribunals=on&tribunals=54a634063004de94513d8288&_tribunals=on']

    def get_latest_cases(self):
        self.make_date_court_code()
        self.pull_cases()
    
    def get_list_sin_duplicates(self) -> list:
        '''
        Returns only missing case data.
        '''
        self.get_latest_cases()
        newest_cases_db = self.newest_cases(self.get_latest_case_date())

        new_cases_set = set(self.case_data_structure.keys())
        old_cases_set = set(newest_cases_db)

        return list(new_cases_set.difference(old_cases_set))

    def upload_data_structure(self):
        add_sql_values = '''

        '''
        
        cases_to_upload = self.get_list_sin_duplicates()
        if len(cases_to_upload) > 0:
            for link in cases_to_upload:
                case = self.case_data_structure.get(link)
                values_to_insert = f'''
                INSERT INTO case_law (citation, case_link, uncleaned_html, decision_date, judge, catchwords, court)
                VALUES ('{case[0].replace("'", "`")}', '{case[1]}', '{case[2].replace("'", "`")}', '{case[4]}', '{case[5].replace("'", "`")}', '{str(case[3]).replace("'", "`")}', '{case[6]}');
                '''
                add_sql_values += values_to_insert
            self.update_records(add_sql_values)
        else:
            print(f"no new cases today ({datetime.now()})")



if __name__ == "__main__":
    NewCaseScraper().upload_data_structure()


    