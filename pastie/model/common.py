"""Common tables and classes for use by Pastie"""
from metadata import Column, mapper, metadata, types, Session, Table

tag_table = Table('tags', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('name', types.String(30), nullable=False),
)

class Tag(object):
    def __init__(self, name):
        """Create a new Tag object with ``name``"""
        self.name = name

mapper(Tag, tag_table)
