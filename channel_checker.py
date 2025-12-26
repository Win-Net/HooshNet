"""
Channel Membership Checker
Ensures users are members of required channel before using bot features
"""

import logging
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError, BadRequest, Forbidden
from config import BOT_CONFIG
from message_templates import MessageTemplates
from channel_manager import channel_manager
from professional_database import ProfessionalDatabaseManager

logger = logging.getLogger(__name__)

# Initialize database for channel manager
db = ProfessionalDatabaseManager()
channel_manager.set_database(db)


async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_config=None) -> bool:
    """
    Check if user is member of required channels
    
    Args:
        update: Telegram update
        context: Bot context
        bot_config: Optional bot config dict (if None, uses BOT_CONFIG from config)
    
    Returns:
        bool: True if user is member or admin, False otherwise
    """
    try:
        # Get bot config
        if bot_config is None:
            from config import BOT_CONFIG
            bot_config = BOT_CONFIG
        
        user_id = update.effective_user.id
        
        # Admin bypass
        if user_id == bot_config['admin_id']:
            return True
        
        # Get required channels
        channels = channel_manager.get_required_channels()
        
        # Also check config channel for backward compatibility
        config_channel_id = bot_config.get('channel_id')
        if config_channel_id:
             # Normalize channel_id
            if isinstance(config_channel_id, str) and not config_channel_id.startswith('@') and not config_channel_id.startswith('-'):
                config_channel_id = f"@{config_channel_id}"
            
            # Check if already in DB channels to avoid duplicate check
            if not any(ch['channel_id'] == config_channel_id for ch in channels):
                channels.append({
                    'channel_id': config_channel_id,
                    'channel_name': 'کانال اصلی',
                    'channel_url': bot_config.get('channel_link', ''),
                    'is_required': True
                })
        
        if not channels:
            return True
        
        bot = context.bot
        all_joined = True
        missing_channels = []
        
        for channel in channels:
            if not channel.get('is_required', True):
                continue
                
            channel_id = channel['channel_id']
            
            try:
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                status = member.status
                
                if status not in ['member', 'administrator', 'creator', 'restricted']:
                    all_joined = False
                    missing_channels.append(channel)
                    logger.info(f"User {user_id} not in {channel_id} (status: {status})")
            except BadRequest as e:
                logger.error(f"BadRequest checking channel {channel_id}: {e}")
                # If channel not found, we can't enforce it
                continue
            except Forbidden as e:
                logger.warning(f"Bot not admin in channel {channel_id}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error checking channel {channel_id}: {e}")
                continue
        
        if not all_joined:
            # Store missing channels in context for show_force_join_message
            context.user_data['missing_channels'] = missing_channels
            return False
            
        return True
            
    except Exception as e:
        logger.error(f"Error in check_channel_membership: {e}")
        return True


async def show_force_join_message(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_config=None):
    """Show force join message with channel links"""
    if bot_config is None:
        from config import BOT_CONFIG
        bot_config = BOT_CONFIG
    
    bot_name = bot_config.get('bot_name', 'ربات')
    
    # Get missing channels from context or fetch all
    missing_channels = context.user_data.get('missing_channels')
    if not missing_channels:
        # Fallback: get all required channels
        missing_channels = channel_manager.get_required_channels()
        # Add config channel if needed
        config_channel_id = bot_config.get('channel_id')
        if config_channel_id and not any(ch['channel_id'] == config_channel_id for ch in missing_channels):
             missing_channels.append({
                'channel_id': config_channel_id,
                'channel_name': 'کانال اصلی',
                'channel_url': bot_config.get('channel_link', ''),
                'is_required': True
            })
    
    message = f"""📢 **عضویت اجباری**

برای استفاده از ربات **{bot_name}**، لطفاً در کانال‌های زیر عضو شوید:

👇 پس از عضویت، روی دکمه «✅ عضو شدم» کلیک کنید."""
    
    keyboard = []
    for channel in missing_channels:
        url = channel.get('channel_url')
        if not url:
            # Try to generate from ID if it's a username
            cid = channel['channel_id']
            if isinstance(cid, str) and cid.startswith('@'):
                url = f"https://t.me/{cid[1:]}"
            else:
                url = "https://t.me/" # Fallback
        
        name = channel.get('channel_name') or "کانال ما"
        keyboard.append([InlineKeyboardButton(f"📢 عضویت در {name}", url=url)])
    
    keyboard.append([InlineKeyboardButton("✅ عضو شدم", callback_data="check_channel_join")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Try to edit message if callback query, otherwise send new message
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await update.callback_query.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    elif update.message:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


def require_channel_membership(func):
    """
    Decorator to require channel membership before executing handler
    
    Usage:
        @require_channel_membership
        async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            ...
    """
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Check if user is member of channel
        is_member = await check_channel_membership(update, context)
        
        if not is_member:
            # Show force join message
            await show_force_join_message(update, context)
            return  # Don't execute handler
        
        # User is member, execute handler
        return await func(self, update, context, *args, **kwargs)
    
    return wrapper

