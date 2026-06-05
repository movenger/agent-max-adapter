from hermes_max_adapter.observability import InMemoryMetrics


def test_in_memory_metrics_increment_counter():
    metrics = InMemoryMetrics()
    metrics.increment("inbound_updates_total")
    metrics.increment("inbound_updates_total")
    assert metrics.counters["inbound_updates_total"] == 2
