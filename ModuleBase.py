import asyncio
import threading
import yaml
from pubsub import pub
import time
import types
import traceback
import tkinter as tk
from tkinter import ttk
import os
import sys
import platform
'''
-----------------------------------------------------------------------
DOCS NOT DONE
User classes:
Reference : Used as a class variable to access data from a yaml file within a Module
Async_Task : The basic unit, contains a single function
Module : A collection of tasks, manages it's own tasks
ModuleManager : A module itself, responsible for managing modules
-----------------------------------------------------------------------
'''
class Task_State:
    states = ["inactive", "new", "ready", "running", "awaiting", "interrupted", "terminated"]
    possible_state_change = {"inactive": ["new"],
                             "new": ["ready"],
                             "ready": ["running", "terminated"],
                             "running": ["interrupted", "awaiting", "terminated"],
                             "awaiting": ["running", "terminated"],
                             "interrupted": ["ready", "terminated"],
                             "terminated": ["new"]}

    def __init__(self, state_num = 0):
        self.state_num = state_num

    def __call__(self, func):
        def inner(instance, *args, **kwargs):
            current_state = instance.state
            next_state = self.__class__.states[self.state_num]
            if self.change_state(current_state, next_state):
                instance.set_state(next_state)
                pub.sendMessage(f"PRIVATE__{instance.name[:instance.name.find('.')]}", message = {"__task_code": instance.task_code,
                                                                                                  "__prev_code": instance.prev_code,
                                                                                                  "__task_name": instance.name, 
                                                                                                  "__current_state": current_state, 
                                                                                                  "__next_state": next_state})
                return func(instance, *args, **kwargs)
            else:
                pass
        return inner

    def change_state(self, from_state, to_state):
        if from_state in self.__class__.possible_state_change:
            if to_state in self.__class__.possible_state_change[from_state]:
                return True
        return False

class Reference:
    class YAML_var(dict):
        def __getattr__(self, name):
            value = self[name]
            if isinstance(value, dict):
                value = self.__class__(value)
            return value

    def __init__(self, reference_yamls):
        self.__dict = {}
        for yaml_file in reference_yamls:
            self.__dict.update(yaml.load(open(f"{yaml_file}.yaml", 'r'), Loader = yaml.FullLoader))
        self.__yaml_object = self.YAML_var(self.__dict)

    def __getattr__(self, name):
        value = self.__yaml_object[name]
        if isinstance(value, dict):
            value = self.YAML_var(value)
        return value


class Base_Task:
    def __init__(self):
        pass

    def new(self):
        pass

    def admitted(self):
        pass

    def ready(self):
        pass

    def running(self):
        pass

    def interrupt(self):
        pass

    def waiting(self):
        pass

    def terminated(self):
        pass

class Task(Base_Task):
    def __init__(self, func, relative_speed_multiplier = 0):
        super().__init__()
        self.__func = func
        self.__relative_speed_multiplier = relative_speed_multiplier
        self.__instance = func
        self.__wait_time = 1
        self.__admitted = False
        self.__name = f"{func.__class__.__name__}.{func.__name__}"
        self.__is_loop = True

    def new(self, task_code):
        self.task_code = task_code

    '''
    @property
    def admitted(self):
        return self.__admitted

    @admitted.setter
    def admitted(self, inp):
        self.__admitted = not self.admitted'''

    def ready(self):
        pass

    def run(self):
        pass

    def running(self):
        pass

    def interrupt(self):
        pass

    def waiting(self):
        pass

    def terminated(self):
        pass

    @property
    def name(self):
        return self.__name

    @staticmethod
    def loop(relative_speed_multiplier = 1):
        def inner(func):
            return Task(func, relative_speed_multiplier)
        return inner

