import interface

class Plan:
    def __init__(self, id):
        self.id = id

class Activity:
    def __init__(self, plan_id, activity_id, type, start_time, args):
        self.plan_id = plan_id
        self.activity_id = activity_id
        self.type = type
        self.start_time = start_time
        self.args = args

class PlanCollaborationInterface(interface.PlanCollaborationInterface):
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
        new_plan = Plan(db.plan_counter)
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
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        activity.start_time = new_start_time
        activity.args = new_activity_args

    def delete_activity(db, plan_id, activity_id):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        db.activities = [_ for _ in db.activities if _ != activity]

    def duplicate(db, plan_id):
        new_plan_id = db.make_fresh_plan()
        for activity_id in db.get_activity_ids(plan_id):
            db.add_activity(
                new_plan_id,
                type=db.get_activity_type(plan_id, activity_id),
                start_time=db.get_activity_start_time(plan_id, activity_id),
                args=db.get_activity_args(plan_id, activity_id)
            )
        return new_plan_id


    def merge(db, source_plan, target_plan):
        raise NotImplementedError

    def delete(db, plan_id):
        db.activities = [activity for activity in db.activities if activity.plan_id != plan_id]
        db.plans = [plan for plan in db.plans if plan.id != plan_id]

    def get_activity_type(db, plan_id, activity_id):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        return activity.type

    def get_activity_args(db, plan_id, activity_id):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        return activity.args

    def get_activity_start_time(db, plan_id, activity_id):
        activity = next(_ for _ in db.activities if _.plan_id == plan_id and _.activity_id == activity_id)
        return activity.start_time


    def activities_are_compatible(db, plan_id_1, activity_id_1, plan_id_2, activity_id_2):
        """
        Determines whether two activities type, start time, and args are equal
        :return: True if they match, False otherwise
        """
        activity1 = next(_ for _ in db.activities if _.plan_id == plan_id_1 and _.activity_id == activity_id_1)
        activity2 = next(_ for _ in db.activities if _.plan_id == plan_id_2 and _.activity_id == activity_id_2)
        return activity1.type == activity2.type and activity1.args == activity2.args and activity1.start_time == activity2.start_time