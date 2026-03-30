"""
仓位管理模块

规则：
- 最多同时持有3只股票
- 单只最大仓位30%
- 资金不足时禁止买入
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Position:
    """持仓"""

    symbol: str
    quantity: int
    avg_cost: float
    current_price: float = 0
    stop_loss_price: float = 0
    take_profit_price: float = 0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def profit_loss(self) -> float:
        return self.quantity * (self.current_price - self.avg_cost)

    @property
    def profit_pct(self) -> float:
        if self.avg_cost == 0:
            return 0
        return (self.current_price - self.avg_cost) / self.avg_cost


class PositionManager:
    """仓位管理器"""

    def __init__(
        self,
        max_stocks: int = 3,
        max_single: float = 0.30,
        initial_capital: float = 100000,
    ):
        self.max_stocks = max_stocks
        self.max_single = max_single
        self.initial_capital = initial_capital
        self.positions: List[Position] = []
        self.cash = initial_capital

    def can_buy(self, symbol: str, price: float, quantity: int) -> dict:
        """
        检查是否可以买入

        Args:
            symbol: 股票代码
            price: 买入价格
            quantity: 买入数量

        Returns:
            检查结果
        """
        # 检查是否已持有
        existing = self.get_position(symbol)
        if existing:
            # 检查是否超过单只最大仓位
            new_value = (existing.quantity + quantity) * price
            if new_value / self.initial_capital > self.max_single:
                return {
                    "allowed": False,
                    "reason": f"超过单只最大仓位{self.max_single * 100}%",
                }

        # 检查持仓数量
        if len(self.positions) >= self.max_stocks and not existing:
            return {"allowed": False, "reason": f"已达最大持仓数量{self.max_stocks}只"}

        # 检查资金
        required = price * quantity
        if required > self.cash:
            return {
                "allowed": False,
                "reason": f"资金不足，需要{required:.2f}，可用{self.cash:.2f}",
            }

        return {"allowed": True, "reason": "可以买入"}

    def add_position(self, symbol: str, price: float, quantity: int):
        """添加持仓"""
        existing = self.get_position(symbol)

        if existing:
            # 追加买入
            total_cost = existing.avg_cost * existing.quantity + price * quantity
            total_quantity = existing.quantity + quantity
            existing.avg_cost = total_cost / total_quantity
            existing.quantity = total_quantity
        else:
            # 新建持仓
            position = Position(
                symbol=symbol, quantity=quantity, avg_cost=price, current_price=price
            )
            self.positions.append(position)

        self.cash -= price * quantity

    def remove_position(self, symbol: str, quantity: int = None) -> float:
        """
        卖出持仓

        Args:
            symbol: 股票代码
            quantity: 卖出数量，默认全部

        Returns:
            卖出金额
        """
        existing = self.get_position(symbol)
        if not existing:
            return 0

        if quantity is None or quantity >= existing.quantity:
            # 全部卖出
            sell_amount = existing.quantity * existing.current_price
            self.cash += sell_amount
            self.positions = [p for p in self.positions if p.symbol != symbol]
            return sell_amount
        else:
            # 部分卖出
            sell_amount = quantity * existing.current_price
            existing.quantity -= quantity
            self.cash += sell_amount
            return sell_amount

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        for p in self.positions:
            if p.symbol == symbol:
                return p
        return None

    def update_prices(self, prices: dict):
        """更新持仓价格"""
        for p in self.positions:
            if p.symbol in prices:
                p.current_price = prices[p.symbol]

    def get_total_value(self) -> float:
        """获取总市值"""
        return self.cash + sum(p.market_value for p in self.positions)

    def get_status(self) -> dict:
        """获取仓位状态"""
        return {
            "cash": round(self.cash, 2),
            "total_value": round(self.get_total_value(), 2),
            "position_count": len(self.positions),
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "avg_cost": round(p.avg_cost, 2),
                    "current_price": round(p.current_price, 2),
                    "market_value": round(p.market_value, 2),
                    "profit_loss": round(p.profit_loss, 2),
                    "profit_pct": round(p.profit_pct * 100, 2),
                }
                for p in self.positions
            ],
        }


if __name__ == "__main__":
    pm = PositionManager()
    print(pm.can_buy("600176.SH", 10.0, 1000))
    pm.add_position("600176.SH", 10.0, 1000)
    print(pm.get_status())
