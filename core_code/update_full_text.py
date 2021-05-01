'''
Modules for bringing full text of the decision (minus the coversheet) out of the html
'''
from bs4 import BeautifulSoup as bs
import re
from connect_to_db import DBConnector, update_records


class FullText(DBConnector):

    sql = '''
    SELECT case_id, uncleaned_html 
    FROM case_law 
    WHERE judgment_text is Null;
    '''
    def __init__(self):
        print('fetching records...')

        self.all_html = self.fetch_records(self.sql)
        self.update_sql = str()

    @staticmethod
    def enumerate_paragraphs(full_text):
        '''
        Turns list items into numbers.
        '''
        li_pattern = re.compile(r'<li.*>')

        list_items = li_pattern.findall(full_text)
        for l_i in enumerate(list_items):
                full_text = full_text.replace(l_i[1], f'[{l_i[0]+1}]', 1)
        return bs(full_text, 'lxml').text


    def run_update(self):
        '''
        Parses over cases in order to write the sql query
        '''
        print('writing sql query...')
        for html in self.all_html:
            judgment_body = bs(html[1], 'lxml').find('div', {'class': 'body'})

            if judgment_body:
                judgment_text = judgment_body.text.replace("'", "''")
            else:
                judgment_text = None

            self.update_sql += f'''

            UPDATE case_law
            SET judgment_text = '{judgment_text}'
            WHERE case_id = {html[0]};

            '''
        if len(self.update_sql) > 0:
            print('updating records...')
            update_records(self.update_sql)

class FullTextCase(DBConnector):
    sql = '''
        SELECT judgment_texts.case_id, judgment_texts.judgment_text
        FROM judgment_texts
        INNER JOIN case_law ON judgment_texts.case_id=case_law.case_id
        WHERE case_law.judgment_text is Null;
        '''

    def __init__(self):
        print('fetching records...')
        self.all_judgments = self.fetch_records(self.sql)
        self.update_sql = str()

    def update_with_text(self):
        print('updating text...')
        for judgment in self.all_judgments:
            self.update_sql += f'''

            UPDATE case_law
            SET judgment_text = '{judgment[1].replace("'", "''")}'
            WHERE case_id = {judgment[0]};

            '''
        if self.update_sql:
            self.update_records(self.update_sql)

if __name__ == "__main__":
    FullText().run_update()
