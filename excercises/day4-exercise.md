# Day 4 Exercise — Create DB and Tasks Table

## Task
Set up SQLite database with SQLAlchemy and verify the `tasks` table is created.

## Instructions
1. Install dependencies: `pip install sqlalchemy`
2. Create a `database.py` file with SQLite connection
3. Create a `models.py` file with a `Task` model
4. Run the script and confirm the `tasks.db` file and table are created

## Starter Code

**database.py**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

**models.py**
```python
from sqlalchemy import Column, Integer, String
from database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    status = Column(String, default="pending")
```

**init_db.py** _(run this to create the table)_
```python
from database import engine, Base
import models

Base.metadata.create_all(bind=engine)
print("Database and tasks table created!")
```

## Run it
```bash
python init_db.py
```

## Expected Output
```
Database and tasks table created!
```
_(Also check that `tasks.db` file appeared in your folder)_

## Your Solution
_(notes or modifications below)_

```python

```
