import pathlib
import json
import typing

import pytest
import pytest_asyncio
from juju.action import Action
from juju.model import Model
from juju.application import Application
from juju.unit import Unit

from pytest_operator.plugin import OpsTest

NUM_UNITS = 3
UNIT_NUM_PARAMS = tuple(pytest.param(i, id=f"any-charm/{i}") for i in range(NUM_UNITS))


@pytest.fixture(name="model", scope="module")
def model_fixture(ops_test: OpsTest) -> Model:
    model = ops_test.model
    assert model
    return model


@pytest_asyncio.fixture(name="any_charm", scope="module")
async def any_charm_fixture(model: Model) -> Application:
    test_charm_path = pathlib.Path(__file__).parent / "secret_storage_test_charm.py"
    secret_storage_path = pathlib.Path(__file__).parent.parent.parent / "src" / "secret_storage.py"
    config = {
        "src-overwrite": json.dumps(
            {
                "any_charm.py": test_charm_path.read_text(),
                "secret_storage.py": secret_storage_path.read_text(),
            }
        )
    }
    app = await model.deploy("any-charm", channel="beta", config=config, num_units=NUM_UNITS)
    await model.wait_for_idle(status="active")
    return app


@pytest_asyncio.fixture(name="run_rpc", scope="module")
async def run_rpc_fixture(any_charm: Application):
    async def run_rpc(
            method: str,
            *,
            unit_num: typing.Union[str, int],
            args: typing.Optional[list] = None,
            kwargs: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ):
        unit: Unit
        if unit_num == "leader":
            unit = [u for u in any_charm.units if await u.is_leader_from_status()][0]
        elif isinstance(unit_num, int):
            unit = any_charm.units[unit_num]
        else:
            raise ValueError("unknown unit number: {}".format(unit_num))
        params = {"method": method}
        if args:
            params["args"] = json.dumps(args)
        if kwargs:
            params["kwargs"] = json.dumps(kwargs)
        action: Action = await unit.run_action("rpc", **params)
        await action.wait()
        if "return" not in action.results:
            print(action.results)
        return json.loads(action.results["return"])

    return run_rpc


@pytest.mark.parametrize("unit_num", UNIT_NUM_PARAMS)
async def test_initial_data(run_rpc, unit_num):
    assert await run_rpc(unit_num=unit_num, method="get_all") == {}


@pytest.mark.parametrize("unit_num", UNIT_NUM_PARAMS)
async def test_initial_change_history(run_rpc, unit_num):
    assert await run_rpc(unit_num=unit_num, method="get_change_history") == []


async def test_event_history(run_rpc):
    event_history = await run_rpc(method="get_event_history", unit_num="leader")
    pivot = [e["is_initialized"] for e in event_history].index(True)
    assert event_history[pivot]["event"] == "RelationChangedEvent"
    assert "RelationChangedEvent" not in [e["event"] for e in event_history[:pivot]]
    assert all(e["is_initialized"] for e in event_history[pivot:])


async def test_put(run_rpc, model):
    excepted_history = []
    for value in (0, 1, "2"):
        excepted_history.append({"foo": value})
        await run_rpc(method="put", unit_num="leader", args=["foo", value])
        await model.wait_for_idle(status="active")
        for unit_num in range(3):
            assert await run_rpc(method="get", unit_num=unit_num, args=["foo"]) == value
            assert await run_rpc(method="get_all", unit_num=unit_num) == {"foo": value}
            assert (
                    await run_rpc(method="get_change_history",
                                  unit_num=unit_num) == excepted_history
            )


@pytest.mark.parametrize("unit_num", UNIT_NUM_PARAMS)
async def test_put_same(run_rpc, model, unit_num):
    current_history = await run_rpc(method="get_change_history", unit_num="leader")
    current_value = await run_rpc(method="get", unit_num="leader", args=["foo"])
    await run_rpc(method="put", unit_num="leader", args=["foo", current_value])
    await model.wait_for_idle(status="active")
    assert await run_rpc(method="get", unit_num=unit_num, args=["foo"]) == current_value
    assert await run_rpc(method="get_change_history", unit_num=unit_num) == current_history


async def test_delete_non_existent(run_rpc, model):
    current_history = await run_rpc(method="get_change_history", unit_num="leader")
    current_data = await run_rpc(method="get_all", unit_num="leader")
    await run_rpc(method="delete", unit_num="leader", args=["bar"])
    await model.wait_for_idle(status="active")
    assert await run_rpc(method="get_all", unit_num="leader") == current_data
    assert await run_rpc(method="get_change_history", unit_num="leader") == current_history


async def test_delete_to_empty(run_rpc, model):
    current_history = await run_rpc(method="get_change_history", unit_num="leader")
    await run_rpc(method="delete", unit_num="leader", args=["foo"])
    await model.wait_for_idle(status="active")
    for unit_num in range(3):
        assert await run_rpc(method="get_all", unit_num=unit_num) == {}
        new_history = current_history + [{}]
        assert await run_rpc(method="get_change_history", unit_num=unit_num) == new_history


async def test_put_many(run_rpc, model):
    current_history = await run_rpc(method="get_change_history", unit_num="leader")
    await run_rpc(method="put", unit_num="leader", args=["foo", {"foo": 1}])
    await model.wait_for_idle(status="active")
    await run_rpc(method="put", unit_num="leader", args=["bar", {"bar": []}])
    await model.wait_for_idle(status="active")
    for unit_num in range(3):
        assert await run_rpc(method="get_all", unit_num=unit_num) == {
            "foo": {"foo": 1},
            "bar": {"bar": []},
        }
        new_history = current_history + [
            {"foo": {"foo": 1}},
            {"foo": {"foo": 1}, "bar": {"bar": []}},
        ]
        assert await run_rpc(method="get_change_history", unit_num=unit_num) == new_history


async def test_delete_one(run_rpc, model):
    current_history = await run_rpc(method="get_change_history", unit_num="leader")
    await run_rpc(method="delete", unit_num="leader", args=["foo"])
    await model.wait_for_idle(status="active")
    for unit_num in range(3):
        assert await run_rpc(method="get_all", unit_num=unit_num) == {"bar": {"bar": []}}
        new_history = current_history + [{"bar": {"bar": []}}]
        assert await run_rpc(method="get_change_history", unit_num=unit_num) == new_history
