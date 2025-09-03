"""Tools for creating Liberty groups. See Liberty User Guide Vol 1, Chapter 1."""

import re

INDENT_STR = '  '

class Statement:
    """Abstract base class for Liberty statements, such as Groups and Attributes"""
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if not re.match(r'^\w+$', name):
            raise ValueError('Liberty object names must consist of only alphanumeric characters and underscores!')
        self._name = name

    def to_liberty(self, indent=0, precision=6):
        return NotImplemented


class Group(Statement):
    def __init__(self, group_name: str, group_id: str=''):
        """Create a new Liberty group.

        Per section 1.2.1, groups have the following syntax:
        group_name (group_id) {
            ... attributes and sub-groups ...
        }

        :param group_name: The Liberty group name, such as 'cell' or 'pin'.
        :param group_id: The group identifier, e.g. the cell name for a 'cell' group.
        """
        self.name = group_name
        self.identifier = group_id # TODO: Validate
        self.groups = dict()
        self.attributes = dict()

    def __hash__(self):
        # Implements hash(Group)
        return hash((self.name, self.identifier))

    def __eq__(self, other):
        # Implements == operation
        if not isinstance(other, Group):
            return NotImplemented
        return hash(self) == hash(other) and self.groups == other.groups and self.attributes == other.attributes

    def __iadd__(self, other):
        # In-place add. Implements += operation
        if not isinstance(other, Group):
            raise NotImplementedError
        self.merge(other)
        return self

    def __repr__(self):
        # Display for debugging
        return f'Group({self.name}, {self.identifier})'

    def __getattr__(self, name):
        # Allows group.key syntax for attribute (but not subgroup) lookup
        try:
            return self.attributes[name]
        except KeyError:
            classname = type(self).__name__
            raise AttributeError(f'{classname!r} object has no attribute {name!r}')

    def add_group(self, group, group_id=''):
        """Add a sub-group.

        :param group: An existing Group object or the name of the group to create.
        :param group_id: The group identifier for the new group. Ignored if group is a Group object.
        """
        if not isinstance(group, Group):
            group = Group(group, group_id)
        try:
            existing_group = self.group(group.name, group.identifier)
            group.merge(existing_group)
        except KeyError:
            pass
        finally:
            self.groups[hash(group)] = group

    def group(self, name, identifier=''):
        """Look up a sub-group by name and id"""
        return self.groups[hash((name, identifier))]

    def add_attribute(self, attr: str, value=None):
        """Add a simple or complex attribute.

        :param attr: An existing Attribute object or the name of the Attribute object to create.
        :param value: The value for the new attribute. Ignored if attr is an Attribute object.
        """
        if isinstance(attr, Attribute):
            self.attributes[attr.name] = attr
        else:
            self.attributes[attr] = Attribute(attr, value)

    def merge(self, other):
        """Merge another group into this one, merging sub-groups and adding attributes.

        Note that attribute values from other will override attribute values from self."""
        if not hash(self) == hash(other):
            raise ValueError("Group name and id must match in order to merge!")
        [self.add_group(group) for group in other.groups.values()]
        self.attributes |= other.attributes

    def to_liberty(self, indent_level=0, precision=1, **kwargs):
        """Convert this group to a Liberty-format string

        :param indent_level: The level of indentation to use. Default 0.
        :param precision: The number of digits to use when displaying float values. Default 1.
        """
        indent = INDENT_STR * indent_level
        group_str = [f'{indent}{self.name} ({self.identifier}) {{']
        for attr in self.attributes.values():
            group_str += [attr.to_liberty(indent_level+1, precision=precision, **kwargs)]
        for group in self.groups.values():
            group_str += group.to_liberty(indent_level+1, precision=precision, **kwargs).split('\n')
        group_str += [f'{indent}}} /* end {self.name} */']
        return '\n'.join(group_str)


