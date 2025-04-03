# This file will contain the response structure and any data validation
from pydantic import BaseModel

class CheckinResponse(BaseModel):
    checkinLink: str

    class Config:
        # Use the same JSON structure that Amadeus returns
        schema_extra = {
            "example": {
                "checkinLink": "https://test.api.amadeus.com/v1/airlines/booking/checkin/PNR123456789"
            }
        }
