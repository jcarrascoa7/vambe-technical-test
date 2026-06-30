# Domain — Problem Definition and Business Logic

> This file defines **what** we're building and **why**. Read it before implementing
> any feature that touches categorization, metrics, or the dashboard.

---

## Project Context

### Challenge

Build an application that processes client data from sales meeting transcripts, automatically categorizes it using an LLM, and displays relevant metrics in an interactive dashboard.

### About Vambe

Vambe is a Chilean startup that automates customer service and sales processes via WhatsApp and Instagram, integrating CRM/ERP data for real-time revenue attribution. With over 1,700 implementations and 17% average monthly growth, it automates the entire commercial cycle from first interaction to closing, retention and support. Operates in ecommerce, health & beauty, appointment-based services, education, and finance.

### Available Data

CSV with 10,000 sales meeting records. Each record contains: name, email, phone, meeting date, assigned salesperson, whether the deal closed or not, and the full meeting transcription.

- **Closed**: 6,888 (~69%)
- **Not closed**: 3,112 (~31%)
- **Salespeople**: Toro, Puma, Zorro, Boa, Tiburón
- **Period**: 2024-01 to 2025-03

### Deliverables

Functional application with: data processing, LLM categorization, interactive dashboard with metrics, filters and search. Code on GitHub, README with instructions, architecture and decisions documentation.

---

## Guiding Principle

> **Every dimension, metric and visualization must answer a concrete business question for Vambe.** If no team decision improves with that information, it is not included.

This principle separates a useful dashboard from a decorative one. The business questions that guide the solution are:

1. **Where to focus?** → Which sectors and acquisition sources to prioritize
2. **Who to assign?** → Which salesperson performs best in which context
3. **What to prepare?** → Which needs, tones and uses dominate by sector
4. **How to qualify better?** → Which signals in the transcription predict closing

---

## Dimensions to Categorize

### Included Dimensions

| Dimension | Decision it improves | Justification | Example categories |
|---|---|---|---|
| **Sector/Industry** | Where to focus commercial and marketing efforts | Most strategic dimension: Vambe's ROI varies completely by vertical | Retail, Health, Education, Professional Services, Real Estate, Gastronomy, Fitness, Transport, Technology, Tourism, Automotive, Manufacturing, Finance/Insurance, NGO |
| **Business size** | Estimate ticket size and implementation complexity | Determines deal size: a micro client with 1 location has a different profile than a 12-branch chain | Micro (1 location, <10 employees), Small (2-3 locations), Medium (4-10 locations), Large (10+ locations) |
| **Monthly inquiry volume** | Validate value proposition and prioritize leads | Indicates client pain. A prospect with 5,000 inquiries/month has an urgent problem justifying investment | Low (<500), Medium (500-2,000), High (2,000-5,000), Very High (>5,000) |
| **Main contact channel** | Prioritize integrations and product development | Vambe's core is WhatsApp/Instagram. If most prospects mention WhatsApp, it validates the product focus | WhatsApp, Instagram, Phone, Email, Multi-channel |
| **Discovery source** | Optimize marketing investment and acquisition channels | If LinkedIn leads close at 75% and Google at 50%, the team should invest more in LinkedIn | LinkedIn, Google/Search, Recommendation, Event/Fair, Podcast/Webinar, Social Media, Advertising |
| **Required integrations** | Anticipate technical complexity and prioritize roadmap | If 40% of prospects ask for Salesforce integration, that's direct input for the product team | CRM, ERP, POS, LMS, Inventory, Booking system, Google Calendar |
| **Desired communication tone** | Parameterize chatbot from onboarding | Each client has a different brand. Capturing this early avoids post-implementation adjustments | Professional, Friendly/Casual, Sophisticated/Elegant, Technical, Fun/Young, Empathetic |
| **Main usage type** | Define product profile and priority features | Not all clients use Vambe for the same thing. If 60% need scheduling, that's the star feature | Scheduling, FAQ/Customer service, Lead qualification, Order tracking, Technical support |
| **Main pain mentioned** | Calibrate sales pitch by sector | If in education the dominant pain is "no-shows" but the team does demos focused on "message volume", the conversation doesn't engage | High message volume, Slow response, Lost leads/follow-up, Appointment no-shows, Lack of automation, Team saturation |
| **Language concreteness** | Qualify leads and prioritize follow-up | Analysis shows that prospects who close use concrete, actionable language; those who don't use tentative language | Concrete/Actionable (indicative mood, mentions past implementations, expresses urgency), Tentative/Exploratory (conditional mood, mentions "looking for", "would like"), Mixed |

