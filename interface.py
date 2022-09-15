from abc import ABC, abstractmethod


class PlanCollaborationInterface(ABC):
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
        Add a new activity to the given plan
        :return: the id of the "persistent identity" of the new activity
        """
        pass

    @abstractmethod
    def modify_activity(db, plan_id, activity_id, new_start_time, new_activity_args):
        pass

    @abstractmethod
    def delete_activity(db, plan_id, activity_id):
        pass

    @abstractmethod
    def duplicate(db, plan):
        pass

    @abstractmethod
    def merge(db, source_plan, target_plan):
        pass

    @abstractmethod
    def delete(db, plan):
        pass