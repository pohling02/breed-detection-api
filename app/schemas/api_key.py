from pydantic import BaseModel

# The JSON structure we expect the user to send us
class KeyCreateRequest(BaseModel):
    name: str
    user_id: int