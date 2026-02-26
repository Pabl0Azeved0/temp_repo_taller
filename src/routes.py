"""
This module defines the Flask API routes for the MiniVenmo application.

It handles user creation, payments, friend management, and activity feed retrieval.
"""
from flask import Blueprint, request, jsonify, Response
from src.models import db, User, MiniVenmo, Activity
from typing import Tuple, Dict, Any, Union, List, Optional

bp = Blueprint("api", __name__)


@bp.route("/users", methods=["POST"])
def create_user() -> Tuple[Response, int]:
    """
    API endpoint to create a new user.

    Expects a JSON payload with 'name', and optional 'initial_balance' and 'credit_limit'.
    Returns the created user's details and wallet information.
    """
    data: Dict[str, Any] = request.json
    name: Optional[str] = data.get("name")
    initial_balance: float = float(data.get("initial_balance", 0.0))
    credit_limit: float = float(data.get("credit_limit", 1000.0))

    if not name:
        return jsonify({"error": "Name is required"}), 400

    try:
        user: User = MiniVenmo.create_user(name, initial_balance, credit_limit)
        return (
            jsonify(
                {
                    "id": user.id,
                    "name": user.name,
                    "wallet_id": user.wallet.id,
                    "balance": user.wallet.balance,
                    "credit": user.wallet.credit,
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/users/<string:user_id>/pay", methods=["POST"])
def pay(user_id: str) -> Tuple[Response, int]:
    """
    API endpoint for a user to make a payment to another user.

    Expects a JSON payload with 'target_id', 'amount', and an optional 'description'.
    The `user_id` in the URL path is the payer.
    """
    data: Dict[str, Any] = request.json
    target_id: Optional[str] = data.get("target_id")
    amount: Optional[Union[float, str]] = data.get("amount")
    description: str = str(data.get("description", ""))

    if not target_id or amount is None:
        return jsonify({"error": "target_id and amount are required"}), 400

    user: Optional[User] = User.query.get(user_id)
    target: Optional[User] = User.query.get(target_id)

    if not user or not target:
        return jsonify({"error": "User or target not found"}), 404

    try:
        user.pay(target, float(amount), description)
        return jsonify({"message": "Payment successful"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/users/<string:user_id>/friends", methods=["POST"])
def add_friend(user_id: str) -> Tuple[Response, int]:
    """
    API endpoint for a user to add another user as a friend.

    Expects a JSON payload with 'friend_id'. The `user_id` in the URL path
    is the user initiating the friend request.
    """
    data: Dict[str, Any] = request.json
    friend_id: Optional[str] = data.get("friend_id")

    if not friend_id:
        return jsonify({"error": "friend_id is required"}), 400

    user: Optional[User] = User.query.get(user_id)
    friend: Optional[User] = User.query.get(friend_id)

    if not user or not friend:
        return jsonify({"error": "User or friend not found"}), 404

    if user.add_friend(friend):
        return jsonify({"message": "Friend added successfully"}), 200
    else:
        return jsonify({"message": "Already friends or invalid operation"}), 200


@bp.route("/users/<string:user_id>/activity", methods=["GET"])
def get_activity(user_id: str) -> Tuple[Response, int]:
    """
    API endpoint to retrieve the personal activity feed for a given user.

    The `user_id` in the URL path specifies whose activity to retrieve.
    """
    user: Optional[User] = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    feed: List[str] = user.retrieve_activity()
    return jsonify({"activity": feed}), 200


@bp.route("/feed", methods=["GET"])
def get_feed() -> Tuple[Response, int]:
    """
    API endpoint to retrieve the application's activity feed.

    Can optionally take a 'user_id' query parameter to retrieve a personalized
    feed for that user, including their friends' activities.
    """
    user_id: Optional[str] = request.args.get("user_id")
    feed: List[str] = MiniVenmo.render_feed(user_id)
    return jsonify({"feed": feed}), 200