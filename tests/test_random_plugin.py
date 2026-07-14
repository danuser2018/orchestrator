import pytest
from unittest.mock import patch, MagicMock
from core.random_service import RandomService
from plugins.random.main import CoinPlugin, DicePlugin, RandomNumberPlugin
from core.models import PluginContext

# 1. Tests for RandomService
def test_random_service_flip_coin():
    service = RandomService()
    with patch("random.choice") as mock_choice:
        mock_choice.return_value = "Cara"
        assert service.flip_coin() == "Cara"
        mock_choice.assert_called_once_with(["Cara", "Cruz"])

def test_random_service_roll_dice():
    service = RandomService()
    with patch("random.randint") as mock_randint:
        mock_randint.return_value = 4
        assert service.roll_dice() == 4
        mock_randint.assert_called_once_with(1, 6)

def test_random_service_random_int():
    service = RandomService()
    with patch("random.randint") as mock_randint:
        mock_randint.return_value = 42
        assert service.random_int(1, 99) == 42
        mock_randint.assert_called_once_with(1, 99)

def test_random_service_flip_coin_exception():
    service = RandomService()
    with patch("random.choice") as mock_choice:
        mock_choice.side_effect = Exception("OS random source error")
        with pytest.raises(Exception) as excinfo:
            service.flip_coin()
        assert "OS random source error" in str(excinfo.value)

def test_random_service_roll_dice_exception():
    service = RandomService()
    with patch("random.randint") as mock_randint:
        mock_randint.side_effect = Exception("OS random source error")
        with pytest.raises(Exception) as excinfo:
            service.roll_dice()
        assert "OS random source error" in str(excinfo.value)

def test_random_service_random_int_exception():
    service = RandomService()
    with patch("random.randint") as mock_randint:
        mock_randint.side_effect = Exception("OS random source error")
        with pytest.raises(Exception) as excinfo:
            service.random_int(1, 99)
        assert "OS random source error" in str(excinfo.value)


# 2. Tests for CoinPlugin
@pytest.mark.asyncio
async def test_coin_plugin_success_cara():
    plugin = CoinPlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "flip_coin") as mock_flip:
        mock_flip.return_value = "Cara"
        context = PluginContext(raw_text="Lanza una moneda al aire", normalized_text="lanza una moneda al aire")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Cara."
        assert result.data == {"result": "Cara"}

@pytest.mark.asyncio
async def test_coin_plugin_success_cruz():
    plugin = CoinPlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "flip_coin") as mock_flip:
        mock_flip.return_value = "Cruz"
        context = PluginContext(raw_text="Cara o cruz", normalized_text="cara o cruz")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Cruz."
        assert result.data == {"result": "Cruz"}

@pytest.mark.asyncio
async def test_coin_plugin_error():
    plugin = CoinPlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "flip_coin") as mock_flip:
        mock_flip.side_effect = Exception("Random service failure")
        context = PluginContext(raw_text="Cara o cruz", normalized_text="cara o cruz")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido completar la operación."
        assert result.data is None


# 3. Tests for DicePlugin
@pytest.mark.asyncio
async def test_dice_plugin_success():
    plugin = DicePlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "roll_dice") as mock_roll:
        mock_roll.return_value = 5
        context = PluginContext(raw_text="Tira un dado", normalized_text="tira un dado")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Ha salido un 5."
        assert result.data == {"result": 5}

@pytest.mark.asyncio
async def test_dice_plugin_error():
    plugin = DicePlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "roll_dice") as mock_roll:
        mock_roll.side_effect = Exception("Random service failure")
        context = PluginContext(raw_text="Dado.", normalized_text="dado")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido completar la operación."
        assert result.data is None


# 4. Tests for RandomNumberPlugin
@pytest.mark.asyncio
async def test_random_number_plugin_success():
    plugin = RandomNumberPlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "random_int") as mock_rand:
        mock_rand.return_value = 37
        context = PluginContext(raw_text="Dame un número aleatorio", normalized_text="dame un numero aleatorio")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "37."
        assert result.data == {"result": 37}

@pytest.mark.asyncio
async def test_random_number_plugin_error():
    plugin = RandomNumberPlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "random_int") as mock_rand:
        mock_rand.side_effect = Exception("Random service failure")
        context = PluginContext(raw_text="Número al azar.", normalized_text="numero al azar")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido completar la operación."
        assert result.data is None


# 5. Metadata verification tests
def test_random_plugins_metadata():
    coin = CoinPlugin()
    dice = DicePlugin()
    rand_num = RandomNumberPlugin()
    
    assert coin.id == "coin"
    assert coin.name == "CoinPlugin"
    assert coin.priority == 60
    assert len(coin.examples) > 0
    assert all(isinstance(e, str) for e in coin.examples)
    
    assert dice.id == "dice"
    assert dice.name == "DicePlugin"
    assert dice.priority == 60
    assert len(dice.examples) > 0
    assert all(isinstance(e, str) for e in dice.examples)
    
    assert rand_num.id == "random-number"
    assert rand_num.name == "RandomNumberPlugin"
    assert rand_num.priority == 60
    assert len(rand_num.examples) > 0
    assert all(isinstance(e, str) for e in rand_num.examples)
    
    # Check that they don't share example phrases to avoid routing ambiguity
    assert set(coin.examples).isdisjoint(set(dice.examples))
    assert set(coin.examples).isdisjoint(set(rand_num.examples))
    assert set(dice.examples).isdisjoint(set(rand_num.examples))
