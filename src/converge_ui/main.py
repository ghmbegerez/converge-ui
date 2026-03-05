import uvicorn

from converge_ui.app import app
from converge_ui.config.settings import load_settings


def main() -> int:
    s = load_settings()
    uvicorn.run(app, host=s.host, port=s.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
