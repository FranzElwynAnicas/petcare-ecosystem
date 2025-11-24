#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vms_project.settings')
    
    from django.core.management import execute_from_command_line
    
    # Check if runserver command is used and no port is specified
    if len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
        # Check if no port is already specified
        if len(sys.argv) == 2:
            sys.argv.append('127.0.0.1:6001')
        elif not any(':' in arg for arg in sys.argv[2:]):
            # If runserver is used but no port specified, add port 6001
            sys.argv.append('6001')
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()