### Discarded Dimensions

| Dimension | Reason for discard |
|---|---|
| **Dominant objection type** | Transcriptions are NOT objection conversations. They are discovery meetings where the prospect describes their business and needs. No classic objections. Regex detection gave 1.1% false positives |
| **B2B vs B2C** | Overlaps with "Sector" and "Size". Adds little incremental value and increases classification load |
| **Availability hours** | Mentioned in very few transcriptions explicitly. Can be partially inferred from sector |

### Nice-to-have Dimensions

| Dimension | Why it's optional |
|---|---|
| **General sentiment** | Weak signal in keyword analysis. LLM could detect subtler patterns, but cost/benefit unclear |
| **Perceived urgency** | Without close date in data (only binary closed/no), can't calculate close speed |
| **Budget signal** | Very subjective and hard to validate. Direct budget mentions appear in <0.2% of cases |
| **Detected closing signal** | Very subjective. Requires LLM to interpret intent, prone to error without cross-validation |

---

## Categories by Dimension

### Sector/Industry
- **Retail/Commerce** (stores, e-commerce, fashion, cosmetics, parts)
- **Health** (clinics, dental, veterinary, pharmacies, laboratories, mental health)
- **Education** (language schools, academies, universities, online courses, nurseries)
- **Professional Services** (consulting, legal, accounting, marketing, HR)
- **Real Estate/Construction**
- **Gastronomy** (restaurants, catering, bakeries, delivery)
- **Fitness/Wellness** (gyms, yoga, spa, wellness)
- **Transport/Logistics** (distribution, courier, freight)
- **Technology/Software** (SaaS, e-commerce platforms, streaming)
- **Tourism/Hotels** (hotels, travel agencies, adventure tourism)
- **Automotive Services** (workshops, dealerships, parts)
- **Manufacturing/Industry** (parts, machinery, food)
- **Financial Services/Insurance** (insurance, tax, accounting)
- **NGO/Non-profit**
- **Entertainment** (cinema, streaming, events)
- **Home/Services** (cleaning, maintenance, gardening)
- **Other**

### Business Size
- **Micro** (1 location, <10 employees)
- **Small** (2-3 locations, 10-50 employees)
- **Medium** (4-10 locations, 50-200 employees)
- **Large** (10+ locations, 200+ employees)

### Monthly Inquiry Volume
- **Low** (<500/month)
- **Medium** (500-2,000/month)
- **High** (2,000-5,000/month)
- **Very High** (>5,000/month)

### Discovery Source
- LinkedIn, Google/Search, Recommendation/Referral, Event/Fair, Podcast/Webinar, Social Media, Advertising, Other

### Main Channel
- WhatsApp, Instagram, Phone, Email, Multi-channel

### Integrations
- CRM (Salesforce, HubSpot, other), ERP, POS, LMS, Inventory, Booking system, Google Calendar, GPS/Tracking, Other

### Communication Tone
- Professional, Friendly/Casual, Sophisticated/Elegant, Technical, Fun/Young, Empathetic/Warm

### Main Usage Type
- Scheduling, FAQ/Customer service, Lead qualification, Order tracking, Technical support, Conversational marketing

### Main Pain
- High message volume, Slow response, Lost leads/follow-up, Appointment no-shows, Lack of automation, Team saturation, No 24/7 availability

### Language Concreteness
- **Concrete/Actionable**: Speaks in indicative mood, mentions past implementations, expresses urgency, gives specific numbers
- **Tentative/Exploratory**: Speaks in conditional ("would like", "might need"), mentions "looking for", "evaluating", no clear commitment
- **Mixed**: Combines elements of both

---

## Metrics

### Data Exclusion Rule

> **Records with `"Not specified"` in any categorization dimension must be excluded from metric calculations that depend on that dimension.**

