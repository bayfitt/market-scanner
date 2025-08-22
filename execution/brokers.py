"""Execution integration framework for multiple brokers"""

import asyncio
import aiohttp
import json
import hmac
import hashlib
import base64
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from utils import logger
from config import config

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled

@dataclass
class OrderResponse:
    order_id: str
    status: OrderStatus
    symbol: str
    side: OrderSide
    quantity: float
    filled_quantity: float = 0.0
    average_price: Optional[float] = None
    timestamp: datetime = None
    message: Optional[str] = None

@dataclass
class Position:
    symbol: str
    quantity: float
    average_price: float
    market_value: float
    unrealized_pnl: float
    
@dataclass
class Account:
    buying_power: float
    total_value: float
    positions: List[Position]

class BrokerInterface(ABC):
    """Abstract base class for broker integrations"""
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the broker"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> OrderResponse:
        """Place an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_account(self) -> Account:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass

class AlpacaBroker(BrokerInterface):
    """Alpaca broker integration (paper and live trading)"""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json"
        }
    
    async def authenticate(self) -> bool:
        """Test authentication"""
        try:
            async with self.session.get(
                f"{self.base_url}/v2/account",
                headers=self._get_headers()
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Alpaca authentication failed: {e}")
            return False
    
    async def place_order(self, order: Order) -> OrderResponse:
        """Place order with Alpaca"""
        try:
            payload = {
                "symbol": order.symbol,
                "side": order.side.value,
                "type": order.order_type.value,
                "qty": str(order.quantity),
                "time_in_force": order.time_in_force
            }
            
            if order.price:
                payload["limit_price"] = str(order.price)
            if order.stop_price:
                payload["stop_price"] = str(order.stop_price)
            
            async with self.session.post(
                f"{self.base_url}/v2/orders",
                headers=self._get_headers(),
                json=payload
            ) as response:
                data = await response.json()
                
                if response.status == 201:
                    return OrderResponse(
                        order_id=data["id"],
                        status=OrderStatus(data["status"].lower()),
                        symbol=data["symbol"],
                        side=OrderSide(data["side"]),
                        quantity=float(data["qty"]),
                        filled_quantity=float(data.get("filled_qty", 0)),
                        timestamp=datetime.now()
                    )
                else:
                    return OrderResponse(
                        order_id="",
                        status=OrderStatus.REJECTED,
                        symbol=order.symbol,
                        side=order.side,
                        quantity=order.quantity,
                        message=data.get("message", "Order rejected"),
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            logger.error(f"Alpaca order failed: {e}")
            return OrderResponse(
                order_id="",
                status=OrderStatus.REJECTED,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                message=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            async with self.session.delete(
                f"{self.base_url}/v2/orders/{order_id}",
                headers=self._get_headers()
            ) as response:
                return response.status == 204
        except Exception as e:
            logger.error(f"Alpaca cancel order failed: {e}")
            return False
    
    async def get_account(self) -> Account:
        """Get account information"""
        try:
            async with self.session.get(
                f"{self.base_url}/v2/account",
                headers=self._get_headers()
            ) as response:
                data = await response.json()
                
                positions = await self.get_positions()
                
                return Account(
                    buying_power=float(data["buying_power"]),
                    total_value=float(data["equity"]),
                    positions=positions
                )
        except Exception as e:
            logger.error(f"Alpaca get account failed: {e}")
            return Account(buying_power=0, total_value=0, positions=[])
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            async with self.session.get(
                f"{self.base_url}/v2/positions",
                headers=self._get_headers()
            ) as response:
                data = await response.json()
                
                positions = []
                for pos in data:
                    positions.append(Position(
                        symbol=pos["symbol"],
                        quantity=float(pos["qty"]),
                        average_price=float(pos["avg_cost"]),
                        market_value=float(pos["market_value"]),
                        unrealized_pnl=float(pos["unrealized_pl"])
                    ))
                
                return positions
        except Exception as e:
            logger.error(f"Alpaca get positions failed: {e}")
            return []

class PaperBroker(BrokerInterface):
    """Paper trading simulator"""
    
    def __init__(self, initial_balance: float = 100000.0):
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, OrderResponse] = {}
        self.order_counter = 0
    
    async def authenticate(self) -> bool:
        """Paper broker always authenticates"""
        return True
    
    async def place_order(self, order: Order) -> OrderResponse:
        """Simulate order placement"""
        self.order_counter += 1
        order_id = f"paper_{self.order_counter}"
        
        # For market orders, simulate immediate fill
        if order.order_type == OrderType.MARKET:
            # Simulate getting current market price (would need real market data)
            estimated_price = order.price or 100.0  # Placeholder
            
            cost = order.quantity * estimated_price
            
            if order.side == OrderSide.BUY:
                if cost <= self.balance:
                    self.balance -= cost
                    
                    # Update position
                    if order.symbol in self.positions:
                        pos = self.positions[order.symbol]
                        total_cost = (pos.quantity * pos.average_price) + cost
                        total_quantity = pos.quantity + order.quantity
                        new_avg_price = total_cost / total_quantity
                        
                        self.positions[order.symbol] = Position(
                            symbol=order.symbol,
                            quantity=total_quantity,
                            average_price=new_avg_price,
                            market_value=total_quantity * estimated_price,
                            unrealized_pnl=(estimated_price - new_avg_price) * total_quantity
                        )
                    else:
                        self.positions[order.symbol] = Position(
                            symbol=order.symbol,
                            quantity=order.quantity,
                            average_price=estimated_price,
                            market_value=cost,
                            unrealized_pnl=0.0
                        )
                    
                    response = OrderResponse(
                        order_id=order_id,
                        status=OrderStatus.FILLED,
                        symbol=order.symbol,
                        side=order.side,
                        quantity=order.quantity,
                        filled_quantity=order.quantity,
                        average_price=estimated_price,
                        timestamp=datetime.now()
                    )
                else:
                    response = OrderResponse(
                        order_id=order_id,
                        status=OrderStatus.REJECTED,
                        symbol=order.symbol,
                        side=order.side,
                        quantity=order.quantity,
                        message="Insufficient buying power",
                        timestamp=datetime.now()
                    )
            
            else:  # SELL
                if order.symbol in self.positions and self.positions[order.symbol].quantity >= order.quantity:
                    proceeds = order.quantity * estimated_price
                    self.balance += proceeds
                    
                    # Update position
                    pos = self.positions[order.symbol]
                    new_quantity = pos.quantity - order.quantity
                    
                    if new_quantity > 0:
                        self.positions[order.symbol] = Position(
                            symbol=order.symbol,
                            quantity=new_quantity,
                            average_price=pos.average_price,
                            market_value=new_quantity * estimated_price,
                            unrealized_pnl=(estimated_price - pos.average_price) * new_quantity
                        )
                    else:
                        del self.positions[order.symbol]
                    
                    response = OrderResponse(
                        order_id=order_id,
                        status=OrderStatus.FILLED,
                        symbol=order.symbol,
                        side=order.side,
                        quantity=order.quantity,
                        filled_quantity=order.quantity,
                        average_price=estimated_price,
                        timestamp=datetime.now()
                    )
                else:
                    response = OrderResponse(
                        order_id=order_id,
                        status=OrderStatus.REJECTED,
                        symbol=order.symbol,
                        side=order.side,
                        quantity=order.quantity,
                        message="Insufficient shares",
                        timestamp=datetime.now()
                    )
        
        else:
            # Limit orders go to pending state
            response = OrderResponse(
                order_id=order_id,
                status=OrderStatus.PENDING,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                timestamp=datetime.now()
            )
        
        self.orders[order_id] = response
        return response
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False
    
    async def get_account(self) -> Account:
        """Get account information"""
        total_value = self.balance + sum(pos.market_value for pos in self.positions.values())
        
        return Account(
            buying_power=self.balance,
            total_value=total_value,
            positions=list(self.positions.values())
        )
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        return list(self.positions.values())

class BrokerManager:
    """Manages multiple broker connections"""
    
    def __init__(self):
        self.brokers: Dict[str, BrokerInterface] = {}
        self.default_broker = "paper"
    
    def add_broker(self, name: str, broker: BrokerInterface):
        """Add a broker connection"""
        self.brokers[name] = broker
        logger.info(f"Added broker: {name}")
    
    def set_default_broker(self, name: str):
        """Set default broker for trades"""
        if name in self.brokers:
            self.default_broker = name
            logger.info(f"Default broker set to: {name}")
        else:
            raise ValueError(f"Broker {name} not found")
    
    async def place_order(self, order: Order, broker_name: Optional[str] = None) -> OrderResponse:
        """Place order with specified or default broker"""
        broker_name = broker_name or self.default_broker
        
        if broker_name not in self.brokers:
            raise ValueError(f"Broker {broker_name} not found")
        
        broker = self.brokers[broker_name]
        
        # Authenticate if needed
        if not await broker.authenticate():
            raise Exception(f"Authentication failed for broker {broker_name}")
        
        async with broker:
            return await broker.place_order(order)
    
    async def get_account(self, broker_name: Optional[str] = None) -> Account:
        """Get account info from specified or default broker"""
        broker_name = broker_name or self.default_broker
        
        if broker_name not in self.brokers:
            raise ValueError(f"Broker {broker_name} not found")
        
        broker = self.brokers[broker_name]
        async with broker:
            return await broker.get_account()

# Initialize default brokers
def create_default_broker_manager() -> BrokerManager:
    """Create broker manager with default paper trading"""
    manager = BrokerManager()
    
    # Always add paper broker
    paper_broker = PaperBroker(initial_balance=100000.0)
    manager.add_broker("paper", paper_broker)
    
    # Add Alpaca if keys are configured
    alpaca_key = config.ALPACA_KEY if hasattr(config, 'ALPACA_KEY') else None
    alpaca_secret = config.ALPACA_SECRET if hasattr(config, 'ALPACA_SECRET') else None
    
    if alpaca_key and alpaca_secret:
        # Paper trading by default
        alpaca_paper = AlpacaBroker(alpaca_key, alpaca_secret, paper=True)
        manager.add_broker("alpaca_paper", alpaca_paper)
        
        # Live trading (use with caution)
        alpaca_live = AlpacaBroker(alpaca_key, alpaca_secret, paper=False)
        manager.add_broker("alpaca_live", alpaca_live)
    
    return manager