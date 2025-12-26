"""
Support Department System for HooshNet VPN Bot
Allows creating different support departments and routing tickets/messages to specific teams
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SupportDepartment:
    """Represents a support department"""
    
    def __init__(self, id: int, name: str, description: str = None, 
                 emoji: str = '🎧', admin_ids: List[int] = None, is_active: bool = True):
        self.id = id
        self.name = name
        self.description = description or ''
        self.emoji = emoji
        self.admin_ids = admin_ids or []
        self.is_active = is_active
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'emoji': self.emoji,
            'admin_ids': self.admin_ids,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SupportDepartment':
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            description=data.get('description'),
            emoji=data.get('emoji', '🎧'),
            admin_ids=data.get('admin_ids', []),
            is_active=data.get('is_active', True)
        )


class SupportDepartmentManager:
    """Manages support departments"""
    
    # Default departments
    DEFAULT_DEPARTMENTS = [
        {'name': 'پشتیبانی فنی', 'emoji': '🔧', 'description': 'مشکلات فنی و اتصال'},
        {'name': 'پشتیبانی مالی', 'emoji': '💰', 'description': 'پرداخت و صورتحساب'},
        {'name': 'پشتیبانی فروش', 'emoji': '🛒', 'description': 'خرید و تمدید سرویس'},
        {'name': 'پشتیبانی عمومی', 'emoji': '📞', 'description': 'سایر سوالات'},
    ]
    
    def __init__(self, db=None):
        self.db = db
    
    def set_database(self, db):
        """Set database instance"""
        self.db = db
    
    # ==================== Department CRUD ====================
    
    def create_department(self, name: str, description: str = None, 
                         emoji: str = '🎧', admin_ids: List[int] = None) -> Optional[int]:
        """Create a new support department"""
        if not self.db:
            return None
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO support_departments (name, description, emoji, admin_ids)
                    VALUES (%s, %s, %s, %s)
                ''', (name, description or '', emoji, ','.join(map(str, admin_ids or []))))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating department: {e}")
            return None
    
    def get_department(self, department_id: int) -> Optional[SupportDepartment]:
        """Get a department by ID"""
        if not self.db:
            return None
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT * FROM support_departments WHERE id = %s', (department_id,))
                row = cursor.fetchone()
                if row:
                    row['admin_ids'] = [int(x) for x in row.get('admin_ids', '').split(',') if x]
                    return SupportDepartment.from_dict(row)
                return None
        except Exception as e:
            logger.error(f"Error getting department: {e}")
            return None
    
    def get_all_departments(self, active_only: bool = True) -> List[SupportDepartment]:
        """Get all departments"""
        if not self.db:
            return []
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                if active_only:
                    cursor.execute('SELECT * FROM support_departments WHERE is_active = 1 ORDER BY display_order, id')
                else:
                    cursor.execute('SELECT * FROM support_departments ORDER BY display_order, id')
                
                departments = []
                for row in cursor.fetchall():
                    row['admin_ids'] = [int(x) for x in row.get('admin_ids', '').split(',') if x]
                    departments.append(SupportDepartment.from_dict(row))
                return departments
        except Exception as e:
            logger.error(f"Error getting all departments: {e}")
            return []
    
    def update_department(self, department_id: int, name: str = None, 
                         description: str = None, emoji: str = None,
                         admin_ids: List[int] = None, is_active: bool = None) -> bool:
        """Update a department"""
        if not self.db:
            return False
        
        try:
            updates = []
            values = []
            
            if name is not None:
                updates.append('name = %s')
                values.append(name)
            if description is not None:
                updates.append('description = %s')
                values.append(description)
            if emoji is not None:
                updates.append('emoji = %s')
                values.append(emoji)
            if admin_ids is not None:
                updates.append('admin_ids = %s')
                values.append(','.join(map(str, admin_ids)))
            if is_active is not None:
                updates.append('is_active = %s')
                values.append(1 if is_active else 0)
            
            if not updates:
                return True
            
            values.append(department_id)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE support_departments 
                    SET {', '.join(updates)}, updated_at = NOW()
                    WHERE id = %s
                ''', tuple(values))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating department: {e}")
            return False
    
    def delete_department(self, department_id: int) -> bool:
        """Delete a department"""
        if not self.db:
            return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM support_departments WHERE id = %s', (department_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting department: {e}")
            return False
    
    # ==================== Department Admin Management ====================
    
    def add_admin_to_department(self, department_id: int, telegram_id: int) -> bool:
        """Add an admin to a department"""
        dept = self.get_department(department_id)
        if not dept:
            return False
        
        if telegram_id not in dept.admin_ids:
            dept.admin_ids.append(telegram_id)
            return self.update_department(department_id, admin_ids=dept.admin_ids)
        return True
    
    def remove_admin_from_department(self, department_id: int, telegram_id: int) -> bool:
        """Remove an admin from a department"""
        dept = self.get_department(department_id)
        if not dept:
            return False
        
        if telegram_id in dept.admin_ids:
            dept.admin_ids.remove(telegram_id)
            return self.update_department(department_id, admin_ids=dept.admin_ids)
        return True
    
    def get_admin_departments(self, telegram_id: int) -> List[SupportDepartment]:
        """Get all departments an admin is assigned to"""
        all_depts = self.get_all_departments()
        return [d for d in all_depts if telegram_id in d.admin_ids]
    
    # ==================== Ticket Routing ====================
    
    def set_ticket_department(self, ticket_id: int, department_id: int) -> bool:
        """Assign a ticket to a department"""
        if not self.db:
            return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tickets 
                    SET department_id = %s, updated_at = NOW()
                    WHERE id = %s
                ''', (department_id, ticket_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error setting ticket department: {e}")
            return False
    
    def get_department_tickets(self, department_id: int, status: str = None) -> List[Dict]:
        """Get all tickets for a department"""
        if not self.db:
            return []
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                if status:
                    cursor.execute('''
                        SELECT t.*, u.telegram_id, u.username, u.first_name
                        FROM tickets t
                        JOIN users u ON t.user_id = u.id
                        WHERE t.department_id = %s AND t.status = %s
                        ORDER BY t.updated_at DESC
                    ''', (department_id, status))
                else:
                    cursor.execute('''
                        SELECT t.*, u.telegram_id, u.username, u.first_name
                        FROM tickets t
                        JOIN users u ON t.user_id = u.id
                        WHERE t.department_id = %s
                        ORDER BY t.updated_at DESC
                    ''', (department_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting department tickets: {e}")
            return []
    
    def get_unassigned_tickets(self) -> List[Dict]:
        """Get tickets without a department"""
        if not self.db:
            return []
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('''
                    SELECT t.*, u.telegram_id, u.username, u.first_name
                    FROM tickets t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.department_id IS NULL AND t.status = 'open'
                    ORDER BY t.created_at ASC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting unassigned tickets: {e}")
            return []
    
    # ==================== Department Statistics ====================
    
    def get_department_stats(self, department_id: int) -> Dict:
        """Get statistics for a department"""
        if not self.db:
            return {}
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                stats = {}
                
                # Total tickets
                cursor.execute('SELECT COUNT(*) as count FROM tickets WHERE department_id = %s', (department_id,))
                stats['total_tickets'] = cursor.fetchone()['count']
                
                # Open tickets
                cursor.execute("SELECT COUNT(*) as count FROM tickets WHERE department_id = %s AND status = 'open'", (department_id,))
                stats['open_tickets'] = cursor.fetchone()['count']
                
                # Closed tickets
                cursor.execute("SELECT COUNT(*) as count FROM tickets WHERE department_id = %s AND status = 'closed'", (department_id,))
                stats['closed_tickets'] = cursor.fetchone()['count']
                
                # Average response time (in hours)
                cursor.execute('''
                    SELECT AVG(TIMESTAMPDIFF(HOUR, t.created_at, 
                        (SELECT MIN(tr.created_at) FROM ticket_replies tr WHERE tr.ticket_id = t.id AND tr.is_admin_reply = 1)
                    )) as avg_hours
                    FROM tickets t
                    WHERE t.department_id = %s
                ''', (department_id,))
                result = cursor.fetchone()
                stats['avg_response_hours'] = round(result['avg_hours'] or 0, 1)
                
                return stats
        except Exception as e:
            logger.error(f"Error getting department stats: {e}")
            return {}
    
    # ==================== Initialization ====================
    
    def initialize_default_departments(self) -> bool:
        """Create default departments if none exist"""
        if not self.db:
            return False
        
        departments = self.get_all_departments(active_only=False)
        if departments:
            return True  # Already initialized
        
        for i, dept in enumerate(self.DEFAULT_DEPARTMENTS):
            self.create_department(
                name=dept['name'],
                description=dept.get('description'),
                emoji=dept.get('emoji', '🎧')
            )
        
        logger.info("✅ Initialized default support departments")
        return True


# Database migrations for support departments
def get_department_migrations() -> List[Dict]:
    """Get SQL migrations for support department system"""
    return [
        {
            'version': 'v3.0_create_support_departments',
            'description': 'Create support_departments table',
            'sql': '''
                CREATE TABLE IF NOT EXISTS support_departments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    emoji VARCHAR(10) DEFAULT '🎧',
                    admin_ids TEXT,
                    display_order INT DEFAULT 0,
                    is_active TINYINT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        },
        {
            'version': 'v3.1_add_department_to_tickets',
            'description': 'Add department_id to tickets table',
            'sql': '''
                ALTER TABLE tickets ADD COLUMN department_id INT,
                ADD FOREIGN KEY (department_id) REFERENCES support_departments (id) ON DELETE SET NULL,
                ADD INDEX idx_department_id (department_id)
            '''
        }
    ]


# Global instance
support_department_manager = SupportDepartmentManager()
