import sys

MEMORY_SIZE = 1024

SLOT_RANGE = range(1, 14)
TEMP_RANGE = range(1, 9001)

AX = "'"
TX = ")"
SX = "}"

runtime_vars = {SX: "sx", AX: "ax", TX: "tx"}

default_constants = {
    "PILL": 11,
    "VIAL": 12,
    "DUMP": 13
}

ADD = "+"
SUB = "-"
RIGHT = ">"
LEFT = "<"
MOVE = "@"
HEAT = "$"
LOG = "."

BASE_HEAT = 273

CMD_SET = "SET"
CMD_INC = "INC"
CMD_MOVE = "MOVE"
CMD_HEAT = "HEAT"
CMD_REPEAT = "REPEAT"
CMD_END = "END"
CMD_LOG = "LOG"

VARIABLE_NAME_CHARS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def is_digit(n):
    try: int(n)
    except: return False
    return True

def is_valid_var_name(var):
    return all([c in VARIABLE_NAME_CHARS for c in var]) and not var[0].isdigit()


class Compiler():
    def __init__(self,code):
        self.code = code

    def reset(self):
        self.lines = self.code.split("\n")
        self.line_index = 0
        self.pointer = 0
        self.memory = [0] * MEMORY_SIZE
        self.vars = dict({runtime_vars[AX]: 0, runtime_vars[TX]: 0, runtime_vars[SX]: 0}, **default_constants)
        self.repeat_stack = []
        self.output = ""

    def compile(self):
        self.reset()

        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            args = line.strip().split()
            if len(args) == 0:
                self.line_index += 1
                continue
            cmd = args.pop(0)

            if cmd == CMD_SET or cmd == CMD_INC:
                t = args.pop(0)
                args = [t] + [self.vars[arg] if arg in self.vars else arg for arg in args]
            else:
                args = [self.vars[arg] if arg in self.vars else arg for arg in args]


            if cmd == CMD_SET: o=self.cmd_set(args)
            elif cmd == CMD_INC: o=self.cmd_inc(args)
            elif cmd == CMD_HEAT: o=self.cmd_heat(args)
            elif cmd == CMD_MOVE: o=self.cmd_move(args)
            elif cmd == CMD_REPEAT: o=self.cmd_repeat(args)
            elif cmd == CMD_END: o=self.cmd_end(args)
            elif cmd == CMD_LOG: o=self.cmd_log(args)

            if isinstance(o, str):
                sys.stdout.write("ERROR on line {} during {}:\n\t{}".format(self.line_index+1, cmd, o))
                return None

            self.line_index += 1

        return self.output

    def get_optimal_mem_index(self,val):
        best_index = None
        best_l = None
        for i in range(len(self.memory)-1):
            l = abs(self.pointer-i)+abs(val-self.memory[i])
            if best_l == None or l < best_l:
                best_index = i
                best_l = l
                if l == 0: break

        return best_index

    def move_pointer_to(self,i):
        d = i - self.pointer
        if d > 0: self.output+=RIGHT*abs(d)
        elif d < 0: self.output+=LEFT*abs(d)
        self.pointer = i

    def generate_val(self,val):
        i = self.get_optimal_mem_index(val)
        self.move_pointer_to(i)
        d = val - self.memory[i]
        if d > 0: self.output+=ADD*abs(d)
        elif d < 0: self.output+=SUB*abs(d)
        self.memory[i] = val

    def set_var(self,var,val):
        if var in runtime_vars:
            self.generate_val(val)
            self.output += var
            self.vars[runtime_vars[var]] = val
        else:
            self.vars[var] = val
        return val

    def get_var(self,var):
        return self.vars[var] if var in self.vars else None

    def cmd_set(self,args):
        if len(args) != 2: return "incorrect argument amount: "+str(len(args))
        if not is_valid_var_name(args[0]): return "invalid var name: "+str(args[0])
        if not is_digit(args[1]): return "invalid var value: "+str(args[1])
        self.set_var(args[0], int(args[1]))

    def cmd_inc(self,args):
        if len(args) != 2: return "incorrect argument amount: "+str(len(args))
        if self.get_var(args[0]) == None: return "unknown variable: "+str(args[0])
        if not is_digit(args[1]): return "invalid inc value: "+str(args[1])

        self.set_var(args[0], self.get_var(args[0])+int(args[1]))

    def cmd_move(self,args):
        if len(args) != 3: return "incorrect argument amount: "+str(len(args))
        if not is_digit(args[0]): return "invalid 1st argument: "+str(args[0])
        if not int(args[0]) in SLOT_RANGE: return "1st argument not in slot range: "+str(args[0])
        if not is_digit(args[1]): return "invalid 2nd argument: "+str(args[1])
        if not int(args[1]) in SLOT_RANGE: return "2nd argument not in slot range: "+str(args[1])
        if not is_digit(args[2]): return "invalid 3rd argument: "+str(args[2])

        self.set_var(SX, int(args[0]))
        self.set_var(TX, int(args[1]))
        self.set_var(AX, int(args[2]))
        self.output += MOVE

    def cmd_heat(self,args):
        if len(args) != 2: return "incorrect argument amount: "+str(len(args))
        if not is_digit(args[0]): return "invalid 1st argument: "+str(args[0])
        if not int(args[0]) in SLOT_RANGE: return "1st argument not in slot range: "+str(args[0])
        if not is_digit(args[1]): return "invalid 2nd argument: "+str(args[1])
        if not int(args[1]) in TEMP_RANGE: return "2nd argument not in temp range: "+str(args[1])

        self.set_var(SX, int(args[0]))

        if int(args[1]) > BASE_HEAT:
            self.set_var(TX, 0)
            self.set_var(AX, int(args[1])-BASE_HEAT)
        elif int(args[1]) < BASE_HEAT:
            self.set_var(TX, BASE_HEAT-int(args[1]))
            self.set_var(AX, 0)
        else:
            self.set_var(TX, 0)
            self.set_var(AX, 0)

        self.output += HEAT

    def cmd_repeat(self,args):
        if len(args) != 1: return "incorrect argument amount: "+str(len(args))
        if not is_digit(args[0]): return "invalid 1st argument: "+str(args[0])
        self.repeat_stack.append([self.line_index,int(args[0]),0])

    def cmd_end(self,args):
        if len(args) != 0: return "no arguments accepted but was passed: "+str(len(args))
        if len(self.repeat_stack) == 0: return "END with no REPEAT"

        self.repeat_stack[-1][2]+=1
        if self.repeat_stack[-1][2] < self.repeat_stack[-1][1]:
            self.line_index = self.repeat_stack[-1][0]
        else:
            del self.repeat_stack[-1]

    def cmd_log(self,args):
        print(args)
        if len(args) != 1: return "incorrect argument amount: "+str(len(args))
        if not is_digit(args[0]): return "invalid 1st argument: "+str(args[0])

        self.generate_val(int(args[0]))
        self.output += LOG

if len(sys.argv) >= 2:
    try:
        code = open(sys.argv[1]).read()
        compiler = Compiler(code)
        out = compiler.compile()
        if out: sys.stdout.write(out)
    except:
        sys.stdout.write("Could not open file "+sys.argv[1])
else:
    sys.stdout.write("Please specify a file to compile!")
