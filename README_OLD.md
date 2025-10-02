# SMS Extractor# SMS Extractor# SMS Extractor



**Systematic Review Management System - Data Extraction Tool**



A Django-based web application for systematic review research with AI-powered assistance and comprehensive paper management.**Systematic Review Management System - Data Extraction Tool****Systematic Review Management System - Data Extraction Tool**



---



## 🚀 Quick StartA Django-based web application for systematic review research with AI-powered assistance and comprehensive paper management.A Django-based web application for systematic review research with AI-powered assistance and comprehensive paper management.



### One-Command Launch (Recommended)



```bash------

./start.sh

```



The startup script will automatically:## 🚀 Quick Start## 🚀 Quick Start

- ✅ Check runtime environment

- ✅ Verify dependencies

- ✅ Test database connection

- ✅ Apply pending migrations### One-Command Launch (Recommended)### One-Command Launch (Recommended)

- ✅ Start development server



### Manual Launch

```bash```bash

```bash

cd sms_backend./start.sh./start.sh

python manage.py runserver

`````````



### Access the Application



After starting, open your browser and visit:The startup script will automatically:The startup script will automatically:



- **Home**: http://127.0.0.1:8000/- ✅ Check runtime environment- ✅ Check runtime environment

- **Paper Library**: http://127.0.0.1:8000/papers/

- **AI Assistant**: http://127.0.0.1:8000/agents/chat/- ✅ Verify dependencies- ✅ Verify dependencies

- **Admin Panel**: http://127.0.0.1:8000/admin/

- ✅ Test database connection- ✅ Test database connection

**Default Admin Account:**

- Username: `admin`- ✅ Apply pending migrations- ✅ Apply pending migrations

- Password: `admin123`

- ✅ Start development server- ✅ Start development server

---



## ✨ Key Features

### Manual Launch### Manual Launch

### 📂 Project Management

- Create and manage systematic review projects

- Custom data extraction field groups

- Project progress tracking and statistics```bash```bash



### 📚 Paper Librarycd sms_backendcd sms_backend

- **BibTeX Support**: Direct paste of BibTeX entries

- **Smart Parsing**: Auto-extract title, authors, year, journal, DOIpython manage.py runserverpython manage.py runserver

- **PDF Management**: Upload and view PDF files online

- **Advanced Search**: Search by citation key, title, author, DOI``````

- **Bulk Import**: Import from Zotero/Mendeley/EndNote (.bib files)

- **Zotero-Style Interface**: Professional literature management experience



### 🔍 Data Extraction### Access the Application### Access the Application

- Structured data extraction

- Customizable extraction templates

- Batch paper processing

- Export extraction resultsAfter starting, open your browser and visit:After starting, open your browser and visit:



### 🤖 AI Assistant

- **Research Assistant**: Answer academic questions

- **Extraction Assistant**: Automated feature extraction- **Home**: http://127.0.0.1:8000/- **Home**: http://127.0.0.1:8000/

- **Workflow Assistant**: Process optimization suggestions

- **Context-Aware**: Understands project background- **Paper Library**: http://127.0.0.1:8000/papers/- **Paper Library**: http://127.0.0.1:8000/papers/



### 📊 Analytics- **AI Assistant**: http://127.0.0.1:8000/agents/chat/- **AI Assistant**: http://127.0.0.1:8000/agents/chat/

- Project progress visualization

- Extraction status statistics- **Admin Panel**: http://127.0.0.1:8000/admin/- **Admin Panel**: http://127.0.0.1:8000/admin/

- Group-based data analysis

- Global statistical reports



---**Default Admin Account:****Default Admin Account:**



## 🛠️ System Requirements- Username: `admin`- Username: `admin`



- **Python**: 3.10 or higher- Password: `admin123`- Password: `admin123`

- **Database**: PostgreSQL 16

- **OS**: macOS, Linux, Windows

- **Browser**: Chrome, Firefox, Safari, Edge (latest versions)

------

---



## 📦 Installation

## ✨ Key Features## ✨ Key Features

### 1. Clone the repository



