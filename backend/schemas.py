from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    turnstile_token: str = ""


class TurnstileRequest(BaseModel):
    turnstile_token: Optional[str] = ""


class ScoreRequest(BaseModel):
    image_id: int
    aesthetic_score: int
    completeness_score: int


class NextTaskRequest(BaseModel):
    turnstile_token: Optional[str] = ""
    current_task_id: Optional[int] = None


class TaskScoreRequest(BaseModel):
    image_id: int
    aesthetic_score: int
    completeness_score: int
