from fastapi import FastAPI
from sqlalchemy import create_engine
import pydantic

print("FastAPI OK")
print("SQLAlchemy OK")
print(f"Pydantic version: {pydantic.__version__}")
print("All good!")