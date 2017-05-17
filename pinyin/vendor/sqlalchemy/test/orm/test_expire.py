"""Attribute/instance expiration, deferral of attributes, etc."""

from sqlalchemy.test.testing import eq_, assert_raises, assert_raises_message
from sqlalchemy.test.util import gc_collect
import sqlalchemy as sa
from sqlalchemy.test import testing
from sqlalchemy import Integer, String, ForeignKey, exc as sa_exc
from sqlalchemy.test.schema import Table
from sqlalchemy.test.schema import Column
from sqlalchemy.orm import mapper, relationship, create_session, \
                        attributes, deferred, exc as orm_exc, defer, undefer,\
                        strategies, state, lazyload, backref, Session
from test.orm import _base, _fixtures


class ExpireTest(_fixtures.FixtureTest):

    @testing.resolve_artifact_names
    def test_expire(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user'),
            })
        mapper(Address, addresses)

        sess = create_session()
        u = sess.query(User).get(7)
        assert len(u.addresses) == 1
        u.name = 'foo'
        del u.addresses[0]
        sess.expire(u)

        assert 'name' not in u.__dict__

        def go():
            assert u.name == 'jack'
        self.assert_sql_count(testing.db, go, 1)
        assert 'name' in u.__dict__

        u.name = 'foo'
        sess.flush()
        # change the value in the DB
        users.update(users.c.id==7, values=dict(name='jack')).execute()
        sess.expire(u)
        # object isnt refreshed yet, using dict to bypass trigger
        assert u.__dict__.get('name') != 'jack'
        assert 'name' in attributes.instance_state(u).expired_attributes

        sess.query(User).all()
        # test that it refreshed
        assert u.__dict__['name'] == 'jack'
        assert 'name' not in attributes.instance_state(u).expired_attributes

        def go():
            assert u.name == 'jack'
        self.assert_sql_count(testing.db, go, 0)

    @testing.resolve_artifact_names
    def test_persistence_check(self):
        mapper(User, users)
        s = create_session()
        u = s.query(User).get(7)
        s.expunge_all()

        assert_raises_message(sa_exc.InvalidRequestError, 
                        r"is not persistent within this Session", s.expire, u)

    @testing.resolve_artifact_names
    def test_get_refreshes(self):
        mapper(User, users)
        s = create_session(autocommit=False)
        u = s.query(User).get(10)
        s.expire_all()

        def go():
            u = s.query(User).get(10)  # get() refreshes
        self.assert_sql_count(testing.db, go, 1)
        def go():
            eq_(u.name, 'chuck')  # attributes unexpired
        self.assert_sql_count(testing.db, go, 0)
        def go():
            u = s.query(User).get(10)  # expire flag reset, so not expired
        self.assert_sql_count(testing.db, go, 0)

        s.expire_all()
        s.execute(users.delete().where(User.id==10))

        # object is gone, get() returns None, removes u from session
        assert u in s
        assert s.query(User).get(10) is None
        assert u not in s # and expunges

        # trick the "deleted" flag so we can re-add for the sake
        # of this test
        del attributes.instance_state(u).deleted

        # add it back
        s.add(u)
        # nope, raises ObjectDeletedError
        assert_raises(sa.orm.exc.ObjectDeletedError, getattr, u, 'name')

        # do a get()/remove u from session again
        assert s.query(User).get(10) is None
        assert u not in s

        s.rollback()

        assert u in s
        # but now its back, rollback has occurred, the _remove_newly_deleted
        # is reverted
        eq_(u.name, 'chuck')

    @testing.resolve_artifact_names
    def test_deferred(self):
        """test that unloaded, deferred attributes aren't included in the expiry list."""

        mapper(Order, orders, properties={'description':deferred(orders.c.description)})

        s = create_session()
        o1 = s.query(Order).first()
        assert 'description' not in o1.__dict__
        s.expire(o1)
        assert o1.isopen is not None
        assert 'description' not in o1.__dict__
        assert o1.description

    @testing.resolve_artifact_names
    def test_lazyload_autoflushes(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, order_by=addresses.c.email_address)
        })
        mapper(Address, addresses)
        s = create_session(autoflush=True, autocommit=False)
        u = s.query(User).get(8)
        adlist = u.addresses
        eq_(adlist, [
            Address(email_address='ed@bettyboop.com'), 
            Address(email_address='ed@lala.com'),
            Address(email_address='ed@wood.com'), 
        ])
        a1 = u.addresses[2]
        a1.email_address = 'aaaaa'
        s.expire(u, ['addresses'])
        eq_(u.addresses, [
            Address(email_address='aaaaa'), 
            Address(email_address='ed@bettyboop.com'), 
            Address(email_address='ed@lala.com'),
        ])

    @testing.resolve_artifact_names
    def test_refresh_collection_exception(self):
        """test graceful failure for currently unsupported 
        immediate refresh of a collection"""

        mapper(User, users, properties={
            'addresses':relationship(Address, order_by=addresses.c.email_address)
        })
        mapper(Address, addresses)
        s = create_session(autoflush=True, autocommit=False)
        u = s.query(User).get(8)
        assert_raises_message(sa_exc.InvalidRequestError, 
                        "properties specified for refresh", 
                        s.refresh, u, ['addresses'])

        # in contrast to a regular query with no columns
        assert_raises_message(sa_exc.InvalidRequestError, 
                        "no columns with which to SELECT", s.query().all)

    @testing.resolve_artifact_names
    def test_refresh_cancels_expire(self):
        mapper(User, users)
        s = create_session()
        u = s.query(User).get(7)
        s.expire(u)
        s.refresh(u)

        def go():
            u = s.query(User).get(7)
            eq_(u.name, 'jack')
        self.assert_sql_count(testing.db, go, 0)

    @testing.resolve_artifact_names
    def test_expire_doesntload_on_set(self):
        mapper(User, users)

        sess = create_session()
        u = sess.query(User).get(7)

        sess.expire(u, attribute_names=['name'])
        def go():
            u.name = 'somenewname'
        self.assert_sql_count(testing.db, go, 0)
        sess.flush()
        sess.expunge_all()
        assert sess.query(User).get(7).name == 'somenewname'

    @testing.resolve_artifact_names
    def test_no_session(self):
        mapper(User, users)
        sess = create_session()
        u = sess.query(User).get(7)

        sess.expire(u, attribute_names=['name'])
        sess.expunge(u)
        assert_raises(orm_exc.DetachedInstanceError, getattr, u, 'name')

    @testing.resolve_artifact_names
    def test_pending_raises(self):
        # this was the opposite in 0.4, but the reasoning there seemed off.
        # expiring a pending instance makes no sense, so should raise
        mapper(User, users)
        sess = create_session()
        u = User(id=15)
        sess.add(u)
        assert_raises(sa_exc.InvalidRequestError, sess.expire, u, ['name'])

    @testing.resolve_artifact_names
    def test_no_instance_key(self):
        # this tests an artificial condition such that
        # an instance is pending, but has expired attributes.  this
        # is actually part of a larger behavior when postfetch needs to
        # occur during a flush() on an instance that was just inserted
        mapper(User, users)
        sess = create_session()
        u = sess.query(User).get(7)

        sess.expire(u, attribute_names=['name'])
        sess.expunge(u)
        attributes.instance_state(u).key = None
        assert 'name' not in u.__dict__
        sess.add(u)
        assert u.name == 'jack'

    @testing.resolve_artifact_names
    def test_no_instance_key_no_pk(self):
        # same as test_no_instance_key, but the PK columns
        # are absent.  ensure an error is raised.
        mapper(User, users)
        sess = create_session()
        u = sess.query(User).get(7)

        sess.expire(u, attribute_names=['name', 'id'])
        sess.expunge(u)
        attributes.instance_state(u).key = None
        assert 'name' not in u.__dict__
        sess.add(u)
        assert_raises(sa_exc.InvalidRequestError, getattr, u, 'name')


    @testing.resolve_artifact_names
    def test_expire_preserves_changes(self):
        """test that the expire load operation doesn't revert post-expire changes"""

        mapper(Order, orders)
        sess = create_session()
        o = sess.query(Order).get(3)
        sess.expire(o)

        o.description = "order 3 modified"
        def go():
            assert o.isopen == 1
        self.assert_sql_count(testing.db, go, 1)
        assert o.description == 'order 3 modified'

        del o.description
        assert "description" not in o.__dict__
        sess.expire(o, ['isopen'])
        sess.query(Order).all()
        assert o.isopen == 1
        assert "description" not in o.__dict__

        assert o.description is None

        o.isopen=15
        sess.expire(o, ['isopen', 'description'])
        o.description = 'some new description'
        sess.query(Order).all()
        assert o.isopen == 1
        assert o.description == 'some new description'

        sess.expire(o, ['isopen', 'description'])
        sess.query(Order).all()
        del o.isopen
        def go():
            assert o.isopen is None
        self.assert_sql_count(testing.db, go, 0)

        o.isopen=14
        sess.expire(o)
        o.description = 'another new description'
        sess.query(Order).all()
        assert o.isopen == 1
        assert o.description == 'another new description'

    @testing.resolve_artifact_names
    def test_expire_committed(self):
        """test that the committed state of the attribute receives the most recent DB data"""
        mapper(Order, orders)

        sess = create_session()
        o = sess.query(Order).get(3)
        sess.expire(o)

        orders.update(id=3).execute(description='order 3 modified')
        assert o.isopen == 1
        assert attributes.instance_state(o).dict['description'] == 'order 3 modified'
        def go():
            sess.flush()
        self.assert_sql_count(testing.db, go, 0)

    @testing.resolve_artifact_names
    def test_expire_cascade(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, cascade="all, refresh-expire")
        })
        mapper(Address, addresses)
        s = create_session()
        u = s.query(User).get(8)
        assert u.addresses[0].email_address == 'ed@wood.com'

        u.addresses[0].email_address = 'someotheraddress'
        s.expire(u)
        assert u.addresses[0].email_address == 'ed@wood.com'

    @testing.resolve_artifact_names
    def test_refresh_cascade(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, cascade="all, refresh-expire")
        })
        mapper(Address, addresses)
        s = create_session()
        u = s.query(User).get(8)
        assert u.addresses[0].email_address == 'ed@wood.com'

        u.addresses[0].email_address = 'someotheraddress'
        s.refresh(u)
        assert u.addresses[0].email_address == 'ed@wood.com'

    def test_expire_cascade_pending_orphan(self):
        cascade = 'save-update, refresh-expire, delete, delete-orphan'
        self._test_cascade_to_pending(cascade, True)

    def test_refresh_cascade_pending_orphan(self):
        cascade = 'save-update, refresh-expire, delete, delete-orphan'
        self._test_cascade_to_pending(cascade, False)

    def test_expire_cascade_pending(self):
        cascade = 'save-update, refresh-expire'
        self._test_cascade_to_pending(cascade, True)

    def test_refresh_cascade_pending(self):
        cascade = 'save-update, refresh-expire'
        self._test_cascade_to_pending(cascade, False)

    @testing.resolve_artifact_names
    def _test_cascade_to_pending(self, cascade, expire_or_refresh):
        mapper(User, users, properties={
            'addresses':relationship(Address, cascade=cascade)
        })
        mapper(Address, addresses)
        s = create_session()

        u = s.query(User).get(8)
        a = Address(id=12, email_address='foobar')

        u.addresses.append(a)
        if expire_or_refresh:
            s.expire(u)
        else:
            s.refresh(u)
        if "delete-orphan" in cascade:
            assert a not in s
        else:
            assert a in s

        assert a not in u.addresses
        s.flush()

    @testing.resolve_artifact_names
    def test_expired_lazy(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user'),
            })
        mapper(Address, addresses)

        sess = create_session()
        u = sess.query(User).get(7)

        sess.expire(u)
        assert 'name' not in u.__dict__
        assert 'addresses' not in u.__dict__

        def go():
            assert u.addresses[0].email_address == 'jack@bean.com'
            assert u.name == 'jack'
        # two loads
        self.assert_sql_count(testing.db, go, 2)
        assert 'name' in u.__dict__
        assert 'addresses' in u.__dict__

    @testing.resolve_artifact_names
    def test_expired_eager(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user', lazy='joined'),
            })
        mapper(Address, addresses)

        sess = create_session()
        u = sess.query(User).get(7)

        sess.expire(u)
        assert 'name' not in u.__dict__
        assert 'addresses' not in u.__dict__

        def go():
            assert u.addresses[0].email_address == 'jack@bean.com'
            assert u.name == 'jack'
        # two loads, since relationship() + scalar are
        # separate right now on per-attribute load
        self.assert_sql_count(testing.db, go, 2)
        assert 'name' in u.__dict__
        assert 'addresses' in u.__dict__

        sess.expire(u, ['name', 'addresses'])
        assert 'name' not in u.__dict__
        assert 'addresses' not in u.__dict__

        def go():
            sess.query(User).filter_by(id=7).one()
            assert u.addresses[0].email_address == 'jack@bean.com'
            assert u.name == 'jack'
        # one load, since relationship() + scalar are
        # together when eager load used with Query
        self.assert_sql_count(testing.db, go, 1)

    @testing.resolve_artifact_names
    def test_relationship_changes_preserved(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user', lazy='joined'),
            })
        mapper(Address, addresses)
        sess = create_session()
        u = sess.query(User).get(8)
        sess.expire(u, ['name', 'addresses'])
        u.addresses
        assert 'name' not in u.__dict__
        del u.addresses[1]
        u.name
        assert 'name' in u.__dict__
        assert len(u.addresses) == 2

    @testing.resolve_artifact_names
    def test_joinedload_props_dontload(self):
        # relationships currently have to load separately from scalar instances.
        # the use case is: expire "addresses".  then access it.  lazy load
        # fires off to load "addresses", but needs foreign key or primary key
        # attributes in order to lazy load; hits those attributes, such as
        # below it hits "u.id".  "u.id" triggers full unexpire operation,
        # joinedloads addresses since lazy='joined'.  this is all wihtin lazy load
        # which fires unconditionally; so an unnecessary joinedload (or
        # lazyload) was issued.  would prefer not to complicate lazyloading to
        # "figure out" that the operation should be aborted right now.

        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user', lazy='joined'),
            })
        mapper(Address, addresses)
        sess = create_session()
        u = sess.query(User).get(8)
        sess.expire(u)
        u.id
        assert 'addresses' not in u.__dict__
        u.addresses
        assert 'addresses' in u.__dict__

    @testing.resolve_artifact_names
    def test_expire_synonym(self):
        mapper(User, users, properties={
            'uname': sa.orm.synonym('name')
        })

        sess = create_session()
        u = sess.query(User).get(7)
        assert 'name' in u.__dict__
        assert u.uname == u.name

        sess.expire(u)
        assert 'name' not in u.__dict__

        users.update(users.c.id==7).execute(name='jack2')
        assert u.name == 'jack2'
        assert u.uname == 'jack2'
        assert 'name' in u.__dict__

        # this wont work unless we add API hooks through the attr. system to
        # provide "expire" behavior on a synonym
        #    sess.expire(u, ['uname'])
        #    users.update(users.c.id==7).execute(name='jack3')
        #    assert u.uname == 'jack3'

    @testing.resolve_artifact_names
    def test_partial_expire(self):
        mapper(Order, orders)

        sess = create_session()
        o = sess.query(Order).get(3)

        sess.expire(o, attribute_names=['description'])
        assert 'id' in o.__dict__
        assert 'description' not in o.__dict__
        assert attributes.instance_state(o).dict['isopen'] == 1

        orders.update(orders.c.id==3).execute(description='order 3 modified')

        def go():
            assert o.description == 'order 3 modified'
        self.assert_sql_count(testing.db, go, 1)
        assert attributes.instance_state(o).dict['description'] == 'order 3 modified'

        o.isopen = 5
        sess.expire(o, attribute_names=['description'])
        assert 'id' in o.__dict__
        assert 'description' not in o.__dict__
        assert o.__dict__['isopen'] == 5
        assert attributes.instance_state(o).committed_state['isopen'] == 1

        def go():
            assert o.description == 'order 3 modified'
        self.assert_sql_count(testing.db, go, 1)
        assert o.__dict__['isopen'] == 5
        assert attributes.instance_state(o).dict['description'] == 'order 3 modified'
        assert attributes.instance_state(o).committed_state['isopen'] == 1

        sess.flush()

        sess.expire(o, attribute_names=['id', 'isopen', 'description'])
        assert 'id' not in o.__dict__
        assert 'isopen' not in o.__dict__
        assert 'description' not in o.__dict__
        def go():
            assert o.description == 'order 3 modified'
            assert o.id == 3
            assert o.isopen == 5
        self.assert_sql_count(testing.db, go, 1)

    @testing.resolve_artifact_names
    def test_partial_expire_lazy(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user'),
            })
        mapper(Address, addresses)

        sess = create_session()
        u = sess.query(User).get(8)

        sess.expire(u, ['name', 'addresses'])
        assert 'name' not in u.__dict__
        assert 'addresses' not in u.__dict__

        # hit the lazy loader.  just does the lazy load,
        # doesnt do the overall refresh
        def go():
            assert u.addresses[0].email_address=='ed@wood.com'
        self.assert_sql_count(testing.db, go, 1)

        assert 'name' not in u.__dict__

        # check that mods to expired lazy-load attributes
        # only do the lazy load
        sess.expire(u, ['name', 'addresses'])
        def go():
            u.addresses = [Address(id=10, email_address='foo@bar.com')]
        self.assert_sql_count(testing.db, go, 1)

        sess.flush()

        # flush has occurred, and addresses was modified,
        # so the addresses collection got committed and is
        # longer expired
        def go():
            assert u.addresses[0].email_address=='foo@bar.com'
            assert len(u.addresses) == 1
        self.assert_sql_count(testing.db, go, 0)

        # but the name attribute was never loaded and so
        # still loads
        def go():
            assert u.name == 'ed'
        self.assert_sql_count(testing.db, go, 1)

    @testing.resolve_artifact_names
    def test_partial_expire_eager(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user', lazy='joined'),
            })
        mapper(Address, addresses)

        sess = create_session()
        u = sess.query(User).get(8)

        sess.expire(u, ['name', 'addresses'])
        assert 'name' not in u.__dict__
        assert 'addresses' not in u.__dict__

        def go():
            assert u.addresses[0].email_address=='ed@wood.com'
        self.assert_sql_count(testing.db, go, 1)

        # check that mods to expired eager-load attributes
        # do the refresh
        sess.expire(u, ['name', 'addresses'])
        def go():
            u.addresses = [Address(id=10, email_address='foo@bar.com')]
        self.assert_sql_count(testing.db, go, 1)
        sess.flush()

        # this should ideally trigger the whole load
        # but currently it works like the lazy case
        def go():
            assert u.addresses[0].email_address=='foo@bar.com'
            assert len(u.addresses) == 1
        self.assert_sql_count(testing.db, go, 0)

        def go():
            assert u.name == 'ed'
        # scalar attributes have their own load
        self.assert_sql_count(testing.db, go, 1)
        # ideally, this was already loaded, but we arent
        # doing it that way right now
        #self.assert_sql_count(testing.db, go, 0)

    @testing.resolve_artifact_names
    def test_relationships_load_on_query(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user'),
            })
        mapper(Address, addresses)

        sess = create_session()
        u = sess.query(User).get(8)
        assert 'name' in u.__dict__
        u.addresses
        assert 'addresses' in u.__dict__

        sess.expire(u, ['name', 'addresses'])
        assert 'name' not in u.__dict__
        assert 'addresses' not in u.__dict__
        (sess.query(User).options(sa.orm.joinedload('addresses')).
         filter_by(id=8).all())
        assert 'name' in u.__dict__
        assert 'addresses' in u.__dict__

    @testing.resolve_artifact_names
    def test_partial_expire_deferred(self):
        mapper(Order, orders, properties={
            'description': sa.orm.deferred(orders.c.description)
        })

        sess = create_session()
        o = sess.query(Order).get(3)
        sess.expire(o, ['description', 'isopen'])
        assert 'isopen' not in o.__dict__
        assert 'description' not in o.__dict__

        # test that expired attribute access refreshes
        # the deferred
        def go():
            assert o.isopen == 1
            assert o.description == 'order 3'
        self.assert_sql_count(testing.db, go, 1)

        sess.expire(o, ['description', 'isopen'])
        assert 'isopen' not in o.__dict__
        assert 'description' not in o.__dict__
        # test that the deferred attribute triggers the full
        # reload
        def go():
            assert o.description == 'order 3'
            assert o.isopen == 1
        self.assert_sql_count(testing.db, go, 1)

        sa.orm.clear_mappers()

        mapper(Order, orders)
        sess.expunge_all()

        # same tests, using deferred at the options level
        o = sess.query(Order).options(sa.orm.defer('description')).get(3)

        assert 'description' not in o.__dict__

        # sanity check
        def go():
            assert o.description == 'order 3'
        self.assert_sql_count(testing.db, go, 1)

        assert 'description' in o.__dict__
        assert 'isopen' in o.__dict__
        sess.expire(o, ['description', 'isopen'])
        assert 'isopen' not in o.__dict__
        assert 'description' not in o.__dict__

        # test that expired attribute access refreshes
        # the deferred
        def go():
            assert o.isopen == 1
            assert o.description == 'order 3'
        self.assert_sql_count(testing.db, go, 1)
        sess.expire(o, ['description', 'isopen'])

        assert 'isopen' not in o.__dict__
        assert 'description' not in o.__dict__
        # test that the deferred attribute triggers the full
        # reload
        def go():
            assert o.description == 'order 3'
            assert o.isopen == 1
        self.assert_sql_count(testing.db, go, 1)

    @testing.resolve_artifact_names
    def test_joinedload_query_refreshes(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user', lazy='joined'),
            })
        mapper(Address, addresses)

        sess = create_session()
        u = sess.query(User).get(8)
        assert len(u.addresses) == 3
        sess.expire(u)
        assert 'addresses' not in u.__dict__
        print("-------------------------------------------")
        sess.query(User).filter_by(id=8).all()
        assert 'addresses' in u.__dict__
        assert len(u.addresses) == 3

    @testing.resolve_artifact_names
    def test_expire_all(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user', lazy='joined', 
                                    order_by=addresses.c.id),
            })
        mapper(Address, addresses)

        sess = create_session()
        userlist = sess.query(User).order_by(User.id).all()
        assert self.static.user_address_result == userlist
        assert len(list(sess)) == 9
        sess.expire_all()
        gc_collect()
        assert len(list(sess)) == 4 # since addresses were gc'ed

        userlist = sess.query(User).order_by(User.id).all()
        u = userlist[1]
        eq_(self.static.user_address_result, userlist)
        assert len(list(sess)) == 9

    @testing.resolve_artifact_names
    def test_state_change_col_to_deferred(self):
        """Behavioral test to verify the current activity of loader callables."""

        mapper(User, users)

        sess = create_session()

        # deferred attribute option, gets the LoadDeferredColumns
        # callable
        u1 = sess.query(User).options(defer(User.name)).first()
        assert isinstance(
                    attributes.instance_state(u1).callables['name'],
                    strategies.LoadDeferredColumns
                )

        # expire the attr, it gets the InstanceState callable
        sess.expire(u1, ['name'])
        assert isinstance(
                    attributes.instance_state(u1).callables['name'],
                    state.InstanceState
                )

        # load it, callable is gone
        u1.name
        assert 'name' not in attributes.instance_state(u1).callables

        # same for expire all
        sess.expunge_all()
        u1 = sess.query(User).options(defer(User.name)).first()
        sess.expire(u1)
        assert isinstance(
                    attributes.instance_state(u1).callables['name'],
                    state.InstanceState
                )

        # load over it.  everything normal.
        sess.query(User).first()
        assert 'name' not in attributes.instance_state(u1).callables

        sess.expunge_all()
        u1 = sess.query(User).first()
        # for non present, still expires the same way
        del u1.name
        sess.expire(u1)
        assert 'name' in attributes.instance_state(u1).callables

    @testing.resolve_artifact_names
    def test_state_deferred_to_col(self):
        """Behavioral test to verify the current activity of loader callables."""

        mapper(User, users, properties={'name':deferred(users.c.name)})

        sess = create_session()
        u1 = sess.query(User).options(undefer(User.name)).first()
        assert 'name' not in attributes.instance_state(u1).callables

        # mass expire, the attribute was loaded, 
        # the attribute gets the callable
        sess.expire(u1)
        assert isinstance(
                    attributes.instance_state(u1).callables['name'],
                    state.InstanceState
                )

        # load it, callable is gone
        u1.name
        assert 'name' not in attributes.instance_state(u1).callables

        # mass expire, attribute was loaded but then deleted,
        # the callable goes away - the state wants to flip 
        # it back to its "deferred" loader.
        sess.expunge_all()
        u1 = sess.query(User).options(undefer(User.name)).first()
        del u1.name
        sess.expire(u1)
        assert 'name' not in attributes.instance_state(u1).callables

        # single attribute expire, the attribute gets the callable
        sess.expunge_all()
        u1 = sess.query(User).options(undefer(User.name)).first()
        sess.expire(u1, ['name'])
        assert isinstance(
                    attributes.instance_state(u1).callables['name'],
                    state.InstanceState
                )

    @testing.resolve_artifact_names
    def test_state_noload_to_lazy(self):
        """Behavioral test to verify the current activity of loader callables."""

        mapper(User, users, properties={'addresses':relationship(Address, lazy='noload')})
        mapper(Address, addresses)

        sess = create_session()
        u1 = sess.query(User).options(lazyload(User.addresses)).first()
        assert isinstance(
                    attributes.instance_state(u1).callables['addresses'],
                    strategies.LoadLazyAttribute
                )
        # expire, it stays
        sess.expire(u1)
        assert isinstance(
                    attributes.instance_state(u1).callables['addresses'],
                    strategies.LoadLazyAttribute
                )

        # load over it.  callable goes away.
        sess.query(User).first()
        assert 'addresses' not in attributes.instance_state(u1).callables

        sess.expunge_all()
        u1 = sess.query(User).options(lazyload(User.addresses)).first()
        sess.expire(u1, ['addresses'])
        assert isinstance(
                    attributes.instance_state(u1).callables['addresses'],
                    strategies.LoadLazyAttribute
                )

        # load the attr, goes away
        u1.addresses
        assert 'addresses' not in attributes.instance_state(u1).callables



