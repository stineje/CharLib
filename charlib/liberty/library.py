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
        self.add_attribute('filename', f'{name}.lib')
        self.add_attribute('technology', 'cmos')
        self.add_attribute('delay_model', 'table_lookup')
        self.add_attribute('bus_naming_style', '%s-%d')
        self.add_attribute('in_place_swap_mode', 'match_footprint')

        # Add nominal operating conditions
        self.add_attribute('nom_process', 1.0)
        self.add_attribute('nom_voltage', 3.3) # FIXME: This isn't a sane default. Needs user input
        self.add_attribute('nom_temperature', 25.0)

        # Override defaults with whatever attrs get passed as kwargs
        [self.add_attribute(attr_name, value) for attr_name, value in attrs.items()]

        # Copy nom_* attrs into operating_conditions group
        op_conditions = liberty.Group('operating_conditions', 'typical')
        op_conditions.add_attribute('process', self.nom_process)
        op_conditions.add_attribute('voltage', self.nom_voltage)
        op_conditions.add_attribute('temperature', self.nom_temperature)

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

    def to_liberty(self, precision=6):
        """Convert this library to a Liberty-format string."""
        # Library display order is specialized
        lib_str = [f'{self.name}, {self.identifier}{{']
        for attr in self.ordered_attributes:
            if hasattr(self, attr):
                lib_str += [self.attributes[attr].to_liberty(1, precision)]
        for key, attr in self.attributes.items():
            if key not in self.ordered_attributes:
                lib_str += [attr.to_liberty(1, precision)]
        for group in self.groups:
            lib_str += group.to_liberty(1, precision).split('\n')
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

    def to_liberty(self, indent_level=0, precision=6):
        # LUT display order is specialized
        indent = liberty.INDENT_STR * indent_level
        indices = range(1, len(self.attributes)//2 + 1)
        lut_str = [f'{indent}{self.name} ({self.identifier}) {{']
        lut_str += [self.attributes[f'variable_{i}'].to_liberty(indent_level+1, precision) for i in indices]
        lut_str += [self.attributes[f'index_{i}'].to_liberty(indent_level+1, precision) for i in indices]
        lut_str += [f'{indent}}}']
        for group in self.groups.values():
            group_str += group.to_liberty(indent_level+1, precision).split('\n')
        return '\n'.join(lut_str)


if __name__ == "__main__":
    # Test Library and LUT classes
    library = Library('gf180')
    lut = LookupTableTemplate('delay_template_5x5', total_output_net_capacitance=5, input_net_transition=5)
    library.add_lu_table_template(lut)
    print(library.to_liberty())
