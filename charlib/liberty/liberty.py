"""Tools for creating Liberty groups. See Liberty User Guide Vol 1, Chapter 1."""

import re
from collections import UserDict

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

    @property
    def unique_key(self):
        return (self.name, self.identifier)

    def to_liberty(self, indent=0, precision=6):
        return NotImplemented


class Group(Statement):

    class SubGroupDict(UserDict):
        """Custom dictionary with auto-updating keys. Used for keeping track of subgroups."""

        def __setitem__(self, key, value):
            self._update_key(key, value)
            value._bind_to_parent_group(self)

        def _update_key(self, key, value):
            new_key = value.unique_key
            existing_group = self.data.get(new_key)
            if existing_group and existing_group is not value:
                # Rekeying value collided with an existing sibling. Rather than raising, merge
                # the sibling into value, since both represent the same logical subgroup.
                del self.data[new_key]
                value.merge(existing_group)
                new_key = value.unique_key
            if key in self.data and key != new_key:
                del self.data[key]
            self.data[new_key] = value

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
        self.groups = self.SubGroupDict()
        self.attributes = dict()
        self._parent_dict = None

    def _bind_to_parent_group(self, parent_group_dict):
        self._parent_dict = parent_group_dict

    def __eq__(self, other):
        # Implements == operation
        if not isinstance(other, Group):
            return NotImplemented
        return self.name == other.name \
            and self.identifier == other.identifier \
            and self.groups == other.groups \
            and self.attributes == other.attributes

    def __iadd__(self, other):
        # In-place add. Implements += operation
        if not isinstance(other, Group):
            raise NotImplementedError
        self.merge(other)
        return self

    def __repr__(self):
        # Display for debugging
        return f'Group({self.name}, {self.identifier})'

    @property
    def unique_key(self):
        # overrides for groups which are not uniquely identifiable by group name and identifier
        if self.name == 'timing' and self.attributes.get('related_pin') and self.attributes.get('timing_type'):
            return (self.name, self.attributes.get('related_pin').value,
                    self.attributes.get('timing_type').value)
        elif self.name == 'leakage_power' and self.attributes.get('when'):
            return (self.name, self.attributes.get('when').value)
        return super().unique_key

    def add_group(self, group, group_id=''):
        """Add a subgroup.

        :param group: An existing Group object or the name of the group to create.
        :param group_id: The group identifier for the new group. Ignored if group is a Group object.
        """
        if not isinstance(group, Group):
            group = Group(group, group_id)
        try:
            existing_group = self.groups[group.unique_key]
            existing_group.merge(group)
            group = existing_group
        except KeyError:
            pass
        finally:
            self.groups[group.unique_key] = group

    def group(self, name, identifier='', **attributes):
        """Look up a subgroup by name and id

        This method is primarily a convenience function for self.groups[(name, id)]. If the initial
        (name, id) lookup fails and attrs are present, an attempt is made to find a unique subgroup
        by checking attributes as well. This method will not return subgroups of subgroups; see
        filter_subgroups if you need that behavior.

        :param name: The subgroup name (i.e. 'timing' of 'cell')
        :param identifier: (Optional) The subgroup identifier. Ignored if not specified.
        :param **attributes: (Optional) Name-value pairs corresponding to subgroup attributes.
        :raises KeyError: If unable to find a unique matching group.
        """
        try:
            return self.groups[(name, identifier)]
        except KeyError as e:
            if attributes: # Fall back to subgroup search
                groups = self.filter_subgroups(name, identifier, **attributes)
                groups = [g for g in groups if self.groups.get(g.unique_key) is g]
                if len(groups) != 1:
                    raise KeyError(f'Subgroup search found {len(groups)} matching groups!') from e
                return groups[0]
            else:
                raise

    def subgroups_with_name(self, name: str):
        """Yield subgroups with the specified name.

        :param name: The subgroup name (i.e. 'timing' or 'cell') to search for.
        """
        for group in self.groups.values():
            if group.name == name:
                yield group
            elif group.groups:
                yield from group.subgroups_with_name(name)

    def filter_subgroups(self, name: str, identifier='', **attributes):
        """Yield subgroups with the specified name, id, and matching attributes

        :param name: The subgroup name (i.e. 'timing' or 'cell') to search for.
        :param identifier: (Optional) The subgroup identifier to search for. Ignored if not
                           specified.
        :param **attributes: (Optional) Name-value pairs corresponding to subgroup attributes
                             to match.
        """
        for group in self.subgroups_with_name(name):
            if identifier and group.identifier != identifier:
                continue
            if any(group.attributes.get(k) != (k,v) for k,v in attributes.items()):
                continue
            yield group

    def add_attribute(self, attr: str, value=None, precision=None):
        """Add a simple or complex attribute.

        :param attr: An existing Attribute object or the name of the Attribute object to create.
        :param value: The value for the new attribute. Ignored if attr is an Attribute object.
        :param precision: If different from default, the number of digits to display when printed.
                          Ignored if attr is an Attribute object.
        """
        old_key = self.unique_key
        if isinstance(attr, Attribute):
            self.attributes[attr.name] = attr
        else:
            self.attributes[attr] = Attribute(attr, value, precision)
        # If this is a subgroup, updating attributes may have changed this group's key
        if self._parent_dict:
            self._parent_dict._update_key(old_key, self)

    def merge(self, other):
        """Merge another group into this one, merging sub-groups and adding attributes.

        Note that attribute values from other will override attribute values from self."""
        old_key = self.unique_key
        if not self.unique_key == other.unique_key:
            raise ValueError(f'Cannot merge groups with different identifiers {self.unique_key} and {other.unique_key}')
        [self.add_group(group) for group in other.groups.values()]
        self.attributes |= other.attributes
        if self._parent_dict:
            self._parent_dict._update_key(old_key, self)

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
    def __init__(self, attribute_name: str, attribute_value: bool|int|float|str|list,
                 precision=None):
        """Create a new Liberty attribute.

        Per section 1.2.2, attributes have one of the following formats:
        attribute_name : attribute_value ;
        OR
        attribute_name (attribute_value[0], attribute_value[1], ...);

        This object will choose which format to use based on the type of attribute_value.

        :param attribute_name: The Liberty attribute name, such as 'function' or 'value'.
        :param attribute_value: The value to store. May be numeric, boolean, string, or list.
        :param precision: The number of digits to display with to_liberty, if different from
                          default.
        """
        self.name = attribute_name
        # TODO: Validate attribute_value
        self.value = attribute_value
        self.precision = precision

    def __eq__(self, other):
        # Implements == operation
        if isinstance(other, Attribute):
            return self.name == other.name and self.value == other.value
        elif isinstance(other, tuple) and len(other) == 2:
            return (self.name, self.value) == other
        else:
            return NotImplemented

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
            return f'{indent}{self.name} ({", ".join([str(v) for v in self.value])});'
        elif isinstance(self.value, str):
            return f'{indent}{self.name} : {self._to_safe_str(self.value)} ;'
        elif isinstance(self.value, float):
            precision = self.precision if self.precision is not None else precision
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
    library.add_group('cell', 'gf180mcu_osu_sc_gp9t3v3__inv_1')
    library.group('cell', 'gf180mcu_osu_sc_gp9t3v3__inv_1').add_attribute('area', 128)
    library.group('cell', 'gf180mcu_osu_sc_gp9t3v3__inv_1').add_group('pg_pin', 'VDD')
    library.group('cell', 'gf180mcu_osu_sc_gp9t3v3__inv_1').group('pg_pin', 'VDD').add_attribute('voltage_name', 'VDD')

    # Try merging another library built in a different way
    library_2 = Group('library', 'gf180mcu_osu_sc_gp9t3v3_tt_25c')
    cell = Group('cell', 'gf180mcu_osu_sc_gp9t3v3__inv_1')
    cell.add_group('pin', 'A')
    cell.group('pin', 'A').add_attribute('direction', 'input')
    cell.group('pin', 'A').add_attribute(Attribute('capacitance', 0.012821))
    cell.add_group('pin', 'Y')
    cell.group('pin', 'Y').add_attribute('direction', 'output')
    library_2.add_group(cell)
    library.merge(library_2)

    print(library.to_liberty())

    [print(g) for g in library.subgroups_with_name('spoon')] # Should print nothing
    [print(g) for g in library.subgroups_with_name('pin')] # Should print 2 pins
