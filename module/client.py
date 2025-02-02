from socket import socket, AF_INET, SOCK_STREAM
from functools import wraps
from socket import error as socket_error
from re import Match, compile, escape, MULTILINE
from struct import pack, unpack
from typing import Generator, Callable
from .utils import time_method
from .logger import logger, debug_logger

from json import loads
import asyncio as aio
import asyncudp


type return_type = int | float | str | bool | None

class Node:
    def __init__(self, name):
        self.name: str = name
        self.children: dict[str, Node] = {}
        self.data = None

    def insert(self, path_parts: list|tuple|str, data=None):
        """Inserts a path into the tree using a dictionary for fast lookups."""
        if isinstance(path_parts, str):
            path_parts = path_parts.split()

        node = self
        for part in path_parts:
            if part not in node.children:
                node.children[part] = Node(part)
            node = node.children[part]
        if data:
            try:
                node.data = tuple(map(int, data))
            except ValueError:
                node.data = tuple(data)

    def search(self, path_parts: list, current_depth=0) -> "Node"|None:
        """Searches for a node, allowing partial path matching."""
        if not path_parts:
            return self
        
        first = path_parts[0]

        # Exact match in current node's children
        if first in self.children:
            return self.children[first].search(path_parts[1:], current_depth + 1)

        # If searching a subpath, do DFS search for partial matches
        for child in self.children.values():
            found = child.search(path_parts, current_depth + 1)
            if found:
                return found

        return None

    def __repr__(self, level=0, prefix="") -> str:
        """Pretty prints the tree structure using dynamically generated Unicode characters."""
        lines = []
        
        # Unicode characters using chr()
        branch_symbol = chr(0x251C) + chr(0x2500) + chr(0x2500)  # ├──
        last_branch_symbol = chr(0x2514) + chr(0x2500) + chr(0x2500)  # └──
        vertical_pipe = chr(0x2502)  # │
        space = "   "

        # Root node
        if level == 0:
            lines.append(f"{self.name}")

        # Children nodes
        for idx, (child_name, child) in enumerate(self.children.items()):
            is_last = idx == len(self.children) - 1
            connector = last_branch_symbol if is_last else branch_symbol
            new_prefix = prefix + (space if is_last else vertical_pipe + "  ")
            lines.append(f"{prefix}{connector} {child.name}")
            lines.extend(child.__repr__(level + 1, new_prefix).split("\n"))

        return "\n".join(lines)

def build_tree(paths:str) -> Node:
    root = Node("root")
    for path in paths.strip().split("\n"):
        *data, path = path.split(",")
        root.insert(path.split("/"), data)
    return root




