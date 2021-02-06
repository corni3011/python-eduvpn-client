import logging
from .server import ServerDatabase
from .storage import get_uuid
from .state_machine import StateMachine, InvalidStateTransition
from .utils import run_in_background_thread


logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        from .network import InitialNetworkState
        from .interface import InitialInterfaceState
        self.network_state_machine = StateMachine(InitialNetworkState())
        self.interface_state_machine = StateMachine(InitialInterfaceState())
        self.server_db = ServerDatabase()
        self.current_network_uuid = None

    def initialize(self, make_func_threadsafe):
        self.initialize_network(make_func_threadsafe)
        self.initialize_server_db()

    @run_in_background_thread
    def initialize_network(self, make_func_threadsafe):
        """
        Determine the current network state.
        """
        # Check if a previous network profile exists.
        self.current_network_uuid = get_uuid()
        threadsafe_transition = make_func_threadsafe(self.network_transition)
        if self.current_network_uuid:
            if 0:  # TODO
                threadsafe_transition('found_active_connection')
            else:
                threadsafe_transition('found_previous_connection')
        else:
            threadsafe_transition('no_previous_connection_found')

    @run_in_background_thread
    def initialize_server_db(self):
        """
        Load the lists of organisations and servers.
        """
        self.server_db.update()

    @property
    def network_state(self):
        """
        Get the current state of the network.
        """
        return self.network_state_machine.state

    @property
    def interface_state(self):
        """
        Get the current state of the interface.
        """
        return self.interface_state_machine.state

    def connect_state_transition_callbacks(self, obj):
        """
        Register all state transition callback methods decorated with
        `@transition_callback()` and `@transition_edge_callback()` of an object.
        """
        from .network import NetworkState
        self.network_state_machine.connect_object_callbacks(obj, NetworkState)
        from .interface import InterfaceState
        self.interface_state_machine.connect_object_callbacks(obj, InterfaceState)

    def network_transition(self, transition, *args, **kwargs):
        """
        Perform a transition on the network state.
        """
        logger.info(f'network transitioning: {self.network_state} -> {transition}')
        try:
            self.network_state_machine.transition(transition, self, *args, **kwargs)
        except InvalidStateTransition:
            logger.error(f'invalid network state transition: {self.network_state} -> {transition}')
        else:
            logger.info(f'network transitioned: {transition} -> {self.network_state}')

    def interface_transition(self, transition, *args, **kwargs):
        """
        Perform a transition on the interface state.
        """
        logger.info(f'interface transitioning: {self.interface_state} -> {transition}')
        try:
            self.interface_state_machine.transition(transition, self, *args, **kwargs)
        except InvalidStateTransition:
            logger.error(f'invalid interface state transition: {self.interface_state} -> {transition}')
        else:
            logger.info(f'interface transitioned: {transition} -> {self.interface_state}')
