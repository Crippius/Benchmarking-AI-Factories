"""Simple job tracking using JSON file storage."""

import json
from pathlib import Path
from datetime import datetime


class JobTracker:
    """Tracks job metadata in a simple JSON file."""
    
    def __init__(self, db_path=None):
        """Initialize the job tracker.
        
        Args:
            db_path: Path to the JSON file. If None, uses default location.
        """
        if db_path is None:
            base_path = Path(__file__).parent.parent.parent
            self.db_path = base_path / ".aif_jobs.json"
        else:
            self.db_path = Path(db_path)
        
        # Create empty DB if it doesn't exist
        if not self.db_path.exists():
            self._save_db({})
    
    def _load_db(self):
        """Load the job database from file."""
        try:
            with open(self.db_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_db(self, data):
        """Save the job database to file."""
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def add_job(self, job_id, job_type, service_name, node=None, config=None, parent_job=None):
        """
        Add a job to the tracker.
        
        Args:
            job_id: Slurm job ID
            job_type: Type of job ('service', 'benchmark', 'monitor')
            service_name: Name of the service/benchmark/monitor
            node: Node where job is running (optional)
            config: Configuration used for the job (optional)
            parent_job: Parent job ID if this job depends on another (optional)
        """
        db = self._load_db()
        
        db[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "service_name": service_name,
            "node": node,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "config": config or {},
            "parent_job": parent_job
        }
        
        self._save_db(db)
    
    def update_job(self, job_id, **kwargs):
        """
        Update job metadata.
        
        Args:
            job_id: Job ID to update
            **kwargs: Fields to update (node, status, etc.)
        """
        db = self._load_db()
        
        if job_id in db:
            db[job_id].update(kwargs)
            self._save_db(db)
        else:
            print(f"Warning: Job {job_id} not found in tracker")
    
    def get_job(self, job_id):
        """
        Get job metadata.
        
        Args:
            job_id: Job ID to retrieve
        
        Returns:
            dict: Job metadata, or None if not found
        """
        db = self._load_db()
        return db.get(job_id)
    
    def get_jobs_by_type(self, job_type):
        """
        Get all jobs of a specific type.
        
        Args:
            job_type: Type of jobs to retrieve ('service', 'benchmark', 'monitor')
        
        Returns:
            list: List of job metadata dictionaries
        """
        db = self._load_db()
        return [job for job in db.values() if job["job_type"] == job_type]
    
    def get_jobs_by_service(self, service_name):
        """
        Get all jobs for a specific service.
        
        Args:
            service_name: Name of the service
        
        Returns:
            list: List of job metadata dictionaries
        """
        db = self._load_db()
        return [job for job in db.values() if job["service_name"] == service_name]
    
    def get_all_jobs(self):
        """
        Get all tracked jobs.
        
        Returns:
            dict: All job metadata
        """
        return self._load_db()
    
    def remove_job(self, job_id):
        """
        Remove a job from the tracker.
        
        Args:
            job_id: Job ID to remove
        """
        db = self._load_db()
        if job_id in db:
            del db[job_id]
            self._save_db(db)
    
    def clear_all(self):
        """Clear all job records."""
        self._save_db({})
