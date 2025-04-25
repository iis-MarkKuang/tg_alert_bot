import json

import requests
from prometheus_http_client import Prometheus
from tenacity import retry, stop_after_attempt, wait_fixed

prom = Prometheus()

def get_top_qps_endpoint_data_tuple():
    query = 'rate(http_server_requests_seconds_count{job="gasfree-api"}[60s])'
    res_json = json.loads(prom.query(metric=query))
    qps_data = res_json["data"]["result"]
    qps_data_sorted = sorted(qps_data, key=lambda x: x['value'][1], reverse=True)
    if qps_data_sorted and len(qps_data_sorted) > 0:
        return qps_data_sorted[0]['metric']['uri'], qps_data_sorted[0]['value'][1]
    return None, None

@retry(stop=stop_after_attempt(10), wait=wait_fixed(1))
def get_metrics(url: str) -> str:
    """
    Get the metrics from the URL.
    :param url: The URL to get the metrics from.
    :return: The metrics.
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.text

class TronTrxEnergyNet:
    def __init__(self, trx: float, energy: float, net: float):
        self.trx = trx
        self.energy = energy
        self.net = net

def parse_tron_trx_energy_net(metrics: str) -> TronTrxEnergyNet:
    """
    Parse the metrics and return the TronTrxEnergyNet object.
    :param metrics: The metrics to parse.
    :return: The TronTrxEnergyNet object.
    """
    trx = 0.0
    energy = 0.0
    net = 0.0

    for line in metrics.split("\n"):
        if line.startswith("tron_trx{"):
            trx = (
                float(line.split("}")[1].strip(",")) / 1000000
            )  # Convert from sun to TRX
        elif line.startswith("tron_energy{"):
            energy = float(line.split("}")[1].strip(","))
        elif line.startswith("tron_net{"):
            net = float(line.split("}")[1].strip(","))

    return TronTrxEnergyNet(trx, energy, net)

def get_resources_fields():
    resp = requests.get('https://apilist.tronscanapi.com/api/accountv2?address=TFNX7TKYCm1kUYDECjkrogBwYZvt69XQNy')
    resource_json = resp.json()
    balance_limit = 10466772977
    balance = resource_json['balance']
    energy = resource_json['bandwidth']['energyRemaining']
    energy_limit = resource_json['bandwidth']['energyLimit']
    net = resource_json['bandwidth']['netRemaining']
    net_limit = resource_json['bandwidth']['netLimit']

    res = {
        'balance_limit': balance_limit,
        'balance_remaining_ratio_float': balance / balance_limit,
        'balance': format(balance / 1000000, ',.2f'),
        'balance_float': balance / 1000000,
        'energy_cost': resource_json['energyCost'],
        'net_cost': resource_json['netCost'],
        'energy_remaining': energy,
        'energy_remaining_ratio_float': energy / energy_limit,
        'energy_remaining_str': '%.1f' % energy,
        'energy_limit': energy_limit,
        'net_remaining': net,
        'net_remaining_ratio_float': net / net_limit,
        'net_remaining_str': '%.1f' % net,
        'net_limit': net_limit,
        'net_remain_ratio':  '%.1f%%' % (net / net_limit * 100),
        'energy_remain_ratio': '%.1f%%' % (energy / energy_limit * 100),
        'estimated_trans_with_energy_with_activation': '%.1f' % (energy / 340000),
        'estimated_trans_with_energy_no_activation': '%.1f' % (energy / 170000),
        'estimated_trans_with_net':  '%.1f' % (net / 699)
    }
    return res
