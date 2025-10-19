# FitScore by Clarivue AI

🚀 **Next-Generation AI-Powered Resume Optimization Platform**

FitScore is an advanced AI-powered platform that revolutionizes resume optimization by reverse-engineering ATS (Applicant Tracking System) algorithms. Our sophisticated AI models analyze resumes and job descriptions to provide actionable intelligence that helps candidates get past automated screening systems and land their dream jobs.

[![AI-Powered](https://img.shields.io/badge/AI-Powered-blue.svg)](https://github.com/tolutally/fitcheck)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python)](https://www.python.org/)

## ✨ Enhanced Features

### 🎯 **Advanced Resume Analysis**
- **AI-Powered Scoring**: Comprehensive ATS compatibility analysis
- **Keyword Optimization**: Intelligent keyword density analysis and recommendations
- **Structure Analysis**: Resume format and section optimization
- **Experience Matching**: Skills and experience alignment with job requirements

### 🔍 **Intelligent Job Matching**
- **Resume-Job Compatibility**: Advanced matching algorithms with detailed scoring
- **Gap Analysis**: Identifies missing skills and experience
- **Improvement Suggestions**: AI-generated recommendations for better matches
- **Bulk Analysis**: Compare one resume against multiple job descriptions

### 📊 **Comprehensive Analytics Dashboard**
- **Match History**: Track all resume-job analyses over time
- **Performance Metrics**: Detailed breakdown of match scores
- **Trend Analysis**: Monitor improvement over multiple iterations
- **Comparison Tools**: Side-by-side resume performance analysis

### 🤖 **Local AI Integration**
- **Privacy-First**: All AI processing happens locally using Ollama
- **No External APIs**: Complete functionality without external dependencies
- **Advanced Models**: Gemma 2B for analysis + Nomic embeddings for semantic matching
- **Real-time Processing**: Fast, responsive AI-powered insights

## Architecture Overview

FitScore is built as a modern full-stack application with clear separation between frontend and backend services:

- **Backend**: Python FastAPI application with AI processing capabilities
- **Frontend**: Next.js TypeScript application with modern React patterns
- **AI Integration**: Local Ollama models for resume analysis and improvement
- **Database**: SQLite with async SQLAlchemy ORM for data persistence

## Backend Architecture (`apps/backend/`)

### Technology Stack
- **Framework**: FastAPI with async/await patterns
- **Database**: SQLite with SQLAlchemy ORM (async sessions)
- **AI Integration**: Ollama serving Gemma 2B and Nomic embedding models
- **Document Processing**: MarkItDown for PDF/DOCX conversion
- **Validation**: Pydantic models for type safety and validation

### Core Components

#### 1. Application Structure
```
apps/backend/app/
├── models/          # SQLAlchemy database models
├── services/        # Business logic layer (service pattern)
├── api/router/      # FastAPI route handlers  
├── agent/           # AI agent management and providers
├── prompt/          # AI prompt templates and schemas
├── schemas/         # Pydantic models and JSON schemas
├── core/            # Configuration, database, exceptions
└── main.py          # FastAPI application entry point
```

#### 2. Data Models & Domain Logic

**Resume Processing Pipeline:**
- **Raw Resume Storage**: `Resume` model stores uploaded files with metadata
- **Document Processing**: MarkItDown converts PDF/DOCX to structured text
- **AI Analysis**: Ollama models extract structured data from resume content
- **Structured Storage**: `ProcessedResume` model stores parsed resume sections

**Core Data Models:**
```python
# Raw data storage
Resume: {id, resume_id, content, content_type, created_at}
Job: {id, job_id, resume_id, content, created_at}

# AI-processed structured data
ProcessedResume: {
    resume_id, personal_data, experiences, projects,
    skills, education, extracted_keywords, processed_at
}
ProcessedJob: {
    job_id, job_title, company_profile, qualifications,
    key_responsibilities, extracted_keywords, processed_at
}
```

#### 3. Service Layer Architecture

**Resume Service** (`services/resume_service.py`):
- File upload validation and processing
- Document parsing with MarkItDown
- AI-powered content extraction
- Database operations with proper error handling

**AI Agent Management** (`agent/`):
- `AgentManager`: Orchestrates AI model interactions
- Structured response generation with validation
- Embedding generation for similarity matching
- Error handling and retry logic for AI failures

**Database Services** (`core/database.py`):
- Async SQLAlchemy session management
- Connection pooling and optimization
- Transaction handling and rollback support

#### 4. Enhanced API Layer (`api/router/v1/`)

**📄 Resume Processing Endpoints:**
- `POST /api/v1/resumes/upload` - Basic resume upload and processing
- `POST /api/v1/resumes/process-enhanced` - **🆕 AI-powered resume analysis with FitScore scoring**
- `POST /api/v1/resumes/improve` - Legacy resume improvement suggestions
- `POST /api/v1/resumes/analyze-match` - **🆕 Resume-job matching with AI insights**
- `GET /api/v1/resumes/{resume_id}/matches` - **🆕 Match history and analytics**
- `GET /api/v1/resumes` - Retrieve resume data and analysis

**💼 Job Processing Endpoints:**
- `POST /api/v1/jobs/upload` - Basic job description processing  
- `POST /api/v1/jobs/process-enhanced` - **🆕 Advanced job requirement extraction**
- `GET /api/v1/jobs` - Retrieve job data and requirements

**📊 Advanced Analytics Endpoints:**
- `GET /api/v1/analysis/dashboard/{resume_id}` - **🆕 Comprehensive analytics dashboard**
- `GET /api/v1/analysis/bulk-analysis/{resume_id}` - **🆕 Multi-job comparison analysis**
- `GET /api/v1/analysis/comparison` - **🆕 Resume performance comparison**

**🔧 Health & Monitoring:**
- `GET /ping` - Health check with database connectivity
- `GET /api/docs` - **Enhanced Swagger/OpenAPI documentation with FitScore branding**
- `GET /api/redoc` - Alternative API documentation

#### 5. AI Processing Workflow

1. **Document Upload**: FastAPI receives PDF/DOCX files
2. **File Validation**: Check file type, size, and content integrity  
3. **Document Parsing**: MarkItDown converts to structured text
4. **AI Processing**: Ollama models extract structured data using prompts
5. **Validation**: Pydantic models ensure data integrity
6. **Storage**: Save both raw and processed data to database
7. **Response**: Return structured JSON with extracted information

#### 6. Configuration & Environment

**Environment Variables:**
```bash
# Core application settings
PROJECT_NAME=Fitscore
ALLOWED_ORIGINS=["http://localhost:3000"]

# Database configuration
ASYNC_DATABASE_URL=sqlite+aiosqlite:///./fitscore.db

# AI model configuration
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LL_MODEL=gemma:2b
EMBEDDING_MODEL=nomic-embed-text
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+  
- Ollama with required models

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fitscore.git
cd fitscore

# Install Ollama models
ollama pull gemma:2b
ollama pull nomic-embed-text

# Setup backend
cd apps/backend
pip install -r requirements.txt
python main.py

# Setup frontend (in new terminal)
cd apps/frontend
npm install
npm run dev
```

Access FitScore at `http://localhost:3000` 🎉

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# Access at http://localhost:3000
```

## Frontend Architecture (`apps/frontend/`)

### Technology Stack
- **Framework**: Next.js 15+ with App Router
- **Language**: TypeScript with strict mode
- **Styling**: Tailwind CSS 4.0 utility-first approach
- **Components**: Radix UI primitives with custom composition
- **State Management**: React hooks and context patterns

### Application Structure
```
apps/frontend/
├── app/                 # Next.js App Router pages and layouts
│   ├── resume/         # Resume upload and analysis pages
│   ├── jobs/           # Job description management
│   └── dashboard/      # Main application dashboard
├── components/         # Reusable UI components
│   ├── common/         # Shared components (file upload, forms)
│   ├── resume/         # Resume-specific components
│   └── jobs/           # Job-related components
└── lib/                # Utilities and configurations
    ├── api/            # Backend API client functions
    ├── types/          # TypeScript type definitions
    └── utils/          # Helper functions and utilities
```

### Key Features

#### 1. Resume Processing Interface
- **File Upload**: Drag-and-drop interface for PDF/DOCX files
- **Progress Tracking**: Real-time upload and processing status
- **Validation**: Client-side file type and size validation
- **Error Handling**: User-friendly error messages and retry options

#### 2. Job Description Analysis
- **Text Input**: Rich text area for job description entry
- **Batch Processing**: Support for multiple job descriptions
- **Keyword Extraction**: Visual highlighting of important terms
- **Match Scoring**: Real-time compatibility scoring with resumes

#### 3. AI-Powered Improvements
- **Resume Analysis**: Detailed breakdown of resume sections
- **Improvement Suggestions**: AI-generated recommendations
- **ATS Optimization**: Specific advice for passing automated screening
- **Keyword Optimization**: Suggestions for relevant skill keywords

#### 4. Type Safety & API Integration

**TypeScript Interfaces:**
```typescript
interface ProcessedResume {
  resumeId: string;
  personalData: PersonalData;
  experiences: Experience[];
  skills: string[];
  education: Education[];
  extractedKeywords: string[];
  processedAt: string;
}

interface JobDescription {
  jobId: string;
  jobTitle: string;
  companyProfile: string;
  qualifications: string[];
  keyResponsibilities: string[];
  extractedKeywords: string[];
}
```

**API Client Functions:**
```typescript
// Resume operations
export async function uploadResume(file: File): Promise<UploadResponse>
export async function getResumeAnalysis(resumeId: string): Promise<ProcessedResume>

// Job operations  
export async function uploadJobDescriptions(jobs: JobInput[]): Promise<JobResponse>

// Improvement operations
export async function getResumeImprovements(resumeId: string, jobId: string): Promise<ImprovementSuggestions>
```

## Development Workflow

### Setting up the Development Environment

1. **Prerequisites:**
   ```bash
   # Install Ollama for AI processing
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull required AI models
   ollama pull gemma:2b
   ollama pull nomic-embed-text
   ```

2. **Backend Setup:**
   ```bash
   cd apps/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.sample .env
   # Edit .env with your configuration
   
   # Start the backend server
   uvicorn app.main:app --reload --port 8001
   ```

3. **Frontend Setup:**
   ```bash
   cd apps/frontend
   npm install
   
   # Configure API endpoint
   echo "API_URL=http://localhost:8001" > .env.local
   
   # Start the development server
   npm run dev
   ```

### Application Flow

1. **Resume Upload**: User uploads PDF/DOCX resume file
2. **Document Processing**: Backend parses document and extracts text
3. **AI Analysis**: Ollama models analyze content and extract structured data
4. **Data Storage**: Processed resume data saved to database
5. **Job Matching**: User adds job descriptions for comparison
6. **Improvement Generation**: AI generates specific improvement suggestions
7. **Results Display**: Frontend shows analysis, scores, and recommendations

## 📖 Enhanced API Documentation

### 🎯 Core FitScore Endpoints

**Enhanced Resume Processing**
```http
POST /api/v1/resumes/process-enhanced
Content-Type: multipart/form-data

Response: {
  "status": "success", 
  "resume_id": "uuid",
  "data": {
    "personal_data": {...},
    "experiences": [...],
    "skills": [...],
    "ai_analysis_scores": {
      "overall_score": 85,
      "ats_compatibility": 78,
      "keyword_optimization": 82,
      "structure_quality": 90
    },
    "ai_feedback": {
      "strengths": [...],
      "improvements": [...],
      "critical_issues": [...]
    }
  }
}
```

**Enhanced Job Analysis**
```http
POST /api/v1/jobs/process-enhanced
Content-Type: application/json

{
  "job_description": "string",
  "resume_id": "uuid"
}

Response: {
  "job_id": "uuid",
  "structured_job": {
    "job_title": "Senior Software Engineer",
    "requirements": [...],
    "nice_to_have": [...],
    "extracted_keywords": [...]
  },
  "ai_analysis": {
    "complexity_score": 75,
    "experience_level": "Senior"
  }
}
```

**Resume-Job Matching**
```http
POST /api/v1/resumes/analyze-match
Content-Type: application/json

{
  "resume_id": "uuid",
  "job_id": "uuid"
}

Response: {
  "match_score": 87,
  "detailed_analysis": {
    "skills_match": 85,
    "experience_match": 90,
    "education_match": 80
  },
  "recommendations": [...],
  "missing_keywords": [...],
  "improvement_priority": "high"
}
```

### 📊 Analytics Dashboard Endpoints

**Comprehensive Dashboard**
```http
GET /api/v1/analysis/dashboard/{resume_id}

Response: {
  "resume_summary": {...},
  "match_history": [...],
  "performance_trends": {...},
  "improvement_tracking": {...}
}
```

**Bulk Analysis**
```http
GET /api/v1/analysis/bulk-analysis/{resume_id}

Response: {
  "job_matches": [...],
  "comparative_analysis": {...},
  "market_insights": {...}
}
```

### Legacy Endpoints (Maintained for Compatibility)

**Basic Resume Upload**
```http
POST /api/v1/resumes/improve
Content-Type: application/json

{
  "resume_id": "uuid",
  "job_id": "uuid"
}

Response: {
  "improvements": ImprovementSuggestion[],
  "match_score": number,
  "key_recommendations": string[]
}
```

### Job Description Endpoints

**Upload Job Descriptions**
```http
POST /api/v1/jobs/upload
Content-Type: application/json

{
  "resume_id": "uuid",
  "job_descriptions": [
    {
      "company": "string",
      "job_title": "string", 
      "job_description": "string"
    }
  ]
}
```

## Security & Data Handling

### PII Protection
- **Temporary File Processing**: Documents processed in memory when possible
- **Secure File Cleanup**: Automatic deletion of temporary files
- **Data Sanitization**: Sensitive information masked in logs
- **Input Validation**: Strict validation of all user inputs

### AI Safety
- **Structured Prompts**: Prevent prompt injection attacks
- **Response Validation**: All AI outputs validated against schemas
- **Fallback Mechanisms**: Graceful handling of AI service failures
- **Rate Limiting**: Protection against excessive API usage

## Deployment

### Production Configuration

**Backend Environment:**
```bash
PROJECT_NAME=Fitscore
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@host/db
LLM_BASE_URL=https://your-ollama-instance.com
ALLOWED_ORIGINS=["https://your-domain.com"]
```

**Frontend Build:**
```bash
npm run build
npm start
```

### Health Monitoring
- **Health Checks**: `/ping` endpoint for service monitoring
- **Structured Logging**: JSON logs for production debugging
- **Error Tracking**: Comprehensive error handling and reporting
- **Performance Metrics**: Database query optimization and AI response timing

## Contributing

1. **Code Standards**: Follow TypeScript strict mode and Python type hints
2. **Testing**: Write tests for all new features and bug fixes
3. **Documentation**: Update documentation for API changes
4. **Security**: Review all changes for potential security implications

## 🗺️ Roadmap

- [ ] **Advanced AI Models**: Integration with multiple LLM providers
- [ ] **Resume Templates**: Industry-specific resume templates
- [ ] **Interview Preparation**: AI-generated interview questions
- [ ] **Salary Analytics**: Market-based salary recommendations
- [ ] **Mobile App**: React Native mobile application
- [ ] **Team Collaboration**: Multi-user workspace features

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Guidelines
1. **Code Standards**: Follow TypeScript strict mode and Python type hints
2. **Testing**: Write comprehensive tests for all new features
3. **Documentation**: Update API documentation for any changes
4. **Security**: Review all changes for potential security implications

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/fitscore/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fitscore/discussions)
- **Email**: support@clarivue.ai

---

**Built with ❤️ by [Clarivue AI](https://clarivue.ai)**

*Transform your resume into a career catalyst with AI-powered insights.*
