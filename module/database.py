from dataclasses import dataclass
from tabulate import tabulate



@dataclass
class Airplane:
    icao: str
    climb_v1: int
    climb_v2: int
    climb_v3: float

    descent_v1: float
    descent_v2: int
    descent_v3: int
    k: float | None

    def __post__init__(self):
        self.icao = self.icao.upper()


database = {
    "B742": Airplane(
        icao="B742",
        climb_v1=250,
        climb_v2=310,
        climb_v3=0.84,
        descent_v1=0.84,
        descent_v2=310,
        descent_v3=250,
        k=0.15
    ),
    "B772": Airplane(
        icao="B772",
        climb_v1=250,
        climb_v2=310,
        climb_v3=0.84,
        descent_v1=0.84,
        descent_v2=310,
        descent_v3=250,
        k=0.12
    ),
    "B77L": Airplane(
        icao="B77L",
        climb_v1=250,
        climb_v2=310,
        climb_v3=0.84,
        descent_v1=0.84,
        descent_v2=310,
        descent_v3=250,
        k=0.10
    ),
    "B77W": Airplane(
        icao="B77W",
        climb_v1=250,
        climb_v2=310,
        climb_v3=0.84,
        descent_v1=0.84,
        descent_v2=310,
        descent_v3=250,
        k=0.10
    ),
    "B748": Airplane(
        icao="B748",
        climb_v1=250,
        climb_v2=310,
        climb_v3=0.84,
        descent_v1=0.84,
        descent_v2=310,
        descent_v3=250,
        k=0.13
    ),
    "B788": Airplane(
        icao="B788",
        climb_v1=250,
        climb_v2=310,
        climb_v3=0.84,
        descent_v1=0.84,
        descent_v2=310,
        descent_v3=250,
        k=0.12
    ),
    "B789": Airplane(
        icao="B789",
        climb_v1=250,
        climb_v2=310,
        climb_v3=0.84,
        descent_v1=0.84,
        descent_v2=310,
        descent_v3=250,
        k=0.11
    ),
    "B78X": Airplane(
        icao="B78X",
        climb_v1=250,
        climb_v2=310,
        climb_v3=0.84,
        descent_v1=0.84,
        descent_v2=310,
        descent_v3=250,
        k=0.11
    ),
    "A339": Airplane(
        icao="A339",
        climb_v1=250,
        climb_v2=300,
        climb_v3=0.80,
        descent_v1=0.85,
        descent_v2=310,
        descent_v3=250,
        k=0.24
    ),
    "A333": Airplane(
        icao="A333",
        climb_v1=250,
        climb_v2=300,
        climb_v3=0.80,
        descent_v1=0.85,
        descent_v2=310,
        descent_v3=250,
        k=0.23
    ),
    "A359": Airplane(
        icao="A359",
        climb_v1=250,
        climb_v2=320,
        climb_v3=0.85,
        descent_v1=0.85,
        descent_v2=300,
        descent_v3=250,
        k=0.25
    ),
    "A388": Airplane(
        icao="A388",
        climb_v1=250,
        climb_v2=320,
        climb_v3=0.84,
        descent_v1=0.85,
        descent_v2=300,
        descent_v3=250,
        k=0.22
    ),
    "A320": Airplane(
        icao="A320",
        climb_v1=250,
        climb_v2=300,
        climb_v3=0.78,
        descent_v1=0.78,
        descent_v2=300,
        descent_v3=250,
        k=0.20
    ),
    "A321": Airplane(
        icao="A321",
        climb_v1=250,
        climb_v2=300,
        climb_v3=0.78,
        descent_v1=0.78,
        descent_v2=300,
        descent_v3=250,
        k=0.20
    ),
    "A318": Airplane(
        icao="A318",
        climb_v1=250,
        climb_v2=300,
        climb_v3=0.78,
        descent_v1=0.78,
        descent_v2=300,
        descent_v3=250,
        k=0.18
    ),
    "A319": Airplane(
        icao="A319",
        climb_v1=250,
        climb_v2=300,
        climb_v3=0.78,
        descent_v1=0.78,
        descent_v2=300,
        descent_v3=250,
        k=0.19
    ),
    "B738": Airplane(
        icao="B738",
        climb_v1=250,
        climb_v2=300,
        climb_v3=0.78,
        descent_v1=0.78,
        descent_v2=300,
        descent_v3=250,
        k=0.18
    ),
    "B739": Airplane(
        icao="B739",
        climb_v1=250,
        climb_v2=300,
        climb_v3=0.78,
        descent_v1=0.78,
        descent_v2=300,
        descent_v3=250,
        k=0.18
    ),
    "B38M": Airplane(
        icao="B38M",
        climb_v1=250,
        climb_v2=280,
        climb_v3=0.78,
        descent_v1=0.78,
        descent_v2=280,
        descent_v3=250,
        k=0.16
    ),
    "BCS3": Airplane(
        icao="BCS3",
        climb_v1=250,
        climb_v2=280,
        climb_v3=0.75,
        descent_v1=0.75,
        descent_v2=280,
        descent_v3=250,
        k=None
    ),
    "E175": Airplane(
        icao="E175",
        climb_v1=240,
        climb_v2=290,
        climb_v3=0.70,
        descent_v1=0.77,
        descent_v2=290,
        descent_v3=250,
        k=None
    ),
}


def retrive_airplane(icao: str) -> Airplane:
    return database.get(icao, None)



def print_table(database):
    """
    Prints all rows in a given SQLAlchemy ORM table.

    Args:
        session: The SQLAlchemy session object.
        model_class: The SQLAlchemy ORM class representing the table.
    """

    data = [vars(airplane) for airplane in database.values()]
    print(tabulate(data, headers='keys'))


    # # Print column headers
    # column_names = [column.name for column in model_class.__table__.columns]
    # header = " | ".join(column_names)
    # print(header)
    # print("-" * len(header))

    # spacing = [len(i) for i in header.split("|")]

    # row_data = ([str(getattr(row, column)) for column in column_names] for row in rows)
    # # Print rows

    # for row in row_data:
    #     print("|".join(map(lambda x: f"{x:^{spacing[row.index(x)]}}", row)))

if __name__ == "__main__":
    print_table(database)
