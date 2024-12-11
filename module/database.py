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
    x = [
        Airplane(icao="B742", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250, k=0.15),
        Airplane(icao="B772", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250, k=0.12),
        Airplane(icao="B77L", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250, k=0.10),
        Airplane(icao="B77W", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250, k=0.10),
        Airplane(icao="B748", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250, k=0.13),
        Airplane(icao="B788", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250, k=0.12),
        Airplane(icao="B789", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250, k=0.11),
        Airplane(icao="B78X", climb_v1=250, climb_v2=310, climb_v3=.84, descent_v1=.84, descent_v2=310, descent_v3=250, k=0.11),
        Airplane(icao="A339", climb_v1=250, climb_v2=300, climb_v3=.80, descent_v1=.85, descent_v2=310, descent_v3=250, k=0.24),
        Airplane(icao="A333", climb_v1=250, climb_v2=300, climb_v3=.80, descent_v1=.85, descent_v2=310, descent_v3=250, k=0.23),
        Airplane(icao="A359", climb_v1=250, climb_v2=320, climb_v3=.85, descent_v1=.85, descent_v2=300, descent_v3=250, k=0.25),
        Airplane(icao="A388", climb_v1=250, climb_v2=320, climb_v3=.84, descent_v1=.85, descent_v2=300, descent_v3=250, k=0.22),
        Airplane(icao="A320", climb_v1=250, climb_v2=300, climb_v3=.78, descent_v1=.78, descent_v2=300, descent_v3=250, k=0.20),
        Airplane(icao="A321", climb_v1=250, climb_v2=300, climb_v3=.78, descent_v1=.78, descent_v2=300, descent_v3=250, k=0.20),
        Airplane(icao="A318", climb_v1=250, climb_v2=300, climb_v3=.78, descent_v1=.78, descent_v2=300, descent_v3=250, k=0.18),
        Airplane(icao="A319", climb_v1=250, climb_v2=300, climb_v3=.78, descent_v1=.78, descent_v2=300, descent_v3=250, k=0.19),
        Airplane(icao="B738", climb_v1=250, climb_v2=300, climb_v3=.78, descent_v1=.78, descent_v2=300, descent_v3=250, k=0.18),
        Airplane(icao="B739", climb_v1=250, climb_v2=300, climb_v3=.78, descent_v1=.78, descent_v2=300, descent_v3=250, k=0.18),
    ]
    map(add_to_db, x)
    
    
def add_to_db(airplane: Airplane):
    existing_row = session.query(type(airplane)).filter_by(icao=airplane.icao).first()
    if existing_row:
        session.merge(airplane)
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
    rows = session.query(model_class).order_by(Airplane.icao).all()  # Fetch all rows
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
    # first_add_to_db()
    print_table(Airplane)