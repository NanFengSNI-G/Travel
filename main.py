import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.logging import init_log
from app.api.graph import router as graph_router
from app.middleware import errors as handler_error, cors


class Server:

    def __init__(self):
        init_log()
        self.app = FastAPI()

    def init_app(self):
        handler_error.init_handler_errors(self.app)
        cors.init_cors(self.app)
        self.app.include_router(graph_router, prefix="/api")

        html_path = Path(__file__).parent / "static" / "chat.html"

        @self.app.get("/", response_class=HTMLResponse)
        def index():
            return html_path.read_text(encoding="utf-8")

    def run(self):
        self.init_app()
        uvicorn.run(
            app=self.app,
            host=settings.HOST,
            port=settings.PORT
        )


if __name__ == '__main__':
    Server().run()
