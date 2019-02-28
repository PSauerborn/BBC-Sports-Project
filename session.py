import numpy as np
import pymysql
import datetime


class Session():
    """Session object that handles the flow of data in and out of the database. Note that the actual interaction with the database is delegated via a DBInteraction() object, and hence the Session acts as a sort of Proxy. This will later allow tight control over what attributes and methods are public and which are private, as opposed to simple inheritance

    Attributes
    ----------
    self.conduit: DBInteraction() Object
        object that handles all contact with the SQL server

    """

    def __init__(self):

        self.login_time = datetime.datetime.now()
        self.conduit = DBInteraction(self, self.login_time)

    def __getattr__(self, attr):
        """Method that delegates any unknown methods/attributes to the DBInteraction Object

        Parameters
        ----------
        attr: string
            attribute/method being accessed

        """

        return getattr(self.conduit, attr)

    def __setattr__(self, attr, val):
        """Any attributes that start with an underscore are set to the DBInteraction Conduit Object; all other attributes are set to the Session object. Note that his is doen via the super() method, which overrides the defined __setattr__ method and access the original __setattr__ method. Otherswise, one enters an infinite recursion regime
        """

        if attr.startswith('_'):
            setattr(self.conduit, attr, val)
        else:
            super().__setattr__(attr, val)

    def __enter__(self):
        """Method used to initiate the Connection to the MySQL database"""

        # the connection to the server is first made

        try:
            self.db = pymysql.connect(host='localhost', user='root',
                                      password='Shadowguy!89', db='football_project')

            self.cursor = self.db.cursor()

        except Exception as err:
            print(err)

        print('Session Created Succesfully')

        # all the current tables are then retrieved

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

            del(self.conduit)

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

        if league_name not in self.tables:
            print('Adding League')
            self.add_league(league_name)

        print('Updating Data for {}'.format(league))
        print('-' * 50, end='\n')

        for fixture in data:

            # the fixture is then added to the database

            result = self.add_fixture(league_name, fixture)

            # the league tables and the individual team tables are then updated

            for team in (fixture.home_team, fixture.away_team):

                print(team)

                self.update_team(league_name, team.replace(' ', ''), fixture)


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

        query1 = """
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

        """.format(league)

        query2 = """
        CREATE TABLE IF NOT EXISTS {} (

        Team VARCHAR(50) NOT NULL PRIMARY KEY,
        Played INT NOT NULL,
        GF INT NOT NULL,
        GA INT NOT NULL,
        GD INT NOT NULL,
        Won INT NOT NULL,
        Lost INT NOT NULL,
        Draw INT NOT NULL,
        Pts INT NOT NULL
        )
        """.format(league)

        try:
            self.sess.cursor.execute(query1)
            self.sess.cursor.execute(query2)
            self.sess.db.commit()

        except Exception as err:
            print(err)

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

        except Exception as err:
            print(err)

    def update_team(self, league, team, fixture):
        """Method that updates the league table"""

        home, scored, conceded = True, 0, 0

        def map_results():
            """Function that defines a list of results; note that the table is of form (team, games_played, GF, GA, GD, Won, Lost, Draw, Pts). A list of add-on values is defined based on the
            fixture results. One can then simply do an operation like current_state = old_state + new_state to update the league table
            """

            nonlocal home, scored, conceded

            if team == fixture.home_team:
                home, scored, conceded = True, int(fixture.home_score), int(fixture.away_score)
            else:
                home, scored, conceded = False, int(fixture.away_score), int(fixture.home_score)

            # note; True evaluates to 1 while False evaluates to 0

            results = [1, scored, conceded, (scored - conceded), scored
                       > conceded, conceded > scored, scored == conceded]

            # the number of points earned in the game is then appened to the list

            if scored > conceded:
                results.append(3)
            elif conceded > scored:
                results.append(0)
            else:
                results.append(1)

            return results

        # if the team has no table, the team is added to the league table and a an individual team table is also created

        if team.lower() not in self.sess.tables:

            query1 = """

            INSERT INTO {0} (Team, Played, GF, GA, GD, Won, Lost, Draw, Pts) VALUES('{1}', '0', '0', '0', '0', '0', '0', '0', '0')
            """.format(league, team)

            query2 = """
            CREATE TABLE IF NOT EXISTS {} (

            Date CHAR(10) NOT NULL PRIMARY KEY,
            Team VARCHAR(50) NOT NULL,
            Scored INT NOT NULL,
            Conceded INT NOT NULL

            )
            """.format(team)

            self.sess.cursor.execute(query1)
            self.sess.cursor.execute(query2)
            self.sess.db.commit()

        # first, the current state of the team is retrieved

        self.sess.cursor.execute('SELECT * FROM {0} WHERE {0}.Team = "{1}"'.format(league, team))
        name, *args = self.sess.cursor.fetchall()[0]

        # the state is then updated

        new_state = [i + j for i, j in zip(args, map_results())]

        # the league table is then updated with the new state

        query1 = """

        UPDATE {} SET Played = '{}', GF = '{}', GA = '{}', GD = '{}', Won = '{}', Lost = '{}', Draw = '{}', Pts = '{}' where {}.Team = '{}'
        """.format(league, *new_state, league, team)

        # the individual team table is then updated

        def opposition(x): return fixture.away_team if x else fixture.home_team

        query2 = """
        INSERT INTO {0} (Date, Team, Scored, Conceded) VALUES ('{1}', '{2}', '{3}', '{4}')

        """.format(team, fixture.date, opposition(home), scored, conceded)

        self.sess.cursor.execute(query1)

        try:
            self.sess.cursor.execute(query2)
        except pymysql.err.IntegrityError:
            print('Ignoring Duplicate')

        self.sess.db.commit()

    def update_player(self):
        pass
