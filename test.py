import pytest

import snapshots

aerie = snapshots.PlanCollaborationInterface()

def test_merge_parent_no_conflicts():
    plan_c = aerie.make_fresh_plan()

    old_start_time = 1
    old_args = {}
    activity_0 = aerie.add_activity(
        plan_c,
        start_time=old_start_time,
        args=old_args,
    )

    assert aerie.get_activity_ids(plan_c) == [activity_0]
    plan_a = aerie.duplicate(plan_c)
    assert aerie.get_activity_ids(plan_a) == [activity_0]
    assert aerie.get_activity_start_time(plan_c, activity_0) == aerie.get_activity_start_time(plan_a, activity_0)

    assert aerie.get_activity_args(plan_c, activity_0) == aerie.get_activity_args(plan_a, activity_0)
    assert aerie.get_activity_start_time(plan_c, activity_0) == aerie.get_activity_start_time(plan_a, activity_0)
    assert aerie.get_activity_type(plan_c, activity_0) == aerie.get_activity_type(plan_a, activity_0)

    new_start_time = aerie.get_activity_start_time(plan_a, activity_0) + 1
    aerie.modify_activity(
        plan_a,
        activity_0,
        new_start_time,
        old_args,
    )

    assert aerie.get_activity_args(plan_a, activity_0) == old_args
    assert aerie.get_activity_args(plan_c, activity_0) == old_args
    assert aerie.get_activity_start_time(plan_a, activity_0) == new_start_time
    assert aerie.get_activity_start_time(plan_c, activity_0) == old_start_time

    merge_id = aerie.request_merge(plan_a, plan_c)  # child into parent
    assert "REQUESTED" == aerie.get_merge_status(merge_id)
    conflicts = aerie.begin_merge(merge_id)
    assert conflicts == []
    assert "INPROGRESS" == aerie.get_merge_status(merge_id)
    aerie.commit_merge(merge_id)
    assert "COMMITTED" == aerie.get_merge_status(merge_id)

    assert aerie.get_activity_args(plan_c, activity_0) == old_args
    assert aerie.get_activity_start_time(plan_a, activity_0) == new_start_time
    assert aerie.get_activity_start_time(plan_c, activity_0) == new_start_time


def test_merge_sibling():
    plan_c = aerie.make_fresh_plan()
    plan_a = aerie.duplicate(plan_c)
    plan_b = aerie.duplicate(plan_c)

    new_activity = aerie.add_activity(plan_a, start_time=1, args={})

    merge_id = aerie.request_merge(plan_a, plan_b)  # siblings
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)

    assert new_activity in aerie.get_activity_ids(plan_a)
    assert new_activity in aerie.get_activity_ids(plan_b)


def test_merge_cousins():
    plan_c = aerie.make_fresh_plan()
    plan_a = aerie.duplicate(plan_c)
    plan_b = aerie.duplicate(plan_c)

    plan_d = aerie.duplicate(plan_b)

    activity_1 = aerie.add_activity(plan_a, start_time=1, args={})
    activity_2 = aerie.add_activity(plan_d, start_time=1, args={})

    merge_id = aerie.request_merge(plan_a, plan_d)  # cousins
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)

    assert activity_1 in aerie.get_activity_ids(plan_d)
    assert activity_2 in aerie.get_activity_ids(plan_d)
    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 not in aerie.get_activity_ids(plan_a)
    assert not aerie.get_activity_ids(plan_c)
    assert not aerie.get_activity_ids(plan_b)


def test_merge_sibling_followed_by_parent():
    plan_c = aerie.make_fresh_plan()
    plan_a = aerie.duplicate(plan_c)
    aerie.add_activity(plan_c, start_time=1, args={})
    plan_b = aerie.duplicate(plan_c)

    aerie.add_activity(plan_a, start_time=2, args={})
    aerie.add_activity(plan_b, start_time=3, args={})

    aerie.request_merge(plan_b, plan_a)  # siblings

    aerie.request_merge(plan_a, plan_c)  # parent


