# SCOPE GUARD 🛡️
### AI-Powered Scope of Work & Task Management for Small Agencies

Scope Guard is a multi-tenant web application engineered specifically for digital, creative, and software agencies. It protects agency profitability by establishing contractually binding Scope of Work (SOW) baselines, tracking sprint tasks against deliverables, analyzing change requests for scope creep using AI, and capturing retrospective lessons to continuously refine future project scopes.

---

## 🚀 Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend** | React 19 + Vite | Fast single-page application bundled with Vite |
| **Styling** | Tailwind CSS v4 | High-performance atomic CSS engine |
| **Backend** | Python 3.12 + FastAPI | Async REST API with OpenAPI (Swagger) documentation |
| **Database** | PostgreSQL (Supabase) | Multi-tenant relational schema with native UUID primary keys |
| **ORM & Migrations** | SQLAlchemy 2.0 + Alembic | Declarative mapping, cross-platform GUID type, versioned migrations |
| **Authentication** | JWT (PyJWT) + bcrypt | Secure password hashing (12 rounds) and stateless Bearer tokens |
| **AI Integration** | Google Gemini API (`gemini-1.5-flash`) | Modular AI Scope Request Checker returning exact classifications & polite client replies |
| **Testing** | Pytest + HTTPX | Integration, tenant-isolation, and AI mock test coverage |

---

## 📁 Project Structure