```bash

git clone https://github.com/icarus-gao/SMS-Extractor.git### 📂 Project Management### � Project Management

cd sms_extractor

```- Create and manage systematic review projects- Create and manage systematic review projects



### 2. Install dependencies- Custom data extraction field groups- Custom data extraction field groups



```bash- Project progress tracking and statistics- Project progress tracking and statistics

pip install -r requirements.txt

```



### 3. Configure environment### 📚 Paper Library### 📚 Paper Library



```bash- **BibTeX Support**: Direct paste of BibTeX entries- **BibTeX Support**: Direct paste of BibTeX entries

cp .env.template .env

```- **Smart Parsing**: Auto-extract title, authors, year, journal, DOI- **Smart Parsing**: Auto-extract title, authors, year, journal, DOI



Edit `.env` and fill in your configuration:- **PDF Management**: Upload and view PDF files online- **PDF Management**: Upload and view PDF files online



```env- **Advanced Search**: Search by citation key, title, author, DOI- **Advanced Search**: Search by citation key, title, author, DOI

# Django Settings

SECRET_KEY=your-secret-key-here- **Bulk Import**: Import from Zotero/Mendeley/EndNote (.bib files)- **Bulk Import**: Import from Zotero/Mendeley/EndNote (.bib files)

DEBUG=True

- **Zotero-Style Interface**: Professional literature management experience- **Zotero-Style Interface**: Professional literature management experience

# PostgreSQL Database

DB_NAME=sms_extractor

DB_USER=your_db_user

DB_PASSWORD=your_db_password### 🔍 Data Extraction### 🔍 Data Extraction

DB_HOST=localhost

DB_PORT=5432- Structured data extraction- Structured data extraction



# OpenAI API Configuration- Customizable extraction templates- Customizable extraction templates

OPENAI_API_KEY=sk-your-openai-api-key-here

OPENAI_MODEL=gpt-4o- Batch paper processing- Batch paper processing

```

- Export extraction results- Export extraction results

> **Generate Django Secret Key:**

> ```bash

> python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

> ```### 🤖 AI Assistant### 🤖 AI Assistant



### 4. Setup database- **Research Assistant**: Answer academic questions- **Research Assistant**: Answer academic questions



```bash- **Extraction Assistant**: Automated feature extraction- **Extraction Assistant**: Automated feature extraction

cd sms_backend

python manage.py migrate- **Workflow Assistant**: Process optimization suggestions- **Workflow Assistant**: Process optimization suggestions

```

- **Context-Aware**: Understands project background- **Context-Aware**: Understands project background

### 5. Create admin user (optional)



```bash

python manage.py createsuperuser### 📊 Analytics### 📊 Analytics

```

- Project progress visualization- Project progress visualization

### 6. Start server

- Extraction status statistics- Extraction status statistics

```bash

cd ..- Group-based data analysis- Group-based data analysis

./start.sh

```- Global statistical reports- Global statistical reports



---



## 📖 Usage Guide------



### 1. Create a Project



1. Click **"Create Project"** on the home page## 🛠️ System Requirements## 🛠️ System Requirements

2. Fill in project information:

   - Project ID (unique identifier)

   - Project name

   - Research keywords- **Python**: 3.10 or higher- **Python**: 3.10 or higher

   - Project description

3. Submit- **Database**: PostgreSQL 16- **Database**: PostgreSQL 16



### 2. Add Papers- **OS**: macOS, Linux, Windows- **OS**: macOS, Linux, Windows



#### Method A: Single Paper- **Browser**: Chrome, Firefox, Safari, Edge (latest versions)- **Browser**: Chrome, Firefox, Safari, Edge (latest versions)



1. Navigate to **Paper Library**

2. Click **"Add Paper"**

3. Enter Paper ID (e.g., `smith2023machine`)------

4. Paste BibTeX from Google Scholar

5. (Optional) Upload PDF file

6. Submit

## 📦 Installation## 📦 Installation

#### Method B: Bulk Import



1. Export BibTeX file from Zotero/Mendeley

2. Paper Library → **"Import BibTeX"**1. **Clone the repository**

3. Upload .bib file

