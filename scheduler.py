from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from models import db, Job, JobExecution, Notebook
from spark_executor import SparkExecutor

class JobScheduler:
    """Scheduler for managing and executing jobs"""
    
    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.spark_executor = SparkExecutor(config)
        
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        # Load active jobs from database
        with self.app.app_context():
            self._load_active_jobs()
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        self.spark_executor.close()
    
    def _load_active_jobs(self):
        """Load all active jobs from database"""
        active_jobs = Job.query.filter_by(status='active').all()
        for job in active_jobs:
            self.add_job(job)
    
    def add_job(self, job):
        """Add a job to the scheduler"""
        if not job.schedule:
            return
        
        try:
            # Parse cron expression
            trigger = CronTrigger.from_crontab(job.schedule)
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                args=[job.id],
                id=f'job_{job.id}',
                replace_existing=True
            )
            
            # Update next run time
            job.next_run = self.scheduler.get_job(f'job_{job.id}').next_run_time
            db.session.commit()
        
        except Exception as e:
            print(f"Error adding job {job.id}: {e}")
    
    def remove_job(self, job_id):
        """Remove a job from the scheduler"""
        try:
            self.scheduler.remove_job(f'job_{job_id}')
        except Exception as e:
            print(f"Error removing job {job_id}: {e}")
    
    def _execute_job(self, job_id):
        """Execute a job"""
        with self.app.app_context():
            job = Job.query.get(job_id)
            if not job or not job.notebook:
                return
            
            # Create execution record
            execution = JobExecution(
                job_id=job_id,
                status='running',
                started_at=datetime.utcnow()
            )
            db.session.add(execution)
            job.last_run = datetime.utcnow()
            db.session.commit()
            
            try:
                # Execute notebook code
                result = self.spark_executor.execute_code(
                    job.notebook.content,
                    job.notebook.language
                )
                
                # Update execution record
                execution.status = 'success' if result['success'] else 'failed'
                execution.output = result.get('output', '')
                execution.error = result.get('error', '')
                execution.completed_at = datetime.utcnow()
                
            except Exception as e:
                execution.status = 'failed'
                execution.error = str(e)
                execution.completed_at = datetime.utcnow()
            
            db.session.commit()
