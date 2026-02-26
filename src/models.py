import uuid
from typing import List

class User():
    id = uuid.uuidv4()
    name = str
    wallet_id = uuid.uuidv4() # Foreign Key
    friends = List[str]

class MiniVenmo():
    id = uuid.uuidv4()
    balance = int
    credit = int
    credit_limit = int
    user_id = uuid.uuidv4() # Foreign Key
