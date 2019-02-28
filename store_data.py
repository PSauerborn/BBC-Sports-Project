import numpy as np
import pymysql
import datetime


class DBInteraction():
    """ Object that handles all the queries made to the SQL server by the Session object. Note that these are delegated via the __getattr__ method directly from the Session object

    Parameters
    ----------
    sess: Session Object
        Session Object using accessing the Database
    timestamp: datetime object
        datetime object indicating when the Session was created
    """

    def __init__(self, sess, timestamp):

        self.sess = sess
        self.timestamp = timestamp

    def add_league(self, league):

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

        self.sess.cursor.execute(query)
        self.sess.db.commit()


    def add_fixture(self, league, fixture):
        """Method used to add a fixture to the current database

        Returns
        -------
        success: boolean or Exception
            returns True if operation was successful, returns an Exception otherwise
        """

        query = """
        INSERT INTO {0}Fixtures (Date, HomeTeam, AwayTeam, HomeScore, AwayScore, Result) VALUES('{1.date}', '{1.home_team}', '{1.away_team}', '{1.home_score}', '{1.away_score}', '{1.result}');
        """.format(league, fixture)

        try:
            self.sess.cursor.execute(query)
            success = True

        except Exception as err:
            success = err

        return success

    def add_team(self):
        pass

    def update_team(self):
        pass

    def add_player(self):
        pass

    def update_player(self):
        pass



class Session():
    """Session objec that handles the flow of data in and out of the database. Note that the actual interaction with the database is delegated via a DBInteraction() object, and hence the Session acts as a sort of
    Proxy. This allows for
    """

    def __init__(self):

        self.login_time = datetime.datetime.now()
        self._conduit = DBInteraction(self, self.login_time)

    def __getattr__(self, attr):
        """Method that delegates any unknonw methods/attributes to the DBInteraction Object

        Parameters
        ----------
        attr: object
            attribute/method being accessed

        """

        return getattr(self,_conduit, attr)

    def __setattr__(self, attr, val):
        """Any attributes that start with an underscore are set to the DBInteraction Conduit Object; all other attributes are set to the Session object. Note that his is doen via the super() method, which overrides
        the defined __setattr__ method and access the original __setattr__ method. Otherswise, one enters an infinite recursion regime
        """

        if attr.startswith('_'):
            setattr(self._conduit, attr, val)
        else:
            super().__setattr__(attr, val)


    def __enter__(self):
        """Method used to initiate the Connection to the MySQL database"""

        try:
            self.db = pymysql.connect(host='localhost', user='root',
                                      password='Shadowguy!89', db='football_project')

            self.cursor = self.db.cursor()

        except Exception as err:
            print(err)

        print('Session Created Succesfully')

        try:
            self.cursor.execute('SHOW TABLES;')
            self.tables = [i[0] for i in self.cursor.fetchall()]

        except Exception as err:
            print(err)

        return self

    def __exit__(self, exc_type, exc_val, tb):
        """Method used to close the connection properly"""

        try:
            self.db.commit()

            del(self._conduit)

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


        print('Updating Data for {}'.format(league))
        print('-'*50, end='\n')

        for fixture in data:

            # the fixture is then added to the database

            self.add_fixture(league_name, fixture)