```text
scope-guard/
├── .gitignore                      # Git ignore rules for Python, Node, Vite, and environment files
├── README.md                       # Complete architecture, database, and setup documentation
├── backend/                        # FastAPI Backend Application
│   ├── .env.example                # Example environment configuration template
│   ├── .env                        # Local environment variables (git-ignored)
│   ├── requirements.txt            # Python dependencies (FastAPI, SQLAlchemy, Alembic, psycopg2, etc.)
│   ├── alembic.ini                 # Alembic migration runner configuration
│   ├── alembic/
│   │   ├── env.py                  # Dynamic database URL injection and model metadata registration
│   │   ├── script.py.mako          # Revision generation template
│   │   └── versions/
│   │       ├── 001_initial_schema.py        # Initial migration creating all 8 PostgreSQL tables
│   │       ├── 002_update_scope_items_table.py # Day 6: included/not_included descriptions
│   │       ├── 003_update_tasks_table.py    # Day 7: tasks status and deliverable linking
│   │       ├── 004_update_requests_table.py # Day 8: requests schema for AI Request Checker
│   │       └── 005_update_lessons_and_requests.py # Day 9: lessons schema, feedback & check-again linking
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI initialization, CORS middleware, healthcheck routes
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Pydantic Settings reading .env variables
│   │   │   ├── database.py         # SQLAlchemy engine, sessionmaker, GUID type, and get_db dependency
│   │   │   ├── dependencies.py     # Auth verification and STRICT workspace-derived tenant security
│   │   │   └── security.py         # Bcrypt password hashing and JWT encoding/decoding utilities
│   │   ├── models/                 # SQLAlchemy 2.0 declarative database models
│   │   │   ├── __init__.py         # Re-exports all models and Base metadata
│   │   │   ├── base.py             # TimestampMixin (created_at, updated_at with timezone)
│   │   │   ├── workspace.py        # 1. workspaces: Top-level tenant boundary
│   │   │   ├── user.py             # 2. users: Agency staff, admins, and client members
│   │   │   ├── client.py           # 3. clients: Agency customer organizations
│   │   │   ├── project.py          # 4. projects: Client engagements / contracts
│   │   │   ├── scope_item.py       # 5. scope_items: Contractual baseline deliverables
│   │   │   ├── task.py             # 6. tasks: Daily actionable work items
│   │   │   ├── request.py          # 7. requests: Client change requests analyzed by AI, feedback & re-evaluations
│   │   │   └── lesson.py           # 8. lessons: Agency retrospective correction lessons
│   │   ├── schemas/                # Pydantic validation & serialization schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Token, TokenPayload, LoginRequest
│   │   │   ├── user.py             # UserRead, Signup schemas
│   │   │   ├── client.py           # ClientCreate, ClientRead, ClientUpdate
│   │   │   ├── project.py          # ProjectCreate, ProjectRead, ProjectUpdate
│   │   │   ├── scope_item.py       # ScopeItemCreate, ScopeItemRead, ScopeItemUpdate
│   │   │   ├── task.py             # TaskCreate, TaskRead, TaskUpdate
│   │   │   ├── request.py          # RequestCheckIn, RequestRead, RequestFeedbackIn, CheckAgainResponse
│   │   │   ├── lesson.py           # LessonRead
│   │   │   └── workspace.py        # WorkspaceRead, WorkspaceCreate
│   │   ├── services/               # Modular service layer
│   │   │   └── ai/                 # Modular AI provider architecture
│   │   │       ├── __init__.py
│   │   │       ├── base.py         # BaseAIService abstract interface & Pydantic models
│   │   │       ├── prompt.py       # Deterministic system instructions, prompt builder & Hierarchy of Truth
│   │   │       ├── gemini.py       # Google Gemini 1.5 Flash REST client with structured JSON
│   │   │       └── factory.py      # Provider factory dependency
│   │   └── api/
│   │       └── v1/
│   │           ├── api.py          # Root v1 router assembling endpoint submodules
│   │           └── endpoints/
│   │               ├── auth.py     # Agency signup, user login, and /auth/me profile
│   │               ├── users.py    # Workspace-isolated user listing
│   │               ├── clients.py  # Client CRUD
│   │               ├── projects.py # Project CRUD
│   │               ├── scope_items.py # Scope of Work CRUD
│   │               ├── tasks.py    # Task CRUD & deliverable linking
│   │               ├── requests.py # AI Request Checker, feedback & Check Again endpoints
│   │               └── lessons.py  # Lessons learned retrieval endpoints
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # Pytest fixtures, test database engine, FastAPI TestClient
│       ├── test_auth.py            # Signup, login, invalid password, token rejection tests
│       ├── test_clients.py         # Client CRUD & workspace isolation tests
│       ├── test_projects.py        # Project CRUD, status transitions & isolation tests
│       ├── test_scope_items.py     # Scope CRUD & dual description tests
│       ├── test_tasks.py           # Task CRUD & deliverable validation tests
│       ├── test_requests.py        # AI Request Checker & classification tests
│       ├── test_lessons.py         # Day 9: Feedback, Lessons, Check Again & AI context tests
│       └── test_workspace_isolation.py # Multi-tenant isolation verification across separate agencies
└── frontend/                       # React + Vite Frontend Application
    ├── package.json                # Frontend package configuration (React 19, Tailwind CSS v4)
    ├── vite.config.js              # Vite configuration with @tailwindcss/vite plugin
    ├── index.html                  # HTML5 application shell
    └── src/
        ├── main.jsx                # React DOM root mounting
        ├── App.jsx                 # Tabbed navigation shell
        ├── pages/
        │   ├── RequestChecker.jsx  # Day 8–9: AI Request Checker with Gemini 1.5 Flash, Feedback & Check Again
        │   ├── Tasks.jsx           # Day 7: Task management & deliverable linking
        │   └── ScopeOfWork.jsx     # Day 6: Scope of Work Included/Not Included editor
        └── index.css               # Tailwind CSS v4 root stylesheet
```

---

## 🗄️ Database Design (PostgreSQL)

Scope Guard models an agency's delivery pipeline across **8 core relational entities**. Every agency-owned entity contains a foreign key to `workspaces.id` with `ON DELETE CASCADE` and dedicated indexes for ultra-fast multi-tenant query filtration.

