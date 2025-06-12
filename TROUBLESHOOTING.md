# Troubleshooting Guide

This guide covers common issues and their solutions for the Document Processing Service.

## Quick Diagnostic Commands

```bash
# Check service status
./docker-compose ps

# View recent logs
./docker-compose logs --tail=50 web
./docker-compose logs --tail=50 db

# Check disk space
df -h
du -sh ./storage/

# Test API connectivity
curl http://localhost:8000/health

# Check environment variables
./docker-compose exec web env | grep LLM
```

## Common Issues

### 1. Application Won't Start

#### Symptom: Container fails to start or exits immediately
```bash
./docker-compose logs web
# Shows: "Exited (1)"
```

#### Possible Causes & Solutions:

**A) Port Already in Use**
```bash
# Check what's using port 8000
lsof -i :8000
# or
netstat -tlnp | grep 8000

# Solution: Stop conflicting service or change port
./docker-compose down
./docker-compose up -d
```

**B) Environment Variables Missing**
```bash
# Check .env file exists
ls -la .env

# Verify required variables
cat .env | grep -E "(LLM_|OPENAI_|ANTHROPIC_)"

# Solution: Create/update .env file
cp .env.example .env
# Edit with your API keys
```

**C) Docker Build Issues**
```bash
# Clean build
./docker-compose down
docker system prune -f
./docker-compose up --build -d
```

### 2. Database Connection Issues

#### Symptom: "Connection refused" or database errors
```bash
./docker-compose logs web
# Shows: "Connection refused" or "could not connect to server"
```

#### Solutions:

**A) Database Not Running**
```bash
# Check database status
./docker-compose ps db

# Start database
./docker-compose up -d db

# Wait for database to be ready
./docker-compose logs -f db
# Look for: "database system is ready to accept connections"
```

**B) Database Connection String Issues**
```bash
# Check DATABASE_URL in environment
./docker-compose exec web env | grep DATABASE_URL

# For local development, ensure it matches docker-compose.yml:
# DATABASE_URL=postgresql://artifacts_user:artifacts_pass@db:5432/artifacts_db
```

**C) Database Migration Issues**
```bash
# Run migrations manually
./docker-compose exec web alembic upgrade head

# If migrations fail, check database schema
./docker-compose exec db psql -U artifacts_user -d artifacts_db -c "\dt"
```

### 3. LLM API Issues

#### Symptom: "LLM service not configured" or extraction failures

#### A) API Key Issues
```bash
# Check if API key is set
./docker-compose exec web env | grep -E "(OPENAI_|ANTHROPIC_|LLM_)"

# Verify API key format:
# OpenAI: starts with "sk-proj-" or "sk-"
# Anthropic: starts with "sk-ant-"

# Test API key manually
curl -H "Authorization: Bearer YOUR_OPENAI_KEY" \
  https://api.openai.com/v1/models
```

#### B) Provider Configuration Issues
```bash
# Check LLM provider setting
./docker-compose exec web env | grep LLM_PROVIDER

# Should be either "openai" or "anthropic"
# Make sure corresponding API key is set
```

#### C) Model Not Available
```bash
# Check model name
./docker-compose exec web env | grep LLM_MODEL

# Common working models:
# OpenAI: gpt-4o-mini, gpt-3.5-turbo, gpt-4
# Anthropic: claude-3-sonnet-20240229, claude-3-haiku-20240307
```

### 4. Document Upload Issues

#### Symptom: "Permission denied" or upload failures

#### A) Storage Permission Issues
```bash
# Check storage directory permissions
ls -la ./storage/

# Fix permissions
chmod -R 755 ./storage/
# or
sudo chown -R 1000:1000 ./storage/
```

#### B) File Size Issues
```bash
# Check file size limits
# Default FastAPI limit is 16MB

# For larger files, update nginx.conf or FastAPI settings
```

#### C) File Type Issues
```bash
# Check file MIME type
file --mime-type your-document.pdf

# Supported types are defined in conversion_service.py
# Check logs for "Unsupported file type" messages
```

### 5. Document Conversion Issues

#### Symptom: "Conversion failed" or LibreOffice errors

#### A) LibreOffice Installation Issues
```bash
# Check if LibreOffice is installed in container
./docker-compose exec web which libreoffice
./docker-compose exec web libreoffice --version

# Should show: LibreOffice 7.x.x.x
```

#### B) Conversion Timeout Issues
```bash
# Check logs for timeout errors
./docker-compose logs web | grep -i timeout

# Increase timeout in conversion_service.py if needed
# Default is 60 seconds
```

#### C) Unsupported Document Format
```bash
# Check file format
file your-document.ext

# Verify format is supported in conversion_service.py
# Add debug logging to see exact MIME type detected
```

### 6. Unicode/Encoding Issues

#### Symptom: "UnicodeDecodeError" or garbled text

#### A) File Encoding Issues
```bash
# Check file encoding
file -i your-document.txt

# The service uses fallback encodings:
# utf-8, utf-8-sig, latin1, cp1252, iso-8859-1

# Check logs for encoding warnings
./docker-compose logs web | grep -i encoding
```

#### B) Special Characters in Filenames
```bash
# Avoid special characters in filenames
# Use ASCII characters when possible
```

### 7. Template/Extraction Issues

#### Symptom: "Invalid JSON response" or template errors

#### A) JSON Schema Issues
```bash
# Validate JSON schema
# Use online JSON schema validators
# Common issues: missing required fields, invalid types
```

