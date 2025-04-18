#!/bin/bash
flask init-db
gunicorn app:app --workers 4 --bind 0.0.0.0:$PORT