```mermaid
erDiagram
    workspaces ||--o{ users : "employs"
    workspaces ||--o{ clients : "serves"
    workspaces ||--o{ projects : "manages"
    workspaces ||--o{ scope_items : "owns"
    workspaces ||--o{ tasks : "tracks"
    workspaces ||--o{ requests : "evaluates"
    workspaces ||--o{ lessons : "records"

    clients ||--o{ projects : "contracts"
    projects ||--o{ scope_items : "defines"
    projects ||--o{ tasks : "contains"
    projects ||--o{ requests : "receives"
    projects ||--o{ lessons : "informs"

    scope_items ||--o{ tasks : "breaks into"
    users ||--o{ tasks : "assigned to"
    users ||--o{ requests : "submits"
```

### Table Specifications

#### 1. `workspaces` (Tenant Boundary)
- `id` (UUID, Primary Key, default `uuid4`): Unique agency identifier.
- `name` (VARCHAR(255), NOT NULL): Agency name (e.g., "Apex Digital Labs").
- `slug` (VARCHAR(100), UNIQUE, NOT NULL, INDEX): URL-friendly unique identifier (e.g., `apex-digital-labs`).
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).

#### 2. `users` (Staff & Agency Admins)
- `id` (UUID, Primary Key, default `uuid4`): User identifier.
- `workspace_id` (UUID, FK -> `workspaces.id` ON DELETE CASCADE, NOT NULL, INDEX): Tenant isolation link.
- `email` (VARCHAR(255), UNIQUE, NOT NULL, INDEX): Sign-in email address.
- `hashed_password` (VARCHAR(255), NOT NULL): Bcrypt-hashed password (rounds=12).
- `full_name` (VARCHAR(255), NOT NULL): Display name.
- `role` (VARCHAR(50), DEFAULT `'admin'`, NOT NULL): Role (`agency_admin`, `agency_member`, `client`).
- `is_active` (BOOLEAN, DEFAULT `true`, NOT NULL): Account status flag.
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).

#### 3. `clients` (Customer Organizations)
- `id` (UUID, Primary Key, default `uuid4`): Client identifier.
- `workspace_id` (UUID, FK -> `workspaces.id` ON DELETE CASCADE, NOT NULL, INDEX): Tenant isolation link.
- `name` (VARCHAR(255), NOT NULL): Client company name.
- `contact_email` (VARCHAR(255), NULLABLE): Primary contact email.
- `contact_name` (VARCHAR(255), NULLABLE): Primary contact name.
- `company_details` (TEXT, NULLABLE): Client notes, billing address, or company background.
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).

#### 4. `projects` (Contracts & Engagements)
- `id` (UUID, Primary Key, default `uuid4`): Project identifier.
- `workspace_id` (UUID, FK -> `workspaces.id` ON DELETE CASCADE, NOT NULL, INDEX): Tenant isolation link.
- `client_id` (UUID, FK -> `clients.id` ON DELETE CASCADE, NOT NULL, INDEX): Associated client.
- `name` (VARCHAR(255), NOT NULL): Project title (e.g. "E-Commerce Re-platforming").
- `description` (TEXT, NULLABLE): Project goals and specifications.
- `budget` (NUMERIC(12, 2), NULLABLE): Total contracted budget.
- `status` (VARCHAR(50), DEFAULT `'draft'`, NOT NULL): `draft`, `in_progress`, `completed`, `on_hold`.
- `start_date` (TIMESTAMP WITH TIME ZONE, NULLABLE).
- `end_date` (TIMESTAMP WITH TIME ZONE, NULLABLE).
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).

#### 5. `scope_items` (Deliverable Baselines & Boundaries)
- `id` (UUID, Primary Key, default `uuid4`): Deliverable identifier.
- `workspace_id` (UUID, FK -> `workspaces.id` ON DELETE CASCADE, NOT NULL, INDEX): Tenant isolation link.
- `project_id` (UUID, FK -> `projects.id` ON DELETE CASCADE, NOT NULL, INDEX): Parent project.
- `included_description` (TEXT, NOT NULL): Contractually promised deliverables (e.g., "Home page design, five pages, contact form").
- `not_included_description` (TEXT, NOT NULL): Explicit out-of-scope exclusions (e.g., "Hindi language version, payment gateway integration").
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).