4. Select project (optional)   ```bash

5. Complete import

   git clone <repository-url>### PrerequisitesOpen http://localhost:8501 :

### 3. Data Extraction

   cd sms_extractor

1. Open project details page

2. Create data extraction field groups   ```1) Paste the citation header

3. Select papers to extract

4. Execute data extraction

5. View and export results

2. **Install dependencies**- Python 3.10+2) Upload the PDF

### 4. Use AI Assistant

   ```bash

1. Click **"AI Assistant"**

2. Select assistant type:   pip install -r requirements.txt- PostgreSQL 163) Set `paper_id` → click **Run extraction**

   - Research Assistant (general Q&A)

   - Extraction Assistant (data extraction)   ```

   - Workflow Assistant (process optimization)

3. Enter your question or requirement- OpenAI API Key

4. Get intelligent answers and suggestions

3. **Configure environment**

---

   ```bashOutputs:

## 🗂️ Project Structure

   cp .env.example .env

```

sms_extractor/   # Edit .env with your configurations### Installation- `data/master.csv` — values aligned with your Master schema

├── start.sh                  # Startup script

├── SMS_Extractor.command     # macOS double-click launcher   ```

├── requirements.txt          # Python dependencies

├── .env                      # Environment configuration (not in git)- `data/evidence_log.csv` — per-field `value | quote | location`

├── .env.template             # Configuration template

├── README.md                 # This file4. **Setup database**

└── sms_backend/              # Django project

    ├── manage.py             # Django management script   ```bash1. Clone the repository- `data/raw/*.json` — raw LLM outputs (audit/cache)

    ├── dashboard/            # Dashboard app

    ├── projects/             # Project management   cd sms_backend

    ├── papers/               # Paper management

    ├── extractions/          # Data extraction   python manage.py migrate```bash

    ├── agents/               # AI assistant

    └── sms_backend/          # Project settings   ```

```

git clone <repository-url>## Configuration precedence

---

5. **Create admin user** (if needed)

## 🔧 Configuration

   ```bashcd sms_extractor`secrets.toml > .env`. The app does **not** expose an API-key input field.

### Environment Variables

   python manage.py createsuperuser

Create a `.env` file with the following variables:

   ``````

| Variable | Description | Required | Default |

|----------|-------------|----------|---------|

| `SECRET_KEY` | Django secret key for security | ✅ Yes | - |

| `DEBUG` | Enable debug mode (False in production) | No | `True` |6. **Start server**## Field Profiles (cost control)

| `ALLOWED_HOSTS` | Comma-separated allowed hosts | No | `localhost,127.0.0.1` |

| `DB_NAME` | PostgreSQL database name | ✅ Yes | - |   ```bash

| `DB_USER` | PostgreSQL username | ✅ Yes | - |

| `DB_PASSWORD` | PostgreSQL password | ✅ Yes | - |   ./start.sh2. Create virtual environment- **Full Schema** — all fields

| `DB_HOST` | Database host | No | `localhost` |

| `DB_PORT` | Database port | No | `5432` |   ```

| `OPENAI_API_KEY` | OpenAI API key for AI features | ✅ Yes | - |

| `OPENAI_MODEL` | OpenAI model name | No | `gpt-4o` |```bash- **Only Classification** — `desc.doc_type`, `survey.method_class`, `research.primary_type`, `research.validation_level`

| `OPENAI_BASE_URL` | Custom OpenAI endpoint | No | - |

| `MAX_UPLOAD_SIZE` | Max file upload size in MB | No | `50` |---



### Supported OpenAI Modelspython -m venv venv- **RQ1 Modules Only** — `algorithm_family` + `module.*`



- `gpt-4o` - Latest and most capable (recommended)## 📖 Usage Guide

- `gpt-4o-mini` - Faster and more affordable

- `gpt-4-turbo` - Previous flagship modelsource venv/bin/activate  # On Windows: venv\Scripts\activate

- `gpt-4` - Stable GPT-4 model

- `gpt-3.5-turbo` - Fast and cost-effective### 1. Create a Project



---```## Notes



## ❓ FAQ1. Click **"Create Project"** on the home page



### Q: How to get BibTeX entries?2. Fill in project information:- Use Python **3.11** to avoid SSL/CA quirks seen on some stacks.



