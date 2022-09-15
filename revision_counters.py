"""
This is the "revision counters" design
"""

from abc import ABC, abstractmethod

class Plan:
    def __init__(self, id, parent):
        self.id = id
        self.parent = parent

class Activity:
    def __init__(self, plan_id, activity_id, type, start_time, args, revision, parent_revision, deleted):
        self.plan_id = plan_id
        self.activity_id = activity_id
        self.type = type
        self.start_time = start_time
        self.args = args

        # Additional fields:
        self.revision = revision
        self.parent_revision = parent_revision
        self.deleted = deleted

class PlanCollaborationInterface(ABC):
    def __init__(db):
        db.plan_counter = 0
        db.activity_counter = 0
        db.plans = []
        db.activities = []

    def make_fresh_plan(db):
        """
        Makes a new, empty plan
        :return: the new plan id
        """
        new_plan = Plan(db.plan_counter, None)
        db.plan_counter += 1
        db.plans.append(new_plan)
        return new_plan.id

    def get_activity_ids(db, plan_id):
        """
        :return: the activity ids of all activities in the given plan
        """
        return [
            activity.activity_id
            for activity in db.activities
            if activity.plan_id == plan_id
        ]

    def get_activity_type(db, plan_id, activity_id):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        return activity.type

    def get_activity_args(db, plan_id, activity_id):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        return activity.args

    def get_activity_start_time(db, plan_id, activity_id):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        return activity.start_time

    def is_same_activity_persistent_identity(db, plan_id_1, activity_id_1, plan_id_2, activity_id_2):
        """
        Determines whether two activities are the "same" activity, in terms of "persistent identity"
        :return: True if they're the same, False otherwise
        """
        return activity_id_1 == activity_id_2

    def activities_are_compatible(db, plan_id_1, activity_id_1, plan_id_2, activity_id_2):
        """
        Determines whether two activities type, start time, and args are equal
        :return: True if they match, False otherwise
        """
        activity1 = next(_ for _ in db.activities if _.plan_id == plan_id_1 and _.activity_id == activity_id_1)
        activity2 = next(_ for _ in db.activities if _.plan_id == plan_id_2 and _.activity_id == activity_id_2)
        return activity1.type == activity2.type and activity1.args == activity2.args and activity1.start_time == activity2.start_time

    def add_activity(db, plan_id, type="Type", *, start_time, args):
        """
        Add a new activity to the given plan
        :return: the id of the "persistent identity" of the new activity
        """
        new_activity = Activity(plan_id, db.activity_counter, type, start_time, args, 0, None, False)
        db.activity_counter += 1
        db.activities.append(new_activity)
        return new_activity.activity_id

    def modify_activity(db, plan_id, activity_id, new_start_time, new_activity_args):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        activity.start_time = new_start_time
        activity.args = new_activity_args
        activity.revision += 1

    def delete_activity(db, plan_id, activity_id):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        activity.deleted = True
        activity.revision += 1

    def duplicate(db, plan_id):
        new_plan = Plan(db.plan_counter, plan_id)
        db.plan_counter += 1
        db.plans.append(new_plan)
        activity_ids = db.get_activity_ids(plan_id)
        for activity_id in activity_ids:
            activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
            db.activities.append(Activity(
                new_plan,
                activity_id,
                activity.type,
                activity.start_time,
                activity.args,
                0,
                activity.revision,
                activity.deleted,
            ))

# Concern: deleted activities need to be duplicated, because
# when merging a grandchild into its grandparent, we need to know what
# activities were deleted in its parent

    def merge(db, source_plan, target_plan):
        """
        The SOURCE plan is being merged into the TARGET plan
        """
        source_activities = [activity for activity in db.activities if activity.plan_id == source_plan]
        target_activities = [activity for activity in db.activities if activity.plan_id == target_plan]

        for source_activity in source_activities:
            corresponding_activities = [_ for _ in target_activities if _.activity_id == source_activity.activity_id]
            if not corresponding_activities and not source_activity.deleted:
                db.activities.append(Activity(
                    target_plan,
                    source_activity.activity_id,
                    source_activity.type,
                    source_activity.start_time,
                    source_activity.args,
                    source_activity.revision,  # !!!
                    None,
                    False,
                ))
            elif corresponding_activities:
                assert len(corresponding_activities) == 1, "activity_id should be unique within one plan"
                target_activity = corresponding_activities[0]
                if source_activity.deleted and not target_activity.deleted:
                    if source_activity.revision > 0




    def delete(db, plan):
        pass