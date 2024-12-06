from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from re import Match, compile, escape, MULTILINE
from struct import pack, unpack
from typing import Generator
from . import time_method
from json import loads
import asyncio as aio

class IFClient:
    command_sent = 0
    sock = None
    is_connected = False
    manifest = None
    def __init__(self, ip: str, port: int) -> None:
        self.port = port
        self.ip = ip
        self.sock = socket(AF_INET, SOCK_STREAM) if self.sock is None else self.sock
        if not self.is_connected:
            self.sock.connect((self.ip, self.port))
            self.manifest = self.send_command(-1, 4)
            with open("logs/manifest.txt", "w") as f:
                f.write(self.manifest)
            self.is_connected = True

    @time_method
    def send_command(self, *args, write: bool = False, data: int = 0):
        def recv_exact(sock: socket, lenght: int) -> bytes:
            data = b''
            while len(data) < lenght:
                data += sock.recv(lenght - len(data))
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
            self.sock.send(pack('<i?', command, write))
            first_response = recv_exact(self.sock, 8)
            _, lenght = unpack("<ii", first_response)
            second_response = recv_exact(self.sock, lenght)
            
            if Type == 0:
                return unpack("<?", second_response)[0]
            elif Type == 1:
                return unpack("<i", second_response)[0]
            elif Type == 2:
                return unpack("<f", second_response)[0]
            elif Type == 3:
                return unpack("<d", second_response)[0]
            elif Type == 4:
                return unpack(f"<i{lenght-4}s", second_response)[-1].decode('utf-8')
            elif Type == 5:
                return unpack("<q", second_response)[0]
        else:
            if Type == 0:
                self.sock.send(pack("<i??", command, write, data))
            elif Type == 1:
                self.sock.send(pack("<i?i", command, write, data))
            elif Type == 2:
                self.sock.send(pack("<i?f", command, write, data))
            elif Type == 3:
                self.sock.send(pack("<i?d", command, write, data))
            elif Type == 4:
                self.sock.send(pack(f"<i?i{len(data)}s", command, write, len(data), data))
            elif Type == 5:
                self.sock.send(pack("<i?q", command, write, data))
            elif Type == -1:
                self.sock.send(pack("<i?", command, write))
            else:
                raise ValueError("Invalid datatype")

    def findfirst(self, *args: tuple[str]) -> tuple[int, int]:
        args:list[str] = list(args)
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

    def findall(self, *args: list[str])-> Generator[tuple[int, int], None, None]:
        args:list[str] = list(args)
        
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
    return aio.run(check_connection_from_file())

async def check_connection(ip, port=10112) -> str|None:
    try:
        _, writer = await aio.open_connection(ip, port)
        return ip
    except Exception:
        return None
    finally:
        try: 
            if writer:
                writer.close()
                await writer.wait_closed()
        except UnboundLocalError:
            pass

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

async def check_connection_from_file(port=10112):
    with open("logs/ip.log", "a+") as f:
        f.seek(0)
        ips = f.read().split("\n")
        ips = filter(lambda x: bool(x), ips)
        f.seek(0, 2)
        tasks = [check_connection(ip, port) for ip in ips]
        results = await aio.gather(*tasks)
        results = list(filter(lambda x: x is not None, results))
        if len(results) == 0:
            with socket(AF_INET, SOCK_DGRAM) as sock:
                server_address = ('', 15000)
                sock.bind(server_address)
                data, _ = sock.recvfrom(4096)
                if data:
                    data = loads(data.decode('utf-8'))
                    ip, port = next(filter(lambda x: x.startswith("192."), data['addresses']), None), data['port']
            f.write(f"{ip}\n")
        elif len(results) > 1:
            raise ValueError("Multiple connections")
        else:
            ip = results[0]
        return ip, port