import tkinter as tk
from tkinter import ttk
import sys
import datetime

LARGE_FONT = ('Comic Sans MS', 20)
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

        super().__init__(parent, relief=tk.RAISED, borderwidth=3)

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
                date = self.convert_date(date)
                self.buttons.append(ttk.Button(
                    self, text='{}\n{} {}'.format(date[0],date[1],date[2]), style='my.TButton'))
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

        months_reversed = {month:num for num, month in self.months.items()}

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

        super().__init__(parent)

        # a style is first defined for the buttons

        style = ttk.Style()
        style.configure('my.TButton', font=('Verdana', 10, 'bold'))

        leagues = ['Premier League', 'German Bundesliga', 'Spanish La Liga', 'Italian Serie A', 'Champions League']

        buttons = {}

        self.grid_rowconfigure(0, weight=1)

        for i, league in enumerate(leagues):
            self.grid_columnconfigure(i, weight=1)

            buttons['league'] = ttk.Button(self, text=league, style='my.TButton')
            buttons['league'].grid(column=i, row=0, sticky='nsew')



class MainPage(tk.Frame):
    """Class defining the main page, which itself consists of 4 seperately defined widgets"""

    def __init__(self, parent, controller):

        super().__init__(parent)

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # the main page window is split into three rows; the first row is for the LeagueBar widget, which allows the user to select a league, the second row is the the DateWidget which allows the user to cyle through days and the final row (which
        # receives the majority of the frame space) is used for the actual data

        self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=30)

        # the LeagueBarWIdget and DateWidgets are then placed into the frame

        leaguebar = LeagueBarWidget(self, controller)
        leaguebar.grid(row=0, sticky='nsew', columnspan=2)

        datebar = DateWidget(self, controller)
        datebar.grid(row=1, sticky='nsew', columnspan=2)

        # a league fixture widget that displays the league fixtures is then added

        fixtures = LeagueFixtureWidget(self, controller)
        fixtures.grid(row=2, column=0, sticky='nsew', pady=5, padx=5)

        # and a league table widget that

        table = LeagueTableWidget(self, controller)
        table.grid(row=2, column=1, sticky='nsew', pady=5, padx=5)


class LeagueFixtureWidget(tk.Frame):

    def __init__(self, parent, controller):

        super().__init__(parent, relief=tk.RAISED, borderwidth=1)



class LeagueTableWidget(tk.Frame):

    def __init__(self, parent, controller):

        super().__init__(parent, relief=tk.RAISED, borderwidth=1)




def main():

    app = Application()
    app.geometry('800x600')
    app.mainloop()


if __name__ == '__main__':
    main()
