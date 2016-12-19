#!/usr/bin/env python3

import os

from charms.reactive import (
   hook,
   RelationBase,
   scopes
)
from charms.reactive.bus import (
    set_state,
    get_state,
    remove_state
)

from charmhelpers.core.hookenv import ( 
   log,
   CRITICAL,
   ERROR,
   WARNING,
   INFO,
   DEBUG,
   remote_unit,
   relation_get,
   related_units,
   status_set
)

from charms.layer.hpccenv import HPCCEnv
from charms.layer.jujuenv import (
   JujuEnv,
   get_all_remote,
   all_related_units
)

class ClusterConfigureProvides(RelationBase):

    #class states(StateList):
    #    node_changed        = State('{relation_name}.node.changed')
    #    configure           = State('{relation_name}.configure')
    #    envxml_fetched      = State('{relation_name}.envxml.fetched')
    #    envxml_fetched_dali = State('{relation_name}.envxml.fetched.dali')
    #    dali_started        = State('{relation_name}.dali.started')
    #    dali_stopped        = State('{relation_name}.dali.stopped')
    #    cluster_started     = State('{relation_name}.cluster.started')
    #    cluster_stopped     = State('{relation_name}.cluster.stopped')
       

    scope = scopes.GLOBAL

    #def __init__(self, relation_name, conversation=None):
    #    super(ClusterConfigureProvides, self).__init__(relation_name, conversation)
    #    self.results = {}
    #    self.primary_state = 'initial'



    @hook('{provides:configure}-relation-joined')
    def joined(self):
        conv = self.conversation()

        remote_unit_id =  remote_unit()
        log("remote cluster node " + remote_unit_id + " joined", INFO)

        # get remote hpcc node ip to the file
        if not os.path.exists(HPCCEnv.CLUSTER_CURRENT_IPS_DIR):
           os.makedirs(HPCCEnv.CLUSTER_CURRENT_IPS_DIR)

        remote_unit_ip =  relation_get("private-address")
        if not remote_unit_ip:
           remote_unit_ip = remote_unit()
 
        log("remote private address " + remote_unit_ip, INFO)
        unit_type = remote_unit_id.split('/', 1)[0]        
        ip_file = HPCCEnv.CLUSTER_CURRENT_IPS_DIR + "/" + unit_type
        with open(ip_file, "a") as file:
           file.write(remote_unit_ip + '\n')

        status_set('active', JujuEnv.STATUS_MSG['NODE_JOINED'])
        self.set_state('{relation_name}.node.changed')
        conv.set_local('primary_state', '{relation_name}.node.changed')


    @hook('{provides:configure}-relation-{broken,departed}')
    def departed(self):
        conv = self.conversation()
        # remove remote hpcc node ip from the file

        remote_unit_id =  remote_unit()
        log("remote cluster node " + remote_unit_id + " departed", INFO)
        line_to_delete =  relation_get("private-address") + '\n'
        unit_type = remote_unit_id.split('/', 1)[0]        
        ip_file = HPCCEnv.CLUSTER_CURRENT_IPS_DIR + "/" + unit_type
        file = open(ip_file, "r")
        lines = file.readlines()
        file.close()
        with open(ip_file, "w") as file:
           for line in lines: 
              if line != line_to_delete:
                 file.write(line)

        status_set('active', JujuEnv.STATUS_MSG['NODE_DEPARTED'])
        #set_state('cluster.changed')
        self.set_state('{relation_name}.node.changed')
        conv.set_local('primary_state', '{relation_name}.node.changed')

    @hook('{provides:configure}-relation-changed')
    def changed(self):

        conv = self.conversation()
        primary_state  = conv.get_local('primary_state')
        log ('Current primary state: ' + primary_state, INFO)
        if self.is_state('{relation_name}.node.changed'):
           self.remove_state('{relation_name}.node.changed')
           self.set_state('{relation_name}.configure')
           conv.set_local('primary_state', '{relation_name}.configure')
           return

        log ('process remote data', INFO)
        # handle other state change without retrieve data from all remote

        # handle data from all remote
  
        last_action = conv.get_local('action')
        results = get_all_remote(conv, 'result')  

        units = all_related_units(conv.relation_ids)
 
        if len(results) != len(units):
           log('get remote response ' + str(len(results)) + 
               ' expect ' + str(len(units)), DEBUG)
           return 

        conv.set_local('results', results)
        for unit, result_str in results.items():
            action, result = result_str.split(':') 
            if action != last_action:
               return
            if result != 'OK':
               log('error in state ' + primary_state, ERROR) 
               self.set_state('{relation_name}.node.error')
               return

        if primary_state == '{relation_name}.configure':
           primary_state = '{relation_name}.envxml.fetched'
        elif primary_state == '{relation_name}.envxml.fetched':
           primary_state = '{relation_name}.envxml.fetched.dali'
        elif primary_state == '{relation_name}.envxml.fetched.dali':
           primary_state = '{relation_name}.dali.started'
        elif primary_state == '{relation_name}.dali.started':
           primary_state = '{relation_name}.started'
        #elif self.primary_state == '{relation_name}.dali.stopped':
        #elif self.primary_state == '{relation_name}.stopped':
        #elif self.primary_state == '{relation_name}.started':

        #self.remove_state(cur_primary_state)
        self.set_state(primary_state)
        conv.set_local('primary_state', primary_state)

