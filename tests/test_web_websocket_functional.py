"""HTTP websocket server functional tests"""

import asyncio
import pytest
import aiohttp
from aiohttp import web
from aiohttp import helpers


@pytest.mark.run_loop
def test_websocket_json(create_app_and_client):
    @asyncio.coroutine
    def handler(request):
        ws = web.WebSocketResponse()
        yield from ws.prepare(request)
        msg = yield from ws.receive()

        msg_json = msg.json()
        answer = msg_json['test']
        ws.send_str(answer)

        yield from ws.close()
        return ws

    app, client = yield from create_app_and_client()
    app.router.add_route('GET', '/', handler)

    ws = yield from client.ws_connect('/')
    expected_value = 'value'
    payload = '{"test": "%s"}' % expected_value
    ws.send_str(payload)

    resp = yield from ws.receive()
    assert resp.data == expected_value


@pytest.mark.run_loop
def test_websocket_json_invalid_message(create_app_and_client):
    @asyncio.coroutine
    def handler(request):
        ws = web.WebSocketResponse()
        yield from ws.prepare(request)
        msg = yield from ws.receive()

        try:
            msg.json()
        except ValueError:
            ws.send_str("ValueError raised: '%s'" % msg.data)
        else:
            raise Exception("No ValueError was raised")
        finally:
            yield from ws.close()
        return ws

    app, client = yield from create_app_and_client()
    app.router.add_route('GET', '/', handler)

    ws = yield from client.ws_connect('/')
    payload = 'NOT A VALID JSON STRING'
    ws.send_str(payload)

    resp = yield from ws.receive()
    assert payload in resp.data


@pytest.mark.run_loop
def test_websocket_receive_json(create_app_and_client):
    @asyncio.coroutine
    def handler(request):
        ws = web.WebSocketResponse()
        yield from ws.prepare(request)

        data = yield from ws.receive_json()
        answer = data['test']
        ws.send_str(answer)

        yield from ws.close()
        return ws

    app, client = yield from create_app_and_client()
    app.router.add_route('GET', '/', handler)

    ws = yield from client.ws_connect('/')
    expected_value = 'value'
    payload = '{"test": "%s"}' % expected_value
    ws.send_str(payload)

    resp = yield from ws.receive()
    assert resp.data == expected_value


@pytest.mark.run_loop
def test_send_recv_text(create_app_and_client, loop):

    closed = helpers.create_future(loop)

    @asyncio.coroutine
    def handler(request):
        ws = web.WebSocketResponse()
        yield from ws.prepare(request)
        msg = yield from ws.receive_str()
        ws.send_str(msg+'/answer')
        yield from ws.close()
        closed.set_result(1)
        return ws

    app, client = yield from create_app_and_client()
    app.router.add_route('GET', '/', handler)

    ws = yield from client.ws_connect('/')
    ws.send_str('ask')
    msg = yield from ws.receive()
    assert msg.tp == aiohttp.MsgType.text
    assert 'ask/answer' == msg.data

    msg = yield from ws.receive()
    assert msg.tp == aiohttp.MsgType.close
    assert msg.data == 1000
    assert msg.extra == ''

    assert ws.closed
    assert ws.close_code == 1000

    yield from closed
