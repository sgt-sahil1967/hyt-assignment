"""Pydantic models: LLM extraction outputs + scorer outputs."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- LLM extraction (resume)
class Skill(BaseModel):
    name: str
    proficiency: Literal["used", "listed", "learning"]
    evidence: str = Field(description="verbatim span copied from the document that shows this skill")


class Role(BaseModel):
    title: str
    company_masked: str
    start: str = Field(description="as written, e.g. '2019', 'Mar 2019', 'Summer 2020'")
    end: str = Field(description="as written, e.g. '2021', 'Present'")
    is_internship: bool
    description_evidence: str = Field(description="verbatim bullet(s) under this role, may be empty")


class Project(BaseModel):
    name: str
    skills: list[str]
    evidence: str


class Education(BaseModel):
    degree_level: Literal["none", "diploma", "bachelor", "master", "phd", "other"]
    field: str
    year: Optional[int] = None


class ResumeExtraction(BaseModel):
    skills: list[Skill]
    roles: list[Role]
    projects: list[Project]
    education: list[Education]
    location: Optional[str] = None
    language: str = Field(description="ISO 639-1 code of the main language, e.g. 'en'")


# ---------------------------------------------------------------- LLM extraction (JD)
class Requirement(BaseModel):
    name: str = Field(description="short canonical name, e.g. 'python', 'ci/cd', 'computer science degree'")
    type: Literal["skill", "degree", "experience", "other"]
    alternatives: list[str] = Field(default_factory=list, description="concrete options when the JD gives examples (e.g. Docker, Kubernetes)")


class JDExtraction(BaseModel):
    title: str
    seniority: Literal["intern", "junior", "mid", "senior", "lead", "unspecified"]
    location: Optional[str] = None
    remote: bool
    must_have: list[Requirement]
    nice_to_have: list[Requirement]
    min_years: Optional[float] = None
    equivalent_experience_allowed: bool
    summary: str = Field(description="one sentence: what the role builds and with which core stack")


# ---------------------------------------------------------------- scorer outputs
class Evidence(BaseModel):
    requirement: str
    level: Literal["must", "nice"]
    matched_skill: Optional[str]
    strength: float
    basis: str  # used | listed | learning | taxonomy:<child> | embedding:<term> | missing
    quote: Optional[str] = None


class ScoreResult(BaseModel):
    job_id: str
    resume_id: str
    score: float
    components: dict[str, Optional[float]]
    evidence: list[Evidence]
    gaps: list[str]
    yoe: float
    yoe_confidence: Literal["high", "low"]
    capped: bool


class Decision(BaseModel):
    decision: Literal["advance", "escalate"]
    reasons: list[str]
    queue: Literal["advance", "review", "low_priority"]
