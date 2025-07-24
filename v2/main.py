import datetime
import os
import time
from multiprocessing import Process


from dotenv import load_dotenv, find_dotenv, set_key
from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

from db_operations import get_psql_conn, query_trx, query_addresses, query_last_day_trx_cnt_rank, \
    query_all_time_trx_cnt_rank
from metrics_operations import get_top_qps_endpoint_data_tuple, get_resources_fields
from im_operations import send_telegram_message, send_slack_message, send_slack_webhook_message

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
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_MEMBER_UIDS = os.getenv("SLACK_MEMBER_UIDS")

# tron configs
TRON_TRX_WARNING = float(os.getenv("TRON_TRX_WARNING"))
TRON_ENERGY_WARNING = float(os.getenv("TRON_ENERGY_WARNING"))
TRON_NET_WARNING = float(os.getenv("TRON_NET_WARNING"))
TRON_ENERGY_WARNING_RATIO = float(os.getenv("TRON_ENERGY_WARNING_RATIO"))
TRON_NET_WARNING_RATIO = float(os.getenv("TRON_NET_WARNING_RATIO"))
TRON_BALANCE_WARNING_RATIO = float(os.getenv("TRON_BALANCE_WARNING_RATIO"))

ALERT_INTERVAL = 600

logger.info(
    f"BOT_TOKEN: {BOT_TOKEN}, CHAT_ID: {CHAT_ID_INNER}, METRICS_URL: {METRICS_URL},\n"
    f"TRON_TRX_WARNING: {TRON_TRX_WARNING}, TRON_ENERGY_WARNING: {TRON_ENERGY_WARNING}, TRON_NET_WARNING: {TRON_NET_WARNING},\n"
)

def update_envs():
    load_dotenv()

    global TRON_TRX_WARNING,TRON_ENERGY_WARNING,TRON_NET_WARNING,TRON_ENERGY_WARNING_RATIO,TRON_NET_WARNING_RATIO,TRON_BALANCE_WARNING_RATIO
    # tron configs
    TRON_TRX_WARNING = float(os.getenv("TRON_TRX_WARNING"))
    TRON_ENERGY_WARNING = float(os.getenv("TRON_ENERGY_WARNING"))
    TRON_NET_WARNING = float(os.getenv("TRON_NET_WARNING"))
    TRON_ENERGY_WARNING_RATIO = float(os.getenv("TRON_ENERGY_WARNING_RATIO"))
    TRON_NET_WARNING_RATIO = float(os.getenv("TRON_NET_WARNING_RATIO"))
    TRON_BALANCE_WARNING_RATIO = float(os.getenv("TRON_BALANCE_WARNING_RATIO"))

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
            f"⚠️ TRX余额不足! 当前TRX: {res_fields['balance_float']:.3f}, 警告阈值: {TRON_TRX_WARNING}"
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
        send_telegram_message(BOT_TOKEN, CHAT_ID_INNER, alert_text)
        send_slack_webhook_message(SLACK_WEBHOOK_URL, alert_text, SLACK_MEMBER_UIDS)

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


    if minutes == 0 and hours == 2:
        message = query_trans_and_add_info(resource_fields)
        send_telegram_message(BOT_TOKEN, CHAT_ID_INNER, message)
        recur_trx_notif.last_heartbeat_time = current_time
        logger.info(message)
    else:
        logger.info(f"cur min {minutes} and hour {hours} not match send timestamp, skipping...")


