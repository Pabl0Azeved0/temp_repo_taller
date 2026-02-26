import uuid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import List, Optional

db = SQLAlchemy()


class Friendship(db.Model):
    """
    Represents a friendship link between two users.

    This model acts as an association table, keeping track of when
    users became friends. It's directional, so two records are created
    for a mutual friendship.
    """

    __tablename__ = "friendships"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    friend_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Activity(db.Model):
    """
    Represents a social activity or transaction in the application.

    Can be a 'payment' between users or a 'friendship' event.
    Keeps a record of actors, targets, amounts, and descriptions.
    """

    __tablename__ = "activities"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 'payment', 'friendship'
    actor_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    target_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    actor = db.relationship("User", foreign_keys=[actor_id])
    target = db.relationship("User", foreign_keys=[target_id])


class User(db.Model):
    """
    Represents a user of the MiniVenmo application.

    A user has a unique ID, a name, and a linked wallet.
    They can add friends, pay other users, and view their activity.
    """

    __tablename__ = "users"
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)

    wallet = db.relationship("MiniVenmo", backref="user", uselist=False)

    def add_friend(self, friend_user: "User") -> bool:
        """
        Adds another user as a friend.

        Args:
            friend_user (User): The user object to be added as a friend.

        Returns:
            bool: True if the friendship was successfully created,
                False if they were already friends or if the user tried to add themselves.
        """
        if self.id == friend_user.id:
            return False

        existing = Friendship.query.filter_by(
            user_id=self.id, friend_id=friend_user.id
        ).first()
        if not existing:
            f1 = Friendship(user_id=self.id, friend_id=friend_user.id)
            f2 = Friendship(user_id=friend_user.id, friend_id=self.id)
            db.session.add_all([f1, f2])

            activity = Activity(
                type="friendship", actor_id=self.id, target_id=friend_user.id
            )
            db.session.add(activity)
            db.session.commit()
            return True
        return False

    def pay(
        self, target_user: "User", amount: float, description: str = ""
    ) -> Activity:
        """
        Transfers funds from this user to a target user.

        If the user does not have enough balance, it utilizes their credit line up
        to their credit limit.

        Args:
            target_user (User): The user receiving the payment.
            amount (float): The amount to pay. Must be positive.
            description (str, optional): A description of the payment. Defaults to "".

        Raises:
            ValueError: If either user lacks a wallet, the amount is negative,
                        or the credit limit is exceeded.

        Returns:
            Activity: The payment activity record that was generated.
        """
        wallet = self.wallet
        if not wallet:
            raise ValueError("User has no wallet")
        target_wallet = target_user.wallet
        if not target_wallet:
            raise ValueError("Target user has no wallet")

        if amount <= 0:
            raise ValueError("Amount must be positive")

        if wallet.balance >= amount:
            wallet.balance -= amount
        else:
            remaining = amount - wallet.balance
            if wallet.credit + remaining > wallet.credit_limit:
                raise ValueError("Credit limit exceeded")
            wallet.balance = 0
            wallet.credit += remaining

        target_wallet.balance += amount

        activity = Activity(
            type="payment",
            actor_id=self.id,
            target_id=target_user.id,
            amount=amount,
            description=description,
        )
        db.session.add(activity)
        db.session.commit()
        return activity

    def retrieve_activity(self) -> List[str]:
        """
        Retrieves the user's personal activity feed.

        This includes payments they made or received, and friendships they formed,
        formatted as human-readable strings.

        Returns:
            List[str]: A list of activity description strings, ordered newest to oldest.
        """
        activities = (
            Activity.query.filter(
                (Activity.actor_id == self.id) | (Activity.target_id == self.id)
            )
            .order_by(Activity.timestamp.desc())
            .all()
        )

        feed = []
        for act in activities:
            if act.type == "payment":
                feed.append(
                    f"{act.actor.name} paid {act.target.name} ${act.amount:.2f} for {act.description}"
                )
            elif act.type == "friendship":
                feed.append(f"{act.actor.name} added {act.target.name} as a friend")
        return feed


class MiniVenmo(db.Model):
    """
    Represents the financial wallet of a User.

    Contains their cash balance, used credit, and the maximum credit limit.
    """

    __tablename__ = "wallets"
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    balance = db.Column(db.Float, default=0.0)
    credit = db.Column(db.Float, default=0.0)
    credit_limit = db.Column(db.Float, default=1000.0)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)

    @classmethod
    def create_user(
        cls, name: str, initial_balance: float = 0.0, credit_limit: float = 1000.0
    ) -> User:
        """
        Factory method to create a new User and their associated MiniVenmo wallet.

        Args:
            name (str): The unique name of the new user.
            initial_balance (float, optional): Starting cash balance. Defaults to 0.0.
            credit_limit (float, optional): Maximum allowed credit. Defaults to 1000.0.

        Returns:
            User: The newly created User object.
        """
        user = User(name=name)
        db.session.add(user)
        db.session.flush()

        wallet = cls(
            user_id=user.id, balance=initial_balance, credit_limit=credit_limit
        )
        db.session.add(wallet)
        db.session.commit()
        return user

    @classmethod
    def render_feed(cls, user_id: Optional[str] = None) -> List[str]:
        """
        Renders the application activity feed.

        If a user_id is provided, it renders a personalized feed including
        activities involving the user and their friends. Otherwise, it renders
        the global feed of all application activities.

        Args:
            user_id (Optional[str], optional): ID of the user to render a specific feed for. Defaults to None.

        Returns:
            List[str]: A list of activity description strings, ordered newest to oldest.
        """
        if user_id:
            friend_ids = [
                f.friend_id for f in Friendship.query.filter_by(user_id=user_id).all()
            ]
            friend_ids.append(user_id)
            activities = (
                Activity.query.filter(
                    (Activity.actor_id.in_(friend_ids))
                    | (Activity.target_id.in_(friend_ids))
                )
                .order_by(Activity.timestamp.desc())
                .all()
            )
        else:
            activities = Activity.query.order_by(Activity.timestamp.desc()).all()

        feed = []
        for act in activities:
            if act.type == "payment":
                feed.append(
                    f"{act.actor.name} paid {act.target.name} ${act.amount:.2f} for {act.description}"
                )
            elif act.type == "friendship":
                feed.append(f"{act.actor.name} added {act.target.name} as a friend")
        return feed
