from pydantic import BaseModel
from typing import Optional


class Sentence(BaseModel):
    """A single sentence segment with translation and timing."""
    en: str
    zh: str
    start: float
    end: float


class VideoInfo(BaseModel):
    """Metadata about an uploaded video."""
    id: str
    name: str
    duration: str
    status: str  # "已处理" | "处理中"


class ProcessResult(BaseModel):
    """Result of processing a video."""
    video_id: str
    sentences: list[Sentence]


class ScoreRequest(BaseModel):
    """Request to score a user recording."""
    sentence_index: int
    recording_path: str


class ScoreResult(BaseModel):
    """Scoring result for a single sentence."""
    pronunciation: float  # 0-100
    fluency: float       # 0-100
    timing: float         # 0-100
    overall: float        # 0-100


class PracticeSession(BaseModel):
    """A complete practice session for one video."""
    video_id: str
    video_name: str
    date: str
    sentences: int
    scores: Optional[list[ScoreResult]] = None


class HistoryItem(BaseModel):
    """History entry shown in the history page."""
    date: str
    video: str
    sentences: int
    score: float
