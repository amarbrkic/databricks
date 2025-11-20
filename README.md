# OpenBricks - Open Source Databricks Alternative

A unified web application that provides Databricks-like functionality using open-source components. Create notebooks, execute code with Apache Spark, and schedule jobs—all from a single, intuitive web interface.

## Features

✨ **Key Features:**
- 🔐 **User Authentication** - Secure login and registration system
- 📓 **Interactive Notebooks** - Write and execute Python/Spark code in a notebook interface
- ⚡ **Apache Spark Integration** - Full Spark support for big data processing
- ⏰ **Job Scheduling** - Schedule notebooks to run automatically using cron expressions
- 📊 **Unified Dashboard** - Single web interface for all operations
- 💾 **Persistent Storage** - SQLite database for notebooks, jobs, and execution history
- 🎨 **Modern UI** - Clean, responsive web interface

## Architecture

- **Backend**: Python Flask web framework
- **Data Processing**: Apache Spark
- **Job Scheduling**: APScheduler with cron expressions
- **Database**: SQLAlchemy with SQLite
- **Authentication**: Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript (no framework dependencies)

## Prerequisites

- Python 3.8 or higher
- Java 8 or higher (required for Apache Spark)

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/amarbrkic/databricks.git
cd databricks
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables (optional):**
```bash
export SECRET_KEY="your-secret-key"
export SPARK_MASTER="local[*]"  # or your Spark cluster URL
```

## Quick Start

1. **Start the application:**
```bash
python app.py
```

2. **Access the web interface:**
Open your browser and navigate to: `http://localhost:5000`

3. **Login with demo account:**
- Username: `demo`
- Password: `demo`

Or create a new account by clicking "Register"

## Usage

### Creating Notebooks

1. Navigate to **Notebooks** from the main menu
2. Click **+ New Notebook**
3. Write your Python/Spark code in the editor
4. Click **▶️ Run** to execute the code
5. View output in the right panel
6. Click **💾 Save** to save your work (or use Ctrl+S)

**Example Notebook Code:**
```python
# Create a Spark DataFrame
data = [("Alice", 34), ("Bob", 45), ("Charlie", 29)]
df = spark.createDataFrame(data, ["name", "age"])

# Show the DataFrame
df.show()

# Perform some operations
df.filter(df.age > 30).show()

# Print results
print(f"Total records: {df.count()}")
```

### Scheduling Jobs

1. Navigate to **Jobs** from the main menu
2. Click **+ New Job**
3. Enter job details:
   - **Job Name**: Descriptive name for your job
   - **Notebook**: Select which notebook to run
   - **Schedule**: Cron expression (e.g., `0 0 * * *` for daily at midnight)
4. Click **Create Job**
5. Click **Start** to activate the job
6. View **History** to see past executions

**Common Cron Expressions:**
- `0 * * * *` - Every hour
- `0 0 * * *` - Daily at midnight
- `0 9 * * 1` - Every Monday at 9 AM
- `*/15 * * * *` - Every 15 minutes

### Dashboard

The dashboard provides:
- Quick access to recent notebooks
- Overview of scheduled jobs and their status
- Quick actions to create notebooks and schedule jobs

## Configuration

Edit `config.py` to customize:

```python
class Config:
    SECRET_KEY = 'your-secret-key'  # Change in production
    SQLALCHEMY_DATABASE_URI = 'sqlite:///databricks.db'  # Database location
    SPARK_MASTER = 'local[*]'  # Spark master URL
    SPARK_APP_NAME = 'OpenSourceDatabricks'
```

## Project Structure

```
databricks/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── spark_executor.py      # Spark code execution engine
├── scheduler.py           # Job scheduling system
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── notebooks.html
│   ├── notebook.html
│   └── jobs.html
└── static/                # Static files
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Notebooks
- `GET /notebooks` - List all notebooks
- `POST /notebooks/create` - Create new notebook
- `GET /notebooks/<id>` - View notebook
- `POST /notebooks/<id>/save` - Save notebook
- `POST /notebooks/<id>/execute` - Execute notebook code
- `POST /notebooks/<id>/delete` - Delete notebook

### Jobs
- `GET /jobs` - List all jobs
- `POST /jobs/create` - Create new job
- `POST /jobs/<id>/activate` - Activate job
- `POST /jobs/<id>/deactivate` - Deactivate job
- `POST /jobs/<id>/delete` - Delete job
- `GET /jobs/<id>/executions` - Get job execution history

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Security Considerations

- Change the `SECRET_KEY` in production
- Use environment variables for sensitive configuration
- Consider using PostgreSQL or MySQL instead of SQLite for production
- Implement HTTPS in production environments
- Add rate limiting for API endpoints
- Implement proper user permissions and role-based access control

## Troubleshooting

**Issue**: Spark fails to start
- **Solution**: Ensure Java 8 or higher is installed and JAVA_HOME is set

**Issue**: Port 5000 already in use
- **Solution**: Change the port in app.py: `app.run(port=8080)`

**Issue**: Database errors
- **Solution**: Delete `databricks.db` file and restart the application to recreate it

## Future Enhancements

- [ ] Support for multiple languages (SQL, Scala, R)
- [ ] Collaborative editing
- [ ] Data visualization library integration
- [ ] Git integration for notebook version control
- [ ] Cluster management interface
- [ ] Advanced job dependencies and workflows
- [ ] User access control and sharing
- [ ] Real-time execution monitoring
- [ ] Export notebooks to various formats

## License

This project is open source and available under the MIT License.

## Acknowledgments

Built with:
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Apache Spark](https://spark.apache.org/) - Data processing engine
- [APScheduler](https://apscheduler.readthedocs.io/) - Job scheduling
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Flask-Login](https://flask-login.readthedocs.io/) - User authentication

## Support

For issues, questions, or contributions, please open an issue on GitHub.