**From Google Scholar:**   - Project ID (unique identifier)

1. Search for paper

2. Click quotation mark icon (")   - Project name3. Install dependencies- For scanned PDFs, add an OCR branch in `utils/extractor.py` if you need it.

3. Select "BibTeX"

4. Copy content   - Research keywords



**From Zotero:**   - Project description```bash- If you host an OpenAI-compatible endpoint, set `OPENAI_BASE_URL` in `.env`.

1. Select papers

2. Right-click → Export Items3. Submit

3. Format: "BibTeX"

4. Save and importpip install -r requirements.txt



### Q: Database connection failed?### 2. Add Papers```



1. Confirm PostgreSQL service is running:

   ```bash

   # macOS#### Method A: Single Paper4. Configure environment variables

   brew services start postgresql@16

   1. Navigate to **Paper Library**```bash

   # Linux

   sudo systemctl start postgresql2. Click **"Add Paper"**cp .env.example .env

   ```

3. Enter Paper ID (e.g., `smith2023machine`)# Edit .env and add your configuration:

2. Check database configuration in `.env`

4. Paste BibTeX from Google Scholar# - DATABASE_URL

3. Ensure database exists:

   ```bash5. (Optional) Upload PDF file# - OPENAI_API_KEY

   createdb sms_extractor

   ```6. Submit# - SECRET_KEY



4. Run migrations:```

   ```bash

   cd sms_backend#### Method B: Bulk Import

   python manage.py migrate

   ```1. Export BibTeX file from Zotero/Mendeley5. Run database migrations



### Q: How to reset admin password?2. Paper Library → **"Import BibTeX"**```bash



```bash3. Upload .bib filecd sms_backend

cd sms_backend

python manage.py changepassword admin4. Select project (optional)python manage.py migrate

```

5. Complete import```

### Q: OpenAI API errors?



1. Verify your API key is valid

2. Check you have sufficient credits### 3. Data Extraction6. Create superuser

3. Ensure model name is correct (not `gpt-5`)

4. Check API rate limits```bash



---1. Open project details pagepython manage.py createsuperuser



## 🔄 Development2. Create data extraction field groups```



### Running Tests3. Select papers to extract



```bash4. Execute data extraction7. Start development server

cd sms_backend

python manage.py test5. View and export results```bash

```

python manage.py runserver

### Creating Migrations

### 4. Use AI Assistant```

After modifying models:



```bash

cd sms_backend1. Click **"AI Assistant"**8. Access the application

python manage.py makemigrations

python manage.py migrate2. Select assistant type:- Main application: http://127.0.0.1:8000/

```

   - Research Assistant (general Q&A)- AI Assistant: http://127.0.0.1:8000/agents/chat/

### Resetting Database

   - Extraction Assistant (data extraction)- Admin panel: http://127.0.0.1:8000/admin/

```bash

cd sms_backend   - Workflow Assistant (process optimization)

python manage.py flush

python manage.py migrate3. Enter your question or requirement## Project Structure

```

4. Get intelligent answers and suggestions

### Code Style

```

This project follows:

- PEP 8 for Python code---sms_extractor/

- Django coding style guide

- Black for code formatting├── sms_backend/              # Django project root



---## 🗂️ Project Structure│   ├── manage.py             # Django management script



## 🚨 Security Notes│   ├── sms_backend/          # Main project settings



⚠️ **Important Security Warnings:**```│   ├── dashboard/            # Main dashboard app



1. **Never commit `.env` file** - Contains sensitive credentialssms_extractor/│   ├── projects/             # Project management app

2. **Change default admin password** - After first login

3. **Generate new SECRET_KEY** - For production deployment├── start.sh                  # Startup script│   ├── papers/               # Paper management app

4. **Rotate exposed API keys** - If accidentally committed

5. **Set DEBUG=False** - In production environment├── SMS_Extractor.command     # macOS double-click launcher│   ├── extractions/          # Data extraction app



---├── requirements.txt          # Python dependencies│   ├── agents/               # AI agent app



## 📄 License├── .env                      # Environment configuration│   └── ai_agents/            # AI agent core logic



MIT License - See LICENSE file for details├── README.md                 # This file├── requirements.txt          # Python dependencies



---└── sms_backend/              # Django project├── .env                      # Environment variables (not in git)



## 📞 Support    ├── manage.py             # Django management script└── README.md                 # This file



- 📧 **Email**: support@sms-extractor.com    ├── dashboard/            # Dashboard app```

- 💬 **GitHub Issues**: [Submit Issue](https://github.com/icarus-gao/SMS-Extractor/issues)

- 📖 **Documentation**: Coming soon    ├── projects/             # Project management



---    ├── papers/               # Paper management## Usage



## 🤝 Contributing    ├── extractions/          # Data extraction



Contributions are welcome! Please feel free to submit a Pull Request.    ├── agents/               # AI assistant### Creating a Project



1. Fork the repository    └── sms_backend/          # Project settings

2. Create your feature branch (`git checkout -b feature/amazing-feature`)

3. Commit your changes (`git commit -m 'Add some amazing feature'`)```1. Navigate to the dashboard

4. Push to the branch (`git push origin feature/amazing-feature`)

5. Open a Pull Request2. Click "Create New Project"



------3. Enter project details (name, description, keywords)



<div align="center">4. Click "Create Project"



**Made with ❤️ by SMS Extractor Team**## 🔧 Configuration



If you find this helpful, please give us a ⭐️### Managing Papers



[GitHub](https://github.com/icarus-gao/SMS-Extractor) • [Report Bug](https://github.com/icarus-gao/SMS-Extractor/issues) • [Request Feature](https://github.com/icarus-gao/SMS-Extractor/issues)Create a `.env` file with the following variables:



</div>1. Open a project


```env2. Go to "Papers" tab

# Django Settings3. Upload PDF files or enter paper information

SECRET_KEY=your-secret-key-here4. Papers will be available for extraction

DEBUG=True

ALLOWED_HOSTS=localhost,127.0.0.1### Extracting Data



# Database Settings1. Select papers from your project

DB_NAME=sms_extractor2. Define extraction fields using groups

DB_USER=your_db_user3. Perform manual or AI-assisted extraction

DB_PASSWORD=your_db_password4. View and export results

DB_HOST=localhost

DB_PORT=5432### Using AI Agents



# OpenAI API (for AI Assistant)1. Click "AI Assistant" in the navigation

OPENAI_API_KEY=sk-your-api-key-here2. Select agent type:

```   - **Research Assistant**: Ask questions about systematic reviews

   - **Extraction Assistant**: Get help with data extraction

---   - **Workflow Assistant**: Optimize your research process

3. Chat naturally with the agent

## ❓ FAQ4. Agents have context awareness of your projects



### Q: How to get BibTeX entries?## Development



**Google Scholar:**### Database

1. Search for paper

2. Click quotation mark icon (")This project uses PostgreSQL. To reset the database:

3. Select "BibTeX"

4. Copy content```bash

cd sms_backend

**From Zotero:**python manage.py flush

1. Select paperspython manage.py migrate

2. Right-click → Export Items```

3. Format: "BibTeX"

4. Save and import### Running Tests



### Q: Database connection failed?```bash

cd sms_backend

1. Confirm PostgreSQL service is runningpython manage.py test

2. Check database configuration in `.env````

3. Ensure database exists:

   ```bash### Creating Migrations

   createdb sms_extractor

   ```After modifying models:

4. Run migrations:

   ```bash```bash

   python manage.py migratecd sms_backend

   ```python manage.py makemigrations

python manage.py migrate

### Q: How to reset admin password?```



```bash## License

cd sms_backend

python manage.py changepassword admin[License information to be added]

```

## Support

---

For issues and questions, please open an issue on GitHub.

## 🔄 Development

### Running Tests

```bash
cd sms_backend
python manage.py test
```

### Creating Migrations

After modifying models:

```bash
cd sms_backend
python manage.py makemigrations
python manage.py migrate
```

### Resetting Database

```bash
cd sms_backend
python manage.py flush
python manage.py migrate
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

<div align="center">

**Made with ❤️ by SMS Extractor Team**

If you find this helpful, please give us a ⭐️

</div>
