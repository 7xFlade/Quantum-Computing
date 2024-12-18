from typing import Any, Dict, Generator
from pydynaa import EventExpression
from squidasm.sim.stack.program import ProgramContext, ProgramMeta
from squidasm.util import create_two_node_network

from qkd_program import QkdProgram

class AliceProgram(QkdProgram):
    # Define Bob as the peer node for the QKD protocol
    PEER = "Bob"

    @property
    def meta(self) -> ProgramMeta:
        # Define program metadata including communication channels and resource requirements
        return ProgramMeta(
            name="alice_program",
            csockets=[self.PEER],  # Classical communication socket with Bob
            epr_sockets=[self.PEER],  # Quantum (EPR) socket with Bob
            max_qubits=1,  # Maximum number of qubits needed at once
        )

    def run(self, context: ProgramContext) -> Generator[EventExpression, None, Dict[str, Any]]:
        # Get the classical communication socket for Bob
        csocket = context.csockets[self.PEER]
        
        # Distribute quantum states (BB84 protocol states)
        pairs_info = yield from self._distribute_states(context, True)
        self.logger.info("Finished distributing states")

        # Wait for confirmation from Bob that all states were measured
        m = yield from csocket.recv()
        if m != self.ALL_MEASURED:
            raise RuntimeError("Failed to distribute BB84 states")

        # Filter out states where Alice and Bob used different bases
        pairs_info = yield from self._filter_bases(csocket, pairs_info, True)
        
        # Estimate the quantum bit error rate using test bits
        pairs_info, error_rate = yield from self._estimate_error_rate(
            csocket, pairs_info, self._num_test_bits, True
        )
        self.logger.info(f"Estimates error rate: {error_rate}")

        # Store all information about the pairs
        self.logger.info(f"Prepared pairs info: {pairs_info}")

        return pairs_info