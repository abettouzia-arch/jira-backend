## Jira Migration Platform - Backend Architecture & API Documentation

### Project Overview

This is a microservices-based platform designed to analyze **Jira Data Center (DC)** instances and assess their migration compatibility to **Jira Cloud**.

**Key Capabilities:**
- Parsing Jira exports (ZIP exports with XML, Groovy scripts, database dumps)
- Compatibility analysis using rules + AI + RAG (Retrieval-Augmented Generation)
- Knowledge-based enrichment via RAG with ChromaDB
- AI-powered migration reports (JSON + PDF formats)
- Full pipeline orchestration via Worker service
- Secure JWT-authenticated API via Gateway

---

## Architecture

### Service Architecture

```
Client → Gateway (JWT Auth + Routing)
         ↓
         ├→ Worker (Orchestrator)
         │   ├→ Parsing Service
         │   ├→ Compatibility Service
         │   ├→ Knowledge Service (RAG)
         │   └→ Report Service
         │
         ├→ Get Job Status
         └→ Get Report Results
```

### Microservices

| Service | Port | Responsibility |
|---------|------|-----------------|
| **gateway** | 5000 | Entry point, JWT authentication, request routing |
| **parsing_service** | 5001 | Parse Jira exports, extract components, users, projects, issues |
| **compatibility_service** | 5002 | Analyze component compatibility (rules + AI + RAG) |
| **knowledge_service** | 5003 | RAG system (ChromaDB vector store, embeddings, document indexing) |
| **report_service** | 5004 | Generate JSON/PDF migration reports with AI summaries |
| **worker** | 5005 | Orchestrate full analysis pipeline, job management |

### Infrastructure

| Component | Technology | Port/Volume |
|-----------|-----------|-------------|
| Database | MongoDB | 27017 / mongo_data |
| Cache/Queue | Redis | 6379 / redis_data |
| Vector DB | ChromaDB | (embedded) / knowledge_chroma_data |
| LLM Models | Ollama | 11434 / ollama_data |
| AI API | Google Gemini 2.5 Flash | - |
| Report Storage | Local Filesystem | report_generated_files |

---

## Full Pipeline Flow

### Analysis Workflow

**Step 1: Upload & Parse**
```
POST /api/analyze (JWT required)
  ↓
  Gateway → Worker
  ↓
  Parser Service extracts:
    - Users, Projects, Issues (from XML)
    - Groovy scripts features (via AI feature detector)
    - Database dump components
  ↓
  Save to MongoDB (analyses collection)
```

**Step 2: Analyze for Compatibility**
```
Compatibility Service loads components
  ↓
  Hybrid Analysis Engine:
    1. Rule-based deterministic checks
    2. RAG enrichment (knowledge base lookup)
    3. AI reasoning (Gemini reasoning)
    4. Result merger (conservative scoring)
  ↓
  Save compatibility matrix to MongoDB (compatibility_matrices collection)
```

**Step 3: Generate Report**
```
Report Service builds structured report:
  - Executive summary (AI-generated)
  - Risk overview
  - Blockers & recommendations
  - Component-level analysis
  - Migration score
  ↓
  Export to JSON + PDF
  Save to MongoDB (reports collection)
```

---

## API Endpoints

### Authentication

**Login (Get JWT Token)**
```
POST /api/login
Content-Type: application/json

Body:
{
  "email": "admin@test.com",
  "password": "1234"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Default Credentials:**
- Email: `admin@test.com`
- Password: `1234`

All subsequent requests require: `Authorization: Bearer <token>`

---

### Pipeline Endpoints

#### **1. Trigger Full Analysis**
```
POST /api/analyze
Authorization: Bearer <token>
Content-Type: multipart/form-data

Body:
  file: <.zip export from Jira DC>

Response (202 or immediate):
{
  "analysis_id": "uuid",
  "source_environment": "Jira Data Center",
  "target_environment": "Jira Cloud",
  "analysis_date": "2026-05-07",
  "components": [...],
  "raw_stats": {
    "user_count": 42,
    "project_count": 5,
    "issue_count": 1250
  }
}
```

---

### Job Management

#### **2. Get Job Status**
```
GET /api/jobs/<job_id>
Authorization: Bearer <token>

