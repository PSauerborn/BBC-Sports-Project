import numpy as np
import pymysql
import datetime
from admin.session import SessionAbstract


class SQLError(Exception):
    pass


class Connection():

    def __init__(self, name, sess):

        self.name = name
        self.sess = sess

        self.db = pymysql.connect(host='localhost', user='root', password='Shadowguy!89', db=name)

        self.cursor = self.db.cursor()

    def close(self):

        self.cursor.close()
        self.db.close()


class Session(SessionAbstract):
    """Session object that handles the flow of data in and out of the database. Note that the actual interaction with the database is delegated via a DBInteraction() object, and hence the Session acts as a sort of Proxy. This will later allow tight control over what attributes and methods are public and which are private, as opposed to simple inheritance

    Attributes
    ----------
    self.conduit: DBInteraction() Object
        object that handles all contact with the SQL server

    """

    _connections = []

    def __init__(self):

        self.login_time = datetime.datetime.now()
        self.conduit = DBInteraction(self, self.login_time)

    def update_database(self, league, data):
        """Method that updates the data in the database

        Parameter
        ---------
        league: str
            name of league
        data: dict
            dictionary of Fixture Objects

        """

        league_name = league.replace(' ', '').lower()

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

                self.update_team(league_name, team.replace(' ', '').lower(), fixture)

            for time, event in fixture.time_line.items():

                team = fixture.home_team if event.home else fixture.away_team

                self.update_player(league_name, team.replace(' ', ''), event)


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
        """Method used to add a new league to the database. Note that 3 new tables are created; one for the fixtures in the league, one for the league table itself and one for the
        individual teams in the league

        Parameters
        ----------
        league: str
            name of league

        """

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

        query3 = """
        CREATE TABLE IF NOT EXISTS {}Players (

        Name VARCHAR(50) NOT NULL PRIMARY KEY,
        Team VARCHAR(50) NOT NULL,
        Goals INT NOT NULL,
        Penalties INT NOT NULL,
        RedCards INT NOT NULL

        )
        """.format(league)

        # the tables are then added to the database

        try:
            self.sess.cursor.execute(query1)
            self.sess.cursor.execute(query2)
            self.sess.cursor.execute(query3)
            self.sess.db.commit()

        except Exception as err:
            print(err)

    def add_fixture(self, league, fixture):
        """Method used to add a fixture to the current database



        """

        query = """
        INSERT INTO {0}Fixtures (Date, HomeTeam, AwayTeam, HomeScore, AwayScore, Result) VALUES('{1.date}', '{1.home_team}', '{1.away_team}', '{1.home_score}', '{1.away_score}', '{1.result}');
        """.format(league, fixture)

        try:
            self.sess.cursor.execute(query)

        except Exception as err:
            print(err)

    def update_team(self, league, team, fixture):
        """Method that updates the data for a team after a fixture has been played. Note that this consists of updating the overall league table and the teams individual team table. In order
        to keep the database as consistent as possible, all team names are converted to lowercase and all spaces are removed so that the tables names are valid

        Parameters
        ----------
        league: str
            league name
        team: str
            team name
        fixture Fixture Object
            fixture object containing details of the fixture

        """

        home, scored, conceded = True, 0, 0

        def map_results():
            """Function that defines a list of results; note that the league table where the data is stored is of form (team, games_played, GF, GA, GD, Won, Lost, Draw, Pts). A list of add-on values is defined based on the fixture results. One can then simply do an operation like current_stats = old_stats + fixture_stats to update the league table

            """

            nonlocal home, scored, conceded

            if team == fixture.home_team.replace(' ', '').lower():
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

        UPDATE {} SET Played = '{}', GF = '{}', GA = '{}', GD = '{}', Won = '{}', Lost = '{}', Draw = '{}', Pts = '{}' WHERE {}.Team = '{}'
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

    def update_player(self, league, team, event):
        """Method used to update the statistics of a player

        Parameters
        ----------
        league: str
            league name
        team: str
            team name
        event: Event object
            event object containing details of the event

        """

        name = event.player.replace('\'', '')

        # the players current stats are retrieved from the database; note that if the palyer has no entry, an enrty is created

        try:
            self.sess.cursor.execute(
                'SELECT * FROM {0}Players WHERE {0}Players.name = "{1}"'.format(league, name))
            *args, goals, pens, reds = self.sess.cursor.fetchall()[0]

        except:
            print('Adding Player', name, team)
            query = """

            INSERT INTO {}Players (Name, Team, Goals, Penalties, RedCards) VALUES ('{}', '{}', '0', '0', '0')
            """.format(league, name, team)

            self.sess.cursor.execute(query)
            self.sess.db.commit()

            return self.update_player(league, team, event)

        # the type of event is then determined

        if event.type == 'goal':
            goals += 1
        elif event.type == 'penalty':
            pens += 1
        else:
            reds += 1

        # the players statstics are updated

        query = """
        UPDATE {}Players SET Goals = '{}', Penalties = '{}', RedCards = '{}'
        """.format(league, goals, pens, reds)

        self.sess.db.commit()

    def clear_system(self):
        """Method Used to clear the Database of all Data"""

        self.sess.cursor.execute('SHOW TABLES')
        tables = self.sess.cursor.fetchall()

        for table in tables:
            self.sess.cursor.execute('DROP TABLE {};'.format(table[0]))

        self.sess.db.commit()

        print('System Cleared')

    def hello(self):
        print('Hello World')
        self.pie = 'cherry'


if __name__ == '__main__':

    with Session() as sess:

        print('Working')
