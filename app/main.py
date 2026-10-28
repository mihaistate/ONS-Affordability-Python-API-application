"""FastAPI entry point; workbook resources load once at application startup."""
import logging
import time
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .config import Settings
from .service import DomainError, Service

logger = logging.getLogger('acre')


def create_app(settings: Settings | None = None, service=None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        if service is not None:
            app.state.service = service
            yield
        else:
            with httpx.Client() as client:
                app.state.service = Service(settings or Settings.from_env(), client)
                yield

    app = FastAPI(title='Acre ONS Affordability API', lifespan=lifespan)

    @app.middleware('http')
    async def log_requests(request: Request, call_next):
        started = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception('request failed')
            response = JSONResponse(status_code=500, content={'error': {'code': 'internal_error', 'message': 'request could not be completed'}})
        logger.info('%s %s %s %.3fs', request.method, request.url.path, response.status_code, time.monotonic() - started)
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(status_code=exc.status, content={'error': {'code': exc.code, 'message': exc.message}})

    @app.get('/')
    def root():
        return {'service': 'Acre ONS Affordability API', 'endpoints': ['GET /healthz', 'GET /v1/cases/{caseId}/recommended-outgoings']}

    @app.get('/healthz')
    def health():
        return {'status': 'ok'}

    @app.get('/v1/cases/{case_id}/recommended-outgoings')
    def recommend(case_id: str, request: Request):
        if not case_id.strip():
            raise DomainError(400, 'invalid_case_id', 'case id is required')
        return request.app.state.service.recommend(case_id.strip())

    return app


app = create_app()


def run():
    import uvicorn
    address = Settings.from_env().http_addr
    host, separator, port = address.rpartition(':')
    if not separator:
        raise ValueError('HTTP_ADDR must be host:port or :port')
    uvicorn.run('app.main:app', host=host.strip('[]') or '0.0.0.0', port=int(port), timeout_keep_alive=60, timeout_graceful_shutdown=10)


if __name__ == '__main__':
    run()
