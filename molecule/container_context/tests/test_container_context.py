"""Test live services from the container-context role path."""

import json


def test_blackbox_config_is_rendered(host):
    config = host.file("/opt/prometheus/etc/blackbox.yml")
    assert config.is_file
    assert "http_alive:" in config.content_string


def test_blackbox_container_is_running(host):
    result = host.run(
        "/usr/bin/docker inspect --format '{{.State.Running}}' prom_blackbox"
    )
    assert result.rc == 0
    assert result.stdout.strip() == "true"


def test_blackbox_serves_over_mtls(host):
    result = host.run(
        "curl -sS --cacert /opt/prometheus/etc/ca.crt "
        "--cert /opt/prometheus/etc/server.crt "
        "--key /opt/prometheus/etc/server.key "
        "-o /dev/null -w '%{http_code}' https://localhost:9115/"
    )
    assert result.rc == 0
    assert result.stdout.strip() == "200"


def test_cadvisor_container_is_running(host):
    result = host.run("/usr/bin/docker inspect --format '{{.State.Running}}' cadvisor")
    assert result.rc == 0
    assert result.stdout.strip() == "true"


def test_cadvisor_is_ready(host):
    inspect = host.run("/usr/bin/docker inspect cadvisor")
    assert inspect.rc == 0
    ports = json.loads(inspect.stdout)[0]["NetworkSettings"]["Ports"]
    host_port = next(binding[0]["HostPort"] for binding in ports.values() if binding)

    result = host.run(f"curl -fsS http://127.0.0.1:{host_port}/healthz")
    assert result.rc == 0
    assert result.stdout.strip() == "ok"
