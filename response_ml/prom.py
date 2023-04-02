from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import pprint
    
# Set up Prometheus client
prometheus_url = 'http://10.0.101.214:9090' 
prom = PrometheusConnect(url=prometheus_url)

## Queries
'''how cpu queries works: 
 (1)rate(container_cpu_usage_seconds_total[2m])[3h:]  returns the cpu cores avg for 2 minute windows for the last 3 hours
    (a) by taking the rate of increase of container_cpu_usage_seconds_total we get the number of CPU-seconds consumed per second.
       (i) container_cpu_usage_seconds_total is a counter (https://prometheus.io/docs/concepts/metric_types/#counter). 1 CPU Second = 1 Core fired up for that second. 
       (ii) rate(m[d])[timewindow] - returns the per-second rate of change for metric for a certain time window
       (iii) rate(x[35s]) = difference in value over 35 seconds / 35s
       (v) rate does not return any results at all if there are less than two samples available.
       (vi) time range should be atleast 2x the scrape interval. So we are using 2m
       ex/ rate(container_cpu_usage_seconds_total[10m]) is 1.34. This means our container spent an avg of 1.34 CPU seconds per seconds. (https://github.com/google/cadvisor/issues/2026)
       extra:https://blog.freshtracks.io/a-deep-dive-into-kubernetes-metrics-part-3-container-resource-metrics-361c5ee46e66
    (c)[3h:] returns the last 3 hours of the time series
    
 (2) max_over_time calculates the maximum value over raw samples on the given lookbehind window per each time series returned from the given series_selector. 
    (a) avg_over_time does the same operation replacing max with avg
 
 (3) sum by (pod) prints the sum of of all containers in a pod 
''' 
max_cpu_query = 'sum by (pod) (max_over_time(irate (container_cpu_usage_seconds_total[2m]) [3h:]))'
avg_cpu_query = 'sum by (pod) (avg_over_time(irate (container_cpu_usage_seconds_total[2m]) [3h:]))'

#memory queries are pretty straight forward: take an avg/max over time for the metric. And sum over all containers in the pod. 
max_memory_query= 'sum by (pod)  (max_over_time(container_memory_usage_bytes[3h]))'
avg_memory_query= 'sum by (pod)  (avg_over_time(container_memory_usage_bytes[3h]))'

## Aggregate all data: 
max_cpu_data = prom.custom_query(query=max_cpu_query)
avg_cpu_data = prom.custom_query(query=avg_cpu_query)
max_memory_query = prom.custom_query(query=max_memory_query)
avg_memory_query = prom.custom_query(query=avg_memory_query)

# Print the data
#pprint.pprint(avg_memory_query)


#turn the data into a pandas dataframe
import numpy as np
import pandas as pd

for i in avg_memory_query:
 try:
  print(i['metric']['pod'])
 except KeyError:
  print("empty records found, ignoring")
 