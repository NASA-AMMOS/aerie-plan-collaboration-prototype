from abc import ABC, abstractmethod

import interface

class Plan:
    def __init__(self, id, start_time, end_time, parent_id):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time
        self.parent_id = parent_id

class Activity:
    def __init__(self, plan_id, activity_id, type, start_time, args):
        self.plan_id = plan_id
        self.activity_id = activity_id
        self.type = type
        self.start_time = start_time
        self.args = args

class PlanSnapshot:
    def __init__(self, id, plan_id, start_time, end_time):
        self.id = id
        self.plan_id = plan_id
        self.start_time = start_time
        self.end_time = end_time

class PlanSnapshotActivity:
    def __init__(self, plan_snapshot_id, activity_id, type, start_time, args):
        self.plan_snapshot_id = plan_snapshot_id
        self.activity_id = activity_id
        self.type = type
        self.start_time = start_time
        self.args = args

class PlanCollaborationInterface(interface.PlanCollaborationInterface):
    def __init__(db):
        db.plans = []
        db.activities = []
        db.snapshots = []
        db.snapshot_activities = []
        db.plan_counter = 0
        db.activity_counter = 0
        db.snapshot_counter = 0

    def make_fresh_plan(db, start_time, end_time):
        """
        Makes a new, empty plan
        :return: the new plan id
        """
        new_plan = Plan(db.plan_counter, start_time, end_time, None)
        db.plan_counter += 1
        db.plans.append(new_plan)
        return new_plan.id

    def get_activity_ids(db, plan_id):
        """
        :return: the activity ids of all activities in the given plan
        """
        for activity in db.activities:
            if activity.plan_id == plan_id:
                yield activity.activity_id

    def is_same_activity_persistent_identity(db, plan_id_1, activity_id_1, plan_id_2, activity_id_2):
        """
        Determines whether two activities are the "same" activity, in terms of "persistent identity"
        :return: True if they're the same, False otherwise
        """
        return plan_id_1 == plan_id_2 and activity_id_1 == activity_id_2

    def add_activity(db, plan_id, type="Type", *, start_time, args):
        """
        Add a new activity to the given plan
        :return: the id of the new activity
        """
        new_activity = Activity(plan_id, db.activity_counter, type, start_time, args)
        db.activity_counter += 1
        db.activities.append(new_activity)
        return new_activity.activity_id

    def modify_activity(db, plan_id, activity_id, new_start_time, new_activity_args):
        activity = get_one(db.activities, plan_id=plan_id, activity_id=activity_id)
        activity.start_time = new_start_time
        activity.args = new_activity_args

    def delete_activity(db, plan_id, activity_id):
        activity_to_delete = get_one(db.activities, plan_id=plan_id, activity_id=activity_id)
        db.activities.remove(activity_to_delete)

    def _take_snapshot(db, plan_id):  # TODO add start/end time to take_snapshot
        plan = get_one(db.plans, plan_id=plan_id)
        snapshot_id = db.snapshot_counter
        db.snapshot_counter += 1
        db.snapshots.append(PlanSnapshot(snapshot_id, plan_id, plan.start_time, plan.end_time))
        for activity in get_all(db.activities, plan_id=plan_id):
            db.snapshot_activities.append(
                PlanSnapshotActivity(
                    snapshot_id,
                    activity.activity_id,
                    activity.type,
                    activity.start_time,
                    activity.args
                ))
        return snapshot_id

    def _make_plan_from_snapshot(db, plan_snapshot_id):
        snapshot: PlanSnapshot = get_one(db.snapshots, id=plan_snapshot_id)
        new_plan_id = db.plan_counter
        db.plan_counter += 1
        db.plans.append(Plan(new_plan_id, snapshot.start_time, snapshot.end_time, snapshot.plan_id))
        for activity in get_all(db.snapshot_activities, plan_snapshot_id=plan_snapshot_id):
            db.activities.append(
                Activity(
                    new_plan_id,
                    activity.activity_id,
                    activity.type,
                    activity.start_time,
                    activity.args
                ))
        return new_plan_id

    def duplicate(db, plan_id):  # TODO add start/end time to duplicate
        """
        We may want to add start and end time parameters to duplicate
        """
        # take a snapshot of plan with id plan_id
        snapshot_id = db._take_snapshot(plan_id)
        # make a new plan with parent plan_id
        new_plan_id = db._make_plan_from_snapshot(snapshot_id)
        return new_plan_id

    def merge(db, plan_supplying_changes, plan_receiving_changes):
        """
        There must be no in-progress merge involving the plan_receiving_changes

        The plan_supplying_changes must be a temporal subset of the plan_receiving_changes.
        The two plans must also be related. (If they're not related, just do a union)

        Identifies the changeset between the source_plan and merge base, and the changeset between target plan and merge base
        Correlates changes between these two changesets:
        - If two changes are identical, we can discard them
            - Identical means either they're both deletes, or both modified to the same end result
        - If a change is in one but not the other, apply that change
        - If a change is in both, and it is not identical, this is a conflict

        Returns an in-progress merge that has:
         - merge id
         - plan_supplying_changes_id
         - plan_receiving_changes_id
         - a staging area that contains the unconflicted changes
         - list of conflicts (which are a tuple of conflict_id, activity_id). This may be empty
         - list of resolutions - initially all "UNRESOLVED"

         The existence of this in-progress merge must "lock" the plan_receiving_changes, preventing it from being modified.
        """
        # Find the snapshot that represents the merge base
        # Diff both sides of the merge against the snapshot
        # We have two changesets, proceed according to the doc comment above
        pass

    def commit_merge(self, merge_id):
        """
        Checks that the merge is fully resolved (no conflicts are in the "UNRESOLVED" state)
        Updates the staging area based on conflict resolutions
        Updates plan_receiving_changes to contain all activities in the staging area
        Marks the merge as "COMMITTED" (which unlocks the plan_receiving_changes for modification)
        """
        #

        pass

    def abort_merge(self, merge_id):
        """
        Marks the merge as "ABORTED" (which unlocks the plan_receiving_changes for modification)
        """
        pass

    def resolve_conflict(self, merge_id, conflict_id, resolution):
        """
        Resolution is either "CHANGE_SUPPLIER" or "CHANGE_RECEIVER"

        A resolution chooses an activity version from one plan or the other
        """
        pass

    def resolve_conflicts_bulk(self, merge_id, conflict_ids, resolutions):
        """
        Applies multiple resolutions
        """
        pass

    def delete(db, plan):
        pass


def get_one(table, **attributes):
    return next(get_all(table, **attributes))


def get_all(table, **attributes):
    for x in table:
        for attribute_name, attribute_value in attributes:
            if getattr(x, attribute_name) != attribute_value:
                break
        else:
            yield x
