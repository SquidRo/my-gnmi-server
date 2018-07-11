#
# gnmi_server.py
#
# GNMI Server
#

import argparse
import time
from concurrent import futures
import grpc
from gnmi import gnmi_pb2
from gnmi import gnmi_pb2_grpc

from oc_dispatcher import ocDispatcher
from pyangbind.lib.xpathhelper import YANGPathHelper
import pyangbind.lib.pybindJSON as pybindJSON
import json
import Queue
import threading
#import pdb

DEBUG_MODE = 1

myDispatcher = ocDispatcher()
Timer_Q = []

def DBG_STR(str):
    if DEBUG_MODE == 1:
        print str

#          input : PathElem
# example of ret : [ 'interfaces', 'interface' ]
def EncodePath(path):
    pathStrs = []
    for pe in path:
        pstr = pe.name
        if pe.key:
             for k, v in pe.key.iteritems():
                  pstr += "[" + str(k) + "=" + str(v) + "]"
        pathStrs += [pstr]

    DBG_STR(pathStrs)

    return pathStrs

#          input : PathElem
# example of ret : [ 'eth0', 'kkk' ]
def EncodePathKey(path):
    key_strs = []
    for pe in path:
        if pe.key:
             for k, v in pe.key.iteritems():
                  key_strs += [v]

    DBG_STR(key_strs)

    return key_strs

# example of input : [ 'interfaces', 'interface' ]
# example of ret   : "/interfaces/interface"
def EncodeYangPath(path_ar):
    ypath = ""
    for p in path_ar:
        ypath += "/" + p

    return ypath

# timer_rec: { 'req':, 'subs':, 'cur-tick':, 'context': , 'workq': }
# workq_rec: { 'req':, 'subs': }
def TimerEventHandler(timer_q):
    l_timer_q = []
    while True:
        #pdb.set_trace()
        while len(timer_q) > 0:
            l_timer_q.append(timer_q.pop())

        new_q = []
        for trec in l_timer_q:
            if trec['context'].is_active():
                trec['cur-tick'] -= 1
                if trec['cur-tick'] == 0:
                    trec['workq'].put( { 'req' : trec['req'],
                                         'subs': trec['subs'] }
                                     )
                else:
                    new_q.append(trec)
        l_timer_q[0:] = new_q
        time.sleep(1)


