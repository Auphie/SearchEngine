## Dependencies
Python 3.5+
pip
lxml
beautifulsoup

## Getting Started
```bash
virtualenv envs --python=python3.6
source envs/bin/activate
pip install -r requirements.txt

# Start RethinkDB
rethink

# Start celery worker, c is the concurrency level
celery -A tasks worker -c 4 --loglevel=info

# In another terminal
source venv/bin/activate

# Launch job manually
python dog_go.py
