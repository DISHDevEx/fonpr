"""
Define fixtures and configurations that can be reused is all pytests.
"""

import pytest


@pytest.fixture(scope="module")
def prom_memory_query():
    """
    Return a string written in promql to retrieve memory for each pod.
    """
    max_memory_query = "sum by (pod)  (max_over_time(container_memory_usage_bytes[3h]))"
    return max_memory_query


@pytest.fixture(scope="module")
def sample_response():
    """
    Return a sample of nested dictionaries in the same format that the Prometheus server returns.
    """
    sample_response = [
        {
            "metric": {"pod": "open5gs-smf-684588d586-gbqss"},
            "value": [1681230632.08, "87298048"],
        }
    ]
    return sample_response