#
# class gNMITargetServicer
#
class gNMITargetServicer(gnmi_pb2_grpc.gNMIServicer):

    def __getCapabilitiesResponseObj(self):
        capResp = gnmi_pb2.CapabilityResponse()
        supModel = gnmi_pb2.ModelData(name="accton_model", organization="Accton", version="1.0")
        capResp.supported_models.extend([supModel])
        capResp.supported_encodings.extend(gnmi_pb2.JSON)
        capResp.gNMI_version = "GNMI Version 0.6"
        return capResp

    # refer to gnmi.proto
    #  get: prefix, path, type, encoding, use_models, extension
    #  set: prefix, delete, replace, update, extension
    #  cap: extension
    #  sub: subscribe, ...
    def __processGetRequestObj(self, reqGetObj):
        pfx_ar = EncodePath(reqGetObj.prefix.elem)
        t = reqGetObj.type

        #pdb.set_trace()

        #FIXME: Build the get response for all the paths
        getResp = gnmi_pb2.GetResponse()
        for path in reqGetObj.path:
            er_code = grpc.StatusCode.INVALID_ARGUMENT
            path_ar = pfx_ar + EncodePath(path.elem)
            pkey_ar = EncodePathKey(path.elem)

            #print path_ar
            oc_yph = myDispatcher.GetRequestYph(path_ar, pkey_ar)
            if isinstance(oc_yph, grpc.StatusCode):
                er_code = oc_yph
            else:
                yp_str = EncodeYangPath(path_ar)
                #pdb.set_trace()
                tmp_obj = oc_yph.get(yp_str) if oc_yph else []

                # TODO: if got more than one obj ?
                if len(tmp_obj) >= 1:
                    leaf_str = path_ar[-1]

                    # sometimes leaf can not be dumped,
                    # so dump the parent for safe
                    # set filter True to filter attributes which are not configured
                    tmp_json = json.loads(pybindJSON.dumps(tmp_obj[0]._parent, filter = True))

                    tmp_leaf_lst = leaf_str.split("[")
                    if len(tmp_leaf_lst) > 1:
                        # leaf_str has key field
                        # ex: ['interface', 'name=eth0]', 'kkk=aaa]']
                        for k in tmp_leaf_lst:
                            tmp_k = k.split("=")
                            if len(tmp_k) == 1:
                                fld_str = k
                            else:
                                fld_str = tmp_k[1][:-1]

                            if fld_str in tmp_json:
                                tmp_json = tmp_json[fld_str]
                    else:
                        if leaf_str in tmp_json:
                            tmp_json = tmp_json[leaf_str]
                        else:
                            tmp_json = None

                    if tmp_json:
                        notif = getResp.notification.add()
                        notif.timestamp = int(time.time())
                        notif.prefix.CopyFrom(reqGetObj.prefix)
                        update = notif.update.add()
                        update.path.CopyFrom(reqGetObj.path[0])

                        #pdb.set_trace()

                        update.val.json_val = json.dumps(tmp_json)
                        er_code = grpc.StatusCode.OK

            DBG_STR(er_code)

            if er_code != grpc.StatusCode.OK:
                getResp.error.code    = er_code.value[0]
                getResp.error.message = er_code.value[1]
                break

        return getResp

    # ErCode : grpc.StatusCode.XXX
    def __AddOneSetResp(self, SetRespObj, Path, Op, ErCode, ErMsg):
        OneUpdRes = SetRespObj.response.add()
        OneUpdRes.path.CopyFrom(Path)
        OneUpdRes.op   = Op
        OneUpdRes.message.code = ErCode.value[0]
        OneUpdRes.message.message = ErMsg if ErMsg != None else ErCode.value[1]

    def __processSetRequestObj(self, reqSetObj):
        IsAnyErr = False
        pathPrefix = EncodePath(reqSetObj.prefix.elem)

        print reqSetObj

        # Now Build the set response
        #
        #   one error => error code
        #   all other => aborted (10)
        #   over all  => aborted (10)
        setResp = gnmi_pb2.SetResponse()
        setResp.timestamp = int(time.time())

        #pdb.set_trace()

        # process order is delete, replace, update
        # refer to gnmi-specification.md

        # input: path (delete)
        for delete in reqSetObj.delete:
            delPath = pathPrefix + EncodePath(delete.elem)
            print delPath

        # input: path, val
        for replace in reqSetObj.replace:
            repPath = pathPrefix + EncodePath(replace.path.elem)

            k = replace.val.WhichOneof("value")

            print k

            val = getattr(replace.val, k)

            print val

            print repPath

        # input: same as replace
        for update in reqSetObj.update:
            updPath = pathPrefix + EncodePath(update.path.elem)
            self.__AddOneSetResp(setResp, update.path, 3, grpc.StatusCode.INVALID_ARGUMENT, None)

            print "updPath", updPath

        # Fill error message
        # refer to google.golang.org/grpc/codes
        #
        # overall result
        if IsAnyErr == True:
            ret_code = grpc.StatusCode.ABORTED
        else:
            ret_code = grpc.StatusCode.OK

        setResp.message.code = ret_code.value[0];
        setResp.message.message = ret_code.value[1];

        return setResp

    def __processSubscribeRequestObj(self, reqSubObj, context):

        # TODO: process more than one req ?
        for req in reqSubObj:
            print req
            #pdb.set_trace()

            k = req.WhichOneof("request")
            print k
            #val = getattr(req, k)
            #print val

            if k == 'subscribe':
                my_work_q = Queue.Queue()

                for subs in req.subscribe.subscription:
                    work_rec = { 'req' : req,
                                 'subs': subs }
                    my_work_q.put(work_rec)

                while True:
                    # wait here until work_rec occurs (from Timer_Q or enter here first time)
                    cur_work_rec = my_work_q.get()

                    cur_req = work_rec['req']
                    cur_subs= work_rec['subs']

                    print ["stream", "once", "poll"][cur_req.subscribe.mode]
                    subResp = gnmi_pb2.SubscribeResponse()
                    subResp.update.timestamp = int(time.time())

                    if cur_req.subscribe.mode == 0:
                        # stream
                        # send first response then wait for next round
                        # 1) put each subs into Timer_Q ???
                        # 2) wait for timer event occurs
                        print ["target defined", "on change", "sample"][cur_subs.mode]
                        print cur_subs.path
                        # on_change     : check heartbeat_interval
                        # sample        : check sample_interval, suppress_redundant (heartbeat_interval)
                        # target defined: per leaf
                        path_ar = []
                        path_ar += EncodePath(cur_req.subscribe.prefix.elem)
                        path_ar += EncodePath(cur_subs.path.elem)

                        subResp.update.prefix.CopyFrom(cur_req.subscribe.prefix)
                        update = subResp.update.update.add()
                        update.path.CopyFrom(cur_subs.path)
                        update.val.string_val = "Test"
                        yield subResp

                        trec = {'req'     : cur_req,
                                'subs'    : cur_subs,
                                'cur-tick': 10,
                                'context' : context,
                                'workq'   : my_work_q
                        }
                        Timer_Q.append(trec)
                        pass
                    elif cur_req.subscribe.mode == 1:
                        # once
                        # send a final response with sync_response set to True
                        # not need to check the subscription's mode
                        if my_work_q.empty():
                            subResp.sync_response = True
                            yield subResp
                            return
                        else:
                            update = subResp.update.update.add()
                            update.val.string_val = "Test"
                            yield subResp
                            path_lst = []
                        pass
                    elif cur_req.subscribe.mode == 2:
                        # poll
                        # send first response then wait for next round
                        pass


            elif k == 'poll':
                # on demand request
                pass
            elif k == 'aliases':
                pass

    # gNMI Services Capabilities Routine
    def Capabilities(self, request, context):
        print "Recv'ed Capabiality Request"
        return self.__getCapabilitiesResponseObj()

    # gNMI Services Get Routine
    def Get(self, request, context):
        print "Recv'ed Get Request"
        return self.__processGetRequestObj(request)

    # gNMI Services Set Routine
    def Set(self, request, context):
        print "Recv'ed Set Request"
        return self.__processSetRequestObj(request)

    # gNMI Services Subscribe Routine
    def Subscribe(self, request, context):
        print "Recv'ed Subscribe Request"
        return self.__processSubscribeRequestObj(request, context)