class Async_Task(Base_Task):

    def __init__(self, func, relative_speed_multiplier = 1, ifreq = None, is_loop = True, condition = "", callback = ""):
        self.__func = func
        self.__interval = 1  # Wait time either 1/(relative*interval) or ifreq, ifreq precedence
        self.__relative_speed_multiplier = relative_speed_multiplier
        self.__ifreq = ifreq
        self.__is_loop = is_loop
        self.__condition_statement = condition
        self.__callback_statement = callback
        self.__instance = None
        self.__name = ""
        self.__unpaused = asyncio.Event() #False
        self.__task_code = None
        self.__prev_code = None
        self.__ran = False
        self.__args = ()
        self.__kwargs = {}
        self.__state = "inactive"
        super().__init__()

    @Task_State(1)
    def new(self, task_code):
        self.__task_code = task_code

    @Task_State(2)
    def ready(self, *args, interval = 1, relative_speed_multiplier = None, ifreq = None, **kwargs): 
        if self.__task_code == None:
            raise RuntimeError("task code not assigned to task")
        self.__interval = interval
        if relative_speed_multiplier != None:
            self.__relative_speed_multiplier = relative_speed_multiplier
        if ifreq!=None:
            self.__ifreq = ifreq
        self.__args = args
        self.__kwargs = kwargs

    @Task_State(3)
    def run(self):
        #Initial run
        if not self.__ran and self.conditions_is_met():
            if self.__is_loop:
                self.__unpaused.set()
                self.__coro = asyncio.ensure_future(self.loop_periodically())
            if not self.__is_loop:
                self.__coro = asyncio.ensure_future(self.run_once())
            self.__ran = True
        #If paused
        elif self.__ran and self.conditions_is_met:
            if self.__is_loop:
                self.__unpaused.set()
        else:
            self.terminate()

    @property
    def running(self):
        if self.__unpaused.is_set():
            return True
        else:
            return False

    @Task_State(4)
    def wait(self):
        self.__unpaused.clear()

    @Task_State(5)
    def interrupt(self): #Back to ready state
        try:
            self.__coro.cancel()
        except:
            pass
        finally:
            self.__ran = False

    @Task_State(6)
    def terminate(self):
        try:
            self.__coro.cancel()
        except:
            pass
        finally:
            self.callback()
            self.__ran = False
            self.__prev_code = self.__task_code
            self.__task_code = None


    @property
    def func(self):
        return self.__func

    def set_func(self, func):
        self.__func = func

    @property
    def relative_speed_multiplier(self):
        return self.__relative_speed_multiplier

    def set_relative_speed_multiplier(self, relative_speed_multiplier):
        self.__relative_speed_multiplier = relative_speed_multiplier

    @property
    def ifreq(self):
        return self.__ifreq

    def set_ifreq(self, ifreq):
        self.__ifreq = ifreq

    @property
    def is_loop(self):
        return self.__is_loop

    def set_is_loop(self, is_loop):
        self.__is_loop = is_loop

    @property
    def instance(self):
        return self.__instance

    def set_instance(self, instance):
        self.__instance = instance

    @property
    def name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name

    @property
    def task_code(self):
        return self.__task_code

    def set_task_code(self, task_code):
        self.__task_code = task_code

    @property
    def prev_code(self):
        return self.__prev_code

    def set_prev_code(self, task_code):
        self.__prev_code = task_code

    @property
    def ran(self):
        return self.__ran

    def set_ran(self, ran):
        self.__ran = ran

    @property
    def state(self):
        return self.__state

    def set_state(self, state):
        self.__state = state

    def wait_time(self):
        if self.__ifreq == None:
            return 1/(self.__relative_speed_multiplier*self.__interval)
        else:
            return 1/self.__ifreq

    def conditions_is_met(self):
        #Default value branch
        if self.__condition_statement == "":
            return True  
        #Evaluate condition
        result = eval(self.__condition_statement, {**globals(), **vars(self.__instance)}) #vars(self.__instance))
        return result if type(result) == bool else False

    def callback(self):
        if self.__callback_statement!= "":
            getattr(self.__instance, self.__callback_statement)()


    @staticmethod
    def create(func, relative_speed_multiplier = 1, ifreq = None, is_loop = True, condition = "", callback = ""):
        return Async_Task(func.__func__, relative_speed_multiplier = relative_speed_multiplier, ifreq = ifreq, is_loop = is_loop, condition = condition, callback = callback)
    
    #@staticmethod
    #def loop(relative_speed_multiplier = 1, ifreq = None, condition = "", callback = ""):
    #    def inner(func):
    #        return Async_Task(func, relative_speed_multiplier = relative_speed_multiplier, ifreq = ifreq, condition = condition, callback = callback)
    #    return inner

    class loop():
        def __init__(self, relative_speed_multiplier = 1, ifreq = None, condition = "", callback = ""):
            self.__info = {"__task_info": True,
                           "__task_type": "async",
                           "relative_speed_multiplier": relative_speed_multiplier,
                           "ifreq": ifreq,
                           "condition": condition,
                           "callback": callback,
                           "is_loop": True}
        
        def __call__(self, func):
            self.__info.update({"func": func})
            return self.__info
        

    async def loop_periodically(self):
        try:
            while True:
                time_passed = 0
                if time_passed<self.wait_time():
                    await asyncio.sleep(self.wait_time()-time_passed)

                await self.__unpaused.wait()
                start_time = time.time()
                await self.__func(self.__instance, *self.__args, **self.__kwargs)
                time_passed = time.time()-start_time

        except asyncio.CancelledError:
            raise
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            print(f"{type(e).__name__}: {e}")
        finally:
            if self.state != "terminated":
                self.terminate()


    #@staticmethod
    #def once(condition = "", callback = ""):
    #    def inner(func):
    #        return Async_Task(func, is_loop = False, condition = condition, callback = callback)
    #    return inner

    class once():
        def __init__(self, condition = "", callback = ""):
            self.__info = {"__task_info": True,
                           "__task_type": "async",
                           "condition": condition,
                           "callback": callback,
                           "is_loop": False}


        def __call__(self, func):
            self.__info.update({"func": func})
            return self.__info

    async def run_once(self):
        try:
            await self.__func(self.__instance, *self.__args, **self.__kwargs)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            print(f"{type(e).__name__}: {e}")
        finally:
            if self.state != "terminated":
                self.terminate()

    def __repr__(self):
        return f"<Task [{self.__task_code}|{self.__name}|{self.__state}|{self.__args}|{self.__kwargs}]>"

class Pub_Task(Base_Task):
    
    def __init__(self, func, topic, condition = "", callback = ""):
        self.__func = func
        self.__topic = topic
        self.__condition_statement = condition
        self.__callback_statement = callback
        self.__instance = None
        self.__name = ""
        self.__unpaused = False
        self.__task_code = None
        self.__prev_code = None
        self.__ran = False
        self.__args = ()
        self.__kwargs = {}
        self.__state = "inactive"
        super().__init__()

    @Task_State(1)
    def new(self, task_code):
        self.__task_code = task_code

    @Task_State(2)
    def ready(self, *args, interval = 1, relative_speed_multiplier = None, ifreq = None, **kwargs): 
        if self.__task_code == None:
            raise RuntimeError("task code not assigned to task")
        self.__args = args
        self.__kwargs = kwargs

    @Task_State(3)
    def run(self):
        #Initial run
        if self.conditions_is_met():
            self.__unpaused = True
            self.__strong_ref, _ = pub.subscribe(self.__listener, self.__topic)
        else:
            self.terminate()

    @property
    def running(self):
        if self.__unpaused:
            return True
        else:
            return False

    @Task_State(4)
    def wait(self):
        self.__unpaused = False

    @Task_State(5)
    def interrupt(self): #Back to ready state
        del self.__strong_ref

    @Task_State(6)
    def terminate(self):
        try:
            del self.__strong_ref
        except:
            pass
        finally:
            self.callback()
            self.__ran = False
            self.__prev_code = self.__task_code
            self.__task_code = None


    @property
    def func(self):
        return self.__func

    def set_func(self, func):
        self.__func = func

    @property
    def instance(self):
        return self.__instance

    def set_instance(self, instance):
        self.__instance = instance

    @property
    def name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name

    @property
    def task_code(self):
        return self.__task_code

    def set_task_code(self, task_code):
        self.__task_code = task_code

    @property
    def prev_code(self):
        return self.__prev_code

    def set_prev_code(self, task_code):
        self.__prev_code = task_code

    @property
    def ran(self):
        return self.__ran

    def set_ran(self, ran):
        self.__ran = ran

    @property
    def state(self):
        return self.__state

    def set_state(self, state):
        self.__state = state

    def conditions_is_met(self):
        #Default value branch
        if self.__condition_statement == "":
            return True  
        #Evaluate condition
        result = eval(self.__condition_statement, {**globals(), **vars(self.__instance)}) 
        return result if type(result) == bool else False

    def callback(self):
        if self.__callback_statement!= "":
            getattr(self.__instance, self.__callback_statement)()

    class subscribe():
        def __init__(self, topic, condition = "", callback = ""):
            self.__info = {"__task_info": True,
                           "__task_type": "pub",
                           "topic": topic,
                           "condition": condition,
                           "callback": callback}
        
        def __call__(self, func):
            self.__info.update({"func": func})
            return self.__info
        

    def __listener(self, message):
        try:
            print(self.__unpaused)
            if self.__unpaused:
                self.__func(self.__instance, message, *self.__args, **self.__kwargs)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            print(f"{type(e).__name__}: {e}")
        finally:
            if self.state != "terminated":
                self.terminate()

    def __repr__(self):
        return f"<Task [{self.__task_code}|{self.__name}|{self.__state}|{self.__args}|{self.__kwargs}]>"
    
