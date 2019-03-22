import re, json, ctags
from ctags import CTags, TagEntry

prefix = './linux/'

# file generated by ctags --fields=afmikKlnsStz --c-kinds=+pc -R
tags = CTags(prefix+'tags')
entry = TagEntry()

syscall_tbl = open(prefix+'arch/x86/entry/syscalls/syscall_64.tbl', 'r')
syscall_out = open('www/syscall.json', 'w+')

syscall_func = []


def parse_line(entry):
    file_name = entry['file']
    line_num = int(entry['lineNumber'])
    syscall_str = entry['pattern'][2:-2]

    if syscall_str[-1] != ')':
        with open(prefix+file_name, 'r') as f:
            # enumerate(x) uses x.next(), so it doesn't need the entire file in memory.
            start = False
            for i, line in enumerate(f):
                if i == line_num:
                    start = True
                if start:
                    line = line.strip()
                    syscall_str += line
                    if line[-1] == ')':
                        break

    match = re.search('SYSCALL_DEFINE\d\((.*)\)', syscall_str)
    symbols = map(str.strip, match.group(1).split(',')[1:])
    params = []
    for i in range(len(symbols)/2):
        params.append({
            'type': symbols[i*2] + ' ' + symbols[i*2+1],
            'def': None
        })

    return params + [{}]*(6-len(params))

for line in syscall_tbl.readlines():
    line = line.strip()
    if line:
        if line.startswith('#'):
            continue
        else:
            syscall = re.search('(\d*)\s*(\w*)\s*(\w*)\s*(\w*)(/.*)?', line)
            symbols = syscall.groups()
            func_id = int(symbols[0])
            func_type = symbols[1]
            func_name = symbols[2]
            func_fullname = symbols[3][10:] if symbols[3] else 'not implemented'

            if func_type != 'x32':
                if tags.find(entry, 'SYSCALL_DEFINE', ctags.TAG_PARTIALMATCH):
                    while True:
                        # '[,\)]' is essential to filter mmap2 or the like
                        if re.search('SYSCALL_DEFINE\d\('+func_fullname+'[,\)]', entry['pattern']):
                            parsed = parse_line(entry)
                            syscall_info = [
                                func_id,
                                func_name,
                                '{0:#04x}'.format(func_id)
                            ]
                            syscall_info += parsed
                            syscall_info += [entry['file'], entry['lineNumber']]
                            syscall_func.append(syscall_info)
                            break

                        elif not tags.findNext(entry):
                            # print(func_name)
                            syscall_func.append([
                                func_id,
                                func_name,
                                '{0:#04x}'.format(func_id),
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                '',
                                0
                            ])
                            break


syscall_out.write(
    json.dumps(
    {
        'aaData': syscall_func
    },
    sort_keys=True,
    indent=2
))

syscall_tbl.close()
syscall_out.close()
