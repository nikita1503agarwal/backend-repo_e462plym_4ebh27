import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from schemas import StoryRequest, StoryPage
from database import create_document, get_documents, db

app = FastAPI(title="MagicBook API", description="Generate personalized illustrated stories for children")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"name": "MagicBook API", "message": "Backend running", "endpoints": ["/api/stories", "/test"]}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ------------------------
# MagicBook: Story Generator
# ------------------------

def _title_from(req: StoryRequest) -> str:
    themes = {
        "espace": "L'odyssée stellaire",
        "pirates": "Le trésor des vagues d'or",
        "jungle": "Le coeur de la forêt magique",
        "château": "Le secret du château arc-en-ciel",
    }
    base = themes.get(req.theme.lower(), "L'aventure merveilleuse")
    return f"{req.child_name} et {base}"


def _image_for(theme: str, page: int) -> str:
    seed = f"{theme}-{page}"
    return f"https://picsum.photos/seed/{seed}/960/640"


def _generate_pages(req: StoryRequest, total_pages: int) -> List[StoryPage]:
    name = req.child_name
    age = req.age
    theme = req.theme.lower()
    tone = req.tone or "doux"

    beats = [
        (
            1,
            f"{name}, {age} ans, adore l'univers {theme}. Un soir, une petite lueur vient chuchoter son prénom...",
        ),
        (
            2,
            f"La lueur ouvre un passage secret. {name} respire doucement, son coeur bat fort mais {tone}.",
        ),
        (
            3,
            f"De l'autre côté, un ami apparaît. Ensemble, ils découvrent une mission simple: écouter, aider et oser.",
        ),
        (
            4,
            f"Un petit défi arrive. {name} inspire, compte jusqu'à trois et trouve une idée lumineuse.",
        ),
        (
            5,
            f"Le monde {theme} s'illumine. Tout devient plus doux, plus coloré, et {name} sourit.",
        ),
        (
            6,
            f"La morale: avec gentillesse et courage, on grandit chaque jour, à son rythme.",
        ),
    ]

    pages: List[StoryPage] = []
    for i in range(1, total_pages + 1):
        base_idx = (i - 1) % len(beats)
        text = beats[base_idx][1]
        text = text.replace("{theme}", theme)
        page = StoryPage(
            page_number=i,
            text=text,
            image_url=_image_for(theme, i),
        )
        pages.append(page)
    return pages


@app.post("/api/stories")
def create_story(req: StoryRequest, variant: str = Query("preview", pattern="^(preview|full)$")):
    """Generate a personalized story and persist it. preview = ~3 pages, full = req.pages"""
    target_pages = 3 if variant == "preview" else max(6, min(req.pages, 20))
    pages = _generate_pages(req, target_pages)
    title = _title_from(req)

    doc = {
        "title": title,
        "child_name": req.child_name,
        "age": req.age,
        "theme": req.theme,
        "tone": req.tone or "doux",
        "language": req.language or "fr",
        "pages": target_pages,
        "variant": variant,
        "price_cents": 1000,
        "pages_data": [p.model_dump() for p in pages],
    }

    story_id = create_document("story", doc)
    doc["id"] = story_id
    return doc


@app.get("/api/stories")
def list_stories(limit: int = 20):
    docs = get_documents("story", {}, limit)
    result = []
    for d in docs:
        d["id"] = str(d.get("_id"))
        if "_id" in d:
            del d["_id"]
        result.append(d)
    return {"items": result}


@app.get("/api/stories/{story_id}")
def get_story(story_id: str):
    try:
        oid = ObjectId(story_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid story id")

    docs = get_documents("story", {"_id": oid}, limit=1)
    if not docs:
        raise HTTPException(status_code=404, detail="Story not found")
    doc = docs[0]
    doc["id"] = str(doc.get("_id"))
    if "_id" in doc:
        del doc["_id"]
    return doc


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
