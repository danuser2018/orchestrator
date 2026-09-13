import time
import jwt
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from core.command_catalog import CommandCatalogProjection
from core.config import settings
from core.engine import ExecutionPlanner, PlanExecutor
from core.events import HostCommandsAvailableEvent, PublicCommandEntry, ResponseGeneratedEvent
from core.host_service_client import HostServiceClient, ExecuteCommandResponse
from core.models import UserRequest, ExecutionPlan, ExecutionPlanStep, PluginContext, AssistantResponse
from core.parameter_resolution import ParameterResolverRegistry, ParameterResolverEngine
from core.parameter_resolution.resolvers.command import CommandResolver
from core.plugin_manager import PluginManager
from core.similarity import RapidFuzzSimilarityEngine


def create_token(execution_id: str, action_id: str, secret: str = None) -> str:
    now = int(time.time())
    sec = secret or settings.security_hmac_secret
    payload = {
        "execution_id": execution_id,
        "action_id": action_id,
        "audience": "nova-orchestrator",
        "issued_at": now,
        "expires_at": now + 300,
        "nonce": "test-nonce-123",
    }
    return jwt.encode(payload, sec, algorithm="HS256")


@pytest.fixture
def test_setup():
    plugin_manager = PluginManager()
    plugin_manager.discover_and_load()
    similarity_engine = RapidFuzzSimilarityEngine()

    catalog = CommandCatalogProjection()
    command_resolver = CommandResolver(catalog)
    registry = ParameterResolverRegistry()
    registry.register(command_resolver)
    parameter_engine = ParameterResolverEngine(registry)

    planner = ExecutionPlanner(
        plugin_manager=plugin_manager,
        similarity_engine=similarity_engine,
        parameter_engine=parameter_engine,
    )

    mock_event_bus = AsyncMock()
    executor = PlanExecutor(plugin_manager=plugin_manager, event_bus=mock_event_bus)

    return {
        "plugin_manager": plugin_manager,
        "catalog": catalog,
        "planner": planner,
        "executor": executor,
        "mock_event_bus": mock_event_bus,
    }


@pytest.mark.asyncio
async def test_planner_resolves_open_app_with_dynamic_phrases(test_setup):
    catalog = test_setup["catalog"]
    plugin_manager = test_setup["plugin_manager"]
    planner = test_setup["planner"]

    # Populate catalog projection
    entries = [
        PublicCommandEntry(
            name="calculator",
            risk="low",
            phrases=["calculadora", "abre la calculadora"],
        )
    ]
    catalog.update_from_event(entries, CommandResolver.normalize_phrase)

    # Inject dynamic phrases into AppLauncherPlugin
    app_launcher = plugin_manager.get_plugin("open_app")
    assert app_launcher is not None
    app_launcher.load_dynamic_phrases(["calculadora", "abre la calculadora"])

    request = UserRequest(text="Abre la calculadora")
    plan = await planner.resolve(request)

    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "open_app"
    assert step.confidence > 80.0
    assert step.parameters == {"command": "calculator"}
    assert step.context.parameters == {"command": "calculator"}


@pytest.mark.asyncio
async def test_executor_executes_open_app_plan(test_setup):
    plugin_manager = test_setup["plugin_manager"]
    executor = test_setup["executor"]
    mock_event_bus = test_setup["mock_event_bus"]

    app_launcher = plugin_manager.get_plugin("open_app")
    mock_client = AsyncMock(spec=HostServiceClient)
    mock_client.execute_command.return_value = ExecuteCommandResponse(
        command="calculator",
        status="started",
        pid=9876,
    )
    app_launcher.client = mock_client

    corr_id = "corr-exec-open-app-1"
    token = create_token(execution_id=corr_id, action_id="open_app")

    step = ExecutionPlanStep(
        plugin="open_app",
        confidence=95.0,
        parameters={"command": "calculator"},
        context=PluginContext(
            raw_text="abre la calculadora",
            normalized_text="abre la calculadora",
            correlation_id=corr_id,
            parameters={"command": "calculator"},
        ),
        security={"authorization_token": token},
    )
    plan = ExecutionPlan(steps=[step], correlation_id=corr_id)

    response = await executor.execute_plan(plan)

    assert isinstance(response, AssistantResponse)
    assert response.success is True
    assert response.plugin_used == "AppLauncherPlugin"
    assert response.speech == "Aplicación abierta."
    mock_client.execute_command.assert_called_once_with("calculator")

    # Verify ResponseGeneratedEvent was published to event bus
    assert mock_event_bus.publish.called
    events = [call.args[0] for call in mock_event_bus.publish.call_args_list]
    response_events = [e for e in events if isinstance(e, ResponseGeneratedEvent)]
    assert len(response_events) == 1
    assert response_events[0].response == "Aplicación abierta."
    assert response_events[0].plugin == "AppLauncherPlugin"


@pytest.mark.asyncio
async def test_hot_reloading_and_dynamic_convergence(test_setup):
    catalog = test_setup["catalog"]
    plugin_manager = test_setup["plugin_manager"]
    planner = test_setup["planner"]
    app_launcher = plugin_manager.get_plugin("open_app")

    # Initial state: only calculator
    initial_entries = [
        PublicCommandEntry(
            name="calculator",
            risk="low",
            phrases=["calculadora"],
        )
    ]
    catalog.update_from_event(initial_entries, CommandResolver.normalize_phrase)
    app_launcher.load_dynamic_phrases(["calculadora"])

    # Simulate arrival of NATS event with new command 'editor'
    event = HostCommandsAvailableEvent(
        version=2,
        commands=[
            PublicCommandEntry(
                name="calculator",
                risk="low",
                phrases=["calculadora"],
            ),
            PublicCommandEntry(
                name="editor",
                risk="medium",
                phrases=["abrir editor de texto", "editor"],
            ),
        ],
    )

    # Ingestion handler simulation as in main.py
    catalog.update_from_event(event.commands, CommandResolver.normalize_phrase)
    all_phrases = []
    for cmd in event.commands:
        all_phrases.extend(cmd.phrases)
    app_launcher.load_dynamic_phrases(all_phrases)

    # Request for newly registered application
    request = UserRequest(text="Abrir editor de texto")
    plan = await planner.resolve(request)

    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "open_app"
    assert step.confidence > 80.0
    assert step.parameters == {"command": "editor"}