async def alter_energy_threshold_command(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("请提供阈值参数，例如：/al_en_th 0.5 代表将能量阈值预警比例改成50%")
        return

    try:
        new_energy_warning_ratio = float(context.args[0])
        # 找到 .env 文件路径（自动查找当前目录）
        env_path = find_dotenv()
        if not env_path:
            await update.message.reply_text("错误：未找到 .env 文件")
            return

        # 更新 .env 文件中的配置（注意：set_key 会覆盖原有值，不存在则新增）
        set_key(env_path, "TRON_ENERGY_WARNING_RATIO", f"{new_energy_warning_ratio}")

        # （可选）如果需要立即生效，重新加载环境变量到全局（根据你的代码结构调整）
        load_dotenv(env_path, override=True)
        global TRON_ENERGY_WARNING_RATIO
        TRON_ENERGY_WARNING_RATIO = float(os.getenv("TRON_ENERGY_WARNING_RATIO"))  # 重新读取最新值

        await update.message.reply_text(f"能量警告比例阈值已更新为：{'%.9f%%' % (new_energy_warning_ratio * 100)}（已写入 .env 文件）")

    except ValueError:
        await update.message.reply_text("参数错误：请输入有效的数字（例如 0.5，代表50%）")
    except Exception as e:
        await update.message.reply_text(f"操作失败：{str(e)}")

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = "以下是可用的命令:\n"
    help_text += "/help - 显示帮助信息\n"
    help_text += "/st - 触发小时级别播报数据\n"
    help_text += "/rs - 获取最新能量+带宽资源信息\n"
    help_text += "/al_en_th <修改能量警告阈值> - 修改能量警告阈值，例如：/al_en_th 0.5 代表将能量阈值预警比例改成50%\n"
    await update.message.reply_text(help_text)

async def handle_get_resource_command(update: Update, context: CallbackContext) -> None:
    resource_fields = get_resources_fields()
    message = (f"资源情况\n"
                f"  剩余能量: {resource_fields['energy_remaining']}\n"
                f"  剩余能量比例: {resource_fields['energy_remain_ratio']}\n"
                f"  能量上限: {resource_fields['energy_limit']}\n"
                f"  剩余能量支持交易数(地址未激活): {resource_fields['estimated_trans_with_energy_with_activation']}\n"
                f"  剩余能量支持交易数(地址已激活): {resource_fields['estimated_trans_with_energy_no_activation']}\n"
                f"\n"
                f"  剩余带宽: {resource_fields['net_remaining']}\n"
                f"  剩余带宽比例: {resource_fields['net_remain_ratio']}\n"
                f"  带宽上限: {resource_fields['net_limit']}\n"
                f"  剩余带宽支持交易数(地址已激活): {resource_fields['estimated_trans_with_net']}\n"
                f"\n"
                f"  剩余备用金: {resource_fields['balance']} TRX \n"
                f"  剩余备用金支持交易数(地址未激活): {'%.1f' % (float(resource_fields['balance'].replace(',', '')) / 40.8)}\n"
                f"  剩余备用金支持交易数(地址已激活): {'%.1f' % (float(resource_fields['balance'].replace(',', '')) / 20.4)}")
    await update.message.reply_text(message)


async def trigger_hourly_stats_command(update: Update, context: CallbackContext) -> None:
    resource_fields = get_resources_fields()
    message = query_trans_and_add_info(resource_fields)
    await update.message.reply_text(message)


def run_bot():
    """子进程：运行 Bot 轮询"""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("st", trigger_hourly_stats_command))
    application.add_handler(CommandHandler("rs", handle_get_resource_command))
    application.add_handler(CommandHandler("al_en_th", alter_energy_threshold_command))  # 新增此行
    application.run_polling()

def run_scheduler():
    """子进程：运行定时任务"""
    while True:
        try:
            update_envs()
            recur_trx_notif()
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"Error in scheduler loop: {e}")
        finally:
            time.sleep(60)  # 控制定时任务的执行间隔

def main_trx():
    # 创建两个子进程
    bot_process = Process(target=run_bot)
    scheduler_process = Process(target=run_scheduler)

    # 启动子进程
    bot_process.start()
    scheduler_process.start()

    # 等待子进程结束（可根据需要添加键盘中断处理）
    try:
        bot_process.join()
        scheduler_process.join()
    except KeyboardInterrupt:
        logger.info("接收到键盘中断，正在停止进程...")
        bot_process.terminate()
        scheduler_process.terminate()
        bot_process.join()
        scheduler_process.join()

if __name__ == "__main__":
    main_trx()