def reconnect(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        tries = 0
        max_tries = 10
        while tries <= max_tries:
            try:
                return func(self, *args, **kwargs)
            except (socket_error, ConnectionError) as e:
                debug_logger.error(f"{e}")
                self.__init__(self.ip, self.port)
                tries += 1
        debug_logger.error(f"Connection failed after {tries} consecutive tries, exiting...")
        raise e
    return wrapper

class IFClient:
    # _instance = None
    command_sent = 0
    manifest = None
    total_call_time = 0
    tries = 0

    read_converter: dict[int, Callable[[bytes, int], return_type]] = {
        0: lambda x, _: unpack("<?", x)[0],
        1: lambda x, _: unpack("<i", x)[0],
        2: lambda x, _: unpack("<f", x)[0],
        3: lambda x, _: unpack("<d", x)[0],
        4: lambda x, lenght: unpack(f"<i{lenght-4}s", x)[-1].decode("utf-8"),
        5: lambda x, _: unpack("q", x)[0],
    }

    write_converter: dict[int, Callable[[int, bool, return_type], bytes]] = {
        0: lambda cmd, wrt, data: pack("<i??", cmd, wrt, data),
        1: lambda cmd, wrt, data: pack("<i?i", cmd, wrt, data),
        2: lambda cmd, wrt, data: pack("<i?f", cmd, wrt, data),
        3: lambda cmd, wrt, data: pack("<i?d", cmd, wrt, data),
        4: lambda cmd, wrt, data: pack(f"<i?i{len(data)}s", cmd, wrt, len(data), data),
        5: lambda cmd, wrt, data: pack("<i?q", cmd, wrt, data),
        -1: lambda cmd, wrt, data: pack("<i?", cmd, False),
    }
    
    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #     return cls._instance

    def __init__(self, ip: str, port: int) -> None:
        self.port = port
        self.ip = ip
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        self.manifest = build_tree(self.send_command(-1, 4))
        with open("logs/manifest.txt", "w") as f:
            f.write(self.manifest)

    @reconnect
    @time_method
    def send_command(self, *args, write: bool = False, data: return_type = None) -> return_type:
        def recv_exact(lenght: int) -> bytes:
            data = b""
            while len(data) < lenght:
                data += self.sock.recv(lenght - len(data))
            return data

        IFClient.command_sent += 1
        match args:
            case (cmd, tp):
                if isinstance(cmd, int) and isinstance(tp, int):
                    command, Type = cmd, tp
                else:
                    finded = self.manifest.search(args)
                    if finded is None:
                        raise ValueError(f"Command not found: {args}")
                    elif finded.value is not None:
                        command, Type = finded.value
            case _:
                finded = self.manifest.search(args)
                if finded is None:
                    raise ValueError(f"Command not found: {args}")
                elif finded.value is not None:
                    command, Type = finded.value

        if not write:
            self.sock.send(pack("<i?", command, write))

            first_response = recv_exact(8)
            _, lenght = unpack("<ii", first_response)

            second_response = recv_exact(lenght)
            return self.__class__.read_converter.get(Type)(second_response, lenght)

        else:
            byte_coomand = self.__class__.write_converter.get(Type)(command, write, data)
            return self.sock.sendall(byte_coomand)

    # def findfirst(self, *args: tuple[str]) -> tuple[int, int]:
    #     args: list[str] = list(args)
    #     if "$" in args:
    #         args.remove("$")
    #         pattern = r".*\b" + r"\b.*\b".join(map(escape, args)) + r"\b$"
    #     else:
    #         pattern = r".*\b" + r"\b.*\b".join(map(escape, args)) + r"\b.*"
    #     pattern = compile(pattern, MULTILINE)
    #     tmp: Match[str] = pattern.search(self.manifest)
    #     if tmp is None:
    #         raise ValueError(f"Command not found: {args}")
    #     tmp = tmp.group().split(",")[:-1]
    #     try:
    #         tmp = map(int, tmp)
    #     except ValueError:
    #         tmp = (tmp[0], 4)            

    #     return tuple(tmp)

    # def findall(self, *args: list[str]) -> Generator[tuple[int, int], None, None]:
    #     args: list[str] = list(args)

    #     if "$" in args:
    #         args.remove("$")
    #         pattern = r".*\b" + r"\b.*\b".join(map(escape, args)) + r"\b$"
    #     else:
    #         pattern = r".*\b" + r"\b.*\b".join(map(escape, args)) + r"\b.*"
    #     pattern = compile(pattern, MULTILINE)
    #     tmp = pattern.findall(self.manifest)
    #     return map(lambda x: tuple(map(int, x.split(",")[:-1])), tmp)

    def __del__(self):
        self.sock.close()


def retrive_ip_port():
    logger.info("Retriving IP and port...")
    result = aio.run(udp_listener(), debug=True)
    return result

async def udp_listener(ip: str='0.0.0.0', port: int=15000) -> tuple[str, int]:
    received = False
    sock = await asyncudp.create_socket(local_addr=(ip, port))
    try:
        while not received:
            data, _ = await sock.recvfrom()
            received = True
            if data:
                data = loads(data.decode('utf-8'))
                return next(filter(lambda x: x.startswith("192."), data['addresses']), None), data['port']
            else:
                return '', -1
    finally:
        sock.close()
