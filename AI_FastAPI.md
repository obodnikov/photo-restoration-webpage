# **AI_FASTAPI.md – Python Async API Application (FastAPI)**

## **General**

* Follow **PEP8**, use **type hints**, and prefer **async/await** for I/O-heavy operations.
* Organize the project into a structured layout:

  ```
  app/
    api/
      v1/
        routes/
        schemas/
    core/
    services/
    models/
    db/
    utils/
  ```
* Define request/response models using **Pydantic**.
* Keep JS/CSS in separate static files — **never embed logic in HTML**.
* Add docstrings for:

  * route handlers
  * service functions
  * background tasks

---

## **Rules**

### **1. No secrets in code**

* Never hardcode keys (HF API keys, DB passwords).
* Use:

  * `.env` + `pydantic.BaseSettings` (preferred)
  * or Docker secrets
* Load settings in a central module: `app/core/config.py`.

### **2. Keep business logic outside routes**

* Route handlers (`api/v1/routes/*.py`) should be thin:

  * parse request
  * call service layer
  * return result
* Heavy logic, external API calls, and async jobs go to `services/`.

### **3. File size limit**

* Soft limit: **one file ≤ 800 lines**.
* Split into modules when:

  * more than 10 endpoints in one file,
  * more than 5k characters of business logic.

### **4. Consistent async usage**

* All HTTP calls → `httpx.AsyncClient`
* All DB calls should preferably use an async ORM (SQLAlchemy 2.0 async or Tortoise).

### **5. Schema-first API design**

* Every route must specify:

  * request schema (`Pydantic BaseModel`)
  * response schema
* Avoid returning raw dictionaries.

---

## **Testing**

* Use **pytest** with FastAPI TestClient:

```python
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
```

* Add tests for:

  * route correctness
  * service logic (HF API mock)
  * error handling

At minimum: **smoke tests for critical routes**.

---

## **Error Handling**

FastAPI automatically converts exceptions to JSON, but standardize via custom handlers:

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)
```

**Rules:**

* Always return JSON for API endpoints.
* Use typed error models for predictable structure.
* Log errors in service layer, not in routes.

---

## **Example Route (FastAPI)**

```python
from fastapi import APIRouter, Depends
from app.schemas import UserOut
from app.services.users import get_user_service

router = APIRouter()

@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, svc=Depends(get_user_service)):
    """
    Fetch a user by ID using async service logic.
    """
    user = await svc.fetch_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

---

## **Example Service (async HF API call)**

```python
import httpx

class HFService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api-inference.huggingface.co/models/.../",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            r.raise_for_status()
            return r.json()
```

**Rules:**

* Services must have clear classes or functions.
* No global state — use dependency injection via FastAPI’s `Depends`.


