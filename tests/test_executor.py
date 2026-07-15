import pytest
from core.engine import PluginExecutor, PluginNotFoundError
from core.models import ExecutionPlan, ExecutionPlanStep, PluginContext, PluginResult, AssistantResponse
from core.plugin_manager import PluginManager
from plugins.base import Plugin

@pytest.fixture
def executor():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    return PluginExecutor(plugin_manager=manager)

class MockSuccessPlugin(Plugin):
    @property
    def name(self) -> str:
        return "MockSuccessPlugin"
    @property
    def description(self) -> str:
        return "Mock Success"
    @property
    def id(self) -> str:
        return "mock_success"
    async def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(success=True, speech="Success Speech")

class MockFailurePlugin(Plugin):
    @property
    def name(self) -> str:
        return "MockFailurePlugin"
    @property
    def description(self) -> str:
        return "Mock Failure"
    @property
    def id(self) -> str:
        return "mock_failure"
    async def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(success=False, speech="Failure Speech")

@pytest.mark.asyncio
async def test_execute_plan_success(executor):
    executor.plugin_manager.plugins["MockSuccessPlugin"] = MockSuccessPlugin()
    
    plan = ExecutionPlan(
        steps=[
            ExecutionPlanStep(
                plugin="MockSuccessPlugin",
                context=PluginContext(raw_text="test", normalized_text="test")
            )
        ]
    )
    
    res = await executor.execute_plan(plan)
    assert isinstance(res, AssistantResponse)
    assert res.success is True
    assert res.plugin_used == "MockSuccessPlugin"
    assert res.speech == "Success Speech"

@pytest.mark.asyncio
async def test_execute_plan_plugin_not_found(executor):
    plan = ExecutionPlan(
        steps=[
            ExecutionPlanStep(
                plugin="NonExistentPlugin",
                context=PluginContext(raw_text="test", normalized_text="test")
            )
        ]
    )
    
    with pytest.raises(PluginNotFoundError) as exc_info:
        await executor.execute_plan(plan)
    
    assert "El plugin 'NonExistentPlugin' no está registrado en el sistema." in str(exc_info.value)

@pytest.mark.asyncio
async def test_execute_plan_stop_on_failure(executor):
    executor.plugin_manager.plugins["MockSuccessPlugin"] = MockSuccessPlugin()
    executor.plugin_manager.plugins["MockFailurePlugin"] = MockFailurePlugin()
    
    plan = ExecutionPlan(
        steps=[
            ExecutionPlanStep(
                plugin="MockFailurePlugin",
                context=PluginContext(raw_text="test", normalized_text="test")
            ),
            ExecutionPlanStep(
                plugin="MockSuccessPlugin",
                context=PluginContext(raw_text="test", normalized_text="test")
            )
        ]
    )
    
    res = await executor.execute_plan(plan)
    assert res.success is False
    assert res.plugin_used == "MockFailurePlugin"
    assert res.speech == "Failure Speech"

class MockExceptionPlugin(Plugin):
    @property
    def name(self) -> str:
        return "MockExceptionPlugin"
    @property
    def description(self) -> str:
        return "Mock Exception"
    @property
    def id(self) -> str:
        return "mock_exception"
    async def execute(self, context: PluginContext) -> PluginResult:
        raise RuntimeError("Unexpected internal error in plugin")

@pytest.mark.asyncio
async def test_execute_plan_plugin_exception(executor):
    executor.plugin_manager.plugins["MockExceptionPlugin"] = MockExceptionPlugin()

    plan = ExecutionPlan(
        steps=[
            ExecutionPlanStep(
                plugin="MockExceptionPlugin",
                context=PluginContext(raw_text="test", normalized_text="test")
            )
        ]
    )

    res = await executor.execute_plan(plan)
    assert isinstance(res, AssistantResponse)
    assert res.success is False
    assert res.plugin_used == "MockExceptionPlugin"
    assert res.speech == "Ha ocurrido un error interno al ejecutar la acción."