class Attribute(Statement):
    def __init__(self, attribute_name: str, attribute_value: bool|int|float|str|list):
        """Create a new Liberty attribute.

        Per section 1.2.2, attributes have one of the following formats:
        attribute_name : attribute_value ;
        OR
        attribute_name (attribute_value[0], attribute_value[1], ...);

        This object will choose which format to use based on the type of attribute_value.

        :param attribute_name: The Liberty attribute name, such as 'function' or 'value'.
        :param attribute_value: The value to store. May be numeric, boolean, string, or list.
        """
        self.name = attribute_name
        # TODO: Validate attribute_value
        self.value = attribute_value

    def __hash__(self):
        # Implements hash(Attribute)
        return hash((self.name, *list(self.value)))

    def __eq__(self, other):
        # Implements == operation
        return self.name == other.name and self.value == other.value

    def __repr__(self):
        # Display for debugging
        return f'Attribute({self.name}, {self.value})'

    def _to_safe_str(self, value: str) -> str:
        """Given a str value, determine whether it needs quotes and add if required

        Some string values require double quotes to prevent errors in Liberty parsers. Whether this
        is really our problem or an issue that should instead be fixed in parsers is not
        particularly relevant to getting this working. There are several categories of strings that
        need to be 'escaped' in this way:
        - Strings containing whitespace
        - Strings which start with numeric characters
        - Strings containing certain special characters, such as hyphens or percent signs

        :param value: A string value that may or may not need to be enclosed in quotes
        """
        value = value.strip()
        if value[0].isnumeric() or not re.match(r'^\w+$', value):
            return f'"{value}"'
        else:
            return value

    def to_liberty(self, indent_level=0, precision=1, **kwargs) -> str:
        """Convert this Attribute to a Liberty-format string

        :param indent_level: The level of indentation to use. Default 0.
        :param precision: The number of digits to include when displaying float values. Default 6.
        """
        indent = INDENT_STR * indent_level
        if isinstance(self.value, list):
            # TODO: Break long lists intelligently
            return f'{indent}{self.name} ({", ".join([str(v) for v in self.value])});'
        elif isinstance(self.value, str):
            return f'{indent}{self.name} : {self._to_safe_str(self.value)} ;'
        elif isinstance(self.value, float):
            return f'{indent}{self.name} : {self.value:.{precision}f} ;'
        else: # Assume int or bool, but don't prevent other types
            return f'{indent}{self.name} : {self.value} ;'


class Define(Attribute):
    """A define is basically a complex attribute with a bit more input validation"""
    def __init__(self, attribute_name, group_name, attribute_type):
        # TODO: validate attribute_type: must be one of 'Boolean', 'string', 'integer', or 'floating point'
        super.__init__('define', [attribute_name, group_name, attribute_type])


if __name__ == "__main__":
    # Test liberty groups
    library = Group('library', 'gf180mcu_osu_sc_gp9t3v3_tt_25c')
    library.add_attribute('technology', 'cmos')
    library.add_attribute('delay_model', 'table_lookup')
    library.add_group('cell', 'gf180mcu_osu_sc_gp9t3v3__addf_1')
    library.group('cell', 'gf180mcu_osu_sc_gp9t3v3__addf_1').add_attribute('area', 128)
    library.group('cell', 'gf180mcu_osu_sc_gp9t3v3__addf_1').add_group('pg_pin', 'VDD')
    library.group('cell', 'gf180mcu_osu_sc_gp9t3v3__addf_1').group('pg_pin', 'VDD').add_attribute('voltage_name', 'VDD')

    # Try merging another library built in a different way
    library_2 = Group('library', 'gf180mcu_osu_sc_gp9t3v3_tt_25c')
    cell = Group('cell', 'gf180mcu_osu_sc_gp9t3v3__addf_1')
    cell.add_group('pin', 'A')
    cell.group('pin', 'A').add_attribute('direction', 'input')
    cell.add_attribute(Attribute('capacitance', 0.012821))
    library_2.add_group(cell)
    library.merge(library_2)

    print(library.to_liberty())
