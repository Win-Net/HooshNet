"""
Admin Roles System for HooshNet VPN Bot
Implements multi-level admin roles: Administrator, Seller, Support
Each role has specific permissions and access levels
"""

from enum import Enum
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class AdminRole(Enum):
    """Admin role levels with their permission weights"""
    NONE = 0        # Regular user
    SUPPORT = 1     # Support staff - can view tickets, respond to users
    SELLER = 2      # Seller - can sell, manage own sales, limited admin
    ADMIN = 3       # Full administrator - full access


# Permission definitions for each role
ROLE_PERMISSIONS = {
    AdminRole.NONE: [],
    
    AdminRole.SUPPORT: [
        'view_tickets',
        'reply_tickets',
        'view_users',
        'send_message_to_user',
        'view_stats_basic',
    ],
    
    AdminRole.SELLER: [
        # Inherits all SUPPORT permissions
        'view_tickets',
        'reply_tickets',
        'view_users',
        'send_message_to_user',
        'view_stats_basic',
        # Additional seller permissions
        'create_service',
        'manage_own_services',
        'add_user_balance',
        'use_discount_codes',
        'view_own_sales',
        'view_panels',
        'view_products',
    ],
    
    AdminRole.ADMIN: [
        # Full access - all permissions
        '*',  # Wildcard for all permissions
    ]
}

# Persian names for roles
ROLE_NAMES_FA = {
    AdminRole.NONE: 'کاربر عادی',
    AdminRole.SUPPORT: 'پشتیبان',
    AdminRole.SELLER: 'نماینده فروش',
    AdminRole.ADMIN: 'مدیر کل',
}

# English names for roles
ROLE_NAMES_EN = {
    AdminRole.NONE: 'User',
    AdminRole.SUPPORT: 'Support',
    AdminRole.SELLER: 'Seller',
    AdminRole.ADMIN: 'Administrator',
}

# Role emojis
ROLE_EMOJIS = {
    AdminRole.NONE: '👤',
    AdminRole.SUPPORT: '🎧',
    AdminRole.SELLER: '💼',
    AdminRole.ADMIN: '👑',
}


