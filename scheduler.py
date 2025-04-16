import schedule
import time
from utils.database import Session, User
import config

def process_payouts():
    session = Session()
    users = session.query(User).filter(User.unconfirmed >= config.PAYOUT_THRESHOLD).all()
    
    for user in users:
        user.balance += user.unconfirmed
        user.unconfirmed = 0
        # Here you would add actual payout logic
    
    session.commit()
    session.close()

def run_scheduler():
    # Schedule payouts every 24 hours
    schedule.every(config.PAYOUT_TIME).hours.do(process_payouts)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    run_scheduler()