This applies to all metrics below. Examples:
- `size = "Not specified"` → excluded from close-rate-by-size calculations
- `inquiry_volume = "Not specified"` → excluded from average volume calculations
- `concreteness = "Not specified"` → excluded from close-rate-by-concreteness
- Records where `categorized = false` → excluded from all metrics (they haven't been processed yet)

Records excluded from one dimension may still be included in metrics that don't depend on that dimension. For example, a record with `size = "Not specified"` is still valid for `close-rate-by-sector` if its `sector` is valid.

### Included Metrics

| Metric | Decision it improves | Calculation |
|---|---|---|
| **Close rate by sector** | Where to focus commercial efforts | `closed=1 by sector / total by sector` |
| **Close rate by vendor × industry** | Who to assign each lead to | `closed=1 by (vendor, sector) / total by (vendor, sector)` |
| **Close rate by acquisition source** | Where to invest in marketing | `closed=1 by source / total by source` |
| **Main pain distribution by sector** | Calibrate sales pitch by vertical | `count(pain) by sector` |
| **Close rate by language concreteness** | Qualify leads in real time | `closed=1 by concreteness level / total by level` |
| **Sector distribution** | Understand current portfolio mix | `count by sector / total` |
| **Average monthly inquiry volume by sector** | Validate value proposition by vertical | `avg(inquiry_volume) by sector` |
| **Requested integrations distribution** | Prioritize technical roadmap | `count of each integration` |
| **Close rate by main channel** | Validate product core | `closed=1 by channel / total by channel` |
| **Temporal evolution of leads and closes** | Evaluate growth and efficiency trend | `leads by month`, `closes by month`, `rate by month` |
| **Top sectors by volume × close rate** | Identify "sweet spots" | `avg_volume * close_rate by sector` |

### Discarded Metrics

| Metric | Reason for discard |
|---|---|
| **Close rate by objection type** | Data doesn't contain classic sales objections |
| **Close rate by sentiment** | Weak keyword signal. "Concreteness" dimension captures the difference better |
| **Close speed by urgency** | Dataset only has binary closed/no, no close date |

---

## Visualizations

| Visualization | Type | Question it answers |
|---|---|---|
| **Top KPIs** | Cards with large numbers | Global context: total close rate, total leads, top sector, top vendor |
| **Close rate by sector** | Sorted horizontal bars | Which verticals should the commercial team focus on? |
| **Vendor × industry heatmap** | Color intensity heatmap | Which vendor performs best in which sector? Dark squares = winning combinations; light = missed opportunities |
| **Main pain distribution by sector** | 100% stacked bars | Does the pain profile vary by sector? Orient sales materials and demos per vertical |
| **Sector distribution** | Donut chart | How diversified is the current portfolio? |
| **Close rate by source** | Bars with reference line (global rate) | Which acquisition channels work best? |
| **Close rate by concreteness** | Bars with highlighted gap | Does concrete language predict close? If the gap is large, it becomes a real-time qualification signal |
| **Temporal evolution** | Double line (leads + closes/month) | Are we improving? Growth and commercial efficiency trend |
| **Top requested integrations** | Treemap or horizontal bars | Which integrations to prioritize on the technical roadmap? |
| **Scatter volume × close rate** | Scatter plot with labeled sectors | Do sectors with more pain close more? Validates the value proposition |
| **Detail table** | Filterable and searchable table | Explore individual prospect data |

---

## Search and Filters

### Free text search
- **Client name**: Search "Carlos" to see all Carlos
- **Email**: Search by specific email
- **Transcription**: Search keywords like "WhatsApp", "Salesforce", "24/7" to find clients with specific needs

### Filters by categorized dimension (dropdown/multiselect)
- **Sector**: Retail, Health, Education, Fitness...
- **Size**: Micro, Small, Medium, Large
- **Inquiry volume**: Low, Medium, High, Very High
- **Acquisition source**: LinkedIn, Google, Recommendation...
- **Main channel**: WhatsApp, Instagram, Phone...
- **Desired tone**: Professional, Friendly, Sophisticated...
- **Main usage**: Scheduling, FAQ, Leads, Orders...
- **Required integration**: CRM, ERP, POS, LMS, Salesforce...
- **Main pain**: Volume, Slow response, No-shows, Saturation...
- **Concreteness**: Concrete, Tentative, Mixed

### Filters by original data
- **Assigned vendor**: Multiselect dropdown
- **Closed**: Toggle (Yes/No/All)
- **Date range**: Date picker
- **Inquiry volume range**: Numeric slider

### Filter combination

Filters are **combinable**. Real usage example:

> *"Show me leads from the Health sector, coming from LinkedIn, with high inquiry volume, that didn't close, assigned to Toro"*

This would identify patterns like: "Toro doesn't close well in Health with LinkedIn leads — does he need training?"
