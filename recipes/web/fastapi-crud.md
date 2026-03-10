---
name: FastAPI CRUD API
description: Build a complete FastAPI CRUD API with SQLAlchemy, Pydantic models, and pytest tests
author: Mekong CLI
tags: fastapi,python,api,crud,sqlalchemy,pydantic
difficulty: intermediate
estimated_time: 30min
---

# FastAPI CRUD API

Build a production-ready REST API with FastAPI, SQLAlchemy, and Pydantic.

## Prerequisites

- Python 3.9+
- Basic knowledge of async/await
- REST API concepts

## Step 1: Project Setup

```bash
# Create project directory
mkdir fastapi-crud-app && cd fastapi-crud-app

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install fastapi uvicorn[standard] sqlalchemy pydantic pytest httpx
```

## Step 2: Create Database Models

Create `models.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500))
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database setup
engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)
```

## Step 3: Create Pydantic Schemas

Create `schemas.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: int = Field(..., gt=0)

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[int] = Field(None, gt=0)

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## Step 4: Create FastAPI App

Create `main.py`:

```python
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from models import create_tables, SessionLocal, Item
from schemas import ItemCreate, ItemUpdate, ItemResponse

app = FastAPI(
    title="FastAPI CRUD",
    description="A simple CRUD API with FastAPI",
    version="1.0.0"
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup event
@app.on_event("startup")
def on_startup():
    create_tables()

# CREATE
@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# READ (all)
@app.get("/items/", response_model=List[ItemResponse])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Item).offset(skip).limit(limit).all()

# READ (single)
@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# UPDATE
@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

# DELETE
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return None
```

## Step 5: Create Tests

Create `test_main.py`:

```python
from fastapi.testclient import TestClient
from models import engine, Base, SessionLocal
from main import app
import pytest

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_create_item(client):
    response = client.post(
        "/items/",
        json={"name": "Test Item", "description": "A test", "price": 99}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data

def test_read_items(client):
    response = client.get("/items/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_item_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404

def test_update_item(client):
    create_resp = client.post(
        "/items/",
        json={"name": "Original", "description": "Desc", "price": 50}
    )
    item_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/items/{item_id}",
        json={"name": "Updated", "price": 75}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated"

def test_delete_item(client):
    create_resp = client.post(
        "/items/",
        json={"name": "ToDelete", "description": "Temp", "price": 10}
    )
    item_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/items/{item_id}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/items/{item_id}")
    assert get_resp.status_code == 404
```

## Step 6: Run and Verify

```bash
# Start server
uvicorn main:app --reload

# In another terminal, test the API
curl -X POST http://localhost:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"Hello","price":100}'

# Run tests
pytest test_main.py -v
```

## Verification Criteria

- [ ] Server starts without errors
- [ ] All CRUD endpoints respond correctly
- [ ] 404 for non-existent items
- [ ] All tests pass
- [ ] Swagger UI available at `/docs`

## Next Steps

- Add authentication (JWT)
- Add pagination metadata
- Add filtering and sorting
- Add database migrations with Alembic
