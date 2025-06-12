# Deployment & Development Guide

This guide covers development setup, deployment options, and operational considerations for the Document Processing Service.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- Text editor
- API keys for LLM provider (OpenAI or Anthropic)

### 1. Clone and Configure
```bash
git clone <repository-url>
cd artifacts
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 2. Start Services
```bash
# Development with auto-rebuild
./docker-compose up --build -d

# Check status
./docker-compose ps

# View logs
./docker-compose logs -f web
```

### 3. Access Application
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Development Setup

### Local Development (Without Docker)

#### 1. Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 2. Start Infrastructure Services
```bash
# Start only database and Redis
./docker-compose up -d db redis
```

#### 3. Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Edit .env for local development
# Set DATABASE_URL for local PostgreSQL or use SQLite:
# DATABASE_URL=sqlite:///./artifacts.db
```

#### 4. Run Application
```bash
# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Development with Docker (Recommended)

#### Hot Reload Setup
```bash
# Mount source code for development
./docker-compose -f docker-compose.dev.yml up --build -d
```

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://artifacts_user:artifacts_pass@db:5432/artifacts_db
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_MODEL=${LLM_MODEL}
      - LLM_API_KEY=${OPENAI_API_KEY}
      - LLM_TEMPERATURE=${LLM_TEMPERATURE}
      - LLM_MAX_TOKENS=${LLM_MAX_TOKENS}
    volumes:
      - ./app:/app/app:ro  # Mount source code
      - ./storage:/app/storage
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=artifacts_db
      - POSTGRES_USER=artifacts_user
      - POSTGRES_PASSWORD=artifacts_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"  # Expose for local access
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"  # Expose for local access

volumes:
  postgres_data:
```

### Database Management

#### Database Migrations (Alembic)
```bash
# Generate migration
./docker-compose exec web alembic revision --autogenerate -m "description"

# Apply migrations
./docker-compose exec web alembic upgrade head

# View migration history
./docker-compose exec web alembic history

# Rollback migration
./docker-compose exec web alembic downgrade -1
```

#### Direct Database Access
```bash
# Connect to PostgreSQL
./docker-compose exec db psql -U artifacts_user -d artifacts_db

# Useful queries
SELECT COUNT(*) FROM artifacts;
SELECT COUNT(*) FROM extractions WHERE success = true;
SELECT * FROM processing_templates;
```

#### Database Backup/Restore
```bash
# Backup
./docker-compose exec db pg_dump -U artifacts_user artifacts_db > backup.sql

# Restore
./docker-compose exec -T db psql -U artifacts_user artifacts_db < backup.sql
```

## Production Deployment

### Environment Configuration

#### Production .env
```bash
# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-proj-your-production-key
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000

# Database (Use managed PostgreSQL in production)
DATABASE_URL=postgresql://user:password@prod-db-host:5432/artifacts_db

# Security
SECRET_KEY=your-secret-key-here

# Optional: Redis for caching/queues
REDIS_URL=redis://prod-redis-host:6379/0

# Storage
STORAGE_PATH=/app/storage
```

### Docker Production Setup

#### 1. Production Dockerfile
Create `Dockerfile.prod`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    libmagic1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/storage/uploads /app/storage/conversions && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/storage

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

#### 2. Production Docker Compose
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  web:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_MODEL=${LLM_MODEL}
      - LLM_API_KEY=${OPENAI_API_KEY}
      - LLM_TEMPERATURE=${LLM_TEMPERATURE}
      - LLM_MAX_TOKENS=${LLM_MAX_TOKENS}
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=artifacts_db
      - POSTGRES_USER=artifacts_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U artifacts_user -d artifacts_db"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

#### 3. Production Requirements
Add to `requirements.prod.txt`:
```txt
# Include all from requirements.txt plus:
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

### Cloud Deployment Options

#### AWS ECS/Fargate
1. **Build and push image to ECR**
2. **Create task definition with environment variables**
3. **Set up RDS PostgreSQL and ElastiCache Redis**
4. **Configure ALB for load balancing**
5. **Set up CloudWatch logging**

#### Google Cloud Run
1. **Build image and push to GCR**
2. **Deploy with Cloud Run**
3. **Use Cloud SQL for PostgreSQL**
4. **Configure environment variables in Cloud Run**

#### Azure Container Instances
1. **Push image to ACR**
2. **Deploy container group**
3. **Use Azure Database for PostgreSQL**
4. **Configure application settings**

#### DigitalOcean App Platform
1. **Connect GitHub repository**
2. **Configure build settings**
3. **Add managed PostgreSQL database**
4. **Set environment variables**

### Monitoring & Logging

#### Application Monitoring
```python
# Add to app/main.py
import logging
from fastapi import Request
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
    return response
