import uvicorn
from fastapi import FastAPI, status, Depends
from contextlib import asynccontextmanager
from src.routes import project_role_routes
from src.auth.auth import verify_token
import src.routes.decision_routes as decision_routes
import src.routes.edge_routes as edge_routes
import src.routes.scenario_routes as scenario_routes
import src.routes.node_routes as node_routes
import src.routes.objective_routes as objective_routes
import src.routes.opportunity_routes as opportunity_routes
import src.routes.uncertainty_routes as uncertainty_routes
import src.routes.discrete_probability_routes as discrete_probability_routes
import src.routes.discrete_utility_routes as discrete_utility_routes
import src.routes.utility_routes as utility_routes
import src.routes.value_metric_routes as value_metric_routes
import src.routes.project_routes as project_routes
import src.routes.issue_routes as issue_routes
import src.routes.user_routes as user_routes
import src.routes.outcome_routes as outcome_routes
import src.routes.option_routes as option_routes
import src.routes.solver_routes as solver_routes
import src.routes.structure_routes as structure_routes
from src.config import config
from src.session_manager import sessionmanager
from src.middleware.py_instrument_middle_ware import PyInstrumentMiddleWare
from fastapi.middleware.cors import CORSMiddleware
from azure.monitor.opentelemetry import configure_azure_monitor  # type: ignore
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore

from src.middleware.exception_handling_middleware import ExceptionFilterMiddleware
from src.logger import DOT_API_LOGGER_NAME, get_dot_api_logger

logger = get_dot_api_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await sessionmanager.init_db()
    yield

    await sessionmanager.close()


app = FastAPI(
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": config.CLIENT_ID,
        "redirectUrl": config.REDIRECT_URL,
    },
    swagger_ui_parameters={"syntaxHighlight": False},
    lifespan=lifespan,
)

if config.LOGGER:
    try:
        configure_azure_monitor(
            logger_name=DOT_API_LOGGER_NAME, connection_string=config.APPINSIGHTS_CONNECTIONSTRING
        )
        FastAPIInstrumentor.instrument_app(app)
        logger.info("Successfully configured telemetry after starting application")
    except Exception as e:
        logger.info("Error occurred while configuring telemetry: %s", e)

# Adding CORS middleware to the FastAPI application
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGINS,  # List of allowed origins
    allow_credentials=True,  # Allow credentials (cookies, authorization headers, etc.)
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)
app.add_middleware(ExceptionFilterMiddleware)

if config.PROFILE:
    # this will generate a profile.html at repository root when running any endpoint
    app.add_middleware(PyInstrumentMiddleWare)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Welcome to the DOT api"}


app.include_router(user_routes.router, dependencies=[Depends(verify_token)])
app.include_router(project_routes.router, dependencies=[Depends(verify_token)])
app.include_router(project_role_routes.router, dependencies=[Depends(verify_token)])
app.include_router(scenario_routes.router, dependencies=[Depends(verify_token)])
app.include_router(solver_routes.router, dependencies=[Depends(verify_token)])
app.include_router(issue_routes.router, dependencies=[Depends(verify_token)])
app.include_router(objective_routes.router, dependencies=[Depends(verify_token)])
app.include_router(opportunity_routes.router, dependencies=[Depends(verify_token)])
app.include_router(node_routes.router, dependencies=[Depends(verify_token)])
app.include_router(uncertainty_routes.router, dependencies=[Depends(verify_token)])
app.include_router(discrete_utility_routes.router, dependencies=[Depends(verify_token)])
app.include_router(discrete_probability_routes.router, dependencies=[Depends(verify_token)])
app.include_router(utility_routes.router, dependencies=[Depends(verify_token)])
app.include_router(value_metric_routes.router, dependencies=[Depends(verify_token)])
app.include_router(decision_routes.router, dependencies=[Depends(verify_token)])
app.include_router(edge_routes.router, dependencies=[Depends(verify_token)])
app.include_router(outcome_routes.router, dependencies=[Depends(verify_token)])
app.include_router(option_routes.router, dependencies=[Depends(verify_token)])
app.include_router(structure_routes.router, dependencies=[Depends(verify_token)])

if __name__ == "__main__":
    uvicorn.run("src.main:app", port=8080)
