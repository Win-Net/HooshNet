"""
Service Renewal Methods for HooshNet VPN Bot
Implements 5 different renewal algorithms as found in mirza_pro
"""

from enum import Enum
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RenewalMethod(Enum):
    """5 different renewal methods"""
    FULL_RESET = 1           # ریست کامل حجم و زمان
    ADD_TO_REMAINING = 2     # اضافه به باقیمانده
    RESET_TIME_KEEP_DATA = 3 # ریست زمان + حفظ حجم
    RESET_DATA_ADD_TIME = 4  # ریست حجم + اضافه زمان
    NEW_PLUS_REMAINING = 5   # حجم جدید + باقیمانده قبلی


RENEWAL_METHOD_NAMES = {
    RenewalMethod.FULL_RESET: '🔄 ریست کامل (حجم و زمان از صفر)',
    RenewalMethod.ADD_TO_REMAINING: '➕ اضافه به باقیمانده',
    RenewalMethod.RESET_TIME_KEEP_DATA: '⏰ ریست زمان + حفظ حجم باقیمانده',
    RenewalMethod.RESET_DATA_ADD_TIME: '📊 ریست حجم + اضافه زمان',
    RenewalMethod.NEW_PLUS_REMAINING: '📦 حجم جدید + باقیمانده قبلی',
}


class RenewalCalculator:
    """
    Calculates renewal parameters based on method and current service state
    """
    
    @staticmethod
    def calculate_renewal(method: RenewalMethod, 
                          current_data_remaining_gb: float,
                          current_time_remaining_days: int,
                          new_data_gb: float,
                          new_duration_days: int) -> Dict:
        """
        Calculate final renewal values based on method
        
        Args:
            method: RenewalMethod enum
            current_data_remaining_gb: Remaining data in GB
            current_time_remaining_days: Remaining days (can be negative if expired)
            new_data_gb: New package data in GB
            new_duration_days: New package duration in days
            
        Returns:
            Dict with 'final_data_gb', 'final_duration_days', 'description'
        """
        # Ensure non-negative values for remaining
        data_remaining = max(0, current_data_remaining_gb)
        time_remaining = max(0, current_time_remaining_days)
        
        if method == RenewalMethod.FULL_RESET:
            # Complete reset - start fresh
            return {
                'final_data_gb': new_data_gb,
                'final_duration_days': new_duration_days,
                'reset_used': True,
                'description': f'ریست کامل به {new_data_gb} گیگ و {new_duration_days} روز'
            }
        
        elif method == RenewalMethod.ADD_TO_REMAINING:
            # Add new to remaining
            return {
                'final_data_gb': data_remaining + new_data_gb,
                'final_duration_days': time_remaining + new_duration_days,
                'reset_used': False,
                'description': f'اضافه به باقیمانده: {data_remaining + new_data_gb:.1f} گیگ و {time_remaining + new_duration_days} روز'
            }
        
        elif method == RenewalMethod.RESET_TIME_KEEP_DATA:
            # Reset time, keep remaining data + new data
            return {
                'final_data_gb': data_remaining + new_data_gb,
                'final_duration_days': new_duration_days,
                'reset_used': False,
                'description': f'حجم {data_remaining + new_data_gb:.1f} گیگ، زمان {new_duration_days} روز (ریست)'
            }
        
        elif method == RenewalMethod.RESET_DATA_ADD_TIME:
            # Reset data to new, add time
            return {
                'final_data_gb': new_data_gb,
                'final_duration_days': time_remaining + new_duration_days,
                'reset_used': True,
                'description': f'حجم {new_data_gb} گیگ (ریست)، زمان {time_remaining + new_duration_days} روز'
            }
        
        elif method == RenewalMethod.NEW_PLUS_REMAINING:
            # New data + remaining data, new time
            return {
                'final_data_gb': new_data_gb + data_remaining,
                'final_duration_days': new_duration_days,
                'reset_used': False,
                'description': f'حجم جدید + باقیمانده = {new_data_gb + data_remaining:.1f} گیگ، {new_duration_days} روز'
            }
        
        else:
            # Default to full reset
            return {
                'final_data_gb': new_data_gb,
                'final_duration_days': new_duration_days,
                'reset_used': True,
                'description': f'ریست پیش‌فرض به {new_data_gb} گیگ و {new_duration_days} روز'
            }
    
    @staticmethod
    def get_method_name(method: RenewalMethod) -> str:
        """Get Persian name for a renewal method"""
        return RENEWAL_METHOD_NAMES.get(method, 'نامشخص')
    
    @staticmethod
    def get_all_methods() -> list:
        """Get list of all renewal methods"""
        return list(RenewalMethod)
    
    @staticmethod
    def method_from_value(value: int) -> RenewalMethod:
        """Convert integer to RenewalMethod"""
        try:
            return RenewalMethod(value)
        except ValueError:
            return RenewalMethod.FULL_RESET
    
    @staticmethod
    def calculate_expiry_date(duration_days: int, from_date: datetime = None) -> datetime:
        """Calculate expiry date from duration"""
        base = from_date or datetime.now()
        return base + timedelta(days=duration_days)
    
    @staticmethod
    def get_remaining_days(expires_at: datetime) -> int:
        """Get remaining days from expiry date"""
        if not expires_at:
            return 0
        remaining = expires_at - datetime.now()
        return max(0, remaining.days)
    
    @staticmethod
    def format_renewal_summary(method: RenewalMethod, result: Dict) -> str:
        """Format a renewal summary for display"""
        method_name = RenewalCalculator.get_method_name(method)
        return f"""
📦 **خلاصه تمدید:**
• روش: {method_name}
• حجم نهایی: {result['final_data_gb']:.1f} گیگابایت
• مدت نهایی: {result['final_duration_days']} روز
• {result['description']}
""".strip()


# Global calculator instance
renewal_calculator = RenewalCalculator()
