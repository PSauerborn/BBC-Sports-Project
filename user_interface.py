import tkinter as tk
from tkinter import ttk
import sys
import datetime
import numpy as np
import pandas as pd
import pickle
from get_data import League, LeagueTable, PlayerTable
from widgets import *

SMALL_FONT = ('Verdana', 8)


class Application(tk.Tk):
    """Defines the parent frame of the application; note that the following application works by stacking frames on top of each other. The main container object therefore must have only one grid row and column; the stacked frames
    will be visible underneath each other. The Application object is passed down to each individual frame and is meant to act as a form of

    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # the container frame is defined and packed into the main window; note that all frame objects require some sort of parent, and the container acts as said parent.

        container = tk.Frame(self)

        # the grid of the container is then configured. Note that the container object must have the below configuration so that all individual pages fill the entire parent container. Otherwise, if multiple rows/columns are used, the underlying stacked
        # widgets can cause unwanted behaviour. The exact configuration of a frame should be specified within the Page object itself.

        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # all subsequent frames are stored in the self.frames dictionary

        self.frames = {}

        for F in (MainPage,):

            # the frame is then instantiated; note that the tk.Frame objects __init__ method only requires the container as an input, and this is what is used to instantiate the frame

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(MainPage)

    def show_frame(self, container):
        """Method Used to raise a frame to the front

        Parameters
        ----------
        container: tk.Frame object
            desired frame object

        """

        frame = self.frames[container]

        frame.tkraise()

    def exit_client(self):
        """Method use to exit the app"""

        sys.exit()


class MainPage(tk.Frame):
    """Class defining the main page, which itself consists of 4 seperately defined widgets"""

    def __init__(self, parent, controller):

        super().__init__(parent)

        # the main page is split into three areas; the top area contains the league selection bar, the second area contains the date selection bar, and the final area contains the data

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=30)

        # the league fixture widget is added

        self.fixtures = LeagueFixtureWidget(self, controller)
        self.fixtures.grid(row=2, column=0, sticky='nsew', pady=5, padx=5)

        # a copy of all the league tables are then created; note that because these are only created once, they are created while loading and stored for retrieval to save time. Note that these are stacked and the proper table is raised when called

        self.league_tables = {}
        self.league_objects = {}

        leagues = ['Premier League', 'German Bundesliga',
                   'Spanish La Liga', 'Italian Serie A']

        for league in leagues:

            with open(r'D:\PythonCode\WebProject\user_interface\data\{}.dat'.format(league.replace(' ', '')), 'rb') as f:
                self.league_objects[league] = pickle.load(f)

            self.league_tables[league] = LeagueTableWidget(self, controller, league)
            self.league_tables[league].grid(row=2, column=1, sticky='nsew', pady=5, padx=5)

        # the league selection bar is then added

        leaguebar = LeagueBarWidget(self, controller)
        leaguebar.grid(row=0, sticky='nsew', columnspan=2)

        # finally the date selection bar is added

        datebar = DateWidget(self, controller)
        datebar.grid(row=1, sticky='nsew', columnspan=2)

    def view_table(self, league):
        """Method that raises the corresponding league table; note that this method is called from the LeagueBarWidget object when a new league is selected"""

        self.league_tables[league].tkraise()


def main():

    app = Application()
    app.geometry('800x600')
    app.mainloop()


if __name__ == '__main__':
    main()