class Module:
    CODE = True
    NAME = False

    def __init__(self, interval = None, task_code_generator = None):
        self.__name = ""#self.__class__.__name__
        self.__active = True
        self.__taskName_code = {}
        self.__taskCode_task = {}
        self.__destroyed = False
        self.__interval = interval
        if task_code_generator == None:
            self.__task_code = self.__task_code_gen()
        
        
        self.__active_tasks = set()
        self.__waiting_tasks = set()
        self.__interrupted_tasks = set()
        self.__inactive_tasks = set()
        self.__taskName_taskDicts = {"running": self.__active_tasks,
                                     "interrupted": self.__interrupted_tasks,
                                     "awaiting": self.__waiting_tasks,
                                     "terminated": self.__inactive_tasks,
                                     "inactive": self.__inactive_tasks,
                                     "new": self.__inactive_tasks, 
                                     "ready": self.__inactive_tasks}
        
    def activate(self):
        if not self.__active:
            self.__active = True
            all_waiting_tasks = []
            for task_code in self.__waiting_tasks:
                all_waiting_tasks.append(self.__taskCode_task[task_code])
            for task in all_waiting_tasks:
                task.run()

    def deactivate(self):
        if self.__active:
            self.__active = False
            all_running_tasks = []
            for task_code in self.__active_tasks:
                all_running_tasks.append(self.__taskCode_task[task_code])
            for task in all_running_tasks:
                task.wait()

    def destroy(self):
        if self.__active:
            self.__active = False
            all_active_tasks = []
            for task_code in self.__active_tasks:
                all_active_tasks.append(self.__taskCode_task[task_code])
            for task in all_active_tasks:
                task.terminate()

    def boot(self):
        if not self.__active:
            self.__active = True
            all_inactive_tasks = []
            for task_code in self.__inactive_tasks:
                all_inactive_tasks.append(self.__taskCode_task[task_code])
            for task in all_inactive_tasks:
                self.__prep_task(task)
                self.run_task(task)



    def __task_code_gen(self):
        counter = -1
        while True:
            counter+=1
            yield oct(counter)
            
    def __prep_task(self, task, *args, **kwargs):
        task.set_instance(self)
        task.set_name(f"{self.__name}.{task.func.__name__}")
        task_code = next(self.__task_code)
        task.new(task_code)
        self.__taskCode_task[task_code] = task
        self.__inactive_tasks.add(task_code)
        if task.name in self.__taskName_code:
            self.__taskName_code[task.name].add(task_code)
        else:
            self.__taskName_code[task.name] = {task_code}
        task.ready(interval = self.__interval, *args, **kwargs)
        return task

    def start(self, interval = None, task_code_generator = None):
        pub.subscribe(self.task_state_listener, f"PRIVATE__{self.__name}")
        if interval!= None:
            self.__interval = interval
        if task_code_generator != None:
            self.__task_code = task_code_generator
        if self.__interval == None or self.__task_code == None:
            raise RuntimeError("both interval and task code generator must be supplied")
        
        """
        getattr(self, func_name) returns a dictionary which contains args and kwargs retrieved from decorators
        '__task_info' is added into the dictionary to determine if this dictionary should be used to make a Task object or not
        '__task_type' is added to determine which Task class should be used to construct this Task object
        only 'func' is allowed to be a positional argument, the rest are passed in as kwargs in dict form
        """

        task_list = []
        for func_name in dir(self):
            potential_task = getattr(self, func_name)
            if type(potential_task) == dict:
                if potential_task.get("__task_info", False):
                    func = potential_task.get("func")
                    task_type = potential_task.get("__task_type")
                    if task_type == "async":
                        task_list.append(Async_Task(func, **{key: value for key,value in potential_task.items() if key not in {"__task_info", "func", "__task_type"}}))
                    if task_type == "pub":
                        task_list.append(Pub_Task(func, **{key: value for key,value in potential_task.items() if key not in {"__task_info", "func", "__task_type"}}))

        for task in task_list:
            self.__prep_task(task)
            self.run_task(task)

    def prepare_task(self, task, *args, relative_speed_multiplier = 1, ifreq = None, **kwargs):
        task.set_instance(self)
        task.set_name(f"{self.__name}.{task.func.__name__}")
        task_code = next(self.__task_code)
        task.new(task_code)
        self.__taskCode_task[task_code] = task
        self.__inactive_tasks.add(task.task_code)
        #if task.name not in self.__taskName_code:
        #    task.set_name(task.func.__qualname__)
        if task.name in self.__taskName_code:
            self.__taskName_code[task.name].add(task_code)
        else:
            self.__taskName_code[task.name] = {task_code}
        task.ready(*args, interval = self.__interval, relative_speed_multiplier = relative_speed_multiplier, ifreq = ifreq, **kwargs)
        return task

    def run_task(self, task):
        if task.state== "ready":
            task.run()
        else:
            try:
                raise RuntimeError(f"task {task} is not in a state to be running")
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print(f"{type(e).__name__}: {e}")

    @property
    def name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name

    def get_tasks(self):
        return self.__taskCode_task

    @property
    def interval(self):
        return self.__interval

    def set_interval(self, interval):
        self.__interval = interval

    @property
    def task_code(self):
        return next(self.__task_code)

    @property
    def task_code_gen(self):
        return self.__task_code

    def set_task_code_gen(self, new_gen):
        self.__task_code = new_gen




    def task_state_listener(self, message):
        task_code, prev_code, task_name, current_state, next_state = message["__task_code"], message["__prev_code"], message["__task_name"], message["__current_state"], message["__next_state"]
        
        if task_code != None:
            self.__taskName_taskDicts[current_state].remove(task_code)
            self.__taskName_taskDicts[next_state].add(task_code)

        if current_state == "terminated" and next_state == "new":
            self.__taskName_code[task_name].remove(prev_code)
            self.__taskCode_task.pop(prev_code)

    def pause_task(self, task_identifier, identifier_type = True):
        if type(identifier_type)!= bool:
            print("Identifier Type must be Module.CODE or Module.NAME")
            return
        #CODE
        if identifier_type:
            if task_identifier in self.__taskCode_task:
                self.__taskCode_task[task_identifier].wait()
            else:
                print(f"task with code {task_identifier} does not exist")
        #NAME
        else:
            if task_identifier in self.__taskName_code:
                for task_code in self.__taskName_code[task_identifier] & self.__active_tasks:
                    self.__taskCode_task[task_code].wait()
            else:
                print(f"task with name {task_identifier} does not exist")

    def unpause_task(self, task_identifier, identifier_type = True):
        if type(identifier_type)!= bool:
            print("Identifier Type must be Module.CODE or Module.NAME")
            return
        #CODE
        if identifier_type:
            if task_identifier in self.__taskCode_task:
                self.__taskCode_task[task_identifier].run()
            else:
                print(f"task with code {task_identifier} does not exist")
        #NAME
        else:
            if task_identifier in self.__taskName_code:
                for task_code in self.__taskName_code[task_identifier] & self.__waiting_tasks:
                    self.__taskCode_task[task_code].run()
            else:
                print(f"task with name {task_identifier} does not exist")

    def interrupt_task(self, task_identifier, identifier_type = True):
        if type(identifier_type)!= bool:
            print("Identifier Type must be Module.CODE or Module.NAME")
            return
        #CODE
        if identifier_type:
            if task_identifier in self.__taskCode_task:
                self.__taskCode_task[task_identifier].interrupt()
            else:
                print(f"task with code {task_identifier} does not exist")
        #NAME
        else:
            if task_identifier in self.__taskName_code:
                for task_code in self.__taskName_code[task_identifier] & self.__active_tasks:
                    self.__taskCode_task[task_code].interrupt()
            else:
                print(f"task with name {task_identifier} does not exist")

    def restart_task(self, task_identifier, *args, relative_speed_multiplier = 1, ifreq = None, identifier_type = True, **kwargs):
        if type(identifier_type)!= bool:
            print("Identifier Type must be Module.CODE or Module.NAME")
            return
        #CODE
        if identifier_type:
            if task_identifier in self.__taskCode_task:
                self.__taskCode_task[task_identifier].ready(*args, relative_speed_multiplier = relative_speed_multiplier, ifreq = ifreq, **kwargs)
                self.run_task(self.__taskCode_task[task_identifier])
            else:
                print(f"task with code {task_identifier} does not exist")
        #NAME
        else:
            if task_identifier in self.__taskName_code:
                for task_code in self.__taskName_code[task_identifier] & self.__interrupted_tasks:
                    self.__taskCode_task[task_code].ready(*args, relative_speed_multiplier = relative_speed_multiplier, ifreq = ifreq, **kwargs)
                    self.run_task(self.__taskCode_task[task_code])
            else:
                print(f"task with name {task_identifier} does not exist")

    def terminate_task(self, task_identifier, identifier_type = True):
        if type(identifier_type)!= bool:
            print("Identifier Type must be Module.CODE or Module.NAME")
            return
        #CODE
        if identifier_type:
            if task_identifier in self.__taskCode_task:
                self.__taskCode_task[task_identifier].terminate()
            else:
                print(f"task with code {task_identifier} does not exist")
        #NAME
        else:
            if task_identifier in self.__taskName_code:
                for task_code in self.__taskName_code[task_identifier]:
                    self.__taskCode_task[task_code].terminate()
            else:
                print(f"task with name {task_identifier} does not exist")

    def reset_task(self, task_identifier, *args, relative_speed_multiplier = 1, ifreq = None, identifier_type = True, **kwargs):
        if type(identifier_type)!= bool:
            print("Identifier Type must be Module.CODE or Module.NAME")
            return
        #CODE
        if identifier_type:
            if task_identifier in self.__taskCode_task:
                prepared_task = self.prepare_task(self.__taskCode_task[task_identifier], *args, relative_speed_multiplier = relative_speed_multiplier, ifreq = ifreq, **kwargs)
                self.run_task(prepared_task)
            else:
                print(f"task with code {task_identifier} does not exist")
        #NAME
        else:
            if task_identifier in self.__taskName_code:
                for task_code in self.__taskName_code[task_identifier]:
                    prepared_task = self.prepare_task(self.__taskCode_task[task_code], *args, relative_speed_multiplier = relative_speed_multiplier, ifreq = ifreq, **kwargs)
                    self.run_task(prepared_task)
            else:
                print(f"task with name {task_identifier} does not exist")

    def change_task_speed(self, task_identifier, relative_speed_multiplier = 1, ifreq = None, identifier_type = True):
        if type(identifier_type)!= bool:
            print("Identifier Type must be Module.CODE or Module.NAME")
            return
        #CODE
        if identifier_type:
            if task_identifier in self.__taskCode_task:
                if ifreq!= None:
                    self.__taskCode_task[task_identifier].set_ifreq(ifreq)
                self.__taskCode_task[task_identifier].set_relative_speed_multiplier(relative_speed_multiplier)
            else:
                print(f"task with code {task_identifier} does not exist")
        #NAME
        else:
            if task_identifier in self.__taskName_code:
                for task_code in self.__taskName_code[task_identifier] & self.__active_tasks:
                    if ifreq!= None:
                        self.__taskCode_task[task_code].set_ifreq(ifreq)
                    self.__taskCode_task[task_code].set_relative_speed_multiplier(relative_speed_multiplier)
            else:
                print(f"task with name {task_identifier} does not exist")
    
    def show_tasks(self):
        return self.__active_tasks


    def __repr__(self):
        return f"<Module {self.name} object at {hex(id(self))}>"

    def __delete__(self, instance):
        pass



