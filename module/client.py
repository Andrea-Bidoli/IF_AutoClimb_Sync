from __future__ import annotations
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from concurrent.futures import ThreadPoolExecutor, as_completed
from re import Match, compile, escape, MULTILINE
from struct import pack, unpack
from typing import Generator
from . import time_method

class IFClient:
    command_sent = 0
    manifest = None
    total_call_time = 0

    read_converter = {
        0: lambda x, _: unpack("<?", x)[0],
        1: lambda x, _: unpack("<i", x)[0],
        2: lambda x, _: unpack("<f", x)[0],
        3: lambda x, _: unpack("<d", x)[0],
        4: lambda x, lenght: unpack(f"<i{lenght-4}s", x)[-1].decode("utf-8"),
        5: lambda x, _: unpack("q", x)[0],
    }

    write_converter = {
        0: lambda cmd, wrt, data: pack("<i??", cmd, wrt, data),
        1: lambda cmd, wrt, data: pack("<i?i", cmd, wrt, data),
        2: lambda cmd, wrt, data: pack("<i?f", cmd, wrt, data),
        3: lambda cmd, wrt, data: pack("<i?d", cmd, wrt, data),
        4: lambda cmd, wrt, data: pack(f"<i?i{len(data)}s", cmd, wrt, len(data), data),
        5: lambda cmd, wrt, data: pack("<i?q", cmd, wrt, data),
        -1: lambda cmd, wrt, data: pack("<i?", cmd, True),
    }

    def __init__(self, ip: str, port: int) -> None:
        self.port = port
        self.ip = ip
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        self.manifest = self.send_command(-1, 4)
        with open("logs/manifest.txt", "w") as f:
            f.write(self.manifest)

    @time_method
    def send_command(self, *args, write: bool = False, data: int = 0):
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
                    command, Type = self.findfirst(*args)
            case _:
                command, Type = self.findfirst(*args)

        if not write:
            self.sock.send(pack("<i?", command, write))

            first_response = recv_exact(8)
            _, lenght = unpack("<ii", first_response)

            second_response = recv_exact(lenght)
            return self.__class__.read_converter[Type](second_response, lenght)

        else:
            byte_coomand = self.__class__.write_converter[Type](command, write, data)
            return self.sock.sendall(byte_coomand)

    def findfirst(self, *args: tuple[str]) -> tuple[int, int]:
        args: list[str] = list(args)
        if "$" in args:
            args.remove("$")
            pattern = r".*\b" + r"\b.*\b".join(map(escape, args)) + r"\b$"
        else:
            pattern = r".*\b" + r"\b.*\b".join(map(escape, args)) + r"\b.*"
        pattern = compile(pattern, MULTILINE)
        tmp: Match[str] = pattern.search(self.manifest)
        if tmp is None:
            raise ValueError(f"Command not found: {args}")
        tmp = tmp.group().split(",")[:-1]
        tmp = map(int, tmp)
        return tuple(tmp)

    def findall(self, *args: list[str]) -> Generator[tuple[int, int], None, None]:
        args: list[str] = list(args)

        if "$" in args:
            args.remove("$")
            pattern = r".*\b" + r"\b.*\b".join(map(escape, args)) + r"\b$"
        else:
            pattern = r".*\b" + r"\b.*\b".join(map(escape, args)) + r"\b.*"
        pattern = compile(pattern, MULTILINE)
        tmp = pattern.findall(self.manifest)
        return map(lambda x: tuple(map(int, x.split(",")[:-1])), tmp)

    def __del__(self):
        self.sock.close()


def retrive_ip_port():
    return check_connection_from_file(), 10112

def check_connection(ip, port=10112) -> str | None:
    with socket(AF_INET, SOCK_STREAM) as sock:
        try:
            sock.connect((ip, port))
            return ip
        except TimeoutError:
            return None
        except InterruptedError:
            return None


# async def udp_listener(ip: str='', port: int=15000) -> tuple[str, int]:
#     received = False
#     sock = await asyncudp.create_socket(local_addr=(ip, port))
#     while not received:
#         data, _ = await sock.recvfrom()
#         received = True
#         if data:
#             data = loads(data.decode('utf-8'))
#             return next(filter(lambda x: x.startswith("192."), data['addresses']), None), data['port']
#         else:
#             return '', -1


def check_connection_from_file(port=10112):
    with open("logs/ip.log", "a+") as f:
        f.seek(0)
        ips = f.read().split("\n")
        ips = filter(lambda x: bool(x), ips)
        f.seek(0, 2)

        with ThreadPoolExecutor(3) as executor:
            thread_list = [executor.submit(check_connection, ip, port) for ip in ips]
            for future in as_completed(thread_list):
                result = future.result()
                if result:
                    return result
        
        with socket(AF_INET, SOCK_DGRAM) as sock:
            sock.bind(("",15000))
            # sock.settimeout(3)
            data, _ = sock.recvfrom(1024)
            ip = compile(r"192\.\d{1,3}\.\d{1,3}\.\d{1,3}").search(data.decode("utf-8")).group()
            f.write(ip + "\n")
            return ip
        return None