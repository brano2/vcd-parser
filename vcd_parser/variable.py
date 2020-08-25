from typing import Optional

class VcdVariable:
    def __init__(self, scope_type: Optional[str], scope: Optional[str],
                 type: str, size: int, id: str, name: str):
        self._scope_type = scope_type
        self._scope = scope

    def _add_change(self, new_val, timestamp):
        pass
