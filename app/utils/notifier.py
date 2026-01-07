import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import app.utils.config as config

class EmailNotifier:
    """
    负责发送邮件通知的类。
    """
    def __init__(self):
        self.enabled = config.ENABLE_EMAIL_NOTIFICATION
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.sender = config.EMAIL_SENDER
        self.password = config.EMAIL_PASSWORD
        self.recipients = config.EMAIL_RECIPIENTS

    def send_summary(self, subject, summary_content, attachment_path=None):
        """
        发送会议纪要邮件。
        
        :param subject: 邮件主题
        :param summary_content: 会议纪要内容 (Markdown 格式)
        :param attachment_path: 附件路径 (可选)
        """
        if not self.enabled:
            return
            
        if not self.recipients:
            print("⚠️ 邮件通知已开启，但收件人列表为空，跳过发送。")
            return

        if not self.sender or not self.password:
            print("❌ 邮件发送失败: 发件人或密码未配置")
            return

        print(f"📧 正在发送邮件通知给 {len(self.recipients)} 位收件人...")

        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ",".join(self.recipients)
            msg['Subject'] = subject

            # 添加正文 (使用 Markdown 内容)
            # 为了更好的显示效果，可以将 Markdown 稍微处理一下，或者直接作为纯文本发送
            body = f"会议纪要如下：\n\n{summary_content}"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 添加附件
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                    # 设置附件头
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                    msg.attach(part)

            # 连接 SMTP 服务器并发送
            # 使用 SMTP_SSL (端口 465)
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.recipients, msg.as_string())
            
            print("✅ 邮件发送成功！")

        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
