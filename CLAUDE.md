# Claude Development Context

This file contains Claude-specific development context and notes to help future Claude sessions understand the codebase and maintain consistency.

## Project Overview

This is a **Document Processing Service** built with FastAPI that processes documents using AI for structured data extraction. The system was developed collaboratively with Claude Code and includes:

- **Document upload and storage**
- **Format conversion** using LibreOffice
- **AI-powered data extraction** using OpenAI/Anthropic APIs
- **Template-based processing** with JSON schemas
- **Web interface** for testing and management

## Architecture Decisions

### Core Components

1. **FastAPI Backend** (`app/main.py`)
   - RESTful API with automatic OpenAPI docs
   - Database integration with SQLAlchemy
   - Environment-based configuration

2. **Document Conversion** (`app/conversion_service.py`)
   - LibreOffice headless for document conversion
   - Multi-format support: PDF, Word, Excel, PowerPoint, text
   - Robust encoding handling with fallback mechanisms

3. **LLM Integration** (`app/llm_service.py`)
   - Supports both OpenAI and Anthropic providers
   - Template-based prompt system
   - JSON schema validation for structured output

4. **Database Layer** (`app/models.py`, `app/database.py`)
   - PostgreSQL for production, SQLite for local development
   - Artifact storage with relationships
   - Template and extraction history

5. **Web Interface** (`app/static/index.html`)
   - Single-page application for testing
   - Full CRUD operations for templates
   - Real-time document processing

### Key Design Patterns

- **Environment-based configuration** - All settings via `.env` file
- **Service layer pattern** - Separate services for conversion and LLM
- **Template system** - Reusable processing configurations
- **Robust error handling** - Encoding fallbacks, detailed logging
- **Docker containerization** - Production-ready deployment

## Development History & Decisions

### Initial Setup
- Started with basic FastAPI structure
- Added PostgreSQL for data persistence
- Implemented Docker containerization early

### Document Conversion Evolution
1. **Simple text-only** - Initial basic implementation
2. **LibreOffice integration** - Added full format support
3. **Encoding fixes** - Solved Unicode issues with robust fallbacks
4. **PowerPoint support** - Extended to handle presentations

### LLM Integration Challenges
- **Template formatting issues** - Fixed KeyError with curly braces in JSON schemas
- **Provider flexibility** - Designed to switch between OpenAI/Anthropic easily
- **Response parsing** - Added markdown cleanup for reliable JSON extraction

### UI Development
- **Progressive enhancement** - Started with basic form, added advanced features
- **Template editing** - Full CRUD with form state management
- **Real-time feedback** - Progress indicators and detailed error messages

## Common Maintenance Tasks

### Adding New Document Formats

1. **Add MIME type detection** in `conversion_service.py`:
   ```python
   elif file_type == "application/your-mime-type":
       return self._extract_your_format_text(file_path)
   ```

2. **Implement extraction method**:
   ```python
   def _extract_your_format_text(self, file_path: str) -> str:
       # Format-specific extraction logic
   ```

3. **Update file input accept types** in `index.html`

### Adding New LLM Providers

1. **Extend LLMService** in `llm_service.py`:
   ```python
   elif config.provider == "new_provider":
       self.client = NewProviderClient(api_key=config.api_key)
   ```

2. **Add provider-specific call method**:
   ```python
   def _call_new_provider(self, system_prompt: str, user_prompt: str) -> str:
       # Provider-specific API call
   ```

3. **Update environment variables** in `.env` and `docker-compose.yml`

### Database Schema Changes

1. **Create migration** using Alembic:
   ```bash
   docker-compose exec web alembic revision --autogenerate -m "description"
   docker-compose exec web alembic upgrade head
   ```

2. **Update models** in `app/models.py`
3. **Update schemas** in `app/schemas.py` if API changes needed

## Configuration Management

### Environment Variables
All configuration is managed through `.env` file:

