import datetime
import os
import time

from dotenv import load_dotenv
from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

from db_operations import get_psql_conn, query_trx, query_addresses, query_last_day_trx_cnt_rank, \
    query_all_time_trx_cnt_rank
from metrics_operations import get_top_qps_endpoint_data_tuple, get_resources_fields
from telegram_operations import send_telegram_message

# Configs
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
CHAT_ID_INNER = os.getenv("CHAT_ID_INNER")
CHAT_ID_EXP = os.getenv("CHAT_ID_EXP")
METRICS_URL = os.getenv("METRICS_URL")
# tron configs
TRON_TRX_WARNING = float(os.getenv("TRON_TRX_WARNING"))
TRON_ENERGY_WARNING = float(os.getenv("TRON_ENERGY_WARNING"))
TRON_NET_WARNING = float(os.getenv("TRON_NET_WARNING"))
TRON_ENERGY_WARNING_RATIO = float(os.getenv("TRON_ENERGY_WARNING_RATIO"))
TRON_NET_WARNING_RATIO = float(os.getenv("TRON_NET_WARNING_RATIO"))
TRON_BALANCE_WARNING_RATIO = float(os.getenv("TRON_BALANCE_WARNING_RATIO"))

ALERT_INTERVAL = 600

logger.info(
    f"BOT_TOKEN: {BOT_TOKEN}, CHAT_ID: {CHAT_ID_EXP}, METRICS_URL: {METRICS_URL},\n"
    f"TRON_TRX_WARNING: {TRON_TRX_WARNING}, TRON_ENERGY_WARNING: {TRON_ENERGY_WARNING}, TRON_NET_WARNING: {TRON_NET_WARNING},\n"
)

def get_resource_msg_simplified(res_dict):
    return (f" 能量剩余: {res_dict['energy_remain_ratio']} (约 {res_dict['estimated_trans_with_energy_with_activation']} - {res_dict['estimated_trans_with_energy_no_activation']} 笔交易) \n"
            f" 带宽剩余: {res_dict['net_remain_ratio']} (约 {res_dict['estimated_trans_with_net']} 笔交易) \n"
            f" 备用金剩: {res_dict['balance']} TRX \n"
    )

def get_resource_msg(res_dict):
    return (f"  Tron Trx额度: {res_dict['balance']} \n"
            f"  剩余能量: {res_dict['energy_remaining_str']} \n"
            f"  能量剩余比例: {res_dict['energy_remain_ratio']} \n"
            f"  剩余带宽: {res_dict['net_remaining_str']} \n"
            f"  带宽剩余比例: {res_dict['net_remain_ratio']} \n"
            f"  剩余能量能够支持交易(地址未激活)数量: {res_dict['estimated_trans_with_energy_with_activation']} \n"
            f"  剩余能量能够支持交易(地址已激活)数量: {res_dict['estimated_trans_with_energy_no_activation']} \n"
            f"  剩余带宽能够支持交易数量: {res_dict['estimated_trans_with_net']} \n")

