from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta

    
# Set up Prometheus client
prometheus_url = 'http://10.0.101.214:9090'
# prometheus_client = PrometheusConnect(url=prometheus_url)

prom = PrometheusConnect(url=prometheus_url)

# Define the time range you want to query
end_time = datetime.utcnow()  # End time is the current time
start_time = end_time - timedelta(days=1)  # Start time -1 day

# Define the query and label config
query = 'sum(rate(container_cpu_usage_seconds_total{container!~"POD|"}[5m])) by (namespace,pod)'


# Make the range query and retrieve the data
#data = prom.custom_query_range(query=query, start_time=start_time, end_time=end_time,step=10000000 )
data = prom.custom_query(query=query)

# Print the data
print(data)

