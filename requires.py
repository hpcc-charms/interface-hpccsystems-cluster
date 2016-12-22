#!/usr/bin/env python3
from charms.reactive import (
   hook,
   RelationBase,
   scopes
)


from charmhelpers.core import hookenv 
from charmhelpers.core.hookenv import (
   status_set,
   remote_unit,
   log,
   CRITICAL,
   ERROR,
   WARNING,
   INFO,
   DEBUG
)

from charms.layer.jujuenv import JujuEnv

class ClusterRequires(RelationBase):
    #class states(StateList):
    #    node_changed          = State('{relation_name}.node.changed')
    #    envxml_available      = State('{relation_name}.envxml.available')
    #    envxml_available_dali = State('{relation_name}.envxml.available.dali')
    #    dali_start            = State('{relation_name}.dali.start')
    #    dali_stop             = State('{relation_name}.dali.stop')
    #    cluster_start         = State('{relation_name}.start.start')
    #    cluster_stop          = State('{relation_name}.start.stop')


    # This probably doesn't matter GLOBAL, SERVICE or UNIT
    # since there is only one providers for this interface
    scope = scopes.UNIT

    #def __init__(self, relation_name, conversation=None):
    #    super(ClusterRequires, self).__init__(relation_name, conversation)
    #    self.result = 'unknown'
    #    self.primary_state = 'initial'

    @hook('{requires:cluster}-relation-joined')
    def joined(self):
        conv = self.conversation()
        status_set('active', JujuEnv.STATUS_MSG['NODE_JOINED'])
        primary_state = '{relation_name}.node.changed'
        self.set_state(primary_state)
        conv.set_local('primary_state', primary_state)

    @hook('{requires:cluster}-relation-{changed}')
    def changed(self):
        conv = self.conversation()
        action = conv.get_remote('action')
        if not action:
           return
        primary_state = conv.get_local('primary_state')
        log("Total conversations: " + str(len(self.conversations())), INFO)
        log("get action request: " + action, INFO)
        #if self.is_state(primary_state):
        #   self.remove_state(primary_state)
        primary_state = '{relation_name}.' + action
        self.set_state(primary_state)
        conv.set_local('primary_state', primary_state)
        
    #@hook('{requires:cluster}-relation-departed')
    #def departed(self):
    #   conv = self.conversation()

