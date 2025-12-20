NOTICE! This readme was generated (mostly) with AI because I'm lazy. I have reviewed it and I encountered no major issues. However, if you find any 
mistakes, let me know.

# Civilization Empire Builder

A browser-based strategy game where empires fight for control over a dynamic world map. Manage resources, build cities, construct buildings, train armies, and lead your civilization to victory! Important note: This game is not yet complete, but continues to expand as I add new features!

## Project Structure

- **backend/**: Python FastAPI server with game logic (in-memory state, no database (yet))
- **frontend/**: React + TypeScript web client

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** and **npm** (for frontend)

## Running the Demo

### Backend Setup & Execution

#### 1. Set Up Python Virtual Environment (Recommended)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Run the Backend Server

The backend requires an **ideology argument**. Valid options are:
- `monarchy`
- `neutral`
- `dictatorship`
- `republic`
- `theocracy`
- `anarchy`
- `communism`
- `socialism`

Run the server from the **capstone** root directory:

```bash
# Make sure you're in the capstone directory, not backend/
cd ..

# Run with desired ideology (example: monarchy)
python -m backend.main monarchy

# Other examples:
python -m backend.main republic
python -m backend.main dictatorship
```

The backend will start at `http://localhost:8000`

**Note:** The backend must be run as a module (using `-m` flag) from the capstone directory to properly resolve relative imports. I know it's dumb, but just run with it

### Frontend Setup & Execution

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Start the Development Server

```bash
npm start
```

The frontend will open at `http://localhost:3000`

## Complete Demo Workflow

1. **Terminal 1 - Start Backend:**
   ```bash
   cd capstone
   python -m backend.main monarchy
   ```

2. **Terminal 2 - Start Frontend:**
   ```bash
   cd capstone/frontend
   npm start
   ```

3. **Browser:** Navigate to `http://localhost:3000` and start playing!

## Game Features

- **Multiple Ideologies**: Choose between 8 different government systems, each with unique bonuses/penalties
- **Resource Management**: Produce and balance food, timber, metal, and wealth
- **City Building**: Construct diverse building types with different effects
- **Population Dynamics**: Manage morale, growth, and employment
- **Military System**: Train troops and build armies for conquest
- **World Map**: Explore and control multiple territories
- **Government Actions**: Implement taxes, subsidies, elections, and propaganda

## Available Dependencies

### Backend
- FastAPI (web framework)
- Uvicorn (ASGI server)  (not used yet)
- SQLAlchemy (ORM)  (not used yet)
- Pydantic (data validation)
- Python-dotenv (environment variables)

### Frontend
- React 19
- TypeScript
- React Scripts (build tools)

## Troubleshooting

### Backend Import Errors
If you see `ImportError: attempted relative import with no known parent package`:
- Make sure you're running from the **capstone** directory
- Use the `-m` flag: `python -m backend.main [ideology]`
- Don't run `python backend/main.py` directly

### Port Already in Use
- Backend default: 8000
- Frontend default: 3000
- If ports are in use, the servers will prompt you or you can change them in configuration

### Dependencies Issues
- Make sure you're in the virtual environment (you should see `(venv)` in your terminal)
- Try `pip install --upgrade pip` before installing requirements
- Clear npm cache: `npm cache clean --force` and retry `npm install`

## Architecture Overview

The backend uses a hierarchical package structure:
- **core/**: Foundational classes, constants, utilities
- **systems/**: Game mechanics, effects, jobs, data management
- **entities/**: Main game objects (Cities, Empires, Units, Buildings)
- **gameplay/**: Game engine, world map, event system
- **unit_classes/**: Specific building and troop definitions

All imports within the backend follow a consistent relative import scheme for better maintainability and reduced coupling.

## Development Notes

- Backend is currently **in-memory only** (state resets on server restart)
- Frontend communicates with backend via WebSocket/REST API
- Game logic runs on the backend; frontend is purely UI/display layer
- Each game tick represents one unit of game time where cities process jobs, resources update, etc.
