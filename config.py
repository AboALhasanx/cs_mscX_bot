"""Configuration module for the quiz bot."""
import os
from dataclasses import dataclass


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./data/database/db.sqlite')


config = Config()