#### 6. `tasks` (Actionable Sprint Work)
- `id` (UUID, Primary Key, default `uuid4`): Task identifier.
- `workspace_id` (UUID, FK -> `workspaces.id` ON DELETE CASCADE, NOT NULL, INDEX): Tenant isolation link.
- `project_id` (UUID, FK -> `projects.id` ON DELETE CASCADE, NOT NULL, INDEX): Parent project.
- `scope_item_id` (UUID, FK -> `scope_items.id` ON DELETE CASCADE, NOT NULL, INDEX): Linked Scope of Work deliverable.
- `title` (VARCHAR(255), NOT NULL): Task description.
- `due_date` (DATE, NULLABLE): Target completion date.
- `status` (VARCHAR(50), DEFAULT `'To do'`, NOT NULL): `To do`, `Doing`, `Done`.
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).

#### 7. `requests` (Client Change Requests & AI Scope Creep Detection)
- `id` (UUID, Primary Key, default `uuid4`): Request identifier.
- `workspace_id` (UUID, FK -> `workspaces.id` ON DELETE CASCADE, NOT NULL, INDEX): Tenant isolation link.
- `project_id` (UUID, FK -> `projects.id` ON DELETE CASCADE, NOT NULL, INDEX): Target project.
- `user_id` (UUID, FK -> `users.id` ON DELETE SET NULL, NULLABLE, INDEX): Submitting agency user.
- `parent_request_id` (UUID, FK -> `requests.id` ON DELETE SET NULL, NULLABLE, INDEX): Link to parent request when re-evaluating with "Check Again".
- `client_request` (TEXT, NOT NULL): The client's requested deliverable or modification.
- `classification` (VARCHAR(50), DEFAULT `'Not sure'`, NOT NULL): Exact AI outcome (`In scope`, `Out of scope`, `Not sure`).
- `reason` (TEXT, NOT NULL): Short justification based strictly on the project's agreed scope baseline and lessons.
- `client_reply` (TEXT, NOT NULL): Courteous and professional communication draft for the client.
- `feedback` (VARCHAR(20), NULLABLE): Agency evaluation feedback (`Right` or `Wrong`).
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).

#### 8. `lessons` (Agency Continuous Learning & Corrections)
- `id` (UUID, Primary Key, default `uuid4`): Lesson identifier.
- `workspace_id` (UUID, FK -> `workspaces.id` ON DELETE CASCADE, NOT NULL, INDEX): Tenant isolation link.
- `project_id` (UUID, FK -> `projects.id` ON DELETE CASCADE, NOT NULL, INDEX): Project origin.
- `request_id` (UUID, FK -> `requests.id` ON DELETE SET NULL, NULLABLE, INDEX): Originating evaluated request.
- `ai_answer` (VARCHAR(50), NOT NULL): Original AI classification on the request.
- `correct_result` (VARCHAR(50), NOT NULL): Human agency correction (`In scope` or `Out of scope`).
- `correction_reason` (TEXT, NOT NULL): Meaningful one-line explanation justifying the correction.
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT `now()`, NOT NULL).

---

## 🔒 Security & Multi-Tenant Data Isolation

### 1. Zero Trust on Client Workspace IDs
In traditional naive multi-tenant setups, APIs often accept `workspace_id` in the request body or URL path (e.g. `/api/projects?workspace_id=...`). This introduces dangerous IDOR (Insecure Direct Object Reference) vulnerabilities.

**Scope Guard Defense:**
The workspace context is **never** accepted from the client.
```python
# app/core/dependencies.py
def get_current_workspace(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    # Derived strictly from the cryptographically verified JWT token
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    return workspace
```

### 2. Password Safety
- Raw passwords are never stored. Passwords are salted and hashed with `bcrypt` (12 rounds).
- Pydantic response models (`UserRead`) intentionally omit `hashed_password` and all authentication secrets.

### 3. Environment Variable Hygiene
- Sensitive secrets (`SECRET_KEY`, `DATABASE_URL`, `GEMINI_API_KEY`) are managed strictly through `.env` and loaded via Pydantic `BaseSettings`. No secrets are hardcoded.

