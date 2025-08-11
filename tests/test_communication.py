import pytest
from core.base import Message, BaseAgent
from core.communication import MessageBus

class MockAgent(BaseAgent):
    def __init__(self, name):
        super().__init__(name, "Mock")
        self.received_messages = []

    def process_message(self, message: Message):
        self.received_messages.append(message)
        if message.type == "PING":
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="PONG",
                content={"response": "pong"}
            )
        return None

    def think(self, context):
        return {"thought": "mock"}

class TestMessageBus:
    def test_agent_registration(self):
        bus = MessageBus()
        agent = MockAgent("TestAgent")

        bus.register_agent(agent)

        assert "TestAgent" in bus.agents
        assert bus.agents["TestAgent"] == agent

    def test_direct_messaging(self):
        bus = MessageBus()
        bus.start()

        sender = MockAgent("Sender")
        receiver = MockAgent("Receiver")

        bus.register_agent(sender)
        bus.register_agent(receiver)

        # Envoyer message direct
        message = Message(
            sender="Sender",
            recipient="Receiver",
            type="TEST",
            content={"data": "test"}
        )

        bus.publish(message)

        # Attendre traitement
        import time
        time.sleep(0.2)

        # Vérifier réception
        assert len(receiver.inbox) == 1
        assert receiver.inbox[0].content["data"] == "test"

        bus.stop()

    def test_broadcast_messaging(self):
        bus = MessageBus()
        bus.start()

        broadcaster = MockAgent("Broadcaster")
        subscriber1 = MockAgent("Sub1")
        subscriber2 = MockAgent("Sub2")

        bus.register_agent(broadcaster)
        bus.register_agent(subscriber1)
        bus.register_agent(subscriber2)

        # Abonnements
        bus.subscribe("Sub1", "ANNOUNCEMENT")
        bus.subscribe("Sub2", "ANNOUNCEMENT")

        # Broadcast
        message = Message(
            sender="Broadcaster",
            type="ANNOUNCEMENT",
            content={"message": "Hello all"}
        )

        bus.publish(message)

        # Attendre
        import time
        time.sleep(0.2)

        # Vérifier
        assert len(subscriber1.inbox) == 1
        assert len(subscriber2.inbox) == 1
        assert subscriber1.inbox[0].content["message"] == "Hello all"

        bus.stop()

    def test_message_processing(self):
        bus = MessageBus()
        bus.start()

        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")

        bus.register_agent(agent1)
        bus.register_agent(agent2)

        # Ping-Pong test
        ping = Message(
            sender="Agent1",
            recipient="Agent2",
            type="PING",
            content={}
        )

        agent1.send_message(ping)
        bus.process_agent_messages()

        import time
        time.sleep(0.2)

        # Agent2 devrait avoir reçu PING et envoyé PONG
        assert len(agent2.received_messages) == 1
        assert agent2.received_messages[0].type == "PING"

        # Process responses
        bus.process_agent_messages()
        time.sleep(0.2)

        # Agent1 devrait avoir reçu PONG
        assert any(msg.type == "PONG" for msg in agent1.inbox)

        bus.stop()

class TestMessage:
    def test_message_creation(self):
        msg = Message(
            sender="TestSender",
            recipient="TestRecipient",
            type="TEST",
            content={"key": "value"}
        )

        assert msg.sender == "TestSender"
        assert msg.recipient == "TestRecipient"
        assert msg.type == "TEST"
        assert msg.content["key"] == "value"
        assert msg.priority == 5
        assert msg.id is not None
        assert msg.timestamp is not None

    def test_message_serialization(self):
        original = Message(
            sender="Sender",
            type="TEST",
            content={"number": 42, "text": "hello"}
        )

        # Sérialiser
        json_str = original.to_json()

        # Désérialiser
        restored = Message.from_json(json_str)

        assert restored.sender == original.sender
        assert restored.type == original.type
        assert restored.content == original.content
        assert restored.id == original.id
