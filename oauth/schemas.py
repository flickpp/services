
from schemas import Schema, String


class NewLoginReq(Schema):
    current_url = String(min_length=10, required=True, description="current url of browser")
