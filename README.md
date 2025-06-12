# Document Processing Service

A web service that receives uploaded files, processes them using LLMs to extract structured data, and provides APIs for managing document artifacts and their associated extractions.

## Features

- **File Upload & Storage**: Upload documents and store them as artifacts
- **Document Conversion**: Convert documents to various formats (PDF, text, CSV, HTML) using LibreOffice
- **LLM Processing**: Extract structured data using configurable prompts and JSON schemas
- **Multiple LLM Providers**: Support for OpenAI and Anthropic APIs
- **Template System**: Create reusable processing templates with custom prompts and schemas
- **Artifact Management**: Track all documents and their associated conversions and extractions

## Architecture

- **FastAPI**: Web framework for REST API
- **PostgreSQL**: Database for storing artifacts and metadata
- **LibreOffice**: Document conversion engine
- **Redis**: Caching and background job queue
- **Celery**: Async task processing
- **Docker**: Containerized deployment

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd artifacts
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## API Endpoints

### Artifacts
- `POST /artifacts/upload` - Upload a document
- `GET /artifacts` - List all artifacts
- `GET /artifacts/{id}` - Get artifact details
- `POST /artifacts/{id}/convert` - Convert artifact to different format

### Processing Templates
- `POST /templates` - Create processing template
- `GET /templates` - List all templates

### Data Extraction
- `POST /artifacts/{id}/extract` - Extract structured data using a template

## Example Usage

### 1. Upload a Document
```bash
curl -X POST "http://localhost:8000/artifacts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### 2. Create a Processing Template
```bash
curl -X POST "http://localhost:8000/templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invoice Extractor",
    "description": "Extract key fields from invoices",
    "system_prompt": "You are an expert at extracting structured data from invoices.",
    "user_prompt_template": "Extract the following information from this invoice:\n\n{document}",
    "json_schema": {
      "type": "object",
      "properties": {
        "invoice_number": {"type": "string"},
        "date": {"type": "string"},
        "total": {"type": "number"},
        "vendor": {"type": "string"}
      },
      "required": ["invoice_number", "date", "total", "vendor"]
    },
    "preferred_format": "text"
  }'
```

### 3. Extract Data
```bash
curl -X POST "http://localhost:8000/artifacts/{artifact_id}/extract" \
  -H "Content-Type: application/json" \
  -d '{"template_id": "{template_id}"}'
```

## Configuration

### Environment Variables

- `LLM_PROVIDER`: `openai` or `anthropic`
- `LLM_MODEL`: Model name (e.g., `gpt-3.5-turbo`, `claude-3-sonnet-20240229`)
- `LLM_API_KEY`: API key for your chosen provider
- `DATABASE_URL`: PostgreSQL connection string
- `LLM_TEMPERATURE`: Temperature for LLM responses (0.0-1.0)
- `LLM_MAX_TOKENS`: Maximum tokens in LLM response

### Supported Document Formats

**Input**: PDF, DOCX, DOC, XLSX, XLS, PPT, PPTX, TXT, RTF, ODT, ODS
**Output**: PDF, TXT, CSV, HTML

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis
docker-compose up -d db redis

# Run the application
uvicorn app.main:app --reload
```

### Running Tests
```bash
pytest tests/
```

## Production Deployment

1. Set up environment variables in `.env`
2. Configure PostgreSQL and Redis
3. Run with Docker Compose:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Security Considerations

- API keys are stored as environment variables
- File uploads are validated and stored securely
- Database connections use proper authentication
- Non-root user in Docker container

## Documentation

- **[API Documentation](API.md)** - Complete API reference with examples
- **[Deployment Guide](DEPLOYMENT.md)** - Development setup and production deployment
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Claude Development Context](CLAUDE.md)** - Development history and maintenance notes

## License

MIT License