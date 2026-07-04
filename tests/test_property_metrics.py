from services.real_estate import PropertyMetricsService


def test_property_metrics_runs():
    df = PropertyMetricsService().property_metrics()
    assert df is not None
