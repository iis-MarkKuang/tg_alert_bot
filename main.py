import json
import os
import time

import datetime
import pg8000
import requests
from dotenv import load_dotenv
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed
from prometheus_http_client import Prometheus
# Configs

# Add file handler with daily rotation and 30 days retention
logger.add(
    "logs/alert_bot_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Rotate at midnight
    retention="30 days",  # Keep logs for 30 days
    compression="gz",  # Compress rotated files using gzip
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    encoding="utf-8",
)

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
METRICS_URL = os.getenv("METRICS_URL")
# tron configs
TRON_TRX_WARNING = float(os.getenv("TRON_TRX_WARNING"))
TRON_ENERGY_WARNING = float(os.getenv("TRON_ENERGY_WARNING"))
TRON_NET_WARNING = float(os.getenv("TRON_NET_WARNING"))
TRON_ENERGY_WARNING_RATIO = float(os.getenv("TRON_ENERGY_WARNING_RATIO"))
TRON_NET_WARNING_RATIO = float(os.getenv("TRON_NET_WARNING_RATIO"))
TRON_BALANCE_WARNING_RATIO = float(os.getenv("TRON_BALANCE_WARNING_RATIO"))

logger.info(
    f"BOT_TOKEN: {BOT_TOKEN}, CHAT_ID: {CHAT_ID}, METRICS_URL: {METRICS_URL},\n"
    f"TRON_TRX_WARNING: {TRON_TRX_WARNING}, TRON_ENERGY_WARNING: {TRON_ENERGY_WARNING}, TRON_NET_WARNING: {TRON_NET_WARNING},\n"
)

# functions

prom = Prometheus()

