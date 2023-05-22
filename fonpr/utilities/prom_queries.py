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
    """
    Function to store and return queries that find network metrics in prometheus.This query is specific to only the upf function

    Returns
    -------
        queries: list[str]


    Notes
    -------
        How network query works:

            (1) The feature container_network_transmit_bytes_total is a counter; it monotonically increases.
               (See https://prometheus.io/docs/concepts/metric_types/#counter).

            (2) That feature comes in units of bytes.

            (3) The Prometheus function rate takes in a time series and a width of a scrape window and returns a per second average.

               (i)The time rate of change of the time series m over the scrape interval of width d is rate(m[d]).
                  It is a time series. Its units are bytes/second.

               (ii)The restriction of this rate time series to the time window tw is rate(m[d])[tw].
                     (e.g. The time series from four hours ago to 3 hours ago is rate(m[d])[4h:3h]. )

               (iii)The query rate(m[d])[tw] does not return any results if there are less than two times from the time series m within the time window tw.
                     Thus, the width of the time window should be at least twice the scrape interval d.
            (4) Sum by pod implies that we will sum over all containers per pod. This will return metrics on a per pod basis.
    """
    avg_upf_network_query = "sum by (pod) (rate(container_network_transmit_bytes_total {pod=~'open5gs-upf.*'}[1h]))"

    return [avg_upf_network_query]
 

def prom_network_upf_interfaces_query():
    """
    Store and return queries that find cpu/memory metrics in Prometheus.
    The first two queries built here capture the Rx,Tx for all interfaces on all UPF pods.
    The third query built here captures the node sizing and dimensioning information for UPF pods.

    Returns
    -------
        queries: list[str]


    Notes
    -------
        How network query works:

            (1) The feature container_network_transmit_bytes_total is a counter; it monotonically increases.
               (See https://prometheus.io/docs/concepts/metric_types/#counter).

            (2) That feature comes in units of bytes.

            (3) The Prometheus function rate takes in a time series and a width of a scrape window and returns a per second average.

               (i)The time rate of change of the time series m over the scrape interval of width d is rate(m[d]).
                  It is a time series. Its units are bytes/second.

               (ii)The restriction of this rate time series to the time window tw is rate(m[d])[tw].
                     (e.g. The time series from four hours ago to 3 hours ago is rate(m[d])[4h:3h]. )

               (iii)The query rate(m[d])[tw] does not return any results if there are less than two times from the time series m within the time window tw.
                     Thus, the width of the time window should be at least twice the scrape interval d.
            (4) Sum by pod implies that we will sum over all containers per pod. This will return metrics on a per pod basis.

        How sizing queries work:
            kube_node_labels returns all labels for a specific node.
    """
    avg_upf_interfaces_network_tx_query = (
        "rate(container_network_transmit_bytes_total {pod=~'open5gs-upf.*'}[1h])"
    )
    avg_upf_interfaces_network_rx_query = (
        "rate(container_network_receive_bytes_total {pod=~'open5gs-upf.*'}[1h])"
    )
    node_sizing_query = "kube_node_labels{label_eks_amazonaws_com_nodegroup=~'upf.*'}"

    return [
        avg_upf_interfaces_network_tx_query,
        avg_upf_interfaces_network_rx_query,
        node_sizing_query,
    ]


def prom_query_rl_upf_experiment1():
    # Get the last 15 minutes of combined user plane network traffic over all upf pods
    throughput = "sum (container_network_transmit_bytes_total {pod=~'open5gs-upf.*', interface=~'eth.*'}) by (time)[15m:]"
    
    # Get pod info for all pods with open5gs-upf in its name over the past 15 minutes
    active_pods = "kube_pod_info{pod=~'open5gs-upf.*'}[15m:]"

    return [throughput, active_pods]