"""testinfra checks for the pkg-exporter repair and boot-run scenario."""

import time


VENV = "/opt/promnode-pkg-exporter"
METRIC = "/var/run/promnode/textfiles/pkg-exporter.prom"
VERSION_PROBE = "import sys; print('%d.%d' % sys.version_info[:2])"


def test_venv_can_import_apt(host):
    """Require the venv to see dpkg's system python3-apt package."""
    cmd = host.run("%s/bin/python -c 'import apt'" % VENV)
    assert cmd.rc == 0, "venv cannot import apt: %r" % cmd.stderr


def test_venv_interpreter_matches_the_system_interpreter(host):
    """Require the repaired venv to use the host Python minor version."""
    venv = host.run('%s/bin/python -c "%s"' % (VENV, VERSION_PROBE))
    system = host.run('python3 -c "%s"' % VERSION_PROBE)
    assert venv.rc == 0
    assert system.rc == 0
    assert venv.stdout.strip() == system.stdout.strip(), (
        "venv interpreter reports %r, system reports %r"
        % (venv.stdout.strip(), system.stdout.strip())
    )


def test_pkg_exporter_entrypoint_is_executable(host):
    f = host.file("%s/bin/pkg-exporter" % VENV)
    assert f.exists
    assert f.mode & 0o111, "pkg-exporter is not executable (mode %o)" % f.mode


def test_pkg_exporter_timer_enabled(host):
    assert host.service("promnode-pkg-exporter.timer").is_enabled


def test_pkg_exporter_repopulates_volatile_metric_on_timer_start(host):
    for _ in range(20):
        if host.file(METRIC).exists:
            break
        time.sleep(0.5)

    metric = host.file(METRIC)
    assert metric.exists
    assert metric.size > 0
