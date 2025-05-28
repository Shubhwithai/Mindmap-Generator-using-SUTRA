from fastapi import FastAPI, APIRouter, HTTPException, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import json
from openai import AsyncOpenAI
import csv
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class FlashCard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    front: str
    back: str
    topic: str
    language: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FlashCardDeck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    topic: str
    language: str
    cards: List[FlashCard]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GenerateCardsRequest(BaseModel):
    topic: str
    language: str
    count: int = 5
    sutra_api_key: str

class GenerateCardsResponse(BaseModel):
    deck: FlashCardDeck
    success: bool
    message: str

class ExportRequest(BaseModel):
    deck_ids: List[str] = []  # Empty means export all decks
    format: str = "json"  # json, csv, pdf

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Multilingual Flash Card Generator API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/test-sutra")
async def test_sutra_api(request: dict):
    """Test the Sutra API connection"""
    try:
        sutra_api_key = request.get("api_key")
        if not sutra_api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        client_sutra = AsyncOpenAI(
            api_key=sutra_api_key,
            base_url='https://api.two.ai/v2',
        )

        response = await client_sutra.chat.completions.create(
            model='sutra-v2',
            messages=[{ 
                'role': 'user', 
                'content': 'मुझे केवल एक वाक्य में उत्तर दें: आप कैसे हैं?' 
            }],
            max_tokens=50,
            temperature=0
        )

        return {
            "success": True,
            "message": "Sutra API connection successful",
            "test_response": response.choices[0].message.content
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Sutra API connection failed: {str(e)}"
        }

