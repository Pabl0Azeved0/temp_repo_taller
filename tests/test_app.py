import pytest
import os
from src.main import create_app
from src.models import db, User, MiniVenmo

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_user(app):
    with app.app_context():
        user = MiniVenmo.create_user("Bobby", 10.0, 100.0)
        assert user.name == "Bobby"
        assert user.wallet.balance == 10.0
        assert user.wallet.credit_limit == 100.0

def test_pay_with_balance(app):
    with app.app_context():
        u1 = MiniVenmo.create_user("Bobby", 50.0)
        u2 = MiniVenmo.create_user("Carol", 10.0)
        
        act = u1.pay(u2, 20.0, "Lunch")
        
        assert u1.wallet.balance == 30.0
        assert u2.wallet.balance == 30.0
        assert act.amount == 20.0
        assert act.description == "Lunch"

def test_pay_with_credit(app):
    with app.app_context():
        u1 = MiniVenmo.create_user("Bobby", 10.0, 100.0)
        u2 = MiniVenmo.create_user("Carol", 10.0)
        
        u1.pay(u2, 50.0, "Dinner")
        
        assert u1.wallet.balance == 0.0
        assert u1.wallet.credit == 40.0
        assert u2.wallet.balance == 60.0

def test_pay_exceed_credit(app):
    with app.app_context():
        u1 = MiniVenmo.create_user("Bobby", 10.0, 20.0)
        u2 = MiniVenmo.create_user("Carol", 10.0)
        
        with pytest.raises(ValueError, match="Credit limit exceeded"):
            u1.pay(u2, 50.0, "Too expensive")

def test_add_friend(app):
    with app.app_context():
        u1 = MiniVenmo.create_user("Bobby")
        u2 = MiniVenmo.create_user("Carol")
        
        res = u1.add_friend(u2)
        assert res is True
        
        res2 = u1.add_friend(u2)
        assert res2 is False # Already friends
        
        res3 = u1.add_friend(u1)
        assert res3 is False # Cannot add self

def test_retrieve_activity(app):
    with app.app_context():
        u1 = MiniVenmo.create_user("Bobby", 50.0)
        u2 = MiniVenmo.create_user("Carol", 50.0)
        
        u1.pay(u2, 5.0, "Coffee")
        u2.pay(u1, 15.0, "Lunch")
        
        feed1 = u1.retrieve_activity()
        assert len(feed1) == 2
        assert feed1[0] == "Carol paid Bobby $15.00 for Lunch"
        assert feed1[1] == "Bobby paid Carol $5.00 for Coffee"

def test_render_feed(app):
    with app.app_context():
        u1 = MiniVenmo.create_user("Bobby", 50.0)
        u2 = MiniVenmo.create_user("Carol", 50.0)
        u3 = MiniVenmo.create_user("Dave", 50.0)
        
        u1.add_friend(u2)
        u1.pay(u2, 5.0, "Coffee")
        u2.pay(u1, 15.0, "Lunch")
        u2.pay(u3, 10.0, "Snack")
        
        global_feed = MiniVenmo.render_feed()
        assert len(global_feed) == 4
        
        bobby_feed = MiniVenmo.render_feed(u1.id)
        assert len(bobby_feed) == 4 # Includes the friend add + 3 payments
        assert "Bobby added Carol as a friend" in bobby_feed
