"""
Create prometheus queries for the prometheus advisor.
"""


def prom_cpu_mem_queries():
    """
    Function to store and return queries that find cpu/memory metrics in prometheus.

    Returns
    -------
        queries: list[str]


    Notes
    -------
        How cpu queries works:

            (1) The feature container_cpu_usage_seconds_total is a counter; it monotonically increases.
               (See https://prometheus.io/docs/concepts/metric_types/#counter).

            (2) That feature comes in units of CPU seconds. One CPU seconds is one core running for one second.

            (3) The Prometheus function rate takes in a time series and a width of a scrape window.

               (i)The time rate of change of the time series m over the scrape interval of width d is rate(m[d]).
                  It is a time series. Its units are CPU seconds per second, or just CPUs.
                  (See https://github.com/google/cadvisor/issues/2026#issuecomment-1003120833.)
                  e.g.If for a container rate(container_cpu_usage_seconds_total[10m]) is 1.34 then that container used an average of 1.34 CPU seconds per second.
                  You could say that the container was using 1.34 of the total available CPUs.

               (ii)The restriction of this rate time series to the time window tw is rate(m[d])[tw].
                     (e.g. The time series from four hours ago to 3 hours ago is rate(m[d])[4h:3h]. )

               (iii)The query rate(m[d])[tw] does not return any results if there are less than two times from the time series m within the time window tw.
                     Thus, the width of the time window should be at least twice the scrape interval d.

        How memory queries work:
            Memory queries are pretty straight forward: take an avg/max over time for the metric. And sum over all containers in the pod.
    """
    max_cpu_query = "sum by (pod) (max_over_time(rate (container_cpu_usage_seconds_total[2m]) [3h:]))"
    avg_cpu_query = "sum by (pod) (avg_over_time(rate (container_cpu_usage_seconds_total[2m]) [3h:]))"

    max_memory_query = "sum by (pod)  (max_over_time(container_memory_usage_bytes[3h]))"
    avg_memory_query = "sum by (pod)  (avg_over_time(container_memory_usage_bytes[3h]))"

    return [max_cpu_query, avg_cpu_query, max_memory_query, avg_memory_query]
    
    
def prom_network_upf_query():
    
    avg_upf_network_query = "sum by (pod) (avg_over_time(rate(container_network_transmit_bytes_total {pod=~'open5gs-upf.*'}[1m])[1h:]))"
    
    return[avg_upf_network_query]