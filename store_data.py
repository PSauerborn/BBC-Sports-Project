import numpy as np
import pymysql
import datetime


class Session():

    def __init__(self):

        self.login_time = datetime.datetime.now()

    def __enter__(self):
        """Method used to initiate the Connection to the MySQL database"""

        try:
            self.db = pymysql.connect(host='localhost', user='root',
                                      password='Shadowguy!89', db='football_project')

            self.cursor = self.db.cursor()

        except Exception as err:
            print(err)

        print('Session Created Succesfully')

        return self

    def __exit__(self, exc_type, exc_val, tb):
        """Method used to close the connection properly"""

        try:
            self.cursor.close()
            self.db.close()

        except Exception as err:
            print(err)

        print('Connection Closed Succesfully')

    def update_database(self, league, data):
        """Method that updates the data in the database

        Parameter
        ---------
        league: str
            name of league
        data: dict
            dictionary of Fixture Objects

        """

        league_name = league.replace(' ', '')

        query = """
        CREATE TABLE IF NOT EXISTS {}Fixtures (

        Date CHAR(10) NOT NULL,
        Time CHAR(5),
        HomeTeam VARCHAR(50) NOT NULL,
        AwayTeam VARCHAR(50) NOT NULL,
        HomeScore INT NOT NULL,
        AwayScore INT NOT NULL,
        Result VARCHAR(10) NOT NULL,
        CONSTRAINT teams PRIMARY KEY (HomeTeam, AwayTeam)

        )

        """.format(league_name)

        self.cursor.execute(query)
        self.db.commit()

        print('Updating Data for {}'.format(league))
        print('-'*50, end='\n')

        for fixture in data:

            try:
                query = """
                INSERT INTO {0}Fixtures (Date, HomeTeam, AwayTeam, HomeScore, AwayScore, Result) VALUES('{1.date}', '{1.home_team}', '{1.away_team}', '{1.home_score}', '{1.away_score}', '{1.result}');
                """.format(league_name, fixture)

                self.cursor.execute(query)
                self.db.commit()

            except Exception as err:
                print(err)
