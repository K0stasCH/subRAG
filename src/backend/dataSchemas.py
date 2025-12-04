from pydantic import BaseModel


class Query(BaseModel):
    """
    The input question sent by the user.

    Attributes:
        text (str): The natural language question to be answered.
    """

    query: str