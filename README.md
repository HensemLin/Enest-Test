# Enest Tender Assistant System

An AI-powered tender document analysis system that extracts requirements, bill of materials (BoM), and provides RAG-based chat assistance.

## Features

- 📄 **PDF Upload & Management** - Upload and process tender documents
- 🔍 **Requirements Extraction** - AI-powered extraction of tender requirements using LLM
- 📋 **Bill of Materials (BoM)** - Automatic extraction of BoM from tender documents
- 💬 **RAG Chat Assistant** - Ask questions about your documents with conversation memory
- ✅ **Batch Updates** - Efficiently update compliance status for multiple requirements
- 📊 **Paginated Tables** - Sort and filter through large datasets (100 items per page)
- 📤 **Export Functionality** - Export requirements to Excel/JSON and BoM to Excel
- ⚡ **Background Processing** - Long-running extractions don't block the API

## Tech Stack

**Backend:**

- FastAPI (Python)
- PostgreSQL
- LangChain
- OpenRouter (LLM API)
- FAISS (Vector database)

**Frontend:**

- Next.js 14
- React Query
- TailwindCSS

## Prerequisites

Before you begin, ensure you have:

- **Docker & Docker Compose** (recommended) OR
- **Python 3.11+** and **Node.js 20+** (for local development)
- **OpenRouter API Key** - Get one from [OpenRouter](https://openrouter.ai/)

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/HensemLin/Enest-Test.git
cd Enest-Test
```

### 2. Set Up Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure the OpenRouter API key:

#### Required Configuration:

**OpenRouter API Key** (for LLM)

1. Sign up at https://openrouter.ai/
2. Generate an API key from your dashboard
3. Add to `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

**Database Configuration** (optional for Docker)

```env
DATABASE_HOSTNAME=db  # Use 'db' for Docker, 'localhost' for local
DATABASE_PORT=5432
DATABASE_NAME=enest
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=postgres
```

#### Optional Configuration:

**LLM Model Selection:**

```env
# Default (free):
LLM_MODEL=mistralai/devstral-2512:free
EMBEDDING_MODEL=qwen/qwen3-embedding-8b

# Alternatives (may require credits):
# LLM_MODEL=google/gemini-flash-1.5
# LLM_MODEL=anthropic/claude-3-haiku
```

### 3. Start Backend and Database

Start only the backend and database first:

```bash
docker-compose up db api pgadmin
```

Wait for the backend to be ready (you'll see "Application startup complete").

### 4. Generate API Key

The backend API key must be generated through the backend and stored in the database.

**Option 1: Using curl**

```bash
curl -X POST http://localhost:8000/api/keys/ | jq -r '.apiKey'
```

**Option 2: Visit API docs**

1. Open http://localhost:8000/docs
2. Find `POST /api/keys/` endpoint
3. Click "Try it out" → "Execute"
4. Copy the `apiKey` value from the response

**IMPORTANT:** Save this key - you'll only see it once!

Example response:

```json
{
  "id": "some-uuid",
  "apiKey": "mMbN4BOkNVRdJseN26vGGIKKyIr6ek",
  "created_at": "2024-12-18T10:30:00"
}
```

### 5. Add API Key to Environment

Add the generated API key to your `.env` file:

```env
API_KEY=mMbN4BOkNVRdJseN26vGGIKKyIr6ek
```

### 6. Start Frontend

Now start the frontend:

```bash
docker compose up frontend --build -d
```

Or restart all services:

```bash
docker compose down
docker compose up -d
```

### 7. Access the Application

Open your browser and go to:

- **Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **PgAdmin**: http://localhost:9898 (admin@admin.com / admin)

## Local Development (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (if needed)
# alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

Backend will run on http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on http://localhost:3000

## Configuration Details

### Environment Variables Explained

| Variable             | Description                            | Required | Default                      |
| -------------------- | -------------------------------------- | -------- | ---------------------------- |
| `OPENROUTER_API_KEY` | Your OpenRouter API key for LLM access | ✅ Yes   | -                            |
| `API_KEY`            | Backend API authentication key         | ✅ Yes   | -                            |
| `API_URL`            | Backend URL for Next.js proxy          | No       | http://localhost:8000        |
| `DATABASE_HOSTNAME`  | PostgreSQL hostname                    | No       | localhost                    |
| `DATABASE_PORT`      | PostgreSQL port                        | No       | 5432                         |
| `DATABASE_NAME`      | Database name                          | No       | enest                        |
| `DATABASE_USERNAME`  | Database username                      | No       | postgres                     |
| `DATABASE_PASSWORD`  | Database password                      | No       | postgres                     |
| `LLM_MODEL`          | OpenRouter model to use                | No       | mistralai/devstral-2512:free |
| `EMBEDDING_MODEL`    | Embedding model for RAG                | No       | qwen/qwen3-embedding-8b      |
| `MAX_UPLOAD_SIZE_MB` | Maximum PDF upload size                | No       | 100                          |

### Getting API Keys

#### OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up or log in
3. Go to **Settings** → **API Keys**
4. Click **Create Key**
5. Copy the key (starts with `sk-or-v1-...`)
6. Paste into `.env` as `OPENROUTER_API_KEY`

**Free Tier Models:**

- `mistralai/devstral-2512:free`

See available models: https://openrouter.ai/models

#### Backend API Key (API_KEY)

This key is generated by the backend and stored in the database (hashed with Argon2).

**Important:**

- You CANNOT generate this manually
- Must be created through the backend API (see step 4 in Quick Start)
- Key is only shown once when created
- If lost, you must generate a new one via `POST /api/keys/`
- The key is kept server-side only (not exposed to browser) for security

## User Manual

This section provides comprehensive step-by-step instructions for using all features of the Enest Tender Assistant System.

---

### 📄 Managing PDF Documents

#### Uploading Tender Documents

1. **Navigate to PDF Documents Page**

   - Click **"PDF Documents"** in the sidebar navigation
   - You'll see a list of all uploaded documents

2. **Upload a New PDF**

   - Click the **"Upload PDF"** button (top-right corner)
   - A file dialog will appear
   - Select one or more PDF files (up to 100MB each)
   - Click **"Open"** to start upload

3. **Monitor Upload Progress**

   - Upload status appears in the UI
   - Wait for "Upload complete" message
   - The new PDF appears in the documents list with status "Ready"

4. **Understanding PDF Status**

   - **Ready**: PDF uploaded and ready for processing
   - **Processing**: Extraction is currently running in background
   - **Failed**: Extraction encountered an error

**Tips:**

- Supported file types: PDF only
- Maximum file size: 100MB (configurable in `.env`)
- PDFs are automatically stored in `storage/pdfs/`
- Each PDF is assigned a unique ID for tracking

#### Deleting PDFs

1. Find the PDF you want to delete
2. Click the **trash icon** or **"Delete"** button
3. Confirm deletion in the dialog
4. **Note**: This also deletes all associated requirements, BoM items, and vector embeddings

---

### 🔍 Extracting and Managing Requirements

#### Step 1: Extract Requirements from PDF

1. **Start Extraction**

   - Go to **"PDF Documents"** page
   - Find your uploaded PDF
   - Click **"Extract Requirements"** button
   - Extraction starts immediately in the background

2. **Monitor Extraction Progress**

   - Button changes to **"Extracting..."** with a spinner
   - Background process typically takes **1-3 minutes** depending on PDF size
   - You can navigate to other pages while extraction runs
   - System polls every 5 seconds to check completion status

3. **Completion Notification**

   - Button changes back to **"Extract Requirements"** when done
   - PDF status updates to show number of requirements extracted
   - Navigate to **"Requirements"** page to view results

**What Gets Extracted:**

- **Requirement Category**: Type of requirement (Technical, Commercial, Quality, etc.)
- **Requirement Detail**: The actual requirement text
- **Mandatory/Optional**: Whether requirement is mandatory or optional
- **Compliance Status**: Initial status (defaults to "Unknown")
- **Document Source**: Which PDF the requirement came from
- **Page Number**: Location in the original PDF

#### Step 2: View and Filter Requirements

1. **Navigate to Requirements Page**

   - Click **"Requirements"** in the sidebar
   - All extracted requirements are displayed in a paginated table (100 items per page)

2. **Search Requirements**

   - Use the **search box** at the top
   - Searches across:
     - Requirement detail (description)
     - Category
     - Document source
   - Results update in real-time as you type

3. **Filter by PDF Source**

   - Use the **"All PDFs"** dropdown
   - Select a specific PDF to show only its requirements
   - Select "All PDFs" to see requirements from all documents

4. **Filter by Mandatory/Optional**

   - Use the **"Mandatory/Optional"** dropdown
   - Options:
     - **All**: Show both mandatory and optional
     - **Mandatory**: Show only mandatory requirements
     - **Optional**: Show only optional requirements
     - **Unclear**: Show requirements where classification is unclear

5. **Filter by Compliance Status**

   - Use the **"All Statuses"** dropdown
   - Options:
     - **All**: Show all statuses
     - **Unknown**: Not yet assessed
     - **Yes**: Compliant
     - **Partial**: Partially compliant
     - **No**: Non-compliant

6. **Sort Requirements**

   - Click any column header to sort:
     - **Document Source**: Alphabetically by PDF name
     - **Requirement Category**: Alphabetically by category
     - **Requirement Detail**: Alphabetically by description
     - **Mandatory/Optional**: Mandatory first
     - **Compliance Status**: By status
   - Click again to reverse sort order
   - Click a third time to remove sorting
   - Sort icons show current state:
     - ⇅ = Not sorted
     - ↑ = Ascending
     - ↓ = Descending

#### Step 3: Update Compliance Status

1. **Single Update**

   - Find the requirement in the table
   - Click the **compliance status dropdown** in that row
   - Select new status:
     - **Unknown**: Not yet assessed (gray badge)
     - **Yes**: Fully compliant (green badge)
     - **Partial**: Partially compliant (yellow badge)
     - **No**: Non-compliant (red badge)
   - Row turns **yellow** to indicate pending change

2. **Batch Update (Recommended for Multiple Changes)**

   - Update multiple requirements by clicking their status dropdowns
   - All changed rows turn yellow
   - Changed items counter appears at top: "X pending changes"
   - Click **"Save Changes"** button to apply all at once
   - Success message shows: "Successfully updated X requirements!"
   - OR click **"Cancel"** to discard all pending changes

**Benefits of Batch Update:**

- More efficient than individual updates
- Reduces API calls
- Single database transaction (faster)
- Can review all changes before committing

#### Step 4: Export Requirements

1. **Export to Excel**

   - Click **"Export Excel"** button (top-right)
   - Excel file downloads automatically
   - Filename format: `requirements_export_YYYYMMDD_HHMMSS.xlsx`
   - Includes all current filters (filtered data only)

2. **Export to JSON**

   - Click **"Export JSON"** button
   - JSON file downloads automatically
   - Useful for further processing or integration
   - Includes all requirement fields

**Export Contents:**

- All visible requirements (respects current filters)
- All columns: category, detail, mandatory/optional, compliance status, source, page number
- Excel includes formatted headers and colored status cells

#### Step 5: Pagination

- **100 requirements per page** for optimal performance
- Use pagination controls at bottom:
  - **Previous** / **Next** buttons
  - **Page number buttons** (shows 5 pages at a time)
  - Current page highlighted in blue
- Shows: "Showing 1-100 of 247 requirements" at bottom
- When filtered: "Showing 15 of 247 requirements (filtered from 500 total)"

---

### 📋 Extracting and Managing Bill of Materials (BoM)

#### Step 1: Extract BoM from PDF

1. **Start Extraction**

   - Go to **"PDF Documents"** page
   - Find your PDF containing BoM tables
   - Click **"Extract BoM"** button
   - Background extraction begins

2. **Wait for Completion**

   - Button shows **"Extracting..."**
   - Takes **1-3 minutes** depending on complexity
   - System automatically detects tables in PDF
   - Extracts hierarchical structure if present

**What Gets Extracted:**

- **Item Number**: BoM item identifier/code
- **Description**: Description of work/item
- **Unit**: Unit of measurement (pcs, m, kg, etc.)
- **Quantity**: Amount needed
- **Notes**: Additional specifications or remarks
- **Hierarchy Level**: Indentation level for nested items
- **Source PDF**: Which document it came from

#### Step 2: View and Filter BoM Items

1. **Navigate to BoM Page**

   - Click **"Bill of Materials"** in the sidebar
   - All extracted items displayed in a table

2. **Search BoM Items**

   - Use the **search box** at top
   - Searches across:
     - Item number
     - Description
     - Unit
     - Notes
   - Real-time filtering

3. **Filter by PDF Source**

   - Use **"All PDFs"** dropdown
   - Select specific PDF or "All PDFs"

4. **Sort BoM Items**

   - Click column headers to sort:
     - **Item No.**: Alphanumeric sorting
     - **Description of Work**: Alphabetically
     - **Unit**: Alphabetically
     - **Quantity**: Numerically
     - **Notes**: Alphabetically
   - Visual hierarchy preserved (indentation shows parent-child relationships)

#### Step 3: Export BoM

1. **Export to Excel**
   - Click **"Export Excel"** button
   - Downloads: `bom_export_YYYYMMDD_HHMMSS.xlsx`
   - Includes:
     - All columns with proper formatting
     - Hierarchy indicated by indentation
     - Source PDF information
     - Total items count

**Export Features:**

- Preserves hierarchical structure
- Formatted headers
- Auto-sized columns
- Includes all current filters
- Totals and summary information

---

### 💬 RAG Chat Assistant

The chat assistant uses Retrieval-Augmented Generation (RAG) to answer questions about your tender documents with context-aware responses.

#### Step 1: Create a Chat Session

1. **Start New Session**

   - Go to **"Dashboard"** page
   - Click **"New Session"** button
   - You're redirected to the chat interface

2. **Select Documents**

   - In the chat interface, you'll see a **PDF selector**
   - Check the boxes next to PDFs you want to include
   - You can select **multiple PDFs** for broader context
   - Selected PDFs are stored with the session

**Tip:** Select only relevant PDFs for faster, more focused responses

#### Step 2: Ask Questions

1. **Type Your Question**

   - Use the message input box at bottom
   - Examples of good questions:
     - "What are the mandatory technical requirements?"
     - "List all quality assurance requirements"
     - "What is the delivery timeline?"
     - "Summarize the payment terms"
     - "What certifications are required?"

2. **Send Message**

   - Click **"Send"** or press **Enter**
   - System processes your question (typically 5-15 seconds)

3. **How RAG Works Behind the Scenes**

   - Your question is converted to vector embedding
   - System searches vector database for relevant PDF sections
   - Top 5 most relevant chunks retrieved
   - LLM generates answer using retrieved context
   - Response includes source citations

#### Step 3: Review Responses

1. **Understanding the Response**

   - **Answer**: Direct answer to your question
   - **Sources**: Citations showing which PDF sections were used
   - Each source shows:
     - PDF filename
     - Page number
     - Relevance score (0-100%)
     - Text snippet from that section

2. **Source Citations Format**

   ```
   📄 tender_document.pdf (Page 12) - 87% relevant
   "...excerpt from the document that was used..."
   ```

3. **Ask Follow-up Questions**

   - Chat maintains conversation memory (last 10 messages buffered)
   - Ask clarifying questions
   - Reference previous answers
   - System remembers context of conversation

**Example Conversation:**

```
You: What are the delivery requirements?
AI: The delivery requirements include... [answer with sources]

You: Are there any penalties for late delivery?
AI: Based on the previous context about delivery, yes there are penalties... [answer]
```

#### Step 4: Manage Sessions

1. **View All Sessions**

   - Go to **"Dashboard"**
   - All your past sessions listed with:
     - Session creation date
     - Number of messages
     - Associated PDFs

2. **Resume a Session**

   - Click on any past session
   - Full conversation history loads
   - Continue asking questions
   - Same PDFs remain selected

3. **Session Features**

   - **Conversation Memory**: Last 10 messages kept in context
   - **Semantic Memory**: Relevant past messages retrieved automatically
   - **Session Persistence**: All sessions saved to database
   - **PDF Association**: Sessions remember selected documents

**Memory System Details:**

- **Buffer Memory**: Last 10 messages always included
- **Semantic Memory**: Top 5 relevant past messages added when useful
- **Summary**: Long conversations auto-summarized when > 15 messages
- **Token Management**: Keeps context under 2000 tokens for efficiency

---

### 📊 Best Practices and Tips

#### Optimal Workflow for Tender Analysis

1. **Initial Setup**

   - Upload all tender documents at once
   - Wait for all uploads to complete
   - Extract requirements from main specification documents first
   - Extract BoM from schedules/pricing documents

2. **Requirements Review**

   - Start with mandatory requirements (filter)
   - Sort by category to review similar items together
   - Use batch update for efficient compliance assessment
   - Export to Excel for sharing with team

3. **Chat for Clarification**

   - Use chat to find specific information quickly
   - Ask about ambiguous requirements
   - Generate summaries of complex sections
   - Compare requirements across multiple documents

4. **BoM Analysis**

   - Review extracted BoM for accuracy
   - Verify quantities and units
   - Export for integration with estimating tools
   - Check hierarchy for correct structure

#### Performance Tips

**For Large PDFs (>50 pages):**

- Extraction may take 3-5 minutes
- Consider splitting very large documents
- Background processing prevents UI blocking

**For Many Requirements (>1000):**

- Use filters to narrow results
- Pagination keeps UI responsive (100 items/page)
- Search is indexed for fast results
- Batch updates more efficient than individual

**For Chat Accuracy:**

- Select only relevant PDFs for your question
- Be specific in your questions
- Check source citations for verification
- Rephrase if answer seems off-topic

---

### ⚠️ Limitations and Known Issues

**Current Limitations**:

- PDF size limit: 100MB (configurable)
- Chat context window: 2000 tokens (configurable)
- Pagination: Fixed at 100 items per page
- Concurrent extractions: One per PDF at a time
- Supported formats: PDF only (no Word/Excel)

**Known Issues**:

- Very complex tables may need manual review
- Scanned PDFs require OCR (not included)
- Handwritten notes not extracted
- Images in PDFs not analyzed

**Workarounds**:

- For scanned PDFs: Use external OCR tool first
- For complex tables: Manual verification recommended
- For large documents: Split into smaller files if needed

---
