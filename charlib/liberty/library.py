import numpy as np

import charlib.liberty.liberty as liberty

class Library(liberty.Group):
    """Convenience class for liberty library groups with pre-populated defaults"""

    # These attributes must be displayed first if present, and in the order below
    ordered_attributes = [
        'technology',
        'delay_model',
        'bus_naming_style',
        'date',
        'comment',
        'time_unit',
        'voltage_unit',
        'leakage_power_unit',
        'current_unit',
        'pulling_resistance_unit',
        'capacitive_load_unit',
        'revision',
        'in_place_swap_mode'
    ]

    def __init__(self, name, **attrs):
        """Construct a library group"""
        super().__init__('library', name)
        self.file_name = attrs.pop('filename', f'{name}.lib')
        self.add_attribute('technology', 'cmos')
        self.add_attribute('delay_model', 'table_lookup')
        self.add_attribute('bus_naming_style', '%s-%d')

        # Add nominal operating conditions
        self.add_attribute('nom_process', 1.0)
        self.add_attribute('nom_voltage', 3.3) # FIXME: This isn't a sane default. Needs user input
        self.add_attribute('nom_temperature', 25.0)

        # Override defaults with whatever attrs get passed as kwargs
        [self.add_attribute(attr_name, value) for attr_name, value in attrs.items()]

        # Copy nom_* attrs into operating_conditions group
        # TODO: Make op_conditions identifier configurable
        op_conditions = liberty.Group('operating_conditions', 'typical')
        op_conditions.add_attribute('process', self.nom_process.value)
        op_conditions.add_attribute('voltage', self.nom_voltage.value)
        op_conditions.add_attribute('temperature', self.nom_temperature.value)
        self.add_group(op_conditions)

    def add_lu_table_template(self, lut, **variables):
        if isinstance(lut, LookupTableTemplate):
            self.add_group(lut)
        else:
            self.add_group(LookupTableTemplate(lut, **variables))

    @property
    def lu_table_templates(self) -> list:
        """Return lu_table_template groups."""
        return [group for group in self.groups if group.name == 'lu_table_template']

    @property
    def cells(self) -> list:
        """Return cell groups."""
        return [group for group in self.groups if group.name == 'cell']

    def to_liberty(self, **kwargs):
        """Convert this library to a Liberty-format string.

        :param precision: Digits of floating-point precision to display. Default 1.
        :param lut_precision: Digits of floating-point precision to display in LUTs. Default 6.
                              Overrides precision for LUTs.
        """
        # Library display order is specialized
        lib_str = [f'{self.name} ({self.identifier}){{']
        for attr in self.ordered_attributes:
            if hasattr(self, attr):
                lib_str += [self.attributes[attr].to_liberty(1, **kwargs)]
        for key, attr in self.attributes.items():
            if key not in self.ordered_attributes:
                lib_str += [attr.to_liberty(1, **kwargs)]
        for group in self.groups.values():
            lib_str += group.to_liberty(1, **kwargs).split('\n')
        lib_str += [f'}} /* end {self.name} */']
        return '\n'.join(lib_str)


class LookupTableTemplate(liberty.Group):
    """Convenience class for lu_table_template groups, which have slightly unusual formatting"""
    def __init__(self, lut_name, **variables):
        """Initialize a lu_table_template group

        :param lut_name: The identifier for the lu_table_template group.
        :param **variables: keyword arguments consisting of variable names and integer sizes.

        While lut templates are normal groups, they have quite a bit of odd formatting. Indices,
        for example, are complex attributes with a single long string value of comma-separated
        floats corresponding to one of the variables. Moreover, we don't care about the values in
        the indices as they are overridden by tables using these templates.
        """
        super().__init__('lu_table_template', lut_name)
        index = 1
        for variable, length in variables.items():
            self.add_attribute(f'variable_{index}', variable)
            self.add_attribute(f'index_{index}', ['"'+', '.join([str(1.0+i) for i in range(length)])+'"'])
            index += 1
        self.size = tuple(variables.values())

    def to_liberty(self, indent_level=0, **kwargs):
        # LUT template display order is specialized
        indent = liberty.INDENT_STR * indent_level
        indices = range(1, len(self.size)+1)
        lut_str = [f'{indent}{self.name} ({self.identifier}) {{']
        lut_str += [self.attributes[f'variable_{i}'].to_liberty(indent_level+1, **kwargs) for i in indices]
        lut_str += [self.attributes[f'index_{i}'].to_liberty(indent_level+1, **kwargs) for i in indices]
        for group in self.groups.values():
            lut_str += group.to_liberty(indent_level+1, **kwargs).split('\n')
        lut_str += [f'{indent}}} /* end {self.name} */']
        return '\n'.join(lut_str)


