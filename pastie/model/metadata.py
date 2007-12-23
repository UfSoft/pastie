import pylons
from sqlalchemy import Column, ForeignKey, MetaData, Table, types
from sqlalchemy.orm import relation, scoped_session, sessionmaker , mapper

# Global session manager.  Session() returns the session object appropriate for the current web request.
Session = scoped_session(sessionmaker(autoflush=True, transactional=True, bind=pylons.config['pylons.g'].sa_engine))


# Global metadata. If you have multiple databases with overlapping table names, you'll need a metadata for each
# database.
metadata = MetaData()