def test_merge_unrelated():
    plan_c = aerie.make_fresh_plan()
    plan_a = aerie.duplicate(plan_c)
    plan_unrelated = aerie.make_fresh_plan()

    with pytest.raises(Exception):
        aerie.request_merge(plan_a, plan_unrelated)  # should error
    aerie.delete(plan_a)
    aerie.delete(plan_c)


def test_add_pull_delete_merge():
    plan_a = aerie.make_fresh_plan()
    plan_b = aerie.duplicate(plan_a)
    activity_id = aerie.add_activity(plan_a, "Foo", start_time=10, args={})
    assert activity_id in list(aerie.get_activity_ids(plan_a))
    assert activity_id not in list(aerie.get_activity_ids(plan_b))
    merge_id = aerie.request_merge(plan_a, plan_b)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)
    assert activity_id in list(aerie.get_activity_ids(plan_a))
    assert activity_id in list(aerie.get_activity_ids(plan_b))
    aerie.delete_activity(plan_b, activity_id)
    assert activity_id in list(aerie.get_activity_ids(plan_a))
    assert activity_id not in list(aerie.get_activity_ids(plan_b))
    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)
    assert activity_id not in list(aerie.get_activity_ids(plan_a))
    assert activity_id not in list(aerie.get_activity_ids(plan_b))


def test_merge_receiver_modified():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={"arg1": 0})
    plan_b = aerie.duplicate(plan_a)
    aerie.modify_activity(plan_a, activity_1, 1, {"arg1": 2})
    activity_2 = aerie.add_activity(plan_b, start_time=2, args={})

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 not in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)
    assert aerie.get_activity_args(plan_a, activity_1) == {"arg1": 2}
    assert aerie.get_activity_args(plan_b, activity_1) == {"arg1": 0}
    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)
    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)
    assert aerie.get_activity_args(plan_a, activity_1) == {"arg1": 2}
    assert aerie.get_activity_args(plan_b, activity_1) == {"arg1": 0}


def test_modify_modify_conflict_resolve_receiver():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={"arg1": 0})
    plan_b = aerie.duplicate(plan_a)
    aerie.modify_activity(plan_a, activity_1, 1, {"arg1": 2})
    aerie.modify_activity(plan_b, activity_1, 1, {"arg1": 3})  # modify - modify conflict

    activity_2 = aerie.add_activity(plan_b, start_time=2, args={})

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 not in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)
    assert aerie.get_activity_args(plan_a, activity_1) == {"arg1": 2}
    assert aerie.get_activity_args(plan_b, activity_1) == {"arg1": 3}
    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    with pytest.raises(Exception) as excinfo:
        aerie.commit_merge(merge_id)
    assert excinfo.value.args[0] == "Merge cannot be committed until all conflicts are resolved"

    aerie.resolve_conflict(merge_id, 0, "CHANGE_RECEIVER")
    aerie.commit_merge(merge_id)

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)
    assert aerie.get_activity_args(plan_a, activity_1) == {"arg1": 2}
    assert aerie.get_activity_args(plan_b, activity_1) == {"arg1": 3}

    # Try to merge again - should error because no changes since last merge
    with pytest.raises(Exception) as excinfo:
        aerie.request_merge(plan_b, plan_a)
    assert excinfo.value.args[0] == "Cannot request merge with empty changeset"


