from app.database import SessionLocal
from app.curd.notification import create_notification
from app.schemas.notification import NotificationCreate, NotificationType

def test_notif():
    db = SessionLocal()
    notif = create_notification(db, NotificationCreate(
        type=NotificationType.INFO,
        title="Test Notification",
        message="This is a test notification for user kk",
        recipient_id=30 # kk's user id
    ))
    print(f"Created Notification: {notif.id}")

if __name__ == "__main__":
    test_notif()
