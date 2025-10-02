# SMS Extractor

**Systematic Review Management System - Data Extraction Tool**

A Django-based web application for systematic review research with AI-powered assistance, comprehensive paper management, and customizable data extraction schemas.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](docs/RELEASE_v1.0.0.md)
[![Django](https://img.shields.io/badge/django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

---

## 🚀 Quick Start

### One-Command Launch (Recommended)

```bash
./start.sh
```

The startup script will automatically:
- ✅ Check runtime environment
- ✅ Verify dependencies  
- ✅ Test database connection
- ✅ Apply pending migrations
- ✅ Start development server

### Manual Launch

```bash
cd sms_backend
python manage.py runserver
```

### Access the Application

After starting, open your browser and visit:

- **Home**: http://127.0.0.1:8000/
- **Paper Library**: http://127.0.0.1:8000/papers/
- **Schema Library**: http://127.0.0.1:8000/projects/schemas/
- **AI Assistant**: http://127.0.0.1:8000/agents/chat/
- **Admin Panel**: http://127.0.0.1:8000/admin/

**Default Admin Account:**
- Username: `admin`
- Password: `admin123`

---

## ✨ Key Features

### 📂 Project Management

- Create and manage systematic review projects
- Custom data extraction field groups
- Project progress tracking and statistics
- Multi-schema support for structured data extraction

### 📦 Schema Library (New!)

- **Custom Data Templates**: Create reusable schemas for structured data extraction
- **12+ Field Types**: Text, number, select, multi-select, boolean, date, year, URL, rating, etc.
- **AI Extraction Config**: Define AI prompts and strategies for automatic extraction
- **Export Configuration**: Customize Excel/CSV export format (column names, widths, alignment)
- **Immutability Design**: Schemas lock after first use to ensure data consistency
- **Version Control**: Duplicate schemas to create new versions while preserving history
- **Sample Schemas**: Includes ML Methods Comparison and Study Characteristics templates

### 📚 Paper Library

- **BibTeX Support**: Direct paste of BibTeX entries
- **Smart Parsing**: Auto-extract title, authors, year, journal, DOI
- **Citation Key Sync**: Paper ID and citation key automatically stay synchronized
- **PDF Management**: Upload and view PDF files online with drag-and-drop
- **Advanced Search**: Search by citation key, title, author, DOI
- **Bulk Import**: Import from Zotero/Mendeley/EndNote (.bib files)
- **Zotero-Style Interface**: Professional literature management experience

**Citation Key Synchronization:**
- When you edit a paper's ID, the citation key automatically updates to match
- BibTeX content is updated with the new citation key
- This ensures consistency across your entire citation database
- You'll receive a confirmation prompt before making ID changes

### 🔍 Data Extraction

- Structured data extraction
- Customizable extraction templates
- Batch paper processing
- Export extraction results

### 🤖 AI Assistant

- **Research Assistant**: Answer academic questions
- **Extraction Assistant**: Automated feature extraction
- **Workflow Assistant**: Process optimization suggestions
- **Context-Aware**: Understands project background

### 📊 Analytics

- Project progress visualization
- Extraction status statistics
- Data quality metrics

---

## 📋 Requirements

- Python 3.10+
- PostgreSQL 16
- Node.js (optional, for frontend tools)

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd sms_extractor
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy the environment template and fill in your configuration:

```bash
cp .env.template .env
```

Edit `.env` file with your settings:

```env
# Database
DB_NAME=sms_extractor_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# OpenAI (for AI Assistant)
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o
```

**Generate a secure SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Set up the database

Create PostgreSQL database:

```bash
createdb sms_extractor_db
```

Or using psql:

```sql
CREATE DATABASE sms_extractor_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sms_extractor_db TO your_username;
```

### 5. Run migrations

```bash
cd sms_backend
python manage.py migrate
```

### 6. Create admin user

```bash
python manage.py createsuperuser
```

### 7. Add sample data (optional)

```bash
# Add sample papers
python add_sample_papers.py

# Add sample schemas
python create_sample_schemas.py
```

### 8. Start the server

```bash
./start.sh
```

Or manually:

```bash
cd sms_backend
python manage.py runserver
```

---

## 📖 Usage Guide

### Scenario 1: Adding a Single Paper

1. Navigate to **Paper Library**
2. Click **"Upload Paper"**
3. Enter Paper ID (e.g., `smith2023machine`)
4. Paste BibTeX from Google Scholar
5. Upload PDF file (optional)
6. Submit - metadata is auto-extracted!

**Note:** The Paper ID and citation key will automatically stay synchronized. If you later edit the Paper ID, the citation key and all BibTeX references will update automatically.

### Scenario 2: Bulk Import from Reference Manager

1. Export BibTeX file from Zotero/Mendeley
2. Paper Library → **"Import BibTeX"**
3. Upload your `.bib` file
4. Review import preview
5. Confirm import - all papers added at once!

### Scenario 3: Creating a Custom Schema

1. Navigate to **Schema Library**
2. Click **"Create New Schema"** or duplicate an existing one
3. Define basic info (name, category, description)
4. Edit JSON to add fields:
   - Field types (text, number, select, etc.)
   - Validation rules
   - AI extraction prompts
   - Export configuration
5. Save as Draft - edit anytime
6. Use in projects - automatically locks on first use

### Scenario 4: Working on a Systematic Review Project

1. Create a new project from Dashboard
2. Associate relevant schemas from Schema Library
3. Add papers to your project from Paper Library
4. Use AI or manual extraction to fill schema fields
5. View data in table format (Excel-like)
6. Export results to Excel/CSV/LaTeX

---

## ❓ FAQ

### Q: Can I change a paper's ID after creation?

**A:** Yes! The system handles this automatically:
- When you change the Paper ID in the edit form, you'll see a confirmation prompt
- The citation key will automatically update to match the new ID
- All BibTeX content will be updated with the new citation key
- Any associated extractions will be preserved
- The change is seamless and maintains data integrity

### Q: Do I need OpenAI API for basic features?

**A:** No. Core features (paper management, extraction) work without OpenAI API. You only need it for the AI Assistant chat feature.

### Q: What citation formats are supported?

**A:** Currently we support BibTeX format. We auto-extract metadata from BibTeX entries and maintain synchronization between paper IDs and citation keys.

### Q: Can I import papers without PDFs?

**A:** Yes! PDFs are optional. You can import just the metadata and add PDFs later. The detail page provides a quick upload button for adding PDFs to existing papers.

### Q: What happens to papers when I delete a project?

**A:** Papers in the library are independent of projects. Deleting a project removes the association but keeps all papers intact in your library.

### Q: How do I backup my data?

**A:** Use PostgreSQL backup:

```bash
pg_dump sms_extractor_db > backup.sql
```

---

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_NAME` | PostgreSQL database name | `sms_extractor_db` |
| `DB_USER` | Database username | - |
| `DB_PASSWORD` | Database password | - |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `SECRET_KEY` | Django secret key | - |
| `DEBUG` | Debug mode | `False` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `MAX_UPLOAD_SIZE` | Max PDF size (MB) | `50` |

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Built with Django and Bootstrap
- AI powered by OpenAI
- Inspired by Zotero for paper management interface

---

## � Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Schema User Guide](docs/SCHEMA_USER_GUIDE.md)** - Complete guide to creating and using schemas
- **[Schema Design](docs/SCHEMA_DESIGN.md)** - Technical design and architecture
- **[Schema Export Implementation](docs/SCHEMA_EXPORT_IMPLEMENTATION.md)** - Export functionality details
- **[Release Notes v1.0.0](docs/RELEASE_v1.0.0.md)** - Version 1.0.0 features and changes
- **[Feature Group Enhancement](docs/FEATURE_GROUP_ENHANCEMENT.md)** - Advanced extraction features

---

## �📧 Contact

For questions or support, please open an issue on GitHub.

---

## 🔧 Development

### Project Structure

```
sms_extractor/
├── sms_backend/           # Django project root
│   ├── papers/            # Paper Library app
│   ├── projects/          # Project management
│   ├── extractions/       # Data extraction
│   ├── agents/            # AI Assistant
│   ├── dashboard/         # Dashboard & analytics
│   └── sms_backend/       # Project settings
├── data/                  # Data storage
│   └── projects/          # Project files
│       └── papers/        # Uploaded PDFs
├── start.sh               # Startup script
├── .env.template          # Environment template
└── README.md              # This file
```

### Running Tests

```bash
cd sms_backend
python manage.py test
```

### Code Style

We follow PEP 8. Format your code with:

```bash
black .
flake8 .
```

---

**Happy Systematic Reviewing! 📚✨**
