from sqlalchemy.orm import Session
from ...db.models import FileSchedule
from .erase_engine import EraseEngine

class SchedulerService:
    def __init__(self, db: Session):
        self.db = db

    def execute_due_jobs(self):
        # In a real system this would parse cron_expr and check times.
        schedules = self.db.query(FileSchedule).all()
        for sched in schedules:
            for path in sched.paths:
                # Default to quarantine unless explicitly skipped
                if not sched.skip_quarantine:
                    EraseEngine.quarantine_file(path)
                else:
                    EraseEngine.overwrite_and_delete(path)
