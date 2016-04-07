import os

import pytest

from test.fixtures import KafkaFixture, ZookeeperFixture


@pytest.fixture(scope="module")
def version():
    if 'KAFKA_VERSION' not in os.environ:
        return ()
    return tuple(map(int, os.environ['KAFKA_VERSION'].split('.')))


@pytest.fixture(scope="module")
def zookeeper(version, request):
    assert version
    zk = ZookeeperFixture.instance()
    def fin():
        zk.close()
    request.addfinalizer(fin)
    return zk


@pytest.fixture(scope="module")
def kafka_broker(version, zookeeper, request):
    assert version
    k = KafkaFixture.instance(0, zookeeper.host, zookeeper.port,
                              partitions=4)
    def fin():
        k.close()
    request.addfinalizer(fin)
    return k


@pytest.fixture
def conn(mocker):
    from kafka.conn import ConnectionStates
    from kafka.future import Future
    from kafka.protocol.metadata import MetadataResponse
    conn = mocker.patch('kafka.client_async.BrokerConnection')
    conn.return_value = conn
    conn.state = ConnectionStates.CONNECTED
    conn.send.return_value = Future().success(
        MetadataResponse[0](
            [(0, 'foo', 12), (1, 'bar', 34)],  # brokers
            []))  # topics
    conn.blacked_out.return_value = False
    conn.connect.side_effect = lambda: conn.state
    conn.connecting = lambda: conn.connect() in (ConnectionStates.CONNECTING,
                                                 ConnectionStates.HANDSHAKE)
    conn.connected = lambda: conn.connect() is ConnectionStates.CONNECTED
    return conn
