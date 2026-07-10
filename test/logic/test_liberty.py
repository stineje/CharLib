from charlib.liberty import liberty


# ---------------------------------------------------------------------------
# Group.merge / rekey collision tests
# ---------------------------------------------------------------------------

def test_merge_rekey_collision_merges_into_existing_sibling():
    """Merging two parents whose timing subgroups only partially specify
    related_pin/timing_type can cause a subgroup's unique_key to change to
    match an already-present sibling once merged. This should merge the two
    subgroups together instead of raising a Duplicate subgroup ValueError."""
    cell = liberty.Group('cell', 'inv')

    # A sibling that already has the fully-qualified key.
    existing = liberty.Group('timing', '')
    existing.add_attribute('related_pin', 'X')
    existing.add_attribute('timing_type', 'combinational_rise')
    existing.add_attribute('marker', 'existing')
    cell.add_group(existing)

    # A timing group that only has related_pin so far; its key is still ('timing', '').
    partial = liberty.Group('timing', '')
    partial.add_attribute('related_pin', 'X')
    cell.add_group(partial)

    # A separate cell with a timing group that only has timing_type; merging this
    # into `cell` will complete `partial`'s key, colliding with `existing`.
    other_cell = liberty.Group('cell', 'inv')
    other = liberty.Group('timing', '')
    other.add_attribute('timing_type', 'combinational_rise')
    other_cell.add_group(other)

    cell.merge(other_cell)

    timing_groups = [g for g in cell.groups.values() if g.name == 'timing']
    assert len(timing_groups) == 1
    merged = timing_groups[0]
    assert merged.attributes['related_pin'] == ('related_pin', 'X')
    assert merged.attributes['timing_type'] == ('timing_type', 'combinational_rise')
    assert merged.attributes['marker'] == ('marker', 'existing')


def test_add_attribute_rekey_collision_merges_into_existing_sibling():
    """Adding an attribute directly to a bound subgroup can also change its
    unique_key to collide with a sibling; this should merge rather than raise."""
    cell = liberty.Group('cell', 'inv')

    existing = liberty.Group('timing', '')
    existing.add_attribute('related_pin', 'X')
    existing.add_attribute('timing_type', 'combinational_rise')
    existing.add_attribute('marker', 'existing')
    cell.add_group(existing)

    partial = liberty.Group('timing', '')
    partial.add_attribute('related_pin', 'X')
    cell.add_group(partial)

    # Directly completing partial's key should merge it with `existing`.
    partial.add_attribute('timing_type', 'combinational_rise')

    timing_groups = [g for g in cell.groups.values() if g.name == 'timing']
    assert len(timing_groups) == 1
    merged = timing_groups[0]
    assert merged.attributes['marker'] == ('marker', 'existing')