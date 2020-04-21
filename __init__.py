import dateutil
import holidays
import datetime 
from dateutil import rrule

class TermDates(object):

    def __init__(self, start_year=2012, end_year=None):
        """Get important dates on Ball State University's Academic Calendar
        
        I determined the patterns (repeating rules) empirically, by downloading the
        academic calendars for years since 2012.
        
        Parameters
        ----------
        start_year : int
            First academic year to produce dates.
        end_year : int
            Last academic year to produce dates. 

        """
        self.semesters = ['Fall', 'Spring', 'Summer']
        self.sem_code_to_int = { 'Fall': 10, 'Spring': 20, 'Summer': 30 }
        self.int_to_sem_code = { v:k for k, v in self.sem_code_to_int.items() }

        if start_year < 2012:
            print('warning: dates have not been validated prior to 2012')
        self.min_date = datetime.date(start_year, 8, 1)
        if end_year is None:
            end_year = datetime.datetime.now().year + 2
        self.max_date = datetime.date(end_year, 8, 1)

        self.years = list(range(self.min_date.year, self.max_date.year))
        # self.terms = [ 100*yr + sem for yr in self.years for sem in [10, 20, 30] ]
        self.n_yrs = len(self.years)

        # First class
        # Last class
        # Finals
        # Midterm grade due
        # Withdraws end
        # Late registration
        # Breaks

        term_length = datetime.timedelta(days=116)
        sum_term_length = datetime.timedelta(days=68)
        xmas_break = datetime.timedelta(days=24)

        thanksgiving = iter(rrule.rrule(rrule.YEARLY, 
                                        dtstart=self.min_date, 
                                        # until=self.max_date,
                                        count=self.n_yrs + 1,
                                        bymonth=11,
                                        byweekday=rrule.TH(4)))

        labor_day = iter(rrule.rrule(rrule.YEARLY, 
                                    dtstart=self.min_date, 
                                    # until=self.max_date,
                                    count=self.n_yrs + 1,
                                    bymonth=9,
                                    byweekday=rrule.MO(1)))

        fall_start = iter(rrule.rrule(rrule.YEARLY, 
                                    dtstart=self.min_date, 
                                    # until=self.max_date,
                                    count=self.n_yrs + 1,
                                    bymonth=8, 
                                    byweekday=rrule.MO(-2)))

        fall_break_start = iter(rrule.rrule(rrule.YEARLY, 
                                        dtstart=self.min_date, 
                                        # until=self.max_date, 
                                        count=self.n_yrs + 1,
                                        bymonth=10, 
                                        byweekday=rrule.MO(-2)))
        # academic calendar
        self.acad_dates = {}
        for yr in self.years:
            yr_dates = {}

            # fall term
            f_start = next(fall_start)
            f_end = f_start + term_length

            f_break_start = next(fall_break_start)
            f_break_end = self._add_days(f_break_start, 1)
            f_withdraw_end = self._add_days(f_break_end, 1)

            f_thank_break_start = self._add_days(next(thanksgiving), -1)
            f_thank_break_end = self._add_days(f_thank_break_start, 4)

            yr_dates['Fall Term Start'] = f_start
            yr_dates['Fall Classes Start'] = f_start
            yr_dates['Fall Late Registration Start'] = f_start
            yr_dates['Fall Late Registration End'] = self._add_days(f_start, 4)

            yr_dates['Labor Day'] = next(labor_day)

            yr_dates['Fall Classes End'] = self._add_days(f_end, 4)            
            yr_dates['Fall Term End'] = f_end        

            # spring term
            # import pdb
            sp_start = self._add_days(f_end, xmas_break)
            sp_end = self._add_days(sp_start, term_length)
            # pdb.set_trace()

            yr_dates['Spring Term Start'] = sp_start
            yr_dates['Spring Term End'] = sp_end

            # summer term
            sm_start = self._add_days(sp_end, 10)
            sm_end = self._add_days(sp_start, sum_term_length)

            yr_dates['Summer Term Start'] = sm_start
            yr_dates['Summer Term End'] = sm_end

            self.acad_dates[yr] = yr_dates

    def get_by_termcode(self, term, field):
        if isinstance(term, str):
            term = int(term)
        yr = int(round(term, -2)/100)
        return self.acad_dates[yr][field]

    def _add_days(self, d, days):
        if isinstance(days, int):
            return d + datetime.timedelta(days=days)
        elif isinstance(days, datetime.timedelta):
            return d + days
        else:
            raise ValueError("days argument must be type int or datetime.timedelta")

    def fall_start(self):
        """Fall terms start the second to last Monday of August"""
        irule = iter(rrule.rrule(rrule.YEARLY, 
                                dtstart=self.min_date, 
                                # until=self.max_date,
                                count=self.n_yrs + 1,
                                bymonth=8, 
                                byweekday=rrule.MO(-2)))
        for date in irule:
            yield date

    def fall_break_start(self):
        """Fall break starts the second to last Monday of August"""
        irule = iter(rrule.rrule(rrule.YEARLY, 
                                dtstart=self.min_date, 
                                # until=self.max_date, 
                                count=self.n_yrs + 1,
                                bymonth=10, 
                                byweekday=rrule.MO(-2)))
        for date in irule:
            yield date
