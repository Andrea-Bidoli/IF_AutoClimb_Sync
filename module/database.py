from module import unit, Quantity
from dataclasses import dataclass, field
from tabulate import tabulate



@dataclass
class Airplane:
    icao: str
    climb_v1: Quantity
    climb_v2: Quantity
    climb_v3: Quantity

    descent_v1: Quantity
    descent_v2: Quantity
    descent_v3: Quantity

    retrive_flaps_spd: float = (200*unit.knot)
    cruise_speed: Quantity | None = field(default=None, init=False)
    k: float | None = None

    def __post__init__(self):
        self.icao = self.icao.upper()


database = {
    "B742": Airplane(
        icao="B742",
        climb_v1=250*unit.knot,
        climb_v2=340*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.84*unit.mach,
        descent_v2=340*unit.knot,
        descent_v3=250*unit.knot,
        k=0.15
    ),
    "B772": Airplane(
        icao="B772",
        climb_v1=250*unit.knot,
        climb_v2=310*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.84*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.12
    ),
    "B77L": Airplane(
        icao="B77L",
        climb_v1=250*unit.knot,
        climb_v2=310*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.84*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.10
    ),
    "B77W": Airplane(
        icao="B77W",
        climb_v1=250*unit.knot,
        climb_v2=310*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.84*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.10
    ),
    "B748": Airplane(
        icao="B748",
        climb_v1=250*unit.knot,
        climb_v2=310*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.84*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.13
    ),
    "B788": Airplane(
        icao="B788",
        climb_v1=250*unit.knot,
        climb_v2=310*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.84*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.12
    ),
    "B789": Airplane(
        icao="B789",
        climb_v1=250*unit.knot,
        climb_v2=310*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.84*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.11
    ),
    "B78X": Airplane(
        icao="B78X",
        climb_v1=250*unit.knot,
        climb_v2=310*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.84*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.11
    ),
    "A339": Airplane(
        icao="A339",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.80*unit.mach,
        descent_v1=0.85*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.24
    ),
    "A333": Airplane(
        icao="A333",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.80*unit.mach,
        descent_v1=0.85*unit.mach,
        descent_v2=310*unit.knot,
        descent_v3=250*unit.knot,
        k=0.23
    ),
    "A359": Airplane(
        icao="A359",
        climb_v1=250*unit.knot,
        climb_v2=320*unit.knot,
        climb_v3=0.85*unit.mach,
        descent_v1=0.85*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.25
    ),
    "A388": Airplane(
        icao="A388",
        climb_v1=250*unit.knot,
        climb_v2=320*unit.knot,
        climb_v3=0.84*unit.mach,
        descent_v1=0.85*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.22
    ),
    "A320": Airplane(
        icao="A320",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.78*unit.mach,
        descent_v1=0.78*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.20
    ),
    "A321": Airplane(
        icao="A321",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.78*unit.mach,
        descent_v1=0.78*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.20
    ),
    "A318": Airplane(
        icao="A318",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.78*unit.mach,
        descent_v1=0.78*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.18
    ),
    "A319": Airplane(
        icao="A319",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.78*unit.mach,
        descent_v1=0.78*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.19
    ),
    "B738": Airplane(
        icao="B738",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.78*unit.mach,
        descent_v1=0.78*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.18
    ),
    "B739": Airplane(
        icao="B739",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.78*unit.mach,
        descent_v1=0.78*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.18
    ),
    "B38M": Airplane(
        icao="B38M",
        climb_v1=250*unit.knot,
        climb_v2=280*unit.knot,
        climb_v3=0.78*unit.mach,
        descent_v1=0.78*unit.mach,
        descent_v2=280*unit.knot,
        descent_v3=250*unit.knot,
        k=0.16
    ),
    "BCS3": Airplane(
        icao="BCS3",
        climb_v1=250*unit.knot,
        climb_v2=280*unit.knot,
        climb_v3=0.75*unit.mach,
        descent_v1=0.75*unit.mach,
        descent_v2=280*unit.knot,
        descent_v3=250*unit.knot,
        k=None
    ),
    "E175": Airplane(
        icao="E175",
        climb_v1=240*unit.knot,
        climb_v2=290*unit.knot,
        climb_v3=0.70*unit.mach,
        descent_v1=0.77*unit.mach,
        descent_v2=290*unit.knot,
        descent_v3=250*unit.knot,
        k=None
    ),
    "MD11": Airplane(
        icao="MD11",
        climb_v1=250*unit.knot,
        climb_v2=330*unit.knot,
        climb_v3=0.82*unit.mach,
        descent_v1=0.82*unit.mach,
        descent_v2=330*unit.knot,
        descent_v3=250*unit.knot,
        k=0.4
    ),
    "DC10F": Airplane(
        icao="DC10F",
        climb_v1=250*unit.knot,
        climb_v2=300*unit.knot,
        climb_v3=0.82*unit.mach,
        descent_v1=0.82*unit.mach,
        descent_v2=300*unit.knot,
        descent_v3=250*unit.knot,
        k=0.4
    ),
}


def retrive_airplane(icao: str) -> Airplane:
    return database.get(icao, Airplane(None, None, None, None, None, None, None))

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
