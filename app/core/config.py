from tokenize import Ignore

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # --DATABASE --
    DATABASE_URL: str

    # --JWT KEY --
    SECRETE_JWT_KEY: str

    # SMTP EMAIL VARIABLES
    MAIL_USER: str
    MAIL_PASS: str
    MAIL_HOST: str
    MAIL_PORT: str
    MAIL_FROM: str

    DELIVERY_PERSON_EMAIL: str

    BACKEND_URL: str
    FRONTEND_URL: str
    RESET_PASSWORD_URL: str

    # GOOLE OAUTH
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_AUTH_BASE_URL: str
    GOOGLE_REDIRECT_URL: str

    # AWS 
    AWS_ACCESS_KEY:str
    AWS_SECRET_KEY:str
    AWS_BUCKET_NAME:str
    AWS_BUCKET_REGION:str

    # PAYMENTS
    STRIPE_SECRET_KEY:str
    PAYMENT_CONFIRMATION_URL:str
    PAYMENT_CANCEL_URL:str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


settings = Settings()
