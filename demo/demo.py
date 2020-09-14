from vcd_parser import VCD

# Open the file and parse its contents
vcd1 = VCD('data.vcd')

# Display the parsed data
print('VCD header data:')
print('\tComments:')
for comment in vcd1.comments:
    print('\t\t' + comment)
print('\tDate: ' + vcd1.date.isoformat())
print('\tVersion: ' + vcd1.version)
print(f'\tTimescale: {vcd1.timescale}s')
print()
print('Variables and value changes:')
for v in vcd1.vars.values():
    var = v.copy()
    del var['vals']
    del var['timestamps']
    var['num_vals'] = len(v['vals'])
    var['num_timestamps'] = len(v['timestamps'])
    print(var)