class LookupTable(liberty.Group):
    """Convenience class for lookup tables.

    LookupTables have odd formatting like LookupTableTemplates, but also need improved tools for
    quickly accessing and manipulating data. Variable values and table contents are stored as numpy
    arrays and matrices respectively.
    """

    def __init__(self, lut_name, lut_template, **variable_values):
        """Initialize a lookup table from a template

        :param lut_name: The name of the lookup table.
        :param lut_template: A LookupTableTemplate group or lu_table_template name to create.
        :param **variable_values: keyword arguments consisting of variable names and values.
        """
        if not isinstance(lut_template, LookupTableTemplate):
            lut_template = LookupTableTemplate(lut_template, **{k: len(v) for k, v in variable_values.items()})

        # Validate variable names and sizes match up with template
        for variable, i, template_length in zip(variable_values.keys(), range(1, len(lut_template.size)+1), lut_template.size):
            template_variable = lut_template.attributes[f'variable_{i}'].value
            if not variable == template_variable:
                raise ValueError(f'Template requires variable_{i} = "{template_variable}", got "{variable}"!')
            if not len(variable_values[variable]) == template_length:
                raise ValueError(f'Template requires variable "{variable}" to have {template_length} values!')
        super().__init__(lut_name, lut_template.identifier)
        self.template = lut_template

        # Store index values as numpy arrays
        self.index_values = np.array([np.array(v) for v in variable_values.values()])

        # Store table values as a matrix
        self.values = np.zeros(self.size)

    @property
    def size(self):
        """Return template size as a shape-like tuple"""
        return self.template.size

    def _get_indices(self, *index_values):
        """Determine the indices matching the ordered list of index values passed"""
        indices = []
        for key, i in zip(index_values, range(len(self.size))):
            try:
                indices += [int(np.argwhere(self.index_values[i] == key)[0][0])]
            except IndexError:
                raise KeyError(f'index_{i+1} contains no such value: {key}')
        return indices

    def __getitem__(self, keys):
        # Lookup and return value by indices
        return self.values[*self._get_indices(*keys)]

    def __setitem__(self, keys, value):
        # Lookup and set value by indices
        self.values[*self._get_indices(*keys)] = value

    def to_liberty(self, indent_level=0, lut_precision=6, **kwargs):
        # LUT display requires reformatting indices and variables
        indent = liberty.INDENT_STR * indent_level
        inner_indent = liberty.INDENT_STR * (indent_level + 1)
        value_indent = liberty.INDENT_STR * (indent_level + 2)
        lut_str = [f'{indent}{self.name} ({self.identifier}) {{']
        for i in range(len(self.index_values)):
            index_values = [f"{v:.{lut_precision}f}" for v in self.index_values[i]]
            lut_str += [f'{inner_indent}index_{i+1} ("{", ".join(index_values)}") ;']
        lut_str += [f'{inner_indent}values ( \\']
        for i in range(len(self.index_values[0])):
            values = [f"{v:.{lut_precision}f}" for v in self.values[i,:]]
            lut_str += [f'{value_indent}"{", ".join(values)}" \\']
        lut_str += [f'{inner_indent}) ;']
        lut_str += [f'{indent}}}  /* end {self.name} */']
        return '\n'.join(lut_str)


if __name__ == "__main__":
    # Test Library and LUT template classes
    library = Library('gf180')
    library.add_attribute('voltage_unit', '1V')
    lut_template = LookupTableTemplate('delay_template_5x5', total_output_net_capacitance=5, input_net_transition=5)
    library.add_lu_table_template(lut_template)

    # Add a cell with a LUT
    cell = liberty.Group('cell', 'gf180mcu_osu_sc_gp9t3v3__addf_1')
    cell.add_group('pin', 'CO')
    cell.group('pin', 'CO').add_attribute('direction', 'output')
    cell.group('pin', 'CO').add_attribute('function', 'A&B | CI&(A^B)')
    cell.group('pin', 'CO').add_group('timing')
    lut = LookupTable('cell_rise', lut_template.identifier,
                      total_output_net_capacitance=[0.0013, 0.0048, 0.0172, 0.0616, 0.2206],
                      input_net_transition=[0.0706, 0.1903, 0.5123, 1.3794, 3.714])
    # Manipulate LUT data
    lut.values[0,2] = 0.016206
    lut[0.0013, 0.1903] = 0.1134 # Test setitem
    lut[0.2206, 3.714] = lut[0.0013, 0.5123] # Test getitem
    cell.group('pin', 'CO').group('timing').add_group(lut)
    library.add_group(cell)

    # Test library merge
    library2 = Library('gf180')
    library2 += library
    assert(library.to_liberty() == library2.to_liberty())
    print(library2.to_liberty(lut_precision=5))
