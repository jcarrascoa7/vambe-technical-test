import pandas as pd


def read_csv(path: str) -> pd.DataFrame:
    """Read CSV and return raw DataFrame."""
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DataFrame: parse dates, handle nulls, remove duplicates."""
    df = df.rename(
        columns={
            "Nombre": "name",
            "Correo Electronico": "email",
            "Numero de Telefono": "phone",
            "Fecha de la Reunion": "meeting_date",
            "Vendedor asignado": "vendor",
            "closed": "closed",
            "Transcripcion": "transcription",
        }
    )

    df["meeting_date"] = pd.to_datetime(df["meeting_date"], errors="coerce")
    df["closed"] = df["closed"].astype(bool)

    df = df.dropna(subset=["name"])
    df = df.drop_duplicates(subset=["email"], keep="first")
    df = df.reset_index(drop=True)

    return df
