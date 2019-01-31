import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup


def get_data(date='2019-01-30'):
    """Function that retrieves the data for the desired day

    Parameters
    ----------
    date: string of form 'yyyy-mm-dd'
        date of interest

    Returns
    -------
    data: dict
        dict containing data for leagues of interest in HTML format in form {league_name: data} i.e. league names form the keys. The data is in the form of bs4 tag elements and is present in a HTML <list> tag

    """

    # a list of leagues of interest is first defined; only data from those leauges are stored and kept track of

    interest_leagues = ['Premier League']

    # the data is first requested from the site

    try:
        response = requests.get(
            'https://www.bbc.co.uk/sport/football/scores-fixtures/{}'.format(date))

        if not response:
            print('HTTP Error: Status Code --> {}'.format(response.status_code))

        else:
            print('Request Successful')

    except Exception as err:
        print('Something Went Wrong:', err)

    # the beautiful soup object is then defined

    bbc_football = BeautifulSoup(response.content, 'lxml')

    # all the seperate leagues are pulled

    data = bbc_football.find_all('div', {'class': 'qa-match-block'})

    league_data = {}

    # the leagues of interest are then picked out

    for league in data:

        league_name = league.find('h3').get_text()

        fixtures = league.find('ul')

        # if the league is in the list of interested leagues, the fixtures are added to the dictionary containing the data with the league name as the key

        if league_name in interest_leagues:

            league_data[league_name] = fixtures

    # print(league_data)

    return league_data, date


def parse_data(data, date):
    """Function used to parse the data

    Parameters
    ----------
    data: dict
        dict containing the league data for the given date. Note that the data is given in the form of bs4 tag elements
    date: string of form 'yyyy-mm-dd'
        string containing date of interest

    Attributes
    ----------
    fixture_list: list object
        list containing a series of Fixture objects for each league
    results: dict
        dictionary containing the results for each league, with the league names as keys. Note that the values within each league entry is a list of Fixture Items

    Returns
    -------
    results: dict
        dictionary containing the results for each league, with the league names as keys. Note that the values within each league entry is a list of Fixture Items

    """

    results = {}

    from pyprind import ProgBar


    for league_name in data.keys():

        fixture_list = []

        # the fixtures are stored in list tags, and each individual game has its own page. The link to this page is extracted

        fixtures = data[league_name].find_all('li')

        bar = ProgBar(len(fixtures), title='Gathering data for {}'.format(league_name))

        # the links for each individual fixture are extracted. Note that each list item refers to a seperate fixture in any given league. A request is then made for the data from that particular league fixture, from which the bulk
        # of the information is retrieved

        for li in fixtures:

            link = 'https://www.bbc.co.uk/' + li.find('a').get('href')

            try:
                response = requests.get(link)

                if not response:
                    print('HTTP Error: Status Code --> {}'.format(response.status_code))
                else:
                    bar.update()

            except Exception as err:
                print('Something went Wrong: ', err)

            # a beautiful soup object is then generated that contains the data for fixture in question

            fixture_data = BeautifulSoup(response.content, 'lxml')

            # the data for the home team is retrieved

            home_team = fixture_data.find('span', {
                                          'class': "fixture__team-name fixture__team-name--home"}).find('abbr').get('title')

            home_score = fixture_data.find('span', {
                                           'class': "fixture__number fixture__number--home fixture__number--ft"}).get_text()

            # followed by the data for the away team

            away_team = fixture_data.find('span', {
                                          'class': "fixture__team-name fixture__team-name--away"}).find('abbr').get('title')

            away_score = fixture_data.find('span', {
                                           'class': "fixture__number fixture__number--away fixture__number--ft"}).get_text()

            # the scorers of the home goals are then identified, as well as the time the goal was scored

            home_scorers = fixture_data.find(
                'ul', {'class': "fixture__scorers fixture__scorers-home gel-brevier"}).find_all('li')

            goals_home, goals_away = [], []

            for scorer in home_scorers:

                data = scorer.find_all('span')

                name = data[0].get_text()

                time = ''

                for element in data:

                    element = element.get_text()

                    if element != name:

                        time += element

                # note that the time returns a duplicate for some reason; hence, the second half of the string can be ignored

                time = time[2:len(time) // 2].split()


                goals_home.append((name, time))

            # the same is then done for the away team

            away_scorers = fixture_data.find(
                'ul', {'class': "fixture__scorers fixture__scorers-away gel-brevier"}).find_all('li')

            for scorer in away_scorers:

                data = scorer.find_all('span')

                name = data[0].get_text()

                time = ''

                for element in data:

                    element = element.get_text()

                    if element != name:
                        time += element

                time = time[2:len(time) // 2]

                goals_away.append((name, time))

            fixture = Fixture(date=date, home_team=home_team, away_team=away_team, home_score=home_score,
                              away_score=away_score, home_goals=goals_home, away_goals=goals_away)

            fixture_list.append(fixture)

        results[league_name] = fixture_list

        return results




class Goal():

    def __init__(self, scorer, time, pen=False):

        self.scorer = scorer
        self.time = time
        self.pen = pen

    def __repr__(self):
        return 'Scorer: {} Time: {} Penalty: {}'.format(self.scorer, self.time, self.pen)


class Fixture():

    def __init__(self, date, home_team, away_team, home_score, away_score, home_goals, away_goals):

        self.date = date
        self.home_team = home_team
        self.away_team = away_team
        self.home_score = home_score
        self.away_score = away_score
        self.home_goals = home_goals
        self.away_goals = away_goals

    def __repr__(self):
        return '{} vs {} --> {}:{}'.format(self.home_team, self.away_team, self.home_score, self.away_score)

    def show_scorers(self):

        for scorer, time in self.home_goals:
            print('naught')


data, date = get_data(date='2019-01-30')

results = parse_data(data, date)


try:
    for fixture in results['Premier League']:
            print(fixture)

except TypeError:
    print('No Fixtures for Selected Leagues')