Response:
{
  "job_id": "uuid",
  "job_type": "FULL_ANALYSIS",
  "status": "RUNNING" | "COMPLETED" | "FAILED" | "QUEUED",
  "created_at": "2026-05-07T10:00:00",
  "started_at": "2026-05-07T10:00:15",
  "completed_at": null,
  "error": null,
  "result": {}
}
```

#### **3. List Jobs**
```
GET /api/jobs?limit=50
Authorization: Bearer <token>

Response:
{
  "job_1": {...},
  "job_2": {...}
}
```

---

### Report Endpoints

#### **4. Get Report**
```
GET /api/reports/<report_id>
Authorization: Bearer <token>

Response:
{
  "report_id": "uuid",
  "matrix_id": "uuid",
  "analysis_id": "uuid",
  "title": "Jira DC to Cloud Migration Report",
  "generated_at": "2026-05-07T10:05:00",
  "summary": "AI-generated executive summary...",
  "migration_score": 0.78,
  "migration_recommendation": "Proceed with migration",
  "sections": {
    "executive_summary": "...",
    "risk_overview": "...",
    "blockers": [...],
    "recommendations": [...]
  }
}
```

#### **5. Export Report as JSON**
```
GET /api/reports/<report_id>/json
Authorization: Bearer <token>

Response: File download (application/json)
```

#### **6. Export Report as PDF**
```
GET /api/reports/<report_id>/pdf
Authorization: Bearer <token>