def test_modify_modify_conflict_resolve_supplier():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={"arg1": 0})
    plan_b = aerie.duplicate(plan_a)
    aerie.modify_activity(plan_a, activity_1, 1, {"arg1": 2})
    aerie.modify_activity(plan_b, activity_1, 1, {"arg1": 3})  # modify - modify conflict

    activity_2 = aerie.add_activity(plan_b, start_time=2, args={})

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 not in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)
    assert aerie.get_activity_args(plan_a, activity_1) == {"arg1": 2}
    assert aerie.get_activity_args(plan_b, activity_1) == {"arg1": 3}
    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    with pytest.raises(Exception) as excinfo:
        aerie.commit_merge(merge_id)
    assert excinfo.value.args[0] == "Merge cannot be committed until all conflicts are resolved"

    aerie.resolve_conflict(merge_id, 0, "CHANGE_SUPPLIER")
    aerie.commit_merge(merge_id)

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)
    assert aerie.get_activity_args(plan_a, activity_1) == {"arg1": 3}
    assert aerie.get_activity_args(plan_b, activity_1) == {"arg1": 3}


def test_modify_modify_no_conflict():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={"arg1": 0})
    plan_b = aerie.duplicate(plan_a)
    aerie.modify_activity(plan_a, activity_1, 1, {"arg1": 2})
    aerie.modify_activity(plan_b, activity_1, 1, {"arg1": 2})  # modify - modify no conflict

    activity_2 = aerie.add_activity(plan_b, start_time=2, args={})

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 not in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)
    assert aerie.get_activity_args(plan_a, activity_1) == {"arg1": 2}
    assert aerie.get_activity_args(plan_b, activity_1) == {"arg1": 2}
    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)
    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_2 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)
    assert aerie.get_activity_args(plan_a, activity_1) == {"arg1": 2}
    assert aerie.get_activity_args(plan_b, activity_1) == {"arg1": 2}


def test_merge_self():
    plan_a = aerie.make_fresh_plan()
    with pytest.raises(Exception) as excinfo:
        aerie.request_merge(plan_a, plan_a)
    assert excinfo.value.args[0] == "Cannot merge a plan into itself"


def test_receiver_delete():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={"arg1": 0})
    plan_b = aerie.duplicate(plan_a)
    aerie.delete_activity(plan_a, activity_1)
    activity_2 = aerie.add_activity(plan_b, start_time=1, args={})

    assert not aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)

    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)

    assert activity_2 in aerie.get_activity_ids(plan_a)
    assert activity_1 not in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)

    merge_id = aerie.request_merge(plan_a, plan_b)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)

    assert activity_2 in aerie.get_activity_ids(plan_a)
    assert activity_1 not in aerie.get_activity_ids(plan_a)
    assert activity_1 not in aerie.get_activity_ids(plan_b)
    assert activity_2 in aerie.get_activity_ids(plan_b)


def test_delete_delete_no_conflict():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={"arg1": 0})
    plan_b = aerie.duplicate(plan_a)

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)

    aerie.delete_activity(plan_a, activity_1)
    aerie.modify_activity(plan_b, activity_1, 1, {"arg1": 1})
    aerie.delete_activity(plan_b, activity_1)

    assert not aerie.get_activity_ids(plan_a)
    assert not aerie.get_activity_ids(plan_b)

    # TODO: should this case be allowed, or should we catch that there are no changes to apply?
    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)

    assert not aerie.get_activity_ids(plan_a)
    assert not aerie.get_activity_ids(plan_b)


def test_identical_modify():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={})
    plan_b = aerie.duplicate(plan_a)

    # identical modifications:
    aerie.modify_activity(plan_a, activity_1, 2, {})
    aerie.modify_activity(plan_b, activity_1, 3, {})
    aerie.modify_activity(plan_b, activity_1, 2, {})

    assert aerie.get_activity_start_time(plan_a, activity_1) == 2
    assert aerie.get_activity_start_time(plan_b, activity_1) == 2

    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)

    assert aerie.get_activity_start_time(plan_a, activity_1) == 2
    assert aerie.get_activity_start_time(plan_b, activity_1) == 2


def test_cover_repr():
    # show repr as "covered" so that it doesn't clutter the coverage report
    plan_a = aerie.make_fresh_plan()
    repr(aerie.plans[-1])


