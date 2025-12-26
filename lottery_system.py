"""
Lottery and Wheel of Fortune System for HooshNet VPN Bot
Implements gamified engagement features: wheel spin, lottery draws, and prize management
"""

import random
import json
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class PrizeType(Enum):
    """Types of prizes that can be won"""
    BALANCE = 'balance'           # Add balance to wallet
    DISCOUNT = 'discount'         # Discount code
    VOLUME = 'volume'             # Extra volume (GB)
    TIME = 'time'                 # Extra time (days)
    SERVICE = 'service'           # Free service
    NOTHING = 'nothing'           # No prize (empty slot)


class LotterySystem:
    """Manages lottery and wheel of fortune features"""
    
    def __init__(self, db=None):
        self.db = db
    
    def set_database(self, db):
        """Set database instance"""
        self.db = db
    
    # ==================== Wheel Configuration ====================
    
    def get_wheel_config(self) -> Dict:
        """Get wheel of fortune configuration from new tables"""
        if not self.db:
            return self._get_default_wheel_config()
        
        try:
            # Get settings
            settings = self.db.get_wheel_settings()
            
            # Get prizes
            prizes = self.db.get_prizes(active_only=True)
            
            # Convert prizes to format expected by lottery system
            formatted_prizes = []
            for p in prizes:
                formatted_prizes.append({
                    'type': p['type'],
                    'value': p['value'],
                    'weight': p['probability'],
                    'label': p['name'],
                    'color': self._get_color_for_type(p['type'])
                })
            
            # If no prizes in DB, use default
            if not formatted_prizes:
                return self._get_default_wheel_config()
                
            return {
                'enabled': settings.get('is_active', 'true').lower() == 'true',
                'spin_cost': int(settings.get('spin_cost', 0)),
                'daily_free_spins': int(settings.get('daily_limit', 1)),
                'cooldown_hours': 24, # Fixed for now or add to settings
                'prizes': formatted_prizes
            }
        except Exception as e:
            logger.error(f"Error getting wheel config: {e}")
            return self._get_default_wheel_config()
    
    def _get_color_for_type(self, type_name: str) -> str:
        """Get color for prize type"""
        colors = {
            'balance': '#4CAF50',   # Green
            'discount': '#2196F3',  # Blue
            'volume': '#9C27B0',    # Purple
            'time': '#FF9800',      # Orange
            'nothing': '#9E9E9E',   # Grey
            'empty': '#9E9E9E'      # Grey
        }
        return colors.get(type_name, '#607D8B')

    def _get_default_wheel_config(self) -> Dict:
        """Get default wheel configuration"""
        return {
            'enabled': True,
            'spin_cost': 0,  # Cost to spin (0 = free)
            'daily_free_spins': 1,  # Free spins per day
            'cooldown_hours': 24,  # Hours between free spins
            'prizes': [
                {'type': 'balance', 'value': 5000, 'weight': 20, 'label': '۵,۰۰۰ تومان', 'color': '#4CAF50'},
                {'type': 'balance', 'value': 10000, 'weight': 15, 'label': '۱۰,۰۰۰ تومان', 'color': '#2196F3'},
                {'type': 'balance', 'value': 25000, 'weight': 8, 'label': '۲۵,۰۰۰ تومان', 'color': '#9C27B0'},
                {'type': 'balance', 'value': 50000, 'weight': 3, 'label': '۵۰,۰۰۰ تومان', 'color': '#FF9800'},
                {'type': 'volume', 'value': 1, 'weight': 10, 'label': '۱ گیگابایت', 'color': '#00BCD4'},
                {'type': 'volume', 'value': 5, 'weight': 5, 'label': '۵ گیگابایت', 'color': '#E91E63'},
                {'type': 'time', 'value': 7, 'weight': 8, 'label': '۷ روز اضافی', 'color': '#795548'},
                {'type': 'discount', 'value': 10, 'weight': 12, 'label': '۱۰٪ تخفیف', 'color': '#607D8B'},
                {'type': 'discount', 'value': 20, 'weight': 6, 'label': '۲۰٪ تخفیف', 'color': '#3F51B5'},
                {'type': 'nothing', 'value': 0, 'weight': 13, 'label': 'شانس بعدی! 🍀', 'color': '#9E9E9E'},
            ]
        }
    
    # save_wheel_config is no longer needed as we use the admin panel API
    
    # ==================== Wheel Spin Logic ====================
    
    def can_spin(self, telegram_id: int) -> Tuple[bool, str]:
        """Check if user can spin the wheel"""
        if not self.db:
            return False, "خطا در اتصال به دیتابیس"
        
        config = self.get_wheel_config()
        
        if not config.get('enabled', True):
            return False, "گردونه شانس در حال حاضر غیرفعال است"
        
        # Check last spin time
        last_spin = self._get_last_spin_time(telegram_id)
        if last_spin:
            cooldown_hours = config.get('cooldown_hours', 24)
            time_since_spin = datetime.now() - last_spin
            
            if time_since_spin.total_seconds() < cooldown_hours * 3600:
                remaining = timedelta(hours=cooldown_hours) - time_since_spin
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return False, f"تا چرخش بعدی: {hours} ساعت و {minutes} دقیقه"
        
        # Check if user needs to pay
        spin_cost = config.get('spin_cost', 0)
        if spin_cost > 0:
            user_balance = self.db.get_user_balance(telegram_id) or 0
            if user_balance < spin_cost:
                return False, f"موجودی کافی نیست. هزینه چرخش: {spin_cost:,} تومان"
        
        return True, "آماده چرخش!"
    
    def spin_wheel(self, telegram_id: int) -> Tuple[bool, Dict]:
        """
        Spin the wheel and return result
        Returns: (success, result_dict)
        result_dict contains: prize_type, prize_value, prize_label, message
        """
        if not self.db:
            return False, {'message': 'خطا در اتصال به دیتابیس'}
        
        # Check if user can spin
        can_spin, reason = self.can_spin(telegram_id)
        if not can_spin:
            return False, {'message': reason}
        
        config = self.get_wheel_config()
        
        # Deduct spin cost if applicable
        spin_cost = config.get('spin_cost', 0)
        if spin_cost > 0:
            self.db.update_user_balance(telegram_id, -spin_cost, 'wheel_spin', 'Wheel of Fortune spin cost')
        
        # Select prize using weighted random
        prizes = config.get('prizes', [])
        prize = self._weighted_random_choice(prizes)
        
        # Apply prize
        result = self._apply_prize(telegram_id, prize)
        
        # Record spin
        self._record_spin(telegram_id, prize, result)
        
        return True, result
    
    def _weighted_random_choice(self, prizes: List[Dict]) -> Dict:
        """Select a prize using weighted random selection"""
        if not prizes:
            return {'type': 'nothing', 'value': 0, 'label': 'شانس بعدی!'}
        
        total_weight = sum(p.get('weight', 1) for p in prizes)
        random_num = random.uniform(0, total_weight)
        
        current_weight = 0
        for prize in prizes:
            current_weight += prize.get('weight', 1)
            if random_num <= current_weight:
                return prize
        
        return prizes[-1]  # Fallback to last prize
    
    def _apply_prize(self, telegram_id: int, prize: Dict) -> Dict:
        """Apply the won prize to user"""
        prize_type = prize.get('type', 'nothing')
        prize_value = prize.get('value', 0)
        prize_label = prize.get('label', '')
        
        result = {
            'prize_type': prize_type,
            'prize_value': prize_value,
            'prize_label': prize_label,
            'prize_color': prize.get('color', '#4CAF50'),
            'message': '',
        }
        
        try:
            if prize_type == 'balance' and prize_value > 0:
                self.db.update_user_balance(
                    telegram_id, 
                    prize_value, 
                    'wheel_prize', 
                    f'جایزه گردونه شانس: {prize_label}'
                )
                result['message'] = f"🎉 تبریک! {prize_label} به موجودی شما اضافه شد!"
                
            elif prize_type == 'volume' and prize_value > 0:
                # Store as credit to be applied on next purchase
                self._add_volume_credit(telegram_id, prize_value)
                result['message'] = f"🎉 تبریک! {prize_label} اعتبار حجم به شما افزوده شد!"
                
            elif prize_type == 'time' and prize_value > 0:
                # Store as credit to be applied on next purchase
                self._add_time_credit(telegram_id, prize_value)
                result['message'] = f"🎉 تبریک! {prize_label} اعتبار زمان به شما افزوده شد!"
                
            elif prize_type == 'discount' and prize_value > 0:
                # Create a personal discount code
                code = self._create_personal_discount(telegram_id, prize_value)
                result['message'] = f"🎉 تبریک! کد تخفیف {prize_label} برای شما: {code}"
                result['discount_code'] = code
                
            else:  # nothing or unknown
                result['message'] = "🍀 این بار شانس نیاوردی! دفعه بعد حتماً برنده می‌شی!"
                
        except Exception as e:
            logger.error(f"Error applying prize: {e}")
            result['message'] = "جایزه ثبت شد اما در اعمال آن مشکلی پیش آمد. با پشتیبانی تماس بگیرید."
        
        return result
    
    def _get_last_spin_time(self, telegram_id: int) -> Optional[datetime]:
        """Get user's last spin time"""
        if not self.db:
            return None
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT created_at FROM wheel_spins 
                    WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)
                    ORDER BY created_at DESC LIMIT 1
                ''', (telegram_id,))
                result = cursor.fetchone()
                return result['created_at'] if result else None
        except Exception as e:
            logger.error(f"Error getting last spin time: {e}")
            return None
    
    def _record_spin(self, telegram_id: int, prize: Dict, result: Dict):
        """Record a spin in the database"""
        if not self.db:
            return
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO wheel_spins (user_id, prize_type, prize_value, prize_label)
                    SELECT id, %s, %s, %s FROM users WHERE telegram_id = %s
                ''', (
                    prize.get('type', 'nothing'),
                    prize.get('value', 0),
                    prize.get('label', ''),
                    telegram_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error recording spin: {e}")
    
    def _add_volume_credit(self, telegram_id: int, gb_amount: int):
        """Add volume credit to user"""
        try:
            current = self.db.get_setting(f'user_{telegram_id}_volume_credit') or 0
            new_credit = int(current) + gb_amount
            self.db.set_setting(f'user_{telegram_id}_volume_credit', str(new_credit))
        except Exception as e:
            logger.error(f"Error adding volume credit: {e}")
    
    def _add_time_credit(self, telegram_id: int, days: int):
        """Add time credit to user"""
        try:
            current = self.db.get_setting(f'user_{telegram_id}_time_credit') or 0
            new_credit = int(current) + days
            self.db.set_setting(f'user_{telegram_id}_time_credit', str(new_credit))
        except Exception as e:
            logger.error(f"Error adding time credit: {e}")
    
    def _create_personal_discount(self, telegram_id: int, discount_percent: int) -> str:
        """Create a personal discount code for the user"""
        import string
        import secrets
        
        code = 'WHEEL' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO discount_codes 
                    (code, code_type, discount_type, discount_value, max_uses, valid_until, description)
                    VALUES (%s, 'personal', 'percentage', %s, 1, DATE_ADD(NOW(), INTERVAL 7 DAY), %s)
                ''', (code, discount_percent, f'کد تخفیف شخصی گردونه شانس برای کاربر {telegram_id}'))
                conn.commit()
            return code
        except Exception as e:
            logger.error(f"Error creating personal discount: {e}")
            return f"WHEEL{discount_percent}"
    
    # ==================== Spin History ====================
    
    def get_user_spin_history(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Get user's spin history"""
        if not self.db:
            return []
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT ws.* FROM wheel_spins ws
                    JOIN users u ON ws.user_id = u.id
                    WHERE u.telegram_id = %s
                    ORDER BY ws.created_at DESC
                    LIMIT %s
                ''', (telegram_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting spin history: {e}")
            return []
    
    def get_spin_statistics(self) -> Dict:
        """Get overall wheel statistics"""
        if not self.db:
            return {}
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                stats = {}
                
                # Total spins
                cursor.execute('SELECT COUNT(*) as count FROM wheel_spins')
                stats['total_spins'] = cursor.fetchone()['count']
                
                # Total prizes given (balance)
                cursor.execute("SELECT SUM(prize_value) as total FROM wheel_spins WHERE prize_type = 'balance'")
                stats['total_balance_given'] = cursor.fetchone()['total'] or 0
                
                # Spins today
                cursor.execute("SELECT COUNT(*) as count FROM wheel_spins WHERE DATE(created_at) = CURDATE()")
                stats['spins_today'] = cursor.fetchone()['count']
                
                # Top winners
                cursor.execute('''
                    SELECT u.telegram_id, u.username, u.first_name, SUM(ws.prize_value) as total_won
                    FROM wheel_spins ws
                    JOIN users u ON ws.user_id = u.id
                    WHERE ws.prize_type = 'balance'
                    GROUP BY u.id
                    ORDER BY total_won DESC
                    LIMIT 5
                ''')
                stats['top_winners'] = [dict(row) for row in cursor.fetchall()]
                
                return stats
        except Exception as e:
            logger.error(f"Error getting spin statistics: {e}")
            return {}


# Database migrations for lottery system
def get_lottery_migrations() -> List[Dict]:
    """Get SQL migrations for lottery system"""
    return [
        {
            'version': 'v2.0_create_wheel_spins',
            'description': 'Create wheel_spins table for wheel of fortune history',
            'sql': '''
                CREATE TABLE IF NOT EXISTS wheel_spins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    prize_type VARCHAR(50) NOT NULL,
                    prize_value INT DEFAULT 0,
                    prize_label VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        },
        {
            'version': 'v2.1_create_lottery_draws',
            'description': 'Create lottery_draws table for lottery management',
            'sql': '''
                CREATE TABLE IF NOT EXISTS lottery_draws (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    prize_type VARCHAR(50) NOT NULL,
                    prize_value INT NOT NULL,
                    ticket_price INT DEFAULT 0,
                    max_tickets INT DEFAULT 0,
                    draw_date TIMESTAMP NOT NULL,
                    winner_user_id INT,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (winner_user_id) REFERENCES users (id) ON DELETE SET NULL,
                    INDEX idx_status (status),
                    INDEX idx_draw_date (draw_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        },
        {
            'version': 'v2.2_create_lottery_tickets',
            'description': 'Create lottery_tickets table for tracking participants',
            'sql': '''
                CREATE TABLE IF NOT EXISTS lottery_tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    draw_id INT NOT NULL,
                    user_id INT NOT NULL,
                    ticket_number VARCHAR(50) NOT NULL,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (draw_id) REFERENCES lottery_draws (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    INDEX idx_draw_id (draw_id),
                    INDEX idx_user_id (user_id),
                    UNIQUE KEY unique_ticket (draw_id, ticket_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        }
    ]


# Global instance
lottery_system = LotterySystem()
