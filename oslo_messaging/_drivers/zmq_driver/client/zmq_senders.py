#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc
import logging

import six

from oslo_messaging._drivers.zmq_driver import zmq_async
from oslo_messaging._drivers.zmq_driver import zmq_names

LOG = logging.getLogger(__name__)

zmq = zmq_async.import_zmq()


@six.add_metaclass(abc.ABCMeta)
class SenderBase(object):
    """Base request/ack/reply sending interface."""

    def __init__(self, conf):
        self.conf = conf

    @abc.abstractmethod
    def send(self, socket, message):
        pass


class RequestSenderProxy(SenderBase):

    def send(self, socket, request):
        socket.send(b'', zmq.SNDMORE)
        socket.send(six.b(str(request.msg_type)), zmq.SNDMORE)
        socket.send(six.b(request.routing_key), zmq.SNDMORE)
        socket.send(six.b(request.message_id), zmq.SNDMORE)
        socket.send_pyobj(request.context, zmq.SNDMORE)
        socket.send_pyobj(request.message)

        LOG.debug("->[proxy:%(addr)s] Sending %(msg_type)s message "
                  "%(msg_id)s to target %(target)s",
                  {"addr": list(socket.connections),
                   "msg_type": zmq_names.message_type_str(request.msg_type),
                   "msg_id": request.message_id,
                   "target": request.target})


class ReplySenderProxy(SenderBase):

    def send(self, socket, reply):
        LOG.debug("Replying to %s", reply.message_id)

        assert reply.type_ == zmq_names.REPLY_TYPE, "Reply expected!"

        socket.send(b'', zmq.SNDMORE)
        socket.send(six.b(str(reply.type_)), zmq.SNDMORE)
        socket.send(reply.reply_id, zmq.SNDMORE)
        socket.send(reply.message_id, zmq.SNDMORE)
        socket.send_pyobj(reply)


class RequestSenderDirect(SenderBase):

    def send(self, socket, request):
        socket.send(b'', zmq.SNDMORE)
        socket.send_pyobj(request)

        LOG.debug("Sending %(msg_type)s message %(msg_id)s to "
                  "target %(target)s",
                  {"msg_type": zmq_names.message_type_str(request.msg_type),
                   "msg_id": request.message_id,
                   "target": request.target})


class ReplySenderDirect(SenderBase):

    def send(self, socket, reply):
        LOG.debug("Replying to %s", reply.message_id)

        assert reply.type_ == zmq_names.REPLY_TYPE, "Reply expected!"

        socket.send(reply.reply_id, zmq.SNDMORE)
        socket.send(b'', zmq.SNDMORE)
        socket.send_pyobj(reply)