def test_receiver_deleted_supplier_modified_different():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={"arg1": 0})
    plan_b = aerie.duplicate(plan_a)

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)

    aerie.delete_activity(plan_a, activity_1)  # receiver deleted
    aerie.modify_activity(plan_b, activity_1, 1, {"arg1": 1})  # supplier modified

    assert activity_1 not in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)

    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    with pytest.raises(Exception) as excinfo:
        aerie.commit_merge(merge_id)
    assert excinfo.value.args[0] == "Merge cannot be committed until all conflicts are resolved"
    aerie.resolve_conflict(merge_id, 0, "CHANGE_SUPPLIER")
    aerie.commit_merge(merge_id)

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)


def test_receiver_deleted_supplier_modified_back_to_same():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={"arg1": 0})
    plan_b = aerie.duplicate(plan_a)

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)

    aerie.delete_activity(plan_a, activity_1)  # receiver deleted
    aerie.modify_activity(plan_b, activity_1, 1, {"arg1": 1})  # supplier modified
    aerie.modify_activity(plan_b, activity_1, 1, {"arg1": 0})  # supplier changed back to original value
    aerie.add_activity(plan_b, start_time=1, args={})  # adding a new activity just so the changeset isn't empty

    assert activity_1 not in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)

    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)  # TODO should this raise an exception because there was a conflict???

# Question: if the plan supplying changes modified an activity twice, the second change undoing the first,
# should that show up as "unchanged" or "modified"???

# Can we display whether a merge_request is "up to date"?
# Can a user rescind a merge request/update it with
# another one/just generally update it based on feedback?

# TODO test plan locking
# TODO test staging plan

def test_modify_delete_supplier():
    plan_a = aerie.make_fresh_plan()
    activity_1 = aerie.add_activity(plan_a, start_time=1, args={})
    plan_b = aerie.duplicate(plan_a)

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_1 in aerie.get_activity_ids(plan_b)

    aerie.modify_activity(plan_a, activity_1, 2, {})
    aerie.delete_activity(plan_b, activity_1)

    assert activity_1 in aerie.get_activity_ids(plan_a)
    assert activity_1 not in aerie.get_activity_ids(plan_b)

    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.resolve_conflict(merge_id, 0, "CHANGE_SUPPLIER")
    aerie.commit_merge(merge_id)

    assert not aerie.get_activity_ids(plan_a)
    assert not aerie.get_activity_ids(plan_b)


def test_abort_merge():
    plan_a = aerie.make_fresh_plan()
    plan_b = aerie.duplicate(plan_a)
    activity_1 = aerie.add_activity(plan_b, start_time=1, args={})
    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.abort_merge(merge_id)

    assert activity_1 in aerie.get_activity_ids(plan_b)
    assert not aerie.get_activity_ids(plan_a)


def test_try_commit_merge_other_states():
    plan_a = aerie.make_fresh_plan()
    plan_b = aerie.duplicate(plan_a)
    aerie.add_activity(plan_b, start_time=1, args={})
    merge_id = aerie.request_merge(plan_b, plan_a)
    with pytest.raises(Exception) as excinfo:
        aerie.commit_merge(merge_id)
    assert excinfo.value.args[0] == "Cannot commit a merge in state REQUESTED"
    aerie.begin_merge(merge_id)
    aerie.abort_merge(merge_id)
    with pytest.raises(Exception) as excinfo:
        aerie.commit_merge(merge_id)
    assert excinfo.value.args[0] == "Cannot commit a merge in state ABORTED"

def test_commit_twice():
    plan_a = aerie.make_fresh_plan()
    plan_b = aerie.duplicate(plan_a)
    aerie.add_activity(plan_b, start_time=1, args={})
    merge_id = aerie.request_merge(plan_b, plan_a)
    aerie.begin_merge(merge_id)
    aerie.commit_merge(merge_id)
    with pytest.raises(Exception) as excinfo:
        aerie.commit_merge(merge_id)
    assert excinfo.value.args[0] == "Cannot commit a merge in state COMMITTED"
