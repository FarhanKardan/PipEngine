from datetime import datetime
from typing import Optional, Dict, Any
from logger import get_logger

class PositionTracker:
    """Tracks trading positions and manages entry/exit logic"""
    
    def __init__(self, take_profit_pips: int = 50, stop_loss_pips: int = 30):
        self.logger = get_logger("PositionTracker")
        self.take_profit_pips = take_profit_pips
        self.stop_loss_pips = stop_loss_pips
        
        # Position state
        self.current_position = 0  # 0: neutral, 1: long, -1: short
        self.entry_price = None
        self.entry_time = None
        
    def reset(self):
        """Reset position state"""
        self.current_position = 0
        self.entry_price = None
        self.entry_time = None
        
    def open_position(self, signal: int, price: float, timestamp: datetime) -> Dict[str, Any]:
        """Open a new position"""
        if signal == 0 or self.current_position != 0:
            return None
            
        self.current_position = signal
        self.entry_price = price
        self.entry_time = timestamp
        
        position_type = "LONG" if signal == 1 else "SHORT"
        tp_price = self._calculate_tp_price(signal, price)
        sl_price = self._calculate_sl_price(signal, price)
        
        return {
            'action': 'OPEN',
            'type': position_type,
            'entry_price': price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'timestamp': timestamp
        }
    
    def close_position(self, price: float, timestamp: datetime) -> Dict[str, Any]:
        """Close current position"""
        if self.current_position == 0:
            return None
            
        old_position = self.current_position
        old_entry_price = self.entry_price
        
        position_type = "LONG" if old_position == 1 else "SHORT"
        pips = self._calculate_pips(old_position, old_entry_price, price)
        
        self.reset()
        
        return {
            'action': 'CLOSE',
            'type': position_type,
            'entry_price': old_entry_price,
            'exit_price': price,
            'pips': pips,
            'timestamp': timestamp
        }
    
    def check_tp_sl(self, price: float, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Check if price hits take profit or stop loss"""
        if self.current_position == 0 or self.entry_price is None:
            return None
            
        if self.current_position == 1:  # Long position
            tp_price = self._calculate_tp_price(1, self.entry_price)
            sl_price = self._calculate_sl_price(1, self.entry_price)
            
            if price >= tp_price:
                return self._create_tp_sl_result('TAKE_PROFIT', 1, price, timestamp)
            elif price <= sl_price:
                return self._create_tp_sl_result('STOP_LOSS', 1, price, timestamp)
                
        elif self.current_position == -1:  # Short position
            tp_price = self._calculate_tp_price(-1, self.entry_price)
            sl_price = self._calculate_sl_price(-1, self.entry_price)
            
            if price <= tp_price:
                return self._create_tp_sl_result('TAKE_PROFIT', -1, price, timestamp)
            elif price >= sl_price:
                return self._create_tp_sl_result('STOP_LOSS', -1, price, timestamp)
        
        return None
    
    def _calculate_tp_price(self, signal: int, entry_price: float) -> float:
        """Calculate take profit price"""
        if signal == 1:  # Long
            return entry_price + (self.take_profit_pips * 0.1)
        else:  # Short
            return entry_price - (self.take_profit_pips * 0.1)
    
    def _calculate_sl_price(self, signal: int, entry_price: float) -> float:
        """Calculate stop loss price"""
        if signal == 1:  # Long
            return entry_price - (self.stop_loss_pips * 0.1)
        else:  # Short
            return entry_price + (self.stop_loss_pips * 0.1)
    
    def _calculate_pips(self, signal: int, entry_price: float, exit_price: float) -> float:
        """Calculate pips from entry to exit"""
        if signal == 1:  # Long
            return (exit_price - entry_price) * 10
        else:  # Short
            return (entry_price - exit_price) * 10
    
    def _create_tp_sl_result(self, action: str, signal: int, price: float, timestamp: datetime) -> Dict[str, Any]:
        """Create TP/SL result"""
        position_type = "LONG" if signal == 1 else "SHORT"
        pips = self._calculate_pips(signal, self.entry_price, price)
        
        return {
            'action': action,
            'type': position_type,
            'entry_price': self.entry_price,
            'exit_price': price,
            'pips': pips,
            'timestamp': timestamp
        }
    
    @property
    def has_position(self) -> bool:
        """Check if currently in a position"""
        return self.current_position != 0
    
    @property
    def position_type(self) -> str:
        """Get current position type"""
        if self.current_position == 1:
            return "LONG"
        elif self.current_position == -1:
            return "SHORT"
        return "NEUTRAL"
