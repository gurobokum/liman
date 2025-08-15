"""
This is a mocked backend server that simulates a real backend server
for demonstration and testing purposes.

It provides a simple User Management API with in-memory storage
to showcase how Liman framework can interact with OpenAPI-based services.
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel

app = FastAPI(
    title="User Management API",
    description="FastAPI implementation based of Liman Simple OpenAPI samle",
    version="1.0.0",
)


class User(BaseModel):
    id: str
    name: str
    email: str
    region: str
    is_admin: bool


class UpdateUserRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    is_admin: bool | None = None


users = {
    "12345": {
        "id": "12345",
        "name": "John",
        "email": "john@example.com",
        "region": "US",
        "is_admin": True,
    },
    "67890": {
        "id": "67890",
        "name": "Max",
        "email": "max@example.com",
        "region": "EU",
        "is_admin": True,
    },
    "54321": {
        "id": "54321",
        "name": "Alice",
        "email": "alice@example.com",
        "region": "US",
        "is_admin": False,
    },
    "17821": {
        "id": "17821",
        "name": "Sofia",
        "email": "sofia@example.com",
        "region": "EU",
        "is_admin": False,
    },
    "99821": {
        "id": "99821",
        "name": "Bob",
        "email": "bob@example.com",
        "region": "EU",
        "is_admin": False,
    },
}


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str) -> User:
    """Get a user by their ID"""
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    return User.model_validate(user)


@app.get("/users", response_model=list[User])
def list_users() -> list[User]:
    """List all users in the system"""
    return [User.model_validate(user) for user in users.values()]


@app.get("/users/search/name/{name}", response_model=User)
def search_user(name: str) -> User:
    """Search a user by name"""
    for user in users.values():
        if user["name"].lower() == name.lower():
            return User.model_validate(user)
    raise HTTPException(status_code=404, detail=f"No user found with name {name}")


@app.get("/users/search/region/{region}", response_model=list[str])
def search_by_region(region: str) -> list[str]:
    """Find user IDs by region"""
    user_ids = [
        user["id"]
        for user in users.values()
        if user["region"].lower() == region.lower()
    ]
    if not user_ids:
        raise HTTPException(
            status_code=404, detail=f"No users found in region {region}"
        )
    return user_ids


@app.put("/users/{user_id}", response_model=dict[str, Any])
def update_user(user_id: str, request: UpdateUserRequest) -> dict[str, Any]:
    """Update a user by ID"""
    if user_id not in users:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

    user = users[user_id]
    changed = False

    for field in ["name", "email", "is_admin"]:
        value = getattr(request, field, None)
        if value is not None and value != user.get(field):
            user[field] = value
            changed = True

    return {"was_changed": changed, "user": user}


@app.delete("/users/{user_id}")
def delete_user(user_id: str) -> dict[str, str]:
    """Delete a user by ID"""
    if user_id in users:
        del users[user_id]
    else:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

    return {"message": f"User with ID {user_id} has been deleted"}


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.

    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


use_route_names_as_operation_ids(app)
