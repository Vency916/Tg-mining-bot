from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String)
    balance = Column(Float, default=0.0)
    unconfirmed = Column(Float, default=0.0)
    hash_rate = Column(Float, default=config.HASH_RATE_BASE)

engine = create_engine('sqlite:///mining_bot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_user_data(user_id):
    with Session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            user = User(id=user_id)
            session.add(user)
            session.commit()
        return {
            'balance': user.balance,
            'unconfirmed': user.unconfirmed,
            'hash_rate': user.hash_rate
        }

def update_mining_stats(user_id, amount):
    with Session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.unconfirmed += amount
            session.commit()