class AdminRolesManager:
    """Manages admin roles and permissions"""
    
    def __init__(self, db=None):
        self.db = db
    
    def set_database(self, db):
        """Set database instance"""
        self.db = db
    
    def get_user_role(self, telegram_id: int) -> AdminRole:
        """Get user's admin role"""
        if not self.db:
            return AdminRole.NONE
        
        try:
            user = self.db.get_user(telegram_id)
            if not user:
                return AdminRole.NONE
            
            # Check if user is admin
            if not user.get('is_admin', 0):
                return AdminRole.NONE
            
            # Get role from admin_role field (default to ADMIN for backward compatibility)
            role_value = user.get('admin_role', 'admin')
            
            # Convert string to AdminRole
            role_map = {
                'admin': AdminRole.ADMIN,
                'seller': AdminRole.SELLER,
                'support': AdminRole.SUPPORT,
                'none': AdminRole.NONE,
            }
            
            return role_map.get(str(role_value).lower(), AdminRole.ADMIN)
            
        except Exception as e:
            logger.error(f"Error getting user role: {e}")
            return AdminRole.NONE
    
    def set_user_role(self, telegram_id: int, role: AdminRole) -> bool:
        """Set user's admin role"""
        if not self.db:
            return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update user's role
                if role == AdminRole.NONE:
                    # Remove admin status
                    cursor.execute('''
                        UPDATE users 
                        SET is_admin = 0, admin_role = 'none'
                        WHERE telegram_id = %s
                    ''', (telegram_id,))
                else:
                    # Set admin status with role
                    role_name = role.name.lower()
                    cursor.execute('''
                        UPDATE users 
                        SET is_admin = 1, admin_role = %s
                        WHERE telegram_id = %s
                    ''', (role_name, telegram_id))
                
                conn.commit()
                
                logger.info(f"✅ Set role {role.name} for user {telegram_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting user role: {e}")
            return False
    
    def has_permission(self, telegram_id: int, permission: str) -> bool:
        """Check if user has a specific permission"""
        role = self.get_user_role(telegram_id)
        
        if role == AdminRole.NONE:
            return False
        
        permissions = ROLE_PERMISSIONS.get(role, [])
        
        # Check for wildcard (admin has all)
        if '*' in permissions:
            return True
        
        return permission in permissions
    
    def get_role_permissions(self, role: AdminRole) -> List[str]:
        """Get list of permissions for a role"""
        return ROLE_PERMISSIONS.get(role, [])
    
    def get_role_display(self, role: AdminRole, include_emoji: bool = True) -> str:
        """Get display name for a role with optional emoji"""
        name = ROLE_NAMES_FA.get(role, 'نامشخص')
        if include_emoji:
            emoji = ROLE_EMOJIS.get(role, '')
            return f"{emoji} {name}"
        return name
    
    def get_all_admins_by_role(self, role: AdminRole = None) -> List[Dict]:
        """Get all admins, optionally filtered by role"""
        if not self.db:
            return []
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                if role:
                    cursor.execute('''
                        SELECT * FROM users 
                        WHERE is_admin = 1 AND admin_role = %s
                        ORDER BY created_at DESC
                    ''', (role.name.lower(),))
                else:
                    cursor.execute('''
                        SELECT * FROM users 
                        WHERE is_admin = 1
                        ORDER BY created_at DESC
                    ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting admins by role: {e}")
            return []
    
    def can_manage_role(self, manager_telegram_id: int, target_role: AdminRole) -> bool:
        """Check if a user can assign/manage a specific role"""
        manager_role = self.get_user_role(manager_telegram_id)
        
        # Only admins can manage roles
        if manager_role != AdminRole.ADMIN:
            return False
        
        # Admins can manage all roles except other admins (optional security)
        return True
    
    def get_role_menu_items(self, telegram_id: int) -> List[Dict]:
        """Get menu items available for user's role"""
        role = self.get_user_role(telegram_id)
        
        # Base menu items for all admin roles
        menu_items = []
        
        if role in [AdminRole.SUPPORT, AdminRole.SELLER, AdminRole.ADMIN]:
            menu_items.extend([
                {'key': 'view_users', 'text': '👥 مشاهده کاربران', 'callback': 'admin:users'},
                {'key': 'view_tickets', 'text': '🎫 تیکت‌ها', 'callback': 'admin:tickets'},
            ])
        
        if role in [AdminRole.SELLER, AdminRole.ADMIN]:
            menu_items.extend([
                {'key': 'view_sales', 'text': '📊 فروش‌ها', 'callback': 'admin:sales'},
                {'key': 'add_balance', 'text': '💰 افزایش موجودی', 'callback': 'admin:add_balance'},
            ])
        
        if role == AdminRole.ADMIN:
            menu_items.extend([
                {'key': 'panels', 'text': '🖥 مدیریت پنل‌ها', 'callback': 'admin:panels'},
                {'key': 'products', 'text': '📦 مدیریت محصولات', 'callback': 'admin:products'},
                {'key': 'discounts', 'text': '🎁 کدهای تخفیف', 'callback': 'admin:discounts'},
                {'key': 'settings', 'text': '⚙️ تنظیمات', 'callback': 'admin:settings'},
                {'key': 'admins', 'text': '👑 مدیریت ادمین‌ها', 'callback': 'admin:admins'},
                {'key': 'broadcast', 'text': '📢 پیام همگانی', 'callback': 'admin:broadcast'},
                {'key': 'stats', 'text': '📈 آمار سیستم', 'callback': 'admin:stats'},
            ])
        
        return menu_items


# Global instance for easy access
admin_roles_manager = AdminRolesManager()


def get_role_emoji(role: AdminRole) -> str:
    """Get emoji for a role"""
    return ROLE_EMOJIS.get(role, '👤')


def get_role_name_fa(role: AdminRole) -> str:
    """Get Persian name for a role"""
    return ROLE_NAMES_FA.get(role, 'نامشخص')


def role_from_string(role_str: str) -> AdminRole:
    """Convert string to AdminRole enum"""
    role_map = {
        'admin': AdminRole.ADMIN,
        'administrator': AdminRole.ADMIN,
        'seller': AdminRole.SELLER,
        'support': AdminRole.SUPPORT,
        'none': AdminRole.NONE,
        'user': AdminRole.NONE,
    }
    return role_map.get(str(role_str).lower(), AdminRole.NONE)