class PolymorphicExpireTest(_base.MappedTest):
    run_inserts = 'once'
    run_deletes = None

    @classmethod
    def define_tables(cls, metadata):
        global people, engineers, Person, Engineer

        people = Table('people', metadata,
           Column('person_id', Integer, primary_key=True,
                  test_needs_autoincrement=True),
           Column('name', String(50)),
           Column('type', String(30)),
           )

        engineers = Table('engineers', metadata,
           Column('person_id', Integer, ForeignKey('people.person_id'),
                  primary_key=True),
           Column('status', String(30)),
          )

    @classmethod
    def setup_classes(cls):
        class Person(_base.ComparableEntity):
            pass
        class Engineer(Person):
            pass

    @classmethod
    @testing.resolve_artifact_names
    def insert_data(cls):
        people.insert().execute(
            {'person_id':1, 'name':'person1', 'type':'person'},
            {'person_id':2, 'name':'engineer1', 'type':'engineer'},
            {'person_id':3, 'name':'engineer2', 'type':'engineer'},
        )
        engineers.insert().execute(
            {'person_id':2, 'status':'new engineer'},
            {'person_id':3, 'status':'old engineer'},
        )

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(Person, people, polymorphic_on=people.c.type, polymorphic_identity='person')
        mapper(Engineer, engineers, inherits=Person, polymorphic_identity='engineer')

    @testing.resolve_artifact_names
    def test_poly_deferred(self):

        sess = create_session()
        [p1, e1, e2] = sess.query(Person).order_by(people.c.person_id).all()

        sess.expire(p1)
        sess.expire(e1, ['status'])
        sess.expire(e2)

        for p in [p1, e2]:
            assert 'name' not in p.__dict__

        assert 'name' in e1.__dict__
        assert 'status' not in e2.__dict__
        assert 'status' not in e1.__dict__

        e1.name = 'new engineer name'

        def go():
            sess.query(Person).all()
        self.assert_sql_count(testing.db, go, 1)

        for p in [p1, e1, e2]:
            assert 'name' in p.__dict__

        assert 'status' not in e2.__dict__
        assert 'status' not in e1.__dict__

        def go():
            assert e1.name == 'new engineer name'
            assert e2.name == 'engineer2'
            assert e1.status == 'new engineer'
            assert e2.status == 'old engineer'
        self.assert_sql_count(testing.db, go, 2)
        eq_(Engineer.name.get_history(e1), (['new engineer name'],(), ['engineer1']))

    @testing.resolve_artifact_names
    def test_no_instance_key(self):

        sess = create_session()
        e1 = sess.query(Engineer).get(2)

        sess.expire(e1, attribute_names=['name'])
        sess.expunge(e1)
        attributes.instance_state(e1).key = None
        assert 'name' not in e1.__dict__
        sess.add(e1)
        assert e1.name == 'engineer1'

    @testing.resolve_artifact_names
    def test_no_instance_key(self):
        # same as test_no_instance_key, but the PK columns
        # are absent.  ensure an error is raised.
        sess = create_session()
        e1 = sess.query(Engineer).get(2)

        sess.expire(e1, attribute_names=['name', 'person_id'])
        sess.expunge(e1)
        attributes.instance_state(e1).key = None
        assert 'name' not in e1.__dict__
        sess.add(e1)
        assert_raises(sa_exc.InvalidRequestError, getattr, e1, 'name')


