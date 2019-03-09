import tkinter as tk
from tkinter import ttk
import pickle
import datetime
import pandas as pd
import numpy as np


class DateWidget(tk.Frame):
    """Widget that shows displays a series of date buttons that can be clicked in order to view data from different days

    Parameters
    ----------
    parent: tk.Frame
        container frame
    controller: Application Object
        the root tk.Tk application object

    """

    months = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
              '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}

    days = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thur', 4: 'Fri', 5: 'Sat', 6: 'Sun'}

    def __init__(self, parent, controller):

        self.parent = parent

        super().__init__(self.parent, relief=tk.RAISED, borderwidth=3)

        # the widget consists of a single row

        self.grid_rowconfigure(0, weight=1)

        # a series of dates is first defined

        style = ttk.Style()
        style.configure('my.TButton', font=('Verdana', 7, 'bold'))

        # a new grid column is then generated for each date; a button is then placed in the newly created grid column, with the date as the button text.

        for i in range(10):
            self.grid_columnconfigure(i, weight=1)

        self.fill_buttons()

    def fill_buttons(self, dates=None):
        """Method that fills the Buttons on the widget with the corresponding dates; note that the first and last button contain arrows used for scrolling through dates. Scrolling through the dates works by deleting all the current
        Buttons and recreating them with the new dates. Hence, the fill_boxes() method is called eveytime the user clicks on the next date

        Parameters
        ----------
        dates: iterator
            iterator containing the dates the buttons should display

        """

        self.buttons = []

        if dates is None:
            dates = reversed([str(datetime.date.today() - datetime.timedelta(days=i))
                              for i in range(1, 11)])

        for i, date in enumerate(dates):

            # Note that the first and last buttons are arrows used to go to cycle between dates; hence the first and last dates are NOT displayed

            if not i:
                self.buttons.append(tk.Button(self, text='<', command=lambda: self.scroll(0)))
                self.buttons[i].grid(row=0, column=i, sticky='nsew')
            elif i == 9:
                self.buttons.append(tk.Button(self, text='>', command=lambda: self.scroll(1)))
                self.buttons[i].grid(row=0, column=i, sticky='nsew')
            else:
                date_str = self.convert_date(date)
                self.buttons.append(ttk.Button(
                    self, text='{}\n{} {}'.format(date_str[0], date_str[1], date_str[2]), style='my.TButton', command=lambda date=date: self.parent.fixtures.display_date(date)))
                self.buttons[i].grid(row=0, column=i, sticky='nsew')

    def convert_date(self, date):
        """Function used to convert from YYYY-MM-DD date format to string Weekday, Day, Month

        Returns
        -------
        returns formated date in tuple (weekday, day of month, month name)

        """

        comps = date.split('-')
        month = self.months[comps[1]]

        day = datetime.date(int(comps[0]), int(comps[1]), int(comps[2])).weekday()

        return (self.days[day], comps[2], month)

    def scroll(self, delta):
        """Method called when a user clicks on the arrow button that takes the user to the next date. Note that the new dates are displayed by deleting the current buttons and generating them again using the fill_buttons() method. The job of
        the following method is to generate the new date iterator

        Parameters
        ----------
        delta: int
            integer passed down by the arrow button. If delta == 1, the dates are advanced further in time. Else, if delta == 0, they are receded in time.

        """

        # a reverse mapping between months numers and month names is generated

        months_reversed = {month: num for num, month in self.months.items()}

        # the date on the last button is then retrieved; note that this is the starting point of the date iterator

        current_date = (self.buttons[8]['text']).replace('\n', ' ').split(' ')

        # the string is converted into a datetime object

        date = datetime.date(2019, int(months_reversed[current_date[2]]), int(current_date[1]))

        # the old buttons are then deleted

        del self.buttons

        # the new starting point for the iterator is defined. Note that, because the first and last dates in the date iterator are ignored, number of days added/subtracted from the starting date may not be intuitive

        if delta:
            start = date + datetime.timedelta(days=3)
        else:
            start = date + datetime.timedelta(days=1)

        # the new iterator is then created using the new starting date

        dates = reversed([str(start - datetime.timedelta(days=i))
                          for i in range(1, 11)])

        # the new buttons are then created with the new iterator

        self.fill_buttons(dates=dates)


class LeagueBarWidget(tk.Frame):
    """Widget that displays buttons with various leagues as button labels; clicking the button will display the data for that particular league

    Parameters
    ----------
    parent: tk.Frame object
        container object
    controller: Application Object
        the root tk.Tk application object

    """

    def __init__(self, parent, controller):

        self.parent = parent

        super().__init__(self.parent)

        # a style is first defined for the buttons

        style = ttk.Style()
        style.configure('my.TButton', font=('Verdana', 10, 'bold'))

        leagues = ['Premier League', 'German Bundesliga',
                   'Spanish La Liga', 'Italian Serie A', 'Champions League']

        buttons = {}

        self.grid_rowconfigure(0, weight=1)

        # A button is created for each league

        for i, league in enumerate(leagues):
            self.grid_columnconfigure(i, weight=1)

            buttons['league'] = ttk.Button(
                self, text=league, style='my.TButton', command=lambda league=league: self.display_league(league))
            buttons['league'].grid(column=i, row=0, sticky='nsew')

        self.display_league('Premier League')

    def display_league(self, league):
        """Callback Method that is called when a league button is clicked"""

        self.parent.fixtures.select_league(league)

        self.parent.view_table(league)


