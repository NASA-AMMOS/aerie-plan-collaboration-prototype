from abc import ABC, abstractmethod


class PlanCollaborationInterface(ABC):
    @abstractmethod
    def make_fresh_plan(db, start_time, end_time):
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
    def duplicate(db, plan, start_time, end_time):
        """
        We may want to add start and end time parameters to duplicate
        """
        pass

    @abstractmethod
    def request_merge(db, plan_supplying_changes, plan_receiving_changes):
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
    def begin_merge(db, merge_request_id):
        """
        1. Lock the plan receiving changes from further modification
        2. Identify the changesets of plans A and B with respect to the merge base.
        3. Identify conflicts between the changesets.
        4. Set the "merge request" state to "in progress", and populate the set of conflicts
        5. Create a staging plan. This staging plan, which is a copy of the plan receiving changes,
           contains all of the same things as the original plan, but it does not allow for modifications
           to be made aside from those that come from resolving conflicts. Importantly, it must allow
           running constraints, in order to help determine the validity of the merge.

        Return the id of the new staging plan
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

        Delete the staging plan
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
    def delete(db, plan):
        pass