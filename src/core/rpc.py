
import time
import queue
import threading
import uuid
import random


from src.core.common import *
from src.core.communicator import *

# ------------------------------------------------------------------------------

class LTS_RPC_Instance(LTS_BaseClass):

    def __init__(self, name="void", rpc_obj=None, handler=None, params_json="{}",
                 rpc_uuid=None, from_uuid=None):

        super().__init__("LTS_RPC")
        self.name = name
        self.rpc_obj = rpc_obj
        self.handler=handler
        self.params_json=params_json
        self.results_json="{}"
        self.uuid = rpc_uuid or str(uuid.uuid4())
        self.from_uuid = from_uuid

    def call(self):
        if self.handler:
            self.results_json = self.handler(self.params_json)
        if self.rpc_obj:
            self.rpc_obj.rpc_queue_out.put(self)

 

# ------------------------------------------------------------------------------

class LTS_RPC(LTS_BaseClass):

    def __init__(self, rpc_uuid=None, rpc_timeout_sec=10, running=True,
                 communicator=None):

        super().__init__("LTS_RPC")
        self.uuid = rpc_uuid or str(uuid.uuid4())

        self.rpc_timeout_sec = rpc_timeout_sec

        self.communicator = communicator

        # get remote callable peer list from procedure name
        # procedure_name : str -> peer_list : list(uuid : str)
        self.rpc_dict_remote = dict()

        # get local callable function from procedure name
        # procedure_name : str -> function_handler : func
        # func : (params_json : str -> results_json : str)
        self.rpc_dict_local = dict()

        # manage incoming and outgoing RPC : Queue(LTS_RPC_Instance)
        self.rpc_queue_in = queue.Queue()
        self.rpc_queue_out = queue.Queue()

        self.pid_sch = None
        self.pid_rsp = None

        self.running_lock = threading.Lock()
        self.setRunning(running)

        if self.getRunning():
            self.pid_sch = threading.Thread(target=self.run_sch)
            self.pid_sch.start()
            self.pid_rsp = threading.Thread(target=self.run_rsp)
            self.pid_rsp.start()


            
    def toJSON(self):
        res = '{"class_name": "LTS_RPC", "uuid": "'+self.uuid+'", "timeout": '+str(self.rpc_timeout_sec)+'}'
        return json.dumps(json.loads(res), sort_keys=True, indent=4)

        
    def getRunning(self):
        self.running_lock.acquire()
        res = self.running
        self.running_lock.release()
        return res

    def setRunning(self, running):
        self.running_lock.acquire()
        self.running = running
        self.running_lock.release()


    def register(self, name, handler):
        logging.info("[RPC] "+self.uuid+" Registering procedure " + name + " with handler " + str(handler))
        self.rpc_dict_local[name] = handler

    def registerRemote(self, name, peer_uuid):
        if name in self.rpc_dict_remote:
            self.rpc_dict_remote[name].append(peer_uuid)
        else:
            peer_list = list()
            peer_list.append(peer_uuid)
            self.rpc_dict_remote[name] = peer_list


    def run_sch(self):
        logging.info("[SCD] "+self.uuid+" RPC scheduler running")
        while self.getRunning():
            try:
                rpc_instance = self.rpc_queue_in.get(timeout=self.rpc_timeout_sec)
            except queue.Empty:
                rpc_instance = None
            if rpc_instance:
                logging.info("[SCD] "+self.uuid+" Scheduling "+rpc_instance.uuid+" procedure " + rpc_instance.name + " for " + str(rpc_instance.from_uuid))
                pid_inst = threading.Thread(target=rpc_instance.call)
                pid_inst.start()

        logging.info("[SCD] "+self.uuid+" RPC scheduler terminating")

    def run_rsp(self):
        logging.info("[RSP] "+self.uuid+" RPC response running")
        while self.getRunning():
            try:
                rpc_instance = self.rpc_queue_out.get(timeout=self.rpc_timeout_sec)
            except queue.Empty:
                rpc_instance = None
            if rpc_instance:
                logging.info("[RSP] "+self.uuid+" Sending back results "+rpc_instance.uuid+" procedure " + rpc_instance.name + " to " + str(rpc_instance.from_uuid))
                content = '{"rpc_uuid" : "'+rpc_instance.uuid+'", "procedure" : "'+rpc_instance.name+'", "results" : '+str(rpc_instance.results_json)+'}'
                message = LTS_Message(LTS_MessageType.RPC_RESULTS, content=content,
                                      from_uuid=self.uuid, to_uuid=rpc_instance.from_uuid)
                self.communicator.sendMessage(rpc_instance.from_uuid, message)

        logging.info("[RSP] "+self.uuid+" RPC response terminating")
        

    def addInstance(self, name, params_json, rpc_uuid=None, from_uuid=None):
        if name in self.rpc_dict_local:
            rpc_instance = LTS_RPC_Instance(name=name, rpc_obj=self,
                                            handler=self.rpc_dict_local[name],
                                            params_json=params_json,
                                            rpc_uuid=rpc_uuid,
                                            from_uuid=from_uuid)
            self.rpc_queue_in.put(rpc_instance)
        else:
            logging.warning("[RPC] "+self.uuid+" Procedure " + name + " unknown")


    def call(self, name, params_json="{}"):
        logging.info("[RPC] "+self.uuid+" Call procedure " + name)
        results_json = "{}"
        if name in self.rpc_dict_local:
            results_json = self.rpc_dict_local[name](params_json)
        elif name in self.rpc_dict_remote:
            rpc_uuid = str(uuid.uuid4())
            uuid_list = self.rpc_dict_remote[name]
            to_uuid = random.choice(uuid_list)
            content = '{"rpc_uuid" : "'+rpc_uuid+'", "procedure" : "'+name+'", "parameters" : '+params_json+'}'
            message = LTS_Message(LTS_MessageType.RPC_CALL, content=content,
                                  from_uuid=self.uuid, to_uuid=to_uuid)
            self.communicator.sendMessage(to_uuid, message)
            # TODO : register sync request in pending rpc dict 


        return results_json


    def terminate(self):
        self.setRunning(False)
        self.pid_sch.join()
        self.pid_rsp.join()
        


        

# ------------------------------------------------------------------------------

def handler_test(params_json):
    print("handler_test procedure " + params_json)
    return "{}"

# ------------------------------------------------------------------------------



if __name__ == "__main__":
    common = LTS_Common()

    rpc = LTS_RPC()
    rpc.register("handler_test", handler_test)
    rpc.addInstance("fail", "{}")
    rpc.addInstance("handler_test", "{}")
    time.sleep(8)
    rpc.terminate()

    exit(0)

