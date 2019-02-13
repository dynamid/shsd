from sqlalchemy import *
from sqlalchemy.sql import *
from sqlalchemy.orm import scoped_session, sessionmaker


metadata = MetaData()

devices = Table('devices', metadata,
                Column('did', Integer, autoincrement=True, primary_key=True),
                Column('ip', String),
                Column('hw', String, unique=True),
                Column('manuf', String),
                Column('label', String),
                Column('firstseen', Date),
                Column('lastseen', Date))

services = Table('services', metadata,
                 Column('sid', Integer, autoincrement=True, primary_key=True),
                 Column('sname', String, unique=True))

accounts = Table('accounts', metadata,
                 Column('aid', Integer, autoincrement=True, primary_key=True),
                 Column('login', String),
                 Column('sid', Integer),
                 Column('ip', Integer),
                 Column('ip_org', String),
                 Column('ip_country', String),
                 Column('ip_countrycode', String),
                 Column('ip_city', String),
                 Column('firstseen', Date),
                 Column('lastseen', Date),
                 Column('ip_longitude', Float),
                 Column('ip_latitude', Float),
                 Column('ip_as', String),
                 Column('is_populated', Boolean, default=False))

ascolors = Table('ascolors', metadata,
                 Column('id_color', Integer, primary_key=True),
                 Column('uid', String, primary_key=True),
                 Column('ip_as', String))


# engine = create_engine('sqlite:///database.db', echo=False)
# metadata.create_all(engine)
# session_factory = sessionmaker(bind=engine)
global Session
Session = None  # scoped_session(session_factory)