#### B) Template Prompt Issues
```bash
# Check for unescaped braces in prompts
# Avoid: "Extract {field_name} from document"
# Use: "Extract field_name from document"

# Or escape braces: "Extract {{field_name}} from document"
```

#### C) LLM Response Format Issues
```bash
# Check extraction logs for raw LLM responses
./docker-compose logs web | grep -A 5 -B 5 "Raw LLM response"

# Common issues:
# - LLM returns markdown code blocks
# - LLM returns explanation + JSON
# - LLM returns invalid JSON
```

### 8. Performance Issues

#### Symptom: Slow response times or timeouts

#### A) Resource Constraints
```bash
# Check container resource usage
./docker-compose exec web top
./docker-compose stats

# Check disk space
df -h
du -sh ./storage/

# Check memory usage
free -h
```

#### B) Large File Processing
```bash
# For large files, consider:
# 1. Increasing processing timeouts
# 2. Using background task processing
# 3. Splitting large documents
```

#### C) Database Performance
```bash
# Check database connections
./docker-compose exec db psql -U artifacts_user -d artifacts_db -c "SELECT * FROM pg_stat_activity;"

# Add database indexes if needed
# Check DEPLOYMENT.md for optimization queries
```

## Log Analysis

### Important Log Patterns

#### Success Patterns
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
DEBUG: About to extract from document with 1234 characters
DEBUG: Extraction result success: True
```

#### Error Patterns
```
ERROR: Failed to connect to database
ERROR: LLM extraction failed: 
ERROR: Conversion failed: 
UnicodeDecodeError: 'utf-8' codec can't decode
KeyError: 'template_field'
```

### Log Locations
```bash
# Application logs
./docker-compose logs web

# Database logs
./docker-compose logs db

# All services
./docker-compose logs

# Follow logs in real-time
./docker-compose logs -f web

# Search logs
./docker-compose logs web | grep -i error
./docker-compose logs web | grep -i "extraction failed"
```

## API Testing

### Manual API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test document upload
curl -X POST "http://localhost:8000/artifacts/upload" \
  -F "file=@test-document.pdf"

# Test template creation
curl -X POST "http://localhost:8000/templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Template",
    "description": "Test description",
    "system_prompt": "Extract data",
    "user_prompt_template": "Extract from: {document}",
    "json_schema": {"type": "object", "properties": {"test": {"type": "string"}}},
    "preferred_format": "text"
  }'

# Test extraction
curl -X POST "http://localhost:8000/artifacts/ARTIFACT_ID/extract" \
  -H "Content-Type: application/json" \
  -d '{"template_id": "TEMPLATE_ID"}'
```

### Using API Documentation
```bash
# Access interactive docs
open http://localhost:8000/docs

# Use Swagger UI to test all endpoints
# Check request/response formats
# Validate API behavior
```

## Environment Debugging

### Development vs Production Issues

#### Development Environment
```bash
# Check if using local SQLite
./docker-compose exec web env | grep DATABASE_URL
# Should show sqlite:///./artifacts.db for local dev

# Check file permissions for local development
ls -la ./storage/
```

#### Production Environment
```bash
# Check production environment variables
./docker-compose exec web env | grep -v -E "(PATH|PWD|SHLVL)"

# Verify production database connectivity
./docker-compose exec web python -c "
import os
from app.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

## Recovery Procedures

### Database Recovery
```bash
# Backup current database
./docker-compose exec db pg_dump -U artifacts_user artifacts_db > backup.sql

# Restore from backup
./docker-compose exec -T db psql -U artifacts_user artifacts_db < backup.sql

# Reset database (WARNING: Data loss)
./docker-compose down
docker volume rm artifacts_postgres_data
./docker-compose up -d db
./docker-compose exec web alembic upgrade head
```

### Storage Recovery
```bash
# Check storage directory structure
find ./storage -type f -name "*.pdf" | head -5
find ./storage -type f -name "*.txt" | head -5

# Fix storage permissions
chmod -R 755 ./storage/
chown -R 1000:1000 ./storage/

# Clean up corrupted files
find ./storage -size 0 -delete  # Remove empty files
```

### Complete Service Reset
```bash
# WARNING: This will delete all data
./docker-compose down -v
docker system prune -a
rm -rf ./storage/*
rm -f artifacts.db*

# Rebuild and restart
./docker-compose up --build -d

# Verify services
curl http://localhost:8000/health
```

## Getting Help

### Before Reporting Issues

1. **Check logs**: `./docker-compose logs web --tail=100`
2. **Verify environment**: Check `.env` file and environment variables
3. **Test with simple document**: Try a basic text file first
4. **Check disk space**: Ensure adequate storage available
5. **Verify API keys**: Test LLM provider API keys manually

### Information to Include in Bug Reports

```bash
# System information
docker --version
./docker-compose --version
uname -a

# Service status
./docker-compose ps

# Environment (sanitized)
./docker-compose exec web env | grep -E "(LLM_PROVIDER|LLM_MODEL)" 

# Recent logs
./docker-compose logs --tail=50 web

# File information (if upload issue)
file --mime-type problematic-file.ext
ls -la problematic-file.ext
```

### Resources

- **API Documentation**: http://localhost:8000/docs
- **Claude Development Context**: See `CLAUDE.md`
- **Deployment Guide**: See `DEPLOYMENT.md`
- **API Reference**: See `API.md`

This troubleshooting guide should help resolve most common issues. For complex problems, enable debug logging and analyze the full log output.