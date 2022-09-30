import interface

class Printable:
    def __repr__(self):
        return repr(self.__dict__)

class Plan(Printable):
    def __init__(self, id, start_time, end_time, parent_id, latest_snapshots):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time
        self.parent_id = parent_id
        self.latest_snapshots = latest_snapshots

class Activity(Printable):
    def __init__(self, plan_id, activity_id, type, start_time, args):
        self.plan_id = plan_id
        self.activity_id = activity_id
        self.type = type
        self.start_time = start_time
        self.args = args

class PlanSnapshot(Printable):
    def __init__(self, id, previous_snapshots):
        self.id = id
        self.previous_snapshots = previous_snapshots

class PlanSnapshotActivity(Printable):
    def __init__(self, plan_snapshot_id, activity_id, type, start_time, args):
        self.plan_snapshot_id = plan_snapshot_id
        self.activity_id = activity_id
        self.type = type
        self.start_time = start_time
        self.args = args

class MergeRequest(Printable):
    def __init__(
            self,
            id,
            state,
            plan_supplying_changes,
            plan_receiving_changes,
            plan_supplying_changes_snapshot,
            plan_supplying_changes_changeset,
            merge_base_id,
            non_conflicting_changes,
            conflicts,
            decisions,
    ):
        self.id = id
        self.state = state
        self.plan_supplying_changes = plan_supplying_changes
        self.plan_receiving_changes = plan_receiving_changes
        self.plan_supplying_changes_snapshot = plan_supplying_changes_snapshot
        self.non_conflicting_changes = non_conflicting_changes
        self.conflicts = conflicts
        self.decisions = decisions
        self.plan_supplying_changes_changeset = plan_supplying_changes_changeset
        self.merge_base_id = merge_base_id

