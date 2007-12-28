"""Pastebin tables and classes"""
from datetime import datetime
import math

from sqlalchemy import desc, Column, ForeignKey, func, select, Table, types
from sqlalchemy.orm import backref, mapper, relation

from pastie.model.metadata import metadata, Session
from pastie.model.common import tag_table, Tag

mapper = Session.mapper

paste_table = Table('pastes', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('author', types.Unicode(50)),
    Column('title', types.Unicode(60)),
    Column('date', types.DateTime, nullable=False),
    Column('language', types.String(30), nullable=False),
    Column('code', types.Unicode, nullable=False),
    Column('parent_id', types.Integer, ForeignKey('pastes.id'), nullable=True)
)

pastetags_table = Table('paste_tags', metadata,
    Column('tag_id', types.Integer,
           ForeignKey('tags.id', ondelete='RESTRICT'), primary_key=True),
    Column('paste_id', types.Integer,
           ForeignKey('pastes.id', ondelete='CASCADE'), primary_key=True),
)

class Paste(object):
    def __init__(self, author=None, title='', language=None,
                 code='', tags='', parent_id=None):
        if not author:
            author = 'anonymous'
        self.author = author
        self.title = title
        self.language = language
        self.code = code
        self.date = datetime.now()
        self.parent_id = parent_id
        if tags:
            taglist = tags.replace(',',' ').strip().split(' ')
            for newtag in taglist:
                newtag = str(newtag.strip().encode('ascii', 'ignore'))
                if not newtag:
                    continue
                ltag = Session.query(Tag).filter_by(name=newtag).first()
                if not ltag:
                    ltag = Tag(newtag)
                    Session.save(ltag)
                self.tags.append(ltag)

    @classmethod
    def recent(cls, count=5):
        return Session.query(cls).order_by([desc(cls.c.date)]).limit(count).all()

    @classmethod
    def tag_sizes(cls):
        """This method returns all the tags and their relative size
        for a tagcloud"""
        results = Session.execute(
            select([tag_table.c.name, func.count(tag_table.c.name)],
                   from_obj=[tag_table.join(pastetags_table).join(paste_table)],
                   group_by=[tag_table.c.name])
        )
        tag_counts = results.fetchall()
        total = sum([tag[1] for tag in tag_counts])
        totalcounts = []
        for tag in tag_counts:
            weight = (math.log(tag[1] or 1) * 4) + 10
            totalcounts.append((tag[0], tag[1],weight))
        return sorted(totalcounts, cmp=lambda x,y: cmp(x[0], y[0]))

mapper(Paste, paste_table,
    properties=dict(
        tags=relation(Tag, secondary=pastetags_table, lazy=False,
                      backref=backref('pastes',
                                      order_by=desc(paste_table.c.date))),
        children=relation(Paste,
                          primaryjoin=paste_table.c.parent_id==paste_table.c.id,
                          cascade='all',
                          backref=backref('parent',
                                          remote_side=[paste_table.c.id]))
    ),
    order_by=[desc(paste_table.c.date)]
)

