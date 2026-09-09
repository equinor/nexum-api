import os
from typing import List
from pydantic import Field
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    load_dotenv()

    ORIGINS: List[str] = [
        "http://localhost:5004",
        "https://frontend-prisma-decision-web-dev.radix.equinor.com",
        "https://frontend-prisma-decision-web-test.radix.equinor.com",
        "https://frontend-prisma-decision-web-prod.radix.equinor.com",
    ]

    APPINSIGHTS_CONNECTIONSTRING: str = Field(default=os.geten v("APPINSIGHTS_CONNECTIONSTRING", ""))
    APP_ENV: str = Field(default=os.getenv("APP_ENV", "local"))
    # Database token duration in seconds (default: 50 minutes)
    DEBUG: bool = False
    # set to true to save the influence diagram to a file pyagrum_data/network.json
    SAVE_INFLUENCE_DIAGRAM: bool = False

    # use to enable PyInstrumentMiddleWare
    # this will generate a profile.html at repository root
    PROFILE: bool = False
    LOGGER: bool = True


config = Config()
