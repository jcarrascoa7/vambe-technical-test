import pandas as pd

from backend.etl.cleaner import clean, read_csv


class TestReadCSV:
    def test_reads_csv_with_correct_columns(self, tmp_path):
        csv_content = (
            "Nombre,Correo Electronico,Numero de Telefono,Fecha de la Reunion,"
            "Vendedor asignado,closed,Transcripcion\n"
            "Test User,test@example.com,56912345678,2024-03-15,Toro,1,Some text\n"
        )
        path = tmp_path / "test.csv"
        path.write_text(csv_content)

        df = read_csv(str(path))
        assert len(df) == 1
        assert "Nombre" in df.columns
        assert df.iloc[0]["Nombre"] == "Test User"


class TestClean:
    def _make_df(self, rows=None):
        if rows is None:
            rows = [
                {
                    "Nombre": "Test User",
                    "Correo Electronico": "test@example.com",
                    "Numero de Telefono": "56912345678",
                    "Fecha de la Reunion": "2024-03-15",
                    "Vendedor asignado": "Toro",
                    "closed": 1,
                    "Transcripcion": "Some text",
                }
            ]
        return pd.DataFrame(rows)

    def test_renames_columns(self):
        df = self._make_df()
        result = clean(df)
        assert "name" in result.columns
        assert "email" in result.columns
        assert "meeting_date" in result.columns

    def test_parses_dates_to_datetime(self):
        df = self._make_df()
        result = clean(df)
        assert pd.api.types.is_datetime64_any_dtype(result["meeting_date"])

    def test_handles_invalid_dates(self):
        rows = [
            {
                "Nombre": "Test User",
                "Correo Electronico": "test@example.com",
                "Numero de Telefono": "123",
                "Fecha de la Reunion": "not-a-date",
                "Vendedor asignado": "Toro",
                "closed": 0,
                "Transcripcion": "text",
            }
        ]
        df = pd.DataFrame(rows)
        result = clean(df)
        assert pd.isna(result.iloc[0]["meeting_date"])

    def test_handles_null_name_by_dropping_row(self):
        rows = [
            {
                "Nombre": None,
                "Correo Electronico": "a@test.com",
                "Numero de Telefono": "123",
                "Fecha de la Reunion": "2024-01-01",
                "Vendedor asignado": "Toro",
                "closed": 0,
                "Transcripcion": "text",
            },
            {
                "Nombre": "Valid User",
                "Correo Electronico": "b@test.com",
                "Numero de Telefono": "456",
                "Fecha de la Reunion": "2024-01-01",
                "Vendedor asignado": "Puma",
                "closed": 0,
                "Transcripcion": "text",
            },
        ]
        df = pd.DataFrame(rows)
        result = clean(df)
        assert len(result) == 1
        assert result.iloc[0]["name"] == "Valid User"

    def test_removes_duplicate_emails(self):
        rows = [
            {
                "Nombre": "User A",
                "Correo Electronico": "same@test.com",
                "Numero de Telefono": "123",
                "Fecha de la Reunion": "2024-01-01",
                "Vendedor asignado": "Toro",
                "closed": 0,
                "Transcripcion": "text A",
            },
            {
                "Nombre": "User B",
                "Correo Electronico": "same@test.com",
                "Numero de Telefono": "456",
                "Fecha de la Reunion": "2024-02-01",
                "Vendedor asignado": "Puma",
                "closed": 1,
                "Transcripcion": "text B",
            },
        ]
        df = pd.DataFrame(rows)
        result = clean(df)
        assert len(result) == 1
        assert result.iloc[0]["name"] == "User A"  # keeps first

    def test_closed_is_bool(self):
        df = self._make_df()
        result = clean(df)
        assert result.iloc[0]["closed"] == True  # noqa: E712
