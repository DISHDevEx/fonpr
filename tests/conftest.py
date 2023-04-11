"""
Define fixtures and configuration
that can be reused throughout pytest without redefinition.
It also defines the configurations for pytest.
"""

import pytest


@pytest.fixture(scope="module")
def prom_memory_query():
    """
    string written in promql to retrieve memory on a per pod basis
    """
    max_memory_query = "sum by (pod)  (max_over_time(container_memory_usage_bytes[3h]))"
    return max_memory_query


@pytest.fixture(scope="module")
def sample_response():
    """
    This is a sample respons that prometheus server would return. 
    List of nested dictionaries is the format that the prometheus server returns. 
    
    In this sample respons, there is only one pod running. 
    Hence we get a list containing one element. This one element is a nested dictionary. 
    """
    sample_response = [{
        "metric": {"pod": "open5gs-smf-684588d586-gbqss"},
        "value": [1681230632.08, "87298048"],
    }]
    return sample_response