def check_resource_and_alert(res_fields, alert_interval):
    """
    Alert if the Tron Trx, Energy or Net is below the warning threshold.
    Only sends alerts once every 30 minutes to avoid spam.
    :param tron: The TronTrxEnergyNet object.
    """
    if not hasattr(check_resource_and_alert, "last_alert_time"):
        check_resource_and_alert.last_alert_time = 0

    current_time = time.time()
    if current_time - check_resource_and_alert.last_alert_time < alert_interval:
        return

    alert_messages = []

    if res_fields['balance_float'] < TRON_TRX_WARNING:
        alert_messages.append(
            f"⚠️ TRX余额不足! 当前USDT: {res_fields['balance_float']:.3f}, 警告阈值: {TRON_TRX_WARNING}"
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
        send_telegram_message(BOT_TOKEN, CHAT_ID_EXP, alert_text)
        check_resource_and_alert.last_alert_time = current_time
        logger.info(f"Sent alert: {alert_text}")

def query_trans_and_add_info(resource_fields):
    try:
        current_time = datetime.datetime.now()
        now_datetime = current_time.strftime('%Y-%m-%dT%H:%M:%S')
        now_datetime_bj = (current_time + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%S')
        minus_one_day_datetime = (current_time - datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
        genesis_datetime = '2025-03-04T00:00:00'
        connection = get_psql_conn()

        one_day_new_trx_count = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', None, None, None)
        one_day_new_trx_count_new_address = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', None, None, None, True)
        one_day_failure_trx_count = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', 'FAILED', None, None)
        one_day_failure_trx_count_new_address = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', 'FAILED', None, None, True)
        one_day_new_gte50_usdt_trx_count = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', None, 50000000, True)
        one_day_new_gte50_usdt_trx_count_new_address = query_trx(connection, minus_one_day_datetime, now_datetime, 'count', None, 50000000, True, True)
        all_time_trx_count = query_trx(connection, genesis_datetime, now_datetime, 'count', None, None, None)
        all_time_trx_failure_count = query_trx(connection, genesis_datetime, now_datetime, 'count', 'FAILED', None, None)
        all_time_trx_amount = format(query_trx(connection, genesis_datetime, now_datetime, 'amount', 'SUCCEED', None, None) / 1000000, ',.2f')
        one_day_gte_50_ratio = '%.1f%%' % (one_day_new_gte50_usdt_trx_count_new_address / one_day_new_trx_count * 100) if one_day_new_trx_count > 0 else 0.0
        one_day_gte_50_ratio_new_address = '%.1f%%' % (one_day_new_gte50_usdt_trx_count_new_address / one_day_new_trx_count_new_address * 100) if one_day_new_trx_count_new_address > 0 else 0.0
        one_day_trx_amount = format(query_trx(connection, minus_one_day_datetime, now_datetime, 'FAILED', 'SUCCEED', None, None) / 1000000, ',.2f')
        one_day_trx_amount_new_address = format(query_trx(connection, minus_one_day_datetime, now_datetime, 'FAILED', 'SUCCEED', None, None, True) / 1000000, ',.2f')

        all_time_third_party_trx_res = query_all_time_trx_cnt_rank(connection)
        all_time_third_party_trx_res_list = [f"   公司: {row[1]}, 交易数: {row[2]}, 交易金额: {format(float(row[3]) / 1000000, ',.2f')}\n" for row in all_time_third_party_trx_res]
        all_time_third_party_trx_res_str = "".join(all_time_third_party_trx_res_list)

        last_day_third_party_trx_res = query_last_day_trx_cnt_rank(connection)
        last_day_third_party_trx_res_list = [f"   公司: {row[1]}, 交易数: {row[2]}, 交易金额: {format(float(row[3]) / 1000000, ',.2f')}\n" for row in last_day_third_party_trx_res]
        last_day_third_party_trx_res_str = "".join(last_day_third_party_trx_res_list)

        resource_message = get_resource_msg_simplified(resource_fields)

        all_addresses_count = query_addresses(connection, 0, 10000000000)
        gte50_addresses_count = query_addresses(connection, 50, 10000000000)
        gte10_lt50_addresses_count = query_addresses(connection, 10, 50)
        gte5_lt10_addresses_count = query_addresses(connection, 5, 10)
        gte0_lt5_addresses_count = query_addresses(connection, 0, 5)
        gte50_address_ratio = '%.1f%%' % (gte50_addresses_count / all_addresses_count * 100) if all_addresses_count > 0 else 0.0
        gte10_lt50_address_ratio = '%.1f%%' % (gte10_lt50_addresses_count / all_addresses_count * 100) if all_addresses_count > 0 else 0.0
        gte5_lt10_add_ratio = '%.1f%%' % (gte5_lt10_addresses_count / all_addresses_count * 100) if all_addresses_count > 0 else 0.0
        gte0_lt5_add_ratio = '%.1f%%' % (gte0_lt5_addresses_count / all_addresses_count * 100) if all_addresses_count > 0 else 0.0

        top_qps_endpoint_data_tuple = get_top_qps_endpoint_data_tuple()
        alert_text = (f"GasFree Provider 截止 {now_datetime_bj} 数据汇总: \n"
                      f"# 整体交易数据  \n"
                      f" 天交易数: {one_day_new_trx_count} (失败:{one_day_failure_trx_count}) \n"
                      f" 天交易额: {one_day_trx_amount} (>50$: {one_day_gte_50_ratio}) \n"
                      f" 天交易数(新增地址): {one_day_new_trx_count_new_address} (失败:{one_day_failure_trx_count_new_address}) \n"
                      f" 天交易额(新增地址): {one_day_trx_amount_new_address} (>50$: {one_day_gte_50_ratio_new_address}) \n"
                      f" 总交易数: {all_time_trx_count} (失败:{all_time_trx_failure_count}) \n"
                      f" 总交易额: {all_time_trx_amount}  \n"
                      f"\n"
                      f"# 地址交易数分布  \n"
                      f" >=50  笔 地址数量: {gte50_addresses_count} 占比: {gte50_address_ratio}  \n"
                      f" 10-50 笔 地址数量: {gte10_lt50_addresses_count} 占比: {gte10_lt50_address_ratio}  \n"
                      f" 5-10  笔 地址数量: {gte5_lt10_addresses_count} 占比: {gte5_lt10_add_ratio}  \n"
                      f" 0-5   笔 地址数量: {gte0_lt5_addresses_count} 占比: {gte0_lt5_add_ratio}  \n"
                      f"\n"
                      f"# 第三方数据  \n"
                      f" 上线以来交易金额排行:  \n"
                      f"{all_time_third_party_trx_res_str}"
                      f" 过去一天交易金额排行:  \n"
                      f"{last_day_third_party_trx_res_str}"
                      f"\n"
                      f"# 资源数据: \n"
                      f"{resource_message}"
                      f"# 接口调用QPS Top1: \n"
                      f" 名称: {top_qps_endpoint_data_tuple[0]} \n"
                      f" qps: {'%.2f' % float(top_qps_endpoint_data_tuple[1])}"
                      )

        return alert_text
    finally:
        if connection:
            connection.close()
            print("PostgreSQL connection is closed")

def recur_trx_notif():
    if not hasattr(recur_trx_notif, "last_heartbeat_time"):
        recur_trx_notif.last_heartbeat_time = 0

    current_time = time.time()
    local_time = time.localtime(current_time)
    minutes = local_time.tm_min
    hours = local_time.tm_hour

    resource_fields = get_resources_fields()
    check_resource_and_alert(resource_fields, ALERT_INTERVAL)


    if minutes == 0:
        message = query_trans_and_add_info(resource_fields)
        send_telegram_message(BOT_TOKEN, CHAT_ID_INNER, message)
        recur_trx_notif.last_heartbeat_time = current_time
        logger.info(message)
    else:
        logger.info(f"cur min {minutes} and hour {hours} not match send timestamp, skipping...")

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = "以下是可用的命令:\n"
    help_text += "/help - 显示帮助信息\n"
    help_text += "/triggerHourlyStats - 触发小时级别播报数据\n"
    update.message.reply_text(help_text)

def trigger_hourly_stats_command(update: Update, context: CallbackContext) -> None:
    resource_fields = get_resources_fields()
    message = query_trans_and_add_info(resource_fields)
    update.message.reply_text(message)

def main_trx():
    application = Application.builder().token(BOT_TOKEN).build()

    # 直接在 application 上添加处理程序
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("triggerHourlyStats", trigger_hourly_stats_command))

    application.run_polling()

    while True:
        try:
            recur_trx_notif()
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"Error in main loop: {e}")
        finally:
            time.sleep(60)

if __name__ == "__main__":
    main_trx()