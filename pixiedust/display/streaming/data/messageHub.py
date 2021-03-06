# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2017
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------
from pixiedust.display.streaming import *
from six import string_types, iteritems
import json
import os
import ssl
from kafka import KafkaConsumer
from kafka.errors import KafkaError

class MessagehubStreamingAdapter(StreamingDataAdapter):
    def __init__(self, topic, username, password):
        # Create a new context using system defaults, disable all but TLS1.2
        context = ssl.create_default_context()
        context.options &= ssl.OP_NO_TLSv1
        context.options &= ssl.OP_NO_TLSv1_1
        conf = {
            'client_id': 'pixieapp.client.id',
            'group_id': 'pixieapp.group',
            'sasl_mechanism': 'PLAIN',
            'security_protocol': 'SASL_SSL',
            'ssl_context': context,
            "bootstrap_servers": [
                "kafka01-prod01.messagehub.services.us-south.bluemix.net:9093",
                "kafka02-prod01.messagehub.services.us-south.bluemix.net:9093",
                "kafka03-prod01.messagehub.services.us-south.bluemix.net:9093",
                "kafka04-prod01.messagehub.services.us-south.bluemix.net:9093",
                "kafka05-prod01.messagehub.services.us-south.bluemix.net:9093"
            ],
            "sasl_plain_username": username,
            "sasl_plain_password": password
        }
        self.consumer = KafkaConsumer(**conf)
        self.consumer.subscribe([topic])
        self.schema = {}
        self.sampleDocCount = 0
        
    def close(self):
        self.consumer.unsubscribe()
        self.consumer.close() 
        
    def tryCast(self, value, t):
        try:
            return t(value)
        except:
            return None
        
    def inferType(self, value):
        if isinstance(value, string_types):
            value = self.tryCast(value, int) or self.tryCast(value, long) or self.tryCast(value, float) or value
        return "integer" if value.__class__==int else "float" if value.__class__ == float else "string"
        
    def inferSchema(self, eventJSON):
        if self.sampleDocCount > 20:
            return
        for key,value in iteritems(eventJSON):
            if not key in self.schema:
                self.schema[key] = self.inferType(value)
        self.sampleDocCount = self.sampleDocCount + 1 
    
    def doGetNextData(self):
        msgs = []
        msg = self.consumer.poll(1, max_records=10)
        if msg is not None:
            for topicPartition,records in iteritems(msg):
                for record in records:
                    if record.value is not None:                    
                        jsonValue = json.loads(record.value)
                        self.inferSchema(jsonValue)
                        msgs.append(jsonValue)
        return msgs
    
    def close(self):
        self.consumer.close()