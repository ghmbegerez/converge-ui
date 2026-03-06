import uvicorn

from converge_ui.app import app
from converge_ui.config.settings import load_settings
from converge_ui.logging import app_started


def main() -> int:
    s = load_settings()
    app_started(s.host, s.port)
    uvicorn.run(app, host=s.host, port=s.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
