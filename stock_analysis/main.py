"""
股票智能分析系统 - 主入口
"""

import sys
import os

# 修复Windows终端编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.collector import DataCollector
from data.storage import Database
from analysis.analyzer import StockAnalyzer
from config import SYMBOLS, PERIODS, PERIOD_CONFIG, CONCURRENCY

TASK_NAME = "stock_analysis"

# 全局预加载数据缓存
preloaded_data = {}


def analyze_symbol(
    symbol: str,
    name: str,
    period: str,
    collector: DataCollector,
    db: Database,
    task_name: str = TASK_NAME,
    preloaded: dict = None,
):
    """分析单个标的"""
    period_info = PERIOD_CONFIG.get(period, {})
    period_name = period_info.get("name", period)

    print(f"\n{'=' * 50}")
    print(f"分析 {symbol} ({name}) - {period_name}")
    print(f"{'=' * 50}")

    try:
        # 直接使用已预加载的数据（避免重复获取）
        if preloaded and symbol in preloaded and period in preloaded[symbol]:
            df = preloaded[symbol][period]
        else:
            # 如果没有预加载，则单独获取
            if period == "daily":
                df = collector.get_stock_daily(symbol, period=period)
            else:
                p = int(period.replace("min", ""))
                df = collector.get_minute(symbol, p)

        if df.empty:
            print(f"  获取数据失败，跳过")
            db.update_task_status(task_name, symbol, period, "failed")
            return

        print(f"  数据量: {len(df)}条")

        # 分析
        analyzer = StockAnalyzer(df, symbol=symbol)
        result = analyzer.analyze()
        result["period"] = period

        # 保存结果
        db.save_analysis(result)

        # 更新任务状态
        db.update_task_status(task_name, symbol, period, "completed")

        # 打印结果
        print(f"  收盘价: {result['close']}")
        print(f"  多空通道: {result['channel_signal']}")
        print(f"  九转序列: {result['seq_desc']}")
        print(f"  MACD结构: {result['macd_desc']}")
        # 缠论信息
        fenxing = result.get("fenxing", "")
        bi = result.get("bi_direction", "")
        beichi = result.get("beichi", "")
        if fenxing or bi or beichi:
            cz_info = []
            if fenxing:
                cz_info.append(f"分型:{fenxing}")
            if bi:
                cz_info.append(f"笔:{bi}")
            if beichi:
                cz_info.append(f"背驰:{beichi}")
            print(f"  缠论: {' '.join(cz_info)}")
        print(f"  综合信号: {result['signal']} (置信度: {result['confidence']}%)")

    except Exception as e:
        print(f"  错误: {e}")
        db.update_task_status(task_name, symbol, period, "failed")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="股票智能分析系统")
    parser.add_argument(
        "-p", "--period", type=str, default="daily", choices=PERIODS, help="分析周期"
    )
    parser.add_argument("-s", "--symbol", type=str, default=None, help="指定股票代码")
    parser.add_argument("-a", "--all", action="store_true", help="分析所有周期")
    parser.add_argument("-r", "--resume", action="store_true", help="从断点继续")
    parser.add_argument("--reset", action="store_true", help="重置任务重新开始")
    args = parser.parse_args()

    print("=" * 60)
    print("股票智能分析系统")
    print("=" * 60)

    collector = DataCollector()
    db = Database()

    # 获取标的列表
    all_symbols = {}
    for category, symbols in SYMBOLS.items():
        all_symbols.update(symbols)

    # 筛选标的
    if args.symbol:
        target_symbols = {args.symbol: all_symbols.get(args.symbol, args.symbol)}
    else:
        target_symbols = all_symbols

    # 分析周期
    if args.all:
        target_periods = PERIODS
    else:
        target_periods = [args.period]

    # 任务初始化
    if args.reset:
        db.clear_task(TASK_NAME)
        print(f"[任务] 已重置\n")

    if args.resume or args.symbol:
        # 继续模式或指定标的：从待处理任务开始
        pending = db.get_pending_tasks(TASK_NAME)
        if pending:
            print(f"[任务] 继续之前工作，待处理: {len(pending)} 项\n")
            task_list = pending
        else:
            # 没有待处理，初始化新任务
            db.init_task(TASK_NAME, list(target_symbols.keys()), target_periods)
            task_list = db.get_pending_tasks(TASK_NAME)
    else:
        # 正常模式：初始化新任务
        db.init_task(TASK_NAME, list(target_symbols.keys()), target_periods)
        task_list = db.get_pending_tasks(TASK_NAME)

    # 显示进度
    progress = db.get_task_progress(TASK_NAME)
    print(f"[进度] {progress['completed']}/{progress['total']} 完成\n")

    # 预加载数据（按周期分组并发获取）
    print("[数据] 预加载数据...")
    max_workers = CONCURRENCY.get("max_workers", 4)
    preloaded = {}  # {symbol: {period: df}}

    # 按周期分组批量获取
    period_groups = {}
    for task in task_list:
        symbol = task["symbol"]
        period = task["period"]
        if period not in period_groups:
            period_groups[period] = []
        period_groups[period].append(symbol)

    # 并发获取每个周期的数据
    for period, symbols in period_groups.items():
        print(f"  {period}: {len(symbols)}个标的")
        batch_results = collector.batch_get(
            symbols, period=period, max_workers=max_workers
        )
        for symbol, df in batch_results.items():
            if symbol not in preloaded:
                preloaded[symbol] = {}
            preloaded[symbol][period] = df

    print(f"[数据] 预加载完成\n")

    # 执行分析（使用预加载数据）
    for task in task_list:
        symbol = task["symbol"]
        period = task["period"]
        name = all_symbols.get(symbol, symbol)
        analyze_symbol(symbol, name, period, collector, db, TASK_NAME, preloaded)

    # 最终进度
    progress = db.get_task_progress(TASK_NAME)
    print("\n" + "=" * 60)
    print(f"分析完成! (共 {progress['completed']}/{progress['total']} 项)")
    print("=" * 60)


if __name__ == "__main__":
    main()
