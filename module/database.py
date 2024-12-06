from calendar import c
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from dataclasses import dataclass

Base = declarative_base()
engine = create_engine('sqlite:///./module/airplane.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


@dataclass
class Airplane(Base):
    __tablename__ = "Airplane"
    icao: str = Column(String, primary_key=True, nullable=False)
    climb_v1: int = Column(Integer, nullable=False)
    climb_v2: int = Column(Integer, nullable=False)
    climb_v3: float = Column(Float, nullable=False)

    descent_v1: float = Column(Float, nullable=False)
    descent_v2: int = Column(Integer, nullable=False)
    descent_v3: int = Column(Integer, nullable=False)
    k: float = Column(Float, nullable=True)
    def __post__init__(self):
        self.icao = self.icao.upper()

def retrive_airplane(icao: str) -> Airplane:
    if icao == "0xdd":
        return None
    return session.query(Airplane).filter_by(icao=icao).first()

def first_add_to_db():
    b772 = Airplane(icao="B772", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250)
    b77l = Airplane(icao="B77L", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250)
    b77w = Airplane(icao="B77W", climb_v1=250, climb_v2=310, climb_v3=.85, descent_v1=.85, descent_v2=310, descent_v3=250)
    a339 = Airplane(icao="A339", climb_v1=250, climb_v2=300, climb_v3=.80, descent_v1=.85, descent_v2=310, descent_v3=250)
    a333 = Airplane(icao="A333", climb_v1=250, climb_v2=300, climb_v3=.80, descent_v1=.85, descent_v2=310, descent_v3=250)
    b788 = Airplane(icao="B788", climb_v1=250, climb_v2=310, climb_v3=.85, descent_v1=.85, descent_v2=310, descent_v3=250)
    b789 = Airplane(icao="B789", climb_v1=250, climb_v2=310, climb_v3=.85, descent_v1=.85, descent_v2=310, descent_v3=250)
    b78x = Airplane(icao="B78X", climb_v1=250, climb_v2=310, climb_v3=.85, descent_v1=.85, descent_v2=310, descent_v3=250)
    a359 = Airplane(icao="A359", climb_v1=250, climb_v2=320, climb_v3=.85, descent_v1=.85, descent_v2=300, descent_v3=250)
    a388 = Airplane(icao="A388", climb_v1=250, climb_v2=320, climb_v3=.84, descent_v1=.85, descent_v2=300, descent_v3=250)

    session.add_all([b772, b77l, b77w, a339, a333, b788, b789, b78x, a359, a388])
    session.commit()

def add_to_db(airplane: Airplane):
    existing_row = session.query(Airplane).filter_by(icao=airplane.icao).first()
    if existing_row:
        existing_row = airplane
    else:
        session.add(airplane)
        session.commit()

def print_table(model_class):
    """
    Prints all rows in a given SQLAlchemy ORM table.

    Args:
        session: The SQLAlchemy session object.
        model_class: The SQLAlchemy ORM class representing the table.
    """
    rows = session.query(model_class).all()  # Fetch all rows
    if not rows:
        print(f"No rows found in table '{model_class.__tablename__}'.")
        return
    
    # Print column headers
    column_names = [column.name for column in model_class.__table__.columns]
    print(" | ".join(column_names))
    print("-" * (len(column_names) * 15))

    # Print rows
    for row in rows:
        row_data = [str(getattr(row, column)) for column in column_names]
        print(" | ".join(row_data))


if __name__ == "__main__":
    tmp = Airplane(icao="B739", climb_v1=250, climb_v2=280, climb_v3=.78, descent_v1=.78, descent_v2=280, descent_v3=250)
    add_to_db(tmp)
