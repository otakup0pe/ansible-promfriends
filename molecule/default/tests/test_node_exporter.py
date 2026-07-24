"""testinfra checks for the node-only promfriends scenario.

Asserts the native node_exporter deployment: binary, systemd unit,
listening port, mutual-TLS web config, supporting group/dirs, and that
the exporter actually serves metrics over mTLS.
"""


def test_node_exporter_binary(host):
    f = host.file("/usr/local/bin/node_exporter")
    assert f.exists
    assert f.is_file
    assert f.mode == 0o770


def test_node_exporter_service(host):
    svc = host.service("node_exporter")
    assert svc.is_running
    assert svc.is_enabled


def test_node_exporter_listening(host):
    assert host.socket("tcp://0.0.0.0:9100").is_listening


def test_node_exporter_web_config(host):
    f = host.file("/opt/prometheus/etc/node_exporter-web_config.yml")
    assert f.exists
    assert "RequireAndVerifyClientCert" in f.content_string


def test_prometheus_group_exists(host):
    assert host.group("prometheus").exists


def test_textfiles_directory(host):
    d = host.file("/var/run/promnode/textfiles")
    assert d.is_directory


def test_tls_assets_present(host):
    for name in ("server.crt", "server.key", "ca.crt"):
        assert host.file("/opt/prometheus/etc/%s" % name).exists


def test_node_exporter_serves_metrics_over_mtls(host):
    hostname = host.check_output("hostname")
    cmd = host.run(
        "curl -sS --cacert /opt/prometheus/etc/ca.crt "
        "--cert /opt/prometheus/etc/server.crt "
        "--key /opt/prometheus/etc/server.key "
        "-o /dev/null -w '%%{http_code}' https://%s:9100/metrics" % hostname
    )
    assert cmd.rc == 0
    assert cmd.stdout.strip() == "200"