Response: File download (application/pdf)
```

---

## Data Models

### Analysis
```json
{
  "analysis_id": "uuid",
  "source_environment": "Jira Data Center",
  "target_environment": "Jira Cloud",
  "analysis_date": "2026-05-07",
  "components": [
    {
      "component_id": "GRV-abc123",
      "component_type": "workflow_validator | post_function | listener | script",
      "plugin": "ScriptRunner | JSU | native | MISC",
      "features_detected": ["java_api", "database_query", ...],
      "source_code": "...",
      "location": {
        "workflow": "Optional workflow name",
        "transition": "Optional transition",
        "file_path": "path_from_export"
      }
    }
  ],
  "raw_stats": {
    "user_count": 42,
    "project_count": 5,
    "issue_count": 1250
  }
}
```

### Compatibility Matrix
```json
{
  "matrix_id": "uuid",
  "analysis_id": "uuid",
  "analyzed_at": "2026-05-07T10:05:00",
  "components": [
    {
      "component_id": "GRV-abc123",
      "final_status": "COMPATIBLE | PARTIAL | DEPRECATED | NEEDS_REVIEW | REWRITE_REQUIRED | INCOMPATIBLE",
      "final_risk": "INFO | MINOR | MAJOR | BLOCKER",
      "confidence": 0.85,
      "reasoning_summary": "...",
      "recommended_action": "...",
      "evidence": [...],
      "ai_reasoning": {
        "used": true,
        "ai_status": "...",
        "ai_risk": "...",
        "ai_confidence": 0.90
      }
    }
  ],
  "summary": {
    "total_components": 42,
    "compatible_count": 28,
    "partial_count": 8,
    "incompatible_count": 6,
    "migration_score": 0.78,
    "migration_recommendation": "Proceed with migration"
  }
}
```

### Report
```json
{
  "report_id": "uuid",
  "matrix_id": "uuid",
  "analysis_id": "uuid",
  "title": "Jira DC to Cloud Migration Report",
  "generated_at": "2026-05-07T10:05:00",
  "summary": "AI executive summary",
  "migration_score": 0.78,
  "migration_recommendation": "Proceed with migration",
  "statistics": { /* from matrix summary */ },
  "sections": {
    "executive_summary": "...",
    "risk_overview": "...",
    "blockers": [...],
    "components": [...],
    "recommendations": [...]
  },
  "raw_matrix": {
    "matrix_id": "uuid",
    "analysis_id": "uuid"
  }
}
```

---

## Technology Stack

### Backend Framework
- **Flask**: Lightweight Python web framework for each microservice
- **Flask-CORS**: Cross-origin request handling
- **Flask-JWT-Extended**: JWT-based authentication
- **Flask-PyMongo**: MongoDB integration

### Database & Storage
- **MongoDB**: Persistent data (analyses, compatibility_matrices, reports, jobs)
- **ChromaDB**: Vector database for RAG (document embeddings, semantic search)
- **Redis**: Caching and async task queue (prepared for future scaling)

### AI & NLP
- **Google Gemini 2.5 Flash**: AI reasoning, report summaries, feature detection
- **Ollama**: Local LLM models (optional add-on)
- **Pydantic**: Data validation and serialization

### Document Processing
- **Groovy Parser**: Detects Java API features in Groovy scripts
- **XML Parser**: Extracts entities from Jira XML exports
- **ReportLab**: PDF report generation

### Containerization
- **Docker**: Containerization of all services
- **Docker Compose**: Orchestration of multi-container setup

---

## Project Structure

```
jira-migration-backend/
├── docker-compose.yml           # Service orchestration
├── Dockerfile                   # Multi-stage build for all services
├── requirements.txt             # Python dependencies
│
├── gateway/                     # API Gateway
│   └── app.py
│
├── parsing_service/             # Jira export parser
│   ├── app.py
│   ├── parsers/
│   │   ├── xml_parser.py
│   │   ├── groovy_parser.py
│   │   ├── dump_parser.py
│   │   └── zip_handler.py
│   └── utils/
│
├── compatibility_service/       # Compatibility analyzer
│   ├── app.py
│   └── engine/
│       ├── hybrid_engine.py     # Rules + AI + RAG merger
│       ├── rule_engine.py       # Deterministic rules
│       ├── ai_reasoner.py       # Gemini AI integration
│       ├── rag_client.py        # RAG/ChromaDB lookup
│       ├── result_merger.py     # Conservative result merging
│       ├── matrix.py            # Compatibility matrix builder
│       └── rules/
│           ├── jsu_rules.py
│           ├── scriptrunner_rules.py
│           └── misc_rules.py
│
├── knowledge_service/           # RAG system
│   ├── app.py
│   ├── indexer/
│   │   ├── document_loader.py
│   │   ├── chunker.py
│   │   └── embedder.py
│   ├── retriever/
│   │   └── search.py
│   └── docs/                    # Knowledge base documents
│
├── report_service/              # Report generation
│   ├── app.py
│   ├── generators/
│   │   ├── report_builder.py
│   │   ├── json_export.py
│   │   └── pdf_export.py
│   └── llm/
│       ├── gemini_client.py
│       └── prompt_builder.py
│
├── worker/                      # Pipeline orchestrator
│   ├── app.py
│   └── tasks/
│       ├── analysis_task.py
│       └── job_manager.py
│
├── shared/                      # Code reuse across services
│   ├── core/
│   │   ├── config.py            # Centralized configuration
│   │   ├── extensions.py        # Flask extensions
│   │   ├── errors.py            # Error handlers
│   │   └── logger.py            # Logging setup
│   ├── db/
│   │   └── mongo_client.py      # MongoDB connection
│   ├── repositories/            # Data access layer
│   │   ├── analysis_repository.py
│   │   ├── job_repository.py
│   │   ├── report_repository.py
│   │   └── compatibility_repository.py
│   ├── schemas/                 # Pydantic validation schemas
│   │   ├── parsed_data_schema.py
│   │   ├── job_schema.py
│   │   ├── report_schema.py
│   │   └── base_schema.py
│   ├── models/                  # Domain models (dataclasses)
│   │   ├── analysis_job.py
│   │   ├── compatibility_result.py
│   │   ├── parsed_data.py
│   │   ├── report.py
│   │   └── user.py
│   └── utils/
│       ├── helpers.py           # Document serialization, ObjectId handling
│       └── validators.py        # UUID, required fields validation
│
├── scripts/
│   └── export_feature_dataset.py
│
├── temp_uploads/                # Temporary file storage
└── knowledge_service/chroma_db/ # ChromaDB persistence
```

---

## Environment Configuration

### Docker Environment Variables

All services use these variables (defined in `.env`):

```
# Database
MONGO_URI=mongodb://mongodb:27017/jira_migration
REDIS_URL=redis://redis:6379

