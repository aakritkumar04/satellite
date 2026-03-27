from datetime import datetime



TARGET_DATE = datetime(2025, 10, 22)


class Util:
    def __init__(self):
        pass

    def _normalize_target_date(self,value: str | datetime | None) -> datetime:
        if value is None:
            return TARGET_DATE
        if isinstance(value, datetime):
            return value

        normalized = value.strip()
        formats = ("%Y-%m-%d", "%m-%Y-%d", "%d-%m-%Y")
        for date_format in formats:
            try:
                return datetime.strptime(normalized, date_format)
            except ValueError:
                continue

        raise ValueError("Invalid date format. Use yyyy-mm-dd, mm-yyyy-dd, or dd-mm-yyyy.")
    
    def _is_supported_cdm_entry(self, filename: str) -> bool:
        if not filename.endswith(".json"):
            return False
        if filename.startswith("__MACOSX/"):
            return False
        if "/._" in filename or filename.split("/")[-1].startswith("._"):
            return False
        return True