from data import gather_data
from data.store_data import Session
from multiprocessing import Process

# the raw data is first obtained from the BBC site

date, raw_data = gather_data.get_data(
    date='2019-02-23', interest_leagues=['Premier League', 'Champions League', 'German Bundesliga', 'Spanish La Liga', 'Italian Serie A'])

processed_data = {}

# the data is then processed; note that the function is recursive and, when done, returns a nested dictionary. Each league has its own dictionary (with the league name as key) and the nested dicionary for each league consists
# of a series of fixture objects

for league in raw_data.keys():

    processed_data = gather_data.process_data(date, league, raw_data[league], processed_data)


# a session object is then instantiated and the database is updated

with Session() as sess:

    for league, data in processed_data.items():

        sess.update_database(league, data.values())
