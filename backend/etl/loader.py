from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from backend.models import Client


def load(df: pd.DataFrame, db: Session) -> int:
    """Load cleaned DataFrame into clients table. Returns count of rows inserted."""
    records = []
    for _, row in df.iterrows():
        record = Client(
            name=row.get("name"),
            email=row.get("email"),
            phone=str(row.get("phone")) if pd.notna(row.get("phone")) else None,
            meeting_date=row.get("meeting_date"),
            vendor=row.get("vendor"),
            closed=bool(row.get("closed", False)),
            transcription=row.get("transcription"),
        )
        records.append(record)

    db.bulk_save_objects(records)
    db.commit()
    return len(records)
