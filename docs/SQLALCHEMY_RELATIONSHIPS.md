# SQLAlchemy Relationships: `back_populates` and `primaryjoin`

## Overview

SQLAlchemy relationships connect models together. Two key concepts are:
- **`back_populates`**: Creates bidirectional relationships
- **`primaryjoin`**: Defines custom join conditions

---

## 1. `back_populates` - Bidirectional Relationships

### What it does
`back_populates` creates a **bidirectional relationship** between two models. When you set it on one side, SQLAlchemy automatically creates the reverse relationship on the other side.

### Example from our codebase

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True)
    # ... other fields
    
    # This relationship says: "A User has many AgentInstallations"
    installations = relationship("AgentInstallation", back_populates="user")


# app/models/agent.py
class AgentInstallation(Base):
    __tablename__ = "agent_installations"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))  # Foreign key
    
    # This relationship says: "An AgentInstallation belongs to one User"
    # back_populates="installations" links back to User.installations
    user = relationship("User", back_populates="installations")
```

### How it works

```python
# Create a user
user = User(id=uuid.uuid4(), email="test@example.com")

# Create an installation
installation = AgentInstallation(
    id=uuid.uuid4(),
    user_id=user.id,
    agent_id="health_agent",
    version="1.0.0"
)

# Bidirectional access:
# Forward: user -> installations
print(user.installations)  # [installation]

# Reverse: installation -> user
print(installation.user)   # <User object>
print(installation.user.email)  # "test@example.com"
```

### Without `back_populates`

If you don't use `back_populates`, you'd have a **one-way relationship**:

```python
# One-way (only User -> AgentInstallation)
class User(Base):
    installations = relationship("AgentInstallation")  # No back_populates

class AgentInstallation(Base):
    user = relationship("User")  # No back_populates
    # This still works, but SQLAlchemy treats them as separate relationships
```

**Key difference**: With `back_populates`, SQLAlchemy knows these are the **same relationship** viewed from different sides.

---

## 2. `primaryjoin` - Custom Join Conditions

### What it does
`primaryjoin` lets you define **custom SQL join conditions** when the default foreign key join isn't sufficient.

### When you need it

1. **Composite key joins** (multiple columns)
2. **Non-standard joins** (not using foreign keys)
3. **Conditional joins** (with WHERE-like conditions)

### Example: Composite Key Join

In our codebase, `AgentManifest` has a composite primary key (agent_id + version), and `AgentInstallation` references it:

```python
class AgentManifest(Base):
    __tablename__ = "agent_manifests"
    agent_id = Column(String, primary_key=True)      # Part 1 of composite key
    version = Column(String, primary_key=True)        # Part 2 of composite key
    # ... other fields


class AgentInstallation(Base):
    __tablename__ = "agent_installations"
    id = Column(UUID, primary_key=True)
    agent_id = Column(String)  # NOT a foreign key (no ForeignKey() constraint)
    version = Column(String)   # NOT a foreign key
    
    # We need to join on BOTH agent_id AND version
    manifest = relationship(
        "AgentManifest",
        primaryjoin="and_("
                    "AgentInstallation.agent_id == AgentManifest.agent_id, "
                    "AgentInstallation.version == AgentManifest.version"
                    ")",
        foreign_keys=[agent_id, version],  # Tell SQLAlchemy which columns to use
        viewonly=True
    )
```

### How it works

```python
# Create a manifest
manifest = AgentManifest(
    agent_id="health_agent",
    version="1.0.0",
    manifest={"name": "Health Agent"}
)

# Create an installation that references it
installation = AgentInstallation(
    id=uuid.uuid4(),
    agent_id="health_agent",  # Matches manifest.agent_id
    version="1.0.0"            # Matches manifest.version
)

# Access the manifest through the relationship
print(installation.manifest.agent_id)  # "health_agent"
print(installation.manifest.version)   # "1.0.0"
```

### Without `primaryjoin` (default behavior)

By default, SQLAlchemy looks for a **single foreign key**:

```python
# Default: SQLAlchemy looks for a ForeignKey
class AgentInstallation(Base):
    manifest_id = Column(UUID, ForeignKey("agent_manifests.id"))  # Single FK
    
    # No primaryjoin needed - SQLAlchemy uses the foreign key automatically
    manifest = relationship("AgentManifest")
