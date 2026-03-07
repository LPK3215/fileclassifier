from __future__ import annotations

import uvicorn


def main() -> int:
    uvicorn.run(
        "fileclassifier.webapi.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
    return 0

