#!/usr/bin/python

from malobot.plugin import Command
import pydistorm

class DisasmCommand(Command):
    names = ["disasm", "dasm"]
    help = "Disassemble hex bytes"
    def cmd(self,argv,message):
        bytes = " ".join(argv[1:])
        address = 0x401000

        rawbytes = ""
        for byte in bytes.split():
            try:
                rawbytes = rawbytes + chr(int(byte,16))
            except:
                pass
        disasm = pydistorm.Decode(address, rawbytes, pydistorm.Decode32Bits)

        ret = [""]
        for i in disasm:
            ret.append( "%08X: %s"%(i.offset, i))
        return "\n".join(ret)