class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, bg,*args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it

        canvas = tk.Canvas(self, bd=0, highlightthickness=0,bg=bg)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.canvasheight = 2000

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas,height=self.canvasheight,bg=bg)
        interior_id = canvas.create_window(0, 0, window=interior,anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

        self.offset_y = 0
        self.prevy = 0
        self.scrollposition = 1

        def on_press(event):
            self.offset_y = event.y_root
            if self.scrollposition < 1:
                self.scrollposition = 1
            elif self.scrollposition > self.canvasheight:
                self.scrollposition = self.canvasheight
            canvas.yview_moveto(self.scrollposition / self.canvasheight)

        def on_touch_scroll(event):
            nowy = event.y_root

            sectionmoved = 15
            if nowy > self.prevy:
                event.delta = -sectionmoved
            elif nowy < self.prevy:
                event.delta = sectionmoved
            else:
                event.delta = 0
            self.prevy= nowy

            self.scrollposition += event.delta
            canvas.yview_moveto(self.scrollposition/ self.canvasheight)

        self.bind("<Enter>", lambda _: self.bind_all('<Button-1>', on_press), '+')
        self.bind("<Leave>", lambda _: self.unbind_all('<Button-1>'), '+')
        self.bind("<Enter>", lambda _: self.bind_all('<B1-Motion>', on_touch_scroll), '+')
        self.bind("<Leave>", lambda _: self.unbind_all('<B1-Motion>'), '+')






class ModuleManager(Module, tk.Tk):
    reference = Reference(["config"])
    class Loader(): 
        @staticmethod
        def load_all(YAML_File):
            nodes = []
            try:
                content = yaml.load(open(str(YAML_File), 'r'), Loader = yaml.FullLoader)
                frequency = 1
                for nodeName in content:
                    if nodeName == "Subfolders":
                        for folder in content[nodeName]:
                            currentdir = os.path.dirname(os.path.realpath(__file__))
                            sys.path.insert(0, os.path.join(currentdir, f"{folder}"))
                            print(f"{currentdir}/{folder} inserted to sys.path") 
                        continue
                    args = ''
                    module = content[nodeName]

                    #Special
                    if nodeName.startswith("_"):
                        continue

                    for key in module:
                        value = module[key]

                        #Special
                        if key.startswith("_"):
                            continue
                        #Required
                        if key == 'file':
                            file = value
                        elif key == 'varclass':
                            varclass = value
                        elif key == 'frequency':
                            frequency = value
                        #Exceptions
                        elif key == 'gui':
                            pass
                        #Arguments
                        else:
                            args = args + f"{key}='{value}',"

                    #Complete argument
                    try:
                        if args[-1] == ',':
                            args = args[:-1]
                    except IndexError:
                        pass

                    #Execute one node
                    exec(f"from {file} import {varclass}") 
                    node = eval(f"{varclass}({args})")
                    nodes.append( { "node": node, "node_name": nodeName,"class": varclass, "frequency": frequency, "args": args} )
                    print(f"{nodeName} successfully loaded")
                    #print(nodes)
            except FileNotFoundError:
                print('File not found')
            return nodes

    def __init__(self, yaml_file, width_height: "tuple containing width and height integer value" = (0, 0)):
        super().__init__()
        self.yaml_file = yaml_file
        self.code_distributor = self.__task_code_gen()
        self.__moduleName_module = {}
        self.__commands = {"pause": self.deactivate_module, 
                           "resume": self.reactivate_module, 
                           "destroy": self.destroy_module, 
                           "reboot": self.reboot_module}


        #def on_closing():
        #    self.destroy()
        #self.protocol("WM_DELETE_WINDOW", on_closing)  
        #Notebook
        tk.Tk.__init__(self)
        self.width_height = width_height
        if width_height != (0, 0):
            self.__width = width_height[0]
            self.__height = width_height[1]
            self.geometry(f"{width_height[0]}x{width_height[1]}")
            self.notebook = ttk.Notebook(self)
            self.terminal = ttk.Frame(self.notebook)
            self.GUI = ttk.Frame(self.notebook)
            self.notebook.add(self.terminal, text ='Console')
            self.notebook.add(self.GUI, text ='GUI')
            self.notebook.pack(fill ="both")
            def on_tab_change(event):
                tab = event.widget.tab('current')['text']
                if tab == 'GUI':
                    self.reactivate_module("GUI")
                else:
                    self.deactivate_module("GUI")
            self.notebook.bind('<<NotebookTabChanged>>', on_tab_change)

            #_Terminal_setup______________________________________________
            #self.terminal.sv = tk.StringVar()                           
            #self.terminal.sv.trace("w", lambda name, index, mode, sv=self.terminal.sv:lambda : sv.get)
            self.terminal.entry = tk.Entry(self.terminal, bg = "black", fg = "white", bd = 0)#textvariable = self.terminal.sv)
            self.terminal.entry.pack(fill = tk.X, side = tk.BOTTOM)
            self.terminal.entry.configure(font=("Helvetica", 10, "italic"), insertborderwidth = 300, insertofftime = 800)

            '''
            self.t1.entry = tk.Entry(self.t1, bg = "black", fg = "white", bd = 0, textvariable = self.t1.sv)
            self.t1.entry.pack(fill = tk.X, side = tk.BOTTOM)
            scrollbar = tk.Scrollbar(self.t1)
            self.t1.display = tk.Text(self.t1, bg = "black", fg = "white")
            scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
            self.t1.display.pack(side=tk.LEFT, fill=tk.BOTH)'''

            #output1
            self.terminal.output1 = tk.Text(self.terminal, bg = "black", fg = "white")
            scrollbar1 = tk.Scrollbar(self.terminal)
            scrollbar1.pack(side=tk.RIGHT, fill = tk.BOTH)
            scrollbar1.config(command=self.terminal.output1.yview)
            self.terminal.output1.config(yscrollcommand=scrollbar1.set)
            self.terminal.output1.configure(font=("Helvetica", 10, "italic"))
            self.terminal.output1.configure(state = "disabled")
            self.terminal.output1.pack(side=tk.LEFT, fill = tk.BOTH)
            #output2
            #scrollbar2 = tk.Scrollbar(self.terminal)
            #scrollbar2.pack(side=tk.RIGHT, fill = tk.BOTH)
            #self.terminal.output2 = tk.Text(self.terminal, bg = "yellow", fg = "white")
            #self.terminal.output2.pack(side=tk.LEFT, fill = tk.Y)
            #scrollbar2.config(command=self.terminal.output2.yview)
            #self.terminal.output2.config(yscrollcommand=scrollbar2.set)
            #self.terminal.output2.configure(font=("Helvetica", 10, "italic"))
            #self.terminal.output2.configure(state = "disabled")


            self.terminal.entry.bind('<KeyPress-Return>', self.update_input)
            #self.terminal.entry.bind('<KeyPress-`>', self.autocomplete)
            #self.terminal.entry.bind('<KeyRelease-`>', self.end_autocomplete)
            #____________________________________________________________


            #GUI
            #os.environ['SDL_WINDOWID'] = str(self.GUI.winfo_id())
            #if platform.system == "Windows":
            #    os.environ['SDL_VIDEODRIVER'] = 'windib'


    def __task_code_gen(self):
        counter = -1
        while True:
            counter+=1
            yield hex(counter)

    def register_all(self):
        nodes = self.Loader.load_all(self.yaml_file)
        for node in nodes:
            module, module_name, frequency = node["node"], node["node_name"], node["frequency"]
            module.set_interval(frequency)
            module.set_name(module_name)
            self.__moduleName_module[module_name] = module

    #def register(self, module):
    #    self.__moduleName_module[module.name] = module

    def start_all(self):
        for module in self.__moduleName_module.values():
            module.start(task_code_generator = self.code_distributor)

    def interpret(self, token_list):
        if len(token_list)==1:
            if token_list[0] in self.__commands:
                self.__commands[token_list[0]]()
        if len(token_list)==2:
            command, operand = token_list
            if command in self.__commands and operand in self.__moduleName_module:
                self.__commands[command](operand)


        

    def reactivate_module(self, module_name):
        self.__moduleName_module[module_name].activate()

    def deactivate_module(self, module_name):
        self.__moduleName_module[module_name].deactivate()

    def reboot_module(self, module_name):
        self.__moduleName_module[module_name].boot()

    def destroy_module(self, module_name):
        self.__moduleName_module[module_name].destroy()

    #_Terminal____________________________________________________
    def update_input(self, event):
        inp = self.terminal.entry.get()
        token_list = inp.split()
        self.interpret(token_list)
        self.terminal.entry.delete(0, 'end')
        self.terminal.output1.configure(state = "normal")
        #self.terminal.output2.configure(state = "normal")
        self.terminal.output1.insert(tk.END, "MM<"+inp+"\n")
        #self.terminal.output2.insert(tk.END, "MM>TEST\n")
        self.terminal.output1.see("end")
        if int(self.terminal.output1.index('end-1c').split('.')[0]) > 51:  
            self.terminal.output1.delete("1.0", "2.0")
        self.terminal.output1.configure(state = "disabled")


    #reference._Module_Manager.terminal_frequency
    @Async_Task.loop(ifreq = reference._Module_Manager.terminal_frequency, condition = "width_height != (0, 0)")
    async def update_loop(self):
        self.update_idletasks()
        self.update()
        print(self.__moduleName_module["ProfileA"].show_tasks())
        self.__moduleName_module["ProfileA"].pause_task("0x9")




    #_____________________________________________________________












    def run_forever(self):
        asyncio.get_event_loop().run_forever()

    #def exit(self):
    #    self.terminate_task("ModuleManager.update_loop", Module.NAME)
    #    self.destroy()


        

    


        



class Thread_Task():
    class thread_default_name:
        val = 0

        @classmethod
        def __iter__(cls):
            cls.val+=1
            yield f"Thread_Task_{str(cls.val)}"

    class run_flag():
        def __init__(self):
            self.__is_activated = False

        def activate(self):
            self.__is_activated = True

        def deactivate(self):
            self.__is_activated = False

        def is_activated(self):
            return self.__is_activated


    def __init__(self, target, record_name = None, args=(), kwargs={}):
        self._running = self.run_flag()
        self.target = target
        self.record_name = record_name
        self.args = args
        self.kwargs = kwargs
        self.kwargs["__thread__"] = self._running
        #target.running = self._running
        if self.record_name==None:
            self.record_name = next(iter(__class__.thread_default_name()))
        self.thread = threading.Thread(target = self.target, name = self.record_name, args = self.args, kwargs = self.kwargs, daemon= True)

    def start(self):
        self._running.activate()
        self._alive = self.thread.is_alive()
        self.thread.start()

    def cancel(self):
        self._running.deactivate()

    def cancelled(self):
        return not self._running.is_activated()

    def done(self):
        return not self.thread.is_alive()

    def get_name(self):
        return self.record_name


    

'''
class Module():
    @staticmethod
    async def __main_run__():
        while True:
            await asyncio.sleep(2)

    asyncio.ensure_future(__main_run__.__func__())
    def __init__(self):
        self.destroyed = False
        self.relative_speed_multiplier = {}     # {"Test.run": [<function Test.test at 0x...>, 10]}
        self.tasks = {}                         # {"Test.run": <Task pending coro=...>"}
        self.inst = {}                          # {"Test" : <__main__.test object at 0x...>}
        self.run_once_tasks = set()             # {"Test.run_once", "Test2.run_once"} no async      
        self.set_task_args_kwargs = {}          # {"Test.pub_handler":[<bound method Test.pub_handler>, [1, 3, "arg"], {"a": 2, "b": "kwarg"}]}    
    
    async def exec_periodically(self, wait_time, func, special_run = False, blocking = False):
        try:
            if blocking:
                loop = asyncio.get_running_loop()
            time_passed = 0
            while True:
                if time_passed<wait_time:
                    await asyncio.sleep(wait_time-time_passed)

                start_time = time.time()

                if special_run and not blocking:
                    func()
                elif special_run and blocking:
                    await loop.run_in_executor(None, func)
                elif not special_run and not blocking:
                    func(self)
                elif not special_run and blocking:
                    await loop.run_in_executor(None, func, self)

                time_passed = time.time()-start_time
        except Exception as e:
            exception_name = type(e).__name__
            if exception_name != "CancelledError":
                print(f"{exception_name}: [{e}]\nModule: [{self.__class__.__name__}]\nTask: [{func.__name__}]")

    async def async_exec_periodically(self, wait_time, coro, special_run = False):
        try:
            while True:
                await asyncio.sleep(wait_time)
                if special_run:
                    await coro()
                elif not special_run:
                    await coro(self)
        except Exception as e:
            exception_name = type(e).__name__
            if exception_name != "CancelledError":
                print(f"{exception_name}: [{e}]\nModule: [{self.__class__.__name__}]\nTask: [{coro.__name__}]")


    def thread_exec_periodically(self, wait_time, func, **kwargs):    
        stopEvent = threading.Event()
        nextTime=time.time()+wait_time
        while (not stopEvent.wait(nextTime-time.time())) and kwargs["__thread__"].is_activated():
            nextTime+=wait_time
            func(self)
        
    def thread_exec_once(self, func, **kwargs):
        if kwargs["__thread__"].is_activated():
            func(self)




    @staticmethod
    def loop(speed_multiplier = 1, blocking = False):
        def outer(func):
            def wrapper(varclass, record_name, interval):
                varclass.relative_speed_multiplier[record_name] = [func, speed_multiplier]
                wait_time = (1/speed_multiplier)*(1/interval)
                varclass.tasks[record_name] = asyncio.ensure_future(varclass.exec_periodically(wait_time, func, blocking = blocking))
            return wrapper
        return outer

    @staticmethod
    def asyncloop(speed_multiplier = 1):
        def outer(func):
            def wrapper(varclass, record_name, interval):
                coro = func
                varclass.relative_speed_multiplier[record_name] = [coro, speed_multiplier]
                wait_time = (1/speed_multiplier)*(1/interval)
                varclass.tasks[record_name] = asyncio.ensure_future(varclass.async_exec_periodically(wait_time, coro))
            return wrapper
        return outer

    @staticmethod
    def threadloop(speed_multiplier = 1):
        def outer(func):
            def wrapper(varclass, record_name, interval):
                varclass.relative_speed_multiplier[record_name] = [func, speed_multiplier]
                wait_time = (1/speed_multiplier)*(1/interval)
                thread = Thread_Task(target = varclass.thread_exec_periodically, record_name = record_name, args=(wait_time, func))
                varclass.tasks[record_name] = thread
                thread.start()
            return wrapper
        return outer

    @staticmethod
    def asynconce(func):
        def wrapper(varclass, record_name):
            coro= func
            try:
                varclass.tasks[record_name]=asyncio.ensure_future(coro(varclass))
            except Exception as e:
                exception_name = type(e).__name__
                if exception_name != "CancelledError":
                    print(f"{exception_name}: [{e}]\nModule: [{varclass.__class__.__name__}]\nTask: [{coro.__name__}]")
        return wrapper

    @staticmethod
    def threadonce(func):
        def wrapper(varclass, record_name):
            varclass.tasks[record_name]=Thread_Task(target = varclass.thread_exec_once, record_name=record_name, args = ([func]))
            varclass.tasks[record_name].start()
        return wrapper


    def task_cleanup(self, task_name):
        cancel_task_name = "cancel_"+task_name[task_name.find(".")+1:]
        if hasattr(self, cancel_task_name):
            getattr(self, cancel_task_name)()

    def create_task(self, func_name, record_name, interval):
        try:
            getattr(self, func_name)(record_name = record_name, interval = interval)
        except TypeError:
            if func_name == "run":
                self.relative_speed_multiplier[record_name] = [getattr(self, "run"), 1]
                self.tasks[record_name] = asyncio.ensure_future(self.exec_periodically(1/interval, getattr(self, "run"), special_run=True))
            else:
                try:
                    getattr(self, func_name)(record_name = record_name)
                except:
                    self.run_once_tasks.add(record_name)
                    getattr(self, func_name)()

    def set_task(self, coro, record_name, *args, **kwargs):
        try:
            self.tasks[record_name] = asyncio.ensure_future(coro(*args, **kwargs))
            self.set_task_args_kwargs[record_name] = [coro, args, kwargs]
        except Exception as e:
            #print("Error in set task")
            print(e)

    def start(self, interval):
        self.destroyed = False
        self.interval = interval
        self.run_funcs = [method for method in dir(self) if method[:3]=="run" and callable(getattr(self, method))]
        for func_name in self.run_funcs:
            run_record_name = str(self.__class__.__name__)+"."+func_name
            self.create_task(func_name, run_record_name, interval)
                
        self.inst[self.__class__.__name__] = self
                       
    def destroy(self):
        pass
'''

class AsyncModuleManager():
    inst = {}
    relative_speed_multiplier = {}
    tasks = {}
    cancelling = set()
    run_once_tasks = set()

    @classmethod
    def module_command_handler(cls, target, command):
        try:
            if command == "start" or command == "restart":
                if "." in target:
                    cls.start_task(target)
                else:
                    cls.restart_module(target)
            elif command == "cancel" or command == "destroy":
                if "." in target:
                    cls.cancel_task(target)
                else:
                    cls.destroy_module(target)
            elif command == "status":
                cls.show_status(target)
            else:
                print(f"Invalid command sent: {command}")
        except:
            print(f"An error occured when trying to send [command: {command}] to [target: {target}]")
    
    @classmethod
    def register_module(cls, module):
        try:
            cls.inst.update(module.inst)
            cls.tasks.update(module.tasks)
            cls.relative_speed_multiplier.update(module.relative_speed_multiplier)
            cls.run_once_tasks = cls.run_once_tasks|module.run_once_tasks
        except:
            raise TypeError("Must provide Modules as arguments")

    @classmethod
    def register_modules(cls, *args):
        for module in args:
            cls.register_module(module)

    @classmethod
    def update_manager(cls, module=None):
        if module==None:
            try:
                for module_ref in cls.inst.values():
                    cls.update_manager(module_ref)
            except:
                print("problem with update manager")
        else:
            cls.inst.update(module.inst)
            cls.tasks.update(module.tasks)
            cls.relative_speed_multiplier.update(module.relative_speed_multiplier)
            cls.run_once_tasks = cls.run_once_tasks|module.run_once_tasks

    @classmethod
    def update_cancelling(cls):
        temp_cancelling = cls.cancelling.copy()
        for cancelling_task_name in temp_cancelling:
            varclass = cls.get_instance(cancelling_task_name)
            if varclass.tasks[cancelling_task_name].done():
                cls.cancelling.remove(cancelling_task_name)


    @classmethod
    def get_instance(cls, module_or_method):
        if "." in module_or_method:
            return cls.inst[module_or_method[:module_or_method.find(".")]]   
        else:
            return cls.inst[module_or_method]

    @classmethod
    def get_method_name(cls, task):
        return task[task.find(".")+1:]
    
    @classmethod
    def start_task(cls, task_name):
        varclass = cls.get_instance(task_name)
        if not varclass.destroyed:
            if varclass.tasks[task_name].done():
                if task_name in varclass.set_task_args_kwargs:
                    varclass.set_task(varclass.set_task_args_kwargs[task_name][0], task_name, *varclass.set_task_args_kwargs[task_name][1], **varclass.set_task_args_kwargs[task_name][2])
                else:
                    varclass.create_task(cls.get_method_name(task_name), task_name, varclass.interval)
                if task_name in cls.cancelling:
                    cls.cancelling.remove(task_name)
                cls.update_manager(varclass)
    
    @classmethod
    def cancel_task(cls, method_name):   
        varclass = cls.get_instance(method_name)  

        if not varclass.tasks[method_name].done():
            varclass.tasks[method_name].cancel()
            varclass.task_cleanup(method_name)
            cls.cancelling.add(method_name)
            cls.update_manager(varclass)

        if not varclass.destroyed:
            if False not in [non_cancelling_task.done() for task_name, non_cancelling_task in varclass.tasks.items() if task_name not in cls.cancelling]:
                varclass.destroy()
                varclass.destroyed = True

    @classmethod
    def restart_module(cls, module_name):
        varclass = cls.get_instance(module_name)
        if varclass.destroyed:
            varclass.start(varclass.interval)
            for task_name in varclass.tasks:
                if task_name in cls.cancelling:
                    cls.cancelling.remove(task_name)
            cls.update_manager(varclass)
    
    @classmethod
    def destroy_module(cls, module_name):
        varclass = cls.get_instance(module_name)
        cls.update_cancelling()

        for task_name, task in varclass.tasks.items():
            if not task.done():
                task.cancel()
                cls.cancelling.add(task_name)
                varclass.task_cleanup(task_name)

        if not varclass.destroyed:
            varclass.destroy()
            varclass.destroyed = True

        cls.update_manager(varclass)

    @classmethod
    def show_status(cls, target):
        def status_report(reference):
            import itertools
            cancelled_tasks = []
            active_tasks = []
            longest_name=20
            
            
            cls.update_manager()
            cls.update_cancelling()
            for task_name, task in reference.tasks.items():
                if len(task_name)>longest_name:
                    longest_name = len(task_name)
                if not task.done():
                    if task_name not in cls.cancelling:
                        active_tasks.append(task_name)
                else:
                    cancelled_tasks.append(task_name)
            for run_once_name in cls.run_once_tasks:
                if len(run_once_name) > longest_name:
                    longest_name = len(run_once_name)
                cancelled_tasks.append(run_once_name)
            longest_name+=5
            yield f"{'ACTIVE':{longest_name}}{'CANCELLING':{longest_name}}{'CANCELLED':{longest_name}}"
            for active_task, cancelling_task, cancelled_task in itertools.zip_longest(active_tasks, cls.cancelling, cancelled_tasks):
                if active_task==None:
                    active_task=  ""
                if cancelled_task== None:
                    cancelled_task = ""
                if cancelling_task ==None:
                    cancelling_task = ""

                yield f"{active_task:{longest_name}}{cancelling_task:{longest_name}}{cancelled_task:{longest_name}}"


        try:
            if target=="AsyncModuleManager":
                reference = cls
            #elif target in cls.inst:
            #    reference = cls.get_instance(target)
            
            print("\n")
            for line in status_report(reference):
                print(line)
            print("\n")
        except Exception as e:
            print("status report", e)


    @classmethod
    def run_forever(cls):
        pub.subscribe(cls.module_command_handler, "AsyncModuleManager")
        asyncio.get_event_loop().run_forever()

    @classmethod
    def stop_all(cls):
        for module in cls.inst:
            try:
                cls.destroy_module(module)
            except Exception as e:
                print(e)







if __name__ == "__main__":
    '''
    class Something(Module):
        def __init__(self):
            self.var = 0
            pub.subscribe(self.handler , "topic")
            super().__init__()

        def something_operation(self, num1, num2):
            return num1 *num1 + num2 * num2
        
        def run(self):
            print(self.var)
            #print(self.inst)
            #self.var += 1

        @Module.asynconce
        async def run_test(self):
            while True:
                print("#@#@#@#@#@#@$@#@#@#@#@#@#@#@#")
                await asyncio.sleep(2)
                #print(len(asyncio.all_tasks()))

        @Module.asyncloop(0.2)
        async def run2(self):
            pass
            #print("######################################")
            #await self.test()



        def handler(self, var):
            self.var = var

        def destroy(self):
            print("Something destroyed")





    class Something2(Module):
        def __init__(self):
            self.var = 0
            super().__init__()

        @Module.loop(1, True)
        def run__increment(self):
            self.var +=1
            input("retrhyjuiktujytrg")
            #print(self.tasks)

        @Module.loop(10, True)
        def run_thread_pub(self):
            pub.sendMessage("topic", var = self.var)
            #self.test(self.run1)

        @Module.threadonce
        def run_thread_once(self):
            print("Something2 thread run_once")

        def cancel_run_thread_pub(self):
            print("Something2.run_thread_pub cancel cleanup done")

        def cancel_run(self):
            print("Something2.run cancel cleanup done")

        def run_once(self):
            print("SOMETHING2.RUN_ONCE")

        def destroy(self):
            print("Something2 destroyed")
    

    class EXIT(Module):
        def __init__(self):
            self.cancelled_counter = 0
            super().__init__()

        @Module.loop()
        def run(self):
            pass

        @Module.loop(0.2)
        def run_exit(self):
            if self.cancelled_counter < 1:
                try:
                    #pub.sendMessage("AsyncModuleManager", target = "Something2", command = "cancel")
                    pub.sendMessage("AsyncModuleManager", target = "Something.run2", command = "cancel")
                    #pub.sendMessage("AsyncModuleManager", target = "Something2.run", command = "cancel")
                    
                    
                    print("cancelled")
                    #
                    
                except Exception as e:
                    print(e)
                #print("exiting")
                #exit()
            elif self.cancelled_counter==2:
                print("STARTED")
                pub.sendMessage("AsyncModuleManager", target = "Something2", command = "start")
            print("len", len(asyncio.Task.all_tasks()))
            self.cancelled_counter +=1
            pub.sendMessage("AsyncModuleManager", target = "AsyncModuleManager", command = "status")

        @Module.loop(0.15)
        def run_start(self):
            #pub.sendMessage("AsyncModuleManager", target = "Something2.run1", command = "start")
            #pub.sendMessage("AsyncModuleManager", target = "Something.run2", command = "start")
            #pub.sendMessage("AsyncModuleManager", target = "Something2.run", command = "start")
            pass
            #pub.sendMessage("AsyncModuleManager", target = "Something2", command = "cancel")
            #pub.sendMessage("AsyncModuleManager", target = "AsyncModuleManager", command = "status")
            #print("restarted")
            #print("len", len(asyncio.Task.all_tasks()))

        def destroy(self):
            print("EXIT destroyed")

        '''


    '''
    s = Something()
    s2 = Something2()
    Exit = EXIT()
    s.start(1)
    s2.start(1)
    Exit.start(1)
    AsyncModuleManager.register_modules(s, s2, Exit)'''
    class test(Module):
        reference = Reference(["testconfig", "config"])
        def __init__(self):
            self.count = 1
            super().__init__()
            

        @Async_Task.loop(1, condition = "count==-1")
        async def this_is_the_loop(self):
            '''
            if self.count%10==0:
                a = Async_Task.create(self.self_invoked_loop, 3, callback="destroy_self_invoked_loop")
                self.__prep_task(a, "yoooo!", kwarg1 = self.count)
                self.run_task(a)'''
            self.change_task_speed("0o1", 10)
            if self.count == 7:
                #self.interrupt_task("0o1", identifier_type= Module.CODE)
                #self.pause_task("test.async_loop", identifier_type= Module.NAME)
                self.terminate_task("0o1", Module.CODE)
                print(self.get_tasks())
                #self.change_task_speed("0o3", 1000)
            if self.count ==  13:
                #self.reset_task("0o1", relative_speed_multiplier = 2 ,identifier_type= Module.CODE)
                self.reset_task("0o1", self.reference.Gamepad.file, relative_speed_multiplier = 2, identifier_type=Module.CODE)
                #self.restart_task("0o1", relative_speed_multiplier = 2 ,identifier_type= Module.CODE)
                #self.cancel_task_name("test.self_invoked_loop")
                #self.cancel_task_name("test.async_loop")
            if self.count == 20:
                self.interrupt_task("0o4", Module.CODE)
                print(self.get_tasks())
            if self.count == 26:
                self.restart_task("0o4", ifreq=30, identifier_type=Module.CODE)
                print(self.get_tasks())
            if self.count == 33:
                self.change_task_speed("0o4", ifreq = 5, identifier_type= Module.CODE)
            self.count +=1
            print(self.count)

        @Async_Task.once("count==0")
        async def do_one_time(self):
            print("did once!!!!")



        async def self_invoked_loop(self, a, kwarg1):
            print("self_invoked_loop says", a, kwarg1)

        def destroy_self_invoked_loop(self):
            print("self invoked loop destroyed")

        
        @Async_Task.loop(reference.test._async_loop, callback="destroy_async_loop")
        async def async_loop(self, *args):
            print("async_loop says hi", *args)

        def destroy_async_loop(self):
            print("async_loop destroyed")

    mm = ModuleManager("testconfig.yaml", (400,400))
    mm.start(1)
    mm.register_all()
    mm.start_all()
    #t = test()
    #t.start(1)
    

    try:
        #AsyncModuleManager.run_forever()
        mm.run_forever()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except BaseException as e:
        print(type(e), e)
    finally:
        print("Closing Loop")
        AsyncModuleManager.stop_all()



