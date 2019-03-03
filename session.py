
import pymysql


class SessionAbstract():
    """Session object that handles the flow of data in and out of the database. Note that the actual interaction with the database is delegated via a DBInteraction() object, and hence the Session acts as a sort of Proxy. This will later allow tight control over what attributes and methods are public and which are private, as opposed to simple inheritance

    Attributes
    ----------
    self.conduit: DBInteraction() Object
        object that handles all contact with the SQL server

    """

    def __getattr__(self, attr):
        """Method that delegates any unknown methods/attributes to the DBInteraction Object

        Parameters
        ----------
        attr: string
            attribute/method being accessed

        """

        return getattr(self.conduit, attr)

    def __setattr__(self, attr, val):
        """Any attributes that start with an underscore are set to the DBInteraction Conduit Object; all other attributes are set to the Session object. Note that this is done via the super() method, which overrides the defined __setattr__ method and access the original __setattr__ method. Otherwise, one enters an infinite recursion regime
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
            raise SQLError(err)

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