class LeagueFixtureWidget(tk.Frame):

    def __init__(self, parent, controller):

        super().__init__(parent, relief=tk.RAISED, borderwidth=1)

        # the fixture section grid is then configured

        self.parent = parent
        self.data = None

        self.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=30)

        # a frame for the title is configured

        title_frame = tk.Frame(self, relief=tk.RAISED, borderwidth=2)
        title_frame.grid(row=0, column=0, sticky='new', pady=10)

        title_frame.grid_rowconfigure(0, weight=1)
        title_frame.grid_columnconfigure(0, weight=3)
        title_frame.grid_columnconfigure(1, weight=1)

        # the name and date are then inserted into the title frameb

        self.title = ttk.Label(title_frame, text='League Fixtures', font=('Verdana', 10))
        self.title.grid(column=0, row=0, sticky='new')

        self.date = ttk.Label(title_frame, text='07-03-2019', font=('Verdana', 10))
        self.date.grid(column=1, row=0)

        # the body frame, which contains the majority of the context, is then defined. The Fixture Data is defined here

        self.body_frame = tk.Frame(self, relief=tk.RAISED, borderwidth=2)
        self.body_frame.grid(row=1, column=0, sticky='nsew')

        self.body_frame.grid_columnconfigure(0, weight=1)
        self.body_frame.grid_columnconfigure(0, weight=1)

        for i in range(10):
            self.body_frame.grid_rowconfigure(i, weight=1)

        self.cells = []

    def select_league(self, league):

        self.title['text'] = league

        self.data = self.parent.league_objects[league]

    def display_date(self, date):

        self.date['text'] = date

        try:
            self.fixtures = self.data.fixtures[date]
        except KeyError:

            self.fixtures = None

        self.display_fixtures(date)

    def display_fixtures(self, date):

        if self.cells:
            for cell in self.cells:
                cell.destroy()

        self.cells = []

        if self.fixtures is None:
            self.no_fix = ttk.Label(
                self.body_frame, text='No Fixtures for Selected Day', font=('Verdana', 10))
            self.no_fix.grid(row=0, columnspan=2)

        else:
            try:
                del self.no_fix
            except AttributeError:
                pass

            for i, fixture in enumerate(self.fixtures.values()):
                self.cells.append(FixtureCell(self.body_frame, fixture))
                self.cells[i].grid(row=i, column=0, sticky='ew', padx=5, pady=5)


class LeagueTableWidget(tk.Frame):

    def __init__(self, parent, controller, league):

        super().__init__(parent, relief=tk.RAISED, borderwidth=1)

        self.grid_rowconfigure(0, weight=1)

        for i in range(9):
            self.grid_columnconfigure(i, weight=1)

        self.select_league(league)

    def display_league(self):
        """Method called when the league is changed in the LeagueBarWidget"""

        self.teams = []

        for i, column in enumerate(self.data, start=1):

            label = ttk.Label(self, text=column, font=('Verdana', 6, 'bold'))
            label.grid(column=i, row=0)

        for j in range(self.data.shape[0]):
            team = self.data.iloc[j, :]
            self.grid_rowconfigure(j + 1, weight=1)

            self.teams.append(ttk.Button(self, text=team.name))
            self.teams[j].grid(row=j + 1, column=0, sticky='nsew')

            for k, val in enumerate(team):
                label = ttk.Label(self, text=str(val), font=('Verdana', 8))
                label.grid(row=j+1, column=k + 1)

    def select_league(self, league):
        league = league.replace(' ', '')
        with open(r'D:\PythonCode\WebProject\user_interface\data\{}.dat'.format(league), 'rb') as f:
            self.data = pickle.load(f).table._data

        self.display_league()


class FixtureCell(tk.Frame):

    def __init__(self, parent, fixture):

        super().__init__(parent)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        team_frame = tk.Frame(self, relief=tk.RAISED, borderwidth=2)
        team_frame.grid(row=0, columnspan=2, sticky='nsew')

        team_frame.grid_rowconfigure(0, weight=1)
        team_frame.grid_columnconfigure(0, weight=1)

        fixture_title = '{} vs {}'.format(fixture.home_team, fixture.away_team)

        title = ttk.Label(team_frame, text=fixture_title, font=('Verdana', '10'))
        title.grid(row=0, column=0, padx=5, pady=5)

        home_frame = tk.Frame(self, relief=tk.RAISED, borderwidth=2)
        home_frame.grid(row=1, column=0, sticky='nsew')

        home_frame.grid_rowconfigure(0, weight=1)
        home_frame.grid_columnconfigure(0, weight=3)
        home_frame.grid_columnconfigure(1, weight=1)

        home_score = ttk.Label(home_frame, text=str(
            fixture.home_score), font=('Verdana', 10, 'bold'))
        home_score.grid(row=0, column=1)

        away_frame = tk.Frame(self, relief=tk.RAISED, borderwidth=2)
        away_frame.grid(row=1, column=1, sticky='nsew')

        away_frame.grid_rowconfigure(0, weight=1)
        away_frame.grid_columnconfigure(1, weight=3)
        away_frame.grid_columnconfigure(0, weight=1)

        home_score = ttk.Label(away_frame, text=str(
            fixture.away_score), font=('Verdana', 10, 'bold'))
        home_score.grid(row=0, column=0)