---

## ⚙️ Environment Variables

Create `backend/.env` using `backend/.env.example`:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string (Supabase URI) | `postgresql+psycopg2://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres` |
| `SECRET_KEY` | Cryptographic secret for signing JWTs | `32+ character random hex string` |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| JWT validity duration in minutes | `1440` (24 hours) |
| `ENVIRONMENT` | Runtime mode (`development`, `production`, `test`) | `development` |
| `AI_PROVIDER` | AI service provider selection (`gemini` or `openai`) | `gemini` |
| `AI_MODEL` | Large language model name | `gemini-1.5-flash` |
| `GEMINI_API_KEY` | Google Gemini API key for Scope Creep AI | `AIzaSy...` |
| `OPENAI_API_KEY` | (Optional) OpenAI API key for alternative provider | `sk-...` |

---

## 🛠️ Setup and Run Instructions

### Prerequisites
- **Python**: 3.12+
- **Node.js**: 20+ (with npm)
- **Database**: Supabase PostgreSQL project or local PostgreSQL 15+

---

### Step 1: Configure Backend Database & Environment

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Configure `.env`:
   ```bash
   copy .env.example .env
   ```
   Open `.env` and set your Supabase database connection string in `DATABASE_URL`:
   ```ini
   DATABASE_URL=postgresql+psycopg2://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

3. Run Alembic database migrations:
   ```bash
   python -m alembic upgrade head
   ```
   *(To preview the generated PostgreSQL DDL offline without executing, run `python -m alembic upgrade head --sql`)*

---

### Step 2: Run Backend Tests

Execute the automated test suite covering signup, login, password verification, protected endpoints, and multi-tenant isolation:
```bash
cd backend
python -m pytest -v
```
All test cases will run and pass:
```text
tests/test_auth.py (8 passed)
tests/test_clients.py (8 passed)
tests/test_lessons.py (15 passed)
tests/test_projects.py (10 passed)
tests/test_requests.py (12 passed)
tests/test_scope_items.py (11 passed)
tests/test_tasks.py (12 passed)
tests/test_workspace_isolation.py (1 passed)
======================= 77 passed in 25.75s ========================
```

---

## 📡 API Endpoints Reference

### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/signup`: Register an agency workspace and admin user.
- `POST /api/v1/auth/login`: Authenticate and receive a JWT token.
- `GET /api/v1/auth/me`: Retrieve current user profile and workspace.

### Client Management (`/api/v1/clients`)
- `POST /api/v1/clients`: Create a new client in the agency workspace.
- `GET /api/v1/clients`: List all clients in the workspace.
- `GET /api/v1/clients/{id}`: Retrieve a single client by ID.
- `PUT /api/v1/clients/{id}`: Update client details.
- `DELETE /api/v1/clients/{id}`: Delete a client.

### Project Management (`/api/v1/projects`)
- `POST /api/v1/projects`: Create project linked to a workspace client (defaults to `Active`).
- `GET /api/v1/projects`: List workspace projects (supports `?client_id=` and `?status=` filters).
- `GET /api/v1/projects/{id}`: Retrieve a project by ID.
- `PUT /api/v1/projects/{id}`: Update project name, status (`Active` or `Done`), or client.
- `DELETE /api/v1/projects/{id}`: Delete a project.

### Scope of Work Management (`/api/v1/scope-items`)
- `POST /api/v1/scope-items`: Create a deliverable baseline with `included_description` and `not_included_description`.
- `GET /api/v1/scope-items`: List all scope items (supports `?project_id=` filter).
- `GET /api/v1/scope-items/{id}`: Retrieve a scope item by ID.
- `PUT /api/v1/scope-items/{id}`: Update included/excluded descriptions or project.
- `DELETE /api/v1/scope-items/{id}`: Delete a scope item.