```bash
# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional tuning
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
```

### Docker Compose
- **Development**: Use `docker-compose.yml` with volume mounts
- **Production**: Consider `docker-compose.prod.yml` with optimizations

## Testing Strategy

### Manual Testing Workflow
1. **Upload diverse document types** - Test format support
2. **Create extraction templates** - Verify JSON schema handling
3. **Test AI extraction** - Check both success and failure cases
4. **Verify data persistence** - Check database storage
5. **Test conversion features** - Validate LibreOffice integration

### Automated Testing (Future)
- Unit tests for conversion service
- Integration tests for API endpoints
- End-to-end tests for document processing workflow

## Common Issues & Solutions

### Unicode Encoding Issues
**Problem**: `UnicodeDecodeError` when reading converted files
**Solution**: Use `_safe_read_text()` method with encoding fallbacks

### LibreOffice Conversion Failures
**Problem**: Conversion timeout or format not supported
**Solution**: Check LibreOffice installation, increase timeout, fallback to text extraction

### LLM API Failures
**Problem**: Rate limits, invalid API keys, network issues
**Solution**: Implement retry logic, validate configuration, graceful error handling

### Template Formatting Errors
**Problem**: `KeyError` when templates contain unescaped braces
**Solution**: Use safe string replacement as fallback to `.format()`

## Development Workflow

### Local Development
1. **Start infrastructure**: `docker-compose up -d db redis`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Run application**: `uvicorn app.main:app --reload`
4. **Access interface**: http://localhost:8000

### Container Development
1. **Full stack**: `./docker-compose up --build -d`
2. **View logs**: `./docker-compose logs -f web`
3. **Access shell**: `./docker-compose exec web bash`

### Adding Features
1. **Create feature branch**
2. **Add tests if applicable**
3. **Update documentation**
4. **Test with various document types**
5. **Update CLAUDE.md with context**

## File Structure Guide

```
artifacts/
├── app/
│   ├── main.py              # FastAPI application & routes
│   ├── conversion_service.py # Document conversion logic
│   ├── llm_service.py       # AI integration
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # Database configuration
│   └── static/
│       └── index.html       # Web interface
├── docker-compose.yml       # Container orchestration
├── Dockerfile              # Application container
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
├── README.md               # User documentation
└── CLAUDE.md               # This file - Claude context
```

## Future Enhancement Ideas

### Short Term
- [ ] Batch processing of multiple documents
- [ ] Export extracted data to CSV/Excel
- [ ] Template import/export functionality
- [ ] Basic user authentication

### Medium Term
- [ ] Advanced PowerPoint extraction with slide structure
- [ ] OCR support for scanned documents
- [ ] Webhook notifications for processing completion
- [ ] API rate limiting and usage analytics

### Long Term
- [ ] Multi-tenant support
- [ ] Workflow automation (chains of processing)
- [ ] Advanced AI features (summarization, classification)
- [ ] Integration with cloud storage providers

## Notes for Future Claude Sessions

### When Debugging Issues
1. **Check logs**: `./docker-compose logs web --tail=50`
2. **Verify environment**: Ensure `.env` variables are loaded
3. **Test document types**: Different formats may have unique issues
4. **Check LibreOffice**: Container includes full LibreOffice installation

### When Adding Features
1. **Maintain backward compatibility** - Existing templates should continue working
2. **Update both API and UI** - Keep interface in sync with backend
3. **Document configuration** - Add new env vars to `.env` and docker-compose
4. **Test error scenarios** - Handle failures gracefully

### Code Style Notes
- **Error handling**: Always log errors before returning user-friendly messages
- **Environment config**: Use `os.getenv()` with sensible defaults
- **Database operations**: Use dependency injection with `Depends(get_db)`
- **Async patterns**: FastAPI endpoints are async, background tasks for long operations

This documentation should be updated whenever significant changes are made to maintain development context for future work.