@retry(stop=stop_after_attempt(10), wait=wait_fixed(1))
def send_telegram_message(bot_token: str, chat_id: str, message: str):
    """
    Send a message to a Telegram chat.
    :param bot_token: The Telegram bot token.
    :param chat_id: The ID of the chat to send the message to.
    :param message: The message to send.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=payload)
    response.raise_for_status()
    data = response.json()
    assert data["ok"]


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


def recur_trx_notif():
    """
    Send a heartbeat message every 8 hours to indicate the script is running.
    Only sends message once every 8 hours to avoid spam.
    """
    if not hasattr(recur_trx_notif, "last_heartbeat_time"):
        recur_trx_notif.last_heartbeat_time = 0

    current_time = time.time()
    # Check if 8 hours (28800 seconds) have passed
    # 将时间戳转换为本地时间元组
    local_time = time.localtime(current_time)
    # 提取分钟信息
    minutes = local_time.tm_min
    hours = local_time.tm_hour
    if minutes == 0 and hours in [0, 6, 12, 18]:
        message = get_oneoff_message()
        send_telegram_message(BOT_TOKEN, CHAT_ID, message)
        recur_trx_notif.last_heartbeat_time = current_time
        logger.info("Sent heartbeat message")
        logger.info(message)
    else:
        logger.info(f"cur min {minutes} and hour {hours} not match send timestamp, skipping...")



def alert_tron_trx_energy_net_v2(res_fields):
    """
    Alert if the Tron Trx, Energy or Net is below the warning threshold.
    Only sends alerts once every 30 minutes to avoid spam.
    :param tron: The TronTrxEnergyNet object.
    """
    # 使用类变量存储上次告警时间
    if not hasattr(alert_tron_trx_energy_net_v2, "last_alert_time"):
        alert_tron_trx_energy_net_v2.last_alert_time = 0

    current_time = time.time()
    # 检查是否到达发送间隔(30分钟 = 1800秒)
    if current_time - alert_tron_trx_energy_net_v2.last_alert_time < 1800:
        return

    alert_messages = []

    if res_fields['balance_remaining_ratio_float'] < TRON_BALANCE_WARNING_RATIO:
        alert_messages.append(
            f"⚠️ TRX余额不足! 当前: {res_fields['balance']:.3f}, 警告阈值: {TRON_TRX_WARNING}"
        )

    if res_fields['energy_remaining_ratio_float'] < TRON_ENERGY_WARNING_RATIO:
        alert_messages.append(
            f"⚠️ Energy不足! 当前: {res_fields['energy_remaining']}, 警告阈值: {res_fields['energy_limit'] * TRON_ENERGY_WARNING_RATIO}"
        )

    if res_fields['net_remaining_ratio_float'] < TRON_NET_WARNING_RATIO:
        alert_messages.append(
            f"⚠️ Net带宽不足! 当前: {res_fields['net_remaining']}, 警告阈值: {res_fields['net_limit'] * TRON_NET_WARNING_RATIO}"
        )

    if alert_messages:
        alert_text = "\n".join(alert_messages)
        # send_telegram_message(BOT_TOKEN, CHAT_ID, alert_text)
        # 更新最后发送时间
        alert_tron_trx_energy_net_v2.last_alert_time = current_time
        logger.info(f"Sent alert: {alert_text}")


def get_oneoff_message():
    try:
        current_time = datetime.datetime.now()
        now_datetime = current_time.strftime('%Y-%m-%dT%H:%M:%S')
        now_datetime_bj = (current_time + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%S')
        minus_one_day_datetime = (current_time - datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
        minus_one_day_datetime_bj = (current_time - datetime.timedelta(hours=16)).strftime('%Y-%m-%dT%H:%M:%S')
        genesis_datetime = '2025-03-04T00:00:00'
        connection = get_psql_conn()
        one_day_new_trx_count = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', None, None, None)
        one_day_success_trx_count = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', 'SUCCEED', None, None)
        one_day_failure_trx_count = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', 'FAILED', None, None)
        one_day_new_gte50_usdt_trx_count = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', None, 50000000, True)
        one_day_new_lt50_usdt_trx_count = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', None, 50000000, False)
        all_time_trx_count = query_trx(connection, genesis_datetime, now_datetime, 'count', None, None, None)
        all_time_trx_success_count = query_trx(connection, genesis_datetime, now_datetime, 'count', 'SUCCEED', None, None)
        all_time_trx_failure_count = query_trx(connection, genesis_datetime, now_datetime, 'count', 'FAILED', None, None)
        all_time_trx_amount = format(query_trx(connection, genesis_datetime, now_datetime, 'amount', 'SUCCEED', None, None) / 1000000, ',.2f')
        one_day_gte_50_ratio = '%.1f%%' % (one_day_new_gte50_usdt_trx_count / one_day_new_trx_count * 100) if one_day_new_trx_count > 0 else 0.0
        one_day_lte_50_ratio = '%.1f%%' % (one_day_new_lt50_usdt_trx_count / one_day_new_trx_count * 100) if one_day_new_trx_count > 0 else 0.0
        one_day_trx_amount = format(query_trx(connection, minus_one_day_datetime, now_datetime, 'FAILED', 'SUCCEED', None, None) / 1000000, ',.2f')

        # resource related fields
        resource_fields = get_resources_fields()
        alert_tron_trx_energy_net_v2(resource_fields)


        resource_message = get_resource_msg_simplified(resource_fields)

        top_qps_endpoint_data_tuple = get_top_qps_endpoint_data_tuple()
        alert_text = (f"GasFree Provider 截止 {now_datetime_bj} 数据汇总: \r\n"
                      f"# 整体交易数据  \r\n"
                      f" 天交易数: {one_day_new_trx_count} (失败:{one_day_failure_trx_count}) \r\n"
                      f" 天交易额: {one_day_trx_amount} (>50$: {one_day_gte_50_ratio}) \r\n"
                      f" 总交易数: {all_time_trx_count} (失败:{all_time_trx_failure_count}) \r\n"
                      f" 总交易额: {all_time_trx_amount}  \r\n"
                      f""
                      # # TODO to be supplied
                      # f"# 第三方数据  \r\n"
                      # f" 天交易数:  \r\n"
                      # f" 天交易额: $15,848,027.38 (>50%: 72.1%) \r\n"
                      # f" 总交易数: 2,919 (失败:0) \r\n"
                      # f" 总交易额: $138,103,653.59  \r\n"
                      f""
                      f"# 资源数据: \r\n"
                      f"{resource_message}"
                      f"# 接口调用QPS Top1: \r\n"
                      f" 名称: {top_qps_endpoint_data_tuple[0]} \r\n"
                      f" qps: {'%.2f' % float(top_qps_endpoint_data_tuple[1])}"
                      )

        return alert_text
    finally:
        if connection:
            cursor = connection.cursor()
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def get_psql_conn():
    return pg8000.connect(
        user="ro1",
        password="2x8g8w949tynkaka1",
        host="gasfree.cluster-ro-cmlrx8br13wh.us-east-1.rds.amazonaws.com",
        port="5432",
        database="gasfree"
    )


# Makes query about offline transactions
# params:
#     1. connection: pgsql connection
#     2. start_time: created_time start
#     3. end_time: created_time end
#     4. agg_type: aggregation func type, supports `count` and `sum`
#     5. state: transaction state, 'SUCCEED' | 'FAILED' | 'INPROGRESS' | 'WAITING'
def query_trx(connection, start_time, end_time, agg_type, state, bound, gt):
    try:
        # 连接到 PostgreSQL 数据库
        # 创建一个游标对象，用于执行 SQL 查询
        cursor = connection.cursor()
        # 定义要执行的 SQL 查询语句
        query_column = 'count(amount)' if agg_type == 'count' else 'sum(amount)'
        state_query = ""

        if state is not None:
            state_query += f" and state = '{state}'"
        if bound is not None and gt is not None:
            state_query += f" and amount {'>=' if gt else '<'} {bound}"
        query = (f"select {query_column} from gasfree_offchains where created_at between '{start_time}' and '{end_time}' {state_query}")
        print(query)
        # 执行 SQL 查询
        cursor.execute(query)
        # 获取查询结果
        results = cursor.fetchall()
        # 打印查询结果
        for row in results:
            print(row)
    except Exception as error:
        print("Error while connecting to PostgreSQL or executing query", error)
        return 0
    return row[0]

def main_trx():
    while True:
        try:
            recur_trx_notif()
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"Error in main loop: {e}")
        finally:
            time.sleep(60)


def get_resource_msg_simplified(res_dict):
    return (f" 能量剩余: {res_dict['energy_remain_ratio']} (约 {res_dict['estimated_trans_with_energy_with_activation']} - {res_dict['estimated_trans_with_energy_no_activation']} 笔交易) \r\n"
            f" 带宽剩余: {res_dict['net_remain_ratio']} (约 {res_dict['estimated_trans_with_net']} 笔交易) \r\n"
            f" 备用金剩: {res_dict['balance']} TRX \r\n"
    )

def get_resource_msg(res_dict):
    return (f"  Tron Trx额度: {res_dict['balance']} \r\n"
            f"  剩余能量: {res_dict['energy_remaining_str']} \r\n"
            f"  能量剩余比例: {res_dict['energy_remain_ratio']} \r\n"
            f"  剩余带宽: {res_dict['net_remaining_str']} \r\n"
            f"  带宽剩余比例: {res_dict['net_remain_ratio']} \r\n"
            f"  剩余能量能够支持交易(地址未激活)数量: {res_dict['estimated_trans_with_energy_with_activation']} \r\n"
            f"  剩余能量能够支持交易(地址已激活)数量: {res_dict['estimated_trans_with_energy_no_activation']} \r\n"
            f"  剩余带宽能够支持交易数量: {res_dict['estimated_trans_with_net']} \r\n")


def get_resources_fields():
    resp = requests.get('https://apilist.tronscanapi.com/api/accountv2?address=TFNX7TKYCm1kUYDECjkrogBwYZvt69XQNy')
    resource_json = resp.json()
    res = {}
    res['balance_limit'] = 10466772977
    res['balance_remaining_ratio_float'] = resource_json['balance'] / res['balance_limit']
    res['balance'] = format(resource_json['balance'] / 1000000, ',.2f')
    res['energy_cost'] = resource_json['energyCost']
    res['net_cost'] = resource_json['netCost']
    res['energy_remaining'] = resource_json['bandwidth']['energyRemaining']
    res['energy_remaining_ratio_float'] = resource_json['bandwidth']['energyRemaining'] / resource_json['bandwidth']['energyLimit']
    res['energy_remaining_str'] = '%.1f' % resource_json['bandwidth']['energyRemaining']
    res['energy_limit'] = resource_json['bandwidth']['energyLimit']
    res['net_remaining'] = resource_json['bandwidth']['netRemaining']
    res['net_remaining_ratio_float'] = resource_json['bandwidth']['netRemaining'] / resource_json['bandwidth']['netLimit']
    res['net_remaining_str'] = '%.1f' % resource_json['bandwidth']['netRemaining']
    res['net_limit'] = resource_json['bandwidth']['netLimit']
    res['net_remain_ratio'] =  '%.1f%%' % (res['net_remaining'] / res['net_limit'] * 100)
    res['energy_remain_ratio'] = '%.1f%%' % (res['energy_remaining'] / res['energy_limit'] * 100)
    res['estimated_trans_with_energy_with_activation'] = '%.1f' % (res['energy_remaining'] / 340000)
    res['estimated_trans_with_energy_no_activation'] = '%.1f' % (res['energy_remaining'] / 170000)
    res['estimated_trans_with_net'] =  '%.1f' % (res['net_remaining'] / 699)
    return res


if __name__ == "__main__":
    main_trx()