class ExpiredPendingTest(_fixtures.FixtureTest):
    run_define_tables = 'once'
    run_setup_classes = 'once'
    run_setup_mappers = None
    run_inserts = None

    @testing.resolve_artifact_names
    def test_expired_pending(self):
        mapper(User, users, properties={
            'addresses':relationship(Address, backref='user'),
            })
        mapper(Address, addresses)

        sess = create_session()
        a1 = Address(email_address='a1')
        sess.add(a1)
        sess.flush()

        u1 = User(name='u1')
        a1.user = u1
        sess.flush()

        # expire 'addresses'.  backrefs
        # which attach to u1 will expect to be "pending"
        sess.expire(u1, ['addresses'])

        # attach an Address.  now its "pending" 
        # in user.addresses
        a2 = Address(email_address='a2')
        a2.user = u1

        # expire u1.addresses again.  this expires
        # "pending" as well.
        sess.expire(u1, ['addresses'])

        # insert a new row
        sess.execute(addresses.insert(), dict(email_address='a3', user_id=u1.id))

        # only two addresses pulled from the DB, no "pending"
        assert len(u1.addresses) == 2

        sess.flush()
        sess.expire_all()
        assert len(u1.addresses) == 3


class RefreshTest(_fixtures.FixtureTest):

    @testing.resolve_artifact_names
    def test_refresh(self):
        mapper(User, users, properties={
            'addresses':relationship(mapper(Address, addresses), backref='user')
        })
        s = create_session()
        u = s.query(User).get(7)
        u.name = 'foo'
        a = Address()
        assert sa.orm.object_session(a) is None
        u.addresses.append(a)
        assert a.email_address is None
        assert id(a) in [id(x) for x in u.addresses]

        s.refresh(u)

        # its refreshed, so not dirty
        assert u not in s.dirty

        # username is back to the DB
        assert u.name == 'jack'

        assert id(a) not in [id(x) for x in u.addresses]

        u.name = 'foo'
        u.addresses.append(a)
        # now its dirty
        assert u in s.dirty
        assert u.name == 'foo'
        assert id(a) in [id(x) for x in u.addresses]
        s.expire(u)

        # get the attribute, it refreshes
        assert u.name == 'jack'
        assert id(a) not in [id(x) for x in u.addresses]

    @testing.resolve_artifact_names
    def test_persistence_check(self):
        mapper(User, users)
        s = create_session()
        u = s.query(User).get(7)
        s.expunge_all()
        assert_raises_message(sa_exc.InvalidRequestError, r"is not persistent within this Session", lambda: s.refresh(u))

    @testing.resolve_artifact_names
    def test_refresh_expired(self):
        mapper(User, users)
        s = create_session()
        u = s.query(User).get(7)
        s.expire(u)
        assert 'name' not in u.__dict__
        s.refresh(u)
        assert u.name == 'jack'

    @testing.resolve_artifact_names
    def test_refresh_with_lazy(self):
        """test that when a lazy loader is set as a trigger on an object's attribute
        (at the attribute level, not the class level), a refresh() operation doesnt
        fire the lazy loader or create any problems"""

        s = create_session()
        mapper(User, users, properties={'addresses':relationship(mapper(Address, addresses))})
        q = s.query(User).options(sa.orm.lazyload('addresses'))
        u = q.filter(users.c.id==8).first()
        def go():
            s.refresh(u)
        self.assert_sql_count(testing.db, go, 1)

    @testing.resolve_artifact_names
    def test_refresh_with_eager(self):
        """test that a refresh/expire operation loads rows properly and sends correct "isnew" state to eager loaders"""

        mapper(User, users, properties={
            'addresses':relationship(mapper(Address, addresses), lazy='joined')
        })

        s = create_session()
        u = s.query(User).get(8)
        assert len(u.addresses) == 3
        s.refresh(u)
        assert len(u.addresses) == 3

        s = create_session()
        u = s.query(User).get(8)
        assert len(u.addresses) == 3
        s.expire(u)
        assert len(u.addresses) == 3

    @testing.fails_on('maxdb', 'FIXME: unknown')
    @testing.resolve_artifact_names
    def test_refresh2(self):
        """test a hang condition that was occurring on expire/refresh"""

        s = create_session()
        mapper(Address, addresses)

        mapper(User, users, properties = dict(addresses=relationship(Address,cascade="all, delete-orphan",lazy='joined')) )

        u = User()
        u.name='Justin'
        a = Address(id=10, email_address='lala')
        u.addresses.append(a)

        s.add(u)
        s.flush()
        s.expunge_all()
        u = s.query(User).filter(User.name=='Justin').one()

        s.expire(u)
        assert u.name == 'Justin'

        s.refresh(u)