### Task Management (`/api/v1/tasks`)
- `POST /api/v1/tasks`: Create a task linked to an approved scope item deliverable and project.
- `GET /api/v1/tasks`: List all tasks in the workspace (supports `?project_id=`, `?scope_item_id=`, and `?status=` filters).
- `GET /api/v1/tasks/{id}`: Retrieve a single task by ID.
- `PUT /api/v1/tasks/{id}`: Update task title, due date, status (`To do`, `Doing`, `Done`), or linked project/scope item.
- `DELETE /api/v1/tasks/{id}`: Delete a task within the workspace.

### AI Request Checker & Learning (`/api/v1/requests`)
- `POST /api/v1/requests/check`: Evaluate a client request against the selected project's agreed scope deliverables and past lessons using Google Gemini 1.5 Flash. Returns `classification` (`In scope`, `Out of scope`, `Not sure`), `reason`, and `client_reply`.
- `POST /api/v1/requests/{id}/feedback`: Submit agency rating (`Right` or `Wrong`). If `Wrong`, requires `correct_result` (`In scope` or `Out of scope`) and `correction_reason`, creating a permanent project lesson.
- `POST /api/v1/requests/{id}/check-again`: Re-evaluates an existing request with the latest project scope and learned lessons. Preserves the original evaluation and records a linked new evaluation, returning both `old_answer` and `new_answer`.
- `GET /api/v1/requests`: List request evaluation history in the workspace (supports `?project_id=` filter).
- `GET /api/v1/requests/{id}`: Retrieve a specific evaluated request by ID.

### Lessons Learned Knowledge Base (`/api/v1/lessons`)
- `GET /api/v1/lessons`: List all retrospective correction lessons for the workspace (supports `?project_id=` filter).
- `GET /api/v1/lessons/{id}`: Retrieve an individual lesson by ID within the authenticated workspace.

---

### Step 3: Start Backend API Server

Run the FastAPI development server with live reload:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger API Documentation: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- Alternative ReDoc API Documentation: [http://127.0.0.1:8000/api/v1/redoc](http://127.0.0.1:8000/api/v1/redoc)
- Healthcheck: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### Step 4: Start Frontend Client

In a separate terminal, start the React + Vite development server:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🎯 Verification Matrix

| Requirement | Implementation | Test Coverage |
| :--- | :--- | :--- |
| **UUID Primary Keys** | `GUID` custom TypeDecorator mapping to `postgresql.UUID(as_uuid=True)` | ✅ Tested in all entity tables |
| **8 PostgreSQL Tables** | `workspaces`, `users`, `clients`, `projects`, `scope_items`, `tasks`, `requests`, `lessons` | ✅ Verified via Alembic DDL & migrations |
| **Workspace Isolation** | Every table has `workspace_id` indexed FK; API dependencies strictly isolate by JWT | ✅ `test_strict_workspace_isolation` & cross-workspace tests |
| **JWT + Bcrypt Auth** | Stateless Bearer token generation, 12 rounds bcrypt salting | ✅ `test_agency_signup_success`, `test_login_success` |
| **Client CRUD** | Full CRUD with input validation and workspace scoping | ✅ 8 tests in `test_clients.py` |
| **Project CRUD** | Client-project workspace relationship enforcement & `Active`/`Done` status | ✅ 10 tests in `test_projects.py` |
| **Scope of Work CRUD** | Dual Included/Not Included text fields, project validation & filtering | ✅ 11 tests in `test_scope_items.py` |
| **Task Management CRUD** | Scope-item deliverable linking, project relationship check, `To do`/`Doing`/`Done` status | ✅ 12 tests in `test_tasks.py` |
| **AI Request Checker** | Modular Gemini 1.5 Flash evaluation, exact classification (`In scope`, `Out of scope`, `Not sure`), justification & polite client reply draft | ✅ 12 tests in `test_requests.py` |
| **Continuous Learning & Check Again** | Human-in-the-loop Right/Wrong feedback, lessons knowledge base persistence, Hierarchy of Truth prompt context, immutable Check Again comparison | ✅ 15 tests in `test_lessons.py` (77 total passing tests) |
