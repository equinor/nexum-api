import os
from typing import List
from pydantic import Field
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    load_dotenv()

    ORIGINS: List[str] = [
        "http://localhost:5004",
        "https://frontend-dot-web-dev.radix.equinor.com",
        "https://frontend-dot-web-test.radix.equinor.com",
        "https://frontend-dot-web-prod.radix.equinor.com",
    ]

    CLIENT_ID: str = Field(default=os.getenv("CLIENT_ID", "4251833c-b9c3-4013-afda-cbfd2cc50f3f"))
    CLIENT_SECRET: str = Field(default=os.getenv("CLIENT_SECRET", ""))

    REDIRECT_URL: str = Field(
        default=os.getenv("REDIRECT_URL", "http://localhost:8000/docs/oauth2-redirect")
    )
    SCOPE: str = Field(default=os.getenv("SCOPE", "4251833c-b9c3-4013-afda-cbfd2cc50f3f/Read"))
    TENANT_ID: str = "3aa4a235-b6e2-48d5-9195-7fcf05b459b0"
    AUTHORITY: str = f"https://login.microsoftonline.com/{TENANT_ID}"
    AUTH_URL: str = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
    TOKEN_URL: str = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    JWKS_URL: str = f"{AUTHORITY}/discovery/v2.0/keys"
    AUDIENCE: str = Field(default=os.getenv("AUDIENCE", "4251833c-b9c3-4013-afda-cbfd2cc50f3f"))
    JWKS_URI: str = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
    ISSUER: str = f"https://sts.windows.net/{TENANT_ID}/"
    APP_ENV: str = Field(default=os.getenv("APP_ENV", "local"))
    DATABASE_CONN_LOCAL: str = Field(
        default=os.getenv("DATABASE_CONN_LOCAL", "sqlite+aiosqlite:///:memory:")
    )
    APPINSIGHTS_CONNECTIONSTRING: str = Field(default=os.getenv("APPINSIGHTS_CONNECTIONSTRING", ""))

    DATABASE_CONN_DEV: str = Field(
        default=os.getenv(
            "DATABASE_CONN_DEV",
            "DRIVER={ODBC Driver 18 for SQL Server};MARS_Connection=Yes;Server=decision-optimization-sqlserver-dev.database.windows.net;Database=decision-optimization-sqldb-dev;",
        )
    )
    DATABASE_CONN_TEST: str = Field(
        default=os.getenv(
            "DATABASE_CONN_TEST",
            "DRIVER={ODBC Driver 18 for SQL Server};MARS_Connection=Yes;Server=decision-optimization-sqlserver-test.database.windows.net;Database=decision-optimization-sqldb-test;",
        )
    )
    DATABASE_CONN_PROD: str = Field(
        default=os.getenv(
            "DATABASE_CONN_PROD",
            "DRIVER={ODBC Driver 18 for SQL Server};MARS_Connection=Yes;Server=decision-optimization-sqlserver-prod.database.windows.net;Database=decision-optimization-sqldb-prod;",
        )
    )

    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_RECYCLE: int = 1800
    # Database token duration in seconds (default: 50 minutes)
    DB_TOKEN_DURATION: int = 3000
    DEBUG: bool = False

    # Cache for 60 minutes
    CACHE_DURATION: int = 3600
    CACHE_MAX_SIZE: int = 256

    # use to enable PyInstrumentMiddleWare
    # this will generate a profile.html at repository root
    PROFILE: bool = False
    LOGGER: bool = True

    ##ratelimiter settings
    RATE_LIMIT_WINDOW: int = 60  # in seconds
    MAX_REQUESTS_PER_WINDOW: int = 100


config = Config()
