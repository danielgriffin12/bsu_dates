import logging
import dateutil
import datetime
import pandas as pd
from dateutil import rrule


class BSUCalendar(object):
    def __init__(self, start_year=2012, end_year=None, log_level="ERROR"):
        """Get important dates on Ball State University's Academic Calendar
        
        Repeating rules for dates were determined by hand, recognizing patterns
        in academic calendars posted online. Only checked back to 2012.
        
        Parameters
        ----------
        start_year : int
            First academic year to produce dates (e.g. 2019 == '2019-2020 academic year')
        end_year : int
            Last academic year to produce dates
        log_level : str
            Level to pass to logger. See logging module.

        """
        self._set_logger(log_level)
        self._semesters = ["Fall", "Spring", "Summer"]
        self._sem_code_to_int = {"Fall": 10, "Spring": 20, "Summer": 30}
        self._int_to_sem_code = {v: k for k, v in self._sem_code_to_int.items()}

        self.holidays = (
            "Thanksgiving Break",
            "Labor Day",
            "MLK Day",
            "Memorial Day",
            "Independence Day",
        )

        # self.tags = {
        #     "Registration": (
        #         "Late Registration Start",
        #         "Late Registration End",
        #         "Withdraw Deadline",
        #     ),
        #     "Instruction": (
        #         "Classes Start",
        #         "Classes End",
        #         "Break Start",
        #         "Break End",
        #         "Finals Start",
        #         "Finals End",
        #         "Final Grades Due",
        #     ),
        #     "Holidays": self.holidays,
        # }
        # TODO: "Midterm Grades Due", for Instruction

        if start_year < 2012:
            self._logger.warning("Dates have not been validated prior to 2012")
        self.min_date = datetime.date(start_year, 8, 1)
        if end_year is None:
            end_year = datetime.datetime.now().year + 2

        self.years = list(range(start_year, end_year))
        self.n_yrs = len(self.years)
        # self.terms = [ 100*yr + sem for yr in self.years for sem in [10, 20, 30] ]

        # Midterm grade due

        term_length = datetime.timedelta(days=116)
        sum_term_length = datetime.timedelta(days=68)
        xmas_break = datetime.timedelta(days=24)

        # Generators that yield holidays and special days
        timeframe = dict(dtstart=self.min_date, count=self.n_yrs)
        thanksgiving = self._thanksgiving(**timeframe)
        labor_day = self._labor_day(**timeframe)
        mlk_day = self._mlk_day(**timeframe)
        memorial_day = self._memorial_day(**timeframe)
        independence_day = self._independence_day(**timeframe)

        fall_start = self._fall_start(**timeframe)
        fall_break_start = self._fall_break_start(**timeframe)
        spring_withdraw = self._spring_withdraw_deadline(**timeframe)

        # Creates dataframe with columns:
        #   Term, Year, Semester, DateName, Date, Tags
        dates = []
        for yr in self.years:
            # fall term
            f_start = next(fall_start)
            f_end = f_start + term_length
            # spring term
            sp_start = self._add_days(f_end, xmas_break)
            sp_end = self._add_days(sp_start, term_length)
            # summer term
            sm_start = self._add_days(sp_end, 10)
            sm_end = self._add_days(sp_start, sum_term_length)

            dates.append(
                self._get_fall_dates(
                    yr, f_start, f_end, fall_break_start, labor_day, thanksgiving,
                )
            )
            dates.append(
                self._get_spring_dates(yr, sp_start, sp_end, mlk_day, spring_withdraw)
            )
            dates.append(
                self._get_summer_dates(
                    yr, sm_start, sm_end, memorial_day, independence_day
                )
            )

        self.dates_df = pd.concat(dates)

    # def date_in_term(self, term, field):
    #     """Get a date in a term"""
    #     if isinstance(term, str):
    #         term = int(term)
    #     yr = int(round(term, -2) / 100)
    #     return self.dates.loc[self.dates.Term.eq(term), field]
    #     return self.dates[yr][field]

    # def dates_by_tag(self, tag):
    #     """Get all dates for a tag"""
    #     yr = int(round(term, -2) / 100)
    #     sem = self._int_to_sem_code(term - round(term, -2))
    #     if tag in self.tags:
    #         fields = self.tags[tag]
    #         if tag == "Holidays":
    #             vals = {}
    #             for hol in self.holidays:
    #                 if hol == "Thanksgiving Break":
    #                     hol_d = self.get_holiday(hol.rstrip(" Break"))
    #                     vals[hol + " Start"] = self._add_days(hol_d, -1)
    #                     vals[hol + " End"] = self._add_days(hol_d, 1)
    #                 else:
    #                     vals[hol] = self.get_holiday(hol)
    #         else:
    #             vals = {
    #                 f"{sem} {fld}": self.dates[f"{sem} {fld}"]
    #                 for sem in self._semesters
    #                 for fld in fields
    #             }
    #         return vals
    #     else:
    #         ValueError(
    #             f"{tag} not valid. Choose from: {list(self.tags.keys()).__str__()}"
    #         )

    def get_holiday(self, holiday, ac_year):
        """Return the date of a holiday for a given academic year"""
        attr_name = "_" + holiday.lower().replace(" ", "_")
        if hasattr(self, attr_name):
            gen_holiday = getattr(self, attr_name)
            if holiday in ["MLK Day", "Memorial Day", "Independence Day"]:
                ac_year += 1
            return list(gen_holiday(dtstart=datetime.date(ac_year, 1, 1), count=1))[0]
        else:
            raise ValueError(f"Holiday {holiday} not recognized")

    def _get_fall_dates(
        self, yr, f_start, f_end, fall_break_start, labor_day, thanksgiving
    ):
        """Fall term important dates"""
        f_term = 100 * yr + 10
        f_break_start = next(fall_break_start)
        f_break_end = self._add_days(f_break_start, 1)
        f_withdraw_end = self._add_days(f_break_end, 1)
        f_labor = next(labor_day)
        f_thank = next(thanksgiving)
        f_thank_break_start = self._add_days(f_thank, -1)
        f_thank_break_end = self._add_days(f_thank_break_start, 2)

        # DateName, Date, Tags
        rows = [
            ["Term Start", f_start, "Instruction"],
            ["Classes Start", f_start, "Instruction"],
            ["Late Registration Start", f_start, "Registration"],
            ["Late Registration End", self._add_days(f_start, 4), "Registration"],
            ["Break Start", f_break_start, "Instruction"],
            ["Break End", f_break_end, "Instruction"],
            ["Withdraw Deadline", f_withdraw_end, "Registration"],
            ["Thanksgiving Break Start", self._add_days(f_thank, -1), "Instruction"],
            ["Thanksgiving", f_thank, "Instruction,Holiday"],
            ["Thanksgiving Break End", self._add_days(f_thank, 1), "Instruction"],
            ["Labor Day", f_labor, "Instruction,Holiday"],
            ["Classes End", self._add_days(f_end, -4), "Instruction"],
            ["Finals Start", self._add_days(f_end, -3), "Instruction"],
            ["Finals End", f_end, "Instruction",],
            ["Term End", self._add_days(f_end, -3), "Instruction"],
            ["Final Grades Due", self._add_days(f_end, 3), "Instruction"],
        ]

        return self._make_semester_df(yr, "Fall", rows)

    def _get_spring_dates(self, yr, sp_start, sp_end, mlk_day, spring_withdraw):
        """Spring term important dates"""
        if yr == 2013:
            sp_break_start = sp_start + datetime.timedelta(weeks=9)
        else:
            sp_break_start = sp_start + datetime.timedelta(weeks=8)

        rows = [
            ["Term Start", sp_start, "Instruction"],
            ["Classes Start", sp_start, "Instruction"],
            ["MLK Day", next(mlk_day), "Instruction,Holiday"],
            ["Break Start", sp_break_start, "Instruction"],
            ["Break End", self._add_days(sp_break_start, 4), "Instruction"],
            ["Withdraw Deadline", next(spring_withdraw), "Registration"],
            ["Classes End", self._add_days(sp_end, -4), "Instruction"],
            ["Finals Start", self._add_days(sp_end, -3), "Instruction"],
            ["Finals End", sp_end, "Instruction"],
            ["Term End", sp_end, "Instruction"],
            ["Final Grades Due", self._add_days(sp_end, 3), "Instruction"],
        ]

        return self._make_semester_df(yr, "Spring", rows)

    def _get_summer_dates(self, yr, sm_start, sm_end, memorial_day, independence_day):
        """Summer term important dates"""
        rows = [
            ["Term Start", sm_start, "Instruction"],
            ["Independence Day", next(independence_day), "Instruction,Holiday"],
            ["Term End", sm_end, "Instruction"],
            ["Final Grades Due", self._add_days(sm_end, 3), "Instruction"],
        ]
        return self._make_semester_df(yr, "Summer", rows)

    def _make_semester_df(self, yr, semester, rows):
        """Take list of semester date data and return DataFrame"""
        term = 100 * yr + self._sem_code_to_int[semester]
        n_rows = len(rows)
        data = {
            "Term": n_rows * [term],
            "Semester": n_rows * [semester],
            "Year": n_rows * [yr],
            "DateName": [r[0] for r in rows],
            "Date": [r[1] for r in rows],
            "Tags": [r[2] for r in rows],
        }
        return pd.DataFrame(data=data)

    def _set_logger(self, level):
        """Create logger with level"""
        logger = logging.getLogger("bsu_dates")
        logger.setLevel(level)
        ch = logging.StreamHandler()
        logger.addHandler(ch)
        self._logger = logger

    def _add_days(self, d, days):
        """Add timedelta or integer number of days to a date"""
        if isinstance(days, int):
            return d + datetime.timedelta(days=days)
        elif isinstance(days, datetime.timedelta):
            return d + days
        else:
            raise ValueError("days argument must be type int or datetime.timedelta")

    def _irule(self, **kwargs):
        """Return iterator for dates defined by a repeating rule
        
        See: dateutil.rrule docs on defining repeating rules
        """
        assert "freq" in kwargs, "Must have freq argument"

        kwargs = {key: val for key, val in kwargs.items() if not val is None}

        self._logger.debug("_irule args: " + kwargs.__str__())

        freq = kwargs.pop("freq")

        if not ("until" in kwargs or "count" in kwargs):
            if "until" in kwargs and "count" in kwargs:
                raise ValueError("Specify either count or until, not both")
            else:
                raise ValueError("Must specify either count or until.")

        return iter(rrule.rrule(freq, **kwargs))

    def _thanksgiving(self, dtstart=None, until=None, count=None):
        """Thanksgiving is the last thursday of every november"""
        kwargs = {
            "freq": rrule.YEARLY,
            "bymonth": 11,
            "byweekday": rrule.TH(4),
            "dtstart": dtstart,
            "until": until,
            "count": count,
        }
        return self._irule(**kwargs)

    def _labor_day(self, dtstart=None, until=None, count=None):
        """Labor day is the first monday of September"""
        kwargs = {
            "freq": rrule.YEARLY,
            "bymonth": 9,
            "byweekday": rrule.MO(1),
            "dtstart": dtstart,
            "until": until,
            "count": count,
        }
        return self._irule(**kwargs)

    def _mlk_day(self, dtstart=None, until=None, count=None):
        """MLK day is the third monday of January"""
        kwargs = {
            "freq": rrule.YEARLY,
            "bymonth": 1,
            "byweekday": rrule.MO(3),
            "dtstart": dtstart,
            "until": until,
            "count": count,
        }
        return self._irule(**kwargs)

    def _memorial_day(self, dtstart=None, until=None, count=None):
        """Memorial day is the last monday of March"""
        kwargs = {
            "freq": rrule.YEARLY,
            "bymonth": 3,
            "byweekday": rrule.MO(-1),
            "dtstart": dtstart,
            "until": until,
            "count": count,
        }
        return self._irule(**kwargs)

    def _independence_day(self, dtstart=None, until=None, count=None):
        """Independence day is the 4th of July"""
        kwargs = {
            "freq": rrule.YEARLY,
            "bymonth": 7,
            "bymonthday": 4,
            "dtstart": dtstart,
            "until": until,
            "count": count,
        }
        return self._irule(**kwargs)

    def _fall_start(self, dtstart=None, until=None, count=None):
        """Fall term starts the second to last Monday of August"""
        kwargs = {
            "freq": rrule.YEARLY,
            "bymonth": 8,
            "byweekday": rrule.MO(-2),
            "dtstart": dtstart,
            "until": until,
            "count": count,
        }
        return self._irule(**kwargs)

    def _fall_break_start(self, dtstart=None, until=None, count=None):
        """Fall break starts the second to last Monday of October"""
        kwargs = {
            "freq": rrule.YEARLY,
            "bymonth": 10,
            "byweekday": rrule.MO(-2),
            "dtstart": dtstart,
            "until": until,
            "count": count,
        }
        return self._irule(**kwargs)

    def _spring_withdraw_deadline(self, dtstart=None, until=None, count=None):
        """Spring withdraw deadline is the third Monday in March"""
        kwargs = {
            "freq": rrule.YEARLY,
            "bymonth": 3,
            "byweekday": rrule.MO(3),
            "dtstart": dtstart,
            "until": until,
            "count": count,
        }
        return self._irule(**kwargs)
