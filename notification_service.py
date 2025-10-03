import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from typing import Dict, List
import streamlit as st

from monitor_db import monitor_db

class NotificationService:
    """通知服务"""
    
    def __init__(self):
        # 强制重新加载环境变量
        from dotenv import load_dotenv
        load_dotenv()
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载通知配置"""
        config = {
            'email_enabled': False,
            'smtp_server': '',
            'smtp_port': 587,
            'email_from': '',
            'email_password': '',
            'email_to': '',
            'webhook_enabled': False,
            'webhook_url': ''
        }
        
        # 从环境变量加载配置
        if os.getenv('EMAIL_ENABLED'):
            config['email_enabled'] = os.getenv('EMAIL_ENABLED').lower() == 'true'
        if os.getenv('SMTP_SERVER'):
            config['smtp_server'] = os.getenv('SMTP_SERVER')
        if os.getenv('SMTP_PORT'):
            config['smtp_port'] = int(os.getenv('SMTP_PORT'))
        if os.getenv('EMAIL_FROM'):
            config['email_from'] = os.getenv('EMAIL_FROM')
        if os.getenv('EMAIL_PASSWORD'):
            config['email_password'] = os.getenv('EMAIL_PASSWORD')
        if os.getenv('EMAIL_TO'):
            config['email_to'] = os.getenv('EMAIL_TO')
        
        return config
    
    def send_notifications(self):
        """发送所有待发送的通知"""
        notifications = monitor_db.get_pending_notifications()
        
        for notification in notifications:
            try:
                if self.send_notification(notification):
                    monitor_db.mark_notification_sent(notification['id'])
                    print(f"✅ 通知已发送: {notification['message']}")
                else:
                    print(f"❌ 通知发送失败: {notification['message']}")
            except Exception as e:
                print(f"❌ 发送通知时出错: {e}")
    
    def send_notification(self, notification: Dict) -> bool:
        """发送单个通知"""
        # 优先尝试邮件通知
        if self.config['email_enabled']:
            return self._send_email_notification(notification)
        
        # 备用方案：在Streamlit界面显示
        self._show_streamlit_notification(notification)
        return True
    
    def _send_email_notification(self, notification: Dict) -> bool:
        """发送邮件通知"""
        try:
            # 检查邮件配置是否完整
            if not all([self.config['smtp_server'], self.config['email_from'], 
                       self.config['email_password'], self.config['email_to']]):
                print("邮件配置不完整，使用界面通知")
                self._show_streamlit_notification(notification)
                return True
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.config['email_from']
            msg['To'] = self.config['email_to']
            msg['Subject'] = f"股票监测提醒 - {notification['symbol']}"
            
            # 邮件正文
            body = f"""
            <h2>股票监测提醒</h2>
            <p><strong>股票代码:</strong> {notification['symbol']}</p>
            <p><strong>股票名称:</strong> {notification['name']}</p>
            <p><strong>提醒类型:</strong> {notification['type']}</p>
            <p><strong>提醒内容:</strong> {notification['message']}</p>
            <p><strong>触发时间:</strong> {notification['triggered_at']}</p>
            <hr>
            <p><em>此邮件由AI股票分析系统自动发送</em></p>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # 根据端口选择连接方式
            if self.config['smtp_port'] == 465:
                server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'], timeout=15)
            else:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=15)
                server.starttls()
            
            server.login(self.config['email_from'], self.config['email_password'])
            server.send_message(msg)
            server.quit()
            print(f"邮件发送成功: {notification['symbol']}")
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            # 邮件发送失败时，使用界面通知作为备用方案
            print("使用界面通知作为备用方案")
            self._show_streamlit_notification(notification)
            return True
    
    def _show_streamlit_notification(self, notification: Dict):
        """在Streamlit界面显示通知"""
        # 使用session_state存储通知
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        # 避免重复通知，使用symbol代替stock_id
        notification_key = f"{notification['symbol']}_{notification['type']}_{notification['triggered_at']}"
        if notification_key not in [n.get('key') for n in st.session_state.notifications]:
            st.session_state.notifications.append({
                'key': notification_key,
                'symbol': notification['symbol'],
                'name': notification['name'],
                'type': notification['type'],
                'message': notification['message'],
                'timestamp': notification['triggered_at']
            })
    
    def get_streamlit_notifications(self) -> List[Dict]:
        """获取Streamlit界面通知"""
        return st.session_state.get('notifications', [])
    
    def clear_streamlit_notifications(self):
        """清空Streamlit界面通知"""
        if 'notifications' in st.session_state:
            st.session_state.notifications = []
    
    def test_email_config(self) -> bool:
        """测试邮件配置"""
        if not self.config['email_enabled']:
            return False
        
        try:
            if self.config['smtp_port'] == 465:
                server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'], timeout=10)
            else:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=10)
                server.starttls()
            
            server.login(self.config['email_from'], self.config['email_password'])
            server.quit()
            return True
        except Exception as e:
            print(f"邮件配置测试失败: {e}")
            return False
    
    def send_test_email(self) -> tuple[bool, str]:
        """发送测试邮件"""
        try:
            # 检查邮件配置是否完整
            if not all([self.config['smtp_server'], self.config['email_from'], 
                       self.config['email_password'], self.config['email_to']]):
                return False, "邮件配置不完整，请检查.env文件中的邮件设置"
            
            # 创建测试邮件
            msg = MIMEMultipart()
            msg['From'] = self.config['email_from']
            msg['To'] = self.config['email_to']
            msg['Subject'] = "AI股票分析系统 - 邮件测试"
            
            # 邮件正文
            body = f"""
            <html>
            <body>
                <h2>邮件测试成功！</h2>
                <p>这是一封来自AI股票分析系统的测试邮件。</p>
                <p>如果您收到这封邮件，说明邮件通知功能已正常工作。</p>
                <hr>
                <p><strong>邮件配置信息：</strong></p>
                <ul>
                    <li>SMTP服务器: {self.config['smtp_server']}</li>
                    <li>SMTP端口: {self.config['smtp_port']}</li>
                    <li>发送邮箱: {self.config['email_from']}</li>
                    <li>接收邮箱: {self.config['email_to']}</li>
                </ul>
                <hr>
                <p><em>此邮件由AI股票分析系统自动发送</em></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # 根据端口选择连接方式
            if self.config['smtp_port'] == 465:
                server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'], timeout=15)
            else:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=15)
                server.starttls()
            
            server.login(self.config['email_from'], self.config['email_password'])
            server.send_message(msg)
            server.quit()
            return True, "测试邮件发送成功！请检查收件箱（包括垃圾邮件箱）。"
            
        except smtplib.SMTPAuthenticationError:
            return False, "邮箱认证失败，请检查邮箱和授权码是否正确"
        except smtplib.SMTPException as e:
            return False, f"SMTP错误: {str(e)}"
        except Exception as e:
            return False, f"发送失败: {str(e)}"
    
    def get_email_config_status(self) -> Dict:
        """获取邮件配置状态"""
        return {
            'enabled': self.config['email_enabled'],
            'smtp_server': self.config['smtp_server'] or '未配置',
            'smtp_port': self.config['smtp_port'],
            'email_from': self.config['email_from'] or '未配置',
            'email_to': self.config['email_to'] or '未配置',
            'configured': all([
                self.config['smtp_server'],
                self.config['email_from'],
                self.config['email_password'],
                self.config['email_to']
            ])
        }

# 全局通知服务实例
notification_service = NotificationService()