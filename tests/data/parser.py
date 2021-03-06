import os
import numpy as np


# unit_fmt = {'cycle': int, 'net': float, 'I_net': float,
#             'act': float, 'act_eq': float, 'act_nd': float,
#             'v_m': float, 'vm_eq': float, 'spike': int, 'adapt': float,
#             'syn_tr': float, 'syn_pr': float, 'syn_nr': float, 'syn_kre': float,
#             'avg_ss': float, 'avg_s': float, 'avg_m': float, 'avg_s_eff': float, 'avg_l': float, 'gc_i': float}
unit_trans = {'vm_eq': 'v_m_eq'}

def parse_unit(filename, flat=False):
    return parse_file(filename, trans=unit_trans, flat=flat)

# weights_fmt = {'trial_name': str, 'sse': float, 'Input_act_m': float, 'Output_act_m': float, 'wts': float}
weights_trans = {'Input_act_m': 'input_act_m', 'Output_act_m': 'output_act_m', 'wts':'wt'}

def parse_weights(filename, flat=False):
    """Parse weight matrix with only one element"""
    return parse_file(filename, trans=weights_trans, flat=flat)

def parse_xy(filename, flat=False):
    return parse_file(filename, flat=flat)

def parse_file(filename, trans=None, flat=False):
    """Return the data file as a dict

    `vm_eq` is renamed in `v_m_eq`.
    """

    filepath = os.path.join(os.path.abspath(os.path.join(__file__, '..')), filename)
    with open(filepath, 'r') as fd:
        lines = fd.readlines()

    # removing the newline characters
    for i, line in enumerate(lines):
        if line.endswith('\n'):
            lines[i] = line[:-1]

    # checking some assumptions about the format
    assert lines[0].startswith('_H:'), 'Unrecognized format {}'.format(filepath)
    for line in lines[1:]:
        assert len(line) == 0 or line.startswith('_D:'), 'Unrecognized format {}'.format(filepath)

    header, fmt, matrices_pos, matrices_dim = [], {}, [], []
    for name in lines[0].split('\t')[1:]:
        fmt_sign = name[0]
        name = name[1:]

        if '[' in name:
            core_name = name[:name.index('[')]
            header.append(core_name)
            fmt[core_name] = float

            matrix_pos = (name[name.index('[')+1:name.index(']')]).split(':')[1].split(',')
            matrix_pos = tuple(int(d) for d in matrix_pos)
            matrices_pos.append(matrix_pos)

            if '<' in name:
                matrix_dims = (name[name.index('<')+1:name.index('>')]).split(':')[1].split(',')
                matrix_dims = tuple(int(d) for d in matrix_dims)
                matrices_dim.append(matrix_dims)
            else:
                matrices_dim.append(None)

        else:
            matrices_dim.append(None)
            matrices_pos.append(None)
            header.append(name)
            fmt[name] = {'|': int, '$': str, '%': float, '&': float}[fmt_sign]

    data = {name: [] for name in header}

    for line in lines[1:]:
        if len(line) > 0:
            values = line.split('\t')[1:]
            values = [v for v in values if v != '']
            assert len(values) == len(header), 'len({}) [values] {} != {} [header] len({})'.format(values, len(values), len(header), header)

            for name, dims in zip(header, matrices_dim):
                if dims is not None:
                    data[name].append(np.ndarray(dims))

            for name, mpos, v in zip(header, matrices_pos, values):
                if mpos is None:
                    data[name].append(fmt[name](v))
                else:
                    data[name][-1][mpos] = fmt[name](v)

    # transforming names according to trans dict
    if trans is not None:
        for name in set(header):
            if name in trans:
                data[trans[name]] = data.pop(name)

    if flat:
        # flatten if only one value
        for values in data.values():
            for i, v in enumerate(values):
                values[i] = flatten_list(v)

    return data

def flatten_list(v):
    try:
        if len(v) == 1:
            return flatten_list(v[0])
        else:
            return v
    except (KeyError, TypeError):
        return v


if __name__ == '__main__':
    print(parse_file('neuron.txt'))