#
# class gNMITarget
#
class gNMITarget:
    """gNMI Wrapper for the Server/Target"""
    def __init__(self, targetUrl, tlsEnabled, caCertPath, privKeyPath):
        self.grpcServer = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        gnmi_pb2_grpc.add_gNMIServicer_to_server(gNMITargetServicer(), self.grpcServer)

        if tlsEnabled == True:
            # secure connection
            print privKeyPath, caCertPath
            with open(privKeyPath) as f:
                privateKey = f.read()
            with open(caCertPath) as f:
                certChain = f.read()
            credentials = grpc.ssl_server_credentials(((privateKey, certChain, ), ))
            self.grpcServer.add_secure_port(targetUrl, credentials)
        else:
            # insecure connection
            self.grpcServer.add_insecure_port(targetUrl)

    def run(self):
        threads = []
        t = threading.Thread(target=TimerEventHandler, args = (Timer_Q,))
        threads.append(t)
        t.daemon = True
        t.start()

        self.grpcServer.start()
        try:
            while True:
                time.sleep(60*60*24)
        except KeyboardInterrupt:
            self.grpcServer.stop(0)

#
# main
#
def main():
    parser = argparse.ArgumentParser()
    parserGrp = parser.add_argument_group("secure grpc")
    parser.add_argument('targetURL', help="target url, typically localhost:<port>")
    parserGrp.add_argument('--tls', action="store_true", help="enable tls connection")
    parserGrp.add_argument('--cert', help="path to the certificate")
    parserGrp.add_argument('--pvtkey', help="path to the private key file")
    args = parser.parse_args()

    print args

    gTarget = gNMITarget(args.targetURL, args.tls, args.cert, args.pvtkey)
    gTarget.run()

# Starts here
if __name__ == '__main__':
    main()