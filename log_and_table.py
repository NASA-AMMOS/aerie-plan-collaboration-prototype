import interface

class PlanCollaborationImplementation(interface.PlanCollaborationInterface):
    def __init__(db):
        # plans table
        # merges table
        # event log for recovering snapshots and heritage
        #  each event is a change to a plan, and it needs to refer to the previous plan snapshot
        # activities table
        # activity plan membership table

        pass

    @abstractmethod
    def make_fresh_plan(db):
        """
        Makes a new, empty plan
        :return: the new plan id
        """
        pass

    @abstractmethod
    def get_activity_ids(db, plan_id):
        """
        :return: the activity ids of all activities in the given plan
        """
        pass

    @abstractmethod
    def get_activity_type(db, plan_id, activity_id):
        pass

    @abstractmethod
    def get_activity_args(db, plan_id, activity_id):
        pass

    @abstractmethod
    def get_activity_start_time(db, plan_id, activity_id):
        pass

    @abstractmethod
    def is_same_activity_persistent_identity(db, plan_id_1, activity_id_1, plan_id_2, activity_id_2):
        """
        Determines whether two activities are the "same" activity, in terms of "persistent identity"
        :return: True if they're the same, False otherwise
        """
        pass

    @abstractmethod
    def activities_are_compatible(db, plan_id_1, activity_id_1, plan_id_2, activity_id_2):
        """
        Determines whether two activities type, start time, and args are equal
        :return: True if they match, False otherwise
        """
        pass

    def activities_match(db, plan_id_1, activity_id_1, plan_id_2, activity_id_2):
        return db.is_same_activity_persistent_identity(plan_id_1, activity_id_1, plan_id_2, activity_id_2) and db.activities_are_compatible(plan_id_1, activity_id_1, plan_id_2, activity_id_2)

    @abstractmethod
    def add_activity(db, plan_id, type="Type", *, start_time, args):
        """
        Add a new activity to the given plan, if there are no in-progress merges where this plan is receiving changes
        :return: the id of the "persistent identity" of the new activity
        """
        pass

    @abstractmethod
    def modify_activity(db, plan_id, activity_id, new_start_time, new_activity_args):
        """
        ... if there are no in-progress merges where this plan is receiving changes
        """
        pass

    @abstractmethod
    def delete_activity(db, plan_id, activity_id):
        """
        ... if there are no in-progress merges where this plan is receiving changes
        """
        pass

    @abstractmethod
    def duplicate(db, plan):
        """
        We may want to add start and end time parameters to duplicate
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def commit_merge(self, merge_id):
        """
        Checks that the merge is fully resolved (no conflicts are in the "UNRESOLVED" state)
        Updates the staging area based on conflict resolutions
        Updates plan_receiving_changes to contain all activities in the staging area
        Marks the merge as "COMMITTED" (which unlocks the plan_receiving_changes for modification)
        """
        pass

    @abstractmethod
    def abort_merge(self, merge_id):
        """
        Marks the merge as "ABORTED" (which unlocks the plan_receiving_changes for modification)
        """
        pass

    @abstractmethod
    def resolve_conflict(self, merge_id, conflict_id, resolution):
        """
        Resolution is either "CHANGE_SUPPLIER" or "CHANGE_RECEIVER"

        A resolution chooses an activity version from one plan or the other
        """
        pass

    @abstractmethod
    def resolve_conflicts_bulk(self, merge_id, conflict_ids, resolutions):
        """
        Applies multiple resolutions
        """
        pass

    @abstractmethod
    def delete(db, plan):
        pass