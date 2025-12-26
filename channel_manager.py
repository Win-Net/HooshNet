"""
Multi-Channel Force Join Manager for HooshNet VPN Bot
Manages multiple required channels for user membership
"""

import logging
from typing import Optional, Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class ChannelManager:
    """Manages multiple required channels for force join"""
    
    def __init__(self, db=None):
        self.db = db
    
    def set_database(self, db):
        """Set database instance"""
        self.db = db
    
    # ==================== Channel CRUD ====================
    
    def add_channel(self, channel_id: str, channel_name: str, 
                    channel_url: str = None, is_required: bool = True) -> Optional[int]:
        """Add a new required channel"""
        if not self.db:
            return None
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO required_channels (channel_id, channel_name, channel_url, is_required)
                    VALUES (%s, %s, %s, %s)
                ''', (channel_id, channel_name, channel_url or '', 1 if is_required else 0))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding channel: {e}")
            return None
    
    def get_channel(self, id: int) -> Optional[Dict]:
        """Get a channel by ID"""
        if not self.db:
            return None
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT * FROM required_channels WHERE id = %s', (id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting channel: {e}")
            return None
    
    def get_all_channels(self, required_only: bool = True) -> List[Dict]:
        """Get all channels"""
        if not self.db:
            return []
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                if required_only:
                    cursor.execute('SELECT * FROM required_channels WHERE is_required = 1 ORDER BY display_order, id')
                else:
                    cursor.execute('SELECT * FROM required_channels ORDER BY display_order, id')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all channels: {e}")
            return []

    def get_required_channels(self) -> List[Dict]:
        """Get all required channels (alias for get_all_channels(required_only=True))"""
        return self.get_all_channels(required_only=True)
    
    def update_channel(self, id: int, channel_name: str = None,
                       channel_url: str = None, is_required: bool = None) -> bool:
        """Update a channel"""
        if not self.db:
            return False
        
        try:
            updates = []
            values = []
            
            if channel_name is not None:
                updates.append('channel_name = %s')
                values.append(channel_name)
            if channel_url is not None:
                updates.append('channel_url = %s')
                values.append(channel_url)
            if is_required is not None:
                updates.append('is_required = %s')
                values.append(1 if is_required else 0)
            
            if not updates:
                return True
            
            values.append(id)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE required_channels 
                    SET {', '.join(updates)}, updated_at = NOW()
                    WHERE id = %s
                ''', tuple(values))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating channel: {e}")
            return False
    
    def delete_channel(self, id: int) -> bool:
        """Delete a channel"""
        if not self.db:
            return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM required_channels WHERE id = %s', (id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting channel: {e}")
            return False
    
    # ==================== Membership Check ====================
    
    async def check_all_memberships(self, bot, user_id: int) -> Dict:
        """
        Check if user is member of all required channels
        
        Returns:
            Dict with 'all_joined': bool and 'missing_channels': List[Dict]
        """
        channels = self.get_all_channels(required_only=True)
        
        if not channels:
            return {'all_joined': True, 'missing_channels': []}
        
        missing = []
        
        for channel in channels:
            channel_id = channel.get('channel_id', '')
            
            try:
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    missing.append(channel)
            except Exception as e:
                logger.warning(f"Could not check membership for channel {channel_id}: {e}")
                # Assume not member if check fails
                missing.append(channel)
        
        return {
            'all_joined': len(missing) == 0,
            'missing_channels': missing
        }
    
    def create_force_join_keyboard(self, missing_channels: List[Dict]) -> InlineKeyboardMarkup:
        """Create keyboard with buttons for missing channels"""
        buttons = []
        
        for channel in missing_channels:
            name = channel.get('channel_name', 'کانال')
            url = channel.get('channel_url', '')
            
            if url:
                buttons.append([
                    InlineKeyboardButton(f"📢 {name}", url=url)
                ])
        
        # Add check button
        buttons.append([
            InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    def create_force_join_message(self, missing_channels: List[Dict]) -> str:
        """Create force join message"""
        message = "🔸 **عضویت در کانال‌های اجباری**\n\n"
        message += "برای استفاده از ربات، لطفاً در کانال‌های زیر عضو شوید:\n\n"
        
        for i, channel in enumerate(missing_channels, 1):
            name = channel.get('channel_name', 'کانال')
            message += f"{i}. 📢 {name}\n"
        
        message += "\n✅ پس از عضویت، دکمه «عضو شدم» را بزنید."
        
        return message


# Database migration for multi-channel
def get_channel_migrations() -> List[Dict]:
    """Get SQL migrations for channel system"""
    return [
        {
            'version': 'v5.0_create_required_channels',
            'description': 'Create required_channels table for multi-channel force join',
            'sql': '''
                CREATE TABLE IF NOT EXISTS required_channels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    channel_id VARCHAR(100) NOT NULL,
                    channel_name VARCHAR(255) NOT NULL,
                    channel_url TEXT,
                    display_order INT DEFAULT 0,
                    is_required TINYINT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_channel_id (channel_id),
                    INDEX idx_is_required (is_required)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        }
    ]


# Global instance
channel_manager = ChannelManager()
