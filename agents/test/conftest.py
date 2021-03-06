
import enforce
import pytest

from agents import AgentWallet, BaseAgent
from web3tools import web3util, web3wallet
from web3tools.web3util import toBase18
from web3engine import bfactory, bpool, datatoken, dtfactory, globaltokens
from util.constants import POOL_WEIGHT_DT, POOL_WEIGHT_OCEAN

#alice:
# 1. starts with an init OCEAN
# 2. creates a DT, and mints an init amount
# 3. creates a DT-OCEAN pool, and adds init liquidity

_OCEAN_INIT = 1000.0
_OCEAN_STAKE = 200.0
_DT_INIT = 100.0
_DT_STAKE = 20.0

@pytest.fixture
def alice_private_key() -> str:
    return _alice_info().private_key

@pytest.fixture
def alice_agent() -> str:
    class MockAgent(BaseAgent.BaseAgent):
        def takeStep(self, state):
            pass
    agent = MockAgent("agent1",USD=0.0,OCEAN=0.0)
    agent._wallet = _alice_info().agent_wallet
    return agent

@pytest.fixture
def alice_agent_wallet() -> AgentWallet.AgentWallet:
    return _alice_info().agent_wallet

@pytest.fixture
def alice_web3wallet() -> web3wallet.Web3Wallet:
    return _alice_info().wallet

@pytest.fixture
def alice_DT() -> datatoken.Datatoken:
    return _alice_info().DT

@pytest.fixture
def alice_pool():
    return _alice_info().pool

@enforce.runtime_validation
def _alice_info():
    return _make_info(private_key_name='TEST_PRIVATE_KEY1')

@enforce.runtime_validation
def _make_info(private_key_name:str):
    
    class _Info:
        pass
    info = _Info()
    
    network = web3util.get_network()
    info.private_key = web3util.confFileValue(network, private_key_name)
    info.agent_wallet = AgentWallet.AgentWallet(
        OCEAN=_OCEAN_INIT,private_key=info.private_key)
    info.web3wallet = info.agent_wallet._web3wallet

    info.DT = _createDT(info.web3wallet)
    info.pool = _createPool(DT=info.DT, web3_w=info.web3wallet)
    return info

_CACHED_DT = None
@enforce.runtime_validation
def _createDT(web3_w:web3wallet.Web3Wallet):
    global _CACHED_DT
    if _CACHED_DT is None:
        DT_address = dtfactory.DTFactory().createToken(
            'foo', 'DT1', 'DT1', toBase18(_DT_INIT),from_wallet=web3_w)
        DT = datatoken.Datatoken(DT_address)
        DT.mint(web3_w.address, toBase18(_DT_INIT), from_wallet=web3_w)
        _CACHED_DT = DT
    return _CACHED_DT

@enforce.runtime_validation
def _createPool(DT:datatoken.Datatoken, web3_w:web3wallet.Web3Wallet):
    OCEAN = globaltokens.OCEANtoken()
    
    #Create OCEAN-DT pool
    p_address = bfactory.BFactory().newBPool(from_wallet=web3_w)
    pool = bpool.BPool(p_address)

    DT.approve(pool.address, toBase18(_DT_STAKE), from_wallet=web3_w)
    OCEAN.approve(pool.address, toBase18(_OCEAN_STAKE),from_wallet=web3_w)

    pool.bind(DT.address, toBase18(_DT_STAKE),
              toBase18(POOL_WEIGHT_DT), from_wallet=web3_w)
    pool.bind(OCEAN.address, toBase18(_OCEAN_STAKE),
              toBase18(POOL_WEIGHT_OCEAN), from_wallet=web3_w)

    pool.finalize(from_wallet=web3_w)
    
    return pool
