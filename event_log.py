import interface

class Event:
    def __init__(self, event_id, plan_id, payload): ### ??
        self.event_id = event_id
        self.plan_id = plan_id
        self.payload = payload

class PlanCollaborationInterface(interface.PlanCollaborationInterface):
    def __init__(db):
        db.event_log = []
        db.plan_counter = 0

    def make_fresh_plan(db):
        """
        Makes a new, empty plan
        :return: the new plan id
        """
        new_plan_id = db.plan_counter
        db.event_log.append(Event(len(db.event_log), new_plan_id, {"type": "PLAN_CREATED", "parent": None}))  # TBD: child?
        db.plan_counter += 1
        return new_plan_id

    def get_activity_ids(db, plan_id):
        """
        :return: the activity ids of all activities in the given plan
        """
        pass

    def get_activity_type(db, plan_id, activity_id):
        pass

    def get_activity_args(db, plan_id, activity_id):
        pass

    def get_activity_start_time(db, plan_id, activity_id):
        pass

    def is_same_activity(db, plan_id_1, activity_id_1, plan_id_2, activity_id_2):
        """
        Determines whether two activities are the "same" activity, in terms of "persistent identity"
        :return: True if they're the same, False otherwise
        """
        pass

    def add_activity(db, plan_id, type="Type", *, start_time, args):
        """
        Add a new activity to the given plan
        :return: the id of the "persistent identity" of the new activity
        """
        db.event_log.append(Event(len(db.event_log), plan_id, {
            "type": "ACTIVITY_CREATED",
            "activity_type": type,
            "start_time": start_time,
            "args": args
        }))

    def modify_activity(db, plan_id, activity_id, new_start_time, new_activity_args):
        db.event_log.append(Event(len(db.event_log), plan_id, {
            "type": "ACTIVITY_MODIFIED",
            "activity_id": activity_id,
            "new_start_time": new_start_time,
            "new_args": new_activity_args
        }))

    def delete_activity(db, plan_id, activity_id):
        db.event_log.append(Event(len(db.event_log), plan_id, {
            "type": "ACTIVITY_DELETED",
            "activity_id": activity_id,
        }))

    def duplicate(db, plan_id):
        new_plan_id = db.plan_counter
        db.event_log.append(Event(len(db.event_log), new_plan_id, {
            "type": "PLAN_CREATED",
            "parent": plan_id
        }))
        db.plan_counter += 1
        return new_plan_id

    def merge(db, source_plan, target_plan):
        # merge_base is the id of most recent event that precedes all changes on both sides of the merge
        merge_base_event_id, common_ancestor_plan_id = db.get_merge_base(source_plan, target_plan)

        # Set of new activities in source that should be added to target

        # get set of all activities that have been created between merge base and source
        # remove all activities that have been deleted..?

        # Question: Should we track activities as their own entities

        # Set of activities that have been modified between the merge base and the source
        # Set of activities that have been modified between the merge base and the target

    def get_merge_base(db, source_plan, target_plan):
        def get_creation_event(plan_id):
            return [
                event
                for event in db.event_log
                if event.payload["type"] == "PLAN_CREATED"
                   and event.plan_id == plan_id
            ]

        def get_parent(plan_id):
            return [
                event.payload["parent"]
                for event in get_creation_event(plan_id)
            ]

        # The nearest common ancestor is the plan of which both source and target are descendants.
        # The pertinent version of the common ancestor is the version at the creation of the older
        # ancestor plan
        source_heritage = [source_plan]
        target_heritage = [target_plan]
        intersection = set(source_heritage).intersection(target_heritage)
        while len(intersection) == 0:
            source_ancestor = get_parent(source_heritage[-1])
            source_heritage.extend(source_ancestor)
            target_ancestor = get_parent(target_heritage[-1])
            target_heritage.extend(target_ancestor)
            intersection = set(source_heritage).intersection(target_heritage)
        common_ancestor = list(intersection)[0]
        if common_ancestor is None:
            raise UnrelatedPlans()
        # Clamp at 0 because if the common ancestor is in index zero, we don't want to loop around
        source_ancestor_creation = \
        get_creation_event(source_heritage[max(0, source_heritage.index(common_ancestor) - 1)])[0]
        target_ancestor_creation = \
        get_creation_event(target_heritage[max(0, target_heritage.index(common_ancestor) - 1)])[0]
        # merge_base is the most recent event that precedes all changes on both sides of the merge
        return min(source_ancestor_creation.event_id, target_ancestor_creation.event_id), common_ancestor

    def delete(db, plan):
        pass

class UnrelatedPlans(Exception):
    pass