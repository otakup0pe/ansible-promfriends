"""testinfra checks for the node-only promfriends scenario."""


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


def test_textfiles_directory_ownership_is_declared(host):
    """Pin ownership so play order cannot silently break producers."""
    d = host.file("/var/run/promnode/textfiles")
    assert d.group == "prometheus"
    # Producers replace one another's files, so the directory cannot be sticky.
    assert d.mode & 0o020, "textfiles dir is not group-writable (mode %o)" % d.mode


def test_textfiles_parent_is_traversable(host):
    """Producers need traversal through the parent regardless of leaf mode."""
    d = host.file("/var/run/promnode")
    assert d.is_directory
    assert d.mode & 0o001, (
        "promnode parent is not world-traversable (mode %o); a non-root "
        "producer cannot reach textfiles/ regardless of the leaf's mode"
        % d.mode
    )


def test_group_member_can_actually_write_a_textfile(host):
    """Test producer capability independently of the permission mechanism."""
    host.run("useradd -r -G prometheus molecule-textfile-writer 2>/dev/null")
    probe = "/var/run/promnode/textfiles/molecule-write-check.prom"
    host.run("rm -f %s", probe)
    cmd = host.run(
        "su -s /bin/sh -c 'echo molecule_write_check 1 > %s' "
        "molecule-textfile-writer" % probe
    )
    try:
        assert cmd.rc == 0, (
            "a prometheus-group member cannot write to the textfile dir: %r"
            % cmd.stderr
        )
        assert host.file(probe).exists
    finally:
        host.run("rm -f %s", probe)


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
