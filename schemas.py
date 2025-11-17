"""
Database Schemas for MagicBook

Each Pydantic model represents a MongoDB collection (lowercased class name).
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class StoryRequest(BaseModel):
    child_name: str = Field(..., description="Child's first name")
    age: int = Field(..., ge=1, le=12, description="Child's age (1-12)")
    theme: str = Field(..., description="Preferred universe/theme, e.g., pirates, space, jungle")
    tone: Optional[str] = Field("doux", description="Narrative tone: doux, aventureux, drôle, apaisant")
    language: str = Field("fr", description="Language code, e.g., fr or en")
    pages: int = Field(12, ge=6, le=20, description="Target number of pages for full book")

class StoryPage(BaseModel):
    page_number: int
    text: str
    image_url: str

class Story(BaseModel):
    title: str
    child_name: str
    age: int
    theme: str
    tone: str = "doux"
    language: str = "fr"
    pages: int
    variant: str = Field("preview", description="preview or full")
    price_cents: int = 1000
    pages_data: List[StoryPage]