# AI
GEMINI_API_KEY=<your-gemini-key>
OLLAMA_URL=http://ollama:11434

# Service URLs (internal)
PARSING_SERVICE_URL=http://parsing_service:5001
COMPATIBILITY_SERVICE_URL=http://compatibility_service:5002
KNOWLEDGE_SERVICE_URL=http://knowledge_service:5003
REPORT_SERVICE_URL=http://report_service:5004
WORKER_URL=http://worker:5005

# JWT
JWT_SECRET_KEY=<your-secret-key>

# Flask
FLASK_ENV=production
DEBUG=false

# Other
ANONYMIZED_TELEMETRY=false
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
```

---

## How to Run

### Using Docker Compose

```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env with your API keys

# 2. Build and start all services
docker-compose up -d

# 3. Services will be available at:
#    - API Gateway: http://docker.itspectrum.fr:88 (or localhost:88)
#    - Mongo Express: http://localhost:8081

# 4. Test health
curl http://localhost:88/api/health
```

### Volumes (Data Persistence)

- `mongo_data`: MongoDB persistence
- `ollama_data`: Ollama models
- `redis_data`: Redis data
- `knowledge_chroma_data`: ChromaDB persistence
- `report_generated_files`: Generated JSON/PDF reports

---

## Authentication Flow

1. **Login**: `POST /api/login` → Get JWT token
2. **Store Token**: Save in localStorage/session
3. **Use Token**: Add `Authorization: Bearer <token>` to all requests
4. **Token Expires**: After 8 hours (configurable in gateway config)

---

## Shared Library Usage

To maintain consistency across services, the **shared/** folder provides:

- **Repositories**: `AnalysisRepository`, `JobRepository`, `ReportRepository`, `CompatibilityRepository`
- **Schemas**: Pydantic models for validation (ParsedJiraData, JobModel, ReportModel)
- **Models**: Domain dataclasses for type safety
- **Utils**: Helper functions (serialize_document, is_valid_uuid, etc.)
- **Core**: Config, logging, error handlers, extensions

All services import from `shared/` instead of duplicating code.

---

## Key Features for Frontend

### 1. Job Status Tracking
Jobs can be QUEUED, RUNNING, COMPLETED, or FAILED. Frontend should poll `/api/jobs/<job_id>` to track progress.

### 2. Error Handling
All endpoints return standard JSON errors:
```json
{
  "error": "Human-readable error message"
}
```
HTTP status codes: 400 (bad request), 404 (not found), 500 (server error), 502 (service error)

### 3. Large File Uploads
The `/api/analyze` endpoint accepts multipart/form-data. For better UX:
- Show upload progress
- Implement retry logic
- Set timeout to 180+ seconds

### 4. Report Exports
Reports can be exported as JSON (lightweight) or PDF (formatted). Store report_id to retrieve later.

### 5. Authentication
JWT tokens are short-lived (8 hours). Implement token refresh or re-login flow.

---

## Example Frontend Workflow

```
1. User Login
   POST /api/login → Get token

2. User Uploads File
   POST /api/analyze (with file) → Get job_id

3. Poll Job Status
   GET /api/jobs/<job_id> (repeat until COMPLETED)

4. Retrieve Report
   GET /api/reports/<report_id>

5. Export if needed
   GET /api/reports/<report_id>/json
   GET /api/reports/<report_id>/pdf
```

---

## Deployment Notes

- **External URLs**: For Portainer/external deployment, use `http://docker.itspectrum.fr:<port>` instead of `localhost`
- **Security**: MongoDB should NOT be exposed publicly (currently port 27017 is exposed for development only)
- **Scaling**: Redis is configured and can support async task queue (Celery/RQ) for future expansion
- **Monitoring**: All services log to stdout with timestamps

---

## Contact & Support

For questions about the backend architecture or API, refer to `PROJECT_CONTEXT.md` for detailed service specifications.
