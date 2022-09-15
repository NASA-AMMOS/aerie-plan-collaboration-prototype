import event_log

aerie = event_log.PlanCollaborationInterface()

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
    assert aerie.is_same_activity(plan_c, activity_0, plan_a, activity_0)

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

    aerie.merge(plan_a, plan_c)  # child into parent

    assert aerie.get_activity_args(plan_c, activity_0) == old_args
    assert aerie.get_activity_start_time(plan_a, activity_0) == new_start_time
    assert aerie.get_activity_start_time(plan_c, activity_0) == new_start_time


def test_merge_sibling():
    plan_c = aerie.make_fresh_plan()
    plan_a = aerie.duplicate(plan_c)
    plan_b = aerie.duplicate(plan_c)

    aerie.merge(plan_a, plan_b)  # siblings

def test_merge_cousins():
    plan_c = aerie.make_fresh_plan()
    plan_a = aerie.duplicate(plan_c)
    plan_b = aerie.duplicate(plan_c)

    plan_d = aerie.duplicate(plan_b)

    aerie.merge(plan_b, plan_d)  # cousins

def test_merge_sibling_followed_by_parent():
    plan_c = aerie.make_fresh_plan()
    plan_a = aerie.duplicate(plan_c)
    aerie.add_activity(plan_c, start_time=1, args={})
    plan_b = aerie.duplicate(plan_c)

    aerie.add_activity(plan_a, start_time=2, args={})
    aerie.add_activity(plan_b, start_time=3, args={})

    aerie.merge(plan_b, plan_a)  # siblings

    aerie.merge(plan_a, plan_c)  # parent


def test_merge_unrelated():
    plan_c = aerie.make_fresh_plan()
    plan_a = aerie.duplicate(plan_c)
    plan_unrelated = aerie.make_fresh_plan()

    aerie.merge(plan_a, plan_unrelated)  # should error
    aerie.delete(plan_a)
    aerie.delete(plan_c)