```

#### Health Checks
```python
# Enhanced health check
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Check database
        db.execute("SELECT 1")
        
        # Check LLM service
        llm_status = "configured" if llm_service else "not configured"
        
        return {
            "status": "healthy",
            "database": "connected",
            "llm_service": llm_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
```

#### Prometheus Metrics
```bash
# Add to requirements.txt
prometheus-fastapi-instrumentator==6.1.0
```

```python
# Add to app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Document Processing Service")

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)
```

### Security Considerations

#### 1. API Security
```python
# Add API key authentication
from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException

security = HTTPBearer()

async def verify_api_key(token: str = Depends(security)):
    if token.credentials != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token.credentials

# Protect endpoints
@app.post("/artifacts/upload")
async def upload_artifact(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    # ... implementation
```

#### 2. File Upload Security
```python
# Validate file types and sizes
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    # ... other allowed types
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

async def validate_upload(file: UploadFile):
    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Check MIME type
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Reset file pointer
    await file.seek(0)
    return file
```

#### 3. Environment Security
```bash
# Use secrets management
# AWS: AWS Secrets Manager
# GCP: Secret Manager
# Azure: Key Vault
# Kubernetes: Secrets

# Don't commit .env files
echo ".env" >> .gitignore
echo "*.log" >> .gitignore
echo "storage/" >> .gitignore
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_artifacts_upload_date ON artifacts(upload_date);
CREATE INDEX idx_extractions_artifact_id ON extractions(artifact_id);
CREATE INDEX idx_extractions_template_id ON extractions(template_id);
CREATE INDEX idx_extractions_success ON extractions(success);
```

#### 2. Caching
```python
# Add Redis caching for templates
import redis
from functools import wraps

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

def cache_template(func):
    @wraps(func)
    async def wrapper(template_id: str, *args, **kwargs):
        cache_key = f"template:{template_id}"
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        result = await func(template_id, *args, **kwargs)
        redis_client.setex(cache_key, 3600, json.dumps(result))
        return result
    return wrapper
```

#### 3. Background Processing
```python
# Use Celery for long-running tasks
from celery import Celery

celery = Celery(
    "document_processor",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

@celery.task
def process_document_async(artifact_id: str, template_id: str):
    # Long-running processing task
    pass

# In endpoint
@app.post("/artifacts/{artifact_id}/extract_async")
async def extract_data_async(artifact_id: str, request: ExtractionRequest):
    task = process_document_async.delay(artifact_id, request.template_id)
    return {"task_id": task.id, "status": "processing"}
```

### Backup Strategy

#### 1. Database Backups
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_${DATE}.sql"

# Create backup
./docker-compose exec -T db pg_dump -U artifacts_user artifacts_db > "${BACKUP_FILE}"

# Compress
gzip "${BACKUP_FILE}"

# Upload to cloud storage (example: AWS S3)
aws s3 cp "${BACKUP_FILE}.gz" s3://your-backup-bucket/db-backups/

# Clean up old backups (keep 30 days)
find . -name "backup_*.sql.gz" -mtime +30 -delete
```

#### 2. File Storage Backups
```bash
#!/bin/bash
# backup_files.sh
DATE=$(date +%Y%m%d_%H%M%S)

# Sync storage to cloud
rsync -av --delete ./storage/ s3://your-backup-bucket/storage-${DATE}/

# Or use cloud-specific tools
# AWS: aws s3 sync ./storage/ s3://your-bucket/storage/
# GCP: gsutil -m rsync -r -d ./storage/ gs://your-bucket/storage/
```

### Troubleshooting Commands

```bash
# Check container status
./docker-compose ps

# View logs
./docker-compose logs -f web
./docker-compose logs -f db

# Connect to containers
./docker-compose exec web bash
./docker-compose exec db psql -U artifacts_user artifacts_db

# Check disk usage
./docker-compose exec web df -h
du -sh ./storage/

# Monitor resources
./docker-compose exec web top
./docker-compose stats

# Restart services
./docker-compose restart web
./docker-compose restart db

# Clean up
./docker-compose down
docker system prune -a
```

This deployment guide provides a comprehensive foundation for both development and production deployment of the Document Processing Service.