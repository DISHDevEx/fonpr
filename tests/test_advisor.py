"""
Module to contain all tests pertaining to agent advisors. 
"""

from nose.tools import assert_is_not_none
from unittest.mock import patch
from fonpr import PromClient



def test_prometheus_advisor(prom_memory_query,sample_response):
    """
    This is a unit test. 
    It ensures that the advisor behaves in the expected manner. 
    Expected behavior --> set the query for the advisor. ask the advisor to run the query. Expect non-null response.
    ##https://stackoverflow.com/questions/71111067/how-does-mock-testing-rest-apis-test-the-api-when-the-actual-api-is-not-called
    """
    ## patch the run_queries function with the expected output. 
    with patch('fonpr.advisors.prometheus_client_advisor.PromClient.run_queries') as mock_get:
        mock_get.return_value = sample_response
        
        prom_client_advisor = PromClient()
        
        prom_client_advisor.add_query_from_string(prom_memory_query)
        
        results = prom_client_advisor.run_queries()
        
        assert_is_not_none(results)