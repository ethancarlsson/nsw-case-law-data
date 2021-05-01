import re

class Representation():
    def __init__(self, representation) -> str:
        self.representation = representation.replace('\t', '')
        self.reps_dict = dict()
        self.find_counsel()
        self.find_solicitors()
        print(self.reps_dict)

    def find_counsel(self):
        '''
        Finds the barristers in the case.
        '''
        rep_pattern = re.compile(r'counsel(.|\s)*solicitors') #gets all info between counsel and solicitors (or the end if there is no solicitor after counsel)
        reps = rep_pattern.match(self.representation)
        if reps is not None:
            reps_list = reps.group().split('\n')
        else:
            reps_list = [self.representation]
        counsel_dict = {
            'applicant_counsel': list(),
            'respondent_counsel': list()
        }
        for rep in reps_list:
            if 'applicant' in rep:
                counsel_dict['applicant_counsel'].append(rep)
            elif 'appellant' in rep:
                counsel_dict['applicant_counsel'].append(rep)
            elif 'respondent' in rep:
                counsel_dict['respondent_counsel'].append(rep)
        self.reps_dict.update(counsel_dict)

    def find_solicitors(self):
        '''
        Finds the solicitors in the case
        '''
        rep_pattern = re.compile(r'solicitors(.|\s)*') #gets all info between solicitors and counsel (or the end if there is no counsel after solicitor)
        reps = rep_pattern.search(self.representation)
        if reps is not None:
            reps_list = reps.group().split('\n')
        else:
            reps_list = [self.representation]
        solicitor_dict = {
            'applicant_solicitors': list(),
            'respondent_solicitors': list()
        }

        for rep in reps_list:
            if 'applicant' in rep:
                solicitor_dict['applicant_solicitors'].append(rep)
            elif 'appellant' in rep:
                solicitor_dict['applicant_solicitors'].append(rep)
            elif 'respondent' in rep:
                solicitor_dict['respondent_solicitors'].append(rep)
        self.reps_dict.update(solicitor_dict)
