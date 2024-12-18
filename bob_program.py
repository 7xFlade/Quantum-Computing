from dataclasses import dataclass
from typing import Any, Dict, Generator

# Import required modules for quantum network simulation
from pydynaa import EventExpression
from squidasm.sim.stack.program import ProgramContext, ProgramMeta
from squidasm.util import create_two_node_network

from qkd_program import QkdProgram

class BobProgram(QkdProgram):
    # Define Alice as the peer node for this quantum communication
    PEER = "Alice"

    @property
    def meta(self) -> ProgramMeta:
        # Define program metadata including network configuration
        return ProgramMeta(
            name="bob_program",
            csockets=[self.PEER],      # Classical communication socket
            epr_sockets=[self.PEER],   # EPR pair socket for quantum entanglement
            max_qubits=1,              # Maximum number of qubits that can be stored
        )

    def run(self, context: ProgramContext) -> Generator[EventExpression, None, Dict[str, Any]]:
        # Get the classical communication socket for the peer
        csocket = context.csockets[self.PEER]
        
        # Distribute quantum states between nodes
        pairs_info = yield from self._distribute_states(context, False)
        self.logger.info("Finished distributing states")

        # Signal that all quantum measurements are complete
        csocket.send(self.ALL_MEASURED)
        
        # Filter quantum states based on matching measurement bases
        pairs_info = yield from self._filter_bases(csocket, pairs_info, False)
        
        # Estimate quantum bit error rate using test bits
        pairs_info, error_rate = yield from self._estimate_error_rate(
            csocket, pairs_info, self._num_test_bits, False
        )
        self.logger.info(f"Estimates error rate: {error_rate}")

        # Store all information about the pairs
        self.logger.info(f"Prepared pairs info: {pairs_info}")

        return pairs_info