class PlanCollaborationInterface(interface.PlanCollaborationInterface):
    def __init__(db):
        db.plans = []
        db.plan_counter = 0

        db.activities = []
        db.activity_counter = 0

        db.snapshots = []
        db.snapshot_counter = 0

        db.snapshot_activities = []

        db.merge_requests = []
        db.merge_request_counter = 0

    def make_fresh_plan(db, start_time=None, end_time=None):
        """
        Makes a new, empty plan
        :return: the new plan id
        """
        new_plan = Plan(db.plan_counter, start_time, end_time, None, [])
        db.plan_counter += 1
        append(new_plan, db.plans, lambda x: x.id)
        new_plan.latest_snapshots = []
        return new_plan.id

    def get_activity_ids(db, plan_id):
        """
        :return: the activity ids of all activities in the given plan
        """
        res = []
        for activity in db.activities:
            if activity.plan_id == plan_id:
                res.append(activity.activity_id)
        return res

    def add_activity(db, plan_id, type="Type", *, start_time, args):
        """
        Add a new activity to the given plan
        :return: the id of the new activity
        """
        new_activity = Activity(plan_id, db.activity_counter, type, start_time, args)
        db.activity_counter += 1
        append(new_activity, db.activities, lambda x: (x.plan_id, x.activity_id))
        return new_activity.activity_id

    def modify_activity(db, plan_id, activity_id, new_start_time, new_activity_args):
        activity = get_one(db.activities, plan_id=plan_id, activity_id=activity_id)
        activity.start_time = new_start_time
        activity.args = new_activity_args

    def delete_activity(db, plan_id, activity_id):
        activity_to_delete = get_one(db.activities, plan_id=plan_id, activity_id=activity_id)
        db.activities.remove(activity_to_delete)

    def get_history_plan_id(db, plan_id):
        plan = get_one(db.plans, id=plan_id)
        return db.get_history(plan.latest_snapshots)

    def get_history(db, snapshot_ids):
        """
        Returns history in topological sort order
        """
        frontier = list(set(snapshot_ids))
        history = list()  # must be in a topological sort order
        while frontier:
            plan_id = frontier.pop()
            history.append(plan_id)
            snapshot = get_one(db.snapshots, id=plan_id)
            new = set(snapshot.previous_snapshots).difference(history).difference(frontier)
            frontier.extend(new)
        return history

    def make_snapshot(db, plan_id):
        plan = get_one(db.plans, id=plan_id)
        snapshot_id = db.snapshot_counter
        db.snapshot_counter += 1

        append(PlanSnapshot(
            snapshot_id,
            plan.latest_snapshots
        ), db.snapshots, lambda x: x.id)

        for activity in get_all(db.activities, plan_id=plan_id):
            append(PlanSnapshotActivity(
                    snapshot_id,
                    activity.activity_id,
                    activity.type,
                    activity.start_time,
                    activity.args
                ), db.snapshot_activities, lambda x: (x.plan_snapshot_id, x.activity_id))

        return snapshot_id

    def duplicate(db, parent_plan_id):  # TODO add start/end time to duplicate
        """
        Duplicating a plan creates a new plan, with a fresh id,
        that contains the same activity versions as the original plan.
        Duplicating a plan also creates a plan comparison point that
        will be in the history of both the child and the parent plan.
        """
        snapshot_id = db.make_snapshot(parent_plan_id)

        parent_plan = get_one(db.plans, id=parent_plan_id)

        parent_plan.latest_snapshots = set(list(parent_plan.latest_snapshots) + [snapshot_id])

        child_plan_id = db.plan_counter
        db.plan_counter += 1
        append(Plan(
            child_plan_id,
            parent_plan.start_time,
            parent_plan.end_time,
            parent_plan_id,
            {snapshot_id}
        ), db.plans, lambda x: x.id)

        for activity in get_all(db.activities, plan_id=parent_plan_id):
            append(
                Activity(
                    child_plan_id,
                    activity.activity_id,
                    activity.type,
                    activity.start_time,
                    activity.args
                ),
                db.activities,
                lambda x: (x.plan_id, x.activity_id)
            )
        return child_plan_id

    def request_merge(db, plan_supplying_changes, plan_receiving_changes):
        if plan_receiving_changes == plan_supplying_changes:
            raise Exception("Cannot merge a plan into itself")

        history_receiving = set(db.get_history_plan_id(plan_receiving_changes))
        history_supplying = db.get_history_plan_id(plan_supplying_changes)
        for snapshot_id in history_supplying:
            if snapshot_id in history_receiving:
                merge_base_id = snapshot_id
                break
        else:
            raise Exception("No merge base found")

        snapshot_id = db.make_snapshot(plan_supplying_changes)

        merge_request_id = db.merge_request_counter
        db.merge_request_counter += 1
        changeset = db.diff_plan_against_snapshot(plan_supplying_changes, merge_base_id)
        if not changeset[0] and not changeset[1] and not changeset[2]:
            raise Exception("Cannot request merge with empty changeset")
        append(MergeRequest(
            merge_request_id,
            "REQUESTED",
            plan_supplying_changes,
            plan_receiving_changes,
            snapshot_id,
            changeset,
            merge_base_id,
            [],  # No non-conflicting changes yet
            [],  # No conflicts yet
            [],  # No decisions yet
        ), db.merge_requests, lambda x: id)
        return merge_request_id

    def begin_merge(db, merge_request_id):
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
        merge_request: "MergeRequest" = get_one(db.merge_requests, id=merge_request_id)

        merge_base_id = merge_request.merge_base_id
        # Diff both sides of the merge against the snapshot
        receiver_adds, receiver_modifies, receiver_deletes = db.diff_plan_against_snapshot(merge_request.plan_receiving_changes, merge_base_id)
        supplier_adds, supplier_modifies, supplier_deletes = merge_request.plan_supplying_changes_changeset

        receiver_modifies_and_deletes_by_id = {}
        for modification, _ in receiver_modifies:
            receiver_modifies_and_deletes_by_id[modification.activity_id] = modification
        for modification in receiver_deletes:
            receiver_modifies_and_deletes_by_id[modification.activity_id] = "DELETE"

        non_conflicting_changes = []
        conflicts = []
        for modification, _ in supplier_modifies:
            if modification.activity_id in receiver_modifies_and_deletes_by_id:
                if receiver_modifies_and_deletes_by_id[modification.activity_id] == "DELETE":
                    conflicts.append((modification.activity_id, modification, "DELETE"))
                else:
                    receiver_modification = receiver_modifies_and_deletes_by_id[modification.activity_id]
                    if modification.start_time != receiver_modification.start_time or modification.args != receiver_modification.args:
                        conflicts.append((modification.activity_id, modification, receiver_modification))
                    else:
                        noop()  # this is a no-op, no need to consider it a change
            else:
                non_conflicting_changes.append(("MODIFY", modification))

        for delete in supplier_deletes:
            if delete.activity_id in receiver_modifies_and_deletes_by_id and receiver_modifies_and_deletes_by_id[delete.activity_id] == "DELETE":
                noop()  # this is a no-op, no need to consider it a change
            elif delete.activity_id not in receiver_modifies_and_deletes_by_id:
                non_conflicting_changes.append(("DELETE", delete.activity_id))
            else:
                conflicts.append((delete.activity_id, "DELETE", receiver_modifies_and_deletes_by_id[delete.activity_id]))

        for add in supplier_adds:
            non_conflicting_changes.append(("ADD", add))

        # Now, we have a set of conflicts, which are tuples of one of the following forms:
        # - (id, activity, activity)
        # - (id, activity, "DELETE")
        # - (id, "DELETE", activity)
        # The items on the left are from the supplier, and the ones on the right are from the receiver.

        merge_request.non_conflicting_changes = non_conflicting_changes
        merge_request.conflicts = conflicts
        merge_request.decisions = [None] * len(conflicts)
        merge_request.state = "INPROGRESS"
        return conflicts

        # TODO create staging plan

    def diff_plan_against_snapshot(db, plan_id, snapshot_id):
        added = []
        deleted = []
        modified = []

        plan_activities = sorted(get_all(db.activities, plan_id=plan_id), key=lambda activity: activity.activity_id)
        snapshot_activities = sorted(get_all(db.snapshot_activities, plan_snapshot_id=snapshot_id), key=lambda activity: activity.activity_id)

        snapshot_activities_by_id = { activity.activity_id: activity for activity in snapshot_activities }
        plan_activities_by_id = { activity.activity_id: activity for activity in plan_activities }
        for activity in plan_activities:
            if activity.activity_id not in snapshot_activities_by_id:
                added.append(activity)
            else:
                matching_activity = snapshot_activities_by_id[activity.activity_id]
                if not (activity.args == matching_activity.args and activity.start_time == matching_activity.start_time):
                    modified.append((activity, snapshot_activities_by_id[activity.activity_id]))
        for activity in snapshot_activities:
            if activity.activity_id not in plan_activities_by_id:
                deleted.append(activity)

        return added, modified, deleted

    def resolve_conflict(db, merge_id, conflict_index, resolution):
        """
        Resolution is either "CHANGE_SUPPLIER" or "CHANGE_RECEIVER"

        A resolution chooses an activity version from one plan or the other
        """
        merge_request = get_one(db.merge_requests, id=merge_id)
        merge_request.decisions[conflict_index] = resolution

    def get_merge_status(db, merge_id):
        return get_one(db.merge_requests, id=merge_id).state

    def commit_merge(db, merge_id):
        """
        Checks that the merge is fully resolved (no conflicts are in the "UNRESOLVED" state)
        Updates the staging area based on conflict resolutions
        Updates plan_receiving_changes to contain all activities in the staging area
        Marks the merge as "COMMITTED" (which unlocks the plan_receiving_changes for modification)
        """
        merge_request: "MergeRequest" = get_one(db.merge_requests, id=merge_id)

        if merge_request.state != "INPROGRESS":
            raise Exception("Cannot commit a merge in state " + merge_request.state)

        if None in merge_request.decisions:
            raise Exception("Merge cannot be committed until all conflicts are resolved")

        # apply changes from the merge request to the plan_receiving_changes
        for change_type, payload in merge_request.non_conflicting_changes:
            if change_type == "ADD":
                append(Activity(
                    merge_request.plan_receiving_changes,
                    payload.activity_id,
                    payload.type,
                    payload.start_time,
                    payload.args
                ), db.activities, lambda x: (x.plan_id, x.activity_id))
            if change_type == "MODIFY":
                db.modify_activity(merge_request.plan_receiving_changes, payload.activity_id, payload.start_time, payload.args)
            if change_type == "DELETE":
                db.delete_activity(merge_request.plan_receiving_changes, payload)

        for decision, (activity_id, supplier, receiver) in zip(merge_request.decisions, merge_request.conflicts):
            if decision == "CHANGE_RECEIVER":
                continue
            if decision == "CHANGE_SUPPLIER":
                if supplier == "DELETE":
                    db.delete_activity(merge_request.plan_receiving_changes, activity_id)
                elif receiver == "DELETE":
                    append(Activity(
                        merge_request.plan_receiving_changes,
                        activity_id,
                        supplier.type,
                        supplier.start_time,
                        supplier.args
                    ), db.activities, lambda x: (x.plan_id, x.activity_id))
                else:
                    db.modify_activity(merge_request.plan_receiving_changes, activity_id, supplier.start_time, supplier.args)
        merge_request.state = "COMMITTED"


        # Include the pre-merge snapshot of the plan_supplying_changes in the history of both plans going forward
        plan_receiving_changes: "Plan" = get_one(db.plans, id=merge_request.plan_receiving_changes)
        plan_supplying_changes: "Plan" = get_one(db.plans, id=merge_request.plan_supplying_changes)

        plan_supplying_changes.latest_snapshots = {merge_request.plan_supplying_changes_snapshot} # the new snapshot dominates the old snapshots

        plan_receiving_changes.latest_snapshots = set(plan_receiving_changes.latest_snapshots)
        plan_receiving_changes.latest_snapshots.update([merge_request.plan_supplying_changes_snapshot])

        # TODO delete staging plan

    def abort_merge(db, merge_id):
        """
        Marks the merge as "ABORTED" (which unlocks the plan_receiving_changes for modification)
        """
        merge_request: "MergeRequest" = get_one(db.merge_requests, id=merge_id)
        merge_request.state = "ABORTED"

        # TODO delete staging plan

    def delete(db, plan):
        pass

    def get_activity_type(db, plan_id, activity_id):
        return get_one(db.activities, plan_id=plan_id, activity_id=activity_id).type

    def get_activity_start_time(db, plan_id, activity_id):
        return get_one(db.activities, plan_id=plan_id, activity_id=activity_id).start_time

    def get_activity_args(db, plan_id, activity_id):
        return get_one(db.activities, plan_id=plan_id, activity_id=activity_id).args


def get_one(table, **attributes):
    all = list(get_all(table, **attributes))
    assert len(all) == 1
    return all[0]


def get_all(table, **attributes):
    for x in table:
        for attribute_name, attribute_value in attributes.items():
            if getattr(x, attribute_name) != attribute_value:
                break
        else:
            yield x

def append(new_element, list_, key):
    keys = set()
    for element in list_:
        new_key = key(element)
        if new_key in keys: raise Exception("Existing uniqueness constraint violation")
    new_key = key(new_element)
    if new_key in keys: raise Exception("New key causes constraint violation")
    list_.append(new_element)

def noop():
    print("", end="")
