#!/usr/bin/env python3
"""
Lightweight DB + Redis verification script for development.
Usage: set environment variables DATABASE_URL and REDIS_URL if needed.
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ensure backend package is importable when run from repo root
repo_backend = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if repo_backend not in sys.path:
    sys.path.insert(0, repo_backend)

try:
    from app.models import models
except Exception as e:
    print('Failed to import models:', e)
    raise

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://stock_user:stock_pass_2026@localhost:5432/stock_analysis_db')
REDIS_URL = os.getenv('REDIS_URL', 'redis://:redis_pass_2026@localhost:6379/0')

print('Using DATABASE_URL=', DATABASE_URL)
print('Using REDIS_URL=', REDIS_URL)

# SQLAlchemy engine + session
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Simple query using ORM
    count = session.query(models.StockInfo).count()
    print(f'stock_info count: {count}')
    rows = session.query(models.StockInfo).limit(5).all()
    for r in rows:
        print(' -', r.stock_code, r.stock_name)

    # Redis check
    try:
        import redis
    except Exception as e:
        print('redis package not available:', e)
        raise

    r = redis.from_url(REDIS_URL)
    pong = r.ping()
    print('redis ping:', pong)
    r.set('verify_script_test', 'ok')
    val = r.get('verify_script_test')
    print('redis get verify_script_test:', val.decode() if val else None)

    print('Verification completed successfully')
finally:
    session.close()
