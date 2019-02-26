import requests
from bs4 import BeautifulSoup
import pymysql
import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re


class Typed():
    """Descriptor class used for a type assertion decorator used to type-check specified attributes

    Parameters
    ----------
    name: str
        name of attribute
    expected_type: type object
        type associated with attribute
    mutable: boolean
        attribute if mutable if set to True and Immutable otherwise
    """

    def __init__(self, name, expected_type, mutable=True):

        self.name = name
        self.expected_type = expected_type
        self.mutable = mutable

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            return instance.__dict__[self.name]

    def __set__(self, instance, val):

        if self.name in instance.__dict__.keys():
            if not self.mutable:
                print('Warning: Attempting to change Immutable Attribute')
                return None

        if not isinstance(val, self.expected_type):
            raise TypeError('Expecting argument of type {}'.format(self.expected_type))

        instance.__dict__[self.name] = val


def typeassert(**kwargs):
    """Function that defines type assertion decorator; note that the decorator simply ensures that the attribute types are not altered in the program, and, if desired, allows the user to specify whether
    or not an attribute is mutable.

    Parameters
    ----------
    kwargs: dict
        keyword argument dictionary; note that the arguments need to take the form 'attribute_name=(attribute_type, mutable)' i.e. if one wants to assert that some attribute x has type float and is immutable, the correct argument
        to pass to the decorator would be x=(int, False)

    Returns
    -------
    wrapper: func object
        wrapper function that sets the specified attributes as clas attributes through the setattr() function

    """

    def wrapper(cls):

        for name, args in kwargs.items():
            expected_type, mutable = args
            setattr(cls, name, Typed(name=name, expected_type=expected_type, mutable=mutable))
        return cls

    return wrapper


