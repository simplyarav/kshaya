import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'python_backend')))
from app.services.forensics.filesystem_parser import FilesystemParser

parser = FilesystemParser("C:\\Users\\Ravi\\OneDrive\\Desktop\\mock_image.001")
print("Unallocated:", parser.get_unallocated_blocks()[:5])
print("Slack:", parser.get_slack_space())
