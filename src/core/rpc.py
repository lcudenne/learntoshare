
import time
import queue
import threading
import uuid


from src.core.common import *

# ------------------------------------------------------------------------------

class LTS_RPC_Instance(LTS_BaseClass):

    def __init__(self, name="void", rpc_obj=None, handler=None, params_json="{}"):

        super().__init__("LTS_RPC")
        self.name = name
        self.rpc_obj = rpc_obj
        self.handler=handler
        self.params_json=params_json
        self.results_json="{}"

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
        self.rpc_uuid = rpc_uuid or str(uuid.uuid4())

        self.rpc_timeout_sec = rpc_timeout_sec

        self.communicator = communicator
        
        self.rpc_dict = dict()
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


    def addRPC(self, name, handler):
        logging.info("[RPC] "+self.rpc_uuid+" Registering procedure " + name + " with handler " + str(handler))
        self.rpc_dict[name] = handler


    def run_sch(self):
        logging.info("[SCD] "+self.rpc_uuid+" RPC scheduler running")
        while self.getRunning():
            try:
                rpc_instance = self.rpc_queue_in.get(timeout=self.rpc_timeout_sec)
            except queue.Empty:
                rpc_instance = None
            if rpc_instance:
                logging.info("[SCD] "+self.rpc_uuid+" Scheduling procedure " + rpc_instance.name)
                pid_inst = threading.Thread(target=rpc_instance.call)
                pid_inst.start()

        logging.info("[SCD] "+self.rpc_uuid+" RPC scheduler terminating")

    def run_rsp(self):
        logging.info("[RSP] "+self.rpc_uuid+" RPC response running")
        while self.getRunning():
            try:
                rpc_instance = self.rpc_queue_out.get(timeout=self.rpc_timeout_sec)
            except queue.Empty:
                rpc_instance = None
            if rpc_instance:
                logging.info("[RSP] "+self.rpc_uuid+" Sending back results for procedure " + rpc_instance.name)

        logging.info("[RSP] "+self.rpc_uuid+" RPC response terminating")
        

    def addInstance(self, name, params_json):
        if name in self.rpc_dict:
            rpc_instance = LTS_RPC_Instance(name=name, rpc_obj=self,
                                            handler=self.rpc_dict[name],
                                            params_json=params_json)
            self.rpc_queue_in.put(rpc_instance)
        else:
            logging.warning("[RPC] "+self.rpc_uuid+" Procedure " + name + " unknown")


    def terminate(self):
        self.setRunning(False)
        self.pid_sch.join()
        self.pid_rsp.join()
        


        

# ------------------------------------------------------------------------------

def handler_test(params_json):
    print("handler_test procedure " + params_json)
    return True




if __name__ == "__main__":
    common = LTS_Common()

    rpc = LTS_RPC()
    rpc.addRPC("handler_test", handler_test)
    rpc.addInstance("fail", "{}")
    rpc.addInstance("handler_test", "{}")
    time.sleep(8)
    rpc.terminate()

    exit(0)