@api_router.post("/generate-cards", response_model=GenerateCardsResponse)
async def generate_flash_cards(request: GenerateCardsRequest):
    """Generate flash cards using Sutra API"""
    try:
        client_sutra = AsyncOpenAI(
            api_key=request.sutra_api_key,
            base_url='https://api.two.ai/v2',
        )

        # Create prompt for generating flash cards with updated language support
        language_instruction = {
            "english": "in English",
            "hindi": "हिंदी में",
            "spanish": "en español", 
            "french": "en français",
            "german": "auf Deutsch",
            "chinese": "用中文",
            "japanese": "日本語で",
            "arabic": "بالعربية",
            "gujarati": "ગુજરાતી માં",
            "marathi": "मराठी मध्ये"
        }.get(request.language.lower(), "in English")

        prompt = f"""Create {request.count} educational flash cards about "{request.topic}" {language_instruction}. 

Please respond with a JSON array where each object has:
- "front": A key term, concept, or question
- "back": A detailed explanation, definition, or answer

Format your response as valid JSON only, no additional text:
[
  {{"front": "term/concept", "back": "detailed explanation"}},
  {{"front": "term/concept", "back": "detailed explanation"}}
]"""

        response = await client_sutra.chat.completions.create(
            model='sutra-v2',
            messages=[{ 
                'role': 'user', 
                'content': prompt
            }],
            max_tokens=1024,
            temperature=0.7
        )

        # Parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Look for JSON array in the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                json_content = content[start_idx:end_idx]
                cards_data = json.loads(json_content)
            else:
                # Fallback: treat entire content as JSON
                cards_data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: create cards from text response
            lines = content.split('\n')
            cards_data = []
            for i in range(0, min(len(lines), request.count * 2), 2):
                if i + 1 < len(lines):
                    front = lines[i].strip().lstrip('- ').lstrip('• ')
                    back = lines[i + 1].strip().lstrip('- ').lstrip('• ')
                    if front and back:
                        cards_data.append({"front": front, "back": back})

        # Create FlashCard objects
        cards = []
        for card_data in cards_data[:request.count]:
            card = FlashCard(
                front=card_data.get("front", ""),
                back=card_data.get("back", ""),
                topic=request.topic,
                language=request.language
            )
            cards.append(card)

        # Create deck
        deck = FlashCardDeck(
            name=f"{request.topic} - {request.language.title()}",
            topic=request.topic,
            language=request.language,
            cards=cards
        )

        # Save to database
        await db.flash_decks.insert_one(deck.dict())

        return GenerateCardsResponse(
            deck=deck,
            success=True,
            message=f"Successfully generated {len(cards)} flash cards"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating cards: {str(e)}")

@api_router.get("/decks", response_model=List[FlashCardDeck])
async def get_all_decks():
    """Get all flash card decks"""
    decks = await db.flash_decks.find().to_list(1000)
    return [FlashCardDeck(**deck) for deck in decks]

@api_router.get("/decks/{deck_id}", response_model=FlashCardDeck)
async def get_deck(deck_id: str):
    """Get a specific deck by ID"""
    deck = await db.flash_decks.find_one({"id": deck_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return FlashCardDeck(**deck)

@api_router.delete("/decks/{deck_id}")
async def delete_deck(deck_id: str):
    """Delete a deck"""
    result = await db.flash_decks.delete_one({"id": deck_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Deck not found")
    return {"message": "Deck deleted successfully"}

@api_router.post("/export")
async def export_decks(request: ExportRequest):
    """Export flash card decks in various formats"""
    try:
        # Get decks to export
        if request.deck_ids:
            # Export specific decks
            decks_data = []
            for deck_id in request.deck_ids:
                deck = await db.flash_decks.find_one({"id": deck_id})
                if deck:
                    decks_data.append(deck)
        else:
            # Export all decks
            decks_data = await db.flash_decks.find().to_list(1000)

        if not decks_data:
            raise HTTPException(status_code=404, detail="No decks found to export")

        # Convert to FlashCardDeck objects
        decks = [FlashCardDeck(**deck) for deck in decks_data]

        if request.format.lower() == "json":
            return export_to_json(decks)
        elif request.format.lower() == "csv":
            return export_to_csv(decks)
        elif request.format.lower() == "pdf":
            return export_to_pdf(decks)
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

def export_to_json(decks: List[FlashCardDeck]):
    """Export decks to JSON format"""
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "total_decks": len(decks),
        "total_cards": sum(len(deck.cards) for deck in decks),
        "decks": [deck.dict() for deck in decks]
    }
    
    json_content = json.dumps(export_data, indent=2, default=str)
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=flashcards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
    )

def export_to_csv(decks: List[FlashCardDeck]):
    """Export decks to CSV format"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Deck Name', 'Topic', 'Language', 'Card Front', 'Card Back', 'Created Date'])
    
    # Write data
    for deck in decks:
        for card in deck.cards:
            writer.writerow([
                deck.name,
                deck.topic,
                deck.language,
                card.front,
                card.back,
                card.created_at.strftime('%Y-%m-%d %H:%M:%S') if card.created_at else ''
            ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=flashcards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

def export_to_pdf(decks: List[FlashCardDeck]):
    """Export decks to PDF format"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=24, spaceAfter=30)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading1'], fontSize=16, spaceAfter=12)
    front_style = ParagraphStyle('CardFront', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', spaceAfter=6)
    back_style = ParagraphStyle('CardBack', parent=styles['Normal'], fontSize=10, spaceAfter=12)
    
    story = []
    
    # Add title
    story.append(Paragraph("Flash Cards Export", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"Total Decks: {len(decks)}", styles['Normal']))
    story.append(Paragraph(f"Total Cards: {sum(len(deck.cards) for deck in decks)}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Add each deck
    for deck_idx, deck in enumerate(decks):
        if deck_idx > 0:
            story.append(PageBreak())
        
        # Deck header
        story.append(Paragraph(f"Deck: {deck.name}", heading_style))
        story.append(Paragraph(f"Topic: {deck.topic} | Language: {deck.language.title()}", styles['Normal']))
        story.append(Paragraph(f"Cards: {len(deck.cards)}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Add cards
        for card_idx, card in enumerate(deck.cards):
            story.append(Paragraph(f"Card {card_idx + 1}:", styles['Heading2']))
            story.append(Paragraph(f"Front: {card.front}", front_style))
            story.append(Paragraph(f"Back: {card.back}", back_style))
            story.append(Spacer(1, 8))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=flashcards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