@typeassert(date=(str, False))
class Fixture():
    """Class used to store all the information about a particular fixture; note

    Paramters
    ---------
    date: str
        date of fixture
    data: list
        list of BeautifulSoup tag items containing the data for an individual fixture

    Attributes
    ----------
    self.time_line: dict
        dictionary containing events of the match of form {'time', Event}. Note that the events are stored as Event objects

    """

    def __init__(self, date, data):

        self.date = date
        self.time_line = {}

        self.data = self.process_data(data)

        if self.home_score > self.away_score:
            self.result = 'Home Win'
        elif self.home_score < self.away_score:
            self.result = 'Away Win'
        else:
            self.result = 'Draw'

    def process_data(self, data):
        """Method used to process that data from the HTML Source

        Parameters
        ----------
        data: list
            list of BeautifulSoup tag items containing the data for an individual fixture

        """

        # first, the home team and away team's are determined, along with the home and away scores

        self.home_team = data.find(
            'span', {'class': 'sp-c-fixture__team sp-c-fixture__team--home'}).find('abbr').get_text()

        self.home_score = data.find(
            'span', {'class': "sp-c-fixture__number sp-c-fixture__number--home sp-c-fixture__number--ft"}).get_text()

        self.away_team = data.find(
            'span', {'class': 'sp-c-fixture__team sp-c-fixture__team--away'}).find('abbr').get_text()

        self.away_score = data.find(
            'span', {'class': "sp-c-fixture__number sp-c-fixture__number--away sp-c-fixture__number--ft"}).get_text()

        # the events data (i.e. goals, red cards etc) is then found

        events = data.find(
            'aside', {'class': 'sp-c-fixture__aside'}).find_all('li')

        # The events are split into seperate blocks, one for each player

        for block in events:
            player_name, *details = block.find_all('span')

            # each block consists of a series of sub events associated with each player; these are cleaned and sorted, then placed in the timeline

            event = ''

            # the event item is first turned from a list of BeautifulSoup Tag items to a single string; note that, somewhat inconveniently, one tag exists for each character

            for detail in details:
                event += detail.get_text()

            # each sub event is seperated by a comma

            for element in event.split(','):

                # note that the data from the HTML source is duplicated every time; hence, the string is first split in half and stripped of any trailing whitespace

                element = element[:len(element)//2 + 1].replace('(', '').strip()

                # if the element is not an empty string (which occasionally occur), it is transformed into an Event instance, which is stored on the timeline dictionary. Note the actual storage is done in the
                # Event class itself, since the time data needs to be extracted first

                if element:
                    element = Event(self, player_name.get_text(), element)

    def __str__(self):

        string = '{0.date}: {0.home_team} vs {0.away_team} --> {0.home_score}:{0.away_score}\n'.format(
            self)

        for time, event in sorted(self.time_line.items()):
            string += (str(event) + '\n')

        return string


@typeassert(player=(str, False), fixture=(Fixture, False))
class Event():
    """Class defining an event (goal, penalty, or red card)

    Parameters
    ----------
    fixture: Fixture object
        the fixture in which the event occured
    player: str
        name of player associated with event
    element: str
        string containing the raw information about the event (time of event and type of event)

    """

    def __init__(self, fixture, player, element):

        self.player = player
        self.fixture = fixture

        # the raw data is then processed

        self.time, self.type = self.process_element(element)

        # the event is added to the timeline

        fixture.time_line[self.time] = self

    def process_element(self, element):
        """Method to process the raw data passed down the the object

        Parameters
        ----------
        element: str
            string containing the information about the event
        """

        # first, the type of event is determined by searching the 'element' string for certain keywords. Note that the .find() function returns a -1 if the substring was not found within the parent string

        if element.find('pen') is not -1:
            self.type = 'penalty'
        elif element.find('Dismissed') is not -1:
            self.type = 'red_card'
            element = element.replace('Dismissed at ', '')
        else:
            self.type = 'goal'

        # the time then needs to be determined

        # note that events that occur in overtime are of form str(time' + overtime) and need to be taken into account

        added_time = element[element.find('+') + 1]

        self.time = int(element.split('\'')[0])

        # if the event occured in overtime, the overtime is added to the event time

        if added_time:
            self.time += int(added_time)

        return (self.time, self.type)

    def __str__(self):
        return 'Time: {0.time} Player: {0.player} Type: {0.type}'.format(self)


def get_data(date=None, interest_leagues=['PREMIER LEAGUE', 'GERMAN BUNDESLIGA', 'SPANISH LA LIGA', 'CHAMPIONS LEAGUE', 'ITALIAN SERIE A']):
    """Function used to retrieve all the data for a given day; problematically, the data on scorers can only be retreived by interacting with the JavaScript on the page. This is overcome using the Selenium
    module with the Chrome driver. Note that once Selenium has been used to Trigger the Javascript on the page, the HTML content is passed down to BeautifulSoup, which is then used to handle the rest of the data processing

    Parameters
    ----------
    date: str
        string of form 'YYYY-MM-DD' specifiying day
    interest_leagues: iterable
        indicates what leagues the data should be gathered for

    """

    interest_leagues = [league.upper() for league in interest_leagues]

    # if no date is given, then the program assumes that it should look for the data from the current dat

    if date is None:
        date = datetime.date.today()

    # the url is first defined

    url = 'https://www.bbc.co.uk/sport/football/scores-fixtures/{}'.format(date)

    # the request for the data is then made

    try:
        response = requests.get(url)

        if not response:
            print('HTTP Error: Status Code --> {}'.format(response.status_code))

    except Exception as err:
        print('Something went wrong: ', err)

    # problematically, the data on scorers can only be retreived by interacting with the JavaScript; this is done via Selenium

    driver = webdriver.Chrome(
        executable_path=r'C:\Users\Six\Downloads\chromedriver_win32\chromedriver.exe')

    driver.get(url)

    driver.find_element_by_css_selector('button.qa-show-scorers-button').click()

    try:
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'qa-match-block')))
    except Exception as err:
        print(err)

    data = BeautifulSoup(driver.page_source, 'lxml')

    driver.quit()

    leagues = data.find_all('div', {'class': 'qa-match-block'})

    # the data for each individual leauge is then found; note that each leagues has its own 'div' tag, which containts the date

    league_dict = {}

    # only the specified leagues are saved; note that the league_dict stores the tags containing each individual league. Note also that the title of the league is automatically capitalized so to avoid error
    # due to lowercase/uppercase mixups

    for league in leagues:
        league_name = league.find('h3').get_text()

        if league_name.upper() in interest_leagues:
            league_dict[league_name] = league

    return date, league_dict


def process_data(date, league, data, parsed_data):
    """Function that processed the data from a particular league and converts it to a dictionary of Fixture objects. Note that the Fixture objects itself sorts through the data, not the function.

    Parameters
    ----------
    date: str
        string of form 'YYYY-MM-DD' giving date
    league: str
        name of league
    data: BeautifulSoup tag object
        tag object containing all fixtures for that particular day
    parsed_data: dict
        dictionary to which the cleaned data is added to. This is then also returned by the function and is then passed down to the function again with the next league

    Attributes
    ----------
    processed_data: dict
        dictionary containing the Fixture objects

    Returns
    -------
    parsed_data: dict
        dictionary containing dictionary of Fixture objects, one for each league

    """

    # individual fixtures are stored in an unordered list, and each list item corresponds to one fixture

    fixtures = data.find_all('article', {'class': 'sp-c-fixture'})

    processed_data = {}

    # all the individual fixture/list items are converted into Fixture Objects; note that the fixture object takes the BeautifulSoup tag as an input and then processes the data

    processed_data = {i: Fixture(date, fixture)
                      for i, fixture in zip(range(len(fixtures)), fixtures)}

    # the data for each league is then added to the parsed data dictionary

    parsed_data[league] = processed_data

    return parsed_data


if __name__ == '__main__':

    date, raw_data = get_data(date='2019-02-23')

    parsed_data = {}

    for league in raw_data.keys():

        parsed_data = process_data(date, league, raw_data[league], parsed_data)

    for fixture in parsed_data['Premier League'].values():
        print(fixture)
