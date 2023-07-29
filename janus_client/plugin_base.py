from .session import JanusSession, SessionMessage


class PluginMessage(SessionMessage):
    handle_id: int = None


class JanusPlugin:
    """Base class to inherit when implementing a plugin"""

    name: str = "janus.plugin.base.dummy"
    """Plugin name

    Must override to match plugin name in Janus server.
    """
    id: str

    def __init__(self, session: JanusSession, handle_id: int):
        self.session = session
        self.id = handle_id

    async def destroy(self):
        """Destroy plugin handle"""

        await self.send(PluginMessage(janus="detach"))
        self.session.destroy_plugin_handle(self)

    async def send(self, message: PluginMessage) -> dict:
        """Send raw message to plugin

        Will auto attach plugin ID to the message.

        :param message: JSON serializable dictionary to send
        :return: Synchronous reply from server
        """

        if message.handle_id:
            raise Exception("Plugin handle ID must not be manually added")

        message.handle_id = self.id
        return await self.session.send(message)

    def handle_async_response(self, response: dict):
        """Handle asynchronous events from Janus

        Must be overridden

        :raises NotImplementedError: If not overridden and received event from server
        """

        raise NotImplementedError()

    async def trickle(self, sdpMLineIndex, candidate):
        """Send WebRTC candidates to Janus

        :param sdpMLineIndex: (I don't know what is this)
        :param candidate: Candidate payload. (I got it from WebRTC instance callback)
        """

        class TrickleMessage(PluginMessage):
            candidate: dict

        candidate_payload = dict()
        if candidate:
            candidate_payload = {
                "sdpMLineIndex": sdpMLineIndex,
                "candidate": candidate,
            }
        else:
            # Reference: https://janus.conf.meetecho.com/docs/rest.html
            # - a null candidate or a completed JSON object to notify the end of the candidates.
            # TODO: test it
            candidate_payload = None

        # await self.send({"janus": "trickle", "candidate": candidate_payload})
        await self.sent(TrickleMessage(janus="trickle", candidate=candidate_payload))
        # TODO: Implement sending an array of candidates