```

But with **composite keys**, there's no single foreign key, so we need `primaryjoin`.

---

## 3. Real-World Examples

### Example 1: Simple One-to-Many (with back_populates)

```python
class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    # One author has many books
    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey("authors.id"))
    
    # One book belongs to one author
    author = relationship("Author", back_populates="books")


# Usage:
author = Author(name="J.K. Rowling")
book1 = Book(title="Harry Potter 1", author_id=author.id)
book2 = Book(title="Harry Potter 2", author_id=author.id)

# Bidirectional access
author.books  # [book1, book2]
book1.author  # <Author: J.K. Rowling>
```

### Example 2: Many-to-Many (with back_populates)

```python
# Association table
student_course = Table(
    'student_course',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    courses = relationship("Course", secondary=student_course, back_populates="students")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    students = relationship("Student", secondary=student_course, back_populates="courses")


# Usage:
student = Student(name="Alice")
course1 = Course(name="Math")
course2 = Course(name="Science")

student.courses = [course1, course2]

# Bidirectional
student.courses     # [course1, course2]
course1.students    # [student]
```

### Example 3: Conditional Join (with primaryjoin)

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    status = Column(String)  # "active", "inactive"
    
    # Only get active posts
    active_posts = relationship(
        "Post",
        primaryjoin="and_(User.id == Post.user_id, Post.status == 'published')",
        foreign_keys="[Post.user_id]"
    )

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)  # "draft", "published"


# Usage:
user = User(id=1, status="active")
post1 = Post(user_id=1, status="published")
post2 = Post(user_id=1, status="draft")

user.active_posts  # Only [post1], not post2
```

---

## 4. Common Patterns in Our Codebase

### Pattern 1: Standard Foreign Key (no primaryjoin needed)

```python
# app/models/user.py
class User(Base):
    installations = relationship("AgentInstallation", back_populates="user")

class AgentInstallation(Base):
    user_id = Column(UUID, ForeignKey("users.id"))  # Standard FK
    user = relationship("User", back_populates="installations")
```

### Pattern 2: Composite Key Join (primaryjoin required)

```python
# app/models/agent.py
class AgentInstallation(Base):
    agent_id = Column(String)  # No FK constraint
    version = Column(String)   # No FK constraint
    
    manifest = relationship(
        "AgentManifest",
        primaryjoin="and_("
                    "AgentInstallation.agent_id == AgentManifest.agent_id, "
                    "AgentInstallation.version == AgentManifest.version"
                    ")",
        foreign_keys=[agent_id, version],
        viewonly=True
    )
```

### Pattern 3: One-to-One (uselist=False)

```python
# app/models/user.py
class User(Base):
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class UserProfile(Base):
    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="profile")
```

---

## 5. Key Takeaways

| Concept | Purpose | When to Use |
|---------|---------|-------------|
| `back_populates` | Creates bidirectional relationships | When you want to navigate both directions (parent→child and child→parent) |
| `primaryjoin` | Defines custom join conditions | When default FK join doesn't work (composite keys, conditional joins) |
| `foreign_keys` | Specifies which columns are "foreign" | Required with `primaryjoin` to tell SQLAlchemy which columns to use |
| `viewonly=True` | Makes relationship read-only | When you don't want SQLAlchemy to manage the relationship (e.g., composite keys without FK constraints) |

---

## 6. Debugging Tips

### Check if relationship works:

```python
from app.database import SessionLocal
from app.models import User, AgentInstallation

db = SessionLocal()

# Test bidirectional access
user = db.query(User).first()
if user:
    print(f"User has {len(user.installations)} installations")
    for inst in user.installations:
        print(f"  - {inst.agent_id} v{inst.version}")
        print(f"    Belongs to: {inst.user.email}")  # Reverse access
```

### Common errors:

1. **"NoForeignKeysError"**: Need `primaryjoin` for composite keys
2. **"Both same direction"**: Need `remote_side` or remove `back_populates`
3. **"Can't determine join"**: Specify `foreign_keys` parameter

---

## Summary

- **`back_populates`**: "Link these two relationships together bidirectionally"
- **`primaryjoin`**: "Join using this custom SQL condition instead of the default"

In our codebase:
- `User` ↔ `AgentInstallation`: Standard FK with `back_populates` ✅
- `AgentInstallation` → `AgentManifest`: Composite key with `primaryjoin` ✅
