import re
from collections import defaultdict, namedtuple
import xml.etree.cElementTree as ET
from zynq_regs import load_registers
import sys

registers_by_uniqueid = load_registers()
registers = defaultdict(list)

for register in registers_by_uniqueid.values():
    registers[register.addr].append(register)

cmds = defaultdict(list)

cmd_maskwrite = namedtuple("MaskWrite", "addr mask value")
cmd_maskdelay = namedtuple("MaskDelay", "addr delay")
cmd_maskpoll = namedtuple("MaskPoll", "addr mask")
cmd_write = namedtuple("Write", "addr value")
cmd_exit = namedtuple("Exit", "")


def get_args(string):
    return [int(arg.strip().replace("U", ""), 16) for arg in re.search(r".*\((.*)\)", string).group(1).split(",") if arg != ""]

with open(sys.argv[1]) as f:
    in_group = False

    for line in f:
        if line.strip() == '};':
            in_group = False

        if in_group:
            line = line.strip()

            if not line.startswith('//'):
                if not line == "":
                    cmd = None
                    if line.startswith("EMIT_MASKWRITE"):
                        cmd = cmd_maskwrite
                    elif line.startswith("EMIT_MASKDELAY"):
                        cmd = cmd_maskdelay
                    elif line.startswith("EMIT_MASKPOLL"):
                        cmd = cmd_maskpoll
                    elif line.startswith("EMIT_WRITE"):
                        cmd = cmd_write
                    elif line.startswith("EMIT_EXIT"):
                        cmd = cmd_exit
                    else:
                        print("unknown command", line)

                    cmds[name].append(cmd(*get_args(line)))


        if m := re.search(r"unsigned long (.*)\[\] = {", line):
            name = m.group(1)
            in_group = True


expanded_commands = defaultdict(list)

ecmd_write = namedtuple("Write", "uniqueid value")
ecmd_poll = namedtuple("Poll", "uniqueid")
ecmd_delay = namedtuple("Delay", "uniqueid delay")
ecmd_exit = namedtuple("Exit", "")

for name, cmd_list in cmds.items():
    for cmd in cmd_list:
        ecmds = []

        if isinstance(cmd, cmd_maskwrite):
            mask = cmd.mask
            possible_regs = registers[cmd.addr]

            for reg in possible_regs:
                if (reg.mask & mask) == reg.mask:
                    mask &= ~reg.mask
                    ecmds.append(ecmd_write(reg.uniqueid, (cmd.value & reg.mask) >> reg.bit_end))
        elif isinstance(cmd, cmd_maskpoll):
            mask = cmd.mask
            possible_regs = registers[cmd.addr]

            for reg in possible_regs:
                if (reg.mask & mask) == reg.mask:
                    mask &= ~reg.mask
                    ecmds.append(ecmd_poll(reg.uniqueid))
        elif isinstance(cmd, cmd_maskdelay):
            mask = 2**32 - 1
            possible_regs = registers[cmd.addr]

            for reg in possible_regs:
                if (reg.mask & mask) == reg.mask:
                    mask &= ~reg.mask
                    ecmds.append(ecmd_delay(reg.uniqueid, cmd.delay))
        elif isinstance(cmd, cmd_write):
            mask = 2**32 - 1
            possible_regs = registers[cmd.addr]

            for reg in possible_regs:
                if (reg.mask & mask) == reg.mask:
                    mask &= ~reg.mask
                    ecmds.append(ecmd_write(reg.uniqueid, (cmd.value & reg.mask) >> reg.bit_end))
        elif isinstance(cmd, cmd_exit):
            ecmds.append(ecmd_exit())
        else:
            print("unknown command", cmd)

        if len(ecmds) == 0:
            print(cmd)
            print(registers[cmd.addr])

        expanded_commands[name] += ecmds

order = ["ps7_mio_init_data_3_0", "ps7_pll_init_data_3_0" ,"ps7_clock_init_data_3_0" , "ps7_ddr_init_data_3_0", "ps7_peripherals_init_data_3_0", "ps7_post_config_3_0"]

for name in order:
    print(name)
    ecmds = expanded_commands[name]
    for cmd in ecmds:
        print(cmd)
