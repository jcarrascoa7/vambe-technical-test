"""Structured prompts for LLM categorization of sales meeting transcripts."""

VALID_CATEGORIES = {
    "sector": [
        "Retail/Commerce",
        "Health",
        "Education",
        "Professional Services",
        "Real Estate/Construction",
        "Gastronomy",
        "Fitness/Wellness",
        "Transport/Logistics",
        "Technology/Software",
        "Tourism/Hotels",
        "Automotive Services",
        "Manufacturing/Industry",
        "Financial Services/Insurance",
        "NGO/Non-profit",
        "Entertainment",
        "Home/Services",
        "Other",
    ],
    "size": ["Micro", "Small", "Medium", "Large", "Not specified"],
    "inquiry_volume": ["Low", "Medium", "High", "Very High", "Not specified"],
    "channel": ["WhatsApp", "Instagram", "Phone", "Email", "Multi-channel"],
    "source": [
        "LinkedIn",
        "Google/Search",
        "Recommendation/Referral",
        "Event/Fair",
        "Podcast/Webinar",
        "Social Media",
        "Advertising",
        "Other",
    ],
    "integrations": [
        "CRM",
        "ERP",
        "POS",
        "LMS",
        "Inventory",
        "Booking system",
        "Google Calendar",
        "GPS/Tracking",
        "Other",
    ],
    "tone": [
        "Professional",
        "Friendly/Casual",
        "Sophisticated/Elegant",
        "Technical",
        "Fun/Young",
        "Empathetic/Warm",
    ],
    "usage_type": [
        "Scheduling",
        "FAQ/Customer service",
        "Lead qualification",
        "Order tracking",
        "Technical support",
        "Conversational marketing",
    ],
    "pain": [
        "High message volume",
        "Slow response",
        "Lost leads/follow-up",
        "Appointment no-shows",
        "Lack of automation",
        "Team saturation",
        "No 24/7 availability",
    ],
    "concreteness": [
        "Concrete/Actionable",
        "Tentative/Exploratory",
        "Mixed",
        "Not specified",
    ],
}

# Map inquiry_volume bucket to a representative integer for metric calculations.
# Used by the API layer when computing averages (e.g. avg-volume-by-sector).
# "Not specified" records should be excluded before applying this map.
INQUIRY_VOLUME_MAP = {
    "Low": 250,
    "Medium": 1250,
    "High": 3500,
    "Very High": 7500,
}


def _format_categories() -> str:
    lines = []
    for dim, cats in VALID_CATEGORIES.items():
        lines.append(f"  {dim}: {cats}")
    return "\n".join(lines)


DIMENSION_DEFINITIONS = """
## Dimension Definitions

### size
Estimate primarily by number of locations/branches. If not mentioned, use employee count.
- **Micro**: 1 location, <10 employees
- **Small**: 2-3 locations, 10-50 employees
- **Medium**: 4-10 locations, 50-200 employees
- **Large**: 10+ locations, 200+ employees

### inquiry_volume
Monthly inquiries the prospect reports receiving. Use the number they mention.
- **Low**: <500/month
- **Medium**: 500-2,000/month
- **High**: 2,000-5,000/month
- **Very High**: >5,000/month

### concreteness
How committed the prospect sounds in the transcription.
- **Concrete/Actionable**: Speaks in indicative mood, mentions past implementations, expresses urgency, gives specific numbers
- **Tentative/Exploratory**: Uses conditional ("would like", "might need"), says "looking for", "evaluating", no clear commitment
- **Mixed**: Combines elements of both

### pain
Pick the single most prominent pain the prospect describes. If multiple, pick the one they emphasize most.
- **High message volume**: Explicitly mentions too many messages/inquiries
- **Slow response**: Mentions delays, not responding fast enough
- **Lost leads/follow-up**: Mentions losing prospects, not following up
- **Appointment no-shows**: Mentions clients not showing up to appointments
- **Lack of automation**: Mentions doing things manually, repetitive tasks
- **Team saturation**: Mentions team overwhelmed, overworked staff
- **No 24/7 availability**: Mentions needing coverage outside business hours
""".strip()


def build_categorization_prompt(transcription: str) -> str:
    """Build a structured prompt that asks the LLM to extract all 10 dimensions.

    Returns a prompt string ready to send to the LLM.
    """
    categories_block = _format_categories()

    return f"""You are a sales meeting analyst. Given a sales meeting transcription, categorize the prospect across 10 dimensions.

## Valid Categories (you MUST pick exactly from these lists)

{categories_block}

{DIMENSION_DEFINITIONS}

## Few-shot Example

**Transcription:**
"Hola, somos una clínica dental con 3 sedes en Santiago. Recibimos como 3000 consultas al mes por WhatsApp y redes. Nos encontraron en Google. Usamos HubSpot como CRM y necesitamos agendar citas automáticamente. Queremos un tono profesional pero cercano. El principal problema es que perdemos leads porque no damos abasto."

**Expected output:**
```json
{{
  "sector": "Health",
  "size": "Small",
  "inquiry_volume": "High",
  "channel": "WhatsApp",
  "source": "Google/Search",
  "integrations": "CRM",
  "tone": "Friendly/Casual",
  "usage_type": "Scheduling",
  "pain": "Lost leads/follow-up",
  "concreteness": "Concrete/Actionable"
}}
```

**Reasoning:**
- size: "3 sedes" → Small (2-3 locations)
- inquiry_volume: "3000 consultas" → High (2,000-5,000/month)
- pain: "perdemos leads porque no damos abasto" → Lost leads/follow-up
- concreteness: mentions specific numbers (3 sedes, 3000 consultas), specific tool (HubSpot), clear urgency → Concrete/Actionable

## Your Task

Analyze the following transcription and return ONLY a JSON object with exactly these 10 keys: sector, size, inquiry_volume, channel, source, integrations, tone, usage_type, pain, concreteness. Pick each value EXACTLY from the valid categories above. Do NOT add any explanation, only the JSON.

**Transcription:**
{transcription}

**Output (JSON only):**"""
