"""Add pipeline_steps column to analysis_history table"""
from app.db.database import engine
from sqlalchemy import text

# Add the pipeline_steps column to the analysis_history table
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE analysis_history ADD COLUMN pipeline_steps JSON DEFAULT '[]'"))
        conn.commit()
        print('Column added successfully!')
    except Exception as e:
        print(f'Error: {e}')
