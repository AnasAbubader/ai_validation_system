# AI Validation System

A microservices-based AI validation system built with React frontend, Python middleware, ResNet model server, and PostgreSQL database.

## Project Structure
```
ai-validation-system/
├── frontend/           # React frontend application
├── middleware/         # Python middleware service
├── resnet_server/      # Python ResNet model server
├── database/          # PostgreSQL database
└── docker-compose.yml # Docker composition file
```

## Prerequisites
- Docker and Docker Compose
- Node.js (v16 or higher)
- Python 3.12
- Git

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/AnasAbubader/ai_validation_system.git
cd ai-validation-system
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Middleware Setup
```bash
cd middleware

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### 4. ResNet Server Setup
```bash
cd resnet_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### 5. Database Setup
```bash
cd database

# Create .env file for database configuration
cp .env.example .env
# Edit .env with your database configuration
```

## Running the Application

### Using Docker (Recommended)
```bash
# Build and start all services
docker-compose up --build

# To run in detached mode
docker-compose up -d --build

# After all services are running, run the setup script for EZKL library
python setup.py
```

### Manual Start (Development)
1. Start Frontend:
```bash
cd frontend
npm install
npm run dev
# Frontend will run on http://localhost:3000
```

2. Start Middleware:
```bash
cd middleware
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Middleware will run on http://localhost:8000
```

3. Start ResNet Server:
```bash
cd resnet_server
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
# ResNet server will run on http://localhost:8001
```

4. Start Database:
```bash
# If using Docker for database only
docker-compose up database

# After all services are running, run the setup script for EZKL library
python setup.py
```

## Environment Variables

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
```

### Middleware (.env)
```
RESNET_SERVER_URL=http://localhost:8001
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### ResNet Server (.env)
```
MODEL_PATH=app/models/resnet34.pth
ONNX_MODEL_PATH=app/models/onnx/resnet34.onnx
```

### Database (.env)
```
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=dbname
```

## API Documentation

### Middleware API Endpoints
- `POST /api/validate` - Submit image for validation
- `GET /api/results` - Get validation results

### ResNet Server API Endpoints
- `POST /predict` - Get predictions for an image

## Testing
Each service includes its own test suite:

```bash
# Frontend tests
cd frontend
npm test

# Middleware tests
cd middleware
python -m pytest

# ResNet server tests
cd resnet_server
python -m pytest
```

## Troubleshooting

### Common Issues
1. **EZKL Setup Issues**
   - If the setup.py script fails, ensure all services are running properly
   - Check that you have the necessary permissions to install and configure EZKL
   - Refer to the EZKL documentation for specific troubleshooting

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials in .env files
   - Ensure database port is not in use

2. **Port Conflicts**
   - Check if ports 3000, 8000, 8001, and 5432 are available
   - Modify port mappings in docker-compose.yml if needed

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License
[Your License Here]