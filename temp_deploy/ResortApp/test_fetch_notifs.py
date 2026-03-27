from app.api.notification import get_unread_count
from app.database import SessionLocal

def test_fetch():
    db = SessionLocal()
    current_user = {"id": 30} # kk's user id
    # Mocking the dependency injection is tricky, let's just call the crud function directly
    from app.curd import notification as notification_crud
    count = notification_crud.get_unread_count(db, user_id=30)
    print(f"Unread count for kk: {count}")
    
    notifs = notification_crud.get_notifications(db, user_id=30)
    print(f"Total notifications for kk: {len(notifs)}")
    for n in notifs:
        print(f"- {n.title}: {n.message} (Read: {n.is_read})")

if __name__ == "__main__